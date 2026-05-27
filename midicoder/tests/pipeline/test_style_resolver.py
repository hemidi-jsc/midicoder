"""
Tests cho StyleResolver — EU-0.3 v2 Component Styles System

Test scope:
- 4-layer merge chain (preset → defaults → per_entity → DSL)
- Infrastructure resolve
- Cache management
- Edge cases (empty inputs, missing preset)
"""

from __future__ import annotations

import pytest

from midicoder.pipeline.styles_resolver import StyleResolver


class TestStyleResolverResolve:
    """Test StyleResolver.resolve() — 4-layer merge chain."""

    def test_empty_inputs_returns_empty(self):
        resolver = StyleResolver()
        result = resolver.resolve(
            stack="react",
            component="NonExistent",
            ui_framework="material",
            entity_rc={},
            user_config={},
        )
        assert result == {}

    def test_layer0_preset_only(self):
        """Khi chỉ có preset, result = preset styles."""
        resolver = StyleResolver()
        result = resolver.resolve(
            stack="react",
            component="Sidebar",
            ui_framework="material",
            entity_rc={},
            user_config={},
        )
        # material.yml có react.Sidebar.width = "280px"
        assert result.get("width") == "280px"
        assert result.get("background") == "#ffffff"

    def test_layer1_defaults_override_preset(self):
        """render.defaults.styles ghi đè preset."""
        resolver = StyleResolver()
        result = resolver.resolve(
            stack="react",
            component="Sidebar",
            ui_framework="material",
            entity_rc={},
            user_config={
                "render": {
                    "defaults": {
                        "styles": {
                            "react": {
                                "Sidebar": {"width": "300px"}
                            }
                        }
                    }
                }
            },
        )
        assert result["width"] == "300px"
        # preserved từ preset
        assert result["background"] == "#ffffff"

    def test_layer2_per_entity_override_defaults(self):
        """render.per_entity.{Name}.styles ghi đè defaults."""
        resolver = StyleResolver()
        result = resolver.resolve(
            stack="react",
            component="Sidebar",
            ui_framework="material",
            entity_rc={},
            user_config={
                "render": {
                    "defaults": {
                        "styles": {
                            "react": {"Sidebar": {"width": "300px"}}
                        }
                    },
                    "per_entity": {
                        "Sidebar": {
                            "styles": {
                                "react": {"Sidebar": {"width": "350px"}}
                            }
                        }
                    },
                }
            },
        )
        assert result["width"] == "350px"

    def test_layer3_dsl_overrides_all(self):
        """DSL render_context.styles ghi đè tất cả."""
        resolver = StyleResolver()
        result = resolver.resolve(
            stack="react",
            component="Sidebar",
            ui_framework="material",
            entity_rc={
                "styles": {
                    "react": {"Sidebar": {"width": "400px", "custom_prop": "abc"}}
                }
            },
            user_config={},
        )
        assert result["width"] == "400px"
        assert result["custom_prop"] == "abc"
        # preserved từ preset
        assert result["background"] == "#ffffff"

    def test_full_chain_priority(self):
        """Test đầy đủ 4-layer: preset < defaults < per_entity < DSL."""
        resolver = StyleResolver()
        result = resolver.resolve(
            stack="react",
            component="Sidebar",
            ui_framework="material",
            entity_rc={
                "styles": {
                    "react": {"Sidebar": {"width": "500px"}}
                }
            },
            user_config={
                "render": {
                    "defaults": {
                        "styles": {
                            "react": {
                                "Sidebar": {
                                    "width": "100px",
                                    "background": "#red",
                                }
                            }
                        }
                    },
                    "per_entity": {
                        "Sidebar": {
                            "styles": {
                                "react": {
                                    "Sidebar": {
                                        "width": "200px",
                                        "position": "fixed",
                                    }
                                }
                            }
                        }
                    },
                }
            },
        )
        # width: DSL wins
        assert result["width"] == "500px"
        # background: defaults wins (DSL không override)
        assert result["background"] == "#red"
        # position: per_entity wins
        assert result["position"] == "fixed"

    def test_different_ui_frameworks(self):
        """Mỗi UI framework có preset khác nhau."""
        resolver = StyleResolver()

        material = resolver.resolve("react", "Sidebar", "material", {}, {})
        tailwind = resolver.resolve("react", "Sidebar", "tailwind", {}, {})
        bootstrap = resolver.resolve("react", "Sidebar", "bootstrap", {}, {})
        antd = resolver.resolve("react", "Sidebar", "antd", {}, {})
        carbon = resolver.resolve("react", "Sidebar", "carbon", {}, {})

        # Sidebar width khác nhau giữa frameworks
        assert material["width"] == "280px"
        assert tailwind["width"] == "256px"
        assert bootstrap["width"] == "280px"
        assert antd["width"] == "220px"
        assert carbon["width"] == "280px"

    def test_different_stacks(self):
        """React và Angular có component styles khác nhau."""
        resolver = StyleResolver()

        react_modal = resolver.resolve("react", "Modal", "material", {}, {})
        angular_dialog = resolver.resolve("angular", "Dialog", "material", {}, {})

        assert "width_sm" in react_modal
        assert "width_antd" in angular_dialog

    def test_deep_merge_preserves_nested(self):
        """Deep merge preserves keys không bị override."""
        resolver = StyleResolver()
        result = resolver.resolve(
            stack="react",
            component="Sidebar",
            ui_framework="material",
            entity_rc={
                "styles": {
                    "react": {"Sidebar": {"width": "999px"}}
                }
            },
            user_config={},
        )
        assert result["width"] == "999px"
        # preserved từ preset
        assert result["background"] == "#ffffff"
        assert result["border_right"] == "1px solid #e5e7eb"


class TestStyleResolverInfrastructure:
    """Test StyleResolver.resolve_infrastructure()."""

    def test_infra_postgres_defaults(self):
        resolver = StyleResolver()
        result = resolver.resolve_infrastructure("postgres", {})
        assert result["image"] == "postgres:15-alpine"
        assert result["port"] == 5432

    def test_infra_redis_defaults(self):
        resolver = StyleResolver()
        result = resolver.resolve_infrastructure("redis", {})
        assert result["image"] == "redis:7-alpine"
        assert result["port"] == 6379

    def test_infra_user_config_override(self):
        resolver = StyleResolver()
        result = resolver.resolve_infrastructure(
            "postgres",
            user_config={
                "render": {
                    "infrastructure": {
                        "postgres": {"image": "postgres:16-alpine"}
                    }
                }
            },
        )
        assert result["image"] == "postgres:16-alpine"
        # preserved từ preset
        assert result["port"] == 5432

    def test_infra_defaults_override(self):
        resolver = StyleResolver()
        result = resolver.resolve_infrastructure(
            "redis",
            user_config={
                "render": {
                    "defaults": {
                        "infrastructure": {
                            "redis": {"port": 6380}
                        }
                    }
                }
            },
        )
        assert result["port"] == 6380
        assert result["image"] == "redis:7-alpine"

    def test_infra_unknown_component(self):
        resolver = StyleResolver()
        result = resolver.resolve_infrastructure("unknown_component", {})
        assert result == {}


class TestStyleResolverCache:
    """Test StyleResolver cache behavior."""

    def test_cache_is_populated(self):
        resolver = StyleResolver()
        assert resolver._preset_cache == {}
        resolver.resolve("react", "Sidebar", "material", {}, {})
        assert "material" in resolver._preset_cache

    def test_clear_cache(self):
        resolver = StyleResolver()
        resolver.resolve("react", "Sidebar", "material", {}, {})
        resolver.clear_cache()
        assert resolver._preset_cache == {}

    def test_missing_preset_returns_empty(self):
        resolver = StyleResolver()
        result = resolver.resolve(
            "react", "Sidebar", "nonexistent_framework", {}, {}
        )
        assert result == {}


class TestPresetFiles:
    """Verify preset files load correctly."""

    def test_all_presets_exist(self):
        from midicoder.presets import list_presets
        presets = list_presets()
        assert "material" in presets
        assert "tailwind" in presets
        assert "bootstrap" in presets
        assert "antd" in presets
        assert "carbon" in presets
        assert "infrastructure" in presets

    def test_preset_has_react_and_angular(self):
        from midicoder.presets import load_preset
        for name in ["material", "tailwind", "bootstrap", "antd", "carbon"]:
            p = load_preset(name)
            assert "react" in p, f"{name} missing 'react'"
            assert "angular" in p, f"{name} missing 'angular'"

    def test_infrastructure_has_all_components(self):
        from midicoder.presets import load_preset
        infra = load_preset("infrastructure")
        assert "postgres" in infra
        assert "redis" in infra
        assert "neo4j" in infra
        assert "kong" in infra
        assert "consul" in infra

    def test_all_5_frameworks_have_sidebar(self):
        from midicoder.presets import load_preset
        for name in ["material", "tailwind", "bootstrap", "antd", "carbon"]:
            p = load_preset(name)
            assert "Sidebar" in p["react"], f"{name} missing Sidebar in react"
            assert "Sidebar" in p["angular"], f"{name} missing Sidebar in angular"
