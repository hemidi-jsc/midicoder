# coding: utf-8
"""
Tests cho CP39 parser: parse_locales, parse_translations,
parse_cache_config, parse_to_ir, I18nRuntimeIR.
"""

from __future__ import annotations

import pytest

from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Test parse_locales
# ============================================================================


class TestParseLocales:
    """Tests cho parse_locales."""

    def test_parse_locales_primary_key(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_locales

        data = {
            "locales": [
                {"code": "en", "name": "English", "is_default": True, "currency_code": "USD"},
                {"code": "vi", "name": "Tiếng Việt", "date_format": "dd/MM/yyyy", "currency_code": "VND"},
            ]
        }
        result = parse_locales(data)
        assert len(result) == 2
        assert result[0].code == "en"
        assert result[0].is_default is True
        assert result[1].currency_code == "VND"

    def test_parse_locales_alt_key(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_locales

        data = {
            "supported_locales": [
                {"locale": "fr", "name": "Français", "default": False},
            ]
        }
        result = parse_locales(data)
        assert len(result) == 1
        assert result[0].code == "fr"

    def test_parse_locales_empty(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_locales

        data = {}
        result = parse_locales(data)
        assert len(result) == 0

    def test_parse_locales_defaults(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_locales
        from midicoder.emitters.core.cp39_i18n_runtime.models import PluralRule

        data = {"locales": [{"code": "en"}]}
        result = parse_locales(data)
        assert result[0].date_format == "dd/MM/yyyy"
        assert result[0].plural_rule == PluralRule.PLURAL
        assert result[0].is_default is False


# ============================================================================
# Test parse_translations
# ============================================================================


class TestParseTranslations:
    """Tests cho parse_translations."""

    def test_parse_translations_primary_key(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_translations

        data = {
            "translations": [
                {"key": "welcome", "namespace": "common", "locale": "vi", "value": "Chào mừng"},
                {"key": "login", "namespace": "auth", "locale": "vi", "value": "Đăng nhập"},
            ]
        }
        result = parse_translations(data)
        assert len(result) == 2
        assert result[0].key == "welcome"
        assert result[1].namespace == "auth"

    def test_parse_translations_alt_key(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_translations

        data = {
            "i18n_entries": [
                {"key": "test", "translation": "Test Value"},
            ]
        }
        result = parse_translations(data)
        assert len(result) == 1
        assert result[0].value == "Test Value"

    def test_parse_translations_empty(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_translations

        data = {}
        result = parse_translations(data)
        assert len(result) == 0

    def test_parse_translations_defaults(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_translations

        data = {"translations": [{"key": "test"}]}
        result = parse_translations(data)
        assert result[0].namespace == "common"
        assert result[0].locale == "en"

    def test_parse_translations_with_tenant(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_translations

        data = {
            "translations": [
                {"key": "welcome", "locale": "vi", "value": "Custom!", "tenant_id": "t1"},
            ]
        }
        result = parse_translations(data)
        assert result[0].tenant_id == "t1"


# ============================================================================
# Test parse_cache_config
# ============================================================================


class TestParseCacheConfig:
    """Tests cho parse_cache_config."""

    def test_parse_cache_config_primary(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_cache_config
        from midicoder.emitters.core.cp39_i18n_runtime.models import CacheBackend

        data = {
            "cache_config": {
                "backend": "redis",
                "ttl_seconds": 600,
                "max_size": 50000,
                "redis_url": "redis://localhost:6379/0",
            }
        }
        result = parse_cache_config(data)
        assert result is not None
        assert result.backend == CacheBackend.REDIS
        assert result.ttl_seconds == 600

    def test_parse_cache_config_alt_key(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_cache_config

        data = {"i18n_cache": {"backend": "memory", "ttl": 120}}
        result = parse_cache_config(data)
        assert result is not None
        assert result.ttl_seconds == 120

    def test_parse_cache_config_none(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_cache_config

        data = {}
        result = parse_cache_config(data)
        assert result is None


# ============================================================================
# Test parse_to_ir
# ============================================================================


class TestParseToIR:
    """Tests cho parse_to_ir."""

    def test_parse_to_ir_full(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_to_ir

        data = {
            "locales": [
                {"code": "en", "name": "English", "is_default": True},
                {"code": "vi", "name": "Tiếng Việt", "currency_code": "VND"},
            ],
            "translations": [
                {"key": "welcome", "locale": "vi", "value": "Chào mừng"},
            ],
            "cache_config": {
                "backend": "memory",
                "ttl_seconds": 300,
                "max_size": 5000,
            },
        }
        ir = parse_to_ir(data)
        assert len(ir.locales) == 2
        assert len(ir.translations) == 1
        assert ir.cache_config is not None
        assert ir.cache_config.ttl_seconds == 300

    def test_parse_to_ir_empty(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import parse_to_ir

        ir = parse_to_ir({})
        assert len(ir.locales) == 0
        assert len(ir.translations) == 0
        assert ir.cache_config is None


# ============================================================================
# Test I18nRuntimeIR
# ============================================================================


class TestI18nRuntimeIR:
    """Tests cho I18nRuntimeIR."""

    def test_ir_to_dict(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import I18nRuntimeIR
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleConfig, TranslationEntry, CacheConfig

        ir = I18nRuntimeIR(
            locales=[LocaleConfig(code="en", is_default=True)],
            translations=[TranslationEntry(key="test", locale="en", value="Test")],
            cache_config=CacheConfig(ttl_seconds=300),
        )
        d = ir.to_dict()
        assert len(d["locales"]) == 1
        assert len(d["translations"]) == 1
        assert d["cache_config"]["ttl_seconds"] == 300

    def test_ir_from_dict(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import I18nRuntimeIR

        data = {
            "locales": [
                {"code": "vi", "name": "Tiếng Việt", "is_default": False, "date_format": "dd/MM/yyyy", "plural_rule": "plural"}
            ],
            "translations": [
                {"key": "hello", "namespace": "common", "locale": "vi", "value": "Xin chào"}
            ],
            "cache_config": {"backend": "memory", "ttl_seconds": 300, "max_size": 10000, "redis_url": ""},
        }
        ir = I18nRuntimeIR.from_dict(data)
        assert len(ir.locales) == 1
        assert ir.locales[0].code == "vi"
        assert len(ir.translations) == 1
        assert ir.translations[0].value == "Xin chào"
        assert ir.cache_config is not None

    def test_ir_from_dict_no_cache(self):
        from midicoder.emitters.core.cp39_i18n_runtime.parser import I18nRuntimeIR

        data = {"locales": [], "translations": [], "cache_config": None}
        ir = I18nRuntimeIR.from_dict(data)
        assert ir.cache_config is None
