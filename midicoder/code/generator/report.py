from __future__ import annotations

import json
from pathlib import Path

from .models import MergeAction


def write_codegen_report(
    *,
    patches_root: Path,
    version: str,
    stack: str,
    runtime_enabled: bool,
    generated_patch_plans: list[str],
    generated_runtime_files: list[str],
    warnings: list[str],
    errors: list[str],
    execution_order: list[str],
    merge_actions: list[MergeAction],
) -> str:
    report_path = patches_root / "code-gen-report.json"
    payload = {
        "schema_version": "3.0.0",
        "version": version,
        "stack": stack,
        "runtime_enabled": bool(runtime_enabled),
        "generated_patch_plans": sorted(set(generated_patch_plans)),
        "generated_runtime_files": sorted(set(generated_runtime_files)),
        "warnings": warnings,
        "errors": errors,
        "execution_order": execution_order,
        "merge_actions": [
            {
                "ir_ref": action.ir_ref,
                "runtime_path": action.runtime_path,
                "mode": action.mode,
                "status": action.status,
                "detail": action.detail,
            }
            for action in merge_actions
        ],
    }
    report_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return str(report_path)
