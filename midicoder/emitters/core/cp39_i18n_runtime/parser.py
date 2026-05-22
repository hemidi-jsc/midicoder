# coding: utf-8
"""
Mô-đun parser cho CP39 — i18n/L10n Runtime.

Parse DSL dict (từ contract YAML) sang I18nRuntimeIR — Intermediate Representation
cho locales, translations, và cache config.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp39_i18n_runtime.models import (
    CacheBackend,
    CacheConfig,
    LocaleConfig,
    PluralRule,
    TranslationEntry,
)


@dataclass
class I18nRuntimeIR:
    """Intermediate Representation cho CP39.

    Gom tập tất cả cấu hình i18n runtime từ DSL, bao gồm locales,
    translations, và cache config.

    Attributes:
        locales: Danh sách locale configs
        translations: Danh sách translation entries
        cache_config: Cấu hình cache
    """
    locales: list[LocaleConfig] = field(default_factory=list)
    translations: list[TranslationEntry] = field(default_factory=list)
    cache_config: CacheConfig | None = None

    def to_dict(self) -> dict[str, Any]:
        """Chuyển I18nRuntimeIR sang dict."""
        return {
            "locales": [loc.to_dict() for loc in self.locales],
            "translations": [t.to_dict() for t in self.translations],
            "cache_config": self.cache_config.to_dict() if self.cache_config else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "I18nRuntimeIR":
        """Tạo I18nRuntimeIR từ dict."""
        locales = [LocaleConfig.from_dict(l) for l in data.get("locales", [])]
        translations = [TranslationEntry.from_dict(t) for t in data.get("translations", [])]
        cache_data = data.get("cache_config")
        cache_config = CacheConfig.from_dict(cache_data) if cache_data else None
        return cls(locales=locales, translations=translations, cache_config=cache_config)


def parse_locales(data: dict[str, Any]) -> list[LocaleConfig]:
    """Parse danh sách locales từ DSL dict.

    Args:
        data: DSL dict với key 'locales' hoặc 'supported_locales'

    Returns:
        Danh sách LocaleConfig
    """
    raw = data.get("locales", data.get("supported_locales", []))
    locales = []
    for loc in raw:
        locales.append(LocaleConfig(
            code=loc.get("code", loc.get("locale", "")),
            name=loc.get("name", ""),
            is_default=loc.get("is_default", loc.get("default", False)),
            date_format=loc.get("date_format", "dd/MM/yyyy"),
            number_format=loc.get("number_format", ""),
            currency_code=loc.get("currency_code", loc.get("currency", "")),
            plural_rule=PluralRule(loc.get("plural_rule", "plural")),
            fallback_locale=loc.get("fallback_locale"),
        ))
    return locales


def parse_translations(data: dict[str, Any]) -> list[TranslationEntry]:
    """Parse danh sách translations từ DSL dict.

    Args:
        data: DSL dict với key 'translations' hoặc 'i18n_entries'

    Returns:
        Danh sách TranslationEntry
    """
    raw = data.get("translations", data.get("i18n_entries", []))
    entries = []
    for t in raw:
        entries.append(TranslationEntry(
            key=t.get("key", ""),
            namespace=t.get("namespace", "common"),
            locale=t.get("locale", "en"),
            value=t.get("value", t.get("translation", "")),
            tenant_id=t.get("tenant_id"),
        ))
    return entries


def parse_cache_config(data: dict[str, Any]) -> CacheConfig | None:
    """Parse cache config từ DSL dict.

    Args:
        data: DSL dict với key 'cache_config' hoặc 'i18n_cache'

    Returns:
        CacheConfig hoặc None nếu không có config
    """
    raw = data.get("cache_config", data.get("i18n_cache"))
    if not raw:
        return None

    return CacheConfig(
        backend=CacheBackend(raw.get("backend", "memory")),
        ttl_seconds=raw.get("ttl_seconds", raw.get("ttl", 300)),
        max_size=raw.get("max_size", 10000),
        redis_url=raw.get("redis_url", ""),
    )


def parse_to_ir(data: dict[str, Any]) -> I18nRuntimeIR:
    """Parse DSL dict thành I18nRuntimeIR.

    Args:
        data: DSL dict với locales, translations, cache_config

    Returns:
        I18nRuntimeIR gom tập tất cả parsed data
    """
    locales = parse_locales(data)
    translations = parse_translations(data)
    cache_config = parse_cache_config(data)
    return I18nRuntimeIR(locales=locales, translations=translations, cache_config=cache_config)


__all__ = [
    "I18nRuntimeIR",
    "parse_locales",
    "parse_translations",
    "parse_cache_config",
    "parse_to_ir",
]
