from __future__ import annotations

import ast
import re
from typing import Any


class ApplyBlockedError(Exception):
    def __init__(self, message: str, *, conflict: bool = False) -> None:
        super().__init__(message)
        self.conflict = conflict


_IMPORT_PATTERN = re.compile(r"^(from\s+\S+\s+import\s+.+|import\s+.+)$")
_LEGACY_DB_MODULES = {"app.db", "app.database", "app.core.database"}
_DISALLOWED_APP_MAIN_SYMBOLS = {"get_db", "get_db_session"}


def _extract_region_from_legacy_content(content: str, *, ir_ref: str) -> str:
    normalized = content.replace("\r\n", "\n").strip()
    lines = normalized.split("\n")
    start_marker = f"# region {ir_ref}"
    end_marker = f"# endregion {ir_ref}"

    if lines and lines[0].strip() == start_marker:
        lines = lines[1:]
    if lines and lines[-1].strip() == end_marker:
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _find_region_bounds(
    content: str, *, region_start: str, region_end: str
) -> tuple[int, int] | None:
    start = content.find(region_start)
    if start < 0:
        return None
    end = content.find(region_end, start)
    if end < 0:
        return None
    end += len(region_end)
    if end < len(content) and content[end : end + 1] == "\n":
        end += 1
    return start, end


def _render_region(*, region_start: str, region_content: str, region_end: str) -> str:
    body = region_content.rstrip() if region_content.strip() else "pass"
    return f"{region_start}\n{body}\n{region_end}\n"


def _normalize_import_line(line: str) -> str:
    return line.strip()


def _should_drop_existing_import(line: str) -> bool:
    stripped = _normalize_import_line(line)
    if not stripped:
        return False
    try:
        node = ast.parse(stripped).body[0]
    except Exception:
        return False

    if isinstance(node, ast.Import):
        for alias in node.names:
            name = str(alias.name or "").strip()
            if name in _LEGACY_DB_MODULES:
                return True
        return False

    if isinstance(node, ast.ImportFrom):
        if node.level and node.level > 0:
            return False
        module = str(node.module or "").strip()
        if module in _LEGACY_DB_MODULES:
            return True
        if module == "app.main":
            imported = {str(alias.name or "").strip() for alias in node.names}
            if imported & _DISALLOWED_APP_MAIN_SYMBOLS:
                return True
    return False


def _alias_to_text(alias: ast.alias) -> str:
    if alias.asname:
        return f"{alias.name} as {alias.asname}"
    return alias.name


def _consolidate_import_lines(import_lines: list[str]) -> list[str]:
    future_imports: list[str] = []
    plain_imports: dict[str, str] = {}
    from_imports: dict[str, dict[str, str]] = {}
    passthrough: list[str] = []

    for raw_line in import_lines:
        line = _normalize_import_line(raw_line)
        if not line:
            continue
        try:
            node = ast.parse(line).body[0]
        except Exception:
            if line not in passthrough:
                passthrough.append(line)
            continue

        if isinstance(node, ast.Import):
            for alias in node.names:
                plain_imports[alias.name] = _alias_to_text(alias)
            continue

        if isinstance(node, ast.ImportFrom):
            module = "." * int(node.level or 0) + (node.module or "")
            if module == "__future__":
                if line not in future_imports:
                    future_imports.append(line)
                continue
            if any(alias.name == "*" for alias in node.names):
                if line not in passthrough:
                    passthrough.append(line)
                continue
            bucket = from_imports.setdefault(module, {})
            for alias in node.names:
                bucket[alias.name] = _alias_to_text(alias)
            continue

        if line not in passthrough:
            passthrough.append(line)

    out: list[str] = []
    out.extend(future_imports)
    if plain_imports:
        out.append(
            "import " + ", ".join(plain_imports[name] for name in sorted(plain_imports))
        )
    for module in sorted(from_imports):
        aliases = [from_imports[module][name] for name in sorted(from_imports[module])]
        out.append(f"from {module} import " + ", ".join(aliases))
    out.extend(passthrough)
    return out


def _upsert_imports(content: str, imports: list[str]) -> str:
    lines = content.replace("\r\n", "\n").split("\n")
    while lines and lines[-1] == "":
        lines.pop()

    existing_top_level_imports = [
        _normalize_import_line(line)
        for line in lines
        if line == line.lstrip()
        and _IMPORT_PATTERN.match(line.strip())
        and not _should_drop_existing_import(line)
    ]
    consolidated_imports = _consolidate_import_lines(
        existing_top_level_imports + imports
    )

    non_import_lines = [
        line
        for line in lines
        if not (line == line.lstrip() and _IMPORT_PATTERN.match(line.strip()))
    ]

    insert_at = 0
    if non_import_lines and non_import_lines[0].startswith("#!"):
        insert_at = 1

    if insert_at < len(non_import_lines):
        opener = non_import_lines[insert_at].strip()
        if opener.startswith('"""') or opener.startswith("'''"):
            quote = opener[:3]
            if opener.count(quote) >= 2 and len(opener) > 3:
                insert_at += 1
            else:
                insert_at += 1
                while insert_at < len(non_import_lines):
                    if quote in non_import_lines[insert_at]:
                        insert_at += 1
                        break
                    insert_at += 1

    merged_lines = non_import_lines[:insert_at]
    if consolidated_imports:
        merged_lines.extend(consolidated_imports)
        if (
            insert_at < len(non_import_lines)
            and non_import_lines[insert_at].strip() != ""
        ):
            merged_lines.append("")
    merged_lines.extend(non_import_lines[insert_at:])

    merged = "\n".join(merged_lines)
    return merged + ("\n" if not merged.endswith("\n") else "")


def apply_upsert_region(
    *,
    current_content: str,
    operation: dict[str, Any],
    force: bool,
    allow_patch_create: bool = False,
) -> tuple[str, bool]:
    op_type = str(operation.get("operation_type") or "upsert_region")
    if op_type != "upsert_region":
        raise ApplyBlockedError(f"Unsupported operation_type: {op_type}")

    ir_ref = str(operation.get("ir_ref") or "unknown")
    merge_mode = str(operation.get("merge_mode") or "patch")
    region_start = str(operation.get("region_start") or f"# region {ir_ref}")
    region_end = str(operation.get("region_end") or f"# endregion {ir_ref}")

    imports_raw = operation.get("imports")
    imports = (
        [
            str(item).strip()
            for item in imports_raw
            if isinstance(item, str) and str(item).strip()
        ]
        if isinstance(imports_raw, list)
        else []
    )

    region_content = operation.get("region_content")
    if not isinstance(region_content, str) or not region_content.strip():
        legacy = operation.get("content")
        if isinstance(legacy, str) and legacy.strip():
            region_content = _extract_region_from_legacy_content(legacy, ir_ref=ir_ref)
        else:
            region_content = "pass"

    merged = _upsert_imports(current_content, imports)
    new_region = _render_region(
        region_start=region_start, region_content=region_content, region_end=region_end
    )
    bounds = _find_region_bounds(
        merged, region_start=region_start, region_end=region_end
    )

    if merge_mode not in {"create", "append", "patch"}:
        raise ApplyBlockedError(f"Unknown merge_mode: {merge_mode}")

    if bounds is None:
        if merge_mode == "patch" and not force and not allow_patch_create:
            raise ApplyBlockedError(f"Region not found for patch mode: {ir_ref}")
        if not merged.endswith("\n"):
            merged += "\n"
        if merged.strip():
            merged += "\n"
        merged += new_region
        return merged, True

    start, end = bounds
    replaced = merged[:start] + new_region + merged[end:]
    return replaced, replaced != merged
