"""Visual specification registry for Mermaid diagrams."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

DEFAULT_TEMPLATE_MAP = {
    "domain.entity": "domain_model.er",
    "domain.value_object": "domain_model.er",
    "domain.enum": "domain_model.er",
    "domain.event": "domain_model.er",
    "app.command": "application.flow.lanes",
    "app.query": "application.flow.lanes",
    "workflow.definition": "workflow.stateDiagram",
    "api.http": "api.http.flow",
    "api.graphql": "api.graphql.map",
    "policy.access": "policy.access.matrix",
    "policy.business": "policy.business.flow",
    "rules.definition": "rules.decision.table",
    "scenario.definition": "scenario.sequence",
}


class VisualSpecRegistry:
    """Loads and exposes visual spec metadata."""

    def __init__(self, spec_path: Path | None = None):
        self.spec_path = spec_path
        self.data: dict[str, Any] = {}
        self.version = "unversioned"
        self.schema_version = None
        self.checksum = None
        self._load()

    def _load(self) -> None:
        if not self.spec_path or not self.spec_path.exists():
            self.data = {}
            return
        content = self.spec_path.read_text(encoding="utf-8")
        yaml = YAML(typ="safe")
        self.data = yaml.load(content) or {}
        self.version = self.data.get("version", "unversioned")
        self.schema_version = self.data.get("schema_version")
        self.checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get_template(self, kind: str) -> dict[str, Any] | None:
        return (self.data.get("kinds") or {}).get(kind)

    def metadata(self) -> dict[str, Any]:
        return {
            "path": str(self.spec_path) if self.spec_path else None,
            "version": self.version,
            "schema_version": self.schema_version,
            "checksum": self.checksum,
        }


def generate_visual_map(tree_path: Path, output_path: Path) -> Path:
    """Generate visual spec map from DSL schema tree."""
    yaml = YAML(typ="safe")
    tree = yaml.load(tree_path.read_text(encoding="utf-8")) or {}
    schema_version = tree.get("version")

    kinds = {}
    for module in tree.get("modules", {}).values():
        for model in module.get("models", {}).values():
            meta = model.get("meta", {})
            kind = meta.get("kind")
            if not kind:
                continue
            kinds[kind] = {
                "template": DEFAULT_TEMPLATE_MAP.get(kind),
                "includes": meta.get("includes", []),
                "included_by": meta.get("included_by", []),
                "visualizers": meta.get("visualizers", []),
            }

    spec = {
        "version": "v1",
        "schema_version": schema_version,
        "generated_from": str(tree_path),
        "kinds": kinds,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        YAML().dump(spec, fh)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate visual IR spec map.")
    parser.add_argument("--tree", type=Path, required=True, help="Path to tree_v0.yml")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/specs/visual-ir-map.yml"),
        help="Output spec file",
    )
    args = parser.parse_args()
    path = generate_visual_map(args.tree, args.output)
    print(f"[visual-map] wrote spec to {path}")


if __name__ == "__main__":
    main()
