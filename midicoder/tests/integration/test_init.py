from __future__ import annotations

import json
from pathlib import Path

from midicoder.cli import main


def _set_common_anthropic_env(monkeypatch, workdir: Path, prefix: str = "MIDICODER_") -> None:
    monkeypatch.setenv(f"{prefix}WORKING_DIR", str(workdir))
    monkeypatch.setenv(f"{prefix}STACK", "fastapi")
    monkeypatch.setenv(f"{prefix}LLM_HIGH_PROVIDER", "anthropic")
    monkeypatch.setenv(f"{prefix}LLM_HIGH_ANTHROPIC_MODEL", "anthropic/claude-3-7-sonnet-latest")
    monkeypatch.setenv(f"{prefix}LLM_CHEAP_PROVIDER", "anthropic")
    monkeypatch.setenv(f"{prefix}LLM_CHEAP_ANTHROPIC_MODEL", "anthropic/claude-3-5-haiku-latest")


def test_init_config_list_prints_keywords_without_writing_config(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    rc = main(["init", "--config-list"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "Configuration Keywords" in out
    assert "--working-dir" in out
    assert "--rewrite-config" in out
    assert not (tmp_path / ".midicoder" / "config.json").exists()


def test_init_non_interactive_from_env_creates_expected_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _set_common_anthropic_env(monkeypatch, tmp_path)

    rc = main(["init", "--non-interactive"])

    assert rc == 0
    config_path = tmp_path / ".midicoder" / "config.json"
    state_path = tmp_path / ".midicoder" / "state.json"
    summary_path = sorted((tmp_path / ".midicoder" / "runs" / "init").iterdir())[-1] / "summary.json"

    assert config_path.exists()
    assert state_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "initialized"
    assert summary["mode"] == "non-interactive"
