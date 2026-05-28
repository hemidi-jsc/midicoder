# coding: utf-8
"""
Tests cho CP39 recipes: basic_i18n_recipe, multitenant_i18n_recipe, RecipeOutput.
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp_full_i18n.recipes import RecipeOutput


# ============================================================================
# Test RecipeOutput
# ============================================================================


class TestRecipeOutput:
    """Tests cho RecipeOutput."""

    def test_recipe_output_creation(self):
        from midicoder.packs.cp_full_i18n.parser import I18nRuntimeIR

        output = RecipeOutput(
            name="test",
            description="Test recipe",
            ir=I18nRuntimeIR(),
        )
        assert output.name == "test"
        assert output.description == "Test recipe"
        assert isinstance(output.ir, I18nRuntimeIR)


# ============================================================================
# Test basic_i18n_recipe
# ============================================================================


class TestBasicI18nRecipe:
    """Tests cho basic_i18n_recipe."""

    def test_returns_recipe_output(self):
        from midicoder.packs.cp_full_i18n.recipes import basic_i18n_recipe

        result = basic_i18n_recipe()
        assert isinstance(result, RecipeOutput)

    def test_name_and_description(self):
        from midicoder.packs.cp_full_i18n.recipes import basic_i18n_recipe

        result = basic_i18n_recipe()
        assert result.name == "basic_i18n"
        assert "memory" in result.description.lower()

    def test_has_2_locales(self):
        from midicoder.packs.cp_full_i18n.recipes import basic_i18n_recipe

        result = basic_i18n_recipe()
        assert len(result.ir.locales) == 2

    def test_has_en_and_vi(self):
        from midicoder.packs.cp_full_i18n.recipes import basic_i18n_recipe

        result = basic_i18n_recipe()
        codes = {loc.code for loc in result.ir.locales}
        assert "en" in codes
        assert "vi" in codes

    def test_has_default_locale(self):
        from midicoder.packs.cp_full_i18n.recipes import basic_i18n_recipe

        result = basic_i18n_recipe()
        defaults = [loc for loc in result.ir.locales if loc.is_default]
        assert len(defaults) == 1
        assert defaults[0].code == "en"

    def test_has_translations(self):
        from midicoder.packs.cp_full_i18n.recipes import basic_i18n_recipe

        result = basic_i18n_recipe()
        assert len(result.ir.translations) > 0

    def test_has_multiple_namespaces(self):
        from midicoder.packs.cp_full_i18n.recipes import basic_i18n_recipe

        result = basic_i18n_recipe()
        namespaces = {t.namespace for t in result.ir.translations}
        assert "common" in namespaces
        assert "auth" in namespaces

    def test_has_memory_cache(self):
        from midicoder.packs.cp_full_i18n.recipes import basic_i18n_recipe
        from midicoder.packs.cp_full_i18n.models import CacheBackend

        result = basic_i18n_recipe()
        assert result.ir.cache_config is not None
        assert result.ir.cache_config.backend == CacheBackend.MEMORY

    def test_translations_cover_both_locales(self):
        from midicoder.packs.cp_full_i18n.recipes import basic_i18n_recipe

        result = basic_i18n_recipe()
        locales_in_translations = {t.locale for t in result.ir.translations}
        assert "en" in locales_in_translations
        assert "vi" in locales_in_translations


# ============================================================================
# Test multitenant_i18n_recipe
# ============================================================================


class TestMultitenantI18nRecipe:
    """Tests cho multitenant_i18n_recipe."""

    def test_returns_recipe_output(self):
        from midicoder.packs.cp_full_i18n.recipes import multitenant_i18n_recipe

        result = multitenant_i18n_recipe()
        assert isinstance(result, RecipeOutput)

    def test_name_and_description(self):
        from midicoder.packs.cp_full_i18n.recipes import multitenant_i18n_recipe

        result = multitenant_i18n_recipe()
        assert result.name == "multitenant_i18n"
        assert "Redis" in result.description or "redis" in result.description

    def test_has_3_locales(self):
        from midicoder.packs.cp_full_i18n.recipes import multitenant_i18n_recipe

        result = multitenant_i18n_recipe()
        assert len(result.ir.locales) == 3

    def test_has_en_vi_fr(self):
        from midicoder.packs.cp_full_i18n.recipes import multitenant_i18n_recipe

        result = multitenant_i18n_recipe()
        codes = {loc.code for loc in result.ir.locales}
        assert "en" in codes
        assert "vi" in codes
        assert "fr" in codes

    def test_has_redis_cache(self):
        from midicoder.packs.cp_full_i18n.recipes import multitenant_i18n_recipe
        from midicoder.packs.cp_full_i18n.models import CacheBackend

        result = multitenant_i18n_recipe()
        assert result.ir.cache_config is not None
        assert result.ir.cache_config.backend == CacheBackend.REDIS

    def test_has_tenant_translations(self):
        from midicoder.packs.cp_full_i18n.recipes import multitenant_i18n_recipe

        result = multitenant_i18n_recipe()
        tenant_translations = [t for t in result.ir.translations if t.tenant_id is not None]
        assert len(tenant_translations) > 0

    def test_has_fallback_locale(self):
        from midicoder.packs.cp_full_i18n.recipes import multitenant_i18n_recipe

        result = multitenant_i18n_recipe()
        vi = next((loc for loc in result.ir.locales if loc.code == "vi"), None)
        fr = next((loc for loc in result.ir.locales if loc.code == "fr"), None)
        assert vi is not None and vi.fallback_locale == "en"
        assert fr is not None and fr.fallback_locale == "en"
