"""Unit tests for `midicoder init` non-interactive flow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from midicoder.commands.base import MidicoderPaths
from midicoder.commands.init import run
from midicoder.config import ConfigManager, SecretsManager

from .conftest import make_non_interactive_args


def test_non_interactive_init_creates_workspace_and_summary(tmp_path: Path) -> None:
    run(tmp_path, make_non_interactive_args(tmp_path))

    paths = MidicoderPaths(root=tmp_path)
    assert paths.config.exists()
    assert paths.state.exists()
    assert (paths.secrets / "secrets.json").exists()
    assert (paths.dot_midicoder / ".gitignore").exists()

    config = ConfigManager(paths).load()
    assert config["working_dir"] == str(tmp_path)
    assert config["stack"] == ["fastapi"]

    run_dirs = sorted((paths.runs / "init").iterdir())
    summary = json.loads((run_dirs[-1] / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "initialized"
    assert summary["mode"] == "non-interactive"


def test_non_interactive_uses_flag_then_env_then_default_priority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIDICODER_STACK", "fastapi")
    monkeypatch.setenv("MIDICODER_LLM_HIGH_PROVIDER", "openai")
    monkeypatch.setenv("MIDICODER_LLM_HIGH_OPENAI_MODEL", "gpt-4o")

    run(
        tmp_path,
        make_non_interactive_args(
            tmp_path,
            stack="nest,angular",
            llm_high_provider="anthropic",
            llm_high_anthropic_model="anthropic/claude-3-7-sonnet-latest",
        ),
    )

    config = ConfigManager(MidicoderPaths(root=tmp_path)).load()
    assert config["stack"] == ["nest", "angular"]
    assert config["llm"]["high"]["provider"] == "anthropic"


def test_non_interactive_reads_missing_values_from_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIDICODER_STACK", "fastapi,nest")
    monkeypatch.setenv("MIDICODER_LLM_HIGH_PROVIDER", "openai")
    monkeypatch.setenv("MIDICODER_LLM_HIGH_OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("MIDICODER_LLM_CHEAP_PROVIDER", "openai")
    monkeypatch.setenv("MIDICODER_LLM_CHEAP_OPENAI_MODEL", "gpt-4o-mini")

    run(
        tmp_path,
        make_non_interactive_args(
            tmp_path,
            stack=None,
            llm_high_provider=None,
            llm_high_openai_model=None,
            llm_high_anthropic_model=None,
            llm_cheap_provider=None,
            llm_cheap_openai_model=None,
            llm_cheap_anthropic_model=None,
        ),
    )

    config = ConfigManager(MidicoderPaths(root=tmp_path)).load()
    assert config["stack"] == ["fastapi", "nest"]
    assert config["llm"]["high"]["provider"] == "openai"
    assert config["llm"]["high"]["model"] == "gpt-4o"


def test_existing_config_without_rewrite_permission_fails(tmp_path: Path) -> None:
    run(tmp_path, make_non_interactive_args(tmp_path, rewrite_config=False))

    with pytest.raises(SystemExit):
        run(tmp_path, make_non_interactive_args(tmp_path, rewrite_config=False))


def test_rewrite_via_custom_prefix_env_var_preserves_legacy_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run(tmp_path, make_non_interactive_args(tmp_path, rewrite_config=False))

    marker = tmp_path / ".midicoder" / "runs" / "keep.txt"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("keep", encoding="utf-8")

    monkeypatch.setenv("MC_REWRITE_CONFIG", "true")
    run(
        tmp_path,
        make_non_interactive_args(
            tmp_path,
            env_prefix="MC_",
            rewrite_config=None,
            stack="fastapi,nest",
        ),
    )

    config = ConfigManager(MidicoderPaths(root=tmp_path)).load()
    assert config["stack"] == ["fastapi", "nest"]
    assert marker.exists()


def test_invalid_rewrite_env_value_exits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIDICODER_REWRITE_CONFIG", "maybe")

    with pytest.raises(SystemExit):
        run(tmp_path, make_non_interactive_args(tmp_path, rewrite_config=None))


def test_provider_specific_validation_for_azure_required_fields(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        run(
            tmp_path,
            make_non_interactive_args(
                tmp_path,
                llm_high_provider="azure",
                llm_high_azure_model="azure/gpt-4o",
                llm_high_azure_openai_endpoint=None,
                llm_high_azure_openai_api_version=None,
                llm_high_azure_openai_deployment=None,
            ),
        )


def test_bedrock_requires_secret_credentials(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        run(
            tmp_path,
            make_non_interactive_args(
                tmp_path,
                llm_high_provider="bedrock",
                llm_high_bedrock_model="bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
                llm_high_aws_region_name="us-east-1",
                llm_cheap_provider="bedrock",
                llm_cheap_bedrock_model="bedrock/anthropic.claude-3-5-haiku-20241022-v1:0",
                llm_cheap_aws_region_name="us-east-1",
                llm_high_anthropic_model=None,
                llm_cheap_anthropic_model=None,
            ),
        )


def test_bedrock_reads_secret_credentials_from_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIDICODER_LLM_HIGH_AWS_ACCESS_KEY_ID", "AKIA-HIGH")
    monkeypatch.setenv("MIDICODER_LLM_HIGH_AWS_SECRET_ACCESS_KEY", "HIGH-SECRET")
    monkeypatch.setenv("MIDICODER_LLM_CHEAP_AWS_ACCESS_KEY_ID", "AKIA-CHEAP")
    monkeypatch.setenv("MIDICODER_LLM_CHEAP_AWS_SECRET_ACCESS_KEY", "CHEAP-SECRET")

    run(
        tmp_path,
        make_non_interactive_args(
            tmp_path,
            llm_high_provider="bedrock",
            llm_high_bedrock_model="bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
            llm_high_aws_region_name="us-east-1",
            llm_cheap_provider="bedrock",
            llm_cheap_bedrock_model="bedrock/anthropic.claude-3-5-haiku-20241022-v1:0",
            llm_cheap_aws_region_name="us-east-1",
            llm_high_anthropic_model=None,
            llm_cheap_anthropic_model=None,
        ),
    )

    llm_secrets = SecretsManager(MidicoderPaths(root=tmp_path).secrets).load_secrets("llm")
    assert llm_secrets["high"]["aws_access_key_id"] == "AKIA-HIGH"
    assert llm_secrets["cheap"]["aws_secret_access_key"] == "CHEAP-SECRET"


def test_non_interactive_allows_missing_api_keys(tmp_path: Path) -> None:
    run(
        tmp_path,
        make_non_interactive_args(
            tmp_path,
            llm_high_anthropic_key=None,
            llm_high_anthropic_key_env=None,
            llm_cheap_anthropic_key=None,
            llm_cheap_anthropic_key_env=None,
        ),
    )

    llm_secrets = SecretsManager(MidicoderPaths(root=tmp_path).secrets).load_secrets("llm")
    assert "api_key" not in llm_secrets["high"]
    assert "api_key" not in llm_secrets["cheap"]
