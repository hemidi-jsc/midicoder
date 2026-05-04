"""Python symbol analyzer."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from ..core.models import ErrorRecord, Symbol
from ..core.scanner import ProjectScanner, normalize_path


class PythonAnalyzer:
    def analyze(
        self, scanner: ProjectScanner, target_files: set[str] | None = None
    ) -> tuple[list[Symbol], list[ErrorRecord]]:
        symbols: list[Symbol] = []
        errors: list[ErrorRecord] = []

        for path in scanner.python_files:
            relative = normalize_path(path.relative_to(scanner.root))
            if target_files is not None and relative not in target_files:
                continue
            file_symbols, file_errors = self._parse_file(scanner, path)
            symbols.extend(file_symbols)
            errors.extend(file_errors)

        return symbols, errors

    def _parse_file(
        self, scanner: ProjectScanner, path: Path
    ) -> tuple[list[Symbol], list[ErrorRecord]]:
        content = scanner.get_content(path)
        if not content:
            return [], []

        relative_path = normalize_path(path.relative_to(scanner.root))
        try:
            tree = ast.parse(content, filename=str(path))
        except SyntaxError as exc:
            fallback_symbols = _extract_fallback_symbols(content, relative_path)
            return fallback_symbols, [
                ErrorRecord(
                    kind="python_syntax_error", file=relative_path, detail=str(exc)
                )
            ]

        visitor = _PythonSymbolVisitor(relative_path)
        visitor.visit(tree)
        block_symbols = _extract_statement_blocks(tree, relative_path)
        visitor.symbols.extend(block_symbols)

        return visitor.symbols, []


class _PythonSymbolVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.class_stack: list[str] = []
        self.function_stack: list[str] = []
        self.symbols: list[Symbol] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        enclosing = [*self.class_stack, *self.function_stack]
        qualified_name = ".".join([*enclosing, node.name]) if enclosing else node.name
        scope = ".".join(enclosing) if enclosing else "module"
        self.symbols.append(
            Symbol(
                name=qualified_name,
                kind="class",
                language="python",
                file=self.file_path,
                line=node.lineno,
                scope=scope,
                signature=None,
            )
        )

        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)

    def _handle_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        is_async = isinstance(node, ast.AsyncFunctionDef)
        inside_function = bool(self.function_stack)
        enclosing = [*self.class_stack, *self.function_stack]
        qualified_name = ".".join([*enclosing, node.name]) if enclosing else node.name

        is_class_method = bool(self.class_stack) and not inside_function
        if is_class_method:
            kind = "async_method" if is_async else "method"
            scope = ".".join(self.class_stack)
        else:
            kind = "async_function" if is_async else "function"
            scope = ".".join(enclosing) if enclosing else "module"

        decorators = [
            d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list[:3]
        ]

        self.symbols.append(
            Symbol(
                name=qualified_name,
                kind=kind,
                language="python",
                file=self.file_path,
                line=node.lineno,
                scope=scope,
                signature=format_python_signature(node, decorators),
            )
        )

        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()


def _extract_statement_blocks(tree: ast.AST, file_path: str) -> list[Symbol]:
    collector = _StatementBlockCollector(file_path)
    collector.collect(tree)
    return collector.symbols


class _StatementBlockCollector:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.symbols: list[Symbol] = []

    def collect(self, node: ast.AST) -> None:
        self._walk(node, scope_stack=[])

    def _walk(self, node: ast.AST, scope_stack: list[str]) -> None:
        body: list[ast.AST] | None = getattr(node, "body", None)
        if not isinstance(body, list):
            return

        block_nodes: list[ast.AST] = [] if not scope_stack else []

        for child in body:
            if isinstance(child, ast.ClassDef):
                if not scope_stack:
                    self._flush_block(block_nodes, scope_stack)
                self._walk(child, scope_stack + [child.name])
                continue

            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not scope_stack:
                    self._flush_block(block_nodes, scope_stack)
                self._walk(child, scope_stack + [child.name])
                continue

            if not scope_stack:
                block_nodes.append(child)

        if not scope_stack:
            self._flush_block(block_nodes, scope_stack)

    def _flush_block(self, nodes: list[ast.AST], scope_stack: list[str]) -> None:
        meaningful = [node for node in nodes if _is_meaningful_statement(node)]
        nodes.clear()
        if not meaningful:
            return

        first = meaningful[0]
        line = getattr(first, "lineno", None)
        if line is None:
            return

        # Double check: if it's only imports/docstrings, skip it
        if all(not _is_meaningful_statement(n) for n in meaningful):
            return

        scope = ".".join(scope_stack) if scope_stack else "module"
        name = _format_block_symbol_name(scope_stack, line)

        self.symbols.append(
            Symbol(
                name=name,
                kind="block",
                language="python",
                file=self.file_path,
                line=line,
                scope=scope,
                signature=None,
            )
        )


def _format_block_symbol_name(scope_stack: list[str], line: int) -> str:
    if scope_stack:
        return ".".join([*scope_stack, f"block_{line}"])
    return f"module_block_{line}"


def _is_meaningful_statement(node: ast.AST) -> bool:
    if isinstance(node, (ast.Pass, ast.Import, ast.ImportFrom)):
        return False
    if isinstance(node, ast.Expr):
        value = getattr(node, "value", None)
        # Skip docstrings and constants at top level/module level
        if isinstance(value, (ast.Constant, ast.Str)):
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return False
            if isinstance(value, ast.Str):
                return False
    return hasattr(node, "lineno")


def format_python_signature(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    decorators: list[str] | None = None,
) -> str:
    args = []
    arguments = node.args

    for arg in getattr(arguments, "posonlyargs", []):
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"
        args.append(arg_str)

    for arg in arguments.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"
        args.append(arg_str)

    if arguments.vararg:
        args.append(f"*{arguments.vararg.arg}")

    for arg in arguments.kwonlyargs:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"
        args.append(arg_str)

    if arguments.kwarg:
        args.append(f"**{arguments.kwarg.arg}")

    sig = f"{node.name}({', '.join(args)})"

    if node.returns:
        sig += f" -> {ast.unparse(node.returns)}"

    if decorators and any(
        d in ("staticmethod", "classmethod", "property") for d in decorators
    ):
        sig = f"[{', '.join(d for d in decorators if d in ('staticmethod', 'classmethod', 'property'))}] {sig}"

    return sig


def _extract_fallback_symbols(content: str, relative_path: str) -> list[Symbol]:
    """Best-effort symbol extraction when AST parsing fails."""
    class_re = re.compile(
        r"^(?P<indent>[ \t]*)class\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b"
    )
    def_re = re.compile(
        r"^(?P<indent>[ \t]*)(?P<async>async\s+)?def\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\("
    )

    symbols: list[Symbol] = []
    class_stack: list[tuple[int, str]] = []
    function_stack: list[tuple[int, str]] = []
    active_block: dict[str, object] | None = None

    def pop_to_indent(indent: int) -> None:
        while function_stack and indent <= function_stack[-1][0]:
            function_stack.pop()
        while class_stack and indent <= class_stack[-1][0]:
            class_stack.pop()

    def flush_block() -> None:
        nonlocal active_block
        if not active_block:
            return
        scope = active_block["scope"]
        if scope != "module":
            active_block = None
            return
        line_no = active_block["line"]
        symbols.append(
            Symbol(
                name=active_block["name"],
                kind="block",
                language="python",
                file=relative_path,
                line=line_no,
                scope=scope,
                signature=None,
            )
        )
        active_block = None

    for line_no, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        raw_indent = line[: len(line) - len(line.lstrip(" \t"))]
        indent = _indent_len(raw_indent)
        pop_to_indent(indent)

        if stripped.startswith("@"):
            continue
        if stripped.startswith("import ") or stripped.startswith("from "):
            continue

        class_match = class_re.match(line)
        if class_match:
            if not function_stack:
                flush_block()
            name = class_match.group("name")
            enclosing_classes = [item[1] for item in class_stack]
            enclosing_functions = [item[1] for item in function_stack]
            components = [*enclosing_classes, *enclosing_functions]
            qualified_name = ".".join([*components, name]) if components else name
            scope = ".".join(components) if components else "module"
            symbols.append(
                Symbol(
                    name=qualified_name,
                    kind="class",
                    language="python",
                    file=relative_path,
                    line=line_no,
                    scope=scope,
                    signature=None,
                )
            )
            class_stack.append((indent, name))
            continue

        def_match = def_re.match(line)
        if def_match:
            if not function_stack:
                flush_block()
            name = def_match.group("name")
            is_async = bool(def_match.group("async"))
            enclosing_classes = [item[1] for item in class_stack]
            enclosing_functions = [item[1] for item in function_stack]
            components = [*enclosing_classes, *enclosing_functions]
            is_class_method = bool(enclosing_classes) and not enclosing_functions

            qualified_name = ".".join([*components, name]) if components else name
            if is_class_method:
                kind = "async_method" if is_async else "method"
                scope = ".".join(enclosing_classes)
            else:
                kind = "async_function" if is_async else "function"
                scope = ".".join(components) if components else "module"

            symbols.append(
                Symbol(
                    name=qualified_name,
                    kind=kind,
                    language="python",
                    file=relative_path,
                    line=line_no,
                    scope=scope,
                    signature=None,
                )
            )
            function_stack.append((indent, name))
            continue

        if function_stack or class_stack:
            continue

        if not active_block:
            active_block = {
                "line": line_no,
                "scope": "module",
                "name": f"module_block_{line_no}",
            }

    flush_block()
    return symbols


def _indent_len(value: str) -> int:
    return len(value.replace("\t", "    "))
