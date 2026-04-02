from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .builders import (
    build_virtual_seams_from_entrypoints,
    build_virtual_seams_from_exemplars,
    build_virtual_seams_from_symbols,
)
from .real import build_real_seams_from_records


def load_real_seams(
    context_dir: str | Path = ".midicoder/context",
) -> tuple[dict[str, dict], list[dict]]:
    """
    Phase 0: load real seams from seams.json.

    Returns:
        (real_seams_map, real_seams_list)
    """
    seams_path = Path(context_dir) / "seams.json"
    if not seams_path.exists():
        return {}, []

    try:
        payload = json.loads(seams_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, []

    if not isinstance(payload, list):
        return {}, []

    return build_real_seams_from_records(payload)


def _derive_repo_root(context_dir: str | Path) -> Path | None:
    context_path = Path(context_dir)
    if context_path.name == "context" and context_path.parent.name == ".midicoder":
        return context_path.parent.parent
    return context_path.parent


def load_exemplar_virtual_seams(
    context_dir: str | Path = ".midicoder/context",
    repo_root: Path | None = None,
) -> list[dict]:
    """Phase 1: Generate virtual seams from exemplars.json."""
    exemplars_path = Path(context_dir) / "exemplars.json"
    if not exemplars_path.exists():
        return []

    try:
        payload = json.loads(exemplars_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(payload, list):
        return []

    if repo_root is None:
        repo_root = _derive_repo_root(context_dir)
    return build_virtual_seams_from_exemplars(payload, repo_root=repo_root)


def load_symbol_virtual_seams(
    context_dir: str | Path = ".midicoder/context",
    covered_group_ids: Iterable[str] | None = None,
    repo_root: Path | None = None,
) -> list[dict]:
    """Phase 2: Generate virtual seams from symbols.json."""
    symbols_path = Path(context_dir) / "symbols.json"
    if not symbols_path.exists():
        return []

    try:
        payload = json.loads(symbols_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(payload, list):
        return []

    if repo_root is None:
        repo_root = _derive_repo_root(context_dir)
    return build_virtual_seams_from_symbols(
        payload, covered_group_ids, repo_root=repo_root
    )


def load_entrypoint_virtual_seams(
    context_dir: str | Path = ".midicoder/context",
    covered_group_ids: Iterable[str] | None = None,
    repo_root: Path | None = None,
) -> list[dict]:
    """Phase 3: Generate virtual seams from entrypoints.json."""
    entrypoints_path = Path(context_dir) / "entrypoints.json"
    if not entrypoints_path.exists():
        return []

    try:
        payload = json.loads(entrypoints_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(payload, list):
        return []

    if repo_root is None:
        repo_root = _derive_repo_root(context_dir)
    return build_virtual_seams_from_entrypoints(
        payload, covered_group_ids, repo_root=repo_root
    )
