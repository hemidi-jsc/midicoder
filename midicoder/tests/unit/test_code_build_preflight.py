from __future__ import annotations

from pathlib import Path

from midicoder.code.builder.loaders import preflight_check


def test_preflight_requires_ir_only_when_context_missing(tmp_path: Path) -> None:
    ir_path = tmp_path / "ir.json"
    ir_path.write_text("{}", encoding="utf-8")
    context_dir = tmp_path / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    ok, errors = preflight_check(ir_path, context_dir)

    assert ok is True
    assert errors == []

