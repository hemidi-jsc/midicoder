from __future__ import annotations

from pathlib import Path

from midicoder.contract.reference_loader import collect_reference_catalog


def write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


def test_collect_reference_catalog(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts"
    contracts_root.mkdir(parents=True, exist_ok=True)

    write_yaml(
        contracts_root / "policy" / "rbac.yaml",
        """
access:
  roles:
    - id: admin
  permissions:
    - id: manage_orders
  bindings: []
""",
    )

    write_yaml(
        contracts_root / "persistence" / "model.yaml",
        """
datasources:
  - id: main_db
tables:
  - id: orders
    datasource: main_db
""",
    )

    write_yaml(
        contracts_root / "integrations" / "integrations.yaml",
        """
integrations:
  - id: BillingGateway
    type: rest_api
operations:
  - id: ChargeCustomer
    integration_id: BillingGateway
    method: POST
    path: /charge
""",
    )

    write_yaml(
        contracts_root / "scenarios" / "scenarios.yaml",
        """
scenarios:
  - id: happy_path
    steps: []
""",
    )

    write_yaml(
        contracts_root / "app" / "commands.yaml",
        """
commands:
  - id: CreateOrder
    input: []
    fetches: []
    guards: []
    effects: []
    errors: []
    returns: []
""",
    )

    references = collect_reference_catalog(contracts_root)
    assert references["available_roles"] == ["admin"]
    assert references["available_permissions"] == ["manage_orders"]
    assert references["available_persistence_datasources"] == ["main_db"]
    assert references["available_persistence_tables"] == ["orders"]
    assert references["available_integrations"] == ["BillingGateway"]
    assert references["available_integration_operations"] == ["ChargeCustomer"]
    assert references["available_scenarios"] == ["happy_path"]
    assert references["existing_commands"] == ["CreateOrder"]
