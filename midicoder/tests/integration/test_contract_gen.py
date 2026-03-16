from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import assert_cli_success, copy_brief, run_cli, write_llm_config


# Happy-path: khi đã có LLM config hợp lệ và master-brief,
# lệnh `contract gen` phải sinh đầy đủ bộ file contracts cho version
def test_contract_gen_happy_path(tmp_workdir: Path) -> None:
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

    gen_result = run_cli(["contract", "gen"], tmp_workdir)
    assert_cli_success(gen_result)

    contracts_root = tmp_workdir / ".midicoder" / "versions" / version / "contracts"
    assert contracts_root.exists(), "expected contracts directory to be created"
    expected_files = [
        contracts_root / "meta" / "info.yaml",
        contracts_root / "glossary.yaml",
        contracts_root / "domain" / "entities.yaml",
        contracts_root / "domain" / "errors.yaml",
        contracts_root / "app" / "commands.yaml",
        contracts_root / "api" / "http.yaml",
        contracts_root / "rules" / "rules.yaml",
    ]
    missing = [path for path in expected_files if not path.exists()]
    assert not missing, f"missing contract files: {[path.as_posix() for path in missing]}"


# Negative-case: khi không có LLM config trong workspace,
# lệnh `contract gen` phải fail để ép người dùng cấu hình trước
def test_contract_gen_fails_without_llm_config(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    index_result = run_cli(["index"], tmp_workdir)
    assert_cli_success(index_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    master_brief = tmp_workdir / ".midicoder" / "versions" / version / "master-brief.md"
    copy_brief("master-brief-basic.md", master_brief)

    gen_result = run_cli(["contract", "gen"], tmp_workdir)
    assert gen_result.returncode != 0
