"""
Test cho models của CP29 — Multi-Language Support Generator.

Kiểm tra:
- I18nKey: tạo hợp lệ, validation key trống, validation format sai
- LanguageProfile: tạo hợp lệ, validation locale, duplicate locale
- I18nBundle: tạo hợp lệ, empty keys, missing translation
- I18nKeyset: CRUD, duplicate detection, serialization
"""

import pytest
from dataclasses import dataclass, field
from typing import Optional

from midicoder.packs.cp29_multi_language.models import (
    I18nKey,
    LanguageProfile,
    I18nBundle,
    I18nKeyset,
)
from midicoder.errors import MidicoderError, ErrorCode


class TestI18nKey:
    """Kiểm tra dataclass I18nKey."""

    def test_create_valid_key_entity_field(self):
        """Tạo key hợp lệ cho entity field."""
        key = I18nKey(
            key="entity.customer.field.name",
            namespace="entity",
            entity_id="Customer",
            category="field",
            path="name",
            description="Customer full name",
        )
        assert key.key == "entity.customer.field.name"
        assert key.namespace == "entity"
        assert key.category == "field"

    def test_create_valid_key_command(self):
        """Tạo key hợp lệ cho command."""
        key = I18nKey(
            key="command.create_order",
            namespace="command",
            entity_id="CreateOrder",
            category="action",
            description="Create a new order",
        )
        assert key.key == "command.create_order"

    def test_create_valid_key_query(self):
        """Tạo key hợp lệ cho query."""
        key = I18nKey(
            key="query.list_orders",
            namespace="query",
            entity_id="ListOrders",
            category="action",
            description="List all orders",
        )
        assert key.key == "query.list_orders"

    def test_create_valid_key_event(self):
        """Tạo key hợp lệ cho event."""
        key = I18nKey(
            key="event.order_created",
            namespace="event",
            entity_id="OrderCreated",
            category="action",
            description="Order was created",
        )
        assert key.key == "event.order_created"

    def test_empty_key_raises_error(self):
        """Key trống phải raise MDC-CP29-006."""
        with pytest.raises(MidicoderError) as exc_info:
            I18nKey(
                key="",
                namespace="entity",
                entity_id="Test",
                category="field",
                description="test",
            )
        assert exc_info.value.code == ErrorCode.CP29_EMPTY_KEY

    def test_whitespace_key_raises_error(self):
        """Key chỉ chứa khoảng trắng phải raise MDC-CP29-006."""
        with pytest.raises(MidicoderError) as exc_info:
            I18nKey(
                key="   ",
                namespace="entity",
                entity_id="Test",
                category="field",
                description="test",
            )
        assert exc_info.value.code == ErrorCode.CP29_EMPTY_KEY

    def test_invalid_namespace_raises_error(self):
        """Namespace không hợp lệ phải raise MDC-CP29-007."""
        with pytest.raises(MidicoderError) as exc_info:
            I18nKey(
                key="invalid.test.key",
                namespace="invalid_namespace",
                entity_id="Test",
                category="field",
                description="test",
            )
        assert exc_info.value.code == ErrorCode.CP29_INVALID_KEY_FORMAT

    def test_optional_fields_default(self):
        """Các field optional mặc định là None."""
        key = I18nKey(
            key="entity.test.field.id",
            namespace="entity",
            entity_id="Test",
            category="field",
            description="test id",
        )
        assert key.path is None

    def test_key_dotted_format(self):
        """Key format phải có dấu chấm phân tách."""
        key = I18nKey(
            key="entity.customer.field.email",
            namespace="entity",
            entity_id="Customer",
            category="field",
            path="email",
            description="Customer email address",
        )
        parts = key.key.split(".")
        assert len(parts) >= 3
        assert parts[0] == "entity"


class TestLanguageProfile:
    """Kiểm tra dataclass LanguageProfile."""

    def test_create_valid_profile(self):
        """Tạo profile hợp lệ với 2 locale."""
        profile = LanguageProfile(
            id="default",
            locales=["en", "vi"],
            default_locale="en",
            fallback_chain=["en"],
        )
        assert profile.id == "default"
        assert len(profile.locales) == 2
        assert profile.default_locale == "en"

    def test_empty_profile_id_raises_error(self):
        """Profile ID trống phải raise MDC-CP29-009."""
        with pytest.raises(MidicoderError) as exc_info:
            LanguageProfile(
                id="",
                locales=["en"],
                default_locale="en",
            )
        assert exc_info.value.code == ErrorCode.CP29_EMPTY_PROFILE_ID

    def test_empty_locales_raises_error(self):
        """Danh sách locale trống phải raise MDC-CP29-001."""
        with pytest.raises(MidicoderError) as exc_info:
            LanguageProfile(
                id="test",
                locales=[],
                default_locale="en",
            )
        assert exc_info.value.code == ErrorCode.CP29_INVALID_LOCALE

    def test_default_locale_not_in_locales_raises_error(self):
        """Default locale không nằm trong locales phải raise MDC-CP29-001."""
        with pytest.raises(MidicoderError) as exc_info:
            LanguageProfile(
                id="test",
                locales=["en", "vi"],
                default_locale="fr",
            )
        assert exc_info.value.code == ErrorCode.CP29_INVALID_LOCALE

    def test_duplicate_locale_raises_error(self):
        """Duplicate locale phải raise MDC-CP29-010."""
        with pytest.raises(MidicoderError) as exc_info:
            LanguageProfile(
                id="test",
                locales=["en", "en", "vi"],
                default_locale="en",
            )
        assert exc_info.value.code == ErrorCode.CP29_DUPLICATE_LOCALE

    def test_fallback_chain_defaults_to_default_locale(self):
        """Fallback chain mặc định lấy từ default_locale."""
        profile = LanguageProfile(
            id="test",
            locales=["en", "vi"],
            default_locale="en",
        )
        assert "en" in profile.fallback_chain

    def test_single_locale(self):
        """Profile chỉ 1 locale."""
        profile = LanguageProfile(
            id="single",
            locales=["en"],
            default_locale="en",
        )
        assert len(profile.locales) == 1


class TestI18nBundle:
    """Kiểm tra dataclass I18nBundle."""

    def test_create_valid_bundle(self):
        """Tạo bundle hợp lệ với keys."""
        keys = [
            I18nKey(
                key="entity.customer.field.name",
                namespace="entity",
                entity_id="Customer",
                category="field",
                description="Customer name",
            )
        ]
        bundle = I18nBundle(
            locale="en",
            keys=keys,
        )
        assert bundle.locale == "en"
        assert len(bundle.keys) == 1

    def test_create_bundle_empty_keys(self):
        """Tạo bundle với danh sách keys trống."""
        bundle = I18nBundle(
            locale="vi",
            keys=[],
        )
        assert bundle.locale == "vi"
        assert len(bundle.keys) == 0

    def test_empty_locale_raises_error(self):
        """Locale trống phải raise MDC-CP29-001."""
        keys = [
            I18nKey(
                key="test.key",
                namespace="entity",
                entity_id="Test",
                category="field",
                description="test",
            )
        ]
        with pytest.raises(MidicoderError) as exc_info:
            I18nBundle(
                locale="",
                keys=keys,
            )
        assert exc_info.value.code == ErrorCode.CP29_INVALID_LOCALE

    def test_get_translation_existing_key(self):
        """Lấy translation của key có tồn tại."""
        keys = [
            I18nKey(
                key="entity.customer.field.name",
                namespace="entity",
                entity_id="Customer",
                category="field",
                description="Customer name",
            )
        ]
        bundle = I18nBundle(locale="en", keys=keys)
        result = bundle.get_translation("entity.customer.field.name")
        assert result == "Customer name"

    def test_get_translation_missing_key(self):
        """Lấy translation của key không tồn tại trả về None."""
        keys = [
            I18nKey(
                key="entity.customer.field.name",
                namespace="entity",
                entity_id="Customer",
                category="field",
                description="Customer name",
            )
        ]
        bundle = I18nBundle(locale="en", keys=keys)
        result = bundle.get_translation("nonexistent.key")
        assert result is None

    def test_to_dict(self):
        """Serialize bundle sang dict."""
        keys = [
            I18nKey(
                key="entity.customer.field.name",
                namespace="entity",
                entity_id="Customer",
                category="field",
                description="Customer name",
            )
        ]
        bundle = I18nBundle(locale="en", keys=keys)
        d = bundle.to_dict()
        assert d["locale"] == "en"
        assert len(d["keys"]) == 1
        assert d["keys"]["entity.customer.field.name"] == "Customer name"


class TestI18nKeyset:
    """Kiểm tra collection class I18nKeyset."""

    def _create_key(self, key: str, entity_id: str = "Test") -> I18nKey:
        """Helper tạo I18nKey hợp lệ."""
        return I18nKey(
            key=key,
            namespace="entity",
            entity_id=entity_id,
            category="field",
            description=f"Description for {key}",
        )

    def test_create_empty_keyset(self):
        """Tạo keyset trống."""
        keyset = I18nKeyset()
        assert len(keyset.keys) == 0
        assert len(keyset.bundles) == 0

    def test_add_key(self):
        """Thêm key vào keyset."""
        keyset = I18nKeyset()
        k = self._create_key("entity.customer.field.name", "Customer")
        keyset.add_key(k)
        assert len(keyset.keys) == 1
        assert keyset.keys[0].key == "entity.customer.field.name"

    def test_get_key_by_id(self):
        """Lấy key theo ID."""
        keyset = I18nKeyset()
        k = self._create_key("entity.customer.field.name", "Customer")
        keyset.add_key(k)
        result = keyset.get_key_by_id("entity.customer.field.name")
        assert result is not None
        assert result.key == "entity.customer.field.name"

    def test_get_key_by_id_not_found(self):
        """Lấy key không tồn tại trả về None."""
        keyset = I18nKeyset()
        result = keyset.get_key_by_id("nonexistent")
        assert result is None

    def test_duplicate_key_raises_error(self):
        """Thêm key trùng phải raise MDC-CP29-004."""
        keyset = I18nKeyset()
        k = self._create_key("entity.test.field.id", "Test")
        keyset.add_key(k)
        with pytest.raises(MidicoderError) as exc_info:
            keyset.add_key(k)
        assert exc_info.value.code == ErrorCode.CP29_KEY_CONFLICT

    def test_add_bundle(self):
        """Thêm bundle vào keyset."""
        keyset = I18nKeyset()
        k = self._create_key("entity.test.field.name", "Test")
        bundle = I18nBundle(locale="en", keys=[k])
        keyset.add_bundle(bundle)
        assert len(keyset.bundles) == 1
        assert keyset.bundles[0].locale == "en"

    def test_get_bundle_by_locale(self):
        """Lấy bundle theo locale."""
        keyset = I18nKeyset()
        k = self._create_key("entity.test.field.name", "Test")
        bundle = I18nBundle(locale="vi", keys=[k])
        keyset.add_bundle(bundle)
        result = keyset.get_bundle_by_locale("vi")
        assert result is not None
        assert result.locale == "vi"

    def test_get_bundle_not_found(self):
        """Lấy bundle không tồn tại trả về None."""
        keyset = I18nKeyset()
        result = keyset.get_bundle_by_locale("ja")
        assert result is None

    def test_has_duplicate_keys(self):
        """Kiểm tra duplicate keys."""
        keyset = I18nKeyset()
        k1 = self._create_key("entity.a.field.id", "A")
        k2 = self._create_key("entity.b.field.id", "B")
        keyset.add_key(k1)
        keyset.add_key(k2)
        assert not keyset.has_duplicate_keys()

    def test_to_dict(self):
        """Serialize keyset sang dict."""
        keyset = I18nKeyset()
        k = self._create_key("entity.test.field.id", "Test")
        keyset.add_key(k)
        d = keyset.to_dict()
        assert len(d["keys"]) == 1
        assert len(d["bundles"]) == 0

    def test_from_dict(self):
        """Deserialize dict thành keyset."""
        data = {
            "keys": [
                {
                    "key": "entity.test.field.id",
                    "namespace": "entity",
                    "entity_id": "Test",
                    "category": "field",
                    "description": "Test id",
                }
            ],
            "bundles": [],
        }
        keyset = I18nKeyset.from_dict(data)
        assert len(keyset.keys) == 1
        assert keyset.keys[0].key == "entity.test.field.id"

    def test_keys_sorted(self):
        """Các keys trong keyset được sắp xếp theo alphabet."""
        keyset = I18nKeyset()
        k3 = self._create_key("entity.z.field.name", "Z")
        k1 = self._create_key("entity.a.field.name", "A")
        k2 = self._create_key("entity.m.field.name", "M")
        keyset.add_key(k3)
        keyset.add_key(k1)
        keyset.add_key(k2)
        key_ids = [k.key for k in keyset.keys]
        assert key_ids == sorted(key_ids)
