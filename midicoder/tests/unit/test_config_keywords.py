"""Unit tests for configuration keywords."""

import os

from midicoder.config.keywords import ConfigKeyword, InitKeywords


class TestConfigKeyword:
    """Test ConfigKeyword dataclass."""

    def test_create_keyword(self):
        """Test creating a ConfigKeyword instance."""
        kw = ConfigKeyword(
            flag="--test-flag",
            env_var="MIDICODER_TEST_FLAG",
            description="Test flag",
            type="text",
            required=True,
            example="test-value",
        )
        assert kw.flag == "--test-flag"
        assert kw.env_var == "MIDICODER_TEST_FLAG"
        assert kw.required is True
        assert kw.example == "test-value"

    def test_keyword_defaults(self):
        """Test default values for optional fields."""
        kw = ConfigKeyword(flag="--test", env_var="TEST", description="Test", type="text")
        assert kw.required is False
        assert kw.default is None
        assert kw.choices is None
        assert kw.example is None


class TestInitKeywords:
    """Test InitKeywords registry."""

    def test_get_by_flag(self):
        """Test getting keyword by flag name."""
        kw = InitKeywords.get_by_flag("--working-dir")
        assert kw is not None
        assert kw.env_var == "MIDICODER_WORKING_DIR"
        assert kw.type == "text"

    def test_get_by_flag_not_found(self):
        """Test getting non-existent flag."""
        kw = InitKeywords.get_by_flag("--nonexistent-flag")
        assert kw is None

    def test_get_by_env_var(self):
        """Test getting keyword by environment variable."""
        kw = InitKeywords.get_by_env_var("MIDICODER_STACK")
        assert kw is not None
        assert kw.flag == "--stack"
        assert kw.type == "multichoice"

    def test_get_by_env_var_not_found(self):
        """Test getting non-existent env var."""
        kw = InitKeywords.get_by_env_var("NONEXISTENT_VAR")
        assert kw is None

    def test_all_keywords_have_required_fields(self):
        """Test that all keywords have required fields."""
        for kw in InitKeywords.KEYWORDS:
            assert kw.flag.startswith("--"), f"Flag {kw.flag} should start with --"
            assert kw.description, f"Flag {kw.flag} missing description"
            assert kw.type in ["text", "choice", "multichoice", "secret"], (
                f"Flag {kw.flag} has invalid type: {kw.type}"
            )

    def test_required_keywords(self):
        """Test that required keywords are marked correctly."""
        required_flags = [
            "--stack",
            "--llm-high-provider",
            "--llm-high-model",
            "--llm-cheap-provider",
            "--llm-cheap-model",
        ]

        for flag in required_flags:
            kw = InitKeywords.get_by_flag(flag)
            assert kw is not None, f"Required flag {flag} not found"
            assert kw.required is True, f"Flag {flag} should be required"

    def test_choice_keywords_have_choices(self):
        """Test that choice/multichoice keywords have choices defined."""
        for kw in InitKeywords.KEYWORDS:
            if kw.type in ["choice", "multichoice"]:
                assert kw.choices is not None, f"Flag {kw.flag} is {kw.type} but has no choices"
                assert len(kw.choices) > 0, f"Flag {kw.flag} has empty choices list"

    def test_provider_keyword_choices_include_cloud_providers(self):
        """Provider choices should include all supported cloud providers."""
        high_kw = InitKeywords.get_by_flag("--llm-high-provider")
        cheap_kw = InitKeywords.get_by_flag("--llm-cheap-provider")

        assert high_kw is not None
        assert cheap_kw is not None

        for provider in ["anthropic", "openai", "aws_bedrock", "azure_openai", "google_vertex"]:
            assert provider in high_kw.choices
            assert provider in cheap_kw.choices

    def test_provider_specific_keywords_are_registered(self):
        """Provider-specific keywords should be listed for non-interactive init."""
        expected_flags = [
            "--llm-high-aws-bedrock-region",
            "--llm-cheap-aws-bedrock-region",
            "--llm-high-azure-openai-endpoint",
            "--llm-high-azure-openai-api-version",
            "--llm-high-azure-openai-deployment",
            "--llm-cheap-azure-openai-endpoint",
            "--llm-cheap-azure-openai-api-version",
            "--llm-cheap-azure-openai-deployment",
            "--llm-high-google-vertex-project",
            "--llm-high-google-vertex-location",
            "--llm-cheap-google-vertex-project",
            "--llm-cheap-google-vertex-location",
        ]
        for flag in expected_flags:
            assert InitKeywords.get_by_flag(flag) is not None


class TestInitHelpers:
    """Test helper functions in init command."""

    def test_get_value_with_priority_flag_first(self):
        """Test that flag value has highest priority."""
        from midicoder.commands.init import _get_value_with_priority

        os.environ["MIDICODER_TEST"] = "from_env"
        try:
            result = _get_value_with_priority(
                flag_value="from_flag", env_var_name="TEST", default="default_value"
            )
            assert result == "from_flag"
        finally:
            del os.environ["MIDICODER_TEST"]

    def test_get_value_with_priority_env_second(self):
        """Test that env var has second priority."""
        from midicoder.commands.init import _get_value_with_priority

        os.environ["MIDICODER_TEST"] = "from_env"
        try:
            result = _get_value_with_priority(
                flag_value=None, env_var_name="TEST", default="default_value"
            )
            assert result == "from_env"
        finally:
            del os.environ["MIDICODER_TEST"]

    def test_get_value_with_priority_default_last(self):
        """Test that default has lowest priority."""
        from midicoder.commands.init import _get_value_with_priority

        result = _get_value_with_priority(
            flag_value=None, env_var_name="NONEXISTENT", default="default_value"
        )
        assert result == "default_value"

    def test_parse_stack_from_string(self):
        """Test parsing stack from comma-separated string."""
        from midicoder.commands.init import _parse_stack

        result = _parse_stack("fastapi,nest,angular")
        assert result == ["fastapi", "nest", "angular"]

    def test_parse_stack_from_string_with_spaces(self):
        """Test parsing stack with spaces around commas."""
        from midicoder.commands.init import _parse_stack

        result = _parse_stack("fastapi, nest , angular")
        assert result == ["fastapi", "nest", "angular"]

    def test_parse_stack_from_list(self):
        """Test parsing stack from list."""
        from midicoder.commands.init import _parse_stack

        result = _parse_stack(["fastapi", "nest"])
        assert result == ["fastapi", "nest"]

    def test_parse_stack_none_returns_default(self):
        """Test that None returns default stack."""
        from midicoder.commands.init import _parse_stack
        from midicoder.config.defaults import DEFAULT_STACK

        result = _parse_stack(None)
        assert result == DEFAULT_STACK

    def test_parse_stack_empty_string_returns_default(self):
        """Test that empty string returns default stack."""
        from midicoder.commands.init import _parse_stack
        from midicoder.config.defaults import DEFAULT_STACK

        result = _parse_stack("")
        assert result == DEFAULT_STACK

    def test_get_api_key_from_direct(self, capsys):
        """Test getting API key from direct value (should warn)."""
        from midicoder.commands.init import _get_api_key

        result = _get_api_key(
            tier="high", key_direct="sk-direct-key", key_env_name=None, env_prefix="MIDICODER_"
        )
        assert result == "sk-direct-key"

        # Check that warning was printed
        captured = capsys.readouterr()
        combined_output = " ".join((captured.out + " " + captured.err).lower().split())
        assert "visible in process list" in combined_output

    def test_get_api_key_from_env_via_flag(self):
        """Test getting API key from custom env var."""
        from midicoder.commands.init import _get_api_key

        os.environ["MY_API_KEY"] = "sk-from-custom-env"
        try:
            result = _get_api_key(
                tier="high", key_direct=None, key_env_name="MY_API_KEY", env_prefix="MIDICODER_"
            )
            assert result == "sk-from-custom-env"
        finally:
            del os.environ["MY_API_KEY"]

    def test_get_api_key_from_default_env(self):
        """Test getting API key from default env var."""
        from midicoder.commands.init import _get_api_key

        os.environ["MIDICODER_LLM_HIGH_API_KEY"] = "sk-from-default-env"
        try:
            result = _get_api_key(
                tier="high", key_direct=None, key_env_name=None, env_prefix="MIDICODER_"
            )
            assert result == "sk-from-default-env"
        finally:
            del os.environ["MIDICODER_LLM_HIGH_API_KEY"]

    def test_get_api_key_returns_none_if_not_found(self):
        """Test that None is returned when no API key found."""
        from midicoder.commands.init import _get_api_key

        result = _get_api_key(
            tier="high", key_direct=None, key_env_name="NONEXISTENT_KEY", env_prefix="MIDICODER_"
        )
        assert result is None

    def test_config_overwrite_requested_from_env(self):
        """Rewrite policy should accept boolean env value when flag is not set."""
        from midicoder.commands.init import _config_overwrite_requested

        class Args:
            rewrite_config = None

        os.environ["MIDICODER_REWRITE_CONFIG"] = "true"
        try:
            assert _config_overwrite_requested(Args(), "MIDICODER_") is True
        finally:
            del os.environ["MIDICODER_REWRITE_CONFIG"]


class TestConfigValidation:
    """Test configuration validation."""

    def test_validate_required_config_success(self):
        """Test validation with all required fields."""
        from midicoder.commands.init import _validate_required_config

        config = {
            "stack": ["fastapi"],
            "llm": {
                "high": {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-5",
                    "base_url": "https://api.anthropic.com",
                },
                "cheap": {
                    "provider": "anthropic",
                    "model": "claude-3-5-haiku",
                    "base_url": "https://api.anthropic.com",
                },
            },
        }
        secrets = {
            "llm": {"high": {"api_key": "sk-test-high"}, "cheap": {"api_key": "sk-test-cheap"}}
        }

        errors = _validate_required_config(config, secrets)
        assert len(errors) == 0

    def test_validate_required_config_missing_stack(self):
        """Test validation fails when stack is missing."""
        from midicoder.commands.init import _validate_required_config

        config = {"llm": {}}
        secrets = {"llm": {}}

        errors = _validate_required_config(config, secrets)
        assert any("Stack is required" in e for e in errors)

    def test_validate_required_config_unsupported_stack(self):
        """Test validation fails for unsupported stack."""
        from midicoder.commands.init import _validate_required_config

        config = {"stack": ["invalid-stack"], "llm": {}}
        secrets = {"llm": {}}

        errors = _validate_required_config(config, secrets)
        assert any("Unsupported stack" in e for e in errors)

    def test_validate_required_config_missing_api_key(self):
        """Test validation fails when API key is missing."""
        from midicoder.commands.init import _validate_required_config

        config = {
            "stack": ["fastapi"],
            "llm": {
                "high": {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-5",
                    "base_url": "https://api.anthropic.com",
                },
                "cheap": {
                    "provider": "anthropic",
                    "model": "claude-3-5-haiku",
                    "base_url": "https://api.anthropic.com",
                },
            },
        }
        secrets = {"llm": {"high": {}, "cheap": {}}}

        errors = _validate_required_config(config, secrets)
        assert any("API key is required" in e for e in errors)

    def test_validate_required_config_missing_llm_provider(self):
        """Test validation fails when LLM provider is missing."""
        from midicoder.commands.init import _validate_required_config

        config = {
            "stack": ["fastapi"],
            "llm": {
                "high": {"model": "claude-sonnet-4-5", "base_url": "https://api.anthropic.com"},
                "cheap": {},
            },
        }
        secrets = {"llm": {}}

        errors = _validate_required_config(config, secrets)
        assert any("provider is required" in e for e in errors)

    def test_validate_required_config_bedrock_requires_region(self):
        """AWS Bedrock provider requires aws_bedrock_region instead of base_url."""
        from midicoder.commands.init import _validate_required_config

        config = {
            "stack": ["fastapi"],
            "llm": {
                "high": {
                    "provider": "aws_bedrock",
                    "model": "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
                    "aws_bedrock_region": "us-east-1",
                },
                "cheap": {
                    "provider": "aws_bedrock",
                    "model": "bedrock/anthropic.claude-3-5-haiku-20241022-v1:0",
                    "aws_bedrock_region": "us-east-1",
                },
            },
        }
        secrets = {
            "llm": {"high": {"api_key": "dummy"}, "cheap": {"api_key": "dummy"}}
        }

        errors = _validate_required_config(config, secrets)
        assert len(errors) == 0

    def test_validate_required_config_azure_requires_specific_fields(self):
        """Azure OpenAI provider should fail when required provider-specific fields are missing."""
        from midicoder.commands.init import _validate_required_config

        config = {
            "stack": ["fastapi"],
            "llm": {
                "high": {
                    "provider": "azure_openai",
                    "model": "azure/gpt-4o",
                    "azure_openai_endpoint": "https://my-resource.openai.azure.com",
                },
                "cheap": {
                    "provider": "azure_openai",
                    "model": "azure/gpt-4o-mini",
                    "azure_openai_endpoint": "https://my-resource.openai.azure.com",
                    "azure_openai_api_version": "2024-10-21",
                    "azure_openai_deployment": "gpt-4o-mini-dev",
                },
            },
        }
        secrets = {
            "llm": {"high": {"api_key": "dummy"}, "cheap": {"api_key": "dummy"}}
        }

        errors = _validate_required_config(config, secrets)
        assert any("azure_openai_api_version" in e for e in errors)
        assert any("azure_openai_deployment" in e for e in errors)
