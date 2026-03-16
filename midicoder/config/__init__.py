"""Configuration management for Midicoder CLI."""

from .manager import ConfigManager
from .schema import (
    apply_defaults,
    check_config_fields,
    get_config_template,
    is_secret_field,
    validate_config_dict,
)
from .secrets import SecretsManager

__all__ = [
    "ConfigManager",
    "SecretsManager",
    "validate_config_dict",
    "check_config_fields",
    "get_config_template",
    "apply_defaults",
    "is_secret_field",
]
