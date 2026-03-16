from __future__ import annotations

from pathlib import Path

from midicoder.contract.contract_validator import _lint_policy_references
from midicoder.dsl.models import PoliciesFile


def test_policy_runtime_field_is_complete_is_allowed_for_entity_scope() -> None:
    policies = PoliciesFile.model_validate(
        {
            "policies": [
                {
                    "id": "payroll_completion_policy",
                    "scope": "entity:Payroll",
                    "conditions": [
                        {"field": "is_complete", "op": "eq", "value": True},
                    ],
                    "effects": [{"type": "deny", "params": {}}],
                }
            ]
        }
    )

    issues = _lint_policy_references(
        policies,
        Path("contracts/policy/policies.yaml"),
        entity_field_map={"Payroll": {"id", "status"}},
        command_ids=set(),
        query_ids=set(),
        workflow_ids=set(),
        projection_ids=set(),
        integration_ids=set(),
    )
    assert not issues
