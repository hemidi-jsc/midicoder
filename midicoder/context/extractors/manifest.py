"""Manifest building utilities."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from ..core.models import (
    EntryPoint,
    Exemplar,
    IndexManifest,
    ProjectProfile,
    Seam,
    Symbol,
)
from ..core.scanner import ProjectScanner
from .constants import TOOL_VERSION

logger = logging.getLogger(__name__)


def build_index_manifest(
    scanner: ProjectScanner,
    profile: ProjectProfile,
    symbols: list[Symbol],
    entrypoints: list[EntryPoint],
    seams: list[Seam],
    exemplars: list[Exemplar],
) -> IndexManifest:
    """Build manifest with file_hashes, output_stats, and project_summary."""
    import subprocess

    # Get repo hash from git
    repo_hash = None
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=scanner.root,
            stderr=subprocess.DEVNULL,
        )
        git_hash = output.decode("utf-8", errors="ignore").strip()
        repo_hash = f"sha1:{git_hash}" if git_hash else None
    except (OSError, subprocess.CalledProcessError):
        pass

    # Build file_hashes map
    file_hashes: dict[str, str] = {}
    for file_meta in scanner.indexed_files:
        if file_meta.sha256:
            file_hashes[file_meta.path] = f"{file_meta.sha256}"

    # Build output_stats
    symbols_by_kind: dict[str, int] = {}
    for symbol in symbols:
        symbols_by_kind[symbol.kind] = symbols_by_kind.get(symbol.kind, 0) + 1

    entrypoints_by_kind: dict[str, int] = {}
    for entrypoint in entrypoints:
        entrypoints_by_kind[entrypoint.kind] = (
            entrypoints_by_kind.get(entrypoint.kind, 0) + 1
        )

    exemplars_by_kind: dict[str, int] = {}
    for exemplar in exemplars:
        exemplars_by_kind[exemplar.kind] = exemplars_by_kind.get(exemplar.kind, 0) + 1

    # Check seams validity (paired begin/end)
    seams_valid = all(seam.paired for seam in seams)

    output_stats: dict[str, object] = {
        "files_found": scanner.total_files_found,
        "files_indexed": scanner.total_files_indexed,
        "files_not_indexed": sorted(scanner.skipped_unindexed_files),
        "files_not_indexed_count": len(scanner.skipped_unindexed_files),
        "symbols_count": len(symbols),
        "symbols_by_kind": symbols_by_kind,
        "entrypoints_count": len(entrypoints),
        "entrypoints_by_kind": entrypoints_by_kind,
        "seams_count": len(seams),
        "seams_valid": seams_valid,
        "exemplars_count": len(exemplars),
        "exemplars_by_kind": exemplars_by_kind,
    }

    # Build project_summary
    total_lines = 0
    for file_meta in scanner.indexed_files:
        file_path = scanner.root / file_meta.path
        content = scanner.get_content(file_path)
        if content:
            total_lines += len(content.splitlines())

    project_summary: dict[str, object] = {
        "language": profile.language,
        "stack": profile.stack,
        "total_lines": total_lines,
    }

    manifest = IndexManifest(
        indexed_at=datetime.now(timezone.utc).isoformat(),
        repo_hash=repo_hash,
        tool_version=TOOL_VERSION,
        file_count=len(scanner.indexed_files),
        ignored_patterns=scanner.ignored_patterns,
        file_hashes=file_hashes,
        output_stats=output_stats,
        project_summary=project_summary,
    )

    logger.debug(
        f"Built manifest: {manifest.file_count} files, "
        f"{len(symbols)} symbols, {len(entrypoints)} entrypoints, "
        f"{len(seams)} seams, {len(exemplars)} exemplars, "
        f"repo_hash={repo_hash[:12] if repo_hash else 'N/A'}"
    )

    return manifest
