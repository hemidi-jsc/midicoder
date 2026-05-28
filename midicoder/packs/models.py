# coding: utf-8
"""
Midicoder CE — Shared Pack Models

RenderContextSpec — typed model thay thế flat dict[str, Any]
StyleResolverV2 — merge behavior + tokens, không chỉ CSS

Module này cung cấp typed models cho hệ thống capability packs mới (taxonomy-v2):
- RenderContextSpec: 4-layer merge, thay thế dict[str, Any] trong config.py
- StyleResolverV2: resolve render context per component, per framework, per entity

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


# ============================================================
# Enums
# ============================================================


class StackType(str, Enum):
    """Loại output stack."""
    FASTAPI = "fastapi"
    NESTJS = "nestjs"
    ANGULAR = "angular"
    REACT = "react"
    INFRASTRUCTURE = "infrastructure"


class PresetType(str, Enum):
    """UI framework presets."""
    MATERIAL = "material"
    TAILWIND = "tailwind"
    BOOTSTRAP = "bootstrap"
    ANTD = "antd"
    CARBON = "carbon"


# ============================================================
# RenderContextSpec — typed replacement cho flat dict
# ============================================================


@dataclass
class GlobalDefaults:
    """
    Global defaults áp dụng cho tất cả component.

    Attributes:
        dark_mode: Bật dark mode toàn cục
        accessible: Inject ARIA attributes tự động
        i18n_enabled: Hỗ trợ internationalization
        default_page_size: Số dòng mỗi trang mặc định
        form_layout: Layout form (single_column, two_column, wizard)
        form_validation_mode: Chế độ validation (on_submit, on_blur, on_change)
    """
    dark_mode: bool = False
    accessible: bool = True
    i18n_enabled: bool = False
    default_page_size: int = 20
    form_layout: str = "single_column"
    form_validation_mode: str = "on_submit"


@dataclass
class ComponentBehavior:
    """
    Behavior props cho một component type cụ thể.

    Attributes:
        sortable: DataTable có thể sort
        paginated: DataTable có phân trang
        page_size: Số dòng mỗi trang
        selectable: Có thể select row
        filterable: Có thể filter
        searchable: Có search bar
        editable: Inline editing
        virtual_scroll: Virtual scroll cho danh sách dài
        form_layout: Override form layout cho component này
        validation_mode: Override validation mode
        conditional_enabled: Bật conditional field rules
        close_on_backdrop: Dialog đóng khi click backdrop
        show_cancel: Hiển thị nút Cancel trong dialog
        default_width: Width mặc định (sm, md, lg, xl)
    """
    sortable: bool = True
    paginated: bool = True
    page_size: int = 20
    selectable: bool = False
    filterable: bool = False
    searchable: bool = False
    editable: bool = False
    virtual_scroll: bool = False
    # Form-specific
    form_layout: Optional[str] = None
    validation_mode: Optional[str] = None
    conditional_enabled: bool = False
    # Dialog-specific
    close_on_backdrop: bool = True
    show_cancel: bool = True
    default_width: str = "md"


@dataclass
class ComponentTokens:
    """
    Framework-specific CSS tokens cho component.

    Mỗi framework (material, tailwind, bootstrap, antd, carbon) có tokens riêng.
    Tokens được resolve theo ui_framework hiện tại.
    """

    material: dict[str, str] = field(default_factory=dict)
    tailwind: dict[str, str] = field(default_factory=dict)
    bootstrap: dict[str, str] = field(default_factory=dict)
    antd: dict[str, str] = field(default_factory=dict)
    carbon: dict[str, str] = field(default_factory=dict)

    def get_for_framework(self, framework: str) -> dict[str, str]:
        """
        Lấy tokens cho framework cụ thể.

        Args:
            framework: Tên framework (material, tailwind, ...)

        Returns:
            dict: Tokens cho framework, rỗng nếu không có
        """
        return getattr(self, framework.lower(), {})


@dataclass
class ComponentOverride:
    """
    Override cho một ComponentType cụ thể — behavior + tokens.

    Gồm:
    - behavior: props hành vi (sortable, paginated, ...)
    - tokens: CSS tokens theo framework
    - template_override: path đến custom template (optional)
    """
    behavior: ComponentBehavior = field(default_factory=ComponentBehavior)
    tokens: ComponentTokens = field(default_factory=ComponentTokens)
    template_override: Optional[str] = None  # path đến custom template


@dataclass
class ThemeSpec:
    """
    Theme override spec.

    Attributes:
        primary_color: Màu primary
        secondary_color: Màu secondary
        background_color: Màu nền
        text_color: Màu chữ
        font_family: Font family
        font_size_base: Font size base
        border_radius: Border radius
        dark_mode: Hỗ trợ dark mode
    """
    primary_color: str = "#3f51b5"
    secondary_color: str = "#f50057"
    background_color: str = "#ffffff"
    text_color: str = "#212121"
    font_family: str = "Roboto, sans-serif"
    font_size_base: str = "14px"
    border_radius: str = "4px"
    dark_mode: bool = False


@dataclass
class RenderContextSpec:
    """
    Typed render context — thay thế flat dict[str, Any] trong config.py.

    4-layer merge (thấp → cao):
    0. Preset v2 (behavior + tokens từ YAML)
    1. user_config render.defaults
    2. user_config render.per_entity.{Name}
    3. DSL render_context (cao nhất)

    Attributes:
        ui_framework: UI framework (material, tailwind, ...)
        theme: Theme spec
        components: Overrides theo component type
        defaults: Global defaults
        extra: Dữ liệu tùy ý (backward compat)
    """
    ui_framework: str = PresetType.TAILWIND.value
    theme: Optional[ThemeSpec] = None
    components: dict[str, ComponentOverride] = field(default_factory=dict)
    defaults: Optional[GlobalDefaults] = None
    # Extra arbitrary data (for backward compat)
    extra: dict[str, Any] = field(default_factory=dict)

    def get_component(self, component_type: str) -> ComponentOverride:
        """
        Lấy component override, hoặc trả về default nếu không có.

        Args:
            component_type: Tên component (vd: "DataTable", "Dialog")

        Returns:
            ComponentOverride: Override hoặc default
        """
        key = component_type.lower()
        if key in self.components:
            return self.components[key]
        return ComponentOverride()

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển thành flat dict cho backward compat với template engine.

        Returns:
            dict: Flat dict có thể inject vào Jinja2 context
        """
        result: dict[str, Any] = {
            "ui_framework": self.ui_framework,
        }

        if self.defaults:
            result["defaults"] = {
                "dark_mode": self.defaults.dark_mode,
                "accessible": self.defaults.accessible,
                "i18n_enabled": self.defaults.i18n_enabled,
                "default_page_size": self.defaults.default_page_size,
                "form_layout": self.defaults.form_layout,
                "form_validation_mode": self.defaults.form_validation_mode,
            }

        if self.theme:
            result["theme"] = {
                "primary_color": self.theme.primary_color,
                "secondary_color": self.theme.secondary_color,
                "background_color": self.theme.background_color,
                "text_color": self.theme.text_color,
                "font_family": self.theme.font_family,
                "font_size_base": self.theme.font_size_base,
                "border_radius": self.theme.border_radius,
                "dark_mode": self.theme.dark_mode,
            }

        # Component overrides — chỉ include non-default values
        component_overrides: dict[str, Any] = {}
        for name, override in self.components.items():
            comp_data: dict[str, Any] = {}
            # Behavior — chỉ include non-default
            b = override.behavior
            behavior_dict: dict[str, Any] = {}
            if b.sortable is not True:
                behavior_dict["sortable"] = b.sortable
            if b.paginated is not True:
                behavior_dict["paginated"] = b.paginated
            if b.page_size != 20:
                behavior_dict["page_size"] = b.page_size
            if b.selectable is not False:
                behavior_dict["selectable"] = b.selectable
            if b.filterable is not False:
                behavior_dict["filterable"] = b.filterable
            if b.searchable is not False:
                behavior_dict["searchable"] = b.searchable
            if b.editable is not False:
                behavior_dict["editable"] = b.editable
            if b.virtual_scroll is not False:
                behavior_dict["virtual_scroll"] = b.virtual_scroll
            if b.conditional_enabled is not False:
                behavior_dict["conditional_enabled"] = b.conditional_enabled
            if b.close_on_backdrop is not True:
                behavior_dict["close_on_backdrop"] = b.close_on_backdrop
            if b.show_cancel is not True:
                behavior_dict["show_cancel"] = b.show_cancel
            if b.default_width != "md":
                behavior_dict["default_width"] = b.default_width
            if b.form_layout is not None:
                behavior_dict["form_layout"] = b.form_layout
            if b.validation_mode is not None:
                behavior_dict["validation_mode"] = b.validation_mode
            if behavior_dict:
                comp_data["behavior"] = behavior_dict

            # Tokens cho framework hiện tại
            tokens = override.tokens.get_for_framework(self.ui_framework)
            if tokens:
                comp_data["tokens"] = tokens

            if override.template_override:
                comp_data["template_override"] = override.template_override

            component_overrides[name] = comp_data

        result["components"] = component_overrides
        result.update(self.extra)
        return result


# ============================================================
# StyleResolverV2 — merge behavior + tokens
# ============================================================


class StyleResolverV2:
    """
    Resolve render context per component, per framework, per entity.

    4-layer merge (thấp → cao):
    0. Preset YAML (behavior + tokens)
    1. midicoder.config.yml render.defaults
    2. midicoder.config.yml render.per_entity.{Name}
    3. DSL render_context (từ entity spec — cao nhất)

    Khác với StyleResolver cũ (chỉ merge CSS styles), V2 merge cả
    behavior props + framework tokens + theme + global defaults.

    Usage:
        resolver = StyleResolverV2(presets_dir=Path("midicoder/presets"))
        rc = resolver.resolve(
            stack_type=StackType.REACT,
            preset_type=PresetType.MATERIAL,
            entity_rc=dsl_context,
            user_defaults=user_config.get("render", {}).get("defaults", {}),
            user_per_entity=user_config.get("render", {}).get("per_entity", {}),
            entity_name="Product",
        )
        # rc → RenderContextSpec typed object
    """

    def __init__(self, presets_dir: Path):
        """
        Khởi tạo StyleResolverV2.

        Args:
            presets_dir: Đường dẫn đến thư mục presets (material.yml, tailwind.yml, ...)
        """
        self._presets_dir = presets_dir
        self._preset_cache: dict[str, dict[str, Any]] = {}

    def resolve(
        self,
        stack_type: StackType,
        preset_type: PresetType,
        entity_rc: Optional[dict[str, Any]] = None,
        user_defaults: Optional[dict[str, Any]] = None,
        user_per_entity: Optional[dict[str, Any]] = None,
        entity_name: Optional[str] = None,
    ) -> RenderContextSpec:
        """
        Resolve render context từ 4 layers.

        Merge order (thấp → cao):
            0. Preset YAML
            1. user_defaults (từ midicoder.config.yml render.defaults)
            2. user_per_entity (từ midicoder.config.yml render.per_entity.{Name})
            3. entity_rc (DSL render_context — cao nhất)

        Args:
            stack_type: Stack type (react, angular, fastapi, nestjs, infrastructure)
            preset_type: UI framework (material, tailwind, ...)
            entity_rc: Render context từ DSL entity spec
            user_defaults: Defaults từ user config
            user_per_entity: Per-entity overrides từ user config
            entity_name: Tên entity (để lookup per_entity config)

        Returns:
            RenderContextSpec: Merged render context typed object
        """
        rc = RenderContextSpec(ui_framework=preset_type.value)

        # Layer 0: Preset YAML
        preset = self._load_preset(preset_type.value)
        if preset:
            self._apply_preset(rc, preset)

        # Layer 1: user config defaults
        if user_defaults:
            self._apply_defaults(rc, user_defaults)

        # Layer 2: user config per_entity
        if user_per_entity and entity_name:
            entity_config = user_per_entity.get(entity_name, {})
            if entity_config:
                self._apply_entity_config(rc, entity_config)

        # Layer 3: DSL entity render_context (highest priority)
        if entity_rc:
            self._apply_dsl_context(rc, entity_rc)

        return rc

    def resolve_component(
        self,
        component_name: str,
        render_context: RenderContextSpec,
    ) -> ComponentOverride:
        """
        Lấy resolved override cho một component type cụ thể.

        Args:
            component_name: Tên component (vd: "DataTable", "Dialog")
            render_context: RenderContextSpec đã merge

        Returns:
            ComponentOverride: Override cho component, hoặc default
        """
        return render_context.get_component(component_name)

    def _load_preset(self, preset_name: str) -> dict[str, Any]:
        """
        Load preset YAML từ disk (có cache).

        Args:
            preset_name: Tên preset (material, tailwind, ...)

        Returns:
            dict: Preset data, rỗng nếu file không tồn tại
        """
        if preset_name in self._preset_cache:
            return self._preset_cache[preset_name]

        preset_path = self._presets_dir / f"{preset_name}.yml"
        if preset_path.exists():
            try:
                with open(preset_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                self._preset_cache[preset_name] = data
                return data
            except yaml.YAMLError as e:
                logger.error("YAML lỗi khi load preset %s: %s", preset_path, e)
                return {}

        logger.warning("Preset không tìm thấy: %s", preset_path)
        return {}

    def _apply_preset(self, rc: RenderContextSpec, preset: dict[str, Any]) -> None:
        """
        Áp dụng preset v2: behavior + tokens per component.

        Preset YAML có thể có cấu trúc:
        - {component_name}: {behavior: {...}, tokens: {...}}
        - {component_name}: {material: {...}, tailwind: {...}} (framework-specific tokens)

        Args:
            rc: RenderContextSpec đang build
            preset: Data từ YAML file
        """
        for component_name, component_data in preset.items():
            if not isinstance(component_data, dict):
                continue

            override = ComponentOverride()

            # Parse behavior
            if "behavior" in component_data:
                b = component_data["behavior"]
                if isinstance(b, dict):
                    for key, val in b.items():
                        if hasattr(override.behavior, key):
                            setattr(override.behavior, key, val)

            # Parse tokens (cấu trúc cũ: tokens.material, tokens.tailwind, ...)
            if "tokens" in component_data:
                tokens_data = component_data["tokens"]
                if isinstance(tokens_data, dict):
                    for fw_name, token_val in tokens_data.items():
                        if hasattr(override.tokens, fw_name):
                            setattr(override.tokens, fw_name, token_val)

            # Parse framework-specific token blocks (material:, tailwind:, etc.)
            for fw_key in ["material", "tailwind", "bootstrap", "antd", "carbon"]:
                if fw_key in component_data and isinstance(component_data[fw_key], dict):
                    setattr(override.tokens, fw_key, component_data[fw_key])

            # Chỉ thêm override nếu có behavior hoặc tokens khác default
            has_behavior = any(
                getattr(override.behavior, attr) != getattr(ComponentBehavior(), attr)
                for attr in [
                    "sortable", "paginated", "page_size", "selectable",
                    "filterable", "searchable", "editable", "virtual_scroll",
                    "close_on_backdrop", "show_cancel", "default_width",
                ]
            )
            has_tokens = any(
                getattr(override.tokens, fw)
                for fw in ["material", "tailwind", "bootstrap", "antd", "carbon"]
            )

            if has_behavior or has_tokens:
                rc.components[component_name.lower()] = override

    def _apply_defaults(self, rc: RenderContextSpec, defaults: dict[str, Any]) -> None:
        """
        Áp dụng user defaults layer.

        Args:
            rc: RenderContextSpec đang build
            defaults: Defaults dict từ user config
        """
        if "ui_framework" in defaults:
            rc.ui_framework = defaults["ui_framework"]

        if "defaults" in defaults:
            g = defaults["defaults"]
            if isinstance(g, dict):
                if rc.defaults is None:
                    rc.defaults = GlobalDefaults()
                for key, val in g.items():
                    if hasattr(rc.defaults, key):
                        setattr(rc.defaults, key, val)

        if "theme" in defaults:
            t = defaults["theme"]
            if isinstance(t, dict):
                if rc.theme is None:
                    rc.theme = ThemeSpec()
                for key, val in t.items():
                    if hasattr(rc.theme, key):
                        setattr(rc.theme, key, val)

        if "components" in defaults:
            comp_defaults = defaults["components"]
            if isinstance(comp_defaults, dict):
                for name, data in comp_defaults.items():
                    if not isinstance(data, dict):
                        continue
                    if name not in rc.components:
                        rc.components[name] = ComponentOverride()

    def _apply_entity_config(self, rc: RenderContextSpec, config: dict[str, Any]) -> None:
        """
        Áp dụng per-entity user config.

        Reuses _apply_defaults logic vì cấu trúc per_entity tương tự defaults.

        Args:
            rc: RenderContextSpec đang build
            config: Per-entity config dict
        """
        self._apply_defaults(rc, config)

    def _apply_dsl_context(self, rc: RenderContextSpec, dsl_context: dict[str, Any]) -> None:
        """
        Áp dụng DSL render_context (highest priority).

        Args:
            rc: RenderContextSpec đang build
            dsl_context: DSL render_context dict
        """
        self._apply_defaults(rc, dsl_context)

    def clear_cache(self) -> None:
        """Xóa cache presets (dùng trong test)."""
        self._preset_cache.clear()


# ============================================================
# Backward compat — resolve_render_context() wrapper
# ============================================================


def resolve_render_context_v2(
    presets_dir: Path,
    stack_type: StackType,
    preset_type: PresetType,
    config_yml: Optional[dict[str, Any]] = None,
    dsl_context: Optional[dict[str, Any]] = None,
    entity_name: Optional[str] = None,
) -> RenderContextSpec:
    """
    Drop-in replacement cho resolve_render_context() trong config.py.

    Trả về RenderContextSpec typed thay vì flat dict.

    Args:
        presets_dir: Đường dẫn đến thư mục presets
        stack_type: Stack type (react, angular, fastapi, ...)
        preset_type: UI framework (material, tailwind, ...)
        config_yml: Dict từ midicoder.config.yml
        dsl_context: Render context từ DSL entity spec
        entity_name: Tên entity (để lookup per_entity config)

    Returns:
        RenderContextSpec: Merged render context typed object
    """
    resolver = StyleResolverV2(presets_dir)
    render_section: dict[str, Any] = {}
    if config_yml:
        render_section = config_yml.get("render", {})

    return resolver.resolve(
        stack_type=stack_type,
        preset_type=preset_type,
        entity_rc=dsl_context,
        user_defaults=render_section.get("defaults", {}),
        user_per_entity=render_section.get("per_entity", {}),
        entity_name=entity_name,
    )
