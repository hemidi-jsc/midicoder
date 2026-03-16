from __future__ import annotations

from pathlib import Path

from midicoder.contract.patch_manager import apply_contract_patches
from ruamel.yaml import YAML


def test_apply_contract_patches_allows_null_new_content(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts"
    target = contracts_root / "rules" / "rules.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "rules:\n"
        "  - id: r1\n"
        "    applies_to: UploadEmployeeDocument\n"
        "    rows: []\n",
        encoding="utf-8",
    )

    errors: list[str] = []
    updated = apply_contract_patches(
        contracts_root,
        [
            {
                "file": "contracts/rules/rules.yaml",
                "kind": "replace_node",
                "location": "rules[0].applies_to",
                "new_content": None,
            }
        ],
        errors=errors,
    )

    assert updated
    yaml_loader = YAML(typ="safe")
    parsed = yaml_loader.load(target.read_text(encoding="utf-8"))
    assert parsed["rules"][0]["applies_to"] is None
    assert not any("missing new_content field" in err for err in errors)
