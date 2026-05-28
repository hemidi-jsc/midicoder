# coding: utf-8
"""
CP39 — i18n/L10n Runtime (merged with CP29 Multi-Language Support).

Public API barrel export.

Tác giả: Midicoder Team
Version: 2.0.0
"""

from midicoder.packs.cp_full_i18n.models import (
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
    # CP29 merged models
    I18nBundle,
    I18nKey,
    I18nKeyset,
    LanguageProfile,
)
from midicoder.packs.cp_full_i18n.parser import (
    I18nRuntimeIR,
    parse_cache_config,
    parse_locales,
    parse_translations,
    parse_to_ir,
    # CP29 merged parser
    I18nParser,
)
from midicoder.packs.cp_full_i18n.recipes import (
    RecipeOutput,
    basic_i18n_recipe,
    multitenant_i18n_recipe,
    # CP29 merged recipes
    auto_generate_i18n_from_mir,
    generate_i18n_bundles,
    generate_language_profile,
)
from midicoder.packs.cp_full_i18n.fastapi import (
    FastAPII18nRuntimeEmitter,
)
from midicoder.packs.cp_full_i18n.nestjs import (
    NestJSI18nRuntimeEmitter,
)
from midicoder.packs.cp_full_i18n.angular import (
    AngularI18nRuntimeEmitter,
)
from midicoder.packs.cp_full_i18n.react import (
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
    # CP29 Models
    "I18nKey",
    "I18nKeyset",
    "I18nBundle",
    "LanguageProfile",
    # Parser
    "I18nRuntimeIR",
    "parse_locales",
    "parse_translations",
    "parse_cache_config",
    "parse_to_ir",
    # CP29 Parser
    "I18nParser",
    # Recipes
    "RecipeOutput",
    "basic_i18n_recipe",
    "multitenant_i18n_recipe",
    # CP29 Recipes
    "auto_generate_i18n_from_mir",
    "generate_language_profile",
    "generate_i18n_bundles",
    # Emitters
    "FastAPII18nRuntimeEmitter",
    "NestJSI18nRuntimeEmitter",
    "AngularI18nRuntimeEmitter",
    "ReactI18nRuntimeEmitter",
]
