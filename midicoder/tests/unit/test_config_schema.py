"""Unit tests for config schema compatibility and defaults."""

from midicoder.config.schema import apply_defaults, get_config_template


def test_config_template_includes_provider_specific_fields() -> None:
    """Template should expose common + provider-specific fields for each tier."""
    template = get_config_template()

    for tier in ["high", "cheap"]:
        tier_cfg = template["llm"][tier]
        assert "provider" in tier_cfg
        assert "model" in tier_cfg
        assert "base_url" in tier_cfg
        assert "aws_bedrock_region" in tier_cfg
        assert "azure_openai_endpoint" in tier_cfg
        assert "azure_openai_api_version" in tier_cfg
        assert "azure_openai_deployment" in tier_cfg
        assert "google_vertex_project" in tier_cfg
        assert "google_vertex_location" in tier_cfg


def test_apply_defaults_is_backward_compatible_with_legacy_llm_shape() -> None:
    """Legacy config should still load without requiring new fields."""
    legacy_config = {
        "working_dir": "/tmp/project",
        "stack": ["fastapi"],
        "commands": [],
        "llm": {
            "high": {"provider": "anthropic", "model": "claude-3-5-sonnet", "base_url": "https://api.anthropic.com"},
            "cheap": {"provider": "anthropic", "model": "claude-3-5-haiku", "base_url": "https://api.anthropic.com"},
        },
        "cache": {"enable": True, "type": "ephemeral"},
    }

    loaded = apply_defaults(legacy_config)

    assert loaded["llm"]["high"]["provider"] == "anthropic"
    assert loaded["llm"]["cheap"]["provider"] == "anthropic"
    # New fields are optional and therefore not required in existing config.
    assert "aws_bedrock_region" not in loaded["llm"]["high"]
