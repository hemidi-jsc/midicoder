# coding: utf-8
"""
CP39 — i18n/L10n Runtime.

Public API barrel export.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from midicoder.packs.cp39_i18n_runtime.models import (
    CacheBackend,
    CacheConfig,
    DiscoverResult,
    DiscoverSource,
    InMemoryTranslationStore,
    LocaleConfig,
    LocaleFormatter,
    PluralRule,
    TranslationEngine,
    TranslationEntry,
    TranslationStore,
)
from midicoder.packs.cp39_i18n_runtime.parser import (
    I18nRuntimeIR,
    parse_cache_config,
    parse_locales,
    parse_translations,
    parse_to_ir,
)
from midicoder.packs.cp39_i18n_runtime.recipes import (
    RecipeOutput,
    basic_i18n_recipe,
    multitenant_i18n_recipe,
)
from midicoder.packs.cp39_i18n_runtime.fastapi import (
    FastAPII18nRuntimeEmitter,
)
from midicoder.packs.cp39_i18n_runtime.nestjs import (
    NestJSI18nRuntimeEmitter,
)
from midicoder.packs.cp39_i18n_runtime.angular import (
    AngularI18nRuntimeEmitter,
)
from midicoder.packs.cp39_i18n_runtime.react import (
    ReactI18nRuntimeEmitter,
)

__all__ = [
    # Models - Enums
    "PluralRule",
    "CacheBackend",
    "DiscoverSource",
    # Models - Core
    "LocaleConfig",
    "TranslationEntry",
    "DiscoverResult",
    "CacheConfig",
    # Models - Storage
    "TranslationStore",
    "InMemoryTranslationStore",
    # Models - Engine
    "LocaleFormatter",
    "TranslationEngine",
    # Parser
    "I18nRuntimeIR",
    "parse_locales",
    "parse_translations",
    "parse_cache_config",
    "parse_to_ir",
    # Recipes
    "RecipeOutput",
    "basic_i18n_recipe",
    "multitenant_i18n_recipe",
    # Emitters
    "FastAPII18nRuntimeEmitter",
    "NestJSI18nRuntimeEmitter",
    "AngularI18nRuntimeEmitter",
    "ReactI18nRuntimeEmitter",
]
