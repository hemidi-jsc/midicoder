"""Unit tests for `midicoder.commands.init` helper functions."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from midicoder.commands import init as init_cmd


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, None), (True, True), (False, False), ("YES", True), ("off", False)],
)
def test_parse_optional_bool_valid_values(value: object, expected: bool | None) -> None:
    assert init_cmd._parse_optional_bool(value) is expected


def test_parse_optional_bool_invalid_value_raises() -> None:
    with pytest.raises(ValueError):
        init_cmd._parse_optional_bool("definitely")


def test_normalize_provider_name_handles_none_and_blank() -> None:
    assert init_cmd._normalize_provider_name(None) is None
    assert init_cmd._normalize_provider_name("   ") is None
    assert init_cmd._normalize_provider_name("  OPENAI  ") == "openai"


def test_get_value_with_priority_prefers_flag_then_env_then_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIDICODER_SAMPLE", "from-env")
    assert init_cmd._get_value_with_priority("from-flag", "SAMPLE", default="fallback") == "from-flag"
    assert init_cmd._get_value_with_priority(None, "SAMPLE", default="fallback") == "from-env"
    monkeypatch.delenv("MIDICODER_SAMPLE")
    assert init_cmd._get_value_with_priority(None, "SAMPLE", default="fallback") == "fallback"


def test_parse_stack_string_list_and_invalid_type() -> None:
    assert init_cmd._parse_stack("fastapi, nest") == ["fastapi", "nest"]
    assert init_cmd._parse_stack(["angular"]) == ["angular"]
    assert init_cmd._parse_stack(123) == ["fastapi"]


def test_get_api_key_prefers_direct_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIDICODER_LLM_HIGH_API_KEY", "env-key")
    assert init_cmd._get_api_key("high", "direct-key", None, "MIDICODER_") == "direct-key"


def test_get_api_key_uses_env_reference_then_default_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CUSTOM_KEY", "custom")
    assert init_cmd._get_api_key("cheap", None, "CUSTOM_KEY", "MIDICODER_") == "custom"
    monkeypatch.delenv("CUSTOM_KEY")
    monkeypatch.setenv("MIDICODER_LLM_CHEAP_API_KEY", "fallback")
    assert init_cmd._get_api_key("cheap", None, "CUSTOM_KEY", "MIDICODER_") == "fallback"


def test_get_secret_value_covers_priority_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    assert (
        init_cmd._get_secret_value(
            tier="high",
            secret_name="aws_access_key_id",
            value_direct="direct-access",
            value_env_name=None,
            env_prefix="MIDICODER_",
        )
        == "direct-access"
    )

    monkeypatch.setenv("CUSTOM_ACCESS", "custom-access")
    assert (
        init_cmd._get_secret_value(
            tier="high",
            secret_name="aws_access_key_id",
            value_direct=None,
            value_env_name="CUSTOM_ACCESS",
            env_prefix="MIDICODER_",
        )
        == "custom-access"
    )

    monkeypatch.delenv("CUSTOM_ACCESS")
    monkeypatch.setenv("MIDICODER_LLM_HIGH_AWS_ACCESS_KEY_ID", "fallback-access")
    assert (
        init_cmd._get_secret_value(
            tier="high",
            secret_name="aws_access_key_id",
            value_direct=None,
            value_env_name="MISSING_ENV",
            env_prefix="MIDICODER_",
        )
        == "fallback-access"
    )


def test_validate_required_config_reports_provider_specific_and_secret_errors() -> None:
    config = {
        "stack": ["invalid-stack"],
        "llm": {
            "high": {
                "provider": "bedrock",
                "model": "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
                "aws_region_name": None,
            },
            "cheap": {
                "provider": "azure",
                "model": "azure/gpt-4o-mini",
                "azure_openai_endpoint": None,
                "azure_openai_api_version": None,
                "azure_openai_deployment": None,
            },
        },
    }
    secrets = {"llm": {"high": {}, "cheap": {}}}

    errors = init_cmd._validate_required_config(config, secrets)
    joined = "\n".join(errors)
    assert "Unsupported stack" in joined
    assert "requires 'aws_region_name'" in joined
    assert "requires secret 'aws_access_key_id'" in joined
    assert "requires secret 'aws_secret_access_key'" in joined
    assert "requires 'azure_openai_endpoint'" in joined
    assert "requires 'azure_openai_api_version'" in joined
    assert "requires 'azure_openai_deployment'" in joined


def test_validate_required_config_happy_path_with_bedrock_secrets() -> None:
    config = {
        "stack": ["fastapi"],
        "llm": {
            "high": {
                "provider": "bedrock",
                "model": "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
                "aws_region_name": "us-east-1",
            },
            "cheap": {
                "provider": "bedrock",
                "model": "bedrock/anthropic.claude-3-5-haiku-20241022-v1:0",
                "aws_region_name": "us-east-1",
            },
        },
    }
    secrets = {
        "llm": {
            "high": {"aws_access_key_id": "AKIA-HIGH", "aws_secret_access_key": "HIGH-SECRET"},
            "cheap": {"aws_access_key_id": "AKIA-CHEAP", "aws_secret_access_key": "CHEAP-SECRET"},
        }
    }
    assert init_cmd._validate_required_config(config, secrets) == []


def test_build_llm_tier_config_uses_provider_default_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIDICODER_LLM_HIGH_PROVIDER", "OPENAI")
    monkeypatch.setenv("MIDICODER_LLM_HIGH_OPENAI_MODEL", "gpt-4o")
    args = SimpleNamespace(
        llm_high_provider=None,
        llm_high_openai_model=None,
        llm_high_url=None,
    )
    config = init_cmd._build_llm_tier_config("high", args, "MIDICODER_")
    assert config["provider"] == "openai"
    assert config["model"] == "gpt-4o"
    assert config["base_url"] == "https://api.openai.com/v1"
