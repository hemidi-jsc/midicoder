from __future__ import annotations

from pathlib import Path

from midicoder.tests.conftest import assert_cli_success, run_cli, write_minimal_contracts


def test_ir_build_generates_ir(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    write_minimal_contracts(tmp_workdir, version)

    ir_result = run_cli(["ir", "build"], tmp_workdir)
    assert_cli_success(ir_result)

    ir_path = tmp_workdir / ".midicoder" / "versions" / version / "irs" / "ir.json"
    assert ir_path.exists(), "expected ir.json to be created"
    # TODO: validate IR manifest payload.


def test_ir_build_preserves_vietnamese_unicode(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    contracts_root = write_minimal_contracts(tmp_workdir, version)
    commands_path = contracts_root / "app" / "commands.yaml"
    command_yaml = commands_path.read_text(encoding="utf-8")
    command_yaml = command_yaml.replace(
        "  - id: CreateOrder\n",
        "  - id: CreateOrder\n    description: Giao dịch đã ghi nhận\n",
        1,
    )
    commands_path.write_text(command_yaml, encoding="utf-8")

    ir_result = run_cli(["ir", "build"], tmp_workdir)
    assert_cli_success(ir_result)

    ir_path = tmp_workdir / ".midicoder" / "versions" / version / "irs" / "ir.json"
    ir_text = ir_path.read_text(encoding="utf-8")
    raw_phrase = "Giao dịch đã ghi nhận"
    escaped_phrase = raw_phrase.encode("unicode_escape").decode("ascii")
    assert raw_phrase in ir_text, "expected raw Vietnamese text in ir.json"
    assert escaped_phrase not in ir_text, "unexpected escaped Unicode sequence in ir.json"
