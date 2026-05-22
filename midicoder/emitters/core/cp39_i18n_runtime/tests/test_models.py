# coding: utf-8
"""
Tests cho CP39 models: LocaleConfig, TranslationEntry, DiscoverResult,
CacheConfig, TranslationStore, InMemoryTranslationStore,
LocaleFormatter, TranslationEngine, enums.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Test Error Codes
# ============================================================================


class TestCP39ErrorCodes:
    """Tests cho CP39 error codes."""

    def test_cp39_empty_locale_code_exists(self):
        assert hasattr(ErrorCode, "CP39_EMPTY_LOCALE_CODE")
        assert ErrorCode.CP39_EMPTY_LOCALE_CODE == "MDC-CP39-001"

    def test_cp39_invalid_locale_code_exists(self):
        assert hasattr(ErrorCode, "CP39_INVALID_LOCALE_CODE")
        assert ErrorCode.CP39_INVALID_LOCALE_CODE == "MDC-CP39-002"

    def test_cp39_empty_translation_key_exists(self):
        assert hasattr(ErrorCode, "CP39_EMPTY_TRANSLATION_KEY")
        assert ErrorCode.CP39_EMPTY_TRANSLATION_KEY == "MDC-CP39-003"

    def test_cp39_duplicate_locale_exists(self):
        assert hasattr(ErrorCode, "CP39_DUPLICATE_LOCALE")
        assert ErrorCode.CP39_DUPLICATE_LOCALE == "MDC-CP39-004"

    def test_cp39_duplicate_key_locale_exists(self):
        assert hasattr(ErrorCode, "CP39_DUPLICATE_KEY_LOCALE")
        assert ErrorCode.CP39_DUPLICATE_KEY_LOCALE == "MDC-CP39-005"

    def test_cp39_locale_not_found_exists(self):
        assert hasattr(ErrorCode, "CP39_LOCALE_NOT_FOUND")
        assert ErrorCode.CP39_LOCALE_NOT_FOUND == "MDC-CP39-006"

    def test_cp39_translation_not_found_exists(self):
        assert hasattr(ErrorCode, "CP39_TRANSLATION_NOT_FOUND")
        assert ErrorCode.CP39_TRANSLATION_NOT_FOUND == "MDC-CP39-007"

    def test_cp39_invalid_namespace_exists(self):
        assert hasattr(ErrorCode, "CP39_INVALID_NAMESPACE")
        assert ErrorCode.CP39_INVALID_NAMESPACE == "MDC-CP39-008"

    def test_cp39_cache_config_invalid_exists(self):
        assert hasattr(ErrorCode, "CP39_CACHE_CONFIG_INVALID")
        assert ErrorCode.CP39_CACHE_CONFIG_INVALID == "MDC-CP39-009"

    def test_cp39_template_not_found_exists(self):
        assert hasattr(ErrorCode, "CP39_TEMPLATE_NOT_FOUND")
        assert ErrorCode.CP39_TEMPLATE_NOT_FOUND == "MDC-CP39-010"

    def test_cp39_render_failed_exists(self):
        assert hasattr(ErrorCode, "CP39_RENDER_FAILED")
        assert ErrorCode.CP39_RENDER_FAILED == "MDC-CP39-011"

    def test_cp39_formatter_invalid_locale_exists(self):
        assert hasattr(ErrorCode, "CP39_FORMATTER_INVALID_LOCALE")
        assert ErrorCode.CP39_FORMATTER_INVALID_LOCALE == "MDC-CP39-012"

    def test_cp39_invalid_plural_rule_exists(self):
        assert hasattr(ErrorCode, "CP39_INVALID_PLURAL_RULE")
        assert ErrorCode.CP39_INVALID_PLURAL_RULE == "MDC-CP39-013"

    def test_cp39_tenant_translation_conflict_exists(self):
        assert hasattr(ErrorCode, "CP39_TENANT_TRANSLATION_CONFLICT")
        assert ErrorCode.CP39_TENANT_TRANSLATION_CONFLICT == "MDC-CP39-014"

    def test_cp39_discover_scan_failed_exists(self):
        assert hasattr(ErrorCode, "CP39_DISCOVER_SCAN_FAILED")
        assert ErrorCode.CP39_DISCOVER_SCAN_FAILED == "MDC-CP39-015"


# ============================================================================
# Test Enums
# ============================================================================


class TestCP39Enums:
    """Tests cho CP39 enums."""

    def test_plural_rule_singular(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import PluralRule
        assert PluralRule.SINGULAR.value == "singular"

    def test_plural_rule_plural(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import PluralRule
        assert PluralRule.PLURAL.value == "plural"

    def test_cache_backend_memory(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import CacheBackend
        assert CacheBackend.MEMORY.value == "memory"

    def test_cache_backend_redis(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import CacheBackend
        assert CacheBackend.REDIS.value == "redis"

    def test_discover_source_template(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import DiscoverSource
        assert DiscoverSource.TEMPLATE.value == "template"

    def test_discover_source_html(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import DiscoverSource
        assert DiscoverSource.HTML.value == "html"

    def test_discover_source_tsx(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import DiscoverSource
        assert DiscoverSource.TSX.value == "tsx"

    def test_discover_source_code(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import DiscoverSource
        assert DiscoverSource.CODE.value == "code"


# ============================================================================
# Test LocaleConfig
# ============================================================================


class TestLocaleConfig:
    """Tests cho LocaleConfig."""

    def test_locale_creation(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleConfig

        loc = LocaleConfig(code="vi", name="Tiếng Việt", is_default=True)
        assert loc.code == "vi"
        assert loc.is_default is True

    def test_locale_empty_code_raises(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleConfig

        with pytest.raises(MidicoderError):
            LocaleConfig(code="")

    def test_locale_invalid_code_raises(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleConfig

        with pytest.raises(MidicoderError):
            LocaleConfig(code="INVALID_CODE")

    def test_locale_with_region(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleConfig

        loc = LocaleConfig(code="en-US", name="English (US)")
        assert loc.code == "en-US"

    def test_locale_timestamps_auto_set(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleConfig

        loc = LocaleConfig(code="vi")
        assert loc.created_at is not None
        assert loc.updated_at is not None

    def test_locale_to_dict(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleConfig

        loc = LocaleConfig(code="vi", name="Tiếng Việt", currency_code="VND")
        d = loc.to_dict()
        assert d["code"] == "vi"
        assert d["currency_code"] == "VND"
        assert d["plural_rule"] == "plural"

    def test_locale_from_dict(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleConfig

        data = {
            "code": "fr",
            "name": "Français",
            "is_default": False,
            "date_format": "dd/MM/yyyy",
            "currency_code": "EUR",
            "plural_rule": "plural",
        }
        loc = LocaleConfig.from_dict(data)
        assert loc.code == "fr"
        assert loc.currency_code == "EUR"


# ============================================================================
# Test TranslationEntry
# ============================================================================


class TestTranslationEntry:
    """Tests cho TranslationEntry."""

    def test_translation_creation(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import TranslationEntry

        entry = TranslationEntry(key="welcome", namespace="common", locale="vi", value="Chào mừng")
        assert entry.key == "welcome"
        assert entry.namespace == "common"
        assert entry.locale == "vi"

    def test_translation_empty_key_raises(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import TranslationEntry

        with pytest.raises(MidicoderError):
            TranslationEntry(key="", namespace="common", locale="vi", value="test")

    def test_translation_invalid_namespace_raises(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import TranslationEntry

        with pytest.raises(MidicoderError):
            TranslationEntry(key="test", namespace="Invalid_NS!", locale="vi", value="test")

    def test_translation_with_tenant(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import TranslationEntry

        entry = TranslationEntry(key="welcome", locale="vi", value="Chào", tenant_id="tenant_1")
        assert entry.tenant_id == "tenant_1"

    def test_translation_to_dict(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import TranslationEntry

        entry = TranslationEntry(key="save", namespace="common", locale="en", value="Save")
        d = entry.to_dict()
        assert d["key"] == "save"
        assert d["namespace"] == "common"

    def test_translation_from_dict(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import TranslationEntry

        data = {
            "key": "cancel",
            "namespace": "common",
            "locale": "vi",
            "value": "Hủy",
            "tenant_id": None,
        }
        entry = TranslationEntry.from_dict(data)
        assert entry.key == "cancel"
        assert entry.value == "Hủy"


# ============================================================================
# Test DiscoverResult
# ============================================================================


class TestDiscoverResult:
    """Tests cho DiscoverResult."""

    def test_discover_result_creation(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import DiscoverResult

        r = DiscoverResult(key="btn_save", source_file="app.py", line_number=42, original_string="Save")
        assert r.key == "btn_save"
        assert r.line_number == 42

    def test_discover_result_to_dict(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import DiscoverResult

        r = DiscoverResult(key="test", original_string="Test String")
        d = r.to_dict()
        assert d["key"] == "test"
        assert d["original_string"] == "Test String"


# ============================================================================
# Test CacheConfig
# ============================================================================


class TestCacheConfig:
    """Tests cho CacheConfig."""

    def test_cache_config_default(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import CacheConfig

        cfg = CacheConfig()
        assert cfg.backend.value == "memory"
        assert cfg.ttl_seconds == 300

    def test_cache_config_redis(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import CacheConfig, CacheBackend

        cfg = CacheConfig(backend=CacheBackend.REDIS, redis_url="redis://localhost:6379/0")
        assert cfg.backend.value == "redis"

    def test_cache_config_invalid_ttl_raises(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import CacheConfig

        with pytest.raises(MidicoderError):
            CacheConfig(ttl_seconds=-1)

    def test_cache_config_redis_no_url_raises(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import CacheConfig, CacheBackend

        with pytest.raises(MidicoderError):
            CacheConfig(backend=CacheBackend.REDIS)

    def test_cache_config_to_dict(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import CacheConfig

        cfg = CacheConfig(ttl_seconds=600, max_size=5000)
        d = cfg.to_dict()
        assert d["ttl_seconds"] == 600
        assert d["max_size"] == 5000

    def test_cache_config_from_dict(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import CacheConfig

        data = {"backend": "redis", "ttl_seconds": 120, "max_size": 10000, "redis_url": "redis://localhost:6379/1"}
        cfg = CacheConfig.from_dict(data)
        assert cfg.ttl_seconds == 120


# ============================================================================
# Test InMemoryTranslationStore
# ============================================================================


class TestInMemoryTranslationStore:
    """Tests cho InMemoryTranslationStore."""

    def test_set_and_get(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import (
            InMemoryTranslationStore,
            TranslationEntry,
        )

        store = InMemoryTranslationStore()
        entry = TranslationEntry(key="welcome", locale="vi", value="Chào mừng")
        store.set(entry)
        result = store.get("welcome", "vi")
        assert result == "Chào mừng"

    def test_get_missing_returns_none(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import InMemoryTranslationStore

        store = InMemoryTranslationStore()
        assert store.get("nonexistent", "vi") is None

    def test_delete(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import (
            InMemoryTranslationStore,
            TranslationEntry,
        )

        store = InMemoryTranslationStore()
        store.set(TranslationEntry(key="test", locale="vi", value="Test"))
        assert store.delete("test", "vi") is True
        assert store.get("test", "vi") is None

    def test_delete_missing_returns_false(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import InMemoryTranslationStore

        store = InMemoryTranslationStore()
        assert store.delete("nonexistent", "vi") is False

    def test_list_by_locale(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import (
            InMemoryTranslationStore,
            TranslationEntry,
        )

        store = InMemoryTranslationStore()
        store.set(TranslationEntry(key="a", locale="vi", value="A"))
        store.set(TranslationEntry(key="b", locale="en", value="B"))
        entries = store.list_by_locale("vi")
        assert len(entries) == 1
        assert entries[0].key == "a"

    def test_missing_keys(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import (
            InMemoryTranslationStore,
            TranslationEntry,
        )

        store = InMemoryTranslationStore()
        store.set(TranslationEntry(key="welcome", locale="vi", value="Chào mừng"))
        missing = store.missing_keys("vi", ["welcome", "save", "cancel"])
        assert "welcome" not in missing
        assert "save" in missing


# ============================================================================
# Test LocaleFormatter
# ============================================================================


class TestLocaleFormatter:
    """Tests cho LocaleFormatter."""

    def test_format_date_vi(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleFormatter, LocaleConfig

        formatter = LocaleFormatter(locales=[LocaleConfig(code="vi", date_format="dd/MM/yyyy")])
        result = formatter.format_date(datetime(2026, 5, 22, tzinfo=timezone.utc), "vi")
        assert result == "22/05/2026"

    def test_format_date_us(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleFormatter, LocaleConfig

        formatter = LocaleFormatter(locales=[LocaleConfig(code="en", date_format="MM/dd/yyyy")])
        result = formatter.format_date(datetime(2026, 5, 22, tzinfo=timezone.utc), "en")
        assert result == "05/22/2026"

    def test_format_number_vi(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleFormatter, LocaleConfig

        formatter = LocaleFormatter(locales=[LocaleConfig(code="vi")])
        result = formatter.format_number(1000000.0, "vi")
        assert result == "1.000.000"

    def test_format_number_en(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleFormatter, LocaleConfig

        formatter = LocaleFormatter(locales=[LocaleConfig(code="en")])
        result = formatter.format_number(1000000.0, "en")
        assert result == "1,000,000"

    def test_format_currency_vi(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleFormatter, LocaleConfig

        formatter = LocaleFormatter(locales=[LocaleConfig(code="vi", currency_code="₫")])
        result = formatter.format_currency(1000000.0, "vi")
        assert result == "1.000.000₫"

    def test_format_currency_us(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleFormatter, LocaleConfig

        formatter = LocaleFormatter(locales=[LocaleConfig(code="en", currency_code="$")])
        result = formatter.format_currency(1000000.0, "en")
        assert result == "$1,000,000.00"

    def test_format_invalid_locale_raises(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleFormatter

        formatter = LocaleFormatter()
        with pytest.raises(MidicoderError):
            formatter.format_date(datetime.now(timezone.utc), "xx")

    def test_format_relative_time(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleFormatter, LocaleConfig

        formatter = LocaleFormatter(locales=[LocaleConfig(code="vi"), LocaleConfig(code="en")])
        now = datetime.now(timezone.utc)
        result = formatter.format_relative_time(now, "vi")
        assert "vừa" in result.lower() or "giây" in result.lower()

    def test_pluralize_vi(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleFormatter, LocaleConfig

        formatter = LocaleFormatter(locales=[LocaleConfig(code="vi")])
        assert formatter.pluralize(1, "vi") == "plural"
        assert formatter.pluralize(5, "vi") == "plural"

    def test_pluralize_en(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleFormatter, LocaleConfig

        formatter = LocaleFormatter(locales=[LocaleConfig(code="en")])
        assert formatter.pluralize(1, "en") == "singular"
        assert formatter.pluralize(5, "en") == "plural"

    def test_add_locale(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import LocaleFormatter, LocaleConfig

        formatter = LocaleFormatter()
        formatter.add_locale(LocaleConfig(code="fr", date_format="dd/MM/yyyy"))
        result = formatter.format_date(datetime(2026, 1, 5, tzinfo=timezone.utc), "fr")
        assert "05" in result


# ============================================================================
# Test TranslationEngine
# ============================================================================


class TestTranslationEngine:
    """Tests cho TranslationEngine."""

    def test_translate_global(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import (
            TranslationEngine,
            TranslationEntry,
            InMemoryTranslationStore,
        )

        store = InMemoryTranslationStore()
        store.set(TranslationEntry(key="welcome", locale="vi", value="Chào mừng"))
        engine = TranslationEngine(store=store)
        result = engine.translate("welcome", "vi")
        assert result == "Chào mừng"

    def test_translate_tenant_override(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import (
            TranslationEngine,
            TranslationEntry,
            InMemoryTranslationStore,
        )

        store = InMemoryTranslationStore()
        store.set(TranslationEntry(key="welcome", locale="vi", value="Chào mừng"))
        store.set(TranslationEntry(key="welcome", locale="vi", value="Chào mừng bạn!", tenant_id="t1"))
        engine = TranslationEngine(store=store)
        result = engine.translate("welcome", "vi", tenant_id="t1")
        assert result == "Chào mừng bạn!"

    def test_translate_fallback_to_key(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import TranslationEngine

        engine = TranslationEngine()
        result = engine.translate("nonexistent", "vi")
        assert result == "nonexistent"

    def test_translate_fallback_chain(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import (
            TranslationEngine,
            TranslationEntry,
            LocaleConfig,
            InMemoryTranslationStore,
        )

        store = InMemoryTranslationStore()
        # Chỉ có translation tiếng Anh
        store.set(TranslationEntry(key="welcome", locale="en", value="Welcome"))
        # French fallback sang English
        locales = [
            LocaleConfig(code="fr", fallback_locale="en"),
            LocaleConfig(code="en"),
        ]
        engine = TranslationEngine(store=store, locales=locales)
        result = engine.translate("welcome", "fr")
        assert result == "Welcome"

    def test_add_translation(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import (
            TranslationEngine,
            TranslationEntry,
        )

        engine = TranslationEngine()
        engine.add_translation(TranslationEntry(key="new_key", locale="vi", value="Giá trị mới"))
        result = engine.translate("new_key", "vi")
        assert result == "Giá trị mới"

    def test_add_bulk(self):
        from midicoder.emitters.core.cp39_i18n_runtime.models import (
            TranslationEngine,
            TranslationEntry,
        )

        engine = TranslationEngine()
        engine.add_bulk([
            TranslationEntry(key="a", locale="vi", value="A"),
            TranslationEntry(key="b", locale="vi", value="B"),
        ])
        assert engine.translate("a", "vi") == "A"
        assert engine.translate("b", "vi") == "B"
