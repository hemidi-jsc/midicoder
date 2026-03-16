"""Index project context."""

from __future__ import annotations

import logging
from pathlib import Path

from midicoder.context.indexer import build_context

from .base import (
    MidicoderPaths,
    create_run_dir,
    ensure_base_layout,
    read_config,
    read_state,
    write_run_outputs,
)

logger = logging.getLogger(__name__)


def _resolve_working_dir(root: Path, config: dict) -> Path:
    """Resolve working_dir from config against root.

    - If working_dir is None or empty: fallback to root.
    - If working_dir is an absolute path: use it directly.
    - If working_dir is a relative path: join with root.
    """
    raw = config.get("working_dir") or None
    if not raw:
        return root
    wd = Path(raw)
    if wd.is_absolute():
        return wd.resolve()
    return (root / wd).resolve()



def run(root: Path) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )
    
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    state = read_state(paths)
    config = read_config(paths)
    run_dir = create_run_dir(paths, "index")

    working_dir = _resolve_working_dir(root, config)

    logger.info("=" * 60)
    logger.info("[index] Path configuration:")
    logger.info("  cwd         : %s", Path.cwd())
    logger.info("  root (.midi): %s", root)
    logger.info("  config.json : %s", paths.config)
    logger.info("  working_dir : %s (raw=%r)", working_dir, config.get("working_dir"))
    logger.info("  context_dir : %s", root / '.midicoder' / 'context')
    logger.info("=" * 60)
    
    try:
        build_context(root=working_dir, context_root=root, refresh=False)
        
        write_run_outputs(
            run_dir, 
            "index", 
            {"status": "ok", "context_dir": str(root / ".midicoder" / "context"), "working_dir": str(working_dir)}, 
            state_before=state,
            state_after=state
        )
        
        logger.info("Index command completed successfully")
        
    except Exception as e:
        logger.error(f"✗ Index command failed: {e}")
        write_run_outputs(
            run_dir,
            "index",
            {"status": "error", "error": str(e)},
            state_before=state,
            state_after=state
        )
        raise


def reindex(root: Path, changed_paths: list[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    state = read_state(paths)
    config = read_config(paths)
    run_dir = create_run_dir(paths, "index")

    working_dir = _resolve_working_dir(root, config)

    logger.info("=" * 60)
    logger.info("[reindex] Path configuration:")
    logger.info("  cwd         : %s", Path.cwd())
    logger.info("  root (.midi): %s", root)
    logger.info("  config.json : %s", paths.config)
    logger.info("  working_dir : %s (raw=%r)", working_dir, config.get("working_dir"))
    logger.info("  context_dir : %s", root / '.midicoder' / 'context')
    logger.info("=" * 60)
    if changed_paths:
        logger.info("Manual changed paths: %d", len(changed_paths))

    try:
        build_context(
            root=working_dir,
            context_root=root,
            refresh=True,
            reindex_only_changed=True,
            changed_paths=changed_paths,
        )

        write_run_outputs(
            run_dir,
            "index",
            {"status": "ok", "context_dir": str(root / ".midicoder" / "context"), "working_dir": str(working_dir)},
            state_before=state,
            state_after=state,
        )

        logger.info("Reindex command completed successfully")

    except Exception as e:
        logger.error(f"✗ Reindex command failed: {e}")
        write_run_outputs(
            run_dir,
            "index",
            {"status": "error", "error": str(e)},
            state_before=state,
            state_after=state,
        )
        raise