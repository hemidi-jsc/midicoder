from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .bounds import (
    resolve_block_bounds_for_entrypoint,
    resolve_block_bounds_for_exemplar,
    resolve_block_bounds_for_symbol,
)
from .utils import (
    ENTRYPOINT_CONFIDENCE,
    EXEMPLAR_GROUP_PENALTY,
    SYMBOL_BASE_CONFIDENCE,
    SYMBOL_SOURCE_PENALTY,
    _clamp,
    _coerce_float,
    _coerce_line,
    _extract_module_from_path,
    _has_parent_symbol,
    _infer_kind_from_path,
    _module_fallback_penalty,
)


def build_virtual_seams_from_entrypoints(
    records: Iterable[dict],
    covered_group_ids: Iterable[str] | None = None,
    repo_root: Path | None = None,
) -> list[dict]:
    covered = {gid for gid in (covered_group_ids or []) if isinstance(gid, str) and gid}
    virtual_seams: list[dict] = []

    for record in records:
        if not isinstance(record, dict):
            continue

        file_path = str(record.get("file", "")).strip()
        if not file_path:
            continue

        module, module_fallback = _extract_module_from_path(file_path)
        raw_kind = str(record.get("kind", "")).strip().lower()
        kind = raw_kind or "entrypoint"
        group_id = f"{kind}:{module}"

        if group_id in covered:
            continue

        line = _coerce_line(record.get("line"))
        if not line:
            continue
        computed_begin, computed_end = resolve_block_bounds_for_entrypoint(
            repo_root, record
        )
        begin_line = _coerce_line(record.get("begin_line")) or computed_begin or line
        end_line = _coerce_line(record.get("end_line")) or computed_end
        module_penalty = 0.85 if module_fallback else 1.0

        virtual_seams.append(
            {
                "kind": "virtual",
                "file": file_path,
                "line": line,
                "begin_line": begin_line,
                "end_line": end_line,
                "detail": f"virtual:{group_id}",
                "group_id": group_id,
                "confidence": _clamp(ENTRYPOINT_CONFIDENCE * module_penalty),
                "_source": "entrypoint",
            }
        )

    return virtual_seams


def build_virtual_seams_from_exemplars(
    records: Iterable[dict],
    repo_root: Path | None = None,
) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = {}

    for record in records:
        if not isinstance(record, dict):
            continue

        kind = str(record.get("kind", "")).strip()
        if not kind:
            continue

        file_path = str(record.get("file", "")).strip()
        module, _ = _extract_module_from_path(file_path)
        key = (kind, module)
        groups.setdefault(key, []).append(record)

    virtual_seams: list[dict] = []

    for (kind, module), items in sorted(
        groups.items(), key=lambda entry: (entry[0][0], entry[0][1])
    ):
        sorted_items = sorted(
            items,
            key=lambda item: (
                -_coerce_float(item.get("score"), 0.0),
                _coerce_line(item.get("line")) or 0,
            ),
        )
        if not sorted_items:
            continue

        representative = sorted_items[0]
        base_score = _coerce_float(representative.get("score"), 0.0)
        penalty = EXEMPLAR_GROUP_PENALTY ** max(len(sorted_items) - 1, 0)
        module_penalty = _module_fallback_penalty(representative.get("file"))
        confidence = _clamp(base_score * penalty * module_penalty)

        line = _coerce_line(representative.get("line"))
        if not line:
            continue
        computed_begin, computed_end = resolve_block_bounds_for_exemplar(
            repo_root, representative
        )
        begin_line = (
            _coerce_line(representative.get("begin_line")) or computed_begin or line
        )
        end_line = _coerce_line(representative.get("end_line")) or computed_end

        group_id = f"{kind}:{module}"
        virtual_seams.append(
            {
                "kind": "virtual",
                "file": str(representative.get("file", "")),
                "line": line,
                "begin_line": begin_line,
                "end_line": end_line,
                "detail": f"virtual:{group_id}",
                "group_id": group_id,
                "confidence": confidence,
                "_source": "exemplar",
            }
        )

    return virtual_seams


def build_virtual_seams_from_symbols(
    records: Iterable[dict],
    covered_group_ids: Iterable[str] | None = None,
    repo_root: Path | None = None,
) -> list[dict]:
    covered = {gid for gid in (covered_group_ids or []) if isinstance(gid, str) and gid}
    by_file: dict[str, list[dict]] = {}

    for record in records:
        if not isinstance(record, dict):
            continue

        kind = str(record.get("kind", "")).strip()
        if kind not in {"class", "function"}:
            continue
        if _has_parent_symbol(record):
            continue

        file_path = str(record.get("file", "")).strip()
        if not file_path:
            continue

        by_file.setdefault(file_path, []).append(record)

    virtual_seams: list[dict] = []

    for file_path, symbols in sorted(by_file.items(), key=lambda entry: entry[0]):
        module, module_fallback = _extract_module_from_path(file_path)
        inferred_kind = _infer_kind_from_path(file_path)
        group_id = f"{inferred_kind}:{module}"

        if group_id in covered:
            continue

        symbols_sorted = sorted(
            symbols,
            key=lambda item: (
                _coerce_line(item.get("line")) or 0,
                str(item.get("name", "")),
            ),
        )
        if not symbols_sorted:
            continue

        representative = symbols_sorted[0]
        line = _coerce_line(representative.get("line"))
        if not line:
            continue
        computed_begin, computed_end = resolve_block_bounds_for_symbol(
            repo_root, representative
        )
        begin_line = (
            _coerce_line(representative.get("begin_line")) or computed_begin or line
        )
        end_line = _coerce_line(representative.get("end_line")) or computed_end

        representative_kind = str(representative.get("kind", "")).strip().lower()
        kind_bonus = (
            0.10
            if representative_kind == "class"
            else 0.06 if representative_kind == "function" else 0.0
        )
        symbol_count_bonus = min(0.12, max(len(symbols_sorted) - 1, 0) * 0.02)
        span_bonus = 0.0
        if end_line and end_line > begin_line:
            span_bonus = min(0.08, (end_line - begin_line) / 200.0)

        source_strength = (
            SYMBOL_BASE_CONFIDENCE + kind_bonus + symbol_count_bonus + span_bonus
        )
        module_penalty = 0.85 if module_fallback else 1.0
        confidence = _clamp(source_strength * SYMBOL_SOURCE_PENALTY * module_penalty)

        virtual_seams.append(
            {
                "kind": "virtual",
                "file": file_path,
                "line": line,
                "begin_line": begin_line,
                "end_line": end_line,
                "detail": f"virtual:{group_id}",
                "group_id": group_id,
                "confidence": confidence,
                "_source": "symbol",
            }
        )

    return virtual_seams
