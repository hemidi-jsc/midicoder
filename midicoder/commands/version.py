"""Version management commands."""

from __future__ import annotations

from pathlib import Path

from midicoder.brief import MASTER_BRIEF_TEMPLATE

from .base import (
    MidicoderPaths,
    create_run_dir,
    ensure_base_layout,
    ensure_version_layout,
    read_state,
    write_run_outputs,
    write_json,
    write_state,
)


def create(root: Path, version: str) -> None:
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)
    ensure_version_layout(paths, version)

    version_root = paths.versions / version
    write_json(version_root / "state.json", {"version": version})

    master_brief = version_root / "master-brief.md"
    if not master_brief.exists():
        master_brief.write_text(MASTER_BRIEF_TEMPLATE, encoding="utf-8")

    state_before = read_state(paths)
    state = dict(state_before)
    state["current_version"] = version
    state["contracts_locked"] = False
    write_state(paths, state)

    run_dir = create_run_dir(paths, "version_create")
    write_run_outputs(
        run_dir,
        "version_create",
        {"version": version, "status": "created"},
        state_before=state_before,
        state_after=state,
    )
