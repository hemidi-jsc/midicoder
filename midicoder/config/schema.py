"""Configuration schema and validation utilities."""

from __future__ import annotations

from typing import Any

from .defaults import CONFIG_FIELDS, DEFAULT_STACK


def _get_default_llm_tier_config() -> dict:
    """Get default LLM tier config (common + provider-specific fields)."""
    return {
        # Common fields (shared by all providers)
        "provider": None,
        "model": None,
        "base_url": None,
        # Provider-specific fields (namespace by provider prefix)
        "aws_region_name": None,
        "aws_bedrock_region": None,
        "azure_openai_endpoint": None,
        "azure_openai_api_version": None,
        "azure_openai_deployment": None,
        "vertex_project": None,
        "vertex_location": None,
    }


def get_config_template() -> dict:
    """
    Get a basic configuration template.
    
    Returns:
        Dictionary with minimal required configuration structure
    
    Examples:
        >>> template = get_config_template()
        >>> template["stack"]
        ['fastapi']
    """
    return {
        "working_dir": None,
        "stack": DEFAULT_STACK,
        "commands": [],
        "llm": {
            "high": _get_default_llm_tier_config(),
            "cheap": _get_default_llm_tier_config(),
        },
        "cache": {
            "enable": True,
            "type": "ephemeral",
        },
        "snapshot_whitelist": None,
    }


def apply_defaults(config: dict) -> dict:
    """
    Apply minimal defaults to configuration if missing.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        New configuration dictionary with defaults applied
    
    Examples:
        >>> config = {"stack": ["fastapi"]}
        >>> config_with_defaults = apply_defaults(config)
        >>> config_with_defaults["commands"]
        []
    """
    result = config.copy()
    
    # Apply only essential defaults
    if "working_dir" not in result:
        result["working_dir"] = None
    
    if "stack" not in result:
        result["stack"] = DEFAULT_STACK
    
    if "commands" not in result:
        result["commands"] = []
    
    if "llm" not in result:
        result["llm"] = {
            "high": _get_default_llm_tier_config(),
            "cheap": _get_default_llm_tier_config(),
        }
    
    if "cache" not in result:
        result["cache"] = {
            "enable": True,
            "type": "ephemeral",
        }
    
    return result


def check_config_fields(config: dict) -> dict[str, list[str]]:
    """
    Check configuration for common issues (non-strict validation).
    
    Args:
        config: Configuration dictionary to check
    
    Returns:
        Dictionary with 'warnings' and 'errors' lists
    
    Examples:
        >>> issues = check_config_fields({"stack": ["fastapi"]})
        >>> issues["errors"]
        []
        >>> issues["warnings"]
        ['Field "llm" is not configured', 'Field "working_dir" is not configured']
    """
    warnings = []
    errors = []
    
    # Check for working directory
    if "working_dir" not in config or config["working_dir"] is None:
        warnings.append('Field "working_dir" is not configured')
    
    # Check for required fields
    if "stack" not in config:
        errors.append('Required field "stack" is missing')
    elif isinstance(config["stack"], list):
        supported = ["fastapi", "nest", "angular"]
        for stack in config["stack"]:
            if stack not in supported:
                warnings.append(f'Stack "{stack}" may not be supported')
    elif isinstance(config["stack"], str):
        # Legacy support for single stack as string
        if config["stack"] not in ["fastapi", "nest", "angular"]:
            warnings.append(f'Stack "{config["stack"]}" may not be supported')
        warnings.append('Stack should be an array, not a string')
    
    # Check for LLM configuration
    if "llm" not in config or not config["llm"]:
        warnings.append('Field "llm" is not configured')
    elif isinstance(config["llm"], dict):
        for tier in ["high", "cheap"]:
            if tier in config["llm"]:
                tier_config = config["llm"][tier]
                if isinstance(tier_config, dict):
                    if not tier_config.get("model"):
                        warnings.append(f'LLM tier "{tier}" has no model specified')
    
    # Check for unknown top-level fields (informational only)
    for field in config:
        if field not in CONFIG_FIELDS:
            warnings.append(f'Unknown top-level field "{field}" (may be custom extension)')
    
    return {
        "warnings": warnings,
        "errors": errors,
    }


def validate_config_dict(config: dict) -> list[str]:
    """
    Validate configuration dictionary (backward compatibility).
    
    Args:
        config: Configuration dictionary to validate
    
    Returns:
        List of error messages, empty if valid
    
    Examples:
        >>> errors = validate_config_dict({"stack": "fastapi", "llm": {}})
        >>> if errors:
        ...     print("Validation errors:", errors)
    """
    issues = check_config_fields(config)
    return issues["errors"]


def is_secret_field(field_path: str) -> bool:
    """
    Check if a field path appears to be a secret field.
    
    Args:
        field_path: Dot-notation path to field (e.g., "llm.high.api_key")
    
    Returns:
        True if field looks like a secret (contains 'key', 'password', 'token', 'secret')
    
    Examples:
        >>> is_secret_field("llm.high.api_key")
        True
        >>> is_secret_field("database.password")
        True
        >>> is_secret_field("stack")
        False
    """
    field_lower = field_path.lower()
    secret_indicators = ["key", "password", "token", "secret", "credential"]
    
    return any(indicator in field_lower for indicator in secret_indicators)
