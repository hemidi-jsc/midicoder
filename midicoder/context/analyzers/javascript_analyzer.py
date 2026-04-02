"""JavaScript/TypeScript/TSX symbol analyzer (Tree-sitter)."""

from __future__ import annotations

import ctypes
import logging
from pathlib import Path
import warnings

import tree_sitter_languages
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language

from ..core.models import ErrorRecord, Symbol
from ..core.scanner import ProjectScanner, normalize_path

logger = logging.getLogger(__name__)

LANGUAGE_PARSERS: dict[str, Parser] = {}
PARSER_INIT_ERRORS: dict[str, str] = {}
LANGUAGES_LIBRARY_HANDLE: ctypes.CDLL | None = None

LANGUAGE_SYMBOL_BY_NAME = {
    "javascript": "tree_sitter_javascript",
    "typescript": "tree_sitter_typescript",
    "tsx": "tree_sitter_tsx",
}


def _resolve_languages_library_path() -> Path:
    package_dir = Path(tree_sitter_languages.__file__).resolve().parent
    for candidate in ("languages.dll", "languages.so", "languages.dylib"):
        path = package_dir / candidate
        if path.exists():
            return path
    raise FileNotFoundError(
        f"tree_sitter_languages shared library not found in {package_dir}"
    )


def _get_languages_library_handle() -> ctypes.CDLL:
    global LANGUAGES_LIBRARY_HANDLE
    if LANGUAGES_LIBRARY_HANDLE is None:
        LANGUAGES_LIBRARY_HANDLE = ctypes.CDLL(str(_resolve_languages_library_path()))
    return LANGUAGES_LIBRARY_HANDLE


def _load_language_from_library(language_name: str) -> Language:
    symbol_name = LANGUAGE_SYMBOL_BY_NAME.get(language_name)
    if not symbol_name:
        raise RuntimeError(f"No grammar symbol mapping for language: {language_name}")

    lib = _get_languages_library_handle()
    try:
        loader = getattr(lib, symbol_name)
    except AttributeError as exc:
        raise RuntimeError(
            f"Grammar symbol not found in shared library: {symbol_name}"
        ) from exc

    loader.restype = ctypes.c_void_p
    language_ptr = loader()
    if not language_ptr:
        raise RuntimeError(f"Grammar pointer is null for: {language_name}")

    # Current tree_sitter bindings accept an integer pointer for Language(...).
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="int argument support is deprecated",
            category=DeprecationWarning,
        )
        return Language(language_ptr)


def _get_parser(language_name: str) -> Parser:
    parser = LANGUAGE_PARSERS.get(language_name)
    if parser is None:
        if language_name in PARSER_INIT_ERRORS:
            raise RuntimeError(PARSER_INIT_ERRORS[language_name])

        try:
            language = get_language(language_name)
        except Exception:
            language = _load_language_from_library(language_name)

        parser = Parser()

        if hasattr(parser, "set_language"):
            parser.set_language(language)
        elif hasattr(parser, "language"):
            parser.language = language
        else:
            message = "Unsupported tree_sitter.Parser API"
            PARSER_INIT_ERRORS[language_name] = message
            raise RuntimeError(message)
        LANGUAGE_PARSERS[language_name] = parser
    return parser


def _language_for_path(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix in (".ts", ".mts", ".cts"):
        return "typescript", "typescript"
    if suffix == ".tsx":
        return "tsx", "typescript"
    return "javascript", "javascript"


class JavaScriptAnalyzer:
    def analyze(
        self, scanner: ProjectScanner, target_files: set[str] | None = None
    ) -> tuple[list[Symbol], list[ErrorRecord]]:
        symbols: list[Symbol] = []
        errors: list[ErrorRecord] = []
        parser_by_language: dict[str, Parser | None] = {}

        for path in scanner.js_ts_files:
            relative_path = normalize_path(path.relative_to(scanner.root))
            if target_files is not None and relative_path not in target_files:
                continue
            content = scanner.get_content(path)
            if not content:
                continue

            language_name, language_label = _language_for_path(path)
            parser = parser_by_language.get(language_name)
            if parser is None and language_name not in parser_by_language:
                try:
                    parser = _get_parser(language_name)
                except Exception as exc:
                    parser = None
                    PARSER_INIT_ERRORS[language_name] = str(exc)
                parser_by_language[language_name] = parser

            if parser is None:
                errors.append(
                    ErrorRecord(
                        kind="js_parse_error",
                        file=relative_path,
                        detail=PARSER_INIT_ERRORS.get(
                            language_name, "Parser unavailable"
                        ),
                    )
                )
                continue

            try:
                tree = parser.parse(content.encode("utf-8"))
            except Exception as exc:
                errors.append(
                    ErrorRecord(
                        kind="js_parse_error", file=relative_path, detail=str(exc)
                    )
                )
                continue

            symbols.extend(
                _extract_symbols_from_tree(
                    tree,
                    content.encode("utf-8"),
                    relative_path,
                    language_label,
                )
            )

        return symbols, errors


def _extract_symbols_from_tree(
    tree, source_bytes: bytes, relative_path: str, language: str
) -> list[Symbol]:
    symbols: list[Symbol] = []
    seen: set[tuple[str, int, str]] = set()

    def add_symbol(name: str, kind: str, line: int, scope: str) -> None:
        key = (name, line, kind)
        if key in seen:
            return
        seen.add(key)
        symbols.append(
            Symbol(
                name=name,
                kind=kind,
                language=language,
                file=relative_path,
                line=line,
                scope=scope,
                signature=None,
            )
        )

    def node_text(node) -> str:
        return source_bytes[node.start_byte : node.end_byte].decode(
            "utf-8", errors="ignore"
        )

    def node_line(node) -> int:
        return node.start_point[0] + 1

    def get_name(node) -> str | None:
        if node is None:
            return None
        if node.type in {
            "identifier",
            "property_identifier",
            "private_property_identifier",
        }:
            return node_text(node)
        name_node = node.child_by_field_name("name")
        if name_node:
            return node_text(name_node)
        for child in node.named_children:
            if child.type in {
                "identifier",
                "property_identifier",
                "private_property_identifier",
            }:
                return node_text(child)
        return None

    def handle_class_body(class_node, class_name: str) -> None:
        body = class_node.child_by_field_name("body")
        if body is None:
            for child in class_node.named_children:
                if child.type == "class_body":
                    body = child
                    break
        if body is None:
            return

        for element in body.named_children:
            if element.type == "method_definition":
                method_name = get_name(element)
                if not method_name or method_name == "constructor":
                    continue
                add_symbol(
                    f"{class_name}.{method_name}",
                    "method",
                    node_line(element),
                    class_name,
                )
                continue

            if element.type in {
                "public_field_definition",
                "property_definition",
                "field_definition",
            }:
                field_name = get_name(element)
                if not field_name or field_name == "constructor":
                    continue
                value = element.child_by_field_name("value")
                if value and value.type in {
                    "arrow_function",
                    "function",
                    "function_expression",
                }:
                    add_symbol(
                        f"{class_name}.{field_name}",
                        "method",
                        node_line(element),
                        class_name,
                    )

    def handle_variable_declaration(node, scope: str) -> None:
        for declarator in node.named_children:
            if declarator.type != "variable_declarator":
                continue
            name_node = declarator.child_by_field_name("name")
            value_node = declarator.child_by_field_name("value")
            if not name_node or not value_node:
                continue
            name = get_name(name_node)
            if not name:
                continue
            if value_node.type in {"arrow_function", "function", "function_expression"}:
                add_symbol(name, "function", node_line(declarator), scope)
            elif value_node.type in {"class", "class_expression"}:
                add_symbol(name, "class", node_line(declarator), scope)
                handle_class_body(value_node, name)

    def handle_declaration(node, export_context: bool) -> None:
        scope = "export" if export_context else "module"

        if node.type == "function_declaration":
            name = get_name(node)
            if name:
                add_symbol(name, "function", node_line(node), scope)
            return

        if node.type == "class_declaration":
            name = get_name(node)
            if name:
                add_symbol(name, "class", node_line(node), scope)
                handle_class_body(node, name)
            return

        if node.type in {"lexical_declaration", "variable_declaration"}:
            handle_variable_declaration(node, scope)
            return

        if node.type == "interface_declaration":
            name = get_name(node)
            if name:
                add_symbol(name, "interface", node_line(node), scope)
            return

        if node.type == "type_alias_declaration":
            name = get_name(node)
            if name:
                add_symbol(name, "type", node_line(node), scope)
            return

        if node.type == "enum_declaration":
            name = get_name(node)
            if name:
                add_symbol(name, "enum", node_line(node), scope)
            return

    def handle_export_statement(node) -> None:
        decl = node.child_by_field_name("declaration")
        if decl is not None:
            handle_declaration(decl, export_context=True)
            return

        export_clause = node.child_by_field_name("value")
        if export_clause is None:
            for child in node.named_children:
                if child.type == "export_clause":
                    export_clause = child
                    break
        if export_clause is not None and export_clause.type == "export_clause":
            for spec in export_clause.named_children:
                if spec.type == "export_specifier":
                    identifiers = [
                        child
                        for child in spec.named_children
                        if child.type in {"identifier", "property_identifier"}
                    ]
                    if identifiers:
                        exported_ident = identifiers[-1]
                        add_symbol(
                            node_text(exported_ident),
                            "export",
                            node_line(exported_ident),
                            "export",
                        )
                elif spec.type in {"identifier", "property_identifier"}:
                    add_symbol(node_text(spec), "export", node_line(spec), "export")
            return

        snippet = node_text(node)
        if "default" not in snippet:
            return

        ident = None
        for child in node.named_children:
            if child.type in {"identifier", "property_identifier"}:
                ident = child
                break
        if ident is not None:
            add_symbol(node_text(ident), "export", node_line(ident), "export")
        else:
            add_symbol("default", "export", node_line(node), "export")

    def traverse(node, export_context: bool = False) -> None:
        if node.type == "export_statement":
            handle_export_statement(node)
            return

        if node.type == "internal_module":
            body = node.child_by_field_name("body")
            if body is None:
                for child in node.named_children:
                    if child.type == "statement_block":
                        body = child
                        break
            if body is not None:
                for child in body.named_children:
                    traverse(child, export_context=export_context)
            return

        if node.type in {
            "function_declaration",
            "class_declaration",
            "lexical_declaration",
            "variable_declaration",
            "interface_declaration",
            "type_alias_declaration",
            "enum_declaration",
        }:
            handle_declaration(node, export_context=export_context)
            return

        for child in node.named_children:
            traverse(child, export_context=export_context)

    traverse(tree.root_node, export_context=False)

    return symbols
