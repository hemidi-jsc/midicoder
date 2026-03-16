from __future__ import annotations

import ast
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..generator.patch_ops import ApplyBlockedError, apply_upsert_region
from .backup import BackupSnapshot, create_backup, restore_backup
from .loader import load_apply_queue
from .models import ApplyFileResult, ApplyOptions, ApplySummary, LoadedPatchPlan
from .report import write_apply_report


def _normalize_runtime_path(path_value: str) -> str:
    return path_value.replace("\\", "/").lstrip("./")


def _format_error(runtime_path: str, ir_ref: str, error_code: str, message: str) -> str:
    return f"{runtime_path}:{ir_ref}:{error_code}:{message}"


def _get_config_bool(config: dict[str, Any], key: str, default: bool) -> bool:
    value = config.get(key, default)
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "off", "no"}
    return bool(value)


def _reindex_changed_paths(
    *,
    workspace_root: Path,
    working_dir: Path,
    changed_paths: list[str],
) -> None:
    from midicoder.context.indexer import build_context

    if not changed_paths:
        return
    build_context(
        root=working_dir,
        context_root=workspace_root,
        refresh=True,
        reindex_only_changed=True,
        changed_paths=changed_paths,
    )


def _should_reset_runtime_content(
    *,
    runtime_path: str,
    target: LoadedPatchPlan,
    options: ApplyOptions,
) -> bool:
    if not options.reset_target_files:
        return False
    normalized = _normalize_runtime_path(runtime_path)
    if normalized == "requirements.txt":
        return True
    if normalized.startswith("app/") and target.operations:
        if all(str(op.get("group") or "") == "project_file" for op in target.operations if isinstance(op, dict)):
            return True
    return False


def _runtime_path_to_module(runtime_path: str) -> str:
    normalized = _normalize_runtime_path(runtime_path)
    if normalized.endswith(".py"):
        normalized = normalized[:-3]
    return normalized.replace("/", ".")


def _collect_internal_imports(content: str) -> set[str]:
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
                    imports.add(module)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            module = str(node.module or "").strip()
            if module.startswith("app."):
                imports.add(module)
    return imports


def _detect_import_cycles(module_to_imports: dict[str, set[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []
    cycles: list[str] = []

    def _dfs(module: str) -> None:
        visiting.add(module)
        stack.append(module)
        for dep in module_to_imports.get(module, set()):
            if dep not in module_to_imports:
                continue
            if dep in visiting:
                if dep in stack:
                    idx = stack.index(dep)
                    cycle = " -> ".join(stack[idx:] + [dep])
                    if cycle not in cycles:
                        cycles.append(cycle)
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
    return cycles


def _validate_post_apply_import_graph(*, working_dir: Path, changed_paths: list[str]) -> list[str]:
    seed_modules = sorted(
        {
            _runtime_path_to_module(path)
            for path in changed_paths
            if _normalize_runtime_path(path).endswith(".py")
        }
    )
    if not seed_modules:
        return []

    module_to_imports: dict[str, set[str]] = {}
    pending = list(seed_modules)
    seen: set[str] = set()
    while pending:
        module = pending.pop()
        if module in seen:
            continue
        seen.add(module)
        runtime_path = module.replace(".", "/") + ".py"
        package_init_path = module.replace(".", "/") + "/__init__.py"
        abs_path = (working_dir / runtime_path).resolve()
        if not abs_path.exists():
            abs_path = (working_dir / package_init_path).resolve()
            runtime_path = package_init_path
        if not abs_path.exists():
            continue
        try:
            content = abs_path.read_text(encoding="utf-8")
        except OSError as exc:
            return [_format_error(runtime_path, "post_apply", "file_read_error", str(exc))]
        imports = _collect_internal_imports(content)
        module_to_imports[module] = imports
        for dep in imports:
            if dep not in seen:
                pending.append(dep)

    cycles = _detect_import_cycles(module_to_imports)
    return [
        _format_error("*", "post_apply", "circular_import", cycle)
        for cycle in cycles
    ]


def _run_smoke_import_main(*, working_dir: Path) -> str | None:
    app_main = working_dir / "app" / "main.py"
    if not app_main.exists():
        return None
    completed = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=str(working_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0:
        return None
    detail = (completed.stderr or completed.stdout or "").strip()
    missing_match = re.search(r"ModuleNotFoundError:\s+No module named ['\"]([^'\"]+)['\"]", detail)
    if missing_match:
        missing_module = str(missing_match.group(1) or "").strip()
        if missing_module and not missing_module.startswith("app"):
            return None
    if len(detail) > 500:
        detail = detail[:500] + "...<truncated>"
    return _format_error("*", "post_apply", "smoke_import_failed", detail or "import app.main failed")


def _apply_single_patch_plan(
    *,
    target: LoadedPatchPlan,
    options: ApplyOptions,
    backup_root: Path,
) -> ApplyFileResult:
    runtime_path = _normalize_runtime_path(target.runtime_path)
    target_path = (options.working_dir / runtime_path).resolve()
    current_content = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    working_content = current_content
    if _should_reset_runtime_content(runtime_path=runtime_path, target=target, options=options):
        working_content = ""
    changed = False

    snapshot = BackupSnapshot(existed=False, backup_path=None)
    if not options.dry_run:
        snapshot = create_backup(target_path, backup_root=backup_root)

    try:
        for operation in target.operations:
            ir_ref = str(operation.get("ir_ref") or "unknown")
            try:
                working_content, op_changed = apply_upsert_region(
                    current_content=working_content,
                    operation=operation,
                    force=options.force,
                    allow_patch_create=True,
                )
            except ApplyBlockedError as exc:
                raise RuntimeError(
                    _format_error(runtime_path, ir_ref, "apply_blocked", str(exc))
                ) from exc
            except Exception as exc:  # pragma: no cover - defensive guard
                raise RuntimeError(
                    _format_error(runtime_path, ir_ref, "apply_error", str(exc))
                ) from exc
            changed = changed or op_changed

        if runtime_path.endswith(".py"):
            try:
                ast.parse(working_content)
            except SyntaxError as exc:
                raise RuntimeError(
                    _format_error(
                        runtime_path,
                        "syntax",
                        "invalid_python_syntax",
                        f"{exc.msg} (line {exc.lineno})",
                    )
                ) from exc

        if changed and not options.dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(working_content, encoding="utf-8")

        return ApplyFileResult(
            runtime_path=runtime_path,
            status="applied" if changed else "noop",
            changed=changed,
            backup_path=str(snapshot.backup_path) if snapshot.backup_path else None,
            restored=False,
            error=None,
        )
    except Exception as exc:
        restored = False
        if not options.dry_run:
            restored = restore_backup(target_path, snapshot)
        return ApplyFileResult(
            runtime_path=runtime_path,
            status="failed",
            changed=False,
            backup_path=str(snapshot.backup_path) if snapshot.backup_path else None,
            restored=restored,
            error=str(exc),
        )


def apply_patch_plans(
    *,
    workspace_root: Path,
    version: str,
    patches_dir: Path,
    working_dir: Path,
    config: dict[str, Any] | None = None,
    force: bool = False,
    dry_run: bool = False,
    reindex: bool = True,
    progress_callback: Callable[[str], None] | None = None,
) -> ApplySummary:
    cfg = config or {}
    reindex_each_patch_plan = _get_config_bool(cfg, "reindex_each_patch_plan", True)
    reset_target_files = _get_config_bool(cfg, "code_apply_reset_target_files", True)

    options = ApplyOptions(
        workspace_root=workspace_root,
        version=version,
        patches_dir=patches_dir,
        working_dir=working_dir,
        force=force,
        dry_run=dry_run,
        reindex=reindex,
        reindex_each_patch_plan=reindex_each_patch_plan,
        reset_target_files=reset_target_files,
    )

    def _progress(message: str) -> None:
        if progress_callback is not None:
            progress_callback(message)

    queue = load_apply_queue(options.patches_dir)
    backup_run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = options.patches_dir / "backups" / backup_run_id

    file_results: list[ApplyFileResult] = []
    errors: list[str] = []
    reindex_errors: list[str] = []
    changed_paths: list[str] = []
    post_apply_errors: list[str] = []

    for idx, target in enumerate(queue, start=1):
        runtime_path = _normalize_runtime_path(target.runtime_path)
        _progress(f"[{idx}/{len(queue)}] Applying patch-plan for {runtime_path}")
        result = _apply_single_patch_plan(
            target=target,
            options=options,
            backup_root=backup_root,
        )
        file_results.append(result)
        if result.error:
            errors.append(result.error)
            continue

        if result.changed and not options.dry_run:
            changed_paths.append(result.runtime_path)
            if options.reindex and options.reindex_each_patch_plan:
                try:
                    _reindex_changed_paths(
                        workspace_root=options.workspace_root,
                        working_dir=options.working_dir,
                        changed_paths=[result.runtime_path],
                    )
                except Exception as exc:
                    reindex_errors.append(
                        _format_error(result.runtime_path, "reindex", "reindex_error", str(exc))
                    )

    if options.reindex and not options.dry_run and not options.reindex_each_patch_plan and changed_paths:
        try:
            _reindex_changed_paths(
                workspace_root=options.workspace_root,
                working_dir=options.working_dir,
                changed_paths=changed_paths,
            )
        except Exception as exc:
            reindex_errors.append(_format_error("*", "reindex", "reindex_error", str(exc)))

    validate_import_graph = _get_config_bool(cfg, "code_apply_validate_import_graph", True)
    validate_smoke_import = _get_config_bool(cfg, "code_apply_smoke_import_main", True)
    if not options.dry_run and changed_paths and validate_import_graph:
        post_apply_errors.extend(
            _validate_post_apply_import_graph(
                working_dir=options.working_dir,
                changed_paths=changed_paths,
            )
        )
    if not options.dry_run and validate_smoke_import:
        smoke_error = _run_smoke_import_main(working_dir=options.working_dir)
        if smoke_error:
            post_apply_errors.append(smoke_error)

    applied_files = [item.runtime_path for item in file_results if item.status == "applied"]
    failed_files = [item.runtime_path for item in file_results if item.status == "failed"]
    backup_paths = [item.backup_path for item in file_results if item.backup_path]
    restored_files = [item.runtime_path for item in file_results if item.restored]

    applied_count = len(applied_files)
    failed_count = len(failed_files)
    noop_count = len([item for item in file_results if item.status == "noop"])
    total_files = len(file_results)

    errors.extend(post_apply_errors)

    if failed_count == 0 and not reindex_errors and not post_apply_errors:
        status = "success"
    elif failed_count == total_files:
        status = "failed"
    else:
        status = "partial"

    summary = ApplySummary(
        status=status,
        version=version,
        dry_run=options.dry_run,
        reindex=options.reindex,
        reindex_each_patch_plan=options.reindex_each_patch_plan,
        total_files=total_files,
        applied_count=applied_count,
        noop_count=noop_count,
        failed_count=failed_count,
        applied_files=applied_files,
        failed_files=failed_files,
        errors=errors,
        backup_paths=[str(path) for path in backup_paths],
        restored_files=restored_files,
        reindex_errors=reindex_errors,
        file_results=file_results,
    )
    summary.report_path = write_apply_report(patches_dir=patches_dir, summary=summary)
    return summary
