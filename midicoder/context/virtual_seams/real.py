from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .utils import GROUP_ID_PATTERN, REAL_SEAM_CONFIDENCE, _coerce_line


@dataclass(frozen=True)
class _SeamCandidate:
    file: str
    begin_line: int
    end_line: int | None
    detail: str


@dataclass(frozen=True)
class _MarkerPoint:
    file: str
    line: int
    detail: str


def build_real_seams_from_records(
    records: Iterable[dict],
) -> tuple[dict[str, dict], list[dict]]:
    begins: dict[str, list[_MarkerPoint]] = {}
    ends: dict[str, list[_MarkerPoint]] = {}
    paired_candidates: dict[str, list[_SeamCandidate]] = {}

    for record in records:
        if not isinstance(record, dict):
            continue

        group_id = _extract_group_id(record)
        if not group_id:
            continue

        file_path = str(record.get("file", ""))
        detail = str(record.get("detail") or record.get("marker") or "")

        begin_line = _coerce_line(record.get("begin_line"))
        end_line = _coerce_line(record.get("end_line"))
        if begin_line and end_line and end_line >= begin_line:
            paired_candidates.setdefault(group_id, []).append(
                _SeamCandidate(
                    file=file_path,
                    begin_line=begin_line,
                    end_line=end_line,
                    detail=detail,
                )
            )
            continue

        kind = str(record.get("kind", "begin")).lower()
        line = _coerce_line(record.get("line"))
        if not line:
            continue

        if kind == "end":
            ends.setdefault(group_id, []).append(
                _MarkerPoint(file=file_path, line=line, detail=detail)
            )
        else:
            begins.setdefault(group_id, []).append(
                _MarkerPoint(file=file_path, line=line, detail=detail)
            )

    real_seams_map: dict[str, dict] = {}

    all_group_ids = set(begins) | set(ends) | set(paired_candidates)
    for group_id in sorted(all_group_ids):
        candidates = list(paired_candidates.get(group_id, []))

        for begin in begins.get(group_id, []):
            for end in ends.get(group_id, []):
                if begin.file != end.file:
                    continue
                if end.line < begin.line:
                    continue
                detail = begin.detail or end.detail
                candidates.append(
                    _SeamCandidate(
                        file=begin.file,
                        begin_line=begin.line,
                        end_line=end.line,
                        detail=detail,
                    )
                )

        if candidates:
            best = min(
                candidates,
                key=lambda c: (
                    (c.end_line or c.begin_line) - c.begin_line,
                    c.begin_line,
                    c.file,
                ),
            )
            real_seams_map[group_id] = _to_real_seam(group_id, best)
            continue

        begin_points = begins.get(group_id, [])
        if begin_points:
            best_begin = min(begin_points, key=lambda b: (b.line, b.file))
            point_candidate = _SeamCandidate(
                file=best_begin.file,
                begin_line=best_begin.line,
                end_line=None,
                detail=best_begin.detail,
            )
            real_seams_map[group_id] = _to_real_seam(group_id, point_candidate)

    real_seams_list = sorted(
        real_seams_map.values(),
        key=lambda s: (
            s.get("file", ""),
            int(s.get("begin_line", 0)),
            s.get("group_id", ""),
        ),
    )

    return real_seams_map, real_seams_list


def _to_real_seam(group_id: str, candidate: _SeamCandidate) -> dict:
    detail = candidate.detail or f"real:{group_id}"
    return {
        "kind": "real",
        "file": candidate.file,
        "line": candidate.begin_line,
        "begin_line": candidate.begin_line,
        "end_line": candidate.end_line,
        "detail": detail,
        "group_id": group_id,
        "confidence": REAL_SEAM_CONFIDENCE,
    }


def _extract_group_id(record: dict) -> str:
    group_id = record.get("group_id")
    if isinstance(group_id, str) and group_id.strip():
        return group_id.strip()

    detail = record.get("detail") or record.get("marker")
    if isinstance(detail, str):
        match = GROUP_ID_PATTERN.search(detail)
        if match:
            candidate = match.group(1).strip()
            if candidate:
                return candidate

    return ""
