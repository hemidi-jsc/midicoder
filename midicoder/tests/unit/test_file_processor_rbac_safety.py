from __future__ import annotations

from pathlib import Path

from midicoder.contract.file_processor import _apply_rbac_repair_safety_fixes


def _write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


def test_rbac_safety_fix_remaps_unknown_entity_and_adds_ownership_policies(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts"

    _write_yaml(
        contracts_root / "domain" / "entities.yaml",
        """
entities:
  - id: Employee
""",
    )
    _write_yaml(
        contracts_root / "app" / "commands.yaml",
        """
commands:
  - id: CheckIn
    input: []
    fetches: []
    guards: []
    effects: []
    errors: []
    returns: []
""",
    )
    _write_yaml(
        contracts_root / "app" / "queries.yaml",
        """
queries:
  - id: GetEmployeeDocuments
    input: []
    returns: []
""",
    )
    _write_yaml(
        contracts_root / "policy" / "rbac.yaml",
        """
access:
  roles:
    - id: Employee
  permissions:
    - id: view_system_logs
      resource: entity:System
      action: read
    - id: view_own_payroll
      resource: entity:Payroll
      action: read
  bindings:
    - role: Employee
      permissions:
        - view_system_logs
        - view_own_payroll
""",
    )
    _write_yaml(
        contracts_root / "policy" / "policies.yaml",
        """
policies: []
""",
    )

    notes = _apply_rbac_repair_safety_fixes(contracts_root)
    assert notes

    rbac_text = (contracts_root / "policy" / "rbac.yaml").read_text(encoding="utf-8")
    assert "document:system_logs" in rbac_text

    policies_text = (contracts_root / "policy" / "policies.yaml").read_text(encoding="utf-8")
    assert "view_own_payroll_ownership_policy" in policies_text
