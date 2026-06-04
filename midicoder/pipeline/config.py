"""
ConfigManager — quản lý cấu hình Midicoder.

Global settings: SQLite settings.db (SettingsManager)
Project settings: YAML tại <project_path>/.midicoder/config/midicoder.yml
"""

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

# EU-0.4: Import typed models (with fallback for import safety)
try:
    from midicoder.packs.models import (
        PresetType,
        RenderContextSpec,
        StackType,
        StyleResolverV2,
    )

    _MODELS_AVAILABLE = True
except ImportError:
    _MODELS_AVAILABLE = False

# Project config YAML filename
PROJECT_CONFIG_FILENAME = "midicoder.yml"


DEFAULT_PROJECT_CONFIG = {
    "midicoder_version": "1.0.0",
    "created_at": None,
    "max_versions": 5,
    "capabilities": {"enabled": []},
}


class ConfigManager:
    """Quản lý cấu hình global (SQLite) và project (YAML)."""

    def __init__(self) -> None:
        self._project_config: Optional[dict] = None
        self._project_path: Optional[str] = None

    @property
    def _settings(self) -> "SettingsManager":
        from midicoder.storage.settings import SettingsManager
        mgr = SettingsManager()
        mgr.init()
        return mgr

    def set_project_path(self, path: Optional[str]) -> None:
        """Set project path để load YAML config đúng."""
        self._project_path = path
        self._project_config = None

    def _project_config_file(self) -> Optional[Path]:
        if not self._project_path:
            return None
        return Path(self._project_path) / ".midicoder" / "config" / PROJECT_CONFIG_FILENAME

    def load_global_config(self) -> "SettingsManager":
        """Return the SettingsManager instance."""
        return self._settings

    def save_global_config(self) -> None:
        """No-op — SettingsManager auto-commits to SQLite."""
        pass

    def load_project_config(self) -> dict:
        """Load project YAML config. Returns empty dict if not found."""
        if self._project_config is not None:
            return self._project_config

        config_file = self._project_config_file()
        if config_file is None or not config_file.exists():
            self._project_config = {}
            return self._project_config

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                self._project_config = yaml.safe_load(f) or {}
        except IOError as e:
            EM.raise_error(ErrorCode.CONFIG_READ_FAILED, file_path=str(config_file), error_type="IOError")
        except yaml.YAMLError as e:
            EM.raise_error(ErrorCode.CONFIG_FORMAT_INVALID, file_path=str(config_file), error_type="YAMLError", original_error=str(e))

        return self._project_config

    def save_project_config(self) -> None:
        """Save project config to YAML."""
        config_file = self._project_config_file()
        if config_file is None:
            return

        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(self._project_config or {}, f, default_flow_style=False, allow_unicode=True)
        except IOError as e:
            EM.raise_error(ErrorCode.CONFIG_WRITE_FAILED, file_path=str(config_file), error_type="IOError")

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key. Project YAML takes priority over global SQLite."""
        scope = _resolve_scope(key)
        if scope == "project":
            project = self.load_project_config()
            value = _get_nested(project, key)
            if value is not None:
                return value
        try:
            return self._settings.get_nested(key, default)
        except Exception:
            return default

    def set(self, key: str, value: Any) -> None:
        """Set config value. Project keys go to YAML, global keys to SQLite."""
        if key.startswith("project."):
            return
        if key == "project_path":
            self.set_project_path(value)
            return

        scope = _resolve_scope(key)
        if scope == "project":
            config = self.load_project_config()
            _set_nested(config, key, value)
            self.save_project_config()
        else:
            self._settings.set_nested(key, value)

    def reset(self, key: Optional[str] = None) -> None:
        """Reset config to defaults."""
        if key is None:
            self._settings.reset(None)
            self._project_config = {}
            self.save_project_config()
        else:
            scope = _resolve_scope(key)
            if scope == "project":
                self._project_config = self._deep_copy(DEFAULT_PROJECT_CONFIG)
                self.save_project_config()
            else:
                self._settings.reset(key)

    def _deep_copy(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        return obj

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_scope(key: str) -> str:
    """Determine whether a config key belongs to project or global scope."""
    project_keys = {"active_version", "midicoder_version", "domain", "created_at", "max_versions"}
    parts = key.split(".")
    if parts[0] in project_keys or parts[0] == "capabilities":
        return "project"
    return "global"


def _get_nested(data: dict, key: str) -> Any:
    """Get nested value from dict by dot-notation key."""
    for part in key.split("."):
        if isinstance(data, dict):
            data = data.get(part)
        else:
            return None
        if data is None:
            return None
    return data


def _set_nested(data: dict, key: str, value: Any) -> None:
    """Set nested value in dict by dot-notation key."""
    parts = key.split(".")
    for part in parts[:-1]:
        if part not in data:
            data[part] = {}
        data = data[part]
    data[parts[-1]] = value


# EU-0.2 constants
USER_CONFIG_FILE = "midicoder.config.yml"


def deep_merge(base: dict, override: dict) -> dict:
    """
    Merge override vào base recursively (deep merge).

    - Dict + Dict: merge recursive
    - Non-dict override: ghi đè base
    - Key chỉ có trong base: giữ nguyên
    - Key chỉ có trong override: thêm vào result
    - Không mutate base hoặc override

    Returns:
        dict: Kết quả merge (dict mới)
    """
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_user_config(project_root: Path) -> dict:
    """
    Đọc midicoder.config.yml từ project root.

    EU-0.2: Project-level render overrides file, khác với internal
    .midicoder/config/midicoder.yml.

    Args:
        project_root: Đường dẫn đến root của project

    Returns:
        dict: Config dict, hoặc {} nếu file không tồn tại

    Raises:
        MidicoderError: Nếu YAML invalid (MDC-CONFIG-003)
    """
    config_path = project_root / USER_CONFIG_FILE

    if not config_path.exists():
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        EM.raise_error(
            ErrorCode.CONFIG_FORMAT_INVALID,
            file_path=str(config_path),
            error_type="YAMLError",
            original_error=str(e),
        )

    return data


def resolve_render_context(
    stack: "StackType",
    preset: "PresetType",
    config_yml: Optional[dict[str, Any]] = None,
    dsl_context: Optional[dict[str, Any]] = None,
    entity_name: Optional[str] = None,
    project_root: Optional[Path] = None,
) -> "RenderContextSpec":
    """
    Resolve RenderContextSpec từ 4 layers bằng StyleResolverV2.

    4-layer merge (thấp → cao):
    0. Preset YAML
    1. midicoder.config.yml render.defaults
    2. midicoder.config.yml render.per_entity.{Name}
    3. DSL render_context (cao nhất)

    EU-0.4: Trả về RenderContextSpec typed object (không còn flat dict).

    Args:
        stack: StackType (react, angular, fastapi, nestjs, infrastructure)
        preset: PresetType (material, tailwind, bootstrap, antd, carbon)
        config_yml: Dict từ midicoder.config.yml
        dsl_context: Render context từ DSL entity spec
        entity_name: Tên entity (để lookup per_entity config)
        project_root: Đường dẫn project root (default: hiện tại)

    Returns:
        RenderContextSpec: Typed object (dùng .to_dict() cho backward compat)
    """
    if _MODELS_AVAILABLE:
        presets_dir = Path(project_root or ".") / "midicoder" / "presets"
        resolver = StyleResolverV2(presets_dir)
        render_section: dict[str, Any] = {}
        if config_yml:
            render_section = config_yml.get("render", {})
        return resolver.resolve(
            stack_type=stack,
            preset_type=preset,
            entity_rc=dsl_context,
            user_defaults=render_section.get("defaults", {}),
            user_per_entity=render_section.get("per_entity", {}),
            entity_name=entity_name,
        )
    else:
        # Fallback: trả về flat dict từ V1 khi models không available
        warnings.warn(
            "RenderContextSpec models not available; falling back to resolve_render_context_v1()",
            UserWarning,
            stacklevel=2,
        )
        # Caller sẽ receive dict, không phải RenderContextSpec
        return resolve_render_context_v1(  # type: ignore[return-value]
            entity_id=entity_name or "",
            entity_rc=dsl_context or {},
            user_config=config_yml or {},
            stack=stack.value if hasattr(stack, "value") else str(stack),
            ui_framework=preset.value if hasattr(preset, "value") else str(preset),
        )


def resolve_render_context_v1(
    entity_id: str,
    entity_rc: dict,
    user_config: dict,
    stack: str = "",
    ui_framework: str = "",
) -> dict:
    """
    [DEPRECATED] Resolve render_context theo 3-layer priority + StyleResolver.

    EU-0.4 Deprecated: Sử dụng resolve_render_context() mới trả về RenderContextSpec.
    Giữ lại cho backward compat với file_contributions_loader expand_* methods.

    3-layer merge:
    1. entity.render_context (DSL-level — CAO NHẤT)
    2. midicoder.config.yml render.per_entity.{EntityName}
    3. midicoder.config.yml render.defaults (THẤP NHẤT)

    EU-0.3: Nếu stack + ui_framework được cung cấp, thêm ``styles`` dict
    vào result qua StyleResolver.

    Args:
        entity_id: ID của entity (vd: "Product")
        entity_rc: render_context từ DSL (entity.render_context)
        user_config: Dict từ midicoder.config.yml
        stack: Stack name ("react", "angular", "fastapi", "nestjs", "infrastructure")
        ui_framework: UI framework ("material", "tailwind", "bootstrap", "antd", "carbon")

    Returns:
        dict: Merged render_context (bao gồm ``styles`` nếu applicable)
    """
    warnings.warn(
        "resolve_render_context_v1 is deprecated; use resolve_render_context() which returns RenderContextSpec",
        DeprecationWarning,
        stacklevel=2,
    )

    from midicoder.pipeline.styles_resolver import StyleResolver  # avoid circular

    merged: dict[str, Any] = {}

    # Layer 1: global defaults (thấp nhất)
    merged.update(user_config.get("render", {}).get("defaults", {}))

    # Layer 2: per-entity override (deep merge)
    per_entity = user_config.get("render", {}).get("per_entity", {}).get(entity_id, {})
    merged = deep_merge(merged, per_entity)

    # Layer 3: DSL-level (cao nhất - deep merge)
    merged = deep_merge(merged, entity_rc)

    # EU-0.3: Resolve component styles via StyleResolver
    if stack and ui_framework and stack in ("react", "angular"):
        resolver = StyleResolver()
        component_styles = resolver.resolve(
            stack=stack,
            component=entity_id,
            ui_framework=ui_framework,
            entity_rc=entity_rc,
            user_config=user_config,
        )
        if component_styles:
            if "styles" not in merged:
                merged["styles"] = {}
            if stack not in merged["styles"]:
                merged["styles"][stack] = {}
            merged["styles"][stack][entity_id] = component_styles

    return merged


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


def get_project_config_path() -> Path:
    """Path to project YAML config file (relative)."""
    return Path(".midicoder") / "config" / PROJECT_CONFIG_FILENAME