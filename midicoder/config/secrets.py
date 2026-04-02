"""Secrets management."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .defaults import SECRET_CATEGORIES, SECRETS_FILE_NAME


class SecretsManager:
    """Manager for secret values stored in a single secrets file."""

    def __init__(self, secrets_dir: Path):
        """
        Initialize SecretsManager.

        Args:
            secrets_dir: Directory to store secrets file
        """
        self.secrets_dir = secrets_dir
        self.secrets_file = secrets_dir / SECRETS_FILE_NAME

    def _load_all_secrets(self) -> dict:
        """
        Load all secrets from the secrets file.

        Returns:
            Dictionary with all secret categories
        """
        if not self.secrets_file.exists():
            return {}

        try:
            data = json.loads(self.secrets_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {}
            return data
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_all_secrets(self, secrets: dict) -> None:
        """
        Save all secrets to the secrets file atomically.

        Args:
            secrets: Dictionary with all secret categories
        """
        self.secrets_dir.mkdir(parents=True, exist_ok=True)

        # Write atomically using temp file
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=self.secrets_dir,
            delete=False,
            encoding="utf-8",
            suffix=".tmp",
        ) as tmp:
            json.dump(secrets, tmp, indent=2, sort_keys=True)
            tmp_path = Path(tmp.name)

        # Replace the original file
        tmp_path.replace(self.secrets_file)

        # Set restrictive permissions on Unix-like systems
        if hasattr(os, "chmod"):
            try:
                os.chmod(self.secrets_file, 0o600)
            except OSError:
                pass

    def load_secrets(self, category: str) -> dict:
        """
        Load secrets from a specific category.

        Args:
            category: Secret category name (e.g., "llm", "database")

        Returns:
            Dictionary of secrets for the category, empty dict if not found

        Examples:
            >>> manager = SecretsManager(Path(".midicoder/secrets"))
            >>> llm_secrets = manager.load_secrets("llm")
        """
        all_secrets = self._load_all_secrets()
        return all_secrets.get(category, {})

    def save_secrets(self, category: str, secrets: dict) -> None:
        """
        Save secrets for a specific category.

        Args:
            category: Secret category name
            secrets: Dictionary of secrets to save

        Examples:
            >>> manager = SecretsManager(Path(".midicoder/secrets"))
            >>> manager.save_secrets("llm", {"high": {"api_key": "sk-123"}})
        """
        all_secrets = self._load_all_secrets()
        all_secrets[category] = secrets
        self._save_all_secrets(all_secrets)

    def get_secret(self, category: str, key: str) -> str | None:
        """
        Get a single secret value.

        Args:
            category: Secret category name
            key: Secret key (supports dot notation for nested keys)

        Returns:
            Secret value or None if not found

        Examples:
            >>> manager = SecretsManager(Path(".midicoder/secrets"))
            >>> api_key = manager.get_secret("llm", "high.api_key")
        """
        category_secrets = self.load_secrets(category)

        if not key:
            return None

        keys = key.split(".")
        current = category_secrets

        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return None
            current = current[k]

        return str(current) if current is not None else None

    def set_secret(self, category: str, key: str, value: str) -> None:
        """
        Set a single secret value.

        Args:
            category: Secret category name
            key: Secret key (supports dot notation for nested keys)
            value: Secret value to set

        Examples:
            >>> manager = SecretsManager(Path(".midicoder/secrets"))
            >>> manager.set_secret("llm", "high.api_key", "sk-123")
        """
        all_secrets = self._load_all_secrets()

        if category not in all_secrets:
            all_secrets[category] = {}

        category_secrets = all_secrets[category]

        keys = key.split(".")
        current = category_secrets

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

        self._save_all_secrets(all_secrets)

    def list_categories(self) -> list[str]:
        """
        List all secret categories that have data.

        Returns:
            Sorted list of category names

        Examples:
            >>> manager = SecretsManager(Path(".midicoder/secrets"))
            >>> categories = manager.list_categories()
            >>> print(categories)
            ['database', 'llm']
        """
        all_secrets = self._load_all_secrets()
        return sorted(all_secrets.keys())

    def mask_secret(self, secret: str, show_chars: int = 4) -> str:
        """
        Mask a secret value for display.

        Args:
            secret: Secret value to mask
            show_chars: Number of characters to show at start and end

        Returns:
            Masked secret string

        Examples:
            >>> manager = SecretsManager(Path(".midicoder/secrets"))
            >>> manager.mask_secret("sk-1234567890abcdef")
            'sk-1...cdef'
            >>> manager.mask_secret("short")
            '****'
        """
        if not secret or len(secret) <= show_chars * 2:
            return "****"

        start = secret[:show_chars]
        end = secret[-show_chars:]
        return f"{start}...{end}"

    def delete_category(self, category: str, backup: bool = True) -> None:
        """
        Delete a secret category from the secrets file.

        Args:
            category: Category name to delete
            backup: If True, create backup before deleting

        Examples:
            >>> manager = SecretsManager(Path(".midicoder/secrets"))
            >>> manager.delete_category("old_category")
        """
        all_secrets = self._load_all_secrets()

        if category not in all_secrets:
            return

        if backup and self.secrets_file.exists():
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_file = self.secrets_dir / f"secrets.{timestamp}.bak"
            backup_file.write_bytes(self.secrets_file.read_bytes())

        del all_secrets[category]
        self._save_all_secrets(all_secrets)

    def initialize_empty(self) -> None:
        """
        Initialize an empty secrets file with all categories.

        Creates the secrets file with empty dictionaries for all
        categories defined in SECRET_CATEGORIES.

        Examples:
            >>> manager = SecretsManager(Path(".midicoder/secrets"))
            >>> manager.initialize_empty()
        """
        if self.secrets_file.exists():
            return

        initial_secrets = {category: {} for category in SECRET_CATEGORIES}
        self._save_all_secrets(initial_secrets)

    def backup(self, suffix: str | None = None) -> Path:
        """
        Create a backup of the secrets file.

        Args:
            suffix: Optional suffix for backup filename, defaults to timestamp

        Returns:
            Path to the backup file

        Examples:
            >>> manager = SecretsManager(Path(".midicoder/secrets"))
            >>> backup_path = manager.backup()
        """
        if not self.secrets_file.exists():
            raise FileNotFoundError("Secrets file does not exist")

        if suffix is None:
            suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        backup_file = self.secrets_dir / f"secrets.{suffix}.bak"
        backup_file.write_bytes(self.secrets_file.read_bytes())

        return backup_file
