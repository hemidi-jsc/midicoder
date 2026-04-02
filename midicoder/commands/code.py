"""Code planning, generation and application commands."""

from __future__ import annotations

import json
from pathlib import Path

from midicoder.code import builder as code_builder
from midicoder.code import orchestrator as code_orchestrator
from midicoder.io.messages import print_error, print_info, print_success, print_warning

from .base import (
    MidicoderPaths,
    create_run_dir,
    ensure_base_layout,
    ensure_version_layout,
    read_state,
    write_run_outputs,
)


def _read_config(paths: MidicoderPaths) -> dict[str, object]:
    if not paths.config.exists():
        return {}
    return json.loads(paths.config.read_text(encoding="utf-8"))


def build(root: Path) -> None:
    """Build file-level pseudo code plans from IR (deterministic, no LLM)."""
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)
    state = read_state(paths)
    version = state.get("current_version")
    if not version:
        raise RuntimeError("No current version set. Run `version create` first.")

    ensure_version_layout(paths, str(version))

    ir_path = paths.versions / str(version) / "irs" / "ir.json"
    if not ir_path.exists():
        raise RuntimeError("IR is missing. Run `ir build` before `code build`.")

    plans_root = paths.versions / str(version) / "plans"
    context_dir = paths.context

    ir = code_builder.load_ir(ir_path)
    config = _read_config(paths)
    plans, warnings = code_orchestrator.build_code_plans(
        ir_json_path=ir,
        context_dir=context_dir,
        output_dir=plans_root,
        project_version=str(version),
        config=config,
    )

    counts = {"commands": 0, "workflows": 0, "api": 0}
    for plan in plans:
        type_name = str(plan.get("ir_ref", "")).split(".", 1)[0]
        if type_name == "Command":
            counts["commands"] += 1
        elif type_name == "Workflow":
            counts["workflows"] += 1
        elif type_name == "HttpRoute":
            counts["api"] += 1

    run_dir = create_run_dir(paths, "code_build")
    current_state = {"current_state": "code_build"}
    write_run_outputs(
        run_dir,
        "code_build",
        {
            "version": version,
            "status": "built",
            "counts": counts,
            "warnings": warnings,
        },
        state_before=state,
        state_after=state | current_state,
    )


def _print_codegen_error_summary(result: dict[str, object], *, limit: int = 10) -> None:
    errors = result.get("errors")
    if not isinstance(errors, list):
        return
    for message in errors[:limit]:
        print_error(str(message))
    if len(errors) > limit:
        print_warning(
            f"... and {len(errors) - limit} more error(s). See code-gen report for full details."
        )
    report_path = result.get("report_path")
    if report_path:
        print_info(f"Detailed code-gen report: {report_path}")


def gen(root: Path, *, runtime: bool = False) -> None:
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)
    state = read_state(paths)
    version = state.get("current_version")
    if not version:
        raise RuntimeError("No current version set. Run `version create` first.")

    ensure_version_layout(paths, str(version))

    plans_root = paths.versions / str(version) / "plans"
    index_path = plans_root / "index.json"
    if not index_path.exists():
        raise RuntimeError(
            "plans/index.json is missing. Run `code plan` before `code gen`."
        )

    patches_root = paths.versions / str(version) / "patches"
    patches_root.mkdir(parents=True, exist_ok=True)

    print_info(f"Starting code generation for version {version}", title="Code Gen")
    config = _read_config(paths)
    result = code_orchestrator.gen_code(
        workspace_root=root,
        version=str(version),
        plans_dir=plans_root,
        patches_dir=patches_root,
        runtime_enabled=runtime,
        config=config,
        progress_callback=lambda msg: print_info(msg),
    )

    if result.get("warnings"):
        print_warning(f"Generation completed with {len(result['warnings'])} warning(s)")
    if result.get("errors"):
        print_warning(f"Generation completed with {len(result['errors'])} error(s)")
        _print_codegen_error_summary(result)
    patch_plan_count = len(result.get("generated_patch_plans", []))
    runtime_file_count = len(result.get("generated_runtime_files", []))
    runtime_enabled = bool(result.get("runtime_enabled", False))
    if runtime_enabled:
        print_success(
            f"Generated {result.get('generated_items', 0)} item(s), "
            f"{patch_plan_count} patch-plan file(s), {runtime_file_count} runtime file(s)"
        )
    else:
        print_success(
            f"Generated {result.get('generated_items', 0)} item(s), "
            f"{patch_plan_count} patch-plan file(s)"
        )

    run_dir = create_run_dir(paths, "code_gen")
    write_run_outputs(
        run_dir,
        "code_gen",
        {
            "version": version,
            "status": "generated",
            "runtime_enabled": runtime_enabled,
            "generated_items": result.get("generated_items", 0),
            "patch_plan_count": patch_plan_count,
            "runtime_file_count": runtime_file_count,
            "generated_patch_plans": result.get("generated_patch_plans", []),
            "generated_runtime_files": result.get("generated_runtime_files", []),
            "warnings": result["warnings"],
            "errors": result["errors"],
            "report_path": result["report_path"],
            "index_path": result.get("index_path"),
        },
        state_before=state,
        state_after=state,
    )


def apply(
    root: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
    reindex: bool = True,
    patches_subdir: str | None = None,
) -> None:
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)
    state = read_state(paths)
    version = state.get("current_version")
    if not version:
        raise RuntimeError("No current version set. Run `version create` first.")

    ensure_version_layout(paths, str(version))

    # Determine patches directory
    if patches_subdir:
        # Custom patches directory (e.g., runtime-fix)
        patches_root = paths.versions / str(version) / patches_subdir
        if not patches_root.exists():
            raise RuntimeError(f"Custom patches directory not found: {patches_root}")
    else:
        # Default patches directory
        patches_root = paths.versions / str(version) / "patches"

    index_path = patches_root / "index.json"
    if not index_path.exists():
        if patches_subdir:
            raise RuntimeError(
                f"index.json is missing in {patches_root}. Check runtime fix output."
            )
        else:
            raise RuntimeError(
                "patches/index.json is missing. Run `code gen` before `code apply`."
            )

    print_info(f"Starting code apply for version {version}", title="Code Apply")
    config = _read_config(paths)
    result = code_orchestrator.apply_generated_code(
        workspace_root=root,
        version=str(version),
        patches_dir=patches_root,
        config=config,
        force=force,
        dry_run=dry_run,
        reindex=reindex,
        progress_callback=lambda msg: print_info(msg),
    )

    errors = result.get("errors", [])
    reindex_errors = result.get("reindex_errors", [])
    if isinstance(errors, list) and errors:
        print_warning(f"Apply completed with {len(errors)} error(s)")
        for message in errors[:10]:
            print_error(str(message))
        if len(errors) > 10:
            print_warning(
                f"... and {len(errors) - 10} more error(s). See apply report for full details."
            )
    if isinstance(reindex_errors, list) and reindex_errors:
        print_warning(f"Reindex completed with {len(reindex_errors)} error(s)")
        for message in reindex_errors[:10]:
            print_error(str(message))

    if result.get("report_path"):
        print_info(f"Detailed code-apply report: {result['report_path']}")

    print_success(
        "Processed "
        f"{result.get('processed_count', 0)} file(s): "
        f"applied={result.get('applied_count', 0)}, "
        f"noop={result.get('noop_count', 0)}, "
        f"failed={result.get('failed_count', 0)}"
    )

    run_dir = create_run_dir(paths, "code_apply")
    write_run_outputs(
        run_dir,
        "code_apply",
        {
            "version": version,
            "status": result.get("status"),
            "dry_run": bool(result.get("dry_run", False)),
            "reindex": bool(result.get("reindex", False)),
            "reindex_each_patch_plan": bool(
                result.get("reindex_each_patch_plan", False)
            ),
            "processed_count": result.get("processed_count", 0),
            "applied_count": result.get("applied_count", 0),
            "noop_count": result.get("noop_count", 0),
            "failed_count": result.get("failed_count", 0),
            "applied_files": result.get("applied_files", []),
            "failed_files": result.get("failed_files", []),
            "errors": errors if isinstance(errors, list) else [],
            "reindex_errors": (
                reindex_errors if isinstance(reindex_errors, list) else []
            ),
            "backup_paths": result.get("backup_paths", []),
            "restored_files": result.get("restored_files", []),
            "report_path": result.get("report_path"),
        },
        state_before=state,
        state_after=state,
    )
