"""Shared orchestrator wrappers for code phases (build/gen/apply)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .applicator import apply_patch_plans
from .builder import build_code_plan
from .generator.pipeline import build_runtime_code


def build_code_plans(
    ir_json_path: str | Path | dict[str, Any],
    context_dir: str | Path | None = None,
    profile_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict_mode: bool = False,
    *,
    plan_dir: Path | None = None,
    project_version: str | None = None,
    config: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Build code plans with a stable wrapper signature."""
    _ = profile_path
    _ = strict_mode
    if not isinstance(ir_json_path, dict):
        raise ValueError("build_code_plans expects a loaded IR object in this implementation.")

    effective_plan_dir = Path(output_dir) if output_dir is not None else plan_dir
    if effective_plan_dir is None:
        raise ValueError("Missing output_dir (or legacy plan_dir) for build_code_plans().")

    if context_dir is None:
        context_path = effective_plan_dir.parent.parent / "context"
    else:
        context_path = Path(context_dir)

    result = build_code_plan(
        ir=ir_json_path,
        plans_dir=effective_plan_dir,
        version=str(project_version or "unknown"),
        context_dir=context_path,
        config=config,
        strict_mode=strict_mode,
    )
    return [plan.to_dict() for plan in result.plans], result.warnings


def gen_code(
    *,
    workspace_root: str | Path,
    version: str,
    plans_dir: str | Path,
    patches_dir: str | Path,
    runtime_enabled: bool = False,
    config: dict[str, Any] | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    result = build_runtime_code(
        workspace_root=Path(workspace_root),
        version=version,
        plans_dir=Path(plans_dir),
        patches_root=Path(patches_dir),
        generator_version="compat",
        config=config,
        progress_callback=progress_callback,
        runtime_enabled=runtime_enabled,
    )
    return {
        "generated_patch_plans": result.generated_patch_plans,
        "generated_runtime_files": result.generated_runtime_files,
        "runtime_enabled": result.runtime_enabled,
        "generated_items": result.generated_items,
        "warnings": result.warnings,
        "errors": result.errors,
        "report_path": result.report_path,
        "index_path": result.index_path,
    }


def apply_generated_code(
    *,
    workspace_root: str | Path,
    version: str,
    patches_dir: str | Path,
    config: dict[str, Any] | None = None,
    force: bool = False,
    dry_run: bool = False,
    reindex: bool = True,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    cfg = config or {}
    workspace_path = Path(workspace_root)
    working_dir_value = str(cfg.get("working_dir", "."))
    working_dir = Path(working_dir_value)
    if not working_dir.is_absolute():
        working_dir = (workspace_path / working_dir).resolve()

    result = apply_patch_plans(
        workspace_root=workspace_path,
        version=version,
        patches_dir=Path(patches_dir),
        working_dir=working_dir,
        config=cfg,
        force=force,
        dry_run=dry_run,
        reindex=reindex,
        progress_callback=progress_callback,
    )
    return {
        "status": result.status,
        "version": result.version,
        "dry_run": result.dry_run,
        "reindex": result.reindex,
        "reindex_each_patch_plan": result.reindex_each_patch_plan,
        "processed_count": result.total_files,
        "applied_count": result.applied_count,
        "noop_count": result.noop_count,
        "failed_count": result.failed_count,
        "applied_files": result.applied_files,
        "failed_files": result.failed_files,
        "errors": result.errors,
        "backup_paths": result.backup_paths,
        "restored_files": result.restored_files,
        "reindex_errors": result.reindex_errors,
        "report_path": result.report_path,
    }
