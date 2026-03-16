"""Tests for Mermaid renderer helper."""

from pathlib import Path

from midicoder.ir.visualize.diagram.base import MermaidRenderer


def test_render_to_file_injects_theme(tmp_path: Path) -> None:
    sample = "flowchart LR\n    A --> B"
    target = tmp_path / "sample.mmd"

    assets = MermaidRenderer.render_to_file(sample, target)

    assert assets
    mmd_path = target.with_suffix(".mmd")
    content = mmd_path.read_text(encoding="utf-8")
    assert "%%{init:" not in content
    assert "flowchart LR" in content
