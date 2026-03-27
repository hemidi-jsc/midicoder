"""Unit tests for config schema behaviors used by init flow."""

from __future__ import annotations

from midicoder.config.schema import apply_defaults, get_config_template


def test_config_template_exposes_provider_specific_llm_fields() -> None:
    template = get_config_template()
    for tier in ["high", "cheap"]:
        tier_cfg = template["llm"][tier]
        assert "provider" in tier_cfg
        assert "model" in tier_cfg
        assert "base_url" in tier_cfg
        assert "aws_region_name" in tier_cfg
        assert "azure_openai_endpoint" in tier_cfg
        assert "azure_openai_api_version" in tier_cfg
        assert "azure_openai_deployment" in tier_cfg
        assert "vertex_project" in tier_cfg
        assert "vertex_location" in tier_cfg


def test_apply_defaults_remains_backward_compatible_for_legacy_llm_shape() -> None:
    legacy_config = {
        "working_dir": "/tmp/project",
        "stack": ["fastapi"],
        "commands": [],
        "llm": {
            "high": {"provider": "anthropic", "model": "claude-sonnet", "base_url": "https://api.anthropic.com"},
            "cheap": {"provider": "anthropic", "model": "claude-haiku", "base_url": "https://api.anthropic.com"},
        },
        "cache": {"enable": True, "type": "ephemeral"},
    }
    loaded = apply_defaults(legacy_config)
    assert loaded["llm"]["high"]["provider"] == "anthropic"
    assert loaded["llm"]["cheap"]["provider"] == "anthropic"
    assert "aws_region_name" not in loaded["llm"]["high"]
