"""Initialize the .midicoder workspace and basic config."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from midicoder.config import ConfigManager
from midicoder.config.defaults import DEFAULT_STACK, SUPPORTED_STACKS
from midicoder.io import print_info, print_warning, prompt_confirm

from .base import (
    MidicoderPaths,
    create_run_dir,
    ensure_base_layout,
    read_state,
    write_run_outputs,
    write_state,
)


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
            print_warning(
                f"Environment variable {key_env_name} not found for {tier} tier"
            )

    # Priority 3: Key directly from MIDICODER_LLM_X_API_KEY env var
    default_env_var = f"{env_prefix}LLM_{tier.upper()}_API_KEY"
    api_key = os.getenv(default_env_var)
    if api_key:
        print_info(f"✓ Using API key for {tier} tier from env var: {default_env_var}")
        return api_key

    return None


def _validate_required_config(config: dict, secrets: dict) -> list[str]:
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
    from midicoder.config.defaults import LLM_PROVIDERS

    for tier in ["high", "cheap"]:
        tier_config = config.get("llm", {}).get(tier, {})

        provider = tier_config.get("provider")
        if not provider:
            errors.append(f"LLM {tier} tier provider is required")
        elif provider not in LLM_PROVIDERS:
            errors.append(
                f"Unsupported LLM provider for {tier} tier: '{provider}'. "
                f"Supported providers: {', '.join(LLM_PROVIDERS)}"
            )

        if not tier_config.get("model"):
            errors.append(f"LLM {tier} tier model is required")

        if not tier_config.get("base_url"):
            errors.append(f"LLM {tier} tier base URL is required")

        # Check API key in secrets
        tier_secrets = secrets.get("llm", {}).get(tier, {})
        if not tier_secrets.get("api_key"):
            errors.append(
                f"LLM {tier} tier API key is required. "
                f"Set via --llm-{tier}-key-env flag or MIDICODER_LLM_{tier.upper()}_API_KEY env var."
            )

    return errors


def _initialize_config_interactive(paths: MidicoderPaths) -> None:
    """Interactive initialization (existing behavior)."""
    if paths.config.exists():
        overwrite = prompt_confirm("Config already exists. Overwrite?", default=False)
        if not overwrite:
            print("Keeping existing config.")
            return

    config_manager = ConfigManager(paths)
    config_manager.initialize_interactive()


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
    from midicoder.io import print_error, print_normal, print_success

    print_info("Initializing configuration (non-interactive mode)...", title="Init")

    env_prefix = getattr(args, "env_prefix", "MIDICODER_")

    # Build configuration using priority: flag > env var > default
    working_dir_raw = _get_value_with_priority(
        getattr(args, "working_dir", None),
        "WORKING_DIR",
        default=str(Path.cwd()),
        env_prefix=env_prefix,
    )

    # Normalize and validate working_dir (same as interactive mode)
    from midicoder.io.validators import (
        normalize_directory_path,
        validate_directory_path,
    )

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
        "high": {
            "provider": _get_value_with_priority(
                getattr(args, "llm_high_provider", None),
                "LLM_HIGH_PROVIDER",
                env_prefix=env_prefix,
            ),
            "model": _get_value_with_priority(
                getattr(args, "llm_high_model", None),
                "LLM_HIGH_MODEL",
                env_prefix=env_prefix,
            ),
            "base_url": _get_value_with_priority(
                getattr(args, "llm_high_url", None),
                "LLM_HIGH_URL",
                env_prefix=env_prefix,
            ),
        },
        "cheap": {
            "provider": _get_value_with_priority(
                getattr(args, "llm_cheap_provider", None),
                "LLM_CHEAP_PROVIDER",
                env_prefix=env_prefix,
            ),
            "model": _get_value_with_priority(
                getattr(args, "llm_cheap_model", None),
                "LLM_CHEAP_MODEL",
                env_prefix=env_prefix,
            ),
            "base_url": _get_value_with_priority(
                getattr(args, "llm_cheap_url", None),
                "LLM_CHEAP_URL",
                env_prefix=env_prefix,
            ),
        },
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
        "high": {},
        "cheap": {},
    }

    for tier in ["high", "cheap"]:
        key_direct = getattr(args, f"llm_{tier}_key", None)
        key_env_name = getattr(args, f"llm_{tier}_key_env", None)

        api_key = _get_api_key(tier, key_direct, key_env_name, env_prefix)
        if api_key:
            llm_secrets[tier]["api_key"] = api_key

    # Validate configuration - wrap secrets in llm key
    errors = _validate_required_config(config, {"llm": llm_secrets})
    if errors:
        print_error("Configuration validation failed:", title="Error")
        for error in errors:
            print_error(f"  • {error}")
        print_normal("")
        print_info(
            "Use 'midicoder init --config-list' to see all required configuration keywords."
        )
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
    print_info(
        f"  • High-tier LLM: {llm_config['high']['model']} ({llm_config['high']['provider']})"
    )
    print_info(
        f"  • Cheap-tier LLM: {llm_config['cheap']['model']} ({llm_config['cheap']['provider']})"
    )


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
    run_dir = create_run_dir(paths, "init")

    state_before = read_state(paths)

    # Determine mode
    non_interactive = args and getattr(args, "non_interactive", False)

    # Set global env var if non-interactive
    if non_interactive:
        os.environ["MIDICODER_NON_INTERACTIVE"] = "true"

    if non_interactive:
        _initialize_config_non_interactive(paths, args)
    else:
        _initialize_config_interactive(paths)

    state = read_state(paths)
    write_state(paths, state)
    write_run_outputs(
        run_dir,
        "init",
        {
            "status": "initialized",
            "mode": "non-interactive" if non_interactive else "interactive",
        },
        state_before=state_before,
        state_after=state,
    )
