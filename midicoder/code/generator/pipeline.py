from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, Callable

from .context_resolver import build_item_context
from .index_manifest import load_index_manifest, resolve_execution_order
from .llm import maybe_generate_with_llm
from .merge import merge_content
from .models import BuildRuntimeCodeResult, MergeAction
from .patch_ops import ApplyBlockedError, apply_upsert_region
from .plan_loader import load_plan_item
from .project_files import generate_project_file_patch_operations, load_context_profile
from .report import write_codegen_report
from .runtime_materializer import materialize_runtime_outputs
from .writer import write_patch_plan_file, write_patches_index


def _normalize_path(path_value: str) -> str:
    return path_value.replace("\\", "/").lstrip("./")


def _runtime_path_to_module(runtime_path: str) -> str:
    normalized = _normalize_path(runtime_path)
    if normalized.endswith(".py"):
        normalized = normalized[:-3]
    return normalized.replace("/", ".")


_DB_MODULE_ALIASES = {
    "app.db",
    "app.database",
    "app.core.database",
}
_CANONICAL_DB_MODULE = "app.shared.db"


def _canonicalize_internal_module(module: str) -> str:
    normalized = str(module or "").strip()
    if normalized in _DB_MODULE_ALIASES:
        return _CANONICAL_DB_MODULE
    return normalized


def _resolve_working_dir(workspace_root: Path, config: dict[str, Any]) -> Path:
    working_dir_value = str(config.get("working_dir", "."))
    working_dir_path = Path(working_dir_value)
    if working_dir_path.is_absolute():
        return working_dir_path
    return (workspace_root / working_dir_path).resolve()


def _collect_existing_app_modules(working_dir: Path) -> set[str]:
    app_root = working_dir / "app"
    if not app_root.exists():
        return set()
    modules: set[str] = set()
    for py_file in app_root.rglob("*.py"):
        rel = py_file.relative_to(working_dir).as_posix()
        modules.add(_runtime_path_to_module(rel))
    return modules


def _module_to_runtime_path(module_name: str) -> str:
    return module_name.replace(".", "/") + ".py"


def _extract_python_exports(content: str) -> list[str]:
    try:
        tree = ast.parse(content)
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
            if (
                isinstance(node.target, ast.Name)
                and node.target.id
                and not node.target.id.startswith("_")
            ):
                exports.add(node.target.id)
    return sorted(exports)


def _collect_existing_symbol_index(working_dir: Path) -> dict[str, list[str]]:
    app_root = working_dir / "app"
    if not app_root.exists():
        return {}
    symbols: dict[str, list[str]] = {}
    for py_file in app_root.rglob("*.py"):
        rel = py_file.relative_to(working_dir).as_posix()
        module = _runtime_path_to_module(rel)
        try:
            content = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        symbols[module] = _extract_python_exports(content)
    return symbols


def _module_allowed(module: str, allowed_modules: set[str]) -> bool:
    module = _canonicalize_internal_module(module)
    if module in allowed_modules:
        return True
    return any(existing.startswith(module + ".") for existing in allowed_modules)


def _collect_missing_internal_modules(
    block: str, *, allowed_modules: set[str]
) -> list[str]:
    import_pattern = re.compile(r"^\s*import\s+(.+)$")
    from_pattern = re.compile(r"^\s*from\s+([A-Za-z_][\w\.]*)\s+import\s+.+$")
    missing: set[str] = set()

    for raw_line in block.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        from_match = from_pattern.match(line)
        if from_match:
            module = _canonicalize_internal_module(from_match.group(1))
            if module.startswith("app.") and not _module_allowed(
                module, allowed_modules
            ):
                missing.add(module)
            continue

        import_match = import_pattern.match(line)
        if not import_match:
            continue
        for chunk in import_match.group(1).split(","):
            token = chunk.strip().split(" as ", 1)[0].strip()
            token = _canonicalize_internal_module(token)
            if token.startswith("app.") and not _module_allowed(token, allowed_modules):
                missing.add(token)
    return sorted(missing)


def _payload_requires_db(payload: dict[str, Any]) -> bool:
    pseudo_struct = payload.get("pseudo_struct") if isinstance(payload, dict) else {}
    if not isinstance(pseudo_struct, dict):
        return False
    dependencies = (
        pseudo_struct.get("dependencies")
        if isinstance(pseudo_struct.get("dependencies"), dict)
        else {}
    )
    if isinstance(dependencies.get("reads"), list) and dependencies.get("reads"):
        return True
    steps = (
        pseudo_struct.get("steps")
        if isinstance(pseudo_struct.get("steps"), list)
        else []
    )
    for step in steps:
        if not isinstance(step, dict):
            continue
        reads = step.get("reads")
        if isinstance(reads, list) and reads:
            return True
        effects = step.get("effects") if isinstance(step.get("effects"), list) else []
        for effect in effects:
            if not isinstance(effect, dict):
                continue
            effect_id = str(effect.get("id", "")).strip().lower()
            if effect_id in {"db.insert", "db.update", "db.delete", "db.upsert"}:
                return True
    return False


def _build_default_db_provider_operation() -> dict[str, Any]:
    ir_ref = "ProjectFile.db_provider.app_shared_db_py"
    region_content = (
        "from collections.abc import Generator\n\n"
        "def get_db() -> Generator[object, None, None]:\n"
        "    raise RuntimeError(\n"
        '        "Database session provider is not configured. Wire SQLAlchemy session in app/shared/db.py"\n'
        "    )\n\n"
        "def get_db_session() -> Generator[object, None, None]:\n"
        "    return get_db()\n"
    )
    return {
        "operation_type": "upsert_region",
        "ir_ref": ir_ref,
        "plan_rel_path": "project_file/db_provider",
        "group": "project_file",
        "merge_mode": "create",
        "region_start": f"# region {ir_ref}",
        "region_end": f"# endregion {ir_ref}",
        "imports": [],
        "region_content": region_content,
        "content": f"# region {ir_ref}\n{region_content}# endregion {ir_ref}\n",
        "apply_hints": {
            "seams": [],
            "virtual_seams": [],
            "symbols": [],
            "entrypoints": [],
            "suggest_path": "app/shared/db.py",
            "create_file_if_missing": True,
            "suggest_reason": "db_provider",
        },
    }


def _load_ir_for_version(workspace_root: Path, version: str) -> dict[str, Any]:
    normalized_version = str(version).strip().strip("/\\")
    ir_path = (
        workspace_root
        / ".midicoder"
        / "versions"
        / normalized_version
        / "irs"
        / "ir.json"
    )
    try:
        if not ir_path.exists():
            return {}
        return json.loads(ir_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _default_db_url_from_datasource(datasource: dict[str, Any] | None) -> str:
    if not isinstance(datasource, dict):
        return "sqlite:///./app.db"

    raw_engine = str(datasource.get("engine") or "").strip().lower()
    if raw_engine in {"postgres", "postgresql"}:
        host = str(datasource.get("host") or "localhost").strip() or "localhost"
        port = int(datasource.get("port") or 5432)
        database = str(datasource.get("database") or "app").strip() or "app"
        return f"postgresql+psycopg://postgres:postgres@{host}:{port}/{database}"
    if raw_engine in {"sqlite", "sqlite3"}:
        database = str(datasource.get("database") or "app.db").strip() or "app.db"
        if database == ":memory:":
            return "sqlite:///:memory:"
        if database.startswith("/"):
            return f"sqlite://{database}"
        return f"sqlite:///./{database}"
    if raw_engine in {"mysql", "mariadb"}:
        host = str(datasource.get("host") or "localhost").strip() or "localhost"
        port = int(datasource.get("port") or 3306)
        database = str(datasource.get("database") or "app").strip() or "app"
        return f"mysql+pymysql://root:root@{host}:{port}/{database}"
    return "sqlite:///./app.db"


def _resolve_default_datasource(ir_payload: dict[str, Any]) -> dict[str, Any] | None:
    persistence = {}
    if isinstance(ir_payload, dict):
        modules = ir_payload.get("modules")
        if isinstance(modules, dict) and isinstance(modules.get("persistence"), dict):
            persistence = modules.get("persistence") or {}
        elif isinstance(ir_payload.get("persistence"), dict):
            persistence = ir_payload.get("persistence") or {}
    datasources = (
        persistence.get("datasources") if isinstance(persistence, dict) else []
    )
    if not isinstance(datasources, list):
        return None
    valid_datasources = [item for item in datasources if isinstance(item, dict)]
    if not valid_datasources:
        return None
    for datasource in valid_datasources:
        if datasource.get("default") is True:
            return datasource
    return valid_datasources[0]


def _build_sqlalchemy_db_provider_operation(
    *, datasource: dict[str, Any] | None = None
) -> dict[str, Any]:
    ir_ref = "ProjectFile.db_provider.app_shared_db_py"
    datasource_id = ""
    if isinstance(datasource, dict):
        datasource_id = str(datasource.get("id") or "").strip()
    source_note = f"# datasource: {datasource_id}\n" if datasource_id else ""
    default_db_url = _default_db_url_from_datasource(datasource)
    region_content = (
        "import os\n"
        "from collections.abc import Generator\n\n"
        "from sqlalchemy import create_engine\n"
        "from sqlalchemy.orm import Session, sessionmaker\n\n"
        f"{source_note}"
        f'DEFAULT_DATABASE_URL = "{default_db_url}"\n'
        'DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)\n\n'
        "_engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)\n"
        "_SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)\n\n"
        "def get_db() -> Generator[Session, None, None]:\n"
        "    db = _SessionLocal()\n"
        "    try:\n"
        "        yield db\n"
        "    finally:\n"
        "        db.close()\n\n"
        "def get_db_session() -> Generator[Session, None, None]:\n"
        "    return get_db()\n"
    )
    return {
        "operation_type": "upsert_region",
        "ir_ref": ir_ref,
        "plan_rel_path": "project_file/db_provider",
        "group": "project_file",
        "merge_mode": "create",
        "region_start": f"# region {ir_ref}",
        "region_end": f"# endregion {ir_ref}",
        "imports": [],
        "region_content": region_content,
        "content": f"# region {ir_ref}\n{region_content}# endregion {ir_ref}\n",
        "apply_hints": {
            "seams": [],
            "virtual_seams": [],
            "symbols": [],
            "entrypoints": [],
            "suggest_path": "app/shared/db.py",
            "create_file_if_missing": True,
            "suggest_reason": "db_provider",
        },
    }


def _get_config_bool(config: dict[str, Any], key: str, default: bool) -> bool:
    value = config.get(key, default)
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "off", "no"}
    return bool(value)


def _get_config_int(
    config: dict[str, Any], key: str, default: int, *, min_value: int, max_value: int
) -> int:
    value = config.get(key, default)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(min_value, min(max_value, parsed))


def _collect_generation_validation_errors(
    *,
    item: Any,
    runtime_path: str,
    block: str,
    allowed_modules: set[str],
    generated_symbol_index: dict[str, list[str]] | None = None,
    existing_symbol_index: dict[str, list[str]] | None = None,
) -> list[str]:
    errors: list[str] = []

    try:
        parsed_block = ast.parse(block)
    except SyntaxError as exc:
        errors.append(f"Invalid Python syntax: {exc.msg}")
        return errors
    has_future_annotations = False
    for top in parsed_block.body:
        if not isinstance(top, ast.ImportFrom):
            continue
        if top.module != "__future__":
            continue
        if any(alias.name == "annotations" for alias in top.names):
            has_future_annotations = True
            break

    missing_modules = _collect_missing_internal_modules(
        block, allowed_modules=allowed_modules
    )
    for module in missing_modules:
        errors.append(f"Missing internal module import: {module}")

    symbol_index = (
        generated_symbol_index if isinstance(generated_symbol_index, dict) else {}
    )
    existing_index = (
        existing_symbol_index if isinstance(existing_symbol_index, dict) else {}
    )
    try:
        tree = ast.parse(block)
    except SyntaxError:
        tree = None
    if tree is not None:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level and node.level > 0:
                continue
            module = node.module or ""
            module = _canonicalize_internal_module(module)
            if not module.startswith("app."):
                continue
            expected_exports = symbol_index.get(module)
            if not isinstance(expected_exports, list) or not expected_exports:
                expected_exports = existing_index.get(module)
            if not isinstance(expected_exports, list) or not expected_exports:
                continue
            exported = {
                name for name in expected_exports if isinstance(name, str) and name
            }
            for alias in node.names:
                if not alias.name or alias.name == "*":
                    continue
                if alias.name not in exported:
                    errors.append(
                        f"Imported symbol '{alias.name}' not found in generated module '{module}'. "
                        f"Available: {', '.join(sorted(exported))}"
                    )

    _, region_content = _parse_operation_block(block=block, ir_ref=str(item.ir_ref))
    region_lines = [
        line.strip() for line in region_content.splitlines() if line.strip()
    ]
    non_comment_lines = [line for line in region_lines if not line.startswith("#")]
    lowered = region_content.lower()

    if not non_comment_lines:
        errors.append("Region content is empty.")
    elif len(non_comment_lines) == 1 and non_comment_lines[0] in {
        "pass",
        "...",
        "raise NotImplementedError",
        "raise NotImplementedError()",
    }:
        errors.append("Region content is placeholder-only.")

    if "todo" in lowered or "fixme" in lowered:
        errors.append("Region content contains TODO/FIXME placeholders.")

    payload = item.payload if isinstance(item.payload, dict) else {}
    pseudo_struct = (
        payload.get("pseudo_struct")
        if isinstance(payload.get("pseudo_struct"), dict)
        else {}
    )
    intent = (
        pseudo_struct.get("intent")
        if isinstance(pseudo_struct.get("intent"), dict)
        else {}
    )
    intent_kind = str(intent.get("kind") or "").strip().lower()
    integration_contract = (
        payload.get("integration_contract")
        if isinstance(payload.get("integration_contract"), dict)
        else {}
    )

    if runtime_path.endswith("/controller.py"):
        route_contract = integration_contract.get("route_handler_contract")
        has_routes = isinstance(route_contract, list) and bool(route_contract)
        if has_routes and "@router." not in region_content:
            errors.append(
                "Controller with route contract must contain @router decorators."
            )
        if has_routes:
            for route in route_contract:
                if not isinstance(route, dict):
                    continue
                handler_symbol = route.get("handler_symbol")
                if not isinstance(handler_symbol, str) or not handler_symbol.strip():
                    continue
                if not re.search(
                    rf"\b(?:async\s+def|def)\s+{re.escape(handler_symbol)}\b",
                    region_content,
                ):
                    errors.append(f"Missing route handler function: {handler_symbol}")

    service_signature = (
        integration_contract.get("service_signature")
        if isinstance(integration_contract.get("service_signature"), dict)
        else {}
    )
    service_name = (
        service_signature.get("name") if isinstance(service_signature, dict) else None
    )
    if (
        runtime_path.endswith("/service.py")
        and isinstance(service_name, str)
        and service_name.strip()
    ):
        if not re.search(
            rf"\b(?:async\s+def|def)\s+{re.escape(service_name)}\b", region_content
        ):
            errors.append(f"Missing service function: {service_name}")

    if (
        runtime_path.endswith("/model.py") or intent_kind == "model"
    ) and "class " not in region_content:
        errors.append("Model target should define at least one class.")

    if runtime_path.endswith("/model.py"):
        for top in parsed_block.body:
            if not isinstance(top, ast.ImportFrom):
                continue
            if str(top.module or "").strip() != "time":
                continue
            if any(str(alias.name or "").strip() == "time" for alias in top.names):
                errors.append(
                    "Model must not import `time` from stdlib `time` module for field types; "
                    "use `datetime.time` instead."
                )
                break
        try:
            model_tree = ast.parse(region_content)
        except SyntaxError:
            model_tree = None
        if model_tree is not None:
            for node in ast.walk(model_tree):
                if not isinstance(node, ast.AnnAssign):
                    continue
                if not isinstance(node.target, ast.Name):
                    continue
                target_name = str(node.target.id or "").strip()
                if not target_name:
                    continue
                ann = node.annotation
                if (
                    isinstance(ann, ast.Name)
                    and str(ann.id or "").strip() == target_name
                    and target_name == "date"
                    and not has_future_annotations
                ):
                    errors.append(
                        f"Model field '{target_name}: {target_name}' is unsafe for runtime evaluation; "
                        "use fully-qualified type or postpone annotations."
                    )

    # Enforce real persistence implementation for DB-related command/query flows.
    db_required = False
    dependencies = (
        pseudo_struct.get("dependencies")
        if isinstance(pseudo_struct.get("dependencies"), dict)
        else {}
    )
    if isinstance(dependencies.get("reads"), list) and dependencies.get("reads"):
        db_required = True
    steps = (
        pseudo_struct.get("steps")
        if isinstance(pseudo_struct.get("steps"), list)
        else []
    )
    for step in steps:
        if not isinstance(step, dict):
            continue
        effects = step.get("effects") if isinstance(step.get("effects"), list) else []
        for effect in effects:
            if not isinstance(effect, dict):
                continue
            effect_id = str(effect.get("id", "")).strip().lower()
            if effect_id in {"db.insert", "db.update", "db.delete", "db.upsert"}:
                db_required = True
                break
        if db_required:
            break

    if db_required:
        forbidden_markers = (
            "simulated repository",
            "in a real implementation",
            "mock repository",
        )
        lowered_region = region_content.lower()
        for marker in forbidden_markers:
            if marker in lowered_region:
                errors.append(
                    "DB contract requires real persistence logic, but simulated/mock wording was detected."
                )
                break

        persistence_patterns = (
            r"\bsession\b",
            r"\bget_db\b",
            r"\basync_session\b",
            r"\brepository\.[a-z_]",
            r"\brepo\.[a-z_]",
            r"\bquery\(",
            r"\bselect\(",
            r"\binsert\(",
            r"\bupdate\(",
            r"\bdelete\(",
            r"\bexecute\(",
            r"\bsqlalchemy\b",
        )
        has_persistence_signal = any(
            re.search(pattern, lowered_region) for pattern in persistence_patterns
        )
        if not has_persistence_signal:
            errors.append(
                "DB contract requires concrete persistence code (repository/session/ORM), but no persistence signal was found."
            )
        if (
            "return [" in region_content or "return {" in region_content
        ) and not has_persistence_signal:
            errors.append(
                "Likely in-memory stub detected for DB flow (hardcoded return collection without persistence)."
            )

    # Validate type mismatches against pseudo_struct schemas (without hardcoded business rules).
    api_struct = (
        pseudo_struct.get("api") if isinstance(pseudo_struct.get("api"), dict) else {}
    )
    routes = (
        api_struct.get("routes") if isinstance(api_struct.get("routes"), list) else []
    )
    string_fields: set[str] = set()
    for route in routes:
        if not isinstance(route, dict):
            continue
        request_schema = (
            route.get("request_schema")
            if isinstance(route.get("request_schema"), list)
            else []
        )
        response_schema = (
            route.get("response_schema")
            if isinstance(route.get("response_schema"), list)
            else []
        )
        for field in request_schema + response_schema:
            if not isinstance(field, dict):
                continue
            name = field.get("name")
            ftype = str(field.get("type") or "").strip().lower()
            if isinstance(name, str) and name and ftype == "string":
                string_fields.add(name)
    if string_fields:
        try:
            tree = ast.parse(region_content)
        except SyntaxError:
            tree = None
        if tree is not None:
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                for kw in node.keywords:
                    if (
                        not isinstance(kw, ast.keyword)
                        or not kw.arg
                        or kw.arg not in string_fields
                    ):
                        continue
                    if isinstance(kw.value, ast.Constant) and not isinstance(
                        kw.value.value, str
                    ):
                        errors.append(
                            f"Field '{kw.arg}' is string by contract but assigned non-string literal."
                        )
    return sorted(set(errors))


def _collect_module_imports(content: str) -> set[str]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return set()
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = str(alias.name or "").strip()
                if module.startswith("app."):
                    imports.add(_canonicalize_internal_module(module))
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            module = str(node.module or "").strip()
            if module.startswith("app."):
                imports.add(_canonicalize_internal_module(module))
    return imports


def _detect_internal_import_cycle(
    *,
    patch_preview_cache: dict[str, str],
    runtime_path: str,
    candidate_block: str,
) -> list[str]:
    module_to_imports: dict[str, set[str]] = {}
    for path, content in patch_preview_cache.items():
        normalized = _normalize_path(path)
        if not normalized.endswith(".py"):
            continue
        module_to_imports[_runtime_path_to_module(normalized)] = (
            _collect_module_imports(content)
        )

    candidate_module = _runtime_path_to_module(runtime_path)
    module_to_imports[candidate_module] = _collect_module_imports(candidate_block)

    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []
    cycles: list[list[str]] = []

    def _dfs(module: str) -> None:
        visiting.add(module)
        stack.append(module)
        for dep in module_to_imports.get(module, set()):
            if dep not in module_to_imports:
                continue
            if dep in visiting:
                if dep in stack:
                    idx = stack.index(dep)
                    cycles.append(stack[idx:] + [dep])
                continue
            if dep in visited:
                continue
            _dfs(dep)
        stack.pop()
        visiting.remove(module)
        visited.add(module)

    for module in sorted(module_to_imports):
        if module in visited:
            continue
        _dfs(module)

    if not cycles:
        return []

    cycle_paths: list[str] = []
    for cycle in cycles:
        normalized = " -> ".join(cycle)
        if normalized not in cycle_paths:
            cycle_paths.append(normalized)
    return cycle_paths


def _sanitize_hint_entry(
    entry: dict[str, Any], *, max_keys: int = 12
) -> dict[str, Any]:
    preferred = [
        "id",
        "name",
        "type",
        "path",
        "file",
        "file_path",
        "runtime_path",
        "target",
        "target_path",
        "module",
        "module_path",
        "symbol",
        "symbol_name",
        "ir_ref",
        "applies_to",
        "owner",
        "owners",
    ]
    out: dict[str, Any] = {}
    for key in preferred:
        if key in entry and len(out) < max_keys:
            value = entry.get(key)
            if isinstance(value, (str, int, float, bool)) or value is None:
                out[key] = value
            elif isinstance(value, list):
                out[key] = [x for x in value if isinstance(x, (str, int, float, bool))]
    if len(out) < max_keys:
        for key, value in entry.items():
            if key in out:
                continue
            if len(out) >= max_keys:
                break
            if isinstance(value, (str, int, float, bool)) or value is None:
                out[key] = value
    return out


def _match_hint_entry(entry: dict[str, Any], *, runtime_path: str, ir_ref: str) -> bool:
    runtime_norm = _normalize_path(runtime_path)
    path_keys = [
        "path",
        "file",
        "file_path",
        "runtime_path",
        "target",
        "target_path",
        "module_path",
    ]
    for key in path_keys:
        value = entry.get(key)
        if isinstance(value, str):
            value_norm = _normalize_path(value)
            if value_norm == runtime_norm or value_norm.endswith(runtime_norm):
                return True

    ir_keys = ["ir_ref", "owner", "applies_to", "name", "id", "symbol", "symbol_name"]
    for key in ir_keys:
        value = entry.get(key)
        if isinstance(value, str) and (value == ir_ref or ir_ref in value):
            return True
        if isinstance(value, list) and ir_ref in value:
            return True

    owners = entry.get("owners")
    if isinstance(owners, list) and any(
        isinstance(x, str) and x == ir_ref for x in owners
    ):
        return True
    return False


def _collect_context_hints(
    *,
    context: dict[str, Any],
    runtime_path: str,
    ir_ref: str,
    limit_per_source: int = 20,
) -> dict[str, list[dict[str, Any]]]:
    sources = ("seams", "virtual_seams", "symbols", "entrypoints")
    hints: dict[str, Any] = {}
    for source in sources:
        raw = context.get(source)
        entries: list[dict[str, Any]] = []
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict):
                    continue
                if _match_hint_entry(item, runtime_path=runtime_path, ir_ref=ir_ref):
                    entries.append(_sanitize_hint_entry(item))
                if len(entries) >= limit_per_source:
                    break
        hints[source] = entries
    has_virtual_seam = bool(hints.get("virtual_seams"))
    hints["suggest_path"] = runtime_path
    hints["create_file_if_missing"] = not has_virtual_seam
    hints["suggest_reason"] = (
        "no_virtual_seam_match" if not has_virtual_seam else "virtual_seam_available"
    )
    return hints


def _parse_operation_block(*, block: str, ir_ref: str) -> tuple[list[str], str]:
    normalized = block.replace("\r\n", "\n").strip()
    lines = normalized.split("\n")
    start_marker = f"# region {ir_ref}"
    end_marker = f"# endregion {ir_ref}"

    if lines and lines[0].strip() == start_marker:
        lines = lines[1:]
    if lines and lines[-1].strip() == end_marker:
        lines = lines[:-1]

    import_pattern = re.compile(r"^(from\s+\S+\s+import\s+.+|import\s+.+)$")
    imports: list[str] = []
    body_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if import_pattern.match(stripped):
            imports.append(stripped)
            continue
        body_lines.append(line.rstrip())

    region_content = "\n".join(body_lines).strip()
    if not region_content:
        region_content = "__all__: list[str] = []"
    return imports, region_content


def _ensure_model_future_annotations(
    block: str, *, runtime_path: str, ir_ref: str
) -> str:
    if not runtime_path.endswith("/model.py"):
        return block
    if "from __future__ import annotations" in block:
        return block
    start_marker = f"# region {ir_ref}"
    lines = block.replace("\r\n", "\n").split("\n")
    if lines and lines[0].strip() == start_marker:
        return "\n".join([lines[0], "from __future__ import annotations"] + lines[1:])
    return "from __future__ import annotations\n" + block


def _normalize_model_annotation_collisions(
    block: str, *, runtime_path: str, ir_ref: str
) -> str:
    if not runtime_path.endswith("/model.py"):
        return block
    imports, region_content = _parse_operation_block(block=block, ir_ref=ir_ref)
    try:
        region_tree = ast.parse(region_content)
    except SyntaxError:
        return block

    collisions: set[str] = set()
    for node in ast.walk(region_tree):
        if not isinstance(node, ast.AnnAssign):
            continue
        if not isinstance(node.target, ast.Name):
            continue
        target_name = str(node.target.id or "").strip()
        if not target_name:
            continue
        if isinstance(node.annotation, ast.Name):
            ann_name = str(node.annotation.id or "").strip()
            if ann_name and ann_name == target_name and ann_name == "date":
                collisions.add(ann_name)
    if not collisions:
        return block

    rewritten_imports: list[str] = []
    for line in imports:
        try:
            stmt = ast.parse(line).body[0]
        except SyntaxError:
            rewritten_imports.append(line)
            continue
        if isinstance(stmt, ast.ImportFrom):
            changed = False
            for alias in stmt.names:
                if alias.name in collisions and not alias.asname:
                    alias.asname = f"{alias.name}_type"
                    changed = True
            if changed:
                module = "." * int(stmt.level or 0) + (stmt.module or "")
                names_text = ", ".join(
                    alias.name + (f" as {alias.asname}" if alias.asname else "")
                    for alias in stmt.names
                )
                rewritten_imports.append(f"from {module} import {names_text}")
                continue
        rewritten_imports.append(line)

    rewritten_region = region_content
    for name in collisions:
        alias = f"{name}_type"
        rewritten_region = re.sub(
            rf"(:[ \t]*){re.escape(name)}(\b)",
            rf"\g<1>{alias}\g<2>",
            rewritten_region,
        )

    out_lines: list[str] = [f"# region {ir_ref}"]
    out_lines.extend(rewritten_imports)
    if rewritten_imports and rewritten_region.strip():
        out_lines.append("")
    out_lines.append(rewritten_region.strip())
    out_lines.append(f"# endregion {ir_ref}")
    return "\n".join(out_lines).rstrip() + "\n"


def _build_region_block(*, ir_ref: str, region_content: str) -> str:
    return f"# region {ir_ref}\n{region_content.rstrip()}\n# endregion {ir_ref}\n"


def _build_patch_plan_payload(
    *,
    version: str,
    stack: str,
    runtime_path: str,
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "2.0.0",
        "version": version,
        "stack": stack,
        "runtime_path": runtime_path,
        "operations": operations,
    }


def _build_patch_plan_targets(
    *,
    patch_plan_operations: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for runtime_path in sorted(patch_plan_operations):
        operations = patch_plan_operations[runtime_path]
        targets.append(
            {
                "runtime_path": runtime_path,
                "patch_plan_file": (
                    f"{runtime_path[:-3].replace('/', '.')}.patch-plan.json"
                    if runtime_path.endswith(".py")
                    else f"{runtime_path.replace('/', '.')}.patch-plan.json"
                ),
                "operation_count": len(operations),
                "ir_refs": [
                    str(op.get("ir_ref")) for op in operations if op.get("ir_ref")
                ],
            }
        )
    return targets


def _flush_patch_plan_files(
    *,
    patches_root: Path,
    version: str,
    stack: str,
    patch_plan_operations: dict[str, list[dict[str, Any]]],
    generated_patch_plans: list[str],
    generated_patch_plan_set: set[str],
) -> None:
    for runtime_path, operations in patch_plan_operations.items():
        payload = _build_patch_plan_payload(
            version=version,
            stack=stack,
            runtime_path=runtime_path,
            operations=operations,
        )
        patch_plan_path = write_patch_plan_file(
            patches_root=patches_root,
            runtime_path=runtime_path,
            payload=payload,
        )
        rel_patch_plan_path = str(Path(patch_plan_path).relative_to(patches_root))
        if rel_patch_plan_path not in generated_patch_plan_set:
            generated_patch_plan_set.add(rel_patch_plan_path)
            generated_patch_plans.append(patch_plan_path)


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
            merged = dict(existing)
            old_imports = (
                existing.get("imports")
                if isinstance(existing.get("imports"), list)
                else []
            )
            new_imports = (
                operation.get("imports")
                if isinstance(operation.get("imports"), list)
                else []
            )
            # Preserve import lines exactly as emitted by LLM; do not normalize or deduplicate.
            merged["imports"] = [x for x in old_imports if isinstance(x, str)] + [
                x for x in new_imports if isinstance(x, str)
            ]

            old_region = str(existing.get("region_content") or "").strip()
            new_region = str(operation.get("region_content") or "").strip()
            if (
                old_region
                and new_region
                and old_region != new_region
                and old_region not in new_region
            ):
                merged_region = f"{old_region}\n\n{new_region}"
            else:
                merged_region = new_region or old_region
            merged["region_content"] = merged_region

            region_start = str(
                operation.get("region_start")
                or existing.get("region_start")
                or f"# region {ir_ref}"
            )
            region_end = str(
                operation.get("region_end")
                or existing.get("region_end")
                or f"# endregion {ir_ref}"
            )
            merged["region_start"] = region_start
            merged["region_end"] = region_end
            merged["content"] = f"{region_start}\n{merged_region}\n{region_end}\n"
            for key in (
                "operation_type",
                "plan_rel_path",
                "group",
                "merge_mode",
                "apply_hints",
            ):
                if key in operation:
                    merged[key] = operation[key]
            operations[idx] = merged
            return True
    operations.append(operation)
    return True


def _write_patch_plan_for_runtime_path(
    *,
    patches_root: Path,
    version: str,
    stack: str,
    patch_plan_operations: dict[str, list[dict[str, Any]]],
    runtime_path: str,
    generated_patch_plans: list[str],
    generated_patch_plan_set: set[str],
) -> None:
    operations = patch_plan_operations.get(runtime_path)
    if not operations:
        return
    payload = _build_patch_plan_payload(
        version=version,
        stack=stack,
        runtime_path=runtime_path,
        operations=operations,
    )
    patch_plan_path = write_patch_plan_file(
        patches_root=patches_root,
        runtime_path=runtime_path,
        payload=payload,
    )
    rel_patch_plan_path = str(Path(patch_plan_path).relative_to(patches_root))
    if rel_patch_plan_path not in generated_patch_plan_set:
        generated_patch_plan_set.add(rel_patch_plan_path)
        generated_patch_plans.append(patch_plan_path)


def build_runtime_code(
    *,
    workspace_root: Path,
    version: str,
    plans_dir: Path,
    patches_root: Path,
    generator_version: str,
    config: dict[str, Any] | None = None,
    progress_callback: Callable[[str], None] | None = None,
    runtime_enabled: bool = False,
) -> BuildRuntimeCodeResult:
    def _progress(message: str) -> None:
        if progress_callback is not None:
            progress_callback(message)

    _ = generator_version
    cfg = config or {}
    context_profile = load_context_profile(workspace_root)
    working_dir = _resolve_working_dir(workspace_root, cfg)
    existing_internal_modules = _collect_existing_app_modules(working_dir)
    existing_symbol_index = _collect_existing_symbol_index(working_dir)
    _progress("Loading plan index manifest...")
    manifest = load_index_manifest(plans_dir)
    ordered_refs = resolve_execution_order(manifest)
    _progress(f"Resolved execution order with {len(ordered_refs)} plan items")

    patches_root.mkdir(parents=True, exist_ok=True)
    runtime_root = patches_root / "runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    errors: list[str] = []
    execution_order: list[str] = []
    merge_actions: list[MergeAction] = []
    generated_patch_plans: list[str] = []
    generated_patch_plan_set: set[str] = set()
    generated_runtime_files: list[str] = []

    stack = "fastapi"
    patch_preview_cache: dict[str, str] = {}
    patch_plan_operations: dict[str, list[dict[str, Any]]] = {}
    planned_runtime_modules: set[str] = set()
    ir_payload = _load_ir_for_version(workspace_root, version)
    default_datasource = _resolve_default_datasource(ir_payload)
    db_required_for_version = False
    for ref in ordered_refs:
        item_preview = load_plan_item(plans_dir, ref, manifest)
        if _payload_requires_db(item_preview.payload):
            db_required_for_version = True
        for runtime_path in item_preview.runtime_paths:
            planned_runtime_modules.add(_runtime_path_to_module(runtime_path))
    if manifest.bootstrap_entrypoint:
        bootstrap_path_preview = manifest.bootstrap_entrypoint.replace("\\", "/")
        if not bootstrap_path_preview.startswith("app/"):
            bootstrap_path_preview = f"app/{bootstrap_path_preview.lstrip('/')}"
        planned_runtime_modules.add(_runtime_path_to_module(bootstrap_path_preview))
    if db_required_for_version:
        planned_runtime_modules.add(_CANONICAL_DB_MODULE)
    allowed_internal_modules = existing_internal_modules | planned_runtime_modules

    if db_required_for_version:
        db_runtime_path = _module_to_runtime_path(_CANONICAL_DB_MODULE)
        db_operation = _build_sqlalchemy_db_provider_operation(
            datasource=default_datasource
        )
        if _upsert_operation_by_ir_ref(
            patch_plan_operations.setdefault(db_runtime_path, []),
            db_operation,
        ):
            _write_patch_plan_for_runtime_path(
                patches_root=patches_root,
                version=version,
                stack=stack,
                patch_plan_operations=patch_plan_operations,
                runtime_path=db_runtime_path,
                generated_patch_plans=generated_patch_plans,
                generated_patch_plan_set=generated_patch_plan_set,
            )
            try:
                preview_content, _ = apply_upsert_region(
                    current_content=patch_preview_cache.get(db_runtime_path, ""),
                    operation=db_operation,
                    force=True,
                    allow_patch_create=True,
                )
                patch_preview_cache[db_runtime_path] = preview_content
            except ApplyBlockedError:
                pass

    for idx, ref in enumerate(ordered_refs, start=1):
        item = load_plan_item(plans_dir, ref, manifest)
        _progress(f"[{idx}/{len(ordered_refs)}] Processing {item.ir_ref}")
        execution_order.append(item.ir_ref)

        for runtime_path in item.runtime_paths:
            preview_outputs = dict(patch_preview_cache)
            context = build_item_context(
                workspace_root=workspace_root,
                version=version,
                plan_item=item,
                patches_root=runtime_root,
                current_outputs=preview_outputs,
            )
            context["allowed_internal_modules"] = sorted(allowed_internal_modules)
            context["existing_internal_modules"] = sorted(existing_internal_modules)
            _progress(f"  -> Building patch-plan op for: {runtime_path}")
            use_llm = _get_config_bool(cfg, "code_gen_use_llm", True)
            validation_enabled = _get_config_bool(
                cfg, "code_gen_validate_and_regen", True
            )
            max_attempts = _get_config_int(
                cfg,
                "code_gen_validation_max_attempts",
                3,
                min_value=1,
                max_value=6,
            )
            if not validation_enabled:
                max_attempts = 1

            if not use_llm:
                error_message = f"{item.ir_ref}:{runtime_path}:code-plan generation requires LLM (code_gen_use_llm=true)"
                errors.append(error_message)
                _progress(f"     ERROR: {error_message}")
                continue

            llm_content: str | None = None
            last_validation_errors: list[str] = []
            llm_returned_any_content = False
            for attempt in range(1, max_attempts + 1):
                candidate, llm_warnings = maybe_generate_with_llm(
                    workspace_root=workspace_root,
                    plan_item=item,
                    context=context,
                    runtime_path=runtime_path,
                    config=cfg,
                    attempt=attempt,
                    max_attempts=max_attempts,
                    validation_errors=last_validation_errors if attempt > 1 else None,
                )
                warnings.extend(llm_warnings)
                if llm_warnings:
                    _progress(f"     LLM warnings: {len(llm_warnings)}")
                if not candidate:
                    continue

                candidate = _ensure_model_future_annotations(
                    candidate,
                    runtime_path=runtime_path,
                    ir_ref=str(item.ir_ref),
                )
                candidate = _normalize_model_annotation_collisions(
                    candidate,
                    runtime_path=runtime_path,
                    ir_ref=str(item.ir_ref),
                )
                llm_returned_any_content = True
                validation_errors = _collect_generation_validation_errors(
                    item=item,
                    runtime_path=runtime_path,
                    block=candidate,
                    allowed_modules=allowed_internal_modules,
                    generated_symbol_index=context.get("generated_symbol_index"),
                    existing_symbol_index=existing_symbol_index,
                )
                cycle_paths = _detect_internal_import_cycle(
                    patch_preview_cache=patch_preview_cache,
                    runtime_path=runtime_path,
                    candidate_block=candidate,
                )
                for cycle in cycle_paths:
                    validation_errors.append(
                        f"Circular internal import detected: {cycle}"
                    )
                if not validation_errors:
                    llm_content = candidate
                    last_validation_errors = []
                    break

                last_validation_errors = validation_errors
                warnings.append(
                    f"{item.ir_ref}:{runtime_path}:attempt {attempt}/{max_attempts} failed validation: "
                    + "; ".join(validation_errors)
                )
                if attempt < max_attempts:
                    _progress(
                        f"     Validation failed; regenerating ({attempt + 1}/{max_attempts})"
                    )

            if llm_content:
                block = llm_content
            else:
                if llm_returned_any_content and last_validation_errors:
                    error_message = (
                        f"{item.ir_ref}:{runtime_path}:validation_failed_after_{max_attempts}_attempts: "
                        + "; ".join(last_validation_errors)
                    )
                else:
                    error_message = f"{item.ir_ref}:{runtime_path}:LLM generation failed; no deterministic fallback"
                errors.append(error_message)
                _progress(f"     ERROR: {error_message}")
                continue
            touched_patch_paths: set[str] = set()
            imports, region_content = _parse_operation_block(
                block=block, ir_ref=item.ir_ref
            )
            canonical_block = _build_region_block(
                ir_ref=item.ir_ref, region_content=region_content
            )

            main_operation = {
                "operation_type": "upsert_region",
                "ir_ref": item.ir_ref,
                "plan_rel_path": item.rel_path,
                "group": item.group,
                "merge_mode": item.merge_mode,
                "region_start": f"# region {item.ir_ref}",
                "region_end": f"# endregion {item.ir_ref}",
                "imports": imports,
                "region_content": region_content,
                # legacy key for backward compatibility
                "content": canonical_block,
                "apply_hints": _collect_context_hints(
                    context=context,
                    runtime_path=runtime_path,
                    ir_ref=item.ir_ref,
                ),
            }
            if _upsert_operation_by_ir_ref(
                patch_plan_operations.setdefault(runtime_path, []),
                main_operation,
            ):
                touched_patch_paths.add(runtime_path)

            for touched_runtime_path in sorted(touched_patch_paths):
                _write_patch_plan_for_runtime_path(
                    patches_root=patches_root,
                    version=version,
                    stack=stack,
                    patch_plan_operations=patch_plan_operations,
                    runtime_path=touched_runtime_path,
                    generated_patch_plans=generated_patch_plans,
                    generated_patch_plan_set=generated_patch_plan_set,
                )

            try:
                preview_content, _ = apply_upsert_region(
                    current_content=patch_preview_cache.get(runtime_path, ""),
                    operation=main_operation,
                    force=True,
                    allow_patch_create=True,
                )
                patch_preview_cache[runtime_path] = preview_content
            except ApplyBlockedError:
                preview_merged = merge_content(
                    runtime_path=runtime_path,
                    existing=patch_preview_cache.get(runtime_path),
                    block=canonical_block,
                    ir_ref=item.ir_ref,
                    mode=item.merge_mode,
                )
                if preview_merged.status in {"created", "updated", "noop"}:
                    patch_preview_cache[runtime_path] = preview_merged.content
                else:
                    previous = patch_preview_cache.get(runtime_path, "")
                    patch_preview_cache[runtime_path] = (
                        previous + "\n" + block
                    ).strip() + "\n"

    (
        project_touched_paths,
        project_warnings,
        project_errors,
    ) = generate_project_file_patch_operations(
        workspace_root=workspace_root,
        config=cfg,
        context_profile=context_profile,
        manifest=manifest,
        patch_plan_operations=patch_plan_operations,
    )
    warnings.extend(project_warnings)
    if project_errors:
        for message in project_errors:
            errors.append(f"ProjectFile:{message}")
            _progress(f"     ERROR: ProjectFile:{message}")
    for touched_runtime_path in project_touched_paths:
        _write_patch_plan_for_runtime_path(
            patches_root=patches_root,
            version=version,
            stack=stack,
            patch_plan_operations=patch_plan_operations,
            runtime_path=touched_runtime_path,
            generated_patch_plans=generated_patch_plans,
            generated_patch_plan_set=generated_patch_plan_set,
        )

    _flush_patch_plan_files(
        patches_root=patches_root,
        version=version,
        stack=stack,
        patch_plan_operations=patch_plan_operations,
        generated_patch_plans=generated_patch_plans,
        generated_patch_plan_set=generated_patch_plan_set,
    )

    if runtime_enabled:
        _progress("Materializing runtime outputs...")
        runtime_outputs, runtime_errors = materialize_runtime_outputs(
            patches_root=patches_root,
            patch_plan_operations=patch_plan_operations,
        )
        generated_runtime_files.extend(runtime_outputs)
        errors.extend(runtime_errors)

    _progress("Writing patches index...")
    patch_plan_targets = _build_patch_plan_targets(
        patch_plan_operations=patch_plan_operations
    )
    index_path = write_patches_index(
        patches_root=patches_root,
        version=version,
        stack=stack,
        generated_patch_plans=[
            str(Path(x).relative_to(patches_root)) for x in generated_patch_plans
        ],
        patch_plan_targets=patch_plan_targets,
        runtime_enabled=runtime_enabled,
        generated_runtime_files=[
            str(Path(x).relative_to(patches_root)) for x in generated_runtime_files
        ],
        execution_order=execution_order,
    )
    _progress("Writing code generation report...")
    report_path = write_codegen_report(
        patches_root=patches_root,
        version=version,
        stack=stack,
        runtime_enabled=runtime_enabled,
        generated_patch_plans=[
            str(Path(x).relative_to(patches_root)) for x in generated_patch_plans
        ],
        generated_runtime_files=[
            str(Path(x).relative_to(patches_root)) for x in generated_runtime_files
        ],
        warnings=warnings,
        errors=errors,
        execution_order=execution_order,
        merge_actions=merge_actions,
    )

    return BuildRuntimeCodeResult(
        generated_patch_plans=sorted(
            set(str(Path(x).relative_to(patches_root)) for x in generated_patch_plans)
        ),
        generated_runtime_files=sorted(
            set(str(Path(x).relative_to(patches_root)) for x in generated_runtime_files)
        ),
        runtime_enabled=runtime_enabled,
        generated_items=len(execution_order),
        warnings=warnings,
        errors=errors,
        report_path=report_path,
        index_path=index_path,
        merge_actions=merge_actions,
    )
