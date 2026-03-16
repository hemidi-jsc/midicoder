"""Seam extraction utilities."""

from __future__ import annotations

import logging
import re

from ..core.models import ErrorRecord, Seam
from ..core.scanner import ProjectScanner, normalize_path

logger = logging.getLogger(__name__)


def extract_seams(scanner: ProjectScanner, target_files: set[str] | None = None) -> tuple[list[Seam], list[ErrorRecord]]:
    """Extract seams with proper schema: kind, file, line, detail, group_id, paired."""
    seams: list[Seam] = []
    errors: list[ErrorRecord] = []

    # Extract marker-based seams (midicoder:begin/end)
    for path in scanner.python_files:
        relative_path = normalize_path(path.relative_to(scanner.root))
        if target_files is not None and relative_path not in target_files:
            continue
        content = scanner.get_content(path)
        if not content:
            continue

        file_seams, file_errors = extract_seams_from_text(content, relative_path)
        seams.extend(file_seams)
        errors.extend(file_errors)

    for path in scanner.js_ts_files:
        relative_path = normalize_path(path.relative_to(scanner.root))
        if target_files is not None and relative_path not in target_files:
            continue
        content = scanner.get_content(path)
        if not content:
            continue

        file_seams, file_errors = extract_seams_from_text(content, relative_path)
        seams.extend(file_seams)
        errors.extend(file_errors)

    logger.debug(f"Extracted {len(seams)} seams")
    return seams, errors


def extract_seams_from_text(content: str, relative_path: str) -> tuple[list[Seam], list[ErrorRecord]]:
    """Extract seams from text content, pairing begin/end markers into seam entries."""
    seams: list[Seam] = []
    errors: list[ErrorRecord] = []
    open_markers: dict[str, list[tuple[int, str, str]]] = {}  # marker -> [(line_no, detail, group_id)]

    lines = content.splitlines()
    # Markers must start at line beginning (optionally after comment prefix).
    # This avoids false positives like "midicoder:end/midicoder:begin".
    begin_pattern = re.compile(
        r"^\s*(?:#|//|/\*+|\*)?\s*midicoder:begin(?:\s+(.*?))?\s*$",
        re.IGNORECASE,
    )
    end_pattern = re.compile(
        r"^\s*(?:#|//|/\*+|\*)?\s*midicoder:end(?:\s+(.*?))?\s*$",
        re.IGNORECASE,
    )

    for line_no, line in enumerate(lines, start=1):
        begin_match = begin_pattern.match(line)
        if begin_match:
            group_id = (begin_match.group(1) or "").strip() or "default"
            open_markers.setdefault(group_id, []).append((line_no, line.strip(), group_id))
            continue

        end_match = end_pattern.match(line)
        if end_match:
            group_id = (end_match.group(1) or "").strip() or "default"
            if group_id in open_markers and open_markers[group_id]:
                line_start, detail_start, group_id = open_markers[group_id].pop()

                seams.append(
                    Seam(
                        kind="begin",
                        file=relative_path,
                        line=line_start,
                        detail=detail_start,
                        group_id=group_id,
                        paired=True,
                    )
                )
                seams.append(
                    Seam(
                        kind="end",
                        file=relative_path,
                        line=line_no,
                        detail=line.strip(),
                        group_id=group_id,
                        paired=True,
                    )
                )
            else:
                seams.append(
                    Seam(
                        kind="end",
                        file=relative_path,
                        line=line_no,
                        detail=line.strip(),
                        group_id=group_id,
                        paired=False,
                    )
                )
                errors.append(
                    ErrorRecord(
                        kind="seam_unpaired_end",
                        file=relative_path,
                        detail=f"Unmatched midicoder:end for marker '{group_id}' at line {line_no}",
                    )
                )

    # Check for unpaired begin markers
    for marker, entries in open_markers.items():
        for line_start, detail_start, group_id in entries:
            seams.append(
                Seam(
                    kind="begin",
                    file=relative_path,
                    line=line_start,
                    detail=detail_start,
                    group_id=group_id,
                    paired=False,
                )
            )
            errors.append(
                ErrorRecord(
                    kind="seam_unpaired_begin",
                    file=relative_path,
                    detail=f"Unmatched midicoder:begin for marker '{marker}' at line {line_start}",
                )
            )

    return seams, errors
