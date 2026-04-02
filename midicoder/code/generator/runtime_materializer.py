from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .harmonize import harmonize_python_file
from .patch_ops import ApplyBlockedError, apply_upsert_region
from .writer import write_runtime_file


def _is_valid_python(content: str) -> bool:
    try:
        ast.parse(content)
        return True
    except SyntaxError:
        return False


def materialize_runtime_outputs(
    *,
    patches_root: Path,
    patch_plan_operations: dict[str, list[dict[str, Any]]],
) -> tuple[list[str], list[str]]:
    generated_runtime_files: list[str] = []
    errors: list[str] = []

    for runtime_path in sorted(patch_plan_operations):
        operations = patch_plan_operations.get(runtime_path) or []
        current_content = ""
        for operation in operations:
            if not isinstance(operation, dict):
                continue
            try:
                current_content, _ = apply_upsert_region(
                    current_content=current_content,
                    operation=operation,
                    force=True,
                    allow_patch_create=True,
                )
            except ApplyBlockedError as exc:
                errors.append(f"{runtime_path}:runtime_materialize_blocked:{exc}")
                current_content = ""
                break
            except Exception as exc:
                errors.append(f"{runtime_path}:runtime_materialize_failed:{exc}")
                current_content = ""
                break

        if not current_content:
            continue

        if runtime_path.endswith(".py"):
            normalized = harmonize_python_file(current_content)
            if not _is_valid_python(normalized):
                errors.append(f"{runtime_path}:runtime_materialize_invalid_python")
                continue
            current_content = normalized
        elif not current_content.endswith("\n"):
            current_content += "\n"

        generated_runtime_files.append(
            write_runtime_file(patches_root, runtime_path, current_content)
        )

    return generated_runtime_files, errors
