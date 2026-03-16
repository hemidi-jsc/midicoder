"""Code applicator package (apply patch-plan artifacts into working_dir)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

__all__ = ["apply_patch_plans"]


def apply_patch_plans(
    *,
    workspace_root: Path,
    version: str,
    patches_dir: Path,
    working_dir: Path,
    config: dict[str, Any] | None = None,
    force: bool = False,
    dry_run: bool = False,
    reindex: bool = True,
    progress_callback: Callable[[str], None] | None = None,
):
    # Lazy import keeps CLI startup independent from optional indexer dependencies.
    from .pipeline import apply_patch_plans as _apply_patch_plans

    return _apply_patch_plans(
        workspace_root=workspace_root,
        version=version,
        patches_dir=patches_dir,
        working_dir=working_dir,
        config=config,
        force=force,
        dry_run=dry_run,
        reindex=reindex,
        progress_callback=progress_callback,
    )
