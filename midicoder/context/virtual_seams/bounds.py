from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple


def read_source_lines(repo_root: Path | None, file_path: str) -> list[str] | None:
    if repo_root is None:
        return None
    candidate = repo_root / file_path
    if not candidate.exists() or not candidate.is_file():
        return None
    try:
        return candidate.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None


def resolve_block_bounds_for_exemplar(
    repo_root: Path | None,
    record: dict,
) -> tuple[int | None, int | None]:
    file_path = str(record.get("file", "")).strip()
    line = _coerce_line(record.get("line"))
    if not file_path or not line:
        return None, None

    lines = read_source_lines(repo_root, file_path)
    if not lines:
        return None, None

    language = _infer_language(record, file_path)
    begin_line = _find_declaration_line(language, lines, line) or line
    end_line = _find_block_end(language, lines, begin_line)
    return begin_line, end_line


def resolve_block_bounds_for_symbol(
    repo_root: Path | None,
    record: dict,
) -> tuple[int | None, int | None]:
    file_path = str(record.get("file", "")).strip()
    line = _coerce_line(record.get("line"))
    if not file_path or not line:
        return None, None

    lines = read_source_lines(repo_root, file_path)
    if not lines:
        return None, None

    language = _infer_language(record, file_path)
    begin_line = line
    end_line = _find_block_end(language, lines, begin_line)
    return begin_line, end_line


def resolve_block_bounds_for_entrypoint(
    repo_root: Path | None,
    record: dict,
) -> tuple[int | None, int | None]:
    file_path = str(record.get("file", "")).strip()
    line = _coerce_line(record.get("line"))
    if not file_path or not line:
        return None, None

    lines = read_source_lines(repo_root, file_path)
    if not lines:
        return None, None

    language = _infer_language(record, file_path)
    begin_line = line
    end_line = _find_block_end(language, lines, begin_line)
    return begin_line, end_line


def _infer_language(record: dict, file_path: str) -> str:
    language = str(record.get("language") or "").strip().lower()
    if language:
        return language
    lowered = file_path.lower()
    if lowered.endswith(".py"):
        return "python"
    if lowered.endswith((".ts", ".tsx")):
        return "typescript"
    if lowered.endswith((".js", ".jsx")):
        return "javascript"
    return "unknown"


def _find_declaration_line(language: str, lines: list[str], line: int) -> int | None:
    if not lines:
        return None
    idx = max(line - 1, 0)
    # Validate index is within bounds
    if idx >= len(lines):
        return None
    if language == "python":
        return _find_python_declaration(lines, idx)
    if language in {"typescript", "javascript"}:
        return _find_js_declaration(lines, idx)
    return None


def _find_block_end(language: str, lines: list[str], begin_line: int) -> int | None:
    if not lines or begin_line <= 0 or begin_line > len(lines):
        return None
    if language == "python":
        return _find_python_block_end(lines, begin_line)
    if language in {"typescript", "javascript"}:
        return _find_js_block_end(lines, begin_line)
    return None


def _find_python_declaration(lines: list[str], start_index: int) -> int | None:
    # Validate bounds
    if start_index < 0 or start_index >= len(lines):
        return None

    for idx in range(start_index, -1, -1):
        line = lines[idx]
        stripped = line.lstrip()
        if not stripped:
            continue
        if (
            stripped.startswith("class ")
            or stripped.startswith("def ")
            or stripped.startswith("async def ")
        ):
            return idx + 1
    return None


def _find_js_declaration(lines: list[str], start_index: int) -> int | None:
    # Validate bounds
    if start_index < 0 or start_index >= len(lines):
        return None

    for idx in range(start_index, -1, -1):
        line = lines[idx].lstrip()
        if not line:
            continue
        if line.startswith("class ") or line.startswith("export class "):
            return idx + 1
        if line.startswith("function ") or line.startswith("export function "):
            return idx + 1
        if line.startswith("export default function "):
            return idx + 1
    return None


def _find_python_block_end(lines: list[str], begin_line: int) -> int | None:
    start_idx = begin_line - 1
    base_line = lines[start_idx]
    base_indent = _indent_width(base_line)

    if start_idx >= len(lines) - 1:
        return begin_line

    for idx in range(start_idx + 1, len(lines)):
        line = lines[idx]
        stripped = line.strip()
        if not stripped:
            continue
        indent = _indent_width(line)
        if indent <= base_indent:
            return idx
    return len(lines)


def _find_js_block_end(lines: list[str], begin_line: int) -> int | None:
    start_idx = begin_line - 1
    brace_started = False
    depth = 0

    for idx in range(start_idx, len(lines)):
        line = lines[idx]
        for ch in line:
            if ch == "{":
                depth += 1
                brace_started = True
            elif ch == "}":
                if depth > 0:
                    depth -= 1
                    if brace_started and depth == 0:
                        return idx + 1
        if brace_started and depth == 0:
            return idx + 1
    return None


def _indent_width(line: str) -> int:
    width = 0
    for ch in line:
        if ch == " ":
            width += 1
        elif ch == "\t":
            width += 4
        else:
            break
    return width


def _coerce_line(value: object) -> int | None:
    try:
        line = int(value)
    except (TypeError, ValueError):
        return None
    return line if line > 0 else None
