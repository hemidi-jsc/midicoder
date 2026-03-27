from __future__ import annotations

import json
from pathlib import Path

from midicoder.tests.conftest import assert_cli_success, run_cli, write_minimal_contracts


def test_code_plan_creates_index(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    write_minimal_contracts(tmp_workdir, version)

    ir_result = run_cli(["ir", "build"], tmp_workdir)
    assert_cli_success(ir_result)

    plan_result = run_cli(["code", "build"], tmp_workdir)
    assert_cli_success(plan_result)

    plans_root = tmp_workdir / ".midicoder" / "versions" / version / "plans"
    index_path = plans_root / "index.json"
    assert index_path.exists(), "expected plans/index.json to be created"

    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    for rel_path in index_payload.get("plans", []):
        payload = json.loads((plans_root / rel_path).read_text(encoding="utf-8"))
        required_files = payload.get("required_files")
        assert isinstance(required_files, list), "required_files must be present"
        assert required_files, "required_files must not be empty"
        for entry in required_files:
            assert isinstance(entry.get("path_pattern"), str) and entry["path_pattern"].strip()
            assert isinstance(entry.get("required"), bool)
            assert isinstance(entry.get("role"), str) and entry["role"].strip()

        if payload.get("target") == "fastapi_model":
            pseudo_struct = payload.get("pseudo_struct", {})
            entity = pseudo_struct.get("entity")
            assert isinstance(entity, dict), "entity pseudo struct is required for model targets"
            assert isinstance(entity.get("fields"), list) and entity["fields"], "entity fields must not be empty"
