from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from tests.conftest import assert_cli_success, run_cli


def test_contract_feedback_creates_file(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    feedback_result = run_cli(["contract", "feedback"], tmp_workdir)
    assert_cli_success(feedback_result)

    feedback_path = tmp_workdir / ".midicoder" / "versions" / version / "contract-feedbacks.yml"
    assert feedback_path.exists(), "expected contract-feedbacks.yml to be created"
    yaml_loader = YAML(typ="safe")
    payload = yaml_loader.load(feedback_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert set(payload.keys()) >= {"meta", "items", "notes"}
    items = payload.get("items")
    assert isinstance(items, list)
    assert items, "expected feedback items generated from contract check"
    first_item = items[0]
    assert isinstance(first_item, dict)
    for key in ("id", "file", "location", "status", "issue"):
        assert key in first_item


def test_contract_feedback_does_not_overwrite_existing_file(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    feedback_path = tmp_workdir / ".midicoder" / "versions" / version / "contract-feedbacks.yml"
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    feedback_path.write_text(
        """
meta:
  version: "0.1.0"
  author: "tester"
  created_at: "2025-01-01T00:00:00Z"
  scope: "contracts"
items:
  - id: "FB-001"
    file: "contracts/app/commands.yaml"
    location: "commands[id=CreateOrder]"
    status: "pending"
    issue: "Existing issue"
    suggestion: "Existing suggestion"
    last_error: null
notes:
  - "initial note"
""".lstrip(),
        encoding="utf-8",
    )

    feedback_result = run_cli(["contract", "feedback"], tmp_workdir)
    assert_cli_success(feedback_result)

    yaml_loader = YAML(typ="safe")
    payload = yaml_loader.load(feedback_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    items = payload.get("items")
    assert isinstance(items, list)
    assert any(item.get("id") == "FB-001" for item in items if isinstance(item, dict))
    assert len(items) >= 1
