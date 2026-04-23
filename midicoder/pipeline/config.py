"""
Configuration Management cho Midicoder Pipeline.

Module này quản lý cấu hình global và project:
- Global config: ~/.midicoder/midicoder.json
- Project config: .midicoder/config/midicoder.yml

Sử dụng:
    from midicoder.pipeline.config import get_config

    # Lấy config manager
    config = get_config()
    
    # Lấy giá trị config
    llm_model = config.get("llm.model", "default-model")
    
    # Set giá trị config
    config.set("llm.temperature", 0.7)
    
    # Reset config về mặc định
    config.reset()  # Reset toàn bộ
    config.reset("cli.theme")  # Reset key cụ thể

E00: Installation & Setup
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

# Đường dẫn cấu hình global
GLOBAL_CONFIG_DIR = Path.home() / ".midicoder"
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "midicoder.json"

# Đường dẫn cấu hình project
PROJECT_CONFIG_DIR = Path(".midicoder")
PROJECT_CONFIG_FILE = PROJECT_CONFIG_DIR / "config" / "midicoder.yml"

# Cấu hình mặc định global theo SoT
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
    "max_versions": 5,
}

# Cấu hình mặc định project theo SoT
DEFAULT_PROJECT_CONFIG = {
    "midicoder_version": "1.0.0",
    "created_at": None,
    "active_version": "v1.0.0",
    "max_versions": 5,
    "capabilities": {
        "enabled": [],
        "domain_packs": [],
        "regulatory_overlays": [],
    },
}


class ConfigManager:
    """
    Manager cho cấu hình Midicoder.

    Hỗ trợ:
    - Đọc/ghi global config (JSON)
    - Đọc/ghi project config (YAML)
    - Set/get cấu hình động với dot notation
    - Reset về mặc định

    Attributes:
        _global_config: Dictionary chứa global config
        _project_config: Dictionary chứa project config
        _global_loaded: Flag đánh dấu global config đã load chưa
        _project_loaded: Flag đánh dấu project config đã load chưa

    Ví dụ:
        >>> config = ConfigManager()
        >>> config.load_global_config()
        >>> llm_model = config.get("llm.model")
        >>> config.set("llm.temperature", 0.7)
    """

    def __init__(self) -> None:
        """Khởi tạo config manager với state rỗng."""
        self._global_config: dict = {}
        self._project_config: dict = {}
        self._global_loaded = False
        self._project_loaded = False

    def load_global_config(self) -> dict:
        """
        Tải global config từ ~/.midicoder/midicoder.json.

        Nếu file không tồn tại, tự động tạo với default values.
        Cache kết quả để tránh load nhiều lần.

        Returns:
            dict: Global config dictionary

        Raises:
            MidicoderError: Nếu không thể đọc file hoặc format không đúng
                - CONFIG_READ_FAILED: Lỗi IO khi đọc file
                - CONFIG_FORMAT_INVALID: JSON không hợp lệ
        """
        if self._global_loaded:
            return self._global_config

        if not GLOBAL_CONFIG_FILE.exists():
            # Tạo config mới với defaults
            self._global_config = self._deep_copy(DEFAULT_GLOBAL_CONFIG)
            self._global_config["created_at"] = self._get_timestamp()
            self.save_global_config()
        else:
            try:
                with open(GLOBAL_CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._global_config = json.load(f)
            except IOError as e:
                # Lỗi IO: không thể đọc file
                EM.raise_error(
                    ErrorCode.CONFIG_READ_FAILED,
                    file_path=str(GLOBAL_CONFIG_FILE),
                    error_type="IOError"
                )
            except json.JSONDecodeError as e:
                # Lỗi format: JSON không hợp lệ
                EM.raise_error(
                    ErrorCode.CONFIG_FORMAT_INVALID,
                    file_path=str(GLOBAL_CONFIG_FILE),
                    error_type="JSONDecodeError",
                    original_error=str(e)
                )

        self._global_loaded = True
        return self._global_config

    def save_global_config(self) -> None:
        """
        Lưu global config vào ~/.midicoder/midicoder.json.

        Tự động tạo thư mục nếu chưa tồn tại.

        Raises:
            MidicoderError: Nếu không thể ghi file
                - CONFIG_WRITE_FAILED: Lỗi IO khi ghi file
        """
        try:
            GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(GLOBAL_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._global_config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            EM.raise_error(
                ErrorCode.CONFIG_WRITE_FAILED,
                file_path=str(GLOBAL_CONFIG_FILE),
                error_type="IOError"
            )

    def load_project_config(self) -> dict:
        """
        Tải project config từ .midicoder/config/midicoder.yml.

        Nếu file không tồn tại, tự động tạo với default values.
        Cache kết quả để tránh load nhiều lần.

        Returns:
            dict: Project config dictionary

        Raises:
            MidicoderError: Nếu không thể đọc file hoặc format không đúng
                - CONFIG_READ_FAILED: Lỗi IO khi đọc file
                - CONFIG_FORMAT_INVALID: YAML không hợp lệ
        """
        if self._project_loaded:
            return self._project_config

        if not PROJECT_CONFIG_FILE.exists():
            self._project_config = self._deep_copy(DEFAULT_PROJECT_CONFIG)
            self.save_project_config()
        else:
            try:
                with open(PROJECT_CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._project_config = yaml.safe_load(f) or {}
            except IOError as e:
                EM.raise_error(
                    ErrorCode.CONFIG_READ_FAILED,
                    file_path=str(PROJECT_CONFIG_FILE),
                    error_type="IOError"
                )
            except yaml.YAMLError as e:
                EM.raise_error(
                    ErrorCode.CONFIG_FORMAT_INVALID,
                    file_path=str(PROJECT_CONFIG_FILE),
                    error_type="YAMLError",
                    original_error=str(e)
                )

        self._project_loaded = True
        return self._project_config

    def save_project_config(self) -> None:
        """
        Lưu project config vào .midicoder/config/midicoder.yml.

        Tự động tạo thư mục nếu chưa tồn tại.

        Raises:
            MidicoderError: Nếu không thể ghi file
                - CONFIG_WRITE_FAILED: Lỗi IO khi ghi file
        """
        try:
            # Tạo parent directory cho file (bao gồm cả config/)
            PROJECT_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PROJECT_CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.dump(
                    self._project_config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True
                )
        except IOError as e:
            EM.raise_error(
                ErrorCode.CONFIG_WRITE_FAILED,
                file_path=str(PROJECT_CONFIG_FILE),
                error_type="IOError"
            )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Lấy giá trị config theo key (dot notation).

        Ưu tiên project config, nếu không có thì lấy từ global config.

        Args:
            key: Key theo dot notation (ví dụ: 'llm.model', 'cli.language')
            default: Giá trị mặc định nếu key không tồn tại

        Returns:
            Any: Giá trị config, hoặc default nếu không tìm thấy

        Ví dụ:
            >>> config = ConfigManager()
            >>> model = config.get("llm.model", "default-model")
            >>> lang = config.get("cli.language", "en")
        """
        # Ưu tiên project config, nếu không có thì global
        project = self.load_project_config()
        global_conf = self.load_global_config()

        # Parse key thành list
        keys = key.split(".")
        
        # Tìm trong project config trước
        value = self._get_nested(project, keys)
        if value is not None:
            return value

        # Tìm trong global config
        value = self._get_nested(global_conf, keys)
        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """
        Set giá trị config theo key.

        Tự động xác định config nào cần set dựa trên key:
        - 'version.*', 'capabilities.*', 'active_version' → project config
        - Các key khác → global config

        Args:
            key: Key theo dot notation
            value: Giá trị mới

        Raises:
            MidicoderError: Nếu value không hợp lệ
                - CONFIG_VALUE_INVALID: Type không đúng

        Ví dụ:
            >>> config = ConfigManager()
            >>> config.set("llm.model", "gpt-4")
            >>> config.set("cli.language", "vi")
        """
        keys = key.split(".")

        # Xác định config nào cần set (project hoặc global)
        # Project-specific keys: version.*, capabilities.*, active_version
        if keys[0] in ["version", "capabilities", "active_version"]:
            config = self._project_config or self.load_project_config()
            save_func = self.save_project_config
            self._project_loaded = True
        else:
            config = self._global_config or self.load_global_config()
            save_func = self.save_global_config
            self._global_loaded = True

        self._set_nested(config, keys, value)
        save_func()

    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset config về mặc định.

        Args:
            key: Key cụ thể để reset, hoặc None để reset toàn bộ

        Ví dụ:
            >>> config = ConfigManager()
            >>> config.reset()  # Reset toàn bộ
            >>> config.reset("llm.model")  # Reset key cụ thể
        """
        if key is None:
            # Reset toàn bộ
            self._global_config = self._deep_copy(DEFAULT_GLOBAL_CONFIG)
            self._project_config = self._deep_copy(DEFAULT_PROJECT_CONFIG)
            self._global_loaded = True
            self._project_loaded = True
            self.save_global_config()
            self.save_project_config()
        else:
            # Reset key cụ thể
            keys = key.split(".")
            if keys[0] in ["version", "capabilities"]:
                self._reset_nested(self._project_config, keys, DEFAULT_PROJECT_CONFIG)
                self.save_project_config()
            else:
                self._reset_nested(self._global_config, keys, DEFAULT_GLOBAL_CONFIG)
                self.save_global_config()

    def _get_nested(self, data: dict, keys: list) -> Any:
        """
        Lấy giá trị nested từ dict theo list keys.

        Args:
            data: Dictionary để lấy giá trị
            keys: List keys để traverse

        Returns:
            Any: Giá trị tìm thấy, hoặc None nếu không có
        """
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            else:
                return None
            if data is None:
                return None
        return data

    def _set_nested(self, data: dict, keys: list, value: Any) -> None:
        """
        Set giá trị nested trong dict theo list keys.

        Tự động tạo các dict trung gian nếu không tồn tại.

        Args:
            data: Dictionary để set giá trị
            keys: List keys để traverse
            value: Giá trị cần set
        """
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]
        data[keys[-1]] = value

    def _reset_nested(self, data: dict, keys: list, default_config: dict) -> None:
        """
        Reset giá trị nested về default value.

        Args:
            data: Dictionary cần reset
            keys: List keys để traverse
            default_config: Default config để lấy default value
        """
        # Tìm default value từ default config
        default = self._get_nested(default_config, keys)

        if default is not None:
            self._set_nested(data, keys, self._deep_copy(default))

    def _deep_copy(self, obj: Any) -> Any:
        """
        Deep copy một object để tránh shared reference.

        Args:
            obj: Object cần copy

        Returns:
            Any: Copied object
        """
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj

    def _get_timestamp(self) -> str:
        """
        Trả về timestamp hiện tại theo ISO format.

        Returns:
            str: Timestamp ISO format (ví dụ: '2026-04-23T15:30:00Z')
        """
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# Global config manager instance (singleton pattern)
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """
    Lấy global config manager instance (singleton).

    Returns:
        ConfigManager: Global config manager instance

    Ví dụ:
        >>> from midicoder.pipeline.config import get_config
        >>> config = get_config()
        >>> model = config.get("llm.model")
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_global_config_path() -> Path:
    """
    Trả về đường dẫn global config file.

    Returns:
        Path: Đường dẫn đến ~/.midicoder/midicoder.json
    """
    return GLOBAL_CONFIG_FILE


def get_project_config_path() -> Path:
    """
    Trả về đường dẫn project config file.

    Returns:
        Path: Đường dẫn đến .midicoder/config/midicoder.yml
    """
    return PROJECT_CONFIG_FILE