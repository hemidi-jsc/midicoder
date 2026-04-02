from __future__ import annotations

import re

_IMPORT_RE = re.compile(r"^(from\s+[A-Za-z0-9_\.]+\s+import\s+.+|import\s+.+)$")
_FROM_RE = re.compile(r"^from\s+([A-Za-z0-9_\.]+)\s+import\s+(.+)$")
_PLAIN_IMPORT_RE = re.compile(r"^import\s+(.+)$")
_ROUTER_RE = re.compile(r"^router\s*=\s*APIRouter\((.*)\)\s*$")


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _normalize_imports(
    import_lines: list[str],
) -> tuple[list[str], set[str], dict[str, set[str]], set[str]]:
    from_map: dict[str, set[str]] = {}
    plain_map: set[str] = set()
    passthrough: list[str] = []
    raw_seen: set[str] = set()

    for line in import_lines:
        raw = line.strip()
        raw_seen.add(raw)

        from_match = _FROM_RE.match(raw)
        if from_match:
            module = from_match.group(1)
            names = _split_csv(from_match.group(2))
            from_map.setdefault(module, set()).update(names)
            continue

        plain_match = _PLAIN_IMPORT_RE.match(raw)
        if plain_match:
            names = _split_csv(plain_match.group(1))
            plain_map.update(names)
            continue

        passthrough.append(raw)

    normalized: list[str] = []
    for module in sorted(from_map):
        normalized.append(f"from {module} import {', '.join(sorted(from_map[module]))}")
    if plain_map:
        normalized.append(f"import {', '.join(sorted(plain_map))}")
    normalized.extend(sorted(set(passthrough)))
    semantic_imports = {
        f"from {module} import {name}"
        for module, names in from_map.items()
        for name in names
    } | {f"import {name}" for name in plain_map}
    return normalized, raw_seen, from_map, plain_map


def _line_semantics(raw: str) -> set[str]:
    from_match = _FROM_RE.match(raw)
    if from_match:
        module = from_match.group(1)
        return {
            f"from {module} import {name}" for name in _split_csv(from_match.group(2))
        }
    plain_match = _PLAIN_IMPORT_RE.match(raw)
    if plain_match:
        return {f"import {name}" for name in _split_csv(plain_match.group(1))}
    return set()


def harmonize_python_file(content: str) -> str:
    lines = content.replace("\r\n", "\n").split("\n")
    cleaned = []
    for line in lines:
        if line.strip().startswith("```"):
            continue
        cleaned.append(line.rstrip())
    lines = cleaned

    imports: list[str] = []
    body: list[str] = []
    router_candidates: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == "from __future__ import annotations":
            continue
        if stripped and not line.startswith((" ", "\t")) and _IMPORT_RE.match(stripped):
            imports.append(stripped)
            continue
        if stripped and not line.startswith((" ", "\t")) and _ROUTER_RE.match(stripped):
            router_candidates.append(stripped)
            continue
        body.append(line)

    router_line = ""
    if router_candidates:
        # Prefer the most specific APIRouter assignment (typically with prefix/tags).
        router_line = max(router_candidates, key=len)

    normalized_imports, raw_seen, from_map, plain_map = _normalize_imports(imports)
    hoisted_semantics = {
        f"from {module} import {name}"
        for module, names in from_map.items()
        for name in names
    } | {f"import {name}" for name in plain_map}

    out: list[str] = ["from __future__ import annotations", ""]
    if normalized_imports:
        out.extend(normalized_imports)
        out.append("")
    if router_line:
        out.append(router_line)
        out.append("")

    out.extend(body)

    deduped: list[str] = []
    for line in out:
        stripped = line.strip()
        # Remove local imports duplicated (exact or subset) by hoisted imports.
        if line.startswith((" ", "\t")) and _IMPORT_RE.match(stripped):
            semantics = _line_semantics(stripped)
            if stripped in raw_seen or (
                semantics and semantics.issubset(hoisted_semantics)
            ):
                continue
        if (
            line.startswith((" ", "\t"))
            and stripped in raw_seen
            and _IMPORT_RE.match(stripped)
        ):
            continue
        deduped.append(line)

    normalized: list[str] = []
    blank_count = 0
    for line in deduped:
        if line.strip() == "":
            blank_count += 1
        else:
            blank_count = 0
        if blank_count <= 1:
            normalized.append(line)

    text = "\n".join(normalized).strip() + "\n"
    return text
