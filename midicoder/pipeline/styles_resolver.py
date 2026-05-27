"""
StyleResolver — 4-layer merge cho component styles qua render_context.

Resolve chuỗi (thấp → cao):
    Layer 0:  Preset từ midicoder/presets/{ui_lib}.yml
    Layer 1:  midicoder.config.yml render.defaults.styles
    Layer 2:  midicoder.config.yml render.per_entity.{Name}.styles
    Layer 3:  DSL render_context.styles (cao nhất)

Usage:
    from midicoder.pipeline.config import StyleResolver

    resolver = StyleResolver()
    styles = resolver.resolve(
        stack="react",
        component="Sidebar",
        ui_framework="material",
        entity_rc={},          # từ DSL
        user_config={},        # từ midicoder.config.yml
    )
    # styles → {"width": "240px", "background": "#fff", ...}

E00: Installation & Setup
"""

from __future__ import annotations

from typing import Any

from midicoder.presets import load_preset

from .config import deep_merge


class StyleResolver:
    """
    Resolve component styles qua 4-layer merge chain.

    Attributes:
        _preset_cache: Cache cho loaded presets (tránh load file nhiều lần)
    """

    def __init__(self) -> None:
        self._preset_cache: dict[str, dict] = {}

    def resolve(
        self,
        stack: str,
        component: str,
        ui_framework: str,
        entity_rc: dict,
        user_config: dict,
    ) -> dict[str, Any]:
        """
        Resolve styles cho một component cụ thể.

        Merge order (thấp → cao):
            0. Preset (midicoder/presets/{ui_framework}.yml)
            1. user_config.render.defaults.styles
            2. user_config.render.per_entity.{component}.styles
            3. entity_rc.styles (DSL — cao nhất)

        Args:
            stack: "react" hoặc "angular"
            component: Tên component (vd: "Sidebar")
            ui_framework: UI framework (material, tailwind, bootstrap, antd, carbon)
            entity_rc: render_context từ DSL
            user_config: Config từ midicoder.config.yml

        Returns:
            dict: Merged styles (rỗng nếu không có style nào)
        """
        merged: dict[str, Any] = {}

        # Layer 0: Preset
        preset_styles = self._get_preset_styles(ui_framework, stack, component)
        merged = deep_merge(merged, preset_styles)

        # Layer 1: user_config render.defaults.styles
        defaults_styles = (
            user_config.get("render", {})
            .get("defaults", {})
            .get("styles", {})
            .get(stack, {})
            .get(component, {})
        )
        merged = deep_merge(merged, defaults_styles)

        # Layer 2: user_config render.per_entity.{Name}.styles
        per_entity_styles = (
            user_config.get("render", {})
            .get("per_entity", {})
            .get(component, {})
            .get("styles", {})
            .get(stack, {})
            .get(component, {})
        )
        merged = deep_merge(merged, per_entity_styles)

        # Layer 3: DSL render_context.styles (cao nhất)
        dsl_styles = (
            entity_rc.get("styles", {})
            .get(stack, {})
            .get(component, {})
        )
        merged = deep_merge(merged, dsl_styles)

        return merged

    def resolve_infrastructure(
        self,
        component: str,
        user_config: dict,
    ) -> dict[str, Any]:
        """
        Resolve styles cho infrastructure components (Docker, K8s, CI/CD).

        Infrastructure không có UI framework, chỉ merge:
            0. Preset (infrastructure.yml)
            1. user_config.render.defaults.infrastructure
            2. user_config.render.infrastructure

        Args:
            component: Tên infra component (vd: "postgres", "redis")
            user_config: Config từ midicoder.config.yml

        Returns:
            dict: Merged infrastructure styles
        """
        merged: dict[str, Any] = {}

        # Layer 0: Preset
        preset = self._get_cached_preset("infrastructure")
        infra_styles = preset.get(component, {})
        merged = deep_merge(merged, infra_styles)

        # Layer 1: defaults.infrastructure
        defaults_infra = (
            user_config.get("render", {})
            .get("defaults", {})
            .get("infrastructure", {})
            .get(component, {})
        )
        merged = deep_merge(merged, defaults_infra)

        # Layer 2: render.infrastructure (toplevel)
        toplevel_infra = (
            user_config.get("render", {})
            .get("infrastructure", {})
            .get(component, {})
        )
        merged = deep_merge(merged, toplevel_infra)

        return merged

    def _get_cached_preset(self, name: str) -> dict:
        if name not in self._preset_cache:
            self._preset_cache[name] = load_preset(name)
        return self._preset_cache[name]

    def _get_preset_styles(
        self, ui_framework: str, stack: str, component: str
    ) -> dict[str, Any]:
        """Lấy styles từ preset file cho component cụ thể."""
        preset = self._get_cached_preset(ui_framework)
        return preset.get(stack, {}).get(component, {})

    def clear_cache(self) -> None:
        """Xóa cache presets (dùng trong test)."""
        self._preset_cache.clear()
