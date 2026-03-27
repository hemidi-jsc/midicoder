from __future__ import annotations

import json
from pathlib import Path

from ruamel.yaml import YAML

import pytest

from midicoder.tests.conftest import assert_cli_success, copy_brief, run_cli, write_llm_config, write_minimal_contracts


def test_contract_repair_run_applies_updates(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    llm_config = write_llm_config(tmp_workdir)
    if llm_config is None:
        pytest.skip("LLM config missing; run `midicoder init` in the repository root")

    index_result = run_cli(["index"], tmp_workdir)
    assert_cli_success(index_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    master_brief = tmp_workdir / ".midicoder" / "versions" / version / "master-brief.md"
    copy_brief("master-brief-basic.md", master_brief)

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

    run_result = run_cli(["contract", "repair", "run"], tmp_workdir)
    assert_cli_success(run_result)

    runs_root = tmp_workdir / ".midicoder" / "runs" / "contract_repair_run"
    run_dirs = sorted([path for path in runs_root.iterdir() if path.is_dir()])
    assert run_dirs, "expected contract_repair_run to create a run directory"
    run_dir = run_dirs[-1]

    plan_path = run_dir / "patch_plan.json"
    assert plan_path.exists(), "expected patch_plan.json to be created"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    summary_path = run_dir / "summary.json"
    assert summary_path.exists(), "expected summary.json to be created"

    yaml_loader = YAML(typ="safe")
    feedback = yaml_loader.load(feedback_path.read_text(encoding="utf-8"))
    assert isinstance(feedback, dict)
    items = feedback.get("items", [])
    assert isinstance(items, list)

    updates = plan.get("feedback_status_updates", [])
    if updates:
        update_map = {update.get("id"): update for update in updates if isinstance(update, dict)}
        for item in items:
            if item.get("id") in update_map:
                expected_status = update_map[item["id"]].get("status")
                if expected_status:
                    assert item.get("status") == expected_status

    memos = plan.get("memos", [])
    if memos:
        memos_dir = tmp_workdir / ".midicoder" / "context" / "memos"
        for memo in memos:
            if isinstance(memo, dict) and memo.get("id"):
                memo_path = memos_dir / f"{memo['id']}.md"
                assert memo_path.exists()

    patches = plan.get("patches", [])
    if patches:
        contracts_root = tmp_workdir / ".midicoder" / "versions" / version / "contracts"
        for patch in patches:
            if not isinstance(patch, dict):
                continue
            file_path = patch.get("file")
            if not file_path:
                continue
            target = contracts_root / str(file_path).replace("contracts/", "")
            assert target.exists()
