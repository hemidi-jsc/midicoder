# coding: utf-8
"""
Test cho CP43 parser — VersioningParser.
"""

import pytest
import yaml

from midicoder.errors import MidicoderError
from midicoder.packs.cp43_versioning.parser import VersioningParser
from midicoder.packs.cp43_versioning.models import (
    OperationType,
    VersionConfig,
    VersioningCollection,
)


class TestVersioningParser:
    """Test cho VersioningParser."""

    def setup_method(self) -> None:
        """Setup parser trước mỗi test."""
        self.parser = VersioningParser()

    def test_parse_empty_string(self) -> None:
        """Kiểm tra parse string rỗng trả về empty collection."""
        result = self.parser.parse("")
        assert isinstance(result, VersioningCollection)
        assert len(result.configs) == 0
        assert len(result.history_records) == 0

    def test_parse_none_string(self) -> None:
        """Kiểm tra parse None trả về empty collection."""
        result = self.parser.parse("")
        assert len(result.configs) == 0

    def test_parse_yaml_only_comments(self) -> None:
        """Kiểm tra parse YAML chỉ có comments trả về empty collection."""
        yaml_str = "# comment only\n# another comment"
        result = self.parser.parse(yaml_str)
        assert len(result.configs) == 0

    def test_parse_invalid_yaml_raises(self) -> None:
        """Kiểm tra parse YAML không hợp lệ raise MidicoderError."""
        yaml_str = "invalid: yaml: content: ["
        with pytest.raises(MidicoderError):
            self.parser.parse(yaml_str)

    def test_parse_non_dict_yaml_raises(self) -> None:
        """Kiểm tra parse YAML không phải dict raise MidicoderError."""
        yaml_str = "- just a list"
        with pytest.raises(MidicoderError):
            self.parser.parse(yaml_str)

    def test_parse_single_entity_config(self) -> None:
        """Kiểm tra parse config cho 1 entity."""
        yaml_str = """
versioning:
  entities:
    - entity_type: "Order"
      enable_versioning: true
      enable_soft_delete: true
      max_versions: 10
"""
        result = self.parser.parse(yaml_str)
        assert len(result.configs) == 1
        config = result.configs[0]
        assert config.entity_type == "Order"
        assert config.enable_versioning is True
        assert config.enable_soft_delete is True
        assert config.max_versions == 10

    def test_parse_multiple_entity_configs(self) -> None:
        """Kiểm tra parse config cho nhiều entities."""
        yaml_str = """
versioning:
  entities:
    - entity_type: "Order"
      enable_soft_delete: true
    - entity_type: "Product"
      enable_soft_delete: false
      max_versions: 5
    - entity_type: "Customer"
      enable_history: false
"""
        result = self.parser.parse(yaml_str)
        assert len(result.configs) == 3
        assert result.configs[0].entity_type == "Order"
        assert result.configs[1].entity_type == "Product"
        assert result.configs[1].enable_soft_delete is False
        assert result.configs[2].entity_type == "Customer"
        assert result.configs[2].enable_history is False

    def test_parse_config_with_all_options(self) -> None:
        """Kiểm tra parse config với đầy đủ options."""
        yaml_str = """
versioning:
  entities:
    - entity_type: "Order"
      enable_versioning: true
      enable_soft_delete: true
      enable_history: true
      enable_audit_integration: true
      max_versions: 100
      history_retention_days: 365
      snapshot_fields: ["status", "total"]
      exclude_fields: ["password"]
"""
        result = self.parser.parse(yaml_str)
        config = result.configs[0]
        assert config.entity_type == "Order"
        assert config.max_versions == 100
        assert config.history_retention_days == 365
        assert config.snapshot_fields == ["status", "total"]
        assert config.exclude_fields == ["password"]

    def test_parse_missing_entity_type_raises(self) -> None:
        """Kiểm tra parse config thiếu entity_type raise MidicoderError."""
        yaml_str = """
versioning:
  entities:
    - enable_versioning: true
"""
        with pytest.raises(MidicoderError):
            self.parser.parse(yaml_str)

    def test_parse_history_records(self) -> None:
        """Kiểm tra parse history records."""
        yaml_str = """
history_records:
  - entity_type: "Order"
    entity_id: "order_123"
    version: 1
    snapshot: {"status": "pending"}
    operation: "CREATE"
    created_by: "user_1"
  - entity_type: "Order"
    entity_id: "order_123"
    version: 2
    snapshot: {"status": "confirmed"}
    operation: "UPDATE"
    created_by: "user_2"
"""
        result = self.parser.parse(yaml_str)
        assert len(result.history_records) == 2
        assert result.history_records[0].version == 1
        assert result.history_records[0].operation == OperationType.CREATE
        assert result.history_records[1].version == 2
        assert result.history_records[1].operation == OperationType.UPDATE

    def test_parse_invalid_operation_raises(self) -> None:
        """Kiểm tra parse operation không hợp lệ raise MidicoderError."""
        yaml_str = """
history_records:
  - entity_type: "Order"
    entity_id: "o1"
    version: 1
    snapshot: {}
    operation: "INVALID_OP"
    created_by: "system"
"""
        with pytest.raises(MidicoderError):
            self.parser.parse(yaml_str)

    def test_parse_combined_config_and_history(self) -> None:
        """Kiểm tra parse cả config và history cùng lúc."""
        yaml_str = """
versioning:
  entities:
    - entity_type: "Order"
      enable_versioning: true
history_records:
  - entity_type: "Order"
    entity_id: "o1"
    version: 1
    snapshot: {}
    operation: "CREATE"
    created_by: "system"
"""
        result = self.parser.parse(yaml_str)
        assert len(result.configs) == 1
        assert len(result.history_records) == 1


class TestVersioningParserFromMetadata:
    """Test cho parse_from_metadata."""

    def setup_method(self) -> None:
        """Setup parser trước mỗi test."""
        self.parser = VersioningParser()

    def test_parse_empty_metadata(self) -> None:
        """Kiểm tra parse metadata rỗng trả về empty collection."""
        result = self.parser.parse_from_metadata({})
        assert len(result.configs) == 0

    def test_parse_single_entity(self) -> None:
        """Kiểm tra parse 1 entity từ metadata."""
        metadata = {
            "entities": [
                {"id": "Order", "fields": [{"name": "total", "type": "int"}]}
            ]
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.configs) == 1
        assert result.configs[0].entity_type == "Order"
        assert result.configs[0].enable_versioning is True

    def test_parse_multiple_entities(self) -> None:
        """Kiểm tra parse nhiều entities từ metadata."""
        metadata = {
            "entities": [
                {"id": "Order"},
                {"id": "Product"},
                {"id": "Customer"},
            ]
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.configs) == 3
        assert result.configs[0].entity_type == "Order"
        assert result.configs[1].entity_type == "Product"
        assert result.configs[2].entity_type == "Customer"

    def test_parse_entity_with_name_fallback(self) -> None:
        """Kiểm tra parse entity dùng 'name' làm fallback khi không có 'id'."""
        metadata = {
            "entities": [
                {"name": "Invoice", "fields": []}
            ]
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.configs) == 1
        assert result.configs[0].entity_type == "Invoice"

    def test_parse_entity_without_id_or_name_skipped(self) -> None:
        """Kiểm tra entity không có id cũng như name bị skip."""
        metadata = {
            "entities": [
                {"fields": []},
                {"id": "Valid"},
            ]
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.configs) == 1
        assert result.configs[0].entity_type == "Valid"

    def test_parse_with_non_dict_entities(self) -> None:
        """Kiểm tra parse entities không phải dict bị skip."""
        metadata = {
            "entities": [
                "string_entity",
                123,
                {"id": "Valid"},
            ]
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.configs) == 1
        assert result.configs[0].entity_type == "Valid"
