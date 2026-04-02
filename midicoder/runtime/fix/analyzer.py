"""Analyze error logs and categorize errors."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ErrorCategory:
    """Categorized error information."""

    type: str
    errors: list[dict] = field(default_factory=list)
    file_context: dict = field(default_factory=dict)


@dataclass
class ErrorAnalysis:
    """Analysis result of error logs."""

    errors: list[ErrorCategory] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    traceback_focus: list[dict[str, Any]] = field(default_factory=list)
    normalized_project_files: list[str] = field(default_factory=list)
    runtime_keywords: list[str] = field(default_factory=list)


def analyze_error_logs(
    log_dir: Path, *, working_dir: Path | None = None
) -> ErrorAnalysis:
    """Analyze error logs and categorize errors."""
    summary_file = log_dir / "summary.json"
    error_log_file = log_dir / "error.log"

    if not summary_file.exists():
        return ErrorAnalysis()

    try:
        summary = json.loads(summary_file.read_text(encoding="utf-8"))
    except Exception:
        return ErrorAnalysis()

    # Categorize errors
    categories: dict[str, ErrorCategory] = {}
    project_files: set[str] = set()
    keywords: set[str] = set()
    traceback_focus: list[dict[str, Any]] = []

    for error in summary.get("errors", []):
        error_type = error.get("type", "unknown")
        keywords.update(_tokenize_text(str(error_type)))
        keywords.update(_tokenize_text(str(error.get("message", ""))))

        if error_type not in categories:
            categories[error_type] = ErrorCategory(
                type=error_type,
                errors=[],
                file_context={},
            )

        categories[error_type].errors.append(error)

        # Extract file context if available
        if error.get("file"):
            file_path = _normalize_path(str(error["file"]), working_dir)
            if file_path not in categories[error_type].file_context:
                categories[error_type].file_context[file_path] = []
            categories[error_type].file_context[file_path].append(error)
            if not _should_skip_file(file_path):
                project_files.add(file_path)
                traceback_focus.append(
                    {
                        "file": file_path,
                        "line": error.get("line"),
                        "error_type": error_type,
                        "source": "summary",
                    }
                )

    # Read error.log for additional context
    if error_log_file.exists():
        error_log_content = error_log_file.read_text(encoding="utf-8")
        # Parse traceback and additional context
        focus_from_log, files_from_log, keywords_from_log = _enrich_error_context(
            categories,
            error_log_content,
            working_dir=working_dir,
        )
        traceback_focus.extend(focus_from_log)
        project_files.update(files_from_log)
        keywords.update(keywords_from_log)

    return ErrorAnalysis(
        errors=list(categories.values()),
        summary=summary,
        traceback_focus=_dedupe_focus(traceback_focus),
        normalized_project_files=sorted(project_files),
        runtime_keywords=sorted(k for k in keywords if len(k) > 2),
    )


def _enrich_error_context(
    categories: dict[str, ErrorCategory],
    error_log: str,
    *,
    working_dir: Path | None = None,
) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    """Enrich error categories with context from error log."""
    file_pattern = r'File "([^"]+)", line (\d+)(?:, in ([A-Za-z_][\w]*))?'
    matches = re.findall(file_pattern, error_log)
    focus: list[dict[str, Any]] = []
    project_files: set[str] = set()
    keywords: set[str] = set()

    for raw_file_path, line_num, in_symbol in matches:
        file_path = _normalize_path(raw_file_path, working_dir)
        keywords.update(_tokenize_text(file_path))
        keywords.update(_tokenize_text(in_symbol))
        if _should_skip_file(file_path):
            continue
        project_files.add(file_path)

        for category in categories.values():
            if file_path not in category.file_context:
                category.file_context[file_path] = []

            existing = any(
                item.get("line") == int(line_num) and item.get("source") == "traceback"
                for item in category.file_context[file_path]
                if isinstance(item, dict)
            )
            if not existing:
                category.file_context[file_path].append(
                    {
                        "line": int(line_num),
                        "source": "traceback",
                        "symbol": in_symbol or None,
                    }
                )

        focus.append(
            {
                "file": file_path,
                "line": int(line_num),
                "symbol": in_symbol or None,
                "source": "traceback",
            }
        )
    return _dedupe_focus(focus), project_files, keywords


def _normalize_path(file_path: str, working_dir: Path | None = None) -> str:
    value = str(file_path or "").strip().replace("\\", "/")
    if not value:
        return value
    # Best effort: relativize absolute path to working_dir when possible.
    if working_dir and (value.startswith("/") or (len(value) > 1 and value[1] == ":")):
        try:
            abs_path = Path(value).resolve()
            base = working_dir.resolve()
            value = abs_path.relative_to(base).as_posix()
        except Exception:
            value = value
    return value


def _tokenize_text(text: str) -> set[str]:
    if not text:
        return set()
    return {tok.lower() for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text)}


def _dedupe_focus(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, int | None, str | None, str | None]] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        key = (
            str(item.get("file") or ""),
            int(item.get("line")) if str(item.get("line") or "").isdigit() else None,
            str(item.get("symbol") or ""),
            str(item.get("source") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _should_skip_file(file_path: str) -> bool:
    """Check if file should be skipped (not part of user's project)."""
    # Normalize path separators
    normalized = file_path.replace("\\", "/").lower()

    # Skip patterns for third-party code
    skip_patterns = [
        "/venv/",
        "/.venv/",
        "/site-packages/",
        "/lib/python",
        "/python3",
        "\\venv\\",
        "\\.venv\\",
        "\\site-packages\\",
        "\\lib\\python",
        "\\python3",
    ]

    # Check if path contains any skip pattern
    for pattern in skip_patterns:
        if pattern.lower() in normalized:
            return True

    # Skip obvious non-source assets
    if normalized.endswith((".pyc", ".log", ".tmp", ".cache")):
        return True

    return False
