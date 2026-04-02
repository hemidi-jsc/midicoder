from __future__ import annotations

from pathlib import Path
from typing import Any

from .contract_utils import extract_ids_from_yaml_list, load_yaml_safe


def _load_yaml(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return load_yaml_safe(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _assign(
    destination: dict[str, list[str]], key: str, values: list[str] | None
) -> None:
    if not values:
        return
    destination[key] = sorted({str(value) for value in values if str(value).strip()})


def collect_reference_catalog(contracts_root: Path) -> dict[str, list[str]]:
    """
    Collect reusable reference IDs (roles, permissions, integrations, persistence, scenarios, etc.)
    for prompt/context consumption.
    """
    references: dict[str, list[str]] = {}

    rbac_path = contracts_root / "policy" / "rbac.yaml"
    rbac_data = _load_yaml(rbac_path)
    if isinstance(rbac_data, dict):
        access = rbac_data.get("access") or {}
        if isinstance(access, dict):
            roles = [
                role.get("id")
                for role in access.get("roles") or []
                if isinstance(role, dict)
            ]
            permissions = [
                permission.get("id")
                for permission in access.get("permissions") or []
                if isinstance(permission, dict)
            ]
            _assign(references, "available_roles", roles)
            _assign(references, "available_permissions", permissions)

    persistence_path = contracts_root / "persistence" / "model.yaml"
    persistence_data = _load_yaml(persistence_path)
    if isinstance(persistence_data, dict):
        datasources = [
            datasource.get("id")
            for datasource in persistence_data.get("datasources") or []
            if isinstance(datasource, dict)
        ]
        tables = [
            table.get("id")
            for table in persistence_data.get("tables") or []
            if isinstance(table, dict)
        ]
        _assign(references, "available_persistence_datasources", datasources)
        _assign(references, "available_persistence_tables", tables)

    integrations_path = contracts_root / "integrations" / "integrations.yaml"
    integrations_data = _load_yaml(integrations_path)
    if isinstance(integrations_data, dict):
        integration_targets = [
            integration.get("id")
            for integration in integrations_data.get("integrations") or []
            if isinstance(integration, dict)
        ]
        operations = [
            operation.get("id")
            for operation in integrations_data.get("operations") or []
            if isinstance(operation, dict)
        ]
        _assign(references, "available_integrations", integration_targets)
        _assign(references, "available_integration_operations", operations)

    scenarios_path = contracts_root / "scenarios" / "scenarios.yaml"
    scenarios_data = _load_yaml(scenarios_path)
    if isinstance(scenarios_data, dict):
        scenarios = [
            scenario.get("id")
            for scenario in scenarios_data.get("scenarios") or []
            if isinstance(scenario, dict)
        ]
        _assign(references, "available_scenarios", scenarios)

    tests_path = contracts_root / "testing" / "tests.yaml"
    tests_data = _load_yaml(tests_path)
    if isinstance(tests_data, dict):
        test_cases = extract_ids_from_yaml_list(tests_data, "tests")
        _assign(references, "existing_tests", test_cases)

    commands_path = contracts_root / "app" / "commands.yaml"
    queries_path = contracts_root / "app" / "queries.yaml"
    commands_data = _load_yaml(commands_path)
    queries_data = _load_yaml(queries_path)
    if isinstance(commands_data, dict):
        _assign(
            references,
            "existing_commands",
            extract_ids_from_yaml_list(commands_data, "commands"),
        )
    if isinstance(queries_data, dict):
        _assign(
            references,
            "existing_queries",
            extract_ids_from_yaml_list(queries_data, "queries"),
        )

    return references
