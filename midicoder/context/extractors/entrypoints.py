"""Entrypoint extraction."""

from __future__ import annotations

import io
import json
import logging
import re
import tokenize
from pathlib import Path

from ..core.models import EntryPoint
from ..core.scanner import ProjectScanner, normalize_path

logger = logging.getLogger(__name__)

PY_ENTRYPOINT_NAMES = {
    "__main__.py",
    "main.py",
    "app.py",
    "wsgi.py",
    "asgi.py",
    "manage.py",
    "run.py",
    "server.py",
}

JS_ENTRYPOINT_NAMES = {
    "index.js",
    "index.ts",
    "main.js",
    "main.ts",
    "server.js",
    "server.ts",
    "app.js",
    "app.ts",
}

JS_ENTRYPOINT_PATHS = {
    "src/index.js",
    "src/index.ts",
    "src/main.js",
    "src/main.ts",
    "src/server.js",
    "src/server.ts",
    "src/app.js",
    "src/app.ts",
    "bin/www",
}

FALLBACK_DIR_NAMES = {
    "src",
    "app",
    "apps",
    "services",
    "service",
    "server",
    "api",
}

def extract_entrypoints(
    scanner: ProjectScanner,
    stack: str,
    target_files: set[str] | None = None,
) -> list[EntryPoint]:
    """Extract entrypoints with proper schema: kind, file, line, detail."""
    entrypoints: list[EntryPoint] = []
    js_entry_targets = _resolve_js_entry_targets(scanner)

    # Python entry points
    for path in scanner.python_files:
        relative_path = normalize_path(path.relative_to(scanner.root))
        if target_files is not None and relative_path not in target_files:
            continue
        content = scanner.get_content(path)
        if not content:
            continue
        code_mask = _compute_python_code_mask(content)
        path_boost = 1 if _is_common_entrypoint_path(relative_path, PY_ENTRYPOINT_NAMES, set()) else 0

        # Check for __main__ block
        main_pattern = re.compile(r'^\s*if\s+__name__\s*==\s*["\']__main__["\']\s*:', re.MULTILINE)
        main_match = _first_code_match(main_pattern, content, code_mask)
        if main_match:
            line = _line_number_at(content, main_match.start())
            entrypoints.append(
                EntryPoint(
                    kind="python",
                    file=relative_path,
                    line=line,
                    detail="Python __main__ block",
                )
            )

        # Check for FastAPI app (multi-signal)
        fastapi_import_pattern = re.compile(r'^\s*(?:from\s+fastapi\s+import|import\s+fastapi)\b', re.MULTILINE)
        fastapi_init_pattern = re.compile(r'(?P<var>\w+)\s*=\s*FastAPI\(')
        fastapi_decorator_pattern = re.compile(r'^\s*@(?:app|router)\.(?:get|post|put|delete|patch)\b', re.MULTILINE)

        fastapi_import = _first_code_match(fastapi_import_pattern, content, code_mask) is not None
        fastapi_init = _first_code_match(fastapi_init_pattern, content, code_mask)
        fastapi_decorator = _first_code_match(fastapi_decorator_pattern, content, code_mask) is not None

        if fastapi_init:
            score = 2 + (1 if fastapi_import else 0) + (1 if fastapi_decorator else 0) + path_boost
            if score >= 3:
                line = _line_number_at(content, fastapi_init.start())
                app_var = fastapi_init.group("var")
                entrypoints.append(
                    EntryPoint(
                        kind="fastapi",
                        file=relative_path,
                        line=line,
                        detail=f"FastAPI application entrypoint ({app_var})",
                    )
                )

    # JavaScript/TypeScript entry points
    for path in scanner.js_ts_files:
        relative_path = normalize_path(path.relative_to(scanner.root))
        if target_files is not None and relative_path not in target_files:
            continue
        if js_entry_targets and relative_path not in js_entry_targets:
            continue
        content = scanner.get_content(path)
        if not content:
            continue
        code_mask = _compute_js_code_mask(content)
        path_boost = 1 if _is_common_entrypoint_path(relative_path, JS_ENTRYPOINT_NAMES, JS_ENTRYPOINT_PATHS) else 0
        entrypoints.extend(
            _extract_js_entrypoints_for_file(
                relative_path,
                content,
                code_mask,
                path_boost=path_boost,
                min_score=3,
            )
        )

    if js_entry_targets:
        entrypoints.extend(
            _extract_js_entrypoints_fallback(scanner, entrypoints, target_files, js_entry_targets)
        )

    logger.debug(f"Extracted {len(entrypoints)} entrypoints")
    return entrypoints


def _parse_port(value: str | None) -> int | None:
    if not value:
        return None
    cleaned = value.strip()
    if cleaned.isdigit():
        try:
            return int(cleaned)
        except ValueError:
            return None
    return None


def _extract_js_entrypoints_for_file(
    relative_path: str,
    content: str,
    code_mask: list[bool],
    path_boost: int,
    min_score: int,
) -> list[EntryPoint]:
    entrypoints: list[EntryPoint] = []

    listen_pattern = re.compile(r'(?P<var>\w+)\.listen\(\s*(?P<arg>[^,\n\)]+)')
    express_init_pattern = re.compile(r'\bexpress\s*\(')
    nest_pattern = re.compile(r'NestFactory\.create')
    angular_pattern = re.compile(r'platformBrowserDynamic|bootstrapApplication')
    angular_import_pattern = re.compile(r'@angular/core')

    listen_match = _first_code_match(listen_pattern, content, code_mask)
    express_init = _first_code_match(express_init_pattern, content, code_mask) is not None
    if listen_match:
        score = 2 + (1 if express_init else 0) + path_boost
        if score >= min_score:
            line = _line_number_at(content, listen_match.start())
            arg = listen_match.group("arg").strip()
            port = _parse_port(arg)
            detail = f"Express app listen on {port}" if port is not None else f"Express app listen ({arg})"
            entrypoints.append(
                EntryPoint(
                    kind="express",
                    file=relative_path,
                    line=line,
                    detail=detail,
                )
            )

    nest_match = _first_code_match(nest_pattern, content, code_mask)
    if nest_match:
        port_pattern = re.compile(r'\.listen\(\s*(?P<arg>[^,\n\)]+)')
        port_match = _first_code_match(port_pattern, content, code_mask)
        if port_match:
            score = 2 + 1 + path_boost
            if score >= min_score:
                line = _line_number_at(content, nest_match.start())
                port_arg = port_match.group("arg").strip()
                port = _parse_port(port_arg) if port_arg else None
                detail = "Nest app entry"
                if port_arg:
                    detail = f"Nest app entry (listen {port if port is not None else port_arg})"
                entrypoints.append(
                    EntryPoint(
                        kind="nest",
                        file=relative_path,
                        line=line,
                        detail=detail,
                    )
                )

    angular_match = _first_code_match(angular_pattern, content, code_mask)
    angular_import = _first_code_match(angular_import_pattern, content, code_mask) is not None
    if angular_match and (angular_import or path_boost):
        line = _line_number_at(content, angular_match.start())
        entrypoints.append(
            EntryPoint(
                kind="angular",
                file=relative_path,
                line=line,
                detail="Angular application bootstrap",
            )
        )

    return entrypoints


def _extract_js_entrypoints_fallback(
    scanner: ProjectScanner,
    entrypoints: list[EntryPoint],
    target_files: set[str] | None,
    primary_targets: set[str],
) -> list[EntryPoint]:
    existing_files = {entry.file for entry in entrypoints}
    fallback_entries: list[EntryPoint] = []

    for path in scanner.js_ts_files:
        relative_path = normalize_path(path.relative_to(scanner.root))
        if relative_path in existing_files:
            continue
        if relative_path in primary_targets:
            continue
        if target_files is not None and relative_path not in target_files:
            continue
        if not _is_fallback_js_candidate(relative_path):
            continue

        content = scanner.get_content(path)
        if not content:
            continue
        code_mask = _compute_js_code_mask(content)
        if not _has_js_strong_signal(content, code_mask):
            continue

        path_boost = 1 if _is_common_entrypoint_path(relative_path, JS_ENTRYPOINT_NAMES, JS_ENTRYPOINT_PATHS) else 0
        fallback_entries.extend(
            _extract_js_entrypoints_for_file(
                relative_path,
                content,
                code_mask,
                path_boost=path_boost,
                min_score=3,
            )
        )

    return fallback_entries


def _line_number_at(content: str, index: int) -> int:
    return content[:index].count("\n") + 1


def _first_code_match(pattern: re.Pattern[str], content: str, code_mask: list[bool]) -> re.Match[str] | None:
    for match in pattern.finditer(content):
        if _is_code_index(code_mask, match.start()):
            return match
    return None


def _is_code_index(code_mask: list[bool], index: int) -> bool:
    if not code_mask:
        return True
    if index < 0 or index >= len(code_mask):
        return False
    return code_mask[index]


def _compute_python_code_mask(content: str) -> list[bool]:
    if not content:
        return []
    mask = [True] * len(content)
    line_offsets = _build_line_offsets(content)
    try:
        for token in tokenize.generate_tokens(io.StringIO(content).readline):
            if token.type not in (tokenize.STRING, tokenize.COMMENT):
                continue
            start_idx = _pos_to_index(line_offsets, token.start[0], token.start[1])
            end_idx = _pos_to_index(line_offsets, token.end[0], token.end[1])
            _mark_mask_false(mask, start_idx, end_idx)
    except tokenize.TokenError:
        return mask
    return mask


def _compute_js_code_mask(content: str) -> list[bool]:
    if not content:
        return []
    mask = [True] * len(content)
    idx = 0
    length = len(content)

    while idx < length:
        ch = content[idx]
        nxt = content[idx + 1] if idx + 1 < length else ""

        if ch == "/" and nxt == "/":
            start = idx
            idx += 2
            while idx < length and content[idx] != "\n":
                idx += 1
            _mark_mask_false(mask, start, idx)
            continue

        if ch == "/" and nxt == "*":
            start = idx
            idx += 2
            while idx + 1 < length and not (content[idx] == "*" and content[idx + 1] == "/"):
                idx += 1
            idx = min(idx + 2, length)
            _mark_mask_false(mask, start, idx)
            continue

        if ch in ("'", '"', "`"):
            quote = ch
            start = idx
            idx += 1
            while idx < length:
                current = content[idx]
                if current == "\\":
                    idx += 2
                    continue
                if current == quote:
                    idx += 1
                    break
                idx += 1
            _mark_mask_false(mask, start, idx)
            continue

        idx += 1

    return mask


def _has_js_strong_signal(content: str, code_mask: list[bool]) -> bool:
    signal_patterns = [
        re.compile(r'\bexpress\s*\('),
        re.compile(r'\.listen\('),
        re.compile(r'NestFactory\.create'),
        re.compile(r'platformBrowserDynamic|bootstrapApplication'),
    ]
    for pattern in signal_patterns:
        if _first_code_match(pattern, content, code_mask):
            return True
    return False


def _build_line_offsets(content: str) -> list[int]:
    offsets = [0]
    for idx, char in enumerate(content):
        if char == "\n":
            offsets.append(idx + 1)
    return offsets


def _pos_to_index(offsets: list[int], row: int, col: int) -> int:
    if row <= 0:
        return 0
    if row > len(offsets):
        return offsets[-1] if offsets else 0
    return offsets[row - 1] + col


def _mark_mask_false(mask: list[bool], start: int, end: int) -> None:
    if start < 0:
        start = 0
    if end > len(mask):
        end = len(mask)
    for idx in range(start, end):
        mask[idx] = False


def _is_common_entrypoint_path(relative_path: str, names: set[str], paths: set[str]) -> bool:
    if relative_path in paths:
        return True
    if Path(relative_path).name in names:
        return True
    return False


def _is_fallback_js_candidate(relative_path: str) -> bool:
    if _is_common_entrypoint_path(relative_path, JS_ENTRYPOINT_NAMES, JS_ENTRYPOINT_PATHS):
        return True
    parts = Path(relative_path).parts
    return any(part in FALLBACK_DIR_NAMES for part in parts)


def _resolve_js_entry_targets(scanner: ProjectScanner) -> set[str]:
    targets: set[str] = set()
    pattern = re.compile(r'([\w./-]+\.(?:js|ts|mjs|cjs|jsx|tsx|mts|cts))', re.IGNORECASE)

    for path in scanner.config_files:
        if path.name != "package.json":
            continue

        content = scanner.get_content(path)
        if not content:
            continue

        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            continue

        base = path.parent

        main_entry = payload.get("main")
        if isinstance(main_entry, str):
            targets.update(_expand_entry_paths(base, main_entry))

        bin_entry = payload.get("bin")
        if isinstance(bin_entry, str):
            targets.update(_expand_entry_paths(base, bin_entry))
        elif isinstance(bin_entry, dict):
            for value in bin_entry.values():
                if isinstance(value, str):
                    targets.update(_expand_entry_paths(base, value))

        scripts = payload.get("scripts")
        if isinstance(scripts, dict):
            start_script = scripts.get("start")
            if isinstance(start_script, str):
                for match in pattern.findall(start_script):
                    targets.update(_expand_entry_paths(base, match))

    normalized: set[str] = set()
    for target in targets:
        try:
            normalized.add(normalize_path(target.relative_to(scanner.root)))
        except ValueError:
            continue
    return normalized


def _expand_entry_paths(base: Path, entry: str) -> set[Path]:
    cleaned = entry.strip()
    if not cleaned:
        return set()

    candidate = (base / cleaned).resolve()
    if candidate.suffix:
        return {candidate} if candidate.exists() else set()

    results: set[Path] = set()
    for ext in (".js", ".ts", ".mjs", ".cjs", ".jsx", ".tsx", ".mts", ".cts"):
        path = candidate.with_suffix(ext)
        if path.exists():
            results.add(path)
    return results
