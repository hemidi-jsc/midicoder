from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import LoadedPatchPlan


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"Missing required file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON file: {path} ({exc})") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid JSON object in file: {path}")
    return payload


def load_apply_queue(patches_dir: Path) -> list[LoadedPatchPlan]:
    index_path = patches_dir / "index.json"
    index_payload = _load_json(index_path)

    # Support both formats:
    # 1. Code gen format: patch_plan_targets (array of objects)
    # 2. Runtime-fix format: patch_files (array of filenames)

    patch_plan_targets = index_payload.get("patch_plan_targets")
    patch_files = index_payload.get("patch_files")

    if isinstance(patch_plan_targets, list) and patch_plan_targets:
        # Code gen format
        return _load_from_patch_plan_targets(patches_dir, patch_plan_targets)
    elif isinstance(patch_files, list) and patch_files:
        # Runtime-fix format
        return _load_from_patch_files(patches_dir, patch_files)
    else:
        raise RuntimeError(
            f"Invalid index.json format in: {index_path}. "
            "Expected either 'patch_plan_targets' or 'patch_files'"
        )


def _load_from_patch_plan_targets(
    patches_dir: Path,
    patch_plan_targets: list,
) -> list[LoadedPatchPlan]:
    """Load patches from code gen format (patch_plan_targets)."""
    queue: list[LoadedPatchPlan] = []
    for item in patch_plan_targets:
        if not isinstance(item, dict):
            raise RuntimeError(f"Invalid patch_plan_targets entry: {item}")

        runtime_path = (
            str(item.get("runtime_path") or "").strip().replace("\\", "/").lstrip("./")
        )
        patch_plan_file = str(item.get("patch_plan_file") or "").strip()
        if not runtime_path:
            raise RuntimeError(
                f"Missing runtime_path in patch_plan_targets entry: {item}"
            )
        if not patch_plan_file:
            raise RuntimeError(
                f"Missing patch_plan_file for runtime_path={runtime_path}"
            )

        patch_plan_path = patches_dir / patch_plan_file
        plan_payload = _load_json(patch_plan_path)
        operations = plan_payload.get("operations")
        if not isinstance(operations, list):
            raise RuntimeError(
                f"Invalid operations[] in patch-plan file: {patch_plan_path}"
            )

        plan_runtime_path = (
            str(plan_payload.get("runtime_path") or "")
            .strip()
            .replace("\\", "/")
            .lstrip("./")
        )
        effective_runtime_path = plan_runtime_path or runtime_path

        queue.append(
            LoadedPatchPlan(
                runtime_path=effective_runtime_path,
                patch_plan_file=patch_plan_file,
                patch_plan_path=patch_plan_path,
                operations=[entry for entry in operations if isinstance(entry, dict)],
            )
        )
    return queue


def _load_from_patch_files(
    patches_dir: Path,
    patch_files: list,
) -> list[LoadedPatchPlan]:
    """Load patches from runtime-fix format (patch_files)."""
    queue: list[LoadedPatchPlan] = []
    for patch_plan_file in patch_files:
        if not isinstance(patch_plan_file, str):
            raise RuntimeError(f"Invalid patch_files entry: {patch_plan_file}")

        patch_plan_path = patches_dir / patch_plan_file
        plan_payload = _load_json(patch_plan_path)

        # Runtime-fix format uses 'patches' array instead of 'operations'
        patches = plan_payload.get("patches", [])
        if not isinstance(patches, list):
            raise RuntimeError(
                f"Invalid patches[] in patch-plan file: {patch_plan_path}"
            )

        # Extract runtime_path from first patch operation
        runtime_path = None
        for patch in patches:
            if isinstance(patch, dict) and patch.get("path"):
                runtime_path = (
                    str(patch["path"]).strip().replace("\\", "/").lstrip("./")
                )
                break

        if not runtime_path:
            # Fallback: extract from filename
            # e.g., "000_app_main.py.patch-plan.json" -> "app/main.py"
            filename = patch_plan_file.replace(".patch-plan.json", "")
            # Remove numeric prefix
            if "_" in filename:
                parts = filename.split("_", 1)
                if parts[0].isdigit():
                    filename = parts[1]
            runtime_path = filename.replace("_", "/")

        # Convert patches to operations format for compatibility
        operations = []
        for patch in patches:
            if isinstance(patch, dict):
                # Runtime-fix patch format -> operations format
                operation = {
                    "path": patch.get("path", runtime_path),
                    "operation": patch.get("operation", "edit"),
                    "anchor": patch.get("anchor"),
                    "mode": patch.get("mode"),
                    "content": patch.get("content"),
                    "ir_ref": plan_payload.get("ir_ref", "runtime_fix"),
                }
                operations.append(operation)

        queue.append(
            LoadedPatchPlan(
                runtime_path=runtime_path,
                patch_plan_file=patch_plan_file,
                patch_plan_path=patch_plan_path,
                operations=operations,
            )
        )
    return queue
