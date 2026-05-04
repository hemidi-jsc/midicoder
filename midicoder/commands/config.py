"""Configuration management commands."""

from __future__ import annotations

import json
from pathlib import Path

from midicoder.config import (
    ConfigManager,
    SecretsManager,
    check_config_fields,
    get_config_template,
)
from midicoder.config.defaults import CONFIG_FIELDS, SECRET_CATEGORIES
from midicoder.io import (
    print_dict,
    print_error,
    print_info,
    print_list,
    print_normal,
    print_success,
    print_warning,
    prompt_confirm,
    prompt_secret,
)

from .base import MidicoderPaths, ensure_base_layout, utc_timestamp


def get_value(root: Path, key: str) -> None:
    """
    Get configuration value by key.

    Args:
        root: Project root directory
        key: Configuration key in dot notation
    """
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    config_manager = ConfigManager(paths)
    value = config_manager.get(key)

    if value is None:
        print_error(f"Key '{key}' not found in config")
        raise SystemExit(1)

    print_info(f"{key} = {value}")


def set_value(root: Path, key: str, value: str) -> None:
    """
    Set configuration value.

    Args:
        root: Project root directory
        key: Configuration key in dot notation
        value: Value to set
    """
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    config_manager = ConfigManager(paths)

    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value

    try:
        config_manager.set(key, parsed_value)
        print_success(f"Set {key} = {parsed_value}")
    except ValueError as e:
        print_error(str(e))
        raise SystemExit(1)


def list_config(root: Path) -> None:
    """
    List all configuration.

    Args:
        root: Project root directory
    """
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    config_manager = ConfigManager(paths)
    config = config_manager.load()

    print_dict(config, title="Current Configuration")


def validate_config(root: Path) -> None:
    """
    Validate configuration (deprecated, use check_config instead).

    Args:
        root: Project root directory
    """
    print_warning("'validate_config' is deprecated, use 'check_config' instead")
    check_config(root)


def check_config(root: Path) -> None:
    """
    Check configuration for issues.

    Args:
        root: Project root directory
    """
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    config_manager = ConfigManager(paths)
    config = config_manager.load()

    issues = check_config_fields(config)

    has_issues = False

    if issues["errors"]:
        has_issues = True
        print_error("Configuration errors found", title="Validation")
        for error in issues["errors"]:
            print_normal(f"  • {error}")

    if issues["warnings"]:
        has_issues = True
        print_warning("Configuration warnings found", title="Validation")
        for warning in issues["warnings"]:
            print_normal(f"  • {warning}")

    if not has_issues:
        print_success("Configuration looks good")
    else:
        print_normal("")
        if issues["errors"]:
            raise SystemExit(1)


def list_secrets(root: Path, show_all: bool = False) -> None:
    """
    List all secret categories.

    Args:
        root: Project root directory
        show_all: If True, show all categories including empty ones
    """
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    secrets_manager = SecretsManager(paths.secrets)

    if show_all:
        # Show all defined categories
        print_info("All secret categories", title="Secrets")
        for category in SECRET_CATEGORIES:
            secrets = secrets_manager.load_secrets(category)
            status = "✓" if secrets else "○"
            print_normal(f"  {status} {category}")
            if secrets:
                _print_secrets_recursive(secrets, secrets_manager, indent=4)
    else:
        # Show only categories with data
        categories = secrets_manager.list_categories()

        if not categories:
            print_info("No secrets configured")
            print_normal(f"Available categories: {', '.join(SECRET_CATEGORIES)}")
            return

        print_info("Configured secrets", title="Secrets")
        for category in categories:
            secrets = secrets_manager.load_secrets(category)
            print_normal(f"\n{category}:")
            _print_secrets_recursive(secrets, secrets_manager, indent=2)


def _print_secrets_recursive(
    data: dict, secrets_manager: SecretsManager, indent: int = 0
) -> None:
    """Helper to print secrets recursively."""
    for key, value in data.items():
        prefix = " " * indent
        if isinstance(value, dict):
            print_normal(f"{prefix}{key}:")
            _print_secrets_recursive(value, secrets_manager, indent + 2)
        else:
            masked = secrets_manager.mask_secret(str(value)) if value else "None"
            print_normal(f"{prefix}{key}: {masked}")


def get_secret(root: Path, category: str, key: str) -> None:
    """
    Get a secret value (masked).

    Args:
        root: Project root directory
        category: Secret category
        key: Secret key
    """
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    secrets_manager = SecretsManager(paths.secrets)
    value = secrets_manager.get_secret(category, key)

    if value is None:
        print_error(f"Secret '{key}' not found in category '{category}'")
        raise SystemExit(1)

    masked = secrets_manager.mask_secret(value)
    print_info(f"{category}.{key}: {masked}")


def set_secret(root: Path, category: str, key: str) -> None:
    """
    Set a secret value interactively.

    Args:
        root: Project root directory
        category: Secret category
        key: Secret key
    """
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    secrets_manager = SecretsManager(paths.secrets)

    value = prompt_secret(f"Enter secret value for {category}.{key}", confirm=True)
    if value is None:
        print_warning("Cancelled")
        return

    secrets_manager.set_secret(category, key, value)
    print_success(f"Secret {category}.{key} set")


def delete_secrets_category(root: Path, category: str) -> None:
    """
    Delete a secrets category.

    Args:
        root: Project root directory
        category: Secret category to delete
    """
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    secrets_manager = SecretsManager(paths.secrets)

    confirm = prompt_confirm(
        f"Delete all secrets in category '{category}'? This will create a backup.",
        default=False,
    )
    if not confirm:
        print_warning("Cancelled")
        return

    secrets_manager.delete_category(category, backup=True)
    print_success(f"Category '{category}' deleted (backup created)")


def reset_config(root: Path) -> None:
    """
    Reset configuration to defaults.

    Args:
        root: Project root directory
    """
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    confirm = prompt_confirm(
        "Reset configuration to defaults? Current config will be backed up.",
        default=False,
    )
    if not confirm:
        print_warning("Cancelled")
        return

    if paths.config.exists():
        backup_path = paths.config.parent / f"config.{utc_timestamp()}.bak"
        backup_path.write_text(paths.config.read_text())
        print_info(f"Backed up to: {backup_path}")

    config_manager = ConfigManager(paths)
    config_manager.initialize_interactive()

    print_success("Configuration reset")


def show_template(root: Path | None = None) -> None:
    """
    Show configuration template.

    Args:
        root: Project root directory (optional)
    """
    template = get_config_template()

    print_dict(template, title="Configuration Template")
    print_normal("")
    print_list(CONFIG_FIELDS, title="Available Fields")
    print_list(SECRET_CATEGORIES, title="Secret Categories")


def show_fields(root: Path | None = None) -> None:
    """
    Show available configuration fields and categories.

    Args:
        root: Project root directory (optional)
    """
    print_list(CONFIG_FIELDS, title=" Configuration Fields")
    print_normal("")
    print_list(SECRET_CATEGORIES, title=" Secret Categories")
    print_normal("")
    print_info("Usage examples", title=" Help")
    print_normal("  midicoder config set <key> <value>")
    print_normal("  midicoder config get <key>")
    print_normal("  midicoder secrets set <category> <key>")
    print_normal("  midicoder secrets get <category> <key>")


def backup_secrets(root: Path) -> None:
    """
    Create a backup of the secrets file.

    Args:
        root: Project root directory
    """
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    secrets_manager = SecretsManager(paths.secrets)

    try:
        backup_path = secrets_manager.backup()
        print_success(f"Secrets backed up to: {backup_path}")
    except FileNotFoundError:
        print_error("No secrets file found to backup")
        raise SystemExit(1)


def init_secrets(root: Path) -> None:
    """
    Initialize empty secrets file with all categories.

    Args:
        root: Project root directory
    """
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)

    secrets_manager = SecretsManager(paths.secrets)

    if secrets_manager.secrets_file.exists():
        print_warning("Secrets file already exists")
        overwrite = prompt_confirm("Overwrite with empty template?", default=False)
        if not overwrite:
            print_warning("Cancelled")
            return

        # Backup first
        backup_path = secrets_manager.backup()
        print_info(f"Backed up existing secrets to: {backup_path}")

    secrets_manager.initialize_empty()
    print_success(f"Secrets file initialized: {secrets_manager.secrets_file}")
    print_normal(f"Categories: {', '.join(SECRET_CATEGORIES)}")
