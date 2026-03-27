"""Initialize the .midicoder workspace and basic config."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from midicoder.config import ConfigManager
from midicoder.config.defaults import (
    DEFAULT_STACK,
    LLM_PROVIDERS,
    PROVIDER_BASE_URLS,
    SUPPORTED_STACKS,
)
from midicoder.io import prompt_confirm, print_warning, print_info

from .base import (
    MidicoderPaths,
    create_run_dir,
    ensure_base_layout,
    read_state,
    write_run_outputs,
    write_state,
)

PROVIDER_REQUIRED_FIELDS: dict[str, list[str]] = {
    "openai_compatible": ["base_url"],
    "bedrock": ["aws_region_name"],
    "azure": [
        "azure_openai_endpoint",
        "azure_openai_api_version",
        "azure_openai_deployment",
    ],
    "vertex_partner": [
        "vertex_project",
        "vertex_location",
    ],
}

def _warn_existing_workspace_detected() -> None:
    """Show overwrite behavior when an existing config is detected."""
    print_warning(
        "Config already exists. Overwrite will update config/secrets only.",
        title="Overwrite Mode",
    )
    print_info("Existing runs, logs, versions, index, and other .midicoder data will be kept.")


def _parse_optional_bool(value: Any) -> bool | None:
    """Parse optional bool values from flag/env inputs."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: '{value}'")


def _normalize_provider_name(provider: Any) -> str | None:
    """Normalize provider id from input value."""
    if provider is None:
        return None
    text = str(provider).strip().lower()
    if not text:
        return None
    return text


def _config_overwrite_requested(args: Any, env_prefix: str) -> bool:
    """Resolve rewrite policy in non-interactive mode."""
    raw = _get_value_with_priority(
        getattr(args, "rewrite_config", None),
        "REWRITE_CONFIG",
        default=False,
        env_prefix=env_prefix,
    )
    parsed = _parse_optional_bool(raw)
    return bool(parsed) if parsed is not None else False


def _get_flag_and_env_for_field(tier: str, field_name: str, env_prefix: str) -> tuple[str, str]:
    """Build CLI flag/env key names from a config field."""
    flag = f"--llm-{tier}-{field_name.replace('_', '-')}"
    env_key = f"{env_prefix}LLM_{tier.upper()}_{field_name.upper()}"
    return flag, env_key


def _get_value_with_priority(
    flag_value: Any,
    env_var_name: str,
    default: Any = None,
    env_prefix: str = "MIDICODER_",
) -> Any:
    """
    Get configuration value with priority: flag > env var > default.
    
    Args:
        flag_value: Value from command-line flag
        env_var_name: Environment variable name (without prefix)
        default: Default value
        env_prefix: Environment variable prefix
    
    Returns:
        Configuration value
    """
    # Priority 1: Command-line flag
    if flag_value is not None:
        return flag_value
    
    # Priority 2: Environment variable
    full_env_var = f"{env_prefix}{env_var_name}"
    env_value = os.getenv(full_env_var)
    if env_value is not None:
        return env_value
    
    # Priority 3: Default value
    return default


def _parse_stack(stack_value: Any) -> list[str]:
    """
    Parse stack value (can be comma-separated string or list).
    
    Args:
        stack_value: Stack value from flag or env var
    
    Returns:
        List of stack names
    """
    if stack_value is None:
        return DEFAULT_STACK
    
    if isinstance(stack_value, str):
        # Split by comma and clean whitespace
        stacks = [s.strip() for s in stack_value.split(",") if s.strip()]
        return stacks if stacks else DEFAULT_STACK
    
    if isinstance(stack_value, list):
        return stack_value
    
    return DEFAULT_STACK


def _get_api_key(
    tier: str,
    key_direct: str | None,
    key_env_name: str | None,
    env_prefix: str,
) -> str | None:
    """
    Get API key from direct value or environment variable.
    
    Args:
        tier: Tier name (high/cheap) for logging
        key_direct: Direct API key value (not recommended)
        key_env_name: Name of environment variable containing API key
        env_prefix: Environment variable prefix
    
    Returns:
        API key or None
    """
    # Priority 1: Direct key from flag (not recommended, will warn)
    if key_direct:
        print_warning(
            f"⚠️  API key for {tier} tier provided via --llm-{tier}-key flag. "
            f"This is visible in process list (ps, top, etc.). "
            f"Use --llm-{tier}-key-env instead for better security."
        )
        return key_direct
    
    # Priority 2: Key from environment variable (via --llm-X-key-env flag)
    if key_env_name:
        api_key = os.getenv(key_env_name)
        if api_key:
            print_info(f"✓ Using API key for {tier} tier from env var: {key_env_name}")
            return api_key
        else:
            print_warning(f"Environment variable {key_env_name} not found for {tier} tier")
    
    # Priority 3: Key directly from MIDICODER_LLM_X_API_KEY env var
    default_env_var = f"{env_prefix}LLM_{tier.upper()}_API_KEY"
    api_key = os.getenv(default_env_var)
    if api_key:
        print_info(f"✓ Using API key for {tier} tier from env var: {default_env_var}")
        return api_key
    
    return None


def _validate_required_config(
    config: dict,
    secrets: dict,
    *,
    env_prefix: str = "MIDICODER_",
) -> list[str]:
    """
    Validate that all required configuration is present.
    
    Args:
        config: Configuration dictionary
        secrets: Secrets dictionary
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check stack
    if not config.get("stack"):
        errors.append("Stack is required")
    else:
        for stack in config["stack"]:
            if stack not in SUPPORTED_STACKS:
                errors.append(
                    f"Unsupported stack: '{stack}'. "
                    f"Supported stacks: {', '.join(SUPPORTED_STACKS)}"
                )
    
    # Check LLM configuration
    for tier in ["high", "cheap"]:
        tier_config = config.get("llm", {}).get(tier, {})
        
        provider = _normalize_provider_name(tier_config.get("provider"))
        if not provider:
            errors.append(f"LLM {tier} tier provider is required")
        elif provider not in LLM_PROVIDERS:
            errors.append(
                f"Unsupported LLM provider for {tier} tier: '{provider}'. "
                f"Supported providers: {', '.join(LLM_PROVIDERS)}"
            )
        
        if not tier_config.get("model"):
            errors.append(f"LLM {tier} tier model is required")

        if provider in PROVIDER_REQUIRED_FIELDS:
            for required_field in PROVIDER_REQUIRED_FIELDS[provider]:
                if not tier_config.get(required_field):
                    flag, env_key = _get_flag_and_env_for_field(tier, required_field, env_prefix)
                    errors.append(
                        f"LLM {tier} tier with provider '{provider}' requires '{required_field}'. "
                        f"Set via {flag} or {env_key}."
                    )
        
    return errors


def _validate_init_payload(
    config: dict,
    llm_secrets: dict,
    *,
    env_prefix: str = "MIDICODER_",
) -> list[str]:
    """Shared init validation for both interactive and non-interactive flows."""
    return _validate_required_config(config, {"llm": llm_secrets}, env_prefix=env_prefix)


def _build_llm_tier_config(tier: str, args: Any, env_prefix: str) -> dict[str, Any]:
    """Build one LLM tier config using naming convention for flag/env/config keys."""
    provider = _get_value_with_priority(
        getattr(args, f"llm_{tier}_provider", None),
        f"LLM_{tier.upper()}_PROVIDER",
        env_prefix=env_prefix,
    )
    provider = _normalize_provider_name(provider)

    tier_config: dict[str, Any] = {
        "provider": provider,
        "model": _get_value_with_priority(
            getattr(args, f"llm_{tier}_model", None),
            f"LLM_{tier.upper()}_MODEL",
            env_prefix=env_prefix,
        ),
        "base_url": _get_value_with_priority(
            getattr(args, f"llm_{tier}_url", None),
            f"LLM_{tier.upper()}_URL",
            default=PROVIDER_BASE_URLS.get(provider),
            env_prefix=env_prefix,
        ),
    }

    provider_specific_fields = [
        "aws_region_name",
        "azure_openai_endpoint",
        "azure_openai_api_version",
        "azure_openai_deployment",
        "vertex_project",
        "vertex_location",
    ]
    for field in provider_specific_fields:
        tier_config[field] = _get_value_with_priority(
            getattr(args, f"llm_{tier}_{field}", None),
            f"LLM_{tier.upper()}_{field.upper()}",
            env_prefix=env_prefix,
        )

    return tier_config


def _initialize_config_interactive(paths: MidicoderPaths) -> None:
    """Interactive initialization (existing behavior)."""
    if paths.config.exists():
        _warn_existing_workspace_detected()
        overwrite = prompt_confirm(
            "Config already exists. Overwrite?",
            default=False
        )
        if not overwrite:
            from midicoder.io import print_error
            print_error(
                "Rewrite denied. Existing config was not changed.",
                title="Rewrite Not Allowed",
            )
            raise SystemExit(1)
    
    config_manager = ConfigManager(paths)
    from midicoder.io import print_error, print_info, print_normal

    try:
        config_manager.initialize_interactive(validate_fn=_validate_init_payload)
    except ValueError as exc:
        print_error("Configuration validation failed:", title="Error")
        for line in str(exc).splitlines():
            line = line.strip()
            if line:
                print_error(f"  • {line}")
        print_normal("")
        print_info("Please retry init and fill the missing provider-specific fields.")
        raise SystemExit(1)


def _initialize_config_non_interactive(paths: MidicoderPaths, args: Any) -> None:
    """
    Non-interactive initialization using flags and environment variables.
    
    Args:
        paths: Midicoder paths
        args: Command-line arguments from argparse
    
    Raises:
        SystemExit: If validation fails
    """
    from midicoder.config import SecretsManager
    from midicoder.io import print_error, print_success, print_normal
    
    print_info("Initializing configuration (non-interactive mode)...", title="Init")
    
    env_prefix = getattr(args, "env_prefix", "MIDICODER_")

    # CL010: explicit rewrite policy for non-interactive mode.
    try:
        rewrite_allowed = _config_overwrite_requested(args, env_prefix)
    except ValueError as exc:
        print_error(str(exc), title="Invalid rewrite setting")
        print_info("Use --rewrite-config or set env value to true/false.")
        raise SystemExit(1)

    if paths.config.exists() and not rewrite_allowed:
        print_error(
            "Config already exists. Refusing to overwrite in non-interactive mode "
            "without explicit rewrite permission.",
            title="Rewrite Not Allowed",
        )
        print_info(f"Retry with --rewrite-config or set {env_prefix}REWRITE_CONFIG=true.")
        raise SystemExit(1)

    if paths.config.exists() and rewrite_allowed:
        _warn_existing_workspace_detected()
    
    # Build configuration using priority: flag > env var > default
    working_dir_raw = _get_value_with_priority(
        getattr(args, "working_dir", None),
        "WORKING_DIR",
        default=str(Path.cwd()),
        env_prefix=env_prefix,
    )
    
    # Normalize and validate working_dir (same as interactive mode)
    from midicoder.io.validators import normalize_directory_path, validate_directory_path
    
    # Validate if directory exists
    try:
        validate_directory_path(working_dir_raw)
    except ValueError as e:
        print_error(f"Invalid working directory: {e}")
        raise SystemExit(1)
    
    # Normalize to absolute path
    working_dir = normalize_directory_path(working_dir_raw)
    
    stack_value = _get_value_with_priority(
        getattr(args, "stack", None),
        "STACK",
        default=None,
        env_prefix=env_prefix,
    )
    stack = _parse_stack(stack_value)
    
    # LLM configuration
    llm_config = {
        "high": _build_llm_tier_config("high", args, env_prefix),
        "cheap": _build_llm_tier_config("cheap", args, env_prefix),
    }
    
    config = {
        "working_dir": working_dir,
        "stack": stack,
        "commands": [],
        "llm": llm_config,
        "cache": {
            "enable": True,
            "type": "ephemeral",
        },
    }
    
    # Get API keys
    llm_secrets = {
        "high": {"provider": llm_config["high"].get("provider")},
        "cheap": {"provider": llm_config["cheap"].get("provider")},
    }
    
    for tier in ["high", "cheap"]:
        key_direct = getattr(args, f"llm_{tier}_key", None)
        key_env_name = getattr(args, f"llm_{tier}_key_env", None)
        
        api_key = _get_api_key(tier, key_direct, key_env_name, env_prefix)
        if api_key:
            llm_secrets[tier]["api_key"] = api_key
    
    # Validate configuration - wrap secrets in llm key
    errors = _validate_init_payload(config, llm_secrets, env_prefix=env_prefix)
    if errors:
        print_error("Configuration validation failed:", title="Error")
        for error in errors:
            print_error(f"  • {error}")
        print_normal("")
        print_info("Use 'midicoder init --config-list' to see all required configuration keywords.")
        raise SystemExit(1)
    
    # Save configuration
    config_manager = ConfigManager(paths)
    config_manager.save(config)
    
    # Initialize and save secrets
    secrets_manager = SecretsManager(paths.secrets)
    secrets_manager.initialize_empty()
    secrets_manager.save_secrets("llm", llm_secrets)
    
    # Success summary
    print_success("Configuration initialized successfully!", title="Complete")
    print_info(f"  • Working directory: {working_dir}")
    print_info(f"  • Stack(s): {', '.join(stack)}")
    print_info(f"  • High-tier LLM: {llm_config['high']['model']} ({llm_config['high']['provider']})")
    print_info(f"  • Cheap-tier LLM: {llm_config['cheap']['model']} ({llm_config['cheap']['provider']})")


def run(root: Path, args: Any = None) -> None:
    """
    Run init command with support for both interactive and non-interactive modes.
    
    Args:
        root: Project root directory
        args: Command-line arguments (from argparse)
    """
    # Handle --config-list flag
    if args and hasattr(args, "config_list") and args.config_list:
        from midicoder.config.keywords import InitKeywords
        InitKeywords.print_help()
        return
    
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)
    state_before = read_state(paths)
    
    # Determine mode
    non_interactive = args and getattr(args, "non_interactive", False)
    
    # Set global env var if non-interactive
    if non_interactive:
        os.environ["MIDICODER_NON_INTERACTIVE"] = "true"
    
    (
        _initialize_config_non_interactive(paths, args)
        if non_interactive
        else _initialize_config_interactive(paths)
    )

    ensure_base_layout(paths)
    run_dir = create_run_dir(paths, "init")
    
    state = read_state(paths)
    write_state(paths, state)
    write_run_outputs(
        run_dir,
        "init",
        {
            "status": "initialized",
            "mode": "non-interactive" if non_interactive else "interactive"
        },
        state_before=state_before,
        state_after=state,
    )
