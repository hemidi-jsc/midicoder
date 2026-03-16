"""Business alignment guardrails for runtime fix operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def validate_runtime_fix_operations(
    operations: list[dict[str, Any]],
    *,
    working_dir: Path,
    relevant_files: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Validate runtime fix operations before saving patch-plans.

    The goal is to prevent risky outputs that can drift business logic or
    attempt to patch non-project artifacts.
    """
    valid: list[dict[str, Any]] = []
    issues: list[str] = []
    relevant_files = relevant_files or set()

    for idx, op in enumerate(operations):
        op_label = f"Operation {idx} (ir_ref={op.get('ir_ref', '?')})"

        file_path = str(op.get("file_path") or "").strip().replace("\\", "/")
        if not file_path:
            issues.append(f"{op_label}: rejected - missing file_path")
            continue

        if file_path.startswith(".midicoder/") or file_path.startswith("contracts/") or file_path.startswith("irs/"):
            issues.append(f"{op_label}: rejected - file_path points to Midicoder artifacts: {file_path}")
            continue

        if _is_absolute_path(file_path):
            try:
                abs_target = Path(file_path).resolve()
                abs_root = working_dir.resolve()
                abs_target.relative_to(abs_root)
            except Exception:
                issues.append(f"{op_label}: rejected - absolute file_path is outside working_dir: {file_path}")
                continue

        region_content = str(op.get("region_content") or "")
        if _is_effectively_empty_region(region_content):
            issues.append(f"{op_label}: rejected - region_content is empty or no-op")
            continue

        if relevant_files and file_path not in relevant_files:
            issues.append(
                f"{op_label}: warning - file_path not in top relevant files ({file_path}). Keeping it but please review."
            )

        valid.append(op)

    return valid, issues


def _is_absolute_path(path_value: str) -> bool:
    if not path_value:
        return False
    return path_value.startswith("/") or (len(path_value) > 2 and path_value[1] == ":")


def _is_effectively_empty_region(region_content: str) -> bool:
    text = region_content.strip()
    if not text:
        return True
    # Common no-op content that usually indicates a failed fix attempt.
    if text in {"pass", "..."}:
        return True
    return False

