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

from midicoder.packs.cp_full_i18n.models import (
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
    # CP29 merged exports
    "I18nParser",
]


# ===========================================================================
# CP29 — Key Extraction Parser (merged from cp29_multi_language)
# ===========================================================================


class I18nParser:
    """Parser chuyển MIR metadata thành I18nKeyset.

    Auto-extract i18n keys từ:
    - Entity fields: entity.{entity_snake}.field.{field_snake}
    - Commands: command.{command_snake}
    - Queries: query.{query_snake}
    - Events: event.{event_snake}
    """

    def parse_from_metadata(self, metadata: dict[str, Any] | None) -> "I18nKeyset":  # type: ignore[name-defined]
        """Parse MIR metadata và extract i18n keys.

        Args:
            metadata: Dict từ MIR chứa entities[], commands[], queries[], events[].

        Returns:
            I18nKeyset với các keys đã extract và sorted.
        """
        if metadata is None:
            from midicoder.packs.cp_full_i18n.models import I18nKeyset

            return I18nKeyset()

        from midicoder.packs.cp_full_i18n.models import I18nKeyset

        keyset = I18nKeyset()

        # Parse entity fields
        for entity in metadata.get("entities", []):
            keys = self._parse_entity(entity)
            for k in keys:
                keyset.add_key(k)

        # Parse commands
        for command in metadata.get("commands", []):
            k = self._parse_command(command)
            if k:
                keyset.add_key(k)

        # Parse queries
        for query in metadata.get("queries", []):
            k = self._parse_query(query)
            if k:
                keyset.add_key(k)

        # Parse events
        for event in metadata.get("events", []):
            k = self._parse_event(event)
            if k:
                keyset.add_key(k)

        return keyset

    def _parse_entity(self, entity: dict[str, Any]) -> list:  # type: ignore[type-arg]
        """Extract i18n keys từ entity và các field của nó."""
        from midicoder.packs.cp_full_i18n.models import I18nKey

        keys: list = []
        entity_id = entity.get("id", "")
        if not entity_id:
            return keys

        entity_snake = self._to_snake_case(entity_id)
        fields = entity.get("fields", [])

        for fld in fields:
            field_id = fld.get("id", "")
            if not field_id:
                continue

            field_snake = self._to_snake_case(field_id)
            key = f"entity.{entity_snake}.field.{field_snake}"
            description = fld.get("description", "")

            ikey = I18nKey(
                key=key,
                namespace="entity",
                entity_id=entity_id,
                category="field",
                path=field_id,
                description=description,
            )
            keys.append(ikey)

        return keys

    def _parse_command(self, command: dict[str, Any]) -> Any:  # type: ignore[type-arg]
        """Extract i18n key từ command."""
        from midicoder.packs.cp_full_i18n.models import I18nKey

        cmd_id = command.get("id", "")
        if not cmd_id:
            return None

        cmd_snake = self._to_snake_case(cmd_id)
        key = f"command.{cmd_snake}"
        description = command.get("description", "")

        return I18nKey(
            key=key,
            namespace="command",
            entity_id=cmd_id,
            category="action",
            description=description,
        )

    def _parse_query(self, query: dict[str, Any]) -> Any:  # type: ignore[type-arg]
        """Extract i18n key từ query."""
        from midicoder.packs.cp_full_i18n.models import I18nKey

        q_id = query.get("id", "")
        if not q_id:
            return None

        q_snake = self._to_snake_case(q_id)
        key = f"query.{q_snake}"
        description = query.get("description", "")

        return I18nKey(
            key=key,
            namespace="query",
            entity_id=q_id,
            category="action",
            description=description,
        )

    def _parse_event(self, event: dict[str, Any]) -> Any:  # type: ignore[type-arg]
        """Extract i18n key từ event."""
        from midicoder.packs.cp_full_i18n.models import I18nKey

        e_id = event.get("id", "")
        if not e_id:
            return None

        e_snake = self._to_snake_case(e_id)
        key = f"event.{e_snake}"
        description = event.get("description", "")

        return I18nKey(
            key=key,
            namespace="event",
            entity_id=e_id,
            category="action",
            description=description,
        )

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Chuyển PascalCase/camelCase sang snake_case."""
        import re

        s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        result = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s1).lower()
        result = re.sub(r"[-\s]+", "_", result)
        return result
