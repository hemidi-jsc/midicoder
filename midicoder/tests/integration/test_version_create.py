from __future__ import annotations

import json
from pathlib import Path

from midicoder.tests.conftest import assert_cli_success, run_cli


def test_version_create_sets_current_version(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    master_brief = tmp_workdir / ".midicoder" / "versions" / version / "master-brief.md"
    assert master_brief.exists(), "expected master-brief.md to be created"

    state_path = tmp_workdir / ".midicoder" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state.get("current_version") == version
    # TODO: add assertions for version state.json and run summaries.
