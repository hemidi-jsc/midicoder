"""
Test key extraction end-to-end — từ MIR metadata → i18n keys → bundles.

Kiểm tra pipeline hoàn chỉnh: parser + recipes kết hợp.
"""

import pytest

from midicoder.emitters.core.cp29_multi_language.parser import I18nParser
from midicoder.emitters.core.cp29_multi_language.recipes import (
    auto_generate_i18n_from_mir,
    generate_i18n_bundles,
)


class TestKeyExtractionE2E:
    """Kiểm tra pipeline extract keys từ MIR metadata hoàn chỉnh."""

    def test_extract_from_commerce_domain(self):
        """Extract i18n keys từ domain thương mại điển hình."""
        metadata = {
            "entities": [
                {
                    "id": "Product",
                    "description": "A product in the catalog",
                    "fields": [
                        {"id": "name", "type": "string", "description": "Product name"},
                        {"id": "sku", "type": "string", "description": "Stock keeping unit"},
                        {"id": "price", "type": "decimal", "description": "Unit price"},
                        {"id": "description", "type": "text", "description": "Product description"},
                    ],
                },
                {
                    "id": "Order",
                    "description": "A customer order",
                    "fields": [
                        {"id": "order_number", "type": "string", "description": "Order number"},
                        {"id": "total", "type": "decimal", "description": "Order total"},
                        {"id": "status", "type": "string", "description": "Order status"},
                    ],
                },
            ],
            "commands": [
                {"id": "CreateOrder", "description": "Create a new order"},
                {"id": "CancelOrder", "description": "Cancel an order"},
                {"id": "UpdateProductPrice", "description": "Update product price"},
            ],
            "queries": [
                {"id": "ListProducts", "description": "List all products"},
                {"id": "GetOrderDetail", "description": "Get order details"},
            ],
            "events": [
                {"id": "OrderCreated", "description": "Order was created"},
                {"id": "OrderCancelled", "description": "Order was cancelled"},
            ],
        }

        result = auto_generate_i18n_from_mir(metadata)

        # 4 + 3 = 7 entity field keys
        # 3 command keys
        # 2 query keys
        # 2 event keys
        # Total = 14
        assert len(result.keys) == 14

        key_ids = [k.key for k in result.keys]

        # Check entity keys
        assert "entity.product.field.name" in key_ids
        assert "entity.product.field.sku" in key_ids
        assert "entity.product.field.price" in key_ids
        assert "entity.product.field.description" in key_ids
        assert "entity.order.field.order_number" in key_ids
        assert "entity.order.field.total" in key_ids
        assert "entity.order.field.status" in key_ids

        # Check command keys
        assert "command.create_order" in key_ids
        assert "command.cancel_order" in key_ids
        assert "command.update_product_price" in key_ids

        # Check query keys
        assert "query.list_products" in key_ids
        assert "query.get_order_detail" in key_ids

        # Check event keys
        assert "event.order_created" in key_ids
        assert "event.order_cancelled" in key_ids

        # Check bundles
        assert len(result.bundles) == 2

        en_bundle = result.get_bundle_by_locale("en")
        assert en_bundle is not None
        assert en_bundle.get_translation("entity.product.field.name") == "Product name"
        assert en_bundle.get_translation("command.create_order") == "Create a new order"

        vi_bundle = result.get_bundle_by_locale("vi")
        assert vi_bundle is not None
        assert vi_bundle.get_translation("entity.product.field.name") == ""

    def test_keys_are_deterministic(self):
        """Cùng input → cùng thứ tự keys output."""
        metadata = {
            "entities": [
                {
                    "id": "Zebra",
                    "fields": [
                        {"id": "z", "type": "string", "description": "Z"},
                    ],
                },
                {
                    "id": "Alpha",
                    "fields": [
                        {"id": "a", "type": "string", "description": "A"},
                    ],
                },
            ],
            "commands": [
                {"id": "Zulu", "description": "Z command"},
                {"id": "Alpha", "description": "A command"},
            ],
        }

        r1 = auto_generate_i18n_from_mir(metadata)
        r2 = auto_generate_i18n_from_mir(metadata)

        keys1 = [k.key for k in r1.keys]
        keys2 = [k.key for k in r2.keys]

        assert keys1 == keys2
        assert keys1 == sorted(keys1)

    def test_namespace_distribution(self):
        """Kiểm tra phân bố namespace của keys."""
        metadata = {
            "entities": [
                {
                    "id": "Test",
                    "fields": [
                        {"id": "f1", "type": "string", "description": "Field 1"},
                        {"id": "f2", "type": "string", "description": "Field 2"},
                        {"id": "f3", "type": "string", "description": "Field 3"},
                    ],
                }
            ],
            "commands": [
                {"id": "CmdA", "description": "Command A"},
                {"id": "CmdB", "description": "Command B"},
            ],
            "queries": [
                {"id": "QryA", "description": "Query A"},
            ],
            "events": [
                {"id": "EvtA", "description": "Event A"},
            ],
        }

        result = auto_generate_i18n_from_mir(metadata)

        namespaces = {k.namespace for k in result.keys}
        assert "entity" in namespaces
        assert "command" in namespaces
        assert "query" in namespaces
        assert "event" in namespaces

        entity_keys = [k for k in result.keys if k.namespace == "entity"]
        command_keys = [k for k in result.keys if k.namespace == "command"]
        query_keys = [k for k in result.keys if k.namespace == "query"]
        event_keys = [k for k in result.keys if k.namespace == "event"]

        assert len(entity_keys) == 3
        assert len(command_keys) == 2
        assert len(query_keys) == 1
        assert len(event_keys) == 1

    def test_bundle_serialization(self):
        """Kiểm tra serialize bundle sang dict."""
        metadata = {
            "entities": [
                {
                    "id": "User",
                    "fields": [
                        {"id": "name", "type": "string", "description": "User name"},
                    ],
                }
            ]
        }

        result = auto_generate_i18n_from_mir(metadata)
        en_bundle = result.get_bundle_by_locale("en")
        assert en_bundle is not None

        d = en_bundle.to_dict()
        assert d["locale"] == "en"
        assert d["keys"]["entity.user.field.name"] == "User name"

    def test_keyset_serialization_round_trip(self):
        """Kiểm tra serialize/deserialize keyset."""
        metadata = {
            "entities": [
                {
                    "id": "Item",
                    "fields": [
                        {"id": "code", "type": "string", "description": "Item code"},
                    ],
                }
            ],
            "commands": [
                {"id": "CreateItem", "description": "Create item"},
            ],
        }

        result = auto_generate_i18n_from_mir(metadata)
        serialized = result.to_dict()
        deserialized = type(result).from_dict(serialized)

        assert len(deserialized.keys) == len(result.keys)
        for orig, new in zip(result.keys, deserialized.keys):
            assert orig.key == new.key
            assert orig.description == new.description

    def test_snake_case_conversion_edge_cases(self):
        """Kiểm tra snake_case conversion với các edge case."""
        parser = I18nParser()

        # CamelCase
        assert parser._to_snake_case("CreateOrder") == "create_order"
        # PascalCase
        assert parser._to_snake_case("OrderItem") == "order_item"
        # Already snake_case
        assert parser._to_snake_case("order_item") == "order_item"
        # Single word
        assert parser._to_snake_case("Order") == "order"
        # With numbers
        assert parser._to_snake_case("OrderItem2") == "order_item2"
        # HTTP prefix — regex gộp chuỗi chữ hoa liên tiếp
        assert parser._to_snake_case("HTTPResponse") == "http_response"
