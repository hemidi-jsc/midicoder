from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

from .llm import maybe_generate_project_file_with_llm
from .patch_ops import apply_upsert_region

_PROJECT_FILE_GROUP = "project_file"
_VALID_MERGE_MODES = {"create", "append", "patch"}
_EXTERNAL_IMPORT_TO_DISTRIBUTION = {
    "jwt": "PyJWT",
    "yaml": "PyYAML",
    "cv2": "opencv-python",
    "PIL": "Pillow",
}

_FALLBACK_STDLIB_MODULES = {
    "abc",
    "argparse",
    "asyncio",
    "base64",
    "collections",
    "contextlib",
    "dataclasses",
    "datetime",
    "decimal",
    "enum",
    "functools",
    "itertools",
    "json",
    "logging",
    "math",
    "os",
    "pathlib",
    "re",
    "sys",
    "time",
    "typing",
    "uuid",
}


def _normalize_path(path_value: str) -> str:
    return path_value.replace("\\", "/").lstrip("./")


def load_context_profile(workspace_root: Path) -> dict[str, Any]:
    profile_path = workspace_root / ".midicoder" / "context" / "profile.json"
    if not profile_path.exists():
        return {}
    try:
        raw = profile_path.read_text(encoding="utf-8")
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _collect_project_file_targets(
    *,
    manifest: Any,
    patch_plan_operations: dict[str, list[dict[str, Any]]],
) -> list[dict[str, str]]:
    targets: list[dict[str, str]] = []
    seen: set[str] = set()

    bootstrap_entrypoint = getattr(manifest, "bootstrap_entrypoint", None)
    if isinstance(bootstrap_entrypoint, str) and bootstrap_entrypoint.strip():
        runtime_path = _normalize_path(bootstrap_entrypoint)
        if not runtime_path.startswith("app/"):
            runtime_path = f"app/{runtime_path}"
        if runtime_path not in seen:
            seen.add(runtime_path)
            targets.append({"kind": "main", "runtime_path": runtime_path})

    targets.append({"kind": "requirements", "runtime_path": "requirements.txt"})

    package_dirs: set[str] = set()
    for runtime_path in patch_plan_operations:
        normalized = _normalize_path(runtime_path)
        if not normalized.startswith("app/") or normalized.endswith(".txt"):
            continue
        parts = normalized.split("/")[:-1]
        for idx in range(1, len(parts) + 1):
            package_dirs.add("/".join(parts[:idx]))
    for package_dir in sorted(package_dirs):
        init_path = f"{package_dir}/__init__.py"
        if init_path in seen:
            continue
        seen.add(init_path)
        targets.append({"kind": "package_init", "runtime_path": init_path})

    return targets


def _collect_context_requirements(context_profile: dict[str, Any]) -> list[str]:
    conventions = context_profile.get("conventions")
    if not isinstance(conventions, dict):
        return []
    deps = conventions.get("python_dependencies")
    if not isinstance(deps, list):
        return []
    lines: list[str] = []
    for dep in deps:
        if isinstance(dep, str) and dep.strip():
            lines.append(dep.strip())
    return sorted(set(lines))


def _normalize_package_name(package: str) -> str:
    return package.strip().lower().replace("_", "-")


def _requirement_base_name(line: str) -> str:
    text = line.strip()
    if not text:
        return ""
    match = re.match(r"^\s*([A-Za-z0-9_.-]+)", text)
    return _normalize_package_name(match.group(1)) if match else ""


def _stdlib_modules() -> set[str]:
    stdlib_names = getattr(sys, "stdlib_module_names", None)
    if isinstance(stdlib_names, set):
        return {
            str(name).strip()
            for name in stdlib_names
            if isinstance(name, str) and name.strip()
        }
    return set(_FALLBACK_STDLIB_MODULES)


def _is_stdlib_module(name: str) -> bool:
    normalized = (name or "").strip()
    if not normalized:
        return False
    return normalized in _stdlib_modules()


def _collect_external_modules_from_operations(
    patch_plan_operations: dict[str, list[dict[str, Any]]],
) -> list[str]:
    modules: set[str] = set()
    for operations in patch_plan_operations.values():
        for op in operations:
            if not isinstance(op, dict):
                continue
            snippets: list[str] = []
            imports = op.get("imports")
            if isinstance(imports, list):
                snippets.extend(
                    line for line in imports if isinstance(line, str) and line.strip()
                )
            region_content = op.get("region_content")
            if isinstance(region_content, str) and region_content.strip():
                snippets.append(region_content)

            for line in snippets:
                try:
                    tree = ast.parse(line)
                except SyntaxError:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            root = alias.name.split(".", 1)[0]
                            if (
                                root
                                and root not in {"app", "__future__"}
                                and not _is_stdlib_module(root)
                            ):
                                modules.add(root)
                    elif isinstance(node, ast.ImportFrom):
                        if node.level and node.level > 0:
                            continue
                        if node.module:
                            root = node.module.split(".", 1)[0]
                            if (
                                root
                                and root not in {"app", "__future__"}
                                and not _is_stdlib_module(root)
                            ):
                                modules.add(root)
    return sorted(modules)


def _collect_python_runtime_files(
    patch_plan_operations: dict[str, list[dict[str, Any]]],
) -> list[str]:
    files = [
        _normalize_path(path)
        for path in patch_plan_operations
        if _normalize_path(path).endswith(".py")
    ]
    return sorted(set(files))


def _collect_exports_from_region(region_content: str) -> list[str]:
    try:
        tree = ast.parse(region_content)
    except SyntaxError:
        return []
    exports: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name and not node.name.startswith("_"):
                exports.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id
                    and not target.id.startswith("_")
                ):
                    exports.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                name = node.target.id
                if name and not name.startswith("_"):
                    exports.add(name)
    return sorted(exports)


def _collect_runtime_exports(
    patch_plan_operations: dict[str, list[dict[str, Any]]],
) -> dict[str, list[str]]:
    exports_by_runtime: dict[str, set[str]] = {}
    for runtime_path, operations in patch_plan_operations.items():
        normalized_path = _normalize_path(runtime_path)
        if not normalized_path.endswith(".py") or normalized_path.endswith(
            "__init__.py"
        ):
            continue
        for op in operations:
            if not isinstance(op, dict):
                continue
            region_content = op.get("region_content")
            if not isinstance(region_content, str) or not region_content.strip():
                continue
            exports_by_runtime.setdefault(normalized_path, set()).update(
                _collect_exports_from_region(region_content)
            )
    return {path: sorted(values) for path, values in exports_by_runtime.items()}


def _build_project_file_context(
    *,
    target: dict[str, str],
    context_profile: dict[str, Any],
    patch_plan_operations: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    runtime_path = target["runtime_path"]
    kind = target["kind"]
    base = {
        "kind": kind,
        "runtime_path": runtime_path,
        "context_profile": context_profile,
        "python_runtime_files": _collect_python_runtime_files(patch_plan_operations),
    }
    runtime_exports = _collect_runtime_exports(patch_plan_operations)
    base["runtime_exports_by_path"] = runtime_exports
    if kind == "requirements":
        required_modules = _collect_external_modules_from_operations(
            patch_plan_operations
        )
        context_requirements = _collect_context_requirements(context_profile)
        base["required_external_modules"] = required_modules
        base["context_requirements"] = context_requirements
        requirements_map = {
            _requirement_base_name(line): line
            for line in context_requirements
            if _requirement_base_name(line)
        }
        required_packages: list[str] = []
        required_packages_with_versions: list[str] = []
        for module_name in required_modules:
            distribution = _EXTERNAL_IMPORT_TO_DISTRIBUTION.get(
                module_name, module_name
            )
            normalized = _normalize_package_name(distribution)
            required_packages.append(normalized)
            if normalized in requirements_map:
                required_packages_with_versions.append(requirements_map[normalized])
        base["required_packages"] = sorted(set(required_packages))
        base["required_packages_with_versions"] = sorted(
            set(required_packages_with_versions)
        )
    elif kind == "main":
        controller_modules: list[str] = []
        for runtime in _collect_python_runtime_files(patch_plan_operations):
            if runtime.endswith("/controller.py"):
                controller_modules.append(runtime[:-3].replace("/", "."))
        base["controller_modules"] = sorted(set(controller_modules))
    elif kind == "package_init":
        package_dir = runtime_path[: -len("/__init__.py")]
        prefix = package_dir + "/"
        members = [
            p
            for p in _collect_python_runtime_files(patch_plan_operations)
            if p.startswith(prefix)
        ]
        export_candidates: set[str] = set()
        module_exports: dict[str, list[str]] = {}
        child_packages: set[str] = set()
        for member in members:
            if not member.endswith(".py") or member.endswith("__init__.py"):
                continue
            module_name = member[len(prefix) :]
            if "/" in module_name:
                child_packages.add(module_name.split("/", 1)[0])
                continue
            bare_module = module_name[:-3]
            exports = runtime_exports.get(member, [])
            module_exports[bare_module] = exports
            # Always keep module name as candidate (e.g. app.main), then add concrete exports.
            export_candidates.add(bare_module)
            if exports:
                export_candidates.update(exports)
        export_candidates.update(child_packages)
        base["package_members"] = sorted(members)
        base["package_export_candidates"] = sorted(export_candidates)
        base["package_module_exports"] = module_exports
        base["package_child_packages"] = sorted(child_packages)
    return base


def _build_runtime_path_preview(
    *,
    runtime_path: str,
    patch_plan_operations: dict[str, list[dict[str, Any]]],
) -> str:
    current = ""
    for op in patch_plan_operations.get(runtime_path, []):
        if not isinstance(op, dict):
            continue
        try:
            current, _ = apply_upsert_region(
                current_content=current,
                operation=op,
                force=True,
                allow_patch_create=True,
            )
        except Exception:
            continue
    return current


def _extract_json_payload(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    if not raw:
        return None
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        # LLM may wrap text around JSON, try to extract first JSON object.
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            value = json.loads(raw[start : end + 1])
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None


def _validate_requirements_region(region_content: str) -> str | None:
    lines = [
        line.strip()
        for line in region_content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not lines:
        return "requirements region_content is empty"
    for line in lines:
        if not re.search(r"[<>=!~]{1,2}\s*[0-9]", line):
            return f"requirements line missing version spec: {line}"
    return None


def _validate_requirements_coverage(
    region_content: str, context_payload: dict[str, Any]
) -> str | None:
    required_packages = {
        _normalize_package_name(x)
        for x in (context_payload.get("required_packages") or [])
        if isinstance(x, str) and x.strip()
    }
    required_packages = {pkg for pkg in required_packages if not _is_stdlib_module(pkg)}
    if not required_packages:
        return None
    generated_packages = set()
    for line in region_content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        base = _requirement_base_name(stripped)
        if base:
            generated_packages.add(base)
    missing = sorted(pkg for pkg in required_packages if pkg not in generated_packages)
    if missing:
        return f"requirements missing packages for used imports: {', '.join(missing)}"
    return None


def _validate_project_file_payload(
    *,
    runtime_path: str,
    payload: dict[str, Any],
    kind: str,
    context_payload: dict[str, Any],
) -> tuple[list[str] | None, str | None, str | None]:
    merge_mode = payload.get("merge_mode")
    imports = payload.get("imports")
    region_content = payload.get("region_content")

    if not isinstance(merge_mode, str) or merge_mode not in _VALID_MERGE_MODES:
        return None, None, f"invalid merge_mode: {merge_mode!r}"
    if not isinstance(imports, list) or not all(isinstance(i, str) for i in imports):
        return None, None, "imports must be a list of strings"
    if not isinstance(region_content, str) or not region_content.strip():
        return None, None, "region_content must be non-empty string"

    clean_imports = [i.strip() for i in imports if i.strip()]
    clean_region = region_content.strip()

    if kind == "requirements":
        err = _validate_requirements_region(clean_region)
        if err:
            return None, None, err
        coverage_err = _validate_requirements_coverage(clean_region, context_payload)
        if coverage_err:
            return None, None, coverage_err
    elif runtime_path.endswith(".py"):
        combined_python = "\n".join(clean_imports + ["", clean_region]).strip()
        try:
            tree = ast.parse(combined_python)
        except SyntaxError as exc:
            return None, None, f"invalid python region_content: {exc.msg}"
        if kind == "package_init":
            package_dir = (
                runtime_path[: -len("/__init__.py")]
                if runtime_path.endswith("/__init__.py")
                else ""
            )
            package_module_name = package_dir.replace("/", ".")
            if package_dir == "app":
                for node in tree.body:
                    if not isinstance(node, ast.ImportFrom):
                        continue
                    if node.level != 1:
                        continue
                    if node.module == "main":
                        return (
                            None,
                            None,
                            "app/__init__.py must not import from .main to avoid circular imports",
                        )
            for node in tree.body:
                if not isinstance(node, ast.ImportFrom):
                    continue
                if node.level != 0:
                    continue
                module_name = str(node.module or "").strip()
                if not module_name:
                    continue
                if module_name == package_module_name or module_name.startswith(
                    package_module_name + "."
                ):
                    return (
                        None,
                        None,
                        "package_init must use relative imports for modules inside the same package",
                    )
            for node in tree.body:
                if (
                    isinstance(node, ast.AnnAssign)
                    and isinstance(node.target, ast.Name)
                    and node.target.id == "__all__"
                ):
                    return (
                        None,
                        None,
                        "__all__ must use plain assignment (__all__ = [...]), not type annotation",
                    )
            available = {
                name
                for name in (context_payload.get("package_export_candidates") or [])
                if isinstance(name, str) and name
            }
            python_runtime_files = {
                str(path).strip()
                for path in (context_payload.get("python_runtime_files") or [])
                if isinstance(path, str) and path.strip()
            }
            runtime_exports_by_path: dict[str, set[str]] = {}
            for runtime_file, exports in (
                context_payload.get("runtime_exports_by_path") or {}
            ).items():
                if not isinstance(runtime_file, str) or not isinstance(exports, list):
                    continue
                runtime_exports_by_path[runtime_file] = {
                    str(symbol).strip()
                    for symbol in exports
                    if isinstance(symbol, str) and str(symbol).strip()
                }
            package_prefix = package_dir + "/" if package_dir else ""
            for node in tree.body:
                if not isinstance(node, ast.ImportFrom):
                    continue
                if node.level != 1 or not isinstance(node.module, str):
                    continue
                rel_module = node.module.strip()
                if not rel_module:
                    continue
                candidate_runtime = f"{package_prefix}{rel_module}.py"
                candidate_init = f"{package_prefix}{rel_module}/__init__.py"
                if (
                    candidate_runtime not in python_runtime_files
                    and candidate_init not in python_runtime_files
                ):
                    # The module may already exist on disk but be outside the current patch-plan scope.
                    continue
                target_runtime = (
                    candidate_runtime
                    if candidate_runtime in python_runtime_files
                    else candidate_init
                )
                exported_symbols = runtime_exports_by_path.get(target_runtime, set())
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    if alias.name == rel_module:
                        continue
                    if exported_symbols and alias.name not in exported_symbols:
                        return (
                            None,
                            None,
                            f"package_init imports unknown symbol '{alias.name}' from '.{rel_module}'",
                        )
            if available:
                for node in tree.body:
                    if isinstance(node, ast.Assign):
                        target_names = [
                            t.id for t in node.targets if isinstance(t, ast.Name)
                        ]
                        if "__all__" not in target_names:
                            continue
                        if not isinstance(node.value, (ast.List, ast.Tuple)):
                            return (
                                None,
                                None,
                                "__all__ must be a list/tuple of string exports",
                            )
                        for elt in node.value.elts:
                            if not isinstance(elt, ast.Constant) or not isinstance(
                                elt.value, str
                            ):
                                return (
                                    None,
                                    None,
                                    "__all__ items must be string literals",
                                )
                            if elt.value not in available:
                                return (
                                    None,
                                    None,
                                    f"__all__ contains unknown export '{elt.value}', available: {', '.join(sorted(available))}",
                                )

    return clean_imports, clean_region, None


def _build_project_file_operation(
    *,
    runtime_path: str,
    kind: str,
    imports: list[str],
    region_content: str,
    merge_mode: str,
) -> dict[str, Any]:
    slug = runtime_path.replace("/", "_").replace(".", "_")
    ir_ref = f"ProjectFile.{kind}.{slug}"
    return {
        "operation_type": "upsert_region",
        "ir_ref": ir_ref,
        "plan_rel_path": f"project_file/{kind}",
        "group": _PROJECT_FILE_GROUP,
        "merge_mode": merge_mode,
        "region_start": f"# region {ir_ref}",
        "region_end": f"# endregion {ir_ref}",
        "imports": imports,
        "region_content": region_content,
        "content": f"# region {ir_ref}\n{region_content}\n# endregion {ir_ref}\n",
        "apply_hints": {
            "seams": [],
            "virtual_seams": [],
            "symbols": [],
            "entrypoints": [],
            "suggest_path": runtime_path,
            "create_file_if_missing": True,
            "suggest_reason": "project_file",
        },
    }


def _upsert_operation_by_ir_ref(
    operations: list[dict[str, Any]],
    operation: dict[str, Any],
) -> bool:
    ir_ref = str(operation.get("ir_ref") or "")
    if not ir_ref:
        operations.append(operation)
        return True
    for idx, existing in enumerate(operations):
        if not isinstance(existing, dict):
            continue
        if str(existing.get("ir_ref") or "") == ir_ref:
            if existing == operation:
                return False
            operations[idx] = operation
            return True
    operations.append(operation)
    return True


def generate_project_file_patch_operations(
    *,
    workspace_root: Path,
    config: dict[str, Any],
    context_profile: dict[str, Any],
    manifest: Any,
    patch_plan_operations: dict[str, list[dict[str, Any]]],
) -> tuple[list[str], list[str], list[str]]:
    touched_paths: set[str] = set()
    warnings: list[str] = []
    errors: list[str] = []

    targets = _collect_project_file_targets(
        manifest=manifest,
        patch_plan_operations=patch_plan_operations,
    )

    for target in targets:
        runtime_path = target["runtime_path"]
        kind = target["kind"]
        max_attempts = 3
        raw_max_attempts = (
            config.get("code_gen_project_file_validation_max_attempts", 3)
            if isinstance(config, dict)
            else 3
        )
        try:
            max_attempts = max(1, min(6, int(raw_max_attempts)))
        except (TypeError, ValueError):
            max_attempts = 3
        last_errors: list[str] = []
        last_output_excerpt = ""
        applied = False
        for attempt in range(1, max_attempts + 1):
            context_payload = _build_project_file_context(
                target=target,
                context_profile=context_profile,
                patch_plan_operations=patch_plan_operations,
            )
            context_payload["destination_snapshot"] = _build_runtime_path_preview(
                runtime_path=runtime_path,
                patch_plan_operations=patch_plan_operations,
            )
            if last_errors:
                context_payload["generation_feedback"] = {
                    "previous_errors": list(last_errors),
                    "previous_output_excerpt": last_output_excerpt,
                }
            llm_text, llm_warnings = maybe_generate_project_file_with_llm(
                workspace_root=workspace_root,
                project_kind=kind,
                runtime_path=runtime_path,
                context_payload=context_payload,
                config=config,
                attempt=attempt,
                max_attempts=max_attempts,
                validation_errors=last_errors if attempt > 1 else None,
            )
            warnings.extend(llm_warnings)
            if not llm_text:
                detail = (
                    "; ".join(llm_warnings[-2:]) if llm_warnings else "empty_response"
                )
                last_errors = [f"project_file_llm_failed:{detail}"]
                last_output_excerpt = ""
                continue

            payload = _extract_json_payload(llm_text)
            if payload is None:
                cleaned = llm_text.strip().replace("\r\n", "\n")
                if len(cleaned) > 500:
                    cleaned = cleaned[:500] + "\n...<truncated>..."
                last_errors = [
                    "project_file_invalid_json_output:must return a single JSON object with keys "
                    "merge_mode/imports/region_content"
                ]
                last_output_excerpt = cleaned
                continue

            imports, region_content, err = _validate_project_file_payload(
                runtime_path=runtime_path,
                payload=payload,
                kind=kind,
                context_payload=context_payload,
            )
            if err:
                last_errors = [f"project_file_invalid_payload:{err}"]
                cleaned = llm_text.strip().replace("\r\n", "\n")
                if len(cleaned) > 500:
                    cleaned = cleaned[:500] + "\n...<truncated>..."
                last_output_excerpt = cleaned
                continue

            operation = _build_project_file_operation(
                runtime_path=runtime_path,
                kind=kind,
                imports=imports or [],
                region_content=region_content or "",
                merge_mode=str(payload.get("merge_mode")),
            )
            if _upsert_operation_by_ir_ref(
                patch_plan_operations.setdefault(runtime_path, []),
                operation,
            ):
                touched_paths.add(runtime_path)
            applied = True
            break

        if not applied:
            if last_errors:
                errors.append(f"{runtime_path}:{';'.join(last_errors)}")
            else:
                errors.append(f"{runtime_path}:project_file_generation_failed")

    return sorted(touched_paths), warnings, errors
