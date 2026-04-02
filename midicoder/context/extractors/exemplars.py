"""Exemplar extraction utilities."""

from __future__ import annotations

import ast
from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
import logging
import re
from pathlib import Path

from ..core.models import Exemplar, Symbol
from ..core.scanner import ProjectScanner, normalize_path
from .constants import (
    EXEMPLAR_PATTERN_AFTER,
    EXEMPLAR_PATTERN_BEFORE,
    MAX_EXEMPLARS,
    MAX_FILES_FOR_EXEMPLARS,
    SNIPPET_CONTEXT_AFTER,
    SNIPPET_CONTEXT_BEFORE,
    SNIPPET_MIN_LENGTH,
)

logger = logging.getLogger(__name__)


FRAMEWORK_MARKERS = (
    r"@Controller",
    r"@app\.",
    r"\brouter\.",
)
ROLE_NAMES = ("Controller", "Service", "Repository", "Handler", "Module")
PATH_MARKERS = ("src/", "app/", "modules/", "services/", "controllers/")
STRUCTURE_RE = re.compile(
    r"\b(class|def|func|interface|struct|module|namespace)\b", re.IGNORECASE
)
TEST_PATH_RE = re.compile(
    r"(?:^|/)(test|tests|spec|__tests__|mock|mocks|fixtures)(?:/|$)", re.IGNORECASE
)


DEFAULT_SCORING = {
    "marker_weight": 0.15,
    "role_weight": 0.10,
    "path_weight": 0.05,
    "structure_weight": 0.05,
    "length_factor": 0.10,
    "length_center": 20,
    "length_scale": 40,
    "softcap_threshold": 0.90,
    "softcap_scale": 0.50,
    "markers": FRAMEWORK_MARKERS,
    "roles": ROLE_NAMES,
    "paths": PATH_MARKERS,
}

STACK_SCORING = {
    "fastapi": {
        "markers": (
            r"@(?:app|router)\.",
            r"\bAPIRouter\(",
            r"\bFastAPI\(",
            r"\bDepends\(",
            r"\bResponse\(",
        ),
        "paths": ("src/", "app/", "api/", "routers/", "routes/"),
        "marker_weight": 0.20,
        "role_weight": 0.12,
        "path_weight": 0.07,
        "structure_weight": 0.06,
        "softcap_scale": 0.70,
    },
    "nest": {
        "markers": (
            r"@Controller\(",
            r"@Module\(",
            r"@Injectable\(",
            r"@Get\(",
            r"@Post\(",
            r"@Put\(",
            r"@Delete\(",
            r"@Patch\(",
        ),
        "roles": (
            "Controller",
            "Service",
            "Repository",
            "Handler",
            "Module",
            "Provider",
            "Guard",
            "Interceptor",
        ),
        "paths": (
            "src/",
            "app/",
            "modules/",
            "controllers/",
            "services/",
            "providers/",
        ),
        "marker_weight": 0.20,
        "role_weight": 0.12,
        "path_weight": 0.07,
        "structure_weight": 0.06,
        "softcap_scale": 0.70,
    },
    "angular": {
        "markers": (
            r"@Component\(",
            r"@Injectable\(",
            r"@Directive\(",
            r"@NgModule\(",
        ),
        "roles": (
            "Component",
            "Service",
            "Module",
            "Directive",
            "Pipe",
        ),
        "paths": ("src/", "app/", "modules/", "components/", "services/", "pipes/"),
        "marker_weight": 0.20,
        "role_weight": 0.12,
        "path_weight": 0.07,
        "structure_weight": 0.06,
        "softcap_scale": 0.70,
    },
    "express": {
        "markers": (
            r"(?:app|router)\.\w+\(",
            r"\bexpress\(",
        ),
        "paths": ("src/", "app/", "routes/", "routers/", "controllers/"),
        "marker_weight": 0.18,
        "role_weight": 0.11,
        "path_weight": 0.06,
        "structure_weight": 0.05,
        "softcap_scale": 0.65,
    },
}

LANGUAGE_LENGTH = {
    "python": {"length_center": 20, "length_scale": 45, "length_factor": 0.10},
    "typescript": {"length_center": 24, "length_scale": 50, "length_factor": 0.08},
    "javascript": {"length_center": 24, "length_scale": 50, "length_factor": 0.08},
}


def resolve_scoring_config(stack: str | None, language: str | None) -> dict:
    config = dict(DEFAULT_SCORING)
    if stack and stack in STACK_SCORING:
        override = STACK_SCORING[stack]
        config.update(override)
    if language and language in LANGUAGE_LENGTH:
        config.update(LANGUAGE_LENGTH[language])
    return config


def _limit_files(paths: list[Path], limit: int | None) -> list[Path]:
    if limit is None:
        return list(paths)
    return list(paths[:limit])


def compute_exemplar_score(
    base_source: str,
    snippet: str,
    file_path: str,
    symbol_name: str | None,
    stack: str | None,
    language: str | None,
) -> float:
    config = resolve_scoring_config(stack, language)
    base = 0.65 if base_source == "symbol" else 0.45
    score = base

    marker_matches = sum(
        1 for marker in config["markers"] if re.search(marker, snippet)
    )
    if marker_matches:
        score += config["marker_weight"] * min(1.0, marker_matches / 2.0)

    if symbol_name:
        role_matches = sum(
            1 for role in config["roles"] if role.lower() in symbol_name.lower()
        )
        if role_matches:
            score += config["role_weight"] * min(1.0, role_matches / 2.0)

    normalized_path = file_path.replace("\\", "/")
    path_matches = sum(
        1 for marker in config["paths"] if marker in normalized_path.lower()
    )
    if path_matches:
        score += config["path_weight"] * min(1.0, path_matches / 2.0)

    structure_matches = len(list(STRUCTURE_RE.finditer(snippet)))
    if structure_matches:
        score += config["structure_weight"] * min(1.0, structure_matches / 3.0)

    # Add a small continuous signal so scores do not collapse into a few buckets.
    identifier_tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", snippet)
    if identifier_tokens:
        unique_ratio = len({token.lower() for token in identifier_tokens}) / len(
            identifier_tokens
        )
        diversity_signal = max(0.0, min(1.0, (unique_ratio - 0.20) / 0.60))
        score += 0.04 * diversity_signal

    decorator_hits = snippet.count("@")
    if decorator_hits:
        score += min(0.03, decorator_hits * 0.01)

    if TEST_PATH_RE.search(normalized_path):
        score -= 0.20

    lines_count = len(snippet.splitlines())
    length_penalty = config["length_factor"] * min(
        1.0, abs(lines_count - config["length_center"]) / config["length_scale"]
    )
    score -= length_penalty

    if score > config["softcap_threshold"]:
        score = (
            config["softcap_threshold"]
            + (score - config["softcap_threshold"]) * config["softcap_scale"]
        )

    score = max(0.05, min(0.98, score))
    score = 0.15 + 0.85 * score
    score = max(0.05, min(0.98, score))
    return round(score, 3)


def extract_exemplars(
    scanner: ProjectScanner,
    symbols: list[Symbol],
    stack: str,
    target_files: set[str] | None = None,
) -> list[Exemplar]:
    exemplars: list[Exemplar] = []

    symbol_map = {(symbol.file, symbol.line): symbol for symbol in symbols}
    symbol_line_index = _build_symbol_line_index(symbols)

    for path in _limit_files(scanner.python_files, MAX_FILES_FOR_EXEMPLARS):
        relative_path = normalize_path(path.relative_to(scanner.root))
        if target_files is not None and relative_path not in target_files:
            continue
        exemplars.extend(
            extract_exemplars_from_file(scanner, path, symbol_map, "python", stack)
        )

    for path in _limit_files(scanner.js_ts_files, MAX_FILES_FOR_EXEMPLARS):
        relative_path = normalize_path(path.relative_to(scanner.root))
        if target_files is not None and relative_path not in target_files:
            continue
        is_ts = path.suffix in (".ts", ".tsx", ".mts", ".cts")
        lang = "typescript" if is_ts else "javascript"
        exemplars.extend(
            extract_exemplars_from_file(scanner, path, symbol_map, lang, stack)
        )

    exemplars.extend(
        extract_pattern_exemplars(
            scanner,
            stack,
            target_files=target_files,
            symbol_line_index=symbol_line_index,
        )
    )

    result = dedupe_exemplars(exemplars)[:MAX_EXEMPLARS]
    logger.debug(
        f"Extracted {len(result)} exemplars (deduplicated from {len(exemplars)})"
    )
    return result


def extract_exemplars_from_file(
    scanner: ProjectScanner,
    path: Path,
    symbol_map: dict[tuple[str, int], Symbol],
    language: str,
    stack: str,
) -> list[Exemplar]:
    content = scanner.get_content(path)
    if not content:
        return []

    lines = content.splitlines()
    exemplars: list[Exemplar] = []
    relative_path = normalize_path(path.relative_to(scanner.root))

    for (file_path, line_number), symbol in symbol_map.items():
        if file_path != relative_path:
            continue

        snippet = extract_symbol_snippet(
            lines,
            line_number - 1,
            language=language,
            default_before=SNIPPET_CONTEXT_BEFORE,
            default_after=SNIPPET_CONTEXT_AFTER,
            symbol_kind=symbol.kind,
        )
        if snippet:
            exemplar_kind = map_symbol_to_exemplar_kind(symbol.kind)
            score = compute_exemplar_score(
                "symbol",
                snippet,
                file_path,
                symbol.name,
                stack=stack,
                language=language,
            )
            exemplars.append(
                Exemplar(
                    kind=exemplar_kind,
                    language=language,
                    file=file_path,
                    line=line_number,
                    snippet=snippet,
                    score=score,
                    source_symbol=symbol.name,
                )
            )

    return exemplars


def extract_pattern_exemplars(
    scanner: ProjectScanner,
    stack: str,
    target_files: set[str] | None = None,
    symbol_line_index: dict[str, tuple[list[int], list[Symbol]]] | None = None,
) -> list[Exemplar]:
    patterns: list[tuple[str, str, re.Pattern[str]]] = []
    python_pattern_kinds: set[str] = set()

    if stack == "fastapi":
        python_pattern_kinds.update({"command_handler", "dependency", "pydantic_model"})

    python_pattern_kinds.update({"repository", "workflow"})

    if stack == "nest":
        patterns.extend(
            [
                (
                    "controller",
                    "typescript",
                    re.compile(r"@Controller\(", re.MULTILINE),
                ),
                ("provider", "typescript", re.compile(r"@Injectable\(", re.MULTILINE)),
                ("module", "typescript", re.compile(r"@Module\(", re.MULTILINE)),
            ]
        )

    if stack == "express":
        patterns.extend(
            [
                (
                    "route",
                    "javascript",
                    re.compile(r"(?:app|router)\.\w+\(['\"]", re.MULTILINE),
                ),
                (
                    "middleware",
                    "javascript",
                    re.compile(r"function\s+\w+\(req,\s*res,\s*next\)", re.MULTILINE),
                ),
            ]
        )

    if stack == "angular":
        patterns.extend(
            [
                ("component", "typescript", re.compile(r"@Component\(", re.MULTILINE)),
                ("service", "typescript", re.compile(r"@Injectable\(", re.MULTILINE)),
                ("directive", "typescript", re.compile(r"@Directive\(", re.MULTILINE)),
            ]
        )

    patterns.extend(
        [
            (
                "repository",
                "typescript",
                re.compile(r"class\s+\w+Repository\s*{", re.MULTILINE),
            ),
            (
                "repository",
                "javascript",
                re.compile(r"class\s+\w+Repository\s*{", re.MULTILINE),
            ),
        ]
    )

    # Workflow pattern
    patterns.extend(
        [
            (
                "workflow",
                "typescript",
                re.compile(r"class\s+\w+Workflow\s*{", re.MULTILINE),
            ),
            (
                "workflow",
                "javascript",
                re.compile(r"class\s+\w+Workflow\s*{", re.MULTILINE),
            ),
        ]
    )

    exemplars: list[Exemplar] = []

    files_to_scan: list[Path] = []
    seen_files: set[Path] = set()

    def enqueue(paths: list[Path]) -> None:
        for candidate in _limit_files(paths, MAX_FILES_FOR_EXEMPLARS):
            if candidate in seen_files:
                continue
            seen_files.add(candidate)
            files_to_scan.append(candidate)

    if python_pattern_kinds:
        enqueue(scanner.python_files)

    if any(p[1] in ("typescript", "javascript") for p in patterns):
        enqueue(scanner.js_ts_files)

    # If no specific stack, scan all
    if not files_to_scan:
        enqueue(scanner.python_files)
        enqueue(scanner.js_ts_files)

    for path in files_to_scan:
        relative_path = normalize_path(path.relative_to(scanner.root))
        if target_files is not None and relative_path not in target_files:
            continue
        content = scanner.get_content(path)
        if not content:
            continue
        lines = content.splitlines()

        # Determine language from file extension
        if path.suffix == ".py":
            language = "python"
        elif path.suffix in (".ts", ".tsx", ".mts", ".cts"):
            language = "typescript"
        elif path.suffix in (".js", ".jsx"):
            language = "javascript"
        elif path.suffix == ".java":
            language = "java"
        else:
            continue

        if language == "python":
            if not python_pattern_kinds:
                continue
            exemplars.extend(
                extract_python_pattern_exemplars_ast(
                    content=content,
                    lines=lines,
                    relative_path=relative_path,
                    stack=stack,
                    pattern_kinds=python_pattern_kinds,
                )
            )
            continue

        for kind, target_language, pattern in patterns:
            if target_language != language:
                continue

            for match in pattern.finditer(content):
                line_number = content[: match.start()].count("\n") + 1

                if symbol_line_index:
                    nearest_symbol = _find_nearest_symbol(
                        symbol_line_index,
                        relative_path,
                        line_number,
                    )
                    if nearest_symbol and abs(nearest_symbol.line - line_number) <= 3:
                        # AST already produced an exemplar for this symbol; skip duplicate pattern.
                        continue
                lines = content.splitlines()
                snippet = extract_snippet_window(
                    lines,
                    line_number - 1,
                    EXEMPLAR_PATTERN_BEFORE,
                    EXEMPLAR_PATTERN_AFTER,
                )

                if snippet and len(snippet) > SNIPPET_MIN_LENGTH:
                    score = compute_exemplar_score(
                        "pattern",
                        snippet,
                        relative_path,
                        None,
                        stack=stack,
                        language=language,
                    )
                    exemplars.append(
                        Exemplar(
                            kind=kind,
                            language=language,
                            file=relative_path,
                            line=line_number,
                            snippet=snippet,
                            score=score,
                            source_symbol=None,
                        )
                    )

    return exemplars


def dedupe_exemplars(exemplars: list[Exemplar]) -> list[Exemplar]:
    grouped: dict[tuple[str, int], list[Exemplar]] = {}
    for exemplar in exemplars:
        key = (exemplar.file, exemplar.line)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(exemplar)

    result: list[Exemplar] = []
    base_kinds = {"type", "function", "method", "export", "class", "enum"}

    for group in grouped.values():
        if len(group) == 1:
            result.append(group[0])
            continue

        specifics = [e for e in group if e.kind not in base_kinds]
        if specifics:
            result.append(max(specifics, key=lambda e: e.score))
        else:
            result.append(max(group, key=lambda e: e.score))

    return result


def map_symbol_to_exemplar_kind(kind: str) -> str:
    mapping = {
        "class": "type",
        "interface": "type",
        "enum": "enum",
        "type": "type",
        "function": "function",
        "method": "method",
        "export": "export",
    }
    return mapping.get(kind, kind)


def extract_snippet_window(
    lines: list[str], line_index: int, before: int, after: int
) -> str:
    start = max(line_index - before, 0)
    end = min(line_index + after, len(lines))

    snippet = "\n".join(lines[start:end]).strip()
    return snippet


def extract_python_pattern_exemplars_ast(
    content: str,
    lines: list[str],
    relative_path: str,
    stack: str,
    pattern_kinds: set[str],
) -> list[Exemplar]:
    if not pattern_kinds:
        return []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    extractor = _PythonPatternExtractor(pattern_kinds)
    extractor.visit(tree)

    exemplars: list[Exemplar] = []

    for match in extractor.matches:
        snippet = extract_symbol_snippet(
            lines,
            match.line_index,
            language="python",
            default_before=SNIPPET_CONTEXT_BEFORE,
            default_after=SNIPPET_CONTEXT_AFTER,
            symbol_kind=match.kind,
        )
        if not snippet:
            continue

        score = compute_exemplar_score(
            "pattern",
            snippet,
            relative_path,
            match.symbol_name,
            stack=stack,
            language="python",
        )
        exemplars.append(
            Exemplar(
                kind=match.kind,
                language="python",
                file=relative_path,
                line=match.line_index + 1,
                snippet=snippet,
                score=score,
                source_symbol=match.symbol_name,
            )
        )

    return exemplars


def _count_parens(line: str, in_quote: str | None = None) -> tuple[int, str | None]:
    """Returns (paren_diff, new_quote_state). Handle triple quotes crudely."""
    line = line.split("#")[0]
    diff = 0
    idx = 0
    while idx < len(line):
        if in_quote:
            if line[idx : idx + 3] == in_quote:
                in_quote = None
                idx += 3
            elif line[idx] == "\\" and idx + 1 < len(line):
                idx += 2
            elif (
                line[idx : idx + 1] == in_quote[0] and in_quote[1:] == ""
            ):  # Single quote case
                in_quote = None
                idx += 1
            else:
                idx += 1
            continue

        if line[idx : idx + 3] in ('"""', "'''"):
            in_quote = line[idx : idx + 3]
            idx += 3
            continue
        if line[idx] in ('"', "'"):
            # Simple check for single line quotes
            char = line[idx]
            in_quote = char
            idx += 1
            continue

        if line[idx] in "([{":
            diff += 1
        elif line[idx] in ")]}":
            diff -= 1
        idx += 1
    return diff, in_quote


def extract_symbol_snippet(
    lines: list[str],
    line_index: int,
    *,
    language: str,
    default_before: int,
    default_after: int,
    symbol_kind: str | None = None,
) -> str:
    if language != "python" or line_index >= len(lines):
        return extract_snippet_window(lines, line_index, default_before, default_after)

    if symbol_kind == "block":
        snippet = _extract_python_block_snippet(lines, line_index)
        if snippet:
            return snippet

    start = max(line_index - default_before, 0)
    block_start = line_index

    # Include contiguous decorators immediately above the definition.
    # IMPORTANT: stop at blank lines — do NOT cross them, as that would
    # pull in decorators/comments that belong to a preceding sibling.
    while block_start - 1 >= 0:
        prev_line = lines[block_start - 1]
        stripped = prev_line.strip()
        if stripped.startswith("@"):
            # Real decorator — include it and keep scanning upward.
            block_start -= 1
            continue
        # Blank line or any other non-decorator line → stop.
        break

    indent_width = _leading_space_width(lines[line_index])
    end = line_index + 1
    paren_depth, in_quote = _count_parens(lines[line_index])

    while end < len(lines):
        line = lines[end]
        stripped = line.strip()

        had_context = paren_depth > 0 or in_quote is not None
        diff, in_quote = _count_parens(line, in_quote)

        if not stripped:
            end += 1
            continue

        if had_context:
            paren_depth += diff
            end += 1
            continue

        current_indent = _leading_space_width(line)
        if current_indent <= indent_width:
            break

        paren_depth += diff
        end += 1

    # `end` now points exactly past the last line that belongs to this
    # symbol's block.  Do NOT add extra padding lines here — for indented
    # symbols (methods/nested functions) that would bleed into the next
    # sibling's body.  For top-level symbols the block detection already
    # walked to the natural end of the definition.
    block_end = end

    # Compute a safe start point to include context like class signatures or comments
    # without bleeding into the preceding sibling method's code.
    safe_start = block_start
    while safe_start - 1 >= start:
        line_above = lines[safe_start - 1]
        stripped_above = line_above.strip()

        # Blank lines or comments are generally safe to include as context.
        if not stripped_above or stripped_above.startswith("#"):
            safe_start -= 1
            continue

        # Lines with strictly less indentation are enclosing scopes.
        # Include them for blocks, but skip for methods/classes to avoid redundancy.
        if _leading_space_width(line_above) < indent_width:
            if symbol_kind == "block":
                safe_start -= 1
                continue
            break

        # Anything else with >= indentation is likely code from the previous block.
        break

    MAX_LINES = 100
    if block_end - safe_start > MAX_LINES:
        block_end = safe_start + MAX_LINES

    snippet_lines = lines[safe_start:block_end]
    snippet = "\n".join(snippet_lines).strip()
    return snippet or extract_snippet_window(
        lines, line_index, default_before, default_after
    )


def _extract_python_block_snippet(lines: list[str], line_index: int) -> str:
    indent_width = _leading_space_width(lines[line_index])
    start = line_index

    while start - 1 >= 0:
        prev_line = lines[start - 1]
        stripped_prev = prev_line.strip()
        if not stripped_prev:
            start -= 1
            continue
        if stripped_prev.startswith("#"):
            start -= 1
            continue
        break

    if indent_width == 0:
        start = _extend_with_import_block(lines, start)

    end = line_index + 1
    while end < len(lines):
        line = lines[end]
        stripped = line.strip()
        if not stripped:
            end += 1
            continue
        if stripped.startswith("#"):
            end += 1
            continue
        current_indent = _leading_space_width(line)
        if current_indent < indent_width:
            break
        lowered = stripped.lower()
        if (
            lowered.startswith("class ")
            or lowered.startswith("def ")
            or lowered.startswith("async def ")
        ):
            break
        if stripped.startswith("@") and end + 1 < len(lines):
            next_line = lines[end + 1].lstrip()
            next_lower = next_line.lower()
            if (
                next_lower.startswith("class ")
                or next_lower.startswith("def ")
                or next_lower.startswith("async def ")
            ):
                break
        end += 1

    snippet = "\n".join(lines[start:end]).strip()
    if snippet:
        return snippet
    return extract_snippet_window(
        lines, line_index, SNIPPET_CONTEXT_BEFORE, SNIPPET_CONTEXT_AFTER
    )


def _leading_space_width(line: str) -> int:
    expanded = line.replace("\t", "    ")
    return len(expanded) - len(expanded.lstrip(" "))


@dataclass(frozen=True)
class _PythonPatternMatch:
    kind: str
    symbol_name: str | None
    line_index: int


class _PythonPatternExtractor(ast.NodeVisitor):
    def __init__(self, pattern_kinds: set[str]) -> None:
        self.pattern_kinds = pattern_kinds
        self.matches: list[_PythonPatternMatch] = []
        self.class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if "pydantic_model" in self.pattern_kinds and _is_base_model_class(node):
            self._add_match("pydantic_model", node.name, node.lineno - 1)
        if "repository" in self.pattern_kinds and node.name.endswith("Repository"):
            self._add_match("repository", node.name, node.lineno - 1)
        if "workflow" in self.pattern_kinds and node.name.endswith("Workflow"):
            self._add_match("workflow", node.name, node.lineno - 1)

        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)
        self.generic_visit(node)

    def _handle_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualified_name = self._qualified_name(node.name)
        if "command_handler" in self.pattern_kinds and _has_fastapi_route_decorator(
            node
        ):
            self._add_match("command_handler", qualified_name, node.lineno - 1)
        if "dependency" in self.pattern_kinds and _function_contains_depends(node):
            self._add_match("dependency", qualified_name, node.lineno - 1)

    def _qualified_name(self, name: str) -> str:
        if not self.class_stack:
            return name
        return ".".join((*self.class_stack, name))

    def _add_match(self, kind: str, symbol_name: str, line_index: int) -> None:
        self.matches.append(
            _PythonPatternMatch(
                kind=kind, symbol_name=symbol_name, line_index=line_index
            )
        )


def _is_base_model_class(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if _node_basename(base) in {
            "BaseModel",
            "BaseSettings",
            "SQLModel",
            "RootModel",
        }:
            return True
    return False


def _node_basename(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _node_root_name(node: ast.AST) -> str | None:
    current = node
    while isinstance(current, ast.Attribute):
        current = current.value
    if isinstance(current, ast.Name):
        return current.id
    return None


def _has_fastapi_route_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        root = _node_root_name(target)
        if root in {"app", "router"}:
            return True
    return False


def _function_contains_depends(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if _node_basename(child.func) == "Depends":
                return True
    return False


def _extend_with_import_block(lines: list[str], start_index: int) -> int:
    """Extend snippet upward to include contiguous top-level import blocks."""
    idx = start_index - 1
    if idx < 0:
        return start_index

    import_seen = False
    pending_lines: list[int] = []
    confirmed_lines: list[int] = []
    paren_balance = 0  # Tracks unmatched closing parens seen while scanning upward

    while idx >= 0:
        line = lines[idx]
        stripped = line.strip()
        delta, _ = _count_parens(line)
        paren_delta = -delta

        if not stripped or stripped.startswith("#"):
            target = confirmed_lines if import_seen else pending_lines
            target.append(idx)
            idx -= 1
            continue

        if stripped.startswith(("import ", "from ")):
            import_seen = True
            confirmed_lines.append(idx)
            if pending_lines:
                confirmed_lines.extend(pending_lines)
                pending_lines.clear()
            idx -= 1
            paren_balance = max(0, paren_balance + paren_delta)
            continue

        continuation = False
        if paren_balance > 0 or paren_delta > 0:
            continuation = True
        elif stripped.endswith("\\"):
            continuation = True
        elif _looks_like_import_continuation(stripped):
            continuation = True

        if continuation:
            target = confirmed_lines if import_seen else pending_lines
            target.append(idx)
            idx -= 1
            paren_balance = max(0, paren_balance + paren_delta)
            continue

        if not import_seen:
            pending_lines.clear()
            paren_balance = 0
            idx -= 1
            break

        break

    if not import_seen:
        return start_index

    return min(confirmed_lines) if confirmed_lines else start_index


def _looks_like_import_continuation(line: str) -> bool:
    stripped = line.lstrip()
    if not stripped:
        return False
    if stripped[0] in ")]}":
        return True
    if stripped[0] in "([{":
        return True
    if stripped.endswith(",") and (":" not in stripped and "=" not in stripped):
        return True
    # Lines that look like alias entries: "Foo as Bar" or "Foo"
    tokens = [token for token in stripped.replace(",", " ").split() if token]
    if tokens and all(token in {"as"} or token.isidentifier() for token in tokens):
        return True
    return False


def _build_symbol_line_index(
    symbols: list[Symbol],
) -> dict[str, tuple[list[int], list[Symbol]]]:
    grouped: dict[str, list[Symbol]] = defaultdict(list)
    for symbol in symbols:
        grouped[symbol.file].append(symbol)

    index: dict[str, tuple[list[int], list[Symbol]]] = {}
    for file_path, items in grouped.items():
        sorted_items = sorted(items, key=lambda s: s.line)
        index[file_path] = ([symbol.line for symbol in sorted_items], sorted_items)
    return index


def _find_nearest_symbol(
    symbol_line_index: dict[str, tuple[list[int], list[Symbol]]],
    file_path: str,
    line_number: int,
) -> Symbol | None:
    entry = symbol_line_index.get(file_path)
    if not entry:
        return None

    lines, symbols = entry
    pos = bisect_left(lines, line_number)

    candidates: list[Symbol] = []
    if pos < len(symbols):
        candidates.append(symbols[pos])
    if pos > 0:
        candidates.append(symbols[pos - 1])

    if not candidates:
        return None

    return min(candidates, key=lambda symbol: abs(symbol.line - line_number))
