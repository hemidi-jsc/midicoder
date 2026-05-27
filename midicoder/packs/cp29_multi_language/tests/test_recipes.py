"""
Test cho recipes của CP29 — Multi-Language Support Generator.

Kiểm tra:
- generate_language_profile
- generate_i18n_bundles
- auto_generate_i18n_from_mir
"""

import pytest

from midicoder.packs.cp29_multi_language.recipes import (
    auto_generate_i18n_from_mir,
    generate_i18n_bundles,
    generate_language_profile,
)
from midicoder.packs.cp29_multi_language.models import I18nKeyset


class TestGenerateLanguageProfile:
    """Kiểm tra generate_language_profile."""

    def test_default_profile(self):
        """Tạo profile mặc định."""
        profile = generate_language_profile()
        assert profile.id == "default"
        assert profile.locales == ["en", "vi"]
        assert profile.default_locale == "en"

    def test_custom_locales(self):
        """Tạo profile với custom locales."""
        profile = generate_language_profile(
            locales=["en", "vi", "ja"],
            default_locale="ja",
        )
        assert profile.locales == ["en", "vi", "ja"]
        assert profile.default_locale == "ja"


class TestGenerateI18nBundles:
    """Kiểm tra generate_i18n_bundles."""

    def _create_keyset(self) -> I18nKeyset:
        """Tạo keyset test với 1 key."""
        from midicoder.packs.cp29_multi_language.models import I18nKey

        keyset = I18nKeyset()
        keyset.add_key(
            I18nKey(
                key="entity.customer.field.name",
                namespace="entity",
                entity_id="Customer",
                category="field",
                description="Customer full name",
            )
        )
        return keyset

    def test_en_bundle_has_description(self):
        """Bundle en có description từ DSL."""
        keyset = self._create_keyset()
        bundles = generate_i18n_bundles(keyset, locales=["en"])
        bundle = bundles[0]

        assert bundle.locale == "en"
        assert bundle.get_translation("entity.customer.field.name") == "Customer full name"

    def test_vi_bundle_has_empty_description(self):
        """Bundle vi có description trống để user điền."""
        keyset = self._create_keyset()
        bundles = generate_i18n_bundles(keyset, locales=["en", "vi"])
        vi_bundle = bundles[1]

        assert vi_bundle.locale == "vi"
        assert vi_bundle.get_translation("entity.customer.field.name") == ""

    def test_empty_keyset_returns_empty_bundles(self):
        """Keyset trống trả về bundle với 0 keys."""
        keyset = I18nKeyset()
        bundles = generate_i18n_bundles(keyset)
        assert len(bundles) == 2  # en + vi
        assert len(bundles[0].keys) == 0
        assert len(bundles[1].keys) == 0


class TestAutoGenerateI18nFromMir:
    """Kiểm tra auto_generate_i18n_from_mir (master recipe)."""

    def test_none_metadata_returns_empty(self):
        """Input None trả về keyset trống."""
        result = auto_generate_i18n_from_mir(None)
        assert len(result.keys) == 0
        assert len(result.bundles) == 0

    def test_empty_metadata_returns_empty(self):
        """Input dict trống trả về keyset trống."""
        result = auto_generate_i18n_from_mir({})
        assert len(result.keys) == 0

    def test_full_metadata_generates_keys_and_bundles(self):
        """Input đầy đủ → generate keys + bundles."""
        metadata = {
            "entities": [
                {
                    "id": "Customer",
                    "fields": [
                        {"id": "name", "type": "string", "description": "Customer name"},
                        {"id": "email", "type": "string", "description": "Customer email"},
                    ],
                }
            ],
            "commands": [
                {"id": "CreateCustomer", "description": "Create a customer"},
            ],
            "queries": [
                {"id": "ListCustomers", "description": "List customers"},
            ],
        }
        result = auto_generate_i18n_from_mir(metadata)

        # 2 field keys + 1 command + 1 query = 4
        assert len(result.keys) == 4
        # 2 bundles (en + vi)
        assert len(result.bundles) == 2

        # Check en bundle
        en_bundle = result.get_bundle_by_locale("en")
        assert en_bundle is not None
        assert en_bundle.get_translation("entity.customer.field.name") == "Customer name"

        # Check vi bundle
        vi_bundle = result.get_bundle_by_locale("vi")
        assert vi_bundle is not None
        assert vi_bundle.get_translation("entity.customer.field.name") == ""

    def test_deterministic_output(self):
        """Cùng input → cùng output (deterministic)."""
        metadata = {
            "entities": [
                {
                    "id": "Order",
                    "fields": [
                        {"id": "total", "type": "decimal", "description": "Order total"},
                    ],
                }
            ],
            "commands": [
                {"id": "CreateOrder", "description": "Create order"},
            ],
        }
        result1 = auto_generate_i18n_from_mir(metadata)
        result2 = auto_generate_i18n_from_mir(metadata)

        keys1 = [k.key for k in result1.keys]
        keys2 = [k.key for k in result2.keys]
        assert keys1 == keys2

    def test_no_commands_queries_events(self):
        """Chỉ có entities, không có commands/queries/events."""
        metadata = {
            "entities": [
                {
                    "id": "Product",
                    "fields": [
                        {"id": "name", "type": "string", "description": "Product name"},
                    ],
                }
            ]
        }
        result = auto_generate_i18n_from_mir(metadata)
        assert len(result.keys) == 1
        assert result.keys[0].key == "entity.product.field.name"

    def test_only_commands(self):
        """Chỉ có commands, không có entities."""
        metadata = {
            "commands": [
                {"id": "ProcessPayment", "description": "Process payment"},
                {"id": "RefundPayment", "description": "Refund payment"},
            ]
        }
        result = auto_generate_i18n_from_mir(metadata)
        assert len(result.keys) == 2

        key_ids = [k.key for k in result.keys]
        assert "command.process_payment" in key_ids
        assert "command.refund_payment" in key_ids
