"""Tests for visual spec map generation."""

from pathlib import Path

from ruamel.yaml import YAML

from midicoder.ir.visualize.spec_map import generate_visual_map


def test_generate_visual_map(tmp_path: Path) -> None:
    tree_path = Path("midicoder/dsl/schemas/tree_v0.yml")
    output = tmp_path / "visual-ir-map.yml"

    generate_visual_map(tree_path, output)

    yaml = YAML(typ="safe")
    data = yaml.load(output.read_text(encoding="utf-8"))

    assert data["schema_version"] == "v0"
    assert data["kinds"]["domain.entity"]["template"] == "domain_model.er"
