"""Integration tests for `midicoder init --non-interactive`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from midicoder.cli import main


def _base_flags(workdir: Path) -> list[str]:
    return [
        "init",
        "--non-interactive",
        "--working-dir",
        str(workdir),
        "--stack",
        "fastapi",
        "--llm-high-provider",
        "anthropic",
        "--llm-high-anthropic-model",
        "anthropic/claude-3-7-sonnet-latest",
        "--llm-cheap-provider",
        "anthropic",
        "--llm-cheap-anthropic-model",
        "anthropic/claude-3-5-haiku-latest",
    ]


def test_non_interactive_respects_flag_over_env_priority(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MIDICODER_STACK", "nest")

    rc = main(_base_flags(tmp_path) + ["--stack", "fastapi,angular"])

    assert rc == 0
    payload = json.loads((tmp_path / ".midicoder" / "config.json").read_text(encoding="utf-8"))
    assert payload["stack"] == ["fastapi", "angular"]


def test_non_interactive_refuses_second_run_without_explicit_rewrite(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(_base_flags(tmp_path)) == 0

    with pytest.raises(SystemExit):
        main(_base_flags(tmp_path))


def test_non_interactive_rewrite_with_custom_prefix_env_keeps_legacy_data(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(_base_flags(tmp_path)) == 0

    legacy_file = tmp_path / ".midicoder" / "runs" / "legacy.log"
    legacy_file.parent.mkdir(parents=True, exist_ok=True)
    legacy_file.write_text("preserve", encoding="utf-8")

    monkeypatch.setenv("MC_REWRITE_CONFIG", "true")
    rc = main(
        _base_flags(tmp_path)
        + [
            "--env-prefix",
            "MC_",
            "--stack",
            "fastapi,nest",
        ]
    )

    assert rc == 0
    config = json.loads((tmp_path / ".midicoder" / "config.json").read_text(encoding="utf-8"))
    assert config["stack"] == ["fastapi", "nest"]
    assert legacy_file.exists()


def test_non_interactive_validates_provider_specific_requirements(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit):
        main(
            [
                "init",
                "--non-interactive",
                "--working-dir",
                str(tmp_path),
                "--stack",
                "fastapi",
                "--llm-high-provider",
                "azure",
                "--llm-high-azure-model",
                "azure/gpt-4o",
                "--llm-cheap-provider",
                "anthropic",
                "--llm-cheap-anthropic-model",
                "anthropic/claude-3-5-haiku-latest",
            ]
        )
