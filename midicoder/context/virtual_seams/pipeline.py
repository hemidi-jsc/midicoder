from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .io import (
    load_entrypoint_virtual_seams,
    load_exemplar_virtual_seams,
    load_real_seams,
    load_symbol_virtual_seams,
)
from .utils import (
    _coerce_float,
    _coerce_line,
    _is_exemplar_source,
    _strip_internal_fields,
)


def deduplicate_virtual_seams(seams: Iterable[dict]) -> list[dict]:
    """Phase 4: Deduplicate virtual seams."""
    # Pass 1: Deduplicate by (file, group_id).
    # Keeps the best source for each conceptual "seam group" in a file.
    by_group: dict[tuple[str, str], list[dict]] = {}

    for seam in seams:
        if not isinstance(seam, dict):
            continue
        file_path = str(seam.get("file", "")).strip()
        group_id = str(seam.get("group_id", "")).strip()
        if not file_path or not group_id:
            continue
        by_group.setdefault((file_path, group_id), []).append(seam)

    temp_deduped: list[dict] = []
    for (_, _), items in sorted(
        by_group.items(), key=lambda entry: (entry[0][0], entry[0][1])
    ):
        best = sorted(
            items,
            key=lambda item: (
                -_coerce_float(item.get("confidence"), 0.0),
                -_is_exemplar_source(item),
                _coerce_line(item.get("line")) or 0,
            ),
        )[0]
        temp_deduped.append(best)

    # Pass 2: Deduplicate by (file, line).
    # If multiple different group_ids point to the exact same line, they likely
    # represent the same code block (e.g. a class being both 'controller' and 'pydantic_model').
    # We keep the one with the more specific or "better" detail/group_id.
    by_line: dict[tuple[str, int], list[dict]] = {}
    for seam in temp_deduped:
        file_path = str(seam.get("file", "")).strip()
        line = _coerce_line(seam.get("line"))
        if line is None:
            continue
        by_line.setdefault((file_path, line), []).append(seam)

    final_deduped: list[dict] = []

    # Priority for kinds when line is the same
    KIND_PRIORITY = {
        "controller": 10,
        "entrypoint": 9,
        "workflow": 8,
        "service": 7,
        "repository": 6,
        "command_handler": 5,
        "dependency": 4,
        "pydantic_model": 3,
        "model": 2,
        "type": 1,
        "function": 1,
        "async_function": 1,
        "method": 1,
    }

    def _get_seam_priority(item: dict) -> int:
        group_id = str(item.get("group_id", ""))
        kind = group_id.split(":")[0] if ":" in group_id else group_id
        return KIND_PRIORITY.get(kind, 0)

    for (_, _), items in sorted(
        by_line.items(), key=lambda entry: (entry[0][0], entry[0][1])
    ):
        if len(items) == 1:
            final_deduped.append(items[0])
            continue

        best = sorted(
            items,
            key=lambda item: (
                -_get_seam_priority(item),
                -_coerce_float(item.get("confidence"), 0.0),
                str(item.get("group_id", "")),
            ),
        )[0]
        final_deduped.append(best)

    return final_deduped


def merge_real_and_virtual_seams(
    real_seams_map: dict[str, dict],
    real_seams_list: Iterable[dict],
    virtual_seams: Iterable[dict],
) -> list[dict]:
    """Phase 5: Merge real seams with virtual seams, real overrides by group_id."""
    final_seams: list[dict] = []

    for seam in real_seams_list:
        if isinstance(seam, dict):
            final_seams.append(seam)

    for seam in virtual_seams:
        if not isinstance(seam, dict):
            continue
        group_id = str(seam.get("group_id", "")).strip()
        if not group_id:
            continue
        if group_id in real_seams_map:
            continue
        final_seams.append(seam)

    final_seams.sort(
        key=lambda item: (
            str(item.get("file", "")),
            _coerce_line(item.get("begin_line")) or _coerce_line(item.get("line")) or 0,
            str(item.get("group_id", "")),
        )
    )

    return final_seams


def build_virtual_seams(
    context_dir: str | Path = ".midicoder/context",
    repo_root: Path | None = None,
) -> list[dict]:
    """Run full virtual seams pipeline and return merged seams list."""
    real_seams_map, real_seams_list = load_real_seams(context_dir)
    exemplar_seams = load_exemplar_virtual_seams(context_dir, repo_root=repo_root)
    covered_group_ids = {
        str(s.get("group_id")) for s in exemplar_seams if isinstance(s, dict)
    }

    symbol_seams = load_symbol_virtual_seams(
        context_dir, covered_group_ids, repo_root=repo_root
    )
    covered_group_ids.update(
        str(s.get("group_id"))
        for s in symbol_seams
        if isinstance(s, dict) and s.get("group_id")
    )

    entrypoint_seams = load_entrypoint_virtual_seams(
        context_dir, covered_group_ids, repo_root=repo_root
    )

    all_virtual = exemplar_seams + symbol_seams + entrypoint_seams
    deduped_virtual = deduplicate_virtual_seams(all_virtual)
    return merge_real_and_virtual_seams(
        real_seams_map, real_seams_list, deduped_virtual
    )


def write_virtual_seams(
    context_dir: str | Path = ".midicoder/context",
    repo_root: Path | None = None,
) -> list[dict]:
    """Build and write virtual_seams.json to the context directory."""
    context_path = Path(context_dir)
    context_path.mkdir(parents=True, exist_ok=True)
    seams = build_virtual_seams(context_path, repo_root=repo_root)
    output_path = context_path / "virtual_seams.json"
    output_path.write_text(
        json.dumps(
            _strip_internal_fields(seams), indent=2, sort_keys=True, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    return _strip_internal_fields(seams)
