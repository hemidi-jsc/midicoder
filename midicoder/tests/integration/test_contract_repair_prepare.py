from __future__ import annotations

from pathlib import Path

from midicoder.tests.conftest import assert_cli_success, run_cli, write_minimal_contracts


def test_contract_repair_prepare_validates_feedback(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    write_minimal_contracts(tmp_workdir, version)

    feedback_path = tmp_workdir / ".midicoder" / "versions" / version / "contract-feedbacks.yml"
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
    issue: "Missing output fields"
    suggestion: "Add returns list"
    last_error: null
notes: []
""".lstrip(),
        encoding="utf-8",
    )

    prepare_result = run_cli(["contract", "repair", "prepare"], tmp_workdir)
    assert_cli_success(prepare_result)


def test_contract_repair_prepare_fails_on_invalid_schema(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    write_minimal_contracts(tmp_workdir, version)

    feedback_path = tmp_workdir / ".midicoder" / "versions" / version / "contract-feedbacks.yml"
    feedback_path.write_text("items: \"not-a-list\"\n", encoding="utf-8")

    prepare_result = run_cli(["contract", "repair", "prepare"], tmp_workdir)
    assert prepare_result.returncode != 0


def test_contract_repair_prepare_fails_on_missing_file_reference(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    write_minimal_contracts(tmp_workdir, version)

    feedback_path = tmp_workdir / ".midicoder" / "versions" / version / "contract-feedbacks.yml"
    feedback_path.write_text(
        """
meta:
  version: "0.1.0"
  author: "tester"
  created_at: "2025-01-01T00:00:00Z"
  scope: "contracts"
items:
  - id: "FB-001"
    file: "contracts/domain/missing.yaml"
    location: "entities[id=Missing]"
    status: "pending"
    issue: "Missing entity"
    suggestion: "Add entity"
    last_error: null
notes: []
""".lstrip(),
        encoding="utf-8",
    )

    prepare_result = run_cli(["contract", "repair", "prepare"], tmp_workdir)
    assert prepare_result.returncode != 0
