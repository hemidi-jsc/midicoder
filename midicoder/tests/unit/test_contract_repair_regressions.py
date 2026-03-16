from __future__ import annotations

from pathlib import Path

from midicoder.contract.contract_utils import _extract_inner_issue_location
from midicoder.contract.contract_validator import _lint_rule_references
from midicoder.contract.patch_manager import _apply_replace_node_patch, _is_array_index_path
from midicoder.dsl.models import RulesFile
from ruamel.yaml import YAML


def test_array_index_path_supports_mixed_field_and_array_segments() -> None:
    assert _is_array_index_path("access.bindings[0].permissions[0]")
    assert _is_array_index_path("commands[1].effects[2]")
    assert not _is_array_index_path("access.bindings.permissions")


def test_rule_applies_to_untyped_query_ref_is_accepted() -> None:
    rules = RulesFile.model_validate(
        {
            "rules": [
                {
                    "id": "secure_file_access",
                    "applies_to": "GetDocumentDownloadURL",
                    "rows": [],
                }
            ]
        }
    )

    issues = _lint_rule_references(
        rules,
        Path("contracts/rules/rules.yaml"),
        command_ids=set(),
        query_ids={"GetDocumentDownloadURL"},
        workflow_ids=set(),
        policy_ids=set(),
        scenario_ids=set(),
    )
    assert not issues


def test_extract_inner_issue_location_windows_drive_path() -> None:
    issue_location = r"D:\workspace\repo\contracts\rules\rules.yaml:rules[2].applies_to"
    assert _extract_inner_issue_location(issue_location) == "rules[2].applies_to"


def test_replace_node_supports_s3_resources_array_path() -> None:
    data = {
        "s3_resources": [
            {
                "operations": [
                    "IntegrationOperation:UploadDocument",
                    "IntegrationOperation:DownloadDocument",
                ]
            }
        ]
    }
    errors: list[str] = []
    yaml_loader = YAML(typ="safe")
    ok = _apply_replace_node_patch(
        data,
        "s3_resources[0].operations",
        "[]\n",
        errors,
        "contracts/integrations/integrations.yaml",
        yaml_loader,
    )
    assert ok
    assert data["s3_resources"][0]["operations"] == []
    assert not errors
