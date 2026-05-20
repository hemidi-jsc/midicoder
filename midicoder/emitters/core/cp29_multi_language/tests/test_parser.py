"""
Test cho parser của CP29 — I18nParser.

Kiểm tra:
- Parse MIR metadata (entities, commands, queries, events) → I18nKeyset
- Xử lý input None, empty, invalid
- Auto-extract keys từ field descriptions
"""

import pytest

from midicoder.emitters.core.cp29_multi_language.parser import I18nParser
from midicoder.errors import MidicoderError


class TestI18nParser:
    """Kiểm tra I18nParser.parse_from_metadata()."""

    def test_parse_none_metadata_returns_empty(self):
        """Input None trả về keyset trống."""
        parser = I18nParser()
        result = parser.parse_from_metadata(None)
        assert len(result.keys) == 0

    def test_parse_empty_dict_returns_empty(self):
        """Input dict trống trả về keyset trống."""
        parser = I18nParser()
        result = parser.parse_from_metadata({})
        assert len(result.keys) == 0

    def test_parse_entities_extracts_field_keys(self):
        """Parse entities và extract keys cho từng field."""
        metadata = {
            "entities": [
                {
                    "id": "Customer",
                    "description": "A customer in the system",
                    "fields": [
                        {"id": "name", "type": "string", "description": "Customer full name"},
                        {"id": "email", "type": "string", "description": "Customer email"},
                    ],
                }
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 2
        key_ids = [k.key for k in result.keys]
        assert "entity.customer.field.name" in key_ids
        assert "entity.customer.field.email" in key_ids

    def test_parse_commands_extracts_keys(self):
        """Parse commands và extract keys."""
        metadata = {
            "commands": [
                {
                    "id": "CreateOrder",
                    "description": "Create a new order",
                }
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 1
        assert result.keys[0].key == "command.create_order"
        assert result.keys[0].description == "Create a new order"

    def test_parse_queries_extracts_keys(self):
        """Parse queries và extract keys."""
        metadata = {
            "queries": [
                {
                    "id": "ListOrders",
                    "description": "List all orders",
                }
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 1
        assert result.keys[0].key == "query.list_orders"

    def test_parse_events_extracts_keys(self):
        """Parse events và extract keys."""
        metadata = {
            "events": [
                {
                    "id": "OrderCreated",
                    "description": "Order was created successfully",
                }
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 1
        assert result.keys[0].key == "event.order_created"

    def test_parse_all_categories_combined(self):
        """Parse tất cả categories cùng lúc."""
        metadata = {
            "entities": [
                {
                    "id": "Product",
                    "description": "A product",
                    "fields": [
                        {"id": "name", "type": "string", "description": "Product name"},
                        {"id": "price", "type": "decimal", "description": "Product price"},
                    ],
                }
            ],
            "commands": [
                {"id": "CreateProduct", "description": "Create product"},
            ],
            "queries": [
                {"id": "ListProducts", "description": "List products"},
            ],
            "events": [
                {"id": "ProductCreated", "description": "Product created"},
            ],
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        # 2 field keys + 1 command + 1 query + 1 event = 5
        assert len(result.keys) == 5

        key_ids = [k.key for k in result.keys]
        assert "entity.product.field.name" in key_ids
        assert "entity.product.field.price" in key_ids
        assert "command.create_product" in key_ids
        assert "query.list_products" in key_ids
        assert "event.product_created" in key_ids

    def test_parse_multiple_entities(self):
        """Parse nhiều entities."""
        metadata = {
            "entities": [
                {
                    "id": "Customer",
                    "fields": [
                        {"id": "name", "type": "string", "description": "Customer name"},
                    ],
                },
                {
                    "id": "Order",
                    "fields": [
                        {"id": "total", "type": "decimal", "description": "Order total"},
                    ],
                },
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 2
        key_ids = [k.key for k in result.keys]
        assert "entity.customer.field.name" in key_ids
        assert "entity.order.field.total" in key_ids

    def test_parse_entity_with_no_fields(self):
        """Entity không có fields không sinh key nào."""
        metadata = {
            "entities": [
                {"id": "EmptyEntity", "description": "No fields"}
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 0

    def test_parse_entity_with_empty_fields(self):
        """Entity có fields list trống không sinh key."""
        metadata = {
            "entities": [
                {"id": "EmptyFields", "fields": []}
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 0

    def test_parse_entity_with_empty_id(self):
        """Entity có id trống (missing) không sinh key — cover branch return."""
        metadata = {
            "entities": [
                {"description": "No ID"},
                {"id": ""},
                {"id": "ValidEntity", "fields": [{"id": "x", "type": "string"}]},
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 1
        assert result.keys[0].entity_id == "ValidEntity"

    def test_parse_entity_field_with_empty_id(self):
        """Field có id trống (continue branch) — skip field đó."""
        metadata = {
            "entities": [
                {
                    "id": "Test",
                    "fields": [
                        {"id": "", "type": "string"},
                        {"type": "string"},
                        {"id": "valid", "type": "string", "description": "Valid field"},
                    ],
                }
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 1
        assert result.keys[0].path == "valid"

    def test_parse_keys_are_sorted(self):
        """Các keys được sắp xếp theo alphabet (deterministic)."""
        metadata = {
            "entities": [
                {
                    "id": "Zebra",
                    "fields": [
                        {"id": "z", "type": "string", "description": "Z field"},
                    ],
                },
                {
                    "id": "Alpha",
                    "fields": [
                        {"id": "a", "type": "string", "description": "A field"},
                    ],
                },
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        key_ids = [k.key for k in result.keys]
        assert key_ids == sorted(key_ids)

    def test_parse_command_without_description(self):
        """Command không có description vẫn sinh key."""
        metadata = {
            "commands": [
                {"id": "DoSomething"},
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 1
        assert result.keys[0].key == "command.do_something"
        assert result.keys[0].description == ""

    def test_to_snake_case_pascal(self):
        """Convert PascalCase sang snake_case."""
        parser = I18nParser()
        assert parser._to_snake_case("CustomerName") == "customer_name"

    def test_to_snake_case_camel(self):
        """Convert camelCase sang snake_case."""
        parser = I18nParser()
        assert parser._to_snake_case("customerName") == "customer_name"

    def test_to_snake_case_already_snake(self):
        """SnakeCase giữ nguyên."""
        parser = I18nParser()
        assert parser._to_snake_case("customer_name") == "customer_name"

    def test_parse_field_without_description(self):
        """Field không có description, dùng field name."""
        metadata = {
            "entities": [
                {
                    "id": "Test",
                    "fields": [
                        {"id": "someField", "type": "string"},
                    ],
                }
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 1
        assert result.keys[0].key == "entity.test.field.some_field"

    def test_parse_preserves_entity_case_in_key(self):
        """Entity ID PascalCase được convert sang snake_case trong key."""
        metadata = {
            "entities": [
                {
                    "id": "OrderItem",
                    "fields": [
                        {"id": "quantity", "type": "int", "description": "Item quantity"},
                    ],
                }
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 1
        assert result.keys[0].key == "entity.order_item.field.quantity"

    def test_parse_command_with_empty_id(self):
        """Command có id trống không sinh key (return None)."""
        metadata = {
            "commands": [
                {"id": "", "description": "Empty"},
                {"description": "No id key"},
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)
        assert len(result.keys) == 0

    def test_parse_query_with_empty_id(self):
        """Query có id trống không sinh key (return None)."""
        metadata = {
            "queries": [
                {"id": ""},
                {},
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)
        assert len(result.keys) == 0

    def test_parse_event_with_empty_id(self):
        """Event có id trống không sinh key (return None)."""
        metadata = {
            "events": [
                {"id": ""},
                {"id": "ValidEvent", "description": "Valid"},
            ]
        }
        parser = I18nParser()
        result = parser.parse_from_metadata(metadata)

        assert len(result.keys) == 1
        assert result.keys[0].key == "event.valid_event"
