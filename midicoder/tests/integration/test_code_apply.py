from __future__ import annotations

import json
from pathlib import Path

from midicoder.tests.conftest import assert_cli_success, run_cli, write_minimal_contracts


def _prepare_generated_patches(tmp_workdir: Path) -> tuple[str, dict[str, object]]:
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

    plan_result = run_cli(["code", "build"], tmp_workdir)
    assert_cli_success(plan_result)

    gen_result = run_cli(["code", "gen", "--runtime"], tmp_workdir)
    assert_cli_success(gen_result)

    patches_index = tmp_workdir / ".midicoder" / "versions" / version / "patches" / "index.json"
    payload = json.loads(patches_index.read_text(encoding="utf-8"))
    generated_patch_plans = payload.get("generated_patch_plans") or []
    assert isinstance(generated_patch_plans, list)
    assert generated_patch_plans, "expected generated patch-plan files from code gen"
    return version, payload


def _resolve_working_dir(tmp_workdir: Path) -> Path:
    config_payload = json.loads((tmp_workdir / ".midicoder" / "config.json").read_text(encoding="utf-8"))
    working_dir = Path(str(config_payload.get("working_dir")))
    if not working_dir.is_absolute():
        working_dir = (tmp_workdir / working_dir).resolve()
    return working_dir


def _latest_apply_summary(tmp_workdir: Path) -> dict[str, object]:
    runs_dir = tmp_workdir / ".midicoder" / "runs" / "code_apply"
    assert runs_dir.exists(), "expected code_apply run directory to be created"
    latest = sorted(runs_dir.iterdir())[-1]
    return json.loads((latest / "summary.json").read_text(encoding="utf-8"))


def test_code_apply_applies_all_patch_plans_and_writes_report(tmp_workdir: Path) -> None:
    version, patches_index = _prepare_generated_patches(tmp_workdir)
    targets = [
        str(item.get("runtime_path"))
        for item in (patches_index.get("patch_plan_targets") or [])
        if isinstance(item, dict) and item.get("runtime_path")
    ]
    assert targets, "expected patch_plan_targets in patches/index.json"

    apply_result = run_cli(["code", "apply"], tmp_workdir)
    assert_cli_success(apply_result)

    payload = _latest_apply_summary(tmp_workdir)
    assert payload.get("status") in {"success", "partial"}
    assert int(payload.get("processed_count", 0)) == len(targets)
    assert int(payload.get("applied_count", 0)) + int(payload.get("noop_count", 0)) >= len(targets)

    report_path = payload.get("report_path")
    assert isinstance(report_path, str) and report_path

    report_payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    assert report_payload.get("version") == version
    assert report_payload.get("status") in {"success", "partial"}
    assert int(report_payload.get("summary", {}).get("total", 0)) == len(targets)


def test_code_apply_dry_run_does_not_write_destination(tmp_workdir: Path) -> None:
    _, patches_index = _prepare_generated_patches(tmp_workdir)
    targets = [
        str(item.get("runtime_path"))
        for item in (patches_index.get("patch_plan_targets") or [])
        if isinstance(item, dict) and item.get("runtime_path")
    ]
    assert targets
    destination_path = _resolve_working_dir(tmp_workdir) / targets[0]
    assert not destination_path.exists()

    apply_result = run_cli(["code", "apply", "--dry-run"], tmp_workdir)
    assert_cli_success(apply_result)

    payload = _latest_apply_summary(tmp_workdir)
    assert payload.get("dry_run") is True
    assert destination_path.exists() is False, "dry-run must not write destination files"


def test_code_apply_is_idempotent_for_same_input(tmp_workdir: Path) -> None:
    _prepare_generated_patches(tmp_workdir)

    first_apply = run_cli(["code", "apply"], tmp_workdir)
    assert_cli_success(first_apply)
    first_payload = _latest_apply_summary(tmp_workdir)
    assert first_payload.get("status") in {"success", "partial"}

    second_apply = run_cli(["code", "apply"], tmp_workdir)
    assert_cli_success(second_apply)
    second_payload = _latest_apply_summary(tmp_workdir)
    assert second_payload.get("status") in {"success", "partial"}
    assert int(second_payload.get("failed_count", 0)) == 0
    assert int(second_payload.get("noop_count", 0)) >= int(first_payload.get("processed_count", 0))


def test_code_apply_rolls_back_file_when_python_syntax_invalid(tmp_workdir: Path) -> None:
    version, patches_index = _prepare_generated_patches(tmp_workdir)

    first_apply = run_cli(["code", "apply"], tmp_workdir)
    assert_cli_success(first_apply)

    targets = [
        item
        for item in (patches_index.get("patch_plan_targets") or [])
        if isinstance(item, dict) and str(item.get("runtime_path", "")).endswith(".py")
    ]
    assert targets, "expected at least one python target in patch_plan_targets"
    target_item = targets[0]
    runtime_path = str(target_item.get("runtime_path"))
    patch_plan_file = str(target_item.get("patch_plan_file"))

    working_file = _resolve_working_dir(tmp_workdir) / runtime_path
    original_content = working_file.read_text(encoding="utf-8")

    patch_plan_path = tmp_workdir / ".midicoder" / "versions" / version / "patches" / patch_plan_file
    plan_payload = json.loads(patch_plan_path.read_text(encoding="utf-8"))
    operations = plan_payload.get("operations") or []
    assert operations and isinstance(operations[0], dict)
    operations[0]["region_content"] = "def broken(:\n    pass\n"
    patch_plan_path.write_text(json.dumps(plan_payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    failed_apply = run_cli(["code", "apply"], tmp_workdir)
    assert_cli_success(failed_apply)

    payload = _latest_apply_summary(tmp_workdir)
    assert payload.get("status") in {"partial", "failed"}
    assert runtime_path in (payload.get("failed_files") or [])
    assert working_file.read_text(encoding="utf-8") == original_content

