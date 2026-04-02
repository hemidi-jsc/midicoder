"""IR build commands."""

from __future__ import annotations

import json
import os
from pathlib import Path

from midicoder.ir import build_ir

from .base import (
    MidicoderPaths,
    create_run_dir,
    ensure_base_layout,
    ensure_version_layout,
    read_state,
    write_run_outputs,
)

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def _apply_strict_cross_ref_default(paths: MidicoderPaths) -> None:
    """
    Seed STRICT_CROSS_REF from config when env vars are not explicitly set.
    """
    if os.getenv("STRICT_CROSS_REF") or os.getenv("MIDICODER_STRICT_CROSS_REF"):
        return

    config_path = paths.config
    if not config_path.exists():
        return
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    contract_cfg = payload.get("contract", {})
    if not isinstance(contract_cfg, dict):
        return

    strict_raw = str(contract_cfg.get("strict_cross_ref", "")).strip().lower()
    if strict_raw in _TRUE_VALUES:
        os.environ["STRICT_CROSS_REF"] = "1"
    elif strict_raw in _FALSE_VALUES:
        os.environ["STRICT_CROSS_REF"] = "0"


def build(root: Path, skip_diagrams: bool = False) -> None:
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)
    state = read_state(paths)
    version = state.get("current_version")
    if not version:
        raise RuntimeError("No current version set. Run `version create` first.")

    ensure_version_layout(paths, str(version))
    _apply_strict_cross_ref_default(paths)

    build_ir(str(version), repo_root=str(root), skip_diagrams=skip_diagrams)

    run_dir = create_run_dir(paths, "ir_build")
    write_run_outputs(
        run_dir,
        "ir_build",
        {"version": version, "status": "built"},
        state_before=state,
        state_after=state,
    )
