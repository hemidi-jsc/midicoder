# coding: utf-8
"""
Tests cho CP37 recipes: simple_flags_recipe, ab_testing_recipe, dynamic_config_recipe.
"""

from __future__ import annotations

from midicoder.packs.cp37_feature_flags.parser import FeatureFlagIR
from midicoder.packs.cp37_feature_flags.recipes import (
    RecipeOutput,
    ab_testing_recipe,
    dynamic_config_recipe,
    simple_flags_recipe,
)


class TestSimpleFlagsRecipe:
    """Tests cho simple_flags_recipe."""

    def test_simple_flags_recipe(self):
        result = simple_flags_recipe()
        assert result.name == "simple_flags"
        assert len(result.ir.flags) >= 2
        assert len(result.ir.configs) >= 1

    def test_recipe_output_has_ir(self):
        result = simple_flags_recipe()
        assert isinstance(result.ir, FeatureFlagIR)

    def test_recipe_has_description(self):
        result = simple_flags_recipe()
        assert isinstance(result, RecipeOutput)
        assert result.description
        assert "flag" in result.description.lower() or "on/off" in result.description.lower()

    def test_flags_have_correct_keys(self):
        result = simple_flags_recipe()
        keys = [f.flag_key for f in result.ir.flags]
        assert "dark_mode" in keys
        assert "new_checkout_flow" in keys
        assert "advanced_search" in keys

    def test_configs_have_cache_settings(self):
        result = simple_flags_recipe()
        config_keys = [c.config_key for c in result.ir.configs]
        assert "feature_flags.cache_ttl" in config_keys


class TestABTestingRecipe:
    """Tests cho ab_testing_recipe."""

    def test_ab_testing_recipe(self):
        result = ab_testing_recipe()
        assert result.name == "ab_testing"
        assert len(result.ir.experiments) >= 1
        assert len(result.ir.experiments[0].variants) >= 2

    def test_recipe_has_experiments(self):
        result = ab_testing_recipe()
        assert isinstance(result.ir, FeatureFlagIR)
        assert len(result.ir.experiments) >= 2

    def test_experiments_have_correct_keys(self):
        result = ab_testing_recipe()
        keys = [e.experiment_key for e in result.ir.experiments]
        assert "checkout_button_color" in keys
        assert "pricing_display" in keys

    def test_has_engine_flag(self):
        result = ab_testing_recipe()
        keys = [f.flag_key for f in result.ir.flags]
        assert "ab_experiment_engine" in keys

    def test_has_assignment_config(self):
        result = ab_testing_recipe()
        config_keys = [c.config_key for c in result.ir.configs]
        assert "ab_testing.assignment_cache_ttl" in config_keys


class TestDynamicConfigRecipe:
    """Tests cho dynamic_config_recipe."""

    def test_dynamic_config_recipe(self):
        result = dynamic_config_recipe()
        assert result.name == "dynamic_config"
        assert len(result.ir.configs) >= 3

    def test_has_global_configs(self):
        result = dynamic_config_recipe()
        from midicoder.packs.cp37_feature_flags.models import ConfigScope

        global_configs = [c for c in result.ir.configs if c.scope == ConfigScope.GLOBAL]
        assert len(global_configs) >= 3

    def test_has_tenant_config(self):
        result = dynamic_config_recipe()
        from midicoder.packs.cp37_feature_flags.models import ConfigScope

        tenant_configs = [c for c in result.ir.configs if c.scope == ConfigScope.TENANT]
        assert len(tenant_configs) >= 1

    def test_has_environment_config(self):
        result = dynamic_config_recipe()
        from midicoder.packs.cp37_feature_flags.models import ConfigScope

        env_configs = [c for c in result.ir.configs if c.scope == ConfigScope.ENVIRONMENT]
        assert len(env_configs) >= 2

    def test_has_sync_flag(self):
        result = dynamic_config_recipe()
        keys = [f.flag_key for f in result.ir.flags]
        assert "dynamic_config_realtime_sync" in keys

    def test_config_values_correct(self):
        result = dynamic_config_recipe()
        rate_limit = next(c for c in result.ir.configs if c.config_key == "app.rate_limit.requests_per_minute")
        assert rate_limit.value == 1000
