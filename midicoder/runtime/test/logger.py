"""Log formatting and storage for runtime tests."""

from __future__ import annotations

import json
from pathlib import Path

from .models import RuntimeTestResult


class RuntimeLogger:
    """Handle log formatting and storage."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    def save_logs(self, log_dir: Path, result: RuntimeTestResult) -> None:
        """Save test results to log directory."""
        # Save error.log (errors only)
        error_log = log_dir / "error.log"
        if result.errors:
            error_lines = []
            for error in result.errors:
                error_lines.append(f"[{error.type}] {error.message}")
                if error.file:
                    error_lines.append(f"  File: {error.file}:{error.line or '?'}")
                if error.traceback:
                    error_lines.append(f"  {error.traceback}")
                error_lines.append("")
            error_log.write_text("\n".join(error_lines), encoding="utf-8")
        else:
            error_log.write_text("No errors detected.\n", encoding="utf-8")

        # Save debug.log (full output)
        debug_log = log_dir / "debug.log"
        debug_log.write_text("\n".join(result.debug_output), encoding="utf-8")

        # Save summary.json
        summary_file = log_dir / "summary.json"
        summary_file.write_text(
            json.dumps(result.to_dict(), indent=2),
            encoding="utf-8",
        )

        # Save manifest.json
        manifest_file = log_dir / "manifest.json"
        manifest = {
            "timestamp": result.timestamp,
            "success": result.success,
            "error_count": len(result.errors),
            "files": {
                "error_log": "error.log",
                "debug_log": "debug.log",
                "summary": "summary.json",
            },
        }
        manifest_file.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
