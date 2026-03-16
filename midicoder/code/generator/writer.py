from __future__ import annotations

import json
from pathlib import Path


def _normalize_runtime_path(runtime_path: str) -> str:
    return runtime_path.replace("\\", "/").lstrip("/")


def patch_plan_filename(runtime_path: str) -> str:
    normalized = _normalize_runtime_path(runtime_path)
    stem = normalized[:-3] if normalized.endswith(".py") else normalized
    return f"{stem.replace('/', '.')}.patch-plan.json"


def write_patch_plan_file(
    *,
    patches_root: Path,
    runtime_path: str,
    payload: dict[str, object],
) -> str:
    output_path = patches_root / patch_plan_filename(runtime_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return str(output_path)


def write_runtime_file(patches_root: Path, runtime_path: str, content: str) -> str:
    normalized = _normalize_runtime_path(runtime_path)
    output_path = patches_root / "runtime" / normalized
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return str(output_path)


def write_patches_index(
    *,
    patches_root: Path,
    version: str,
    stack: str,
    generated_patch_plans: list[str],
    patch_plan_targets: list[dict[str, object]],
    runtime_enabled: bool,
    generated_runtime_files: list[str],
    execution_order: list[str],
) -> str:
    payload = {
        "schema_version": "3.0.0",
        "version": version,
        "stack": stack,
        "generated_patch_plans": sorted(set(generated_patch_plans)),
        "patch_plan_targets": patch_plan_targets,
        "runtime_enabled": bool(runtime_enabled),
        "generated_runtime_files": sorted(set(generated_runtime_files)),
        "execution_order": execution_order,
    }
    index_path = patches_root / "index.json"
    index_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return str(index_path)
