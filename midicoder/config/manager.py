"""Configuration manager."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Callable

from .schema import apply_defaults, validate_config_dict
from .secrets import SecretsManager


def _normalize_optional_text(value: str | None) -> str | None:
    """Normalize prompt text into optional config value."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def _prompt_provider_common_fields(
    *,
    tier_label: str,
    provider: str,
    default_base_url: str | None,
):
    """Prompt common fields shared by all providers."""
    from midicoder.io import prompt_secret
    from midicoder.io.messages import print_info

    if provider in {"anthropic", "openai"}:
        # Use default provider URL without asking user to type it.
        llm_url = _normalize_optional_text(default_base_url)
        if llm_url:
            print_info(f"{tier_label} tier provider '{provider}' uses default base URL: {llm_url}")
    elif provider == "openai_compatible":
        from midicoder.io import prompt_text
        llm_url = _normalize_optional_text(prompt_text("Base URL", default=default_base_url or ""))
    else:
        llm_url = None
        print_info(
            f"{tier_label} tier provider '{provider}' uses provider-specific connection settings."
        )

    llm_key = prompt_secret("API key", confirm=False)
    return llm_url, _normalize_optional_text(llm_key)


def _prompt_provider_specific_fields(
    *,
    provider: str,
    tier_label: str,
    defaults: dict[str, str | None] | None = None,
) -> dict[str, str | None]:
    """Prompt provider-specific fields and return full namespaced dict."""
    from midicoder.io import prompt_text
    from midicoder.io.messages import print_info

    defaults = defaults or {}
    fields = {
        "aws_region_name": None,
        "aws_bedrock_region": None,
        "azure_openai_endpoint": None,
        "azure_openai_api_version": None,
        "azure_openai_deployment": None,
        "vertex_project": None,
        "vertex_location": None,
    }

    if provider in {"bedrock", "aws_bedrock"}:
        print_info(f"{tier_label} tier requires AWS region.")
        aws_region = _normalize_optional_text(
            prompt_text(
                "AWS region name",
                default=defaults.get("aws_region_name") or defaults.get("aws_bedrock_region") or "us-east-1",
            )
        )
        fields["aws_region_name"] = aws_region
        fields["aws_bedrock_region"] = aws_region
    elif provider in {"azure", "azure_openai"}:
        print_info(f"{tier_label} tier requires Azure OpenAI endpoint/api-version/deployment.")
        fields["azure_openai_endpoint"] = _normalize_optional_text(
            prompt_text(
                "Azure OpenAI endpoint",
                default=defaults.get("azure_openai_endpoint") or "",
            )
        )
        fields["azure_openai_api_version"] = _normalize_optional_text(
            prompt_text(
                "Azure OpenAI API version",
                default=defaults.get("azure_openai_api_version") or "2024-10-21",
            )
        )
        fields["azure_openai_deployment"] = _normalize_optional_text(
            prompt_text(
                "Azure OpenAI deployment name",
                default=defaults.get("azure_openai_deployment") or "",
            )
        )
    elif provider == "vertex_partner":
        print_info(f"{tier_label} tier requires Vertex project/location.")
        vertex_project = _normalize_optional_text(
            prompt_text(
                "Vertex project id",
                default=defaults.get("vertex_project") or "",
            )
        )
        vertex_location = _normalize_optional_text(
            prompt_text(
                "Vertex location",
                default=defaults.get("vertex_location") or "us-central1",
            )
        )
        fields["vertex_project"] = vertex_project
        fields["vertex_location"] = vertex_location

    return fields


class ConfigManager:
    """Manager for configuration files."""

    def __init__(self, paths):
        """
        Initialize ConfigManager.
        
        Args:
            paths: MidicoderPaths instance
        """
        self.paths = paths

    def load(self) -> dict:
        """
        Load configuration from file.
        
        Returns:
            Configuration dictionary with defaults applied
        
        Examples:
            >>> manager = ConfigManager(paths)
            >>> config = manager.load()
        """
        if not self.paths.config.exists():
            return apply_defaults({})
        
        try:
            config = json.loads(self.paths.config.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return apply_defaults({})
        
        return apply_defaults(config)

    def save(self, config: dict) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary to save
        
        Raises:
            ValueError: If configuration is invalid
        
        Examples:
            >>> manager = ConfigManager(paths)
            >>> manager.save({"stack": "fastapi", "llm": {}})
        """
        errors = validate_config_dict(config)
        if errors:
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")
        
        self.paths.config.parent.mkdir(parents=True, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=self.paths.config.parent,
            delete=False,
            encoding='utf-8'
        ) as tmp:
            json.dump(config, tmp, indent=2, sort_keys=True)
            tmp_path = Path(tmp.name)
        
        tmp_path.replace(self.paths.config)

    def get(self, key: str, default=None) -> Any:
        """
        Get configuration value by dot notation key.
        
        Args:
            key: Dot notation key (e.g., "llm.high.model")
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        
        Examples:
            >>> manager = ConfigManager(paths)
            >>> model = manager.get("llm.high.model")
        """
        config = self.load()
        
        keys = key.split(".")
        current = config
        
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return default
            current = current[k]
        
        return current

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by dot notation key.
        
        Args:
            key: Dot notation key (e.g., "llm.high.model")
            value: Value to set
        
        Examples:
            >>> manager = ConfigManager(paths)
            >>> manager.set("llm.high.model", "claude-sonnet-4")
            >>> manager.save(manager.load())
        """
        config = self.load()
        
        keys = key.split(".")
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        self.save(config)

    def update(self, updates: dict) -> None:
        """
        Update configuration with multiple values.
        
        Args:
            updates: Dictionary of updates to merge
        
        Examples:
            >>> manager = ConfigManager(paths)
            >>> manager.update({"stack": "nest", "commands": []})
        """
        config = self.load()
        _deep_merge(config, updates)
        self.save(config)

    def validate(self) -> list[str]:
        """
        Validate current configuration.
        
        Returns:
            List of error messages, empty if valid
        
        Examples:
            >>> manager = ConfigManager(paths)
            >>> errors = manager.validate()
            >>> if errors:
            ...     print("Errors:", errors)
        """
        config = self.load()
        return validate_config_dict(config)

    def get_merged_with_secrets(self) -> dict:
        """
        Load configuration merged with secrets.
        
        Returns:
            Configuration dictionary with secrets merged in
        
        Examples:
            >>> manager = ConfigManager(paths)
            >>> config = manager.get_merged_with_secrets()
        """
        config = self.load()
        secrets_manager = SecretsManager(self.paths.secrets)
        
        for category in secrets_manager.list_categories():
            secrets = secrets_manager.load_secrets(category)
            if category in config:
                _deep_merge(config[category], secrets)
            else:
                config[category] = secrets
        
        return config

    def migrate_secrets_from_config(self) -> bool:
        """
        Migrate secrets from config to the secrets file.
        
        Returns:
            True if migration occurred, False otherwise
        
        Examples:
            >>> manager = ConfigManager(paths)
            >>> if manager.migrate_secrets_from_config():
            ...     print("Secrets migrated")
        """
        if not self.paths.config.exists():
            return False
        
        raw_config = json.loads(self.paths.config.read_text(encoding="utf-8"))
        secrets_manager = SecretsManager(self.paths.secrets)
        
        migrated = False
        llm_secrets = {}
        
        # Check for API keys in llm config
        if "llm" in raw_config:
            for tier in ["high", "cheap"]:
                if tier in raw_config["llm"] and "api_key" in raw_config["llm"][tier]:
                    api_key_value = raw_config["llm"][tier]["api_key"]
                    if api_key_value is not None:
                        if tier not in llm_secrets:
                            llm_secrets[tier] = {}
                        llm_secrets[tier]["api_key"] = api_key_value
                        del raw_config["llm"][tier]["api_key"]
                        migrated = True
        
        if migrated:
            # Initialize secrets file if needed
            if not secrets_manager.secrets_file.exists():
                secrets_manager.initialize_empty()
            
            # Save migrated LLM secrets
            secrets_manager.save_secrets("llm", llm_secrets)
            
            # Save updated config
            self.paths.config.write_text(
                json.dumps(raw_config, indent=2, sort_keys=True),
                encoding="utf-8"
            )
        
        return migrated

    def initialize_interactive(
        self,
        validate_fn: Callable[[dict, dict], list[str]] | None = None,
    ) -> None:
        """
        Interactive initialization wizard.
        
        Examples:
            >>> manager = ConfigManager(paths)
            >>> manager.initialize_interactive()
        """
        from midicoder.io import prompt_text, prompt_choice, prompt_multichoice
        from midicoder.io.messages import print_info, print_success, print_normal
        from midicoder.io.validators import validate_directory_path, normalize_directory_path
        from midicoder.config.defaults import (
            DEFAULT_STACK,
            SUPPORTED_STACKS,
            LLM_PROVIDERS,
            PROVIDER_BASE_URLS,
            PROVIDER_DEFAULT_MODELS,
        )
        import os
        
        print_info("Initializing Midicoder configuration...", title="Setup Wizard")
        
        # Working directory configuration
        print_normal("\n" + "="*60)
        print_normal("[bold]Working Directory Configuration[/bold]")
        print_normal("="*60)
        print_normal("Enter the working directory for your project.")
        print_normal("You can use:")
        print_normal("  • Absolute path: /path/to/project or C:\\path\\to\\project")
        print_normal("  • Relative path: ./project or ../other-project")
        print_normal("  • Home directory: ~/projects/myapp")
        
        default_working_dir = os.getcwd()
        working_dir_input = prompt_text(
            "\nWorking directory path",
            default=default_working_dir,
            validator=validate_directory_path
        )
        
        # Normalize the path to absolute path
        working_dir = normalize_directory_path(working_dir_input or default_working_dir)
        print_success(f"Working directory set to: {working_dir}")
        
        # Select tech stacks (multiple)
        print_normal("\n" + "="*60)
        print_normal("[bold]Tech Stack Selection[/bold]")
        print_normal("="*60)
        
        target_stacks = prompt_multichoice(
            "Select target tech stack(s)",
            choices=SUPPORTED_STACKS,
            defaults=DEFAULT_STACK
        )
        
        # High-level LLM configuration
        print_normal("\n" + "="*60)
        print_normal("[bold]High-level LLM Configuration[/bold] (for complex tasks)")
        print_normal("="*60)
        
        llm_high_provider = prompt_choice(
            "Select LLM provider",
            choices=LLM_PROVIDERS,
            default=LLM_PROVIDERS[0]
        )
        
        default_high_url = PROVIDER_BASE_URLS.get(llm_high_provider)
        llm_high_url, llm_high_key = _prompt_provider_common_fields(
            tier_label="High",
            provider=llm_high_provider,
            default_base_url=default_high_url,
        )
        high_provider_specific = _prompt_provider_specific_fields(
            provider=llm_high_provider,
            tier_label="High",
        )
        
        default_high_model = PROVIDER_DEFAULT_MODELS.get(llm_high_provider, {}).get("high", "")
        print_info(f"Recommended model: {default_high_model}")
        llm_high_model = prompt_text(
            "Model name",
            default=default_high_model
        )
        
        # Cheap LLM configuration
        print_normal("\n" + "="*60)
        print_normal("[bold]Cheap LLM Configuration[/bold] (for simple tasks)")
        print_normal("="*60)
        
        llm_cheap_provider = prompt_choice(
            "Select LLM provider",
            choices=LLM_PROVIDERS,
            default=llm_high_provider
        )
        
        # If same provider as high, use high's values as defaults
        same_provider = (llm_cheap_provider == llm_high_provider)
        
        default_cheap_url: str | None = None
        if same_provider:
            default_cheap_url = llm_high_url or PROVIDER_BASE_URLS.get(llm_cheap_provider)
            if llm_cheap_provider in {"anthropic", "openai", "openai_compatible"}:
                print_info(
                    f"Using same provider as high-level. Base URL defaults to: {default_cheap_url}"
                )
        else:
            default_cheap_url = PROVIDER_BASE_URLS.get(llm_cheap_provider)

        llm_cheap_url, llm_cheap_key = _prompt_provider_common_fields(
            tier_label="Cheap",
            provider=llm_cheap_provider,
            default_base_url=default_cheap_url,
        )

        cheap_defaults = high_provider_specific if same_provider else None
        cheap_provider_specific = _prompt_provider_specific_fields(
            provider=llm_cheap_provider,
            tier_label="Cheap",
            defaults=cheap_defaults,
        )

        if same_provider:
            print_info("Using same provider. You can reuse the same API key or enter a different one.")

        # If no key provided and same provider, reuse high key
        if not llm_cheap_key and same_provider:
            llm_cheap_key = llm_high_key
            if llm_cheap_key:
                print_info("Using same API key as high-level configuration")

        # If same provider and provider-specific fields left blank, reuse from high tier.
        if same_provider:
            for field_name, field_value in cheap_provider_specific.items():
                if field_value is None and high_provider_specific.get(field_name):
                    cheap_provider_specific[field_name] = high_provider_specific[field_name]
        
        default_cheap_model = PROVIDER_DEFAULT_MODELS.get(llm_cheap_provider, {}).get("cheap", "")
        print_info(f"Recommended model: {default_cheap_model}")
        llm_cheap_model = prompt_text(
            "Model name",
            default=default_cheap_model
        )
        
        # Save configuration
        config = {
            "working_dir": working_dir,
            "stack": target_stacks,
            "commands": [],
            "llm": {
                "high": {
                    "model": llm_high_model or None,
                    "base_url": llm_high_url,
                    "provider": llm_high_provider or None,
                    **high_provider_specific,
                },
                "cheap": {
                    "model": llm_cheap_model or None,
                    "base_url": llm_cheap_url,
                    "provider": llm_cheap_provider or None,
                    **cheap_provider_specific,
                },
            },
            "cache": {
                "enable": True,
                "type": "ephemeral",
            },
        }

        llm_secrets = {
            "high": {
                "provider": llm_high_provider or None,
                "api_key": llm_high_key or None,
            },
            "cheap": {
                "provider": llm_cheap_provider or None,
                "api_key": llm_cheap_key or None,
            },
        }

        if validate_fn:
            errors = validate_fn(config, llm_secrets)
            if errors:
                raise ValueError("\n".join(errors))
        
        self.save(config)
        
        # Initialize and save secrets
        secrets_manager = SecretsManager(self.paths.secrets)
        secrets_manager.initialize_empty()  # Initialize with all categories
        
        secrets_manager.save_secrets("llm", llm_secrets)
        
        # Success summary
        print_success("Configuration initialized successfully!", title="Setup Complete")
        
        print_normal("\n[bold]Configuration Summary:[/bold]")
        print_normal(f"  • Working directory: [cyan]{working_dir}[/cyan]")
        print_normal(f"  • Selected stacks: [cyan]{', '.join(target_stacks)}[/cyan]")
        print_normal(f"  • High-level LLM: [cyan]{llm_high_model}[/cyan] ([dim]{llm_high_provider}[/dim])")
        print_normal(f"  • Cheap LLM: [cyan]{llm_cheap_model}[/cyan] ([dim]{llm_cheap_provider}[/dim])")
        print_normal(f"  • Cache: [cyan]enabled[/cyan] ([dim]ephemeral[/dim])")


def _deep_merge(target: dict, source: dict) -> None:
    """Deep merge source dict into target dict."""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
