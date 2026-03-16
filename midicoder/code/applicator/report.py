from __future__ import annotations

import json
from pathlib import Path

from .models import ApplySummary


def write_apply_report(*, patches_dir: Path, summary: ApplySummary) -> str:
    report_path = patches_dir / "code-apply-report.json"
    payload = {
        "schema_version": "1.0.0",
        "version": summary.version,
        "status": summary.status,
        "dry_run": summary.dry_run,
        "reindex": summary.reindex,
        "reindex_each_patch_plan": summary.reindex_each_patch_plan,
        "summary": {
            "total": summary.total_files,
            "applied": summary.applied_count,
            "noop": summary.noop_count,
            "failed": summary.failed_count,
        },
        "applied_files": summary.applied_files,
        "failed_files": summary.failed_files,
        "errors": summary.errors,
        "backup_paths": summary.backup_paths,
        "restored_files": summary.restored_files,
        "reindex_errors": summary.reindex_errors,
        "file_results": [
            {
                "runtime_path": item.runtime_path,
                "status": item.status,
                "changed": item.changed,
                "backup_path": item.backup_path,
                "restored": item.restored,
                "error": item.error,
            }
            for item in summary.file_results
        ],
    }
    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return str(report_path)

