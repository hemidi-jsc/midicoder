"""
Unit tests cho EU-0.2: midicoder.config.yml (Project-level render overrides).

Kiểm tra:
- deep_merge(): merge recursive 2 dict
- load_user_config(): đọc file, không tồn tại, YAML invalid
- resolve_render_context(): priority order (defaults → per_entity → DSL RC)
"""

import yaml
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from midicoder.pipeline.config import (
    deep_merge,
    load_user_config,
    resolve_render_context,
    USER_CONFIG_FILE,
)


# ============================================================================
# deep_merge tests
# ============================================================================


class TestDeepMerge:
    """Test cases cho deep_merge()."""

    def test_merge_empty_dicts(self):
        """Merge 2 dict rỗng → dict rỗng."""
        result = deep_merge({}, {})
        assert result == {}

    def test_merge_override_empty(self):
        """Override rỗng → giữ nguyên base."""
        result = deep_merge({"a": 1, "b": 2}, {})
        assert result == {"a": 1, "b": 2}

    def test_merge_base_empty(self):
        """Base rỗng → giữ nguyên override."""
        result = deep_merge({}, {"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    def test_merge_flat_override(self):
        """Override flat dict — ghi đè key có sẵn, thêm key mới."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_nested_dict_deep(self):
        """Override nested dict — merge recursive (deep), preserve keys không được override."""
        base = {"sidebar": {"width": 280, "color": "red"}}
        override = {"sidebar": {"width": 320}}
        result = deep_merge(base, override)
        # width được override, color được preserve
        assert result == {"sidebar": {"width": 320, "color": "red"}}

    def test_merge_nested_multiple_levels(self):
        """Merge nested nhiều cấp."""
        base = {"a": {"b": {"c": 1, "d": 2, "e": {"f": 3, "g": 4}}}}
        override = {"a": {"b": {"c": 10, "e": {"f": 30}}}}
        result = deep_merge(base, override)
        assert result == {"a": {"b": {"c": 10, "d": 2, "e": {"f": 30, "g": 4}}}}

    def test_merge_non_dict_override_wins(self):
        """Override non-dict ghi đè dict của base."""
        base = {"a": {"b": 1}}
        override = {"a": "flat_string"}
        result = deep_merge(base, override)
        assert result == {"a": "flat_string"}

    def test_merge_list_override(self):
        """List override — ghi đè, không merge."""
        base = {"tags": ["a", "b"]}
        override = {"tags": ["c"]}
        result = deep_merge(base, override)
        assert result == {"tags": ["c"]}

    def test_merge_mixed_types(self):
        """Mix của deep merge và flat override."""
        base = {"ui": {"sidebar": {"width": 240}, "header": "fixed"}, "theme": "dark"}
        override = {"ui": {"sidebar": {"color": "blue"}, "footer": "sticky"}, "version": 2}
        result = deep_merge(base, override)
        assert result == {
            "ui": {
                "sidebar": {"width": 240, "color": "blue"},
                "header": "fixed",
                "footer": "sticky",
            },
            "theme": "dark",
            "version": 2,
        }

    def test_merge_does_not_mutate_base(self):
        """deep_merge không mutate base dict."""
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        base_copy = {"a": {"b": 1}}
        deep_merge(base, override)
        assert base == base_copy

    def test_merge_does_not_mutate_override(self):
        """deep_merge không mutate override dict."""
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        override_copy = {"a": {"c": 2}}
        deep_merge(base, override)
        assert override == override_copy


# ============================================================================
# load_user_config tests
# ============================================================================


class TestLoadUserConfig:
    """Test cases cho load_user_config()."""

    def test_load_existing_config(self, tmp_path):
        """Đọc file tồn tại → return dict đúng."""
        config_content = {
            "render": {
                "defaults": {"sidebar_width": 280},
                "per_entity": {"Product": {"grid_columns": 4}},
                "infrastructure": {"docker_compose": {"api_replicas": 3}},
            }
        }
        config_file = tmp_path / USER_CONFIG_FILE
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        result = load_user_config(config_file.parent)

        assert result == config_content
        assert result["render"]["defaults"]["sidebar_width"] == 280

    def test_load_nonexistent_file_returns_empty(self, tmp_path):
        """File không tồn tại → return {} (backward compatible)."""
        result = load_user_config(tmp_path)
        assert result == {}

    def test_load_invalid_yaml_raises_error(self, tmp_path):
        """YAML invalid → throw MDC-CONFIG-003."""
        config_file = tmp_path / USER_CONFIG_FILE
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(":\n  invalid: yaml: [broken\n  - missing bracket")

        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError) as exc_info:
            load_user_config(tmp_path)

        assert exc_info.value.code.value == "MDC-CONFIG-003"

    def test_load_empty_file_returns_empty_dict(self, tmp_path):
        """File rỗng → return {}."""
        config_file = tmp_path / USER_CONFIG_FILE
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("")

        result = load_user_config(tmp_path)
        assert result == {}

    def test_load_config_with_nested_values(self, tmp_path):
        """Config có nested values → preserve structure."""
        config_content = {
            "render": {
                "infrastructure": {
                    "kubernetes": {
                        "resource_limits": {
                            "cpu": "500m",
                            "memory": "512Mi",
                        }
                    }
                }
            }
        }
        config_file = tmp_path / USER_CONFIG_FILE
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        result = load_user_config(tmp_path)
        assert result["render"]["infrastructure"]["kubernetes"]["resource_limits"]["cpu"] == "500m"

    def test_load_config_preserves_types(self, tmp_path):
        """Config preserve types (int, bool, string)."""
        config_content = {
            "render": {
                "defaults": {
                    "width": 280,
                    "enabled": True,
                    "label": "test",
                }
            }
        }
        config_file = tmp_path / USER_CONFIG_FILE
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        result = load_user_config(tmp_path)
        assert result["render"]["defaults"]["width"] == 280
        assert result["render"]["defaults"]["enabled"] is True
        assert result["render"]["defaults"]["label"] == "test"


# ============================================================================
# resolve_render_context tests
# ============================================================================


class TestResolveRenderContext:
    """Test cases cho resolve_render_context() — priority order."""

    def test_no_user_config_returns_entity_rc(self):
        """Không có user_config → return entity RC (EU-0.1 behavior)."""
        entity_rc = {"sidebar_width": 300}
        result = resolve_render_context("Product", entity_rc, {})
        assert result == {"sidebar_width": 300}

    def test_only_defaults_applied(self):
        """Chỉ có defaults → apply defaults."""
        entity_rc = {}
        user_config = {"render": {"defaults": {"sidebar_width": 280, "grid": 4}}}
        result = resolve_render_context("Product", entity_rc, user_config)
        assert result == {"sidebar_width": 280, "grid": 4}

    def test_per_entity_overrides_defaults(self):
        """Per_entity ghi đè defaults."""
        entity_rc = {}
        user_config = {
            "render": {
                "defaults": {"sidebar_width": 280, "grid": 4},
                "per_entity": {"Product": {"sidebar_width": 320}},
            }
        }
        result = resolve_render_context("Product", entity_rc, user_config)
        # per_entity override sidebar_width, defaults giữ grid
        assert result["sidebar_width"] == 320
        assert result["grid"] == 4

    def test_dsl_rc_overrides_all(self):
        """DSL render_context (entity_rc) priority cao nhất — ghi đè tất cả."""
        entity_rc = {"sidebar_width": 999}
        user_config = {
            "render": {
                "defaults": {"sidebar_width": 280, "grid": 4},
                "per_entity": {"Product": {"sidebar_width": 320}},
            }
        }
        result = resolve_render_context("Product", entity_rc, user_config)
        # DSL-level ghi đè cả defaults và per_entity
        assert result["sidebar_width"] == 999
        assert result["grid"] == 4

    def test_per_entity_deep_merge_preserves_defaults(self):
        """Per_entity deep merge — preserve nested keys từ defaults."""
        entity_rc = {}
        user_config = {
            "render": {
                "defaults": {
                    "list_view": {
                        "pagination_size": 20,
                        "sortable_columns": ["name"],
                        "filterable": True,
                    }
                },
                "per_entity": {
                    "Product": {
                        "list_view": {
                            "pagination_size": 25,
                        }
                    }
                },
            }
        }
        result = resolve_render_context("Product", entity_rc, user_config)
        assert result == {
            "list_view": {
                "pagination_size": 25,  # per_entity override
                "sortable_columns": ["name"],  # defaults preserved
                "filterable": True,  # defaults preserved
            }
        }

    def test_entity_not_in_per_entity_uses_defaults(self):
        """Entity không có trong per_entity → chỉ dùng defaults."""
        entity_rc = {}
        user_config = {
            "render": {
                "defaults": {"sidebar_width": 280},
                "per_entity": {"Order": {"sidebar_width": 400}},
            }
        }
        result = resolve_render_context("Product", entity_rc, user_config)
        # Product không có trong per_entity → dùng defaults
        assert result == {"sidebar_width": 280}

    def test_full_priority_chain(self):
        """Full priority chain: defaults → per_entity (deep) → DSL RC (deep)."""
        entity_rc = {"sidebar_width": 999, "theme": "light"}
        user_config = {
            "render": {
                "defaults": {
                    "sidebar_width": 280,
                    "grid": 4,
                    "list_view": {"size": 20, "sortable": True},
                },
                "per_entity": {
                    "Product": {
                        "sidebar_width": 320,
                        "list_view": {"size": 25},
                    }
                },
            }
        }
        result = resolve_render_context("Product", entity_rc, user_config)
        assert result == {
            "sidebar_width": 999,  # DSL RC wins
            "grid": 4,  # defaults preserved (not in per_entity or entity_rc)
            "list_view": {
                "size": 25,  # per_entity overrides defaults
                "sortable": True,  # defaults preserved (per_entity không có sortable)
            },
            "theme": "light",  # DSL RC added
        }

    def test_empty_entity_rc_still_merges_defaults_and_per_entity(self):
        """Entity RC rỗng → merge defaults + per_entity."""
        entity_rc = {}
        user_config = {
            "render": {
                "defaults": {"a": 1, "b": 2},
                "per_entity": {"Product": {"b": 20, "c": 30}},
            }
        }
        result = resolve_render_context("Product", entity_rc, user_config)
        assert result == {"a": 1, "b": 20, "c": 30}

    def test_missing_render_key_uses_defaults(self):
        """User config không có render key → giống như không có config."""
        entity_rc = {"x": 1}
        user_config = {"other_key": "value"}
        result = resolve_render_context("Product", entity_rc, user_config)
        assert result == {"x": 1}

    def test_infrastructure_not_in_per_entity_resolution(self):
        """resolve_render_context không xử lý infrastructure — chỉ defaults + per_entity + DSL."""
        entity_rc = {}
        user_config = {
            "render": {
                "defaults": {"width": 280},
                "infrastructure": {"docker": {"replicas": 3}},
            }
        }
        result = resolve_render_context("Product", entity_rc, user_config)
        # infrastructure không apply trong per_entity resolution
        assert result == {"width": 280}
        assert "infrastructure" not in result
