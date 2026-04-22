"""
Configuration Management cho Midicoder Pipeline.

Module này quản lý cấu hình global và project:
- Global config: ~/.midicoder/midicoder.json
- Project config: .midicoder/config/midicoder.yml

E00: Installation & Setup
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

import yaml


# Đường dẫn cấu hình global
GLOBAL_CONFIG_DIR = Path.home() / ".midicoder"
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "midicoder.json"

# Đường dẫn cấu hình project
PROJECT_CONFIG_DIR = Path(".midicoder")
PROJECT_CONFIG_FILE = PROJECT_CONFIG_DIR / "config" / "midicoder.yml"


# Cấu hình mặc định global
DEFAULT_GLOBAL_CONFIG = {
    "midicoder_version": "1.0.0",
    "created_at": None,  # Will be set on first init
    "last_run": None,
    "cli": {
        "theme": "default",
        "language": "vi",
        "output_format": "human",
    },
    "llm": {
        "provider": "openai-compatible",
        "model": "qwen3.5-27B",
        "api_url": "http://localhost:11434/v1",
        "api_key": None,
        "max_tokens": 8192,
        "temperature": 0.3,
        "timeout_seconds": 300,
        "retry_attempts": 3,
        "cache_enabled": True,
    },
    "mcp": {
        "host": "localhost",
        "port": 2026,
    },
    "neo4j": {
        "host": "localhost",
        "port": 7687,
        "username": "neo4j",
        "password": "password",
        "docker_auto_start": True,
    },
    "webgui": {
        "host": "localhost",
        "port": 6868,
        "frontend_port": 7272,
        "auto_start": True,
        "open_browser": True,
    },
    "project": {
        "cwd": str(Path.cwd()),
        "last_opened": None,
    },
    "version": {
        "max_versions": 5,
    },
}

# Cấu hình mặc định project
DEFAULT_PROJECT_CONFIG = {
    "version": "1.0.0",
    "created_at": None,
    "active_version": "v1.0.0",
    "capabilities": {
        "enabled": [],
        "domain_packs": [],
        "regulatory_overlays": [],
    },
}


class ConfigError(Exception):
    """Lỗi khi đọc/ghi cấu hình."""

    pass


class ConfigManager:
    """
    Manager cho cấu hình Midicoder.

    Hỗ trợ:
    - Đọc/ghi global config
    - Đọc/ghi project config
    - Set/get cấu hình động
    """

    def __init__(self) -> None:
        """Khởi tạo config manager."""
        self._global_config: dict = {}
        self._project_config: dict = {}
        self._global_loaded = False
        self._project_loaded = False

    def load_global_config(self) -> dict:
        """
        Tải global config từ ~/.midicoder/midicoder.json.

        Returns:
            Global config dictionary

        Raises:
            ConfigError: Nếu không thể đọc file
        """
        if self._global_loaded:
            return self._global_config

        if not GLOBAL_CONFIG_FILE.exists():
            # Tạo config mới với defaults
            self._global_config = DEFAULT_GLOBAL_CONFIG.copy()
            self._global_config["created_at"] = self._get_timestamp()
            self.save_global_config()
        else:
            try:
                with open(GLOBAL_CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._global_config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                raise ConfigError(f"Không thể đọc global config: {e}")

        self._global_loaded = True
        return self._global_config

    def save_global_config(self) -> None:
        """
        Lưu global config vào ~/.midicoder/midicoder.json.

        Raises:
            ConfigError: Nếu không thể ghi file
        """
        try:
            GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(GLOBAL_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._global_config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise ConfigError(f"Không thể lưu global config: {e}")

    def load_project_config(self) -> dict:
        """
        Tải project config từ .midicoder/config/midicoder.yml.

        Returns:
            Project config dictionary

        Raises:
            ConfigError: Nếu không thể đọc file
        """
        if self._project_loaded:
            return self._project_config

        if not PROJECT_CONFIG_FILE.exists():
            self._project_config = DEFAULT_PROJECT_CONFIG.copy()
            self.save_project_config()
        else:
            try:
                with open(PROJECT_CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._project_config = yaml.safe_load(f) or {}
            except (yaml.YAMLError, IOError) as e:
                raise ConfigError(f"Không thể đọc project config: {e}")

        self._project_loaded = True
        return self._project_config

    def save_project_config(self) -> None:
        """
        Lưu project config vào .midicoder/config/midicoder.yml.

        Raises:
            ConfigError: Nếu không thể ghi file
        """
        try:
            PROJECT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(PROJECT_CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.dump(self._project_config, f, default_flow_style=False, allow_unicode=True)
        except IOError as e:
            raise ConfigError(f"Không thể lưu project config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Lấy giá trị config theo key (dot notation).

        Args:
            key: Key theo dot notation (vd: 'llm.model')
            default: Giá trị mặc định nếu key không tồn tại

        Returns:
            Giá trị config
        """
        # Ưu tiên project config, nếu không có thì global
        project = self.load_project_config()
        global_conf = self.load_global_config()

        # Parse key
        keys = key.split(".")
        value = self._get_nested(project, keys)
        if value is not None:
            return value

        value = self._get_nested(global_conf, keys)
        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """
        Set giá trị config theo key.

        Args:
            key: Key theo dot notation
            value: Giá trị mới
        """
        keys = key.split(".")

        # Xác định config nào cần set (project hoặc global)
        if keys[0] in ["version", "capabilities"]:
            config = self._project_config
            save_func = self.save_project_config
        else:
            config = self._global_config
            save_func = self.save_global_config

        self._set_nested(config, keys, value)
        save_func()

    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset config về mặc định.

        Args:
            key: Key cụ thể để reset, hoặc None để reset toàn bộ
        """
        if key is None:
            self._global_config = DEFAULT_GLOBAL_CONFIG.copy()
            self._project_config = DEFAULT_PROJECT_CONFIG.copy()
            self.save_global_config()
            self.save_project_config()
        else:
            keys = key.split(".")
            if keys[0] in ["version", "capabilities"]:
                self._reset_nested(self._project_config, keys)
                self.save_project_config()
            else:
                self._reset_nested(self._global_config, keys)
                self.save_global_config()

    def _get_nested(self, data: dict, keys: list) -> Any:
        """Lấy giá trị nested từ dict."""
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            else:
                return None
            if data is None:
                return None
        return data

    def _set_nested(self, data: dict, keys: list, value: Any) -> None:
        """Set giá trị nested trong dict."""
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]
        data[keys[-1]] = value

    def _reset_nested(self, data: dict, keys: list) -> None:
        """Reset giá trị nested về default."""
        # Tìm default value
        default = self._get_nested(DEFAULT_GLOBAL_CONFIG, keys)
        if default is None:
            default = self._get_nested(DEFAULT_PROJECT_CONFIG, keys)

        if default is not None:
            self._set_nested(data, keys, default)

    def _get_timestamp(self) -> str:
        """Trả về timestamp hiện tại."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """
    Lấy global config manager instance.

    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_global_config_path() -> Path:
    """
    Trả về đường dẫn global config file.

    Returns:
        Path đến ~/.midicoder/midicoder.json
    """
    return GLOBAL_CONFIG_FILE


def get_project_config_path() -> Path:
    """
    Trả về đường dẫn project config file.

    Returns:
        Path đến .midicoder/config/midicoder.yml
    """
    return PROJECT_CONFIG_FILE