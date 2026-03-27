"""Unit tests for `midicoder init` interactive flow and run() interactive branches."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from midicoder.commands import init as init_cmd
from midicoder.commands.base import MidicoderPaths
from midicoder.config import ConfigManager, SecretsManager


def test_run_config_list_calls_help_and_returns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[bool] = []

    class _FakeKeywords:
        @staticmethod
        def print_help() -> None:
            called.append(True)

    monkeypatch.setattr("midicoder.config.keywords.InitKeywords", _FakeKeywords)
    init_cmd.run(tmp_path, SimpleNamespace(config_list=True, non_interactive=False))

    assert called == [True]
    assert not MidicoderPaths(root=tmp_path).config.exists()


def test_run_interactive_mode_writes_interactive_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(init_cmd, "_initialize_config_interactive", lambda _paths: None)
    init_cmd.run(tmp_path, SimpleNamespace(config_list=False, non_interactive=False))

    run_root = MidicoderPaths(root=tmp_path).runs / "init"
    run_dirs = sorted(run_root.iterdir())
    assert run_dirs
    summary = (run_dirs[-1] / "summary.json").read_text(encoding="utf-8")
    assert '"mode": "interactive"' in summary


def test_interactive_existing_config_rewrite_denied_exits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = MidicoderPaths(root=tmp_path)
    paths.config.parent.mkdir(parents=True, exist_ok=True)
    paths.config.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(init_cmd, "prompt_confirm", lambda *_args, **_kwargs: False)
    with pytest.raises(SystemExit):
        init_cmd._initialize_config_interactive(paths)


def test_interactive_config_manager_validation_error_exits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = MidicoderPaths(root=tmp_path)

    def _raise_value_error(self: ConfigManager, validate_fn: object | None = None) -> None:
        raise ValueError("line-a\nline-b")

    monkeypatch.setattr(ConfigManager, "initialize_interactive", _raise_value_error)
    with pytest.raises(SystemExit):
        init_cmd._initialize_config_interactive(paths)


def test_config_manager_interactive_persists_azure_provider_specific_fields(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Keep regression coverage for the interactive wizard details used by init."""
    paths = MidicoderPaths(root=tmp_path)
    manager = ConfigManager(paths)

    choice_answers = iter(["azure", "azure"])
    text_answers = iter(
        [
            str(tmp_path),
            "https://my-resource.openai.azure.com",
            "2024-10-21",
            "gpt-4o-prod",
            "azure/gpt-4o",
            "",
            "",
            "",
            "azure/gpt-4o-mini",
        ]
    )
    secret_answers = iter(["sk-high", ""])

    monkeypatch.setattr("midicoder.io.prompt_text", lambda *_a, **_k: next(text_answers))
    monkeypatch.setattr("midicoder.io.prompt_choice", lambda *_a, **_k: next(choice_answers))
    monkeypatch.setattr("midicoder.io.prompt_multichoice", lambda *_a, **_k: ["fastapi"])
    monkeypatch.setattr("midicoder.io.prompt_secret", lambda *_a, **_k: next(secret_answers))
    monkeypatch.setattr("midicoder.io.messages.print_info", lambda *_a, **_k: None)
    monkeypatch.setattr("midicoder.io.messages.print_success", lambda *_a, **_k: None)
    monkeypatch.setattr("midicoder.io.messages.print_normal", lambda *_a, **_k: None)

    manager.initialize_interactive()

    config = manager.load()
    assert config["llm"]["high"]["provider"] == "azure"
    assert config["llm"]["high"]["azure_openai_endpoint"] == "https://my-resource.openai.azure.com"
    assert config["llm"]["high"]["azure_openai_api_version"] == "2024-10-21"
    assert config["llm"]["high"]["azure_openai_deployment"] == "gpt-4o-prod"
    assert config["llm"]["cheap"]["provider"] == "azure"
    assert config["llm"]["cheap"]["azure_openai_endpoint"] == "https://my-resource.openai.azure.com"
    assert config["llm"]["cheap"]["azure_openai_api_version"] == "2024-10-21"
    assert config["llm"]["cheap"]["azure_openai_deployment"] == "gpt-4o-prod"

    llm_secrets = SecretsManager(paths.secrets).load_secrets("llm")
    assert llm_secrets["high"]["api_key"] == "sk-high"
    assert llm_secrets["cheap"]["api_key"] == "sk-high"


def test_config_manager_interactive_uses_shared_validator(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Keep regression coverage for validate_fn hook consumed by init command."""
    manager = ConfigManager(MidicoderPaths(root=tmp_path))
    choice_answers = iter(["anthropic", "anthropic"])
    text_answers = iter([str(tmp_path), "anthropic/claude-3-7-sonnet-latest", "anthropic/claude-3-5-haiku-latest"])
    secret_answers = iter(["sk-high", "sk-cheap"])

    monkeypatch.setattr("midicoder.io.prompt_text", lambda *_a, **_k: next(text_answers))
    monkeypatch.setattr("midicoder.io.prompt_choice", lambda *_a, **_k: next(choice_answers))
    monkeypatch.setattr("midicoder.io.prompt_multichoice", lambda *_a, **_k: ["fastapi"])
    monkeypatch.setattr("midicoder.io.prompt_secret", lambda *_a, **_k: next(secret_answers))
    monkeypatch.setattr("midicoder.io.messages.print_info", lambda *_a, **_k: None)
    monkeypatch.setattr("midicoder.io.messages.print_success", lambda *_a, **_k: None)
    monkeypatch.setattr("midicoder.io.messages.print_normal", lambda *_a, **_k: None)

    def _reject(_config: dict, _secrets: dict) -> list[str]:
        return ["forced validation error"]

    with pytest.raises(ValueError):
        manager.initialize_interactive(validate_fn=_reject)
