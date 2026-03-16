from __future__ import annotations

import json
import os
from pathlib import Path

from midicoder.commands.base import MidicoderPaths
from midicoder.commands.ir import _apply_strict_cross_ref_default


def _write_config(root: Path, strict_value: bool) -> None:
    config_path = root / ".midicoder" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps({"contract": {"strict_cross_ref": strict_value}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_apply_strict_cross_ref_default_reads_config_when_env_unset(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("STRICT_CROSS_REF", raising=False)
    monkeypatch.delenv("MIDICODER_STRICT_CROSS_REF", raising=False)
    _write_config(tmp_path, strict_value=True)
    paths = MidicoderPaths(root=tmp_path)

    _apply_strict_cross_ref_default(paths)

    assert os.getenv("STRICT_CROSS_REF") == "1"


def test_apply_strict_cross_ref_default_does_not_override_explicit_env(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("STRICT_CROSS_REF", "0")
    _write_config(tmp_path, strict_value=True)
    paths = MidicoderPaths(root=tmp_path)

    _apply_strict_cross_ref_default(paths)

    assert os.getenv("STRICT_CROSS_REF") == "0"
