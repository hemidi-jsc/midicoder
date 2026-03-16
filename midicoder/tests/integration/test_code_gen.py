from __future__ import annotations

import json
from pathlib import Path

from tests.conftest import assert_cli_success, run_cli, write_minimal_contracts


def test_code_gen_creates_runtime_code_index(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)
    index_result = run_cli(["index"], tmp_workdir)
    assert_cli_success(index_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    write_minimal_contracts(tmp_workdir, version)

    ir_result = run_cli(["ir", "build"], tmp_workdir)
    assert_cli_success(ir_result)

    plan_result = run_cli(["code", "plan"], tmp_workdir)
    assert_cli_success(plan_result)

    gen_result = run_cli(["code", "gen"], tmp_workdir)
    assert_cli_success(gen_result)

    index_path = (
        tmp_workdir
        / ".midicoder"
        / "versions"
        / version
        / "patches"
        / "index.json"
    )
    assert index_path.exists(), "expected patches/index.json to be created"

    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload.get("schema_version") == "3.0.0"
    assert payload.get("stack") == "fastapi"
    assert payload.get("runtime_enabled") is False
    generated_patch_plans = payload.get("generated_patch_plans")
    assert isinstance(generated_patch_plans, list)
    assert generated_patch_plans, "expected generated patch-plan files in patches"
    first_patch_plan = tmp_workdir / ".midicoder" / "versions" / version / "patches" / generated_patch_plans[0]
    assert first_patch_plan.exists(), "expected patch-plan file to be generated"
    assert first_patch_plan.suffixes[-2:] == [".patch-plan", ".json"] or first_patch_plan.name.endswith(".patch-plan.json")

    runtime_files = payload.get("generated_runtime_files")
    assert isinstance(runtime_files, list)
    assert runtime_files == [], "runtime files should be empty by default"


def test_code_gen_is_deterministic_for_same_input(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)
    index_result = run_cli(["index"], tmp_workdir)
    assert_cli_success(index_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    write_minimal_contracts(tmp_workdir, version)

    ir_result = run_cli(["ir", "build"], tmp_workdir)
    assert_cli_success(ir_result)

    plan_result = run_cli(["code", "plan"], tmp_workdir)
    assert_cli_success(plan_result)

    gen_first = run_cli(["code", "gen"], tmp_workdir)
    assert_cli_success(gen_first)

    index_path = tmp_workdir / ".midicoder" / "versions" / version / "patches" / "index.json"
    first_output = index_path.read_text(encoding="utf-8")

    gen_second = run_cli(["code", "gen"], tmp_workdir)
    assert_cli_success(gen_second)
    second_output = index_path.read_text(encoding="utf-8")

    assert first_output == second_output, "code gen index should be deterministic across runs"


def test_code_gen_runtime_flag_generates_runtime_artifacts(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)
    index_result = run_cli(["index"], tmp_workdir)
    assert_cli_success(index_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    write_minimal_contracts(tmp_workdir, version)

    ir_result = run_cli(["ir", "build"], tmp_workdir)
    assert_cli_success(ir_result)

    plan_result = run_cli(["code", "plan"], tmp_workdir)
    assert_cli_success(plan_result)

    gen_result = run_cli(["code", "gen", "--runtime"], tmp_workdir)
    assert_cli_success(gen_result)

    index_path = tmp_workdir / ".midicoder" / "versions" / version / "patches" / "index.json"
    payload = json.loads(index_path.read_text(encoding="utf-8"))

    assert payload.get("runtime_enabled") is True
    generated_patch_plans = payload.get("generated_patch_plans")
    assert isinstance(generated_patch_plans, list) and generated_patch_plans

    generated_runtime_files = payload.get("generated_runtime_files")
    assert isinstance(generated_runtime_files, list) and generated_runtime_files
    first_runtime = tmp_workdir / ".midicoder" / "versions" / version / "patches" / generated_runtime_files[0]
    assert first_runtime.exists()
    assert "runtime" in first_runtime.parts
