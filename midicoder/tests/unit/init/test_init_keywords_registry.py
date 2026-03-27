"""Unit tests for init keyword registry and metadata contracts."""

from __future__ import annotations

from midicoder.config.keywords import ConfigKeyword, InitKeywords


def test_config_keyword_dataclass_defaults() -> None:
    kw = ConfigKeyword(flag="--test", env_var="TEST_ENV", description="test", type="text")
    assert kw.required is False
    assert kw.default is None
    assert kw.choices is None
    assert kw.example is None


def test_init_keywords_lookup_by_flag_and_env() -> None:
    by_flag = InitKeywords.get_by_flag("--working-dir")
    by_env = InitKeywords.get_by_env_var("MIDICODER_STACK")

    assert by_flag is not None
    assert by_flag.env_var == "MIDICODER_WORKING_DIR"
    assert by_env is not None
    assert by_env.flag == "--stack"


def test_init_keywords_required_core_flags_are_marked_required() -> None:
    for flag in [
        "--stack",
        "--llm-high-provider",
        "--llm-cheap-provider",
    ]:
        keyword = InitKeywords.get_by_flag(flag)
        assert keyword is not None
        assert keyword.required is True


def test_init_keywords_provider_choices_include_all_supported_clouds() -> None:
    high_kw = InitKeywords.get_by_flag("--llm-high-provider")
    cheap_kw = InitKeywords.get_by_flag("--llm-cheap-provider")
    assert high_kw is not None
    assert cheap_kw is not None

    for provider in ["anthropic", "openai", "openai_compatible", "bedrock", "azure", "vertex_partner"]:
        assert provider in high_kw.choices
        assert provider in cheap_kw.choices


def test_init_keywords_provider_specific_flags_are_registered() -> None:
    for flag in [
        "--llm-high-model",
        "--llm-high-url",
        "--llm-high-key",
        "--llm-high-key-env",
        "--llm-cheap-model",
        "--llm-cheap-url",
        "--llm-cheap-key",
        "--llm-cheap-key-env",
        "--llm-high-anthropic-model",
        "--llm-high-anthropic-key",
        "--llm-high-anthropic-key-env",
        "--llm-cheap-anthropic-model",
        "--llm-cheap-anthropic-key",
        "--llm-cheap-anthropic-key-env",
        "--llm-high-openai-model",
        "--llm-high-openai-key",
        "--llm-high-openai-key-env",
        "--llm-cheap-openai-model",
        "--llm-cheap-openai-key",
        "--llm-cheap-openai-key-env",
        "--llm-high-bedrock-model",
        "--llm-high-aws-region-name",
        "--llm-high-aws-access-key-id",
        "--llm-high-aws-access-key-id-env",
        "--llm-high-aws-secret-access-key",
        "--llm-high-aws-secret-access-key-env",
        "--llm-cheap-bedrock-model",
        "--llm-cheap-aws-region-name",
        "--llm-cheap-aws-access-key-id",
        "--llm-cheap-aws-access-key-id-env",
        "--llm-cheap-aws-secret-access-key",
        "--llm-cheap-aws-secret-access-key-env",
        "--llm-high-azure-model",
        "--llm-high-azure-key",
        "--llm-high-azure-key-env",
        "--llm-high-azure-openai-endpoint",
        "--llm-high-azure-openai-api-version",
        "--llm-high-azure-openai-deployment",
        "--llm-cheap-azure-model",
        "--llm-cheap-azure-key",
        "--llm-cheap-azure-key-env",
        "--llm-cheap-azure-openai-endpoint",
        "--llm-cheap-azure-openai-api-version",
        "--llm-cheap-azure-openai-deployment",
        "--llm-high-vertex-model",
        "--llm-high-vertex-key",
        "--llm-high-vertex-key-env",
        "--llm-high-vertex-project",
        "--llm-high-vertex-location",
        "--llm-cheap-vertex-model",
        "--llm-cheap-vertex-key",
        "--llm-cheap-vertex-key-env",
        "--llm-cheap-vertex-project",
        "--llm-cheap-vertex-location",
    ]:
        assert InitKeywords.get_by_flag(flag) is not None
