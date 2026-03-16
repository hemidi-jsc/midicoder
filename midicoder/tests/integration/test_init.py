from __future__ import annotations

from pathlib import Path

from tests.conftest import assert_cli_success, run_cli


def test_init_creates_base_files(tmp_workdir: Path) -> None:
    result = run_cli(["init"], tmp_workdir)
    assert_cli_success(result)

    config_path = tmp_workdir / ".midicoder" / "config.json"
    state_path = tmp_workdir / ".midicoder" / "state.json"

    assert config_path.exists(), "expected config.json to be created"
    assert state_path.exists(), "expected state.json to be created"
    # TODO: validate config/state payloads in more detail.
