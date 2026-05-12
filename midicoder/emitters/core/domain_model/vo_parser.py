"""
Value Object Parser Module.

Module này cung cấp ValueObjectParser để parse Value Object DSL YAML:
- Parse YAML → ValueObject models
- Validate fields, types, và required keys
- Support inheritance (extends)
- Error handling với MidicoderError

Sử dụng:
    from midicoder.emitters.core.domain_model import ValueObjectParser

    parser = ValueObjectParser()
    vos = parser.parse(yaml_string)
    # vos: list[ValueObject]

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import yaml
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

from .vo_models import ValueObject, VOField, VOFieldType


# ============================================================================
# Valid Field Types
# ============================================================================

VALID_FIELD_TYPES = {ft.value for ft in VOFieldType}


# ============================================================================
# ValueObjectParser Class
# ============================================================================

class ValueObjectParser:
    """
    Parser cho Value Object DSL YAML.

    Parse YAML string thành list của ValueObject objects với validation.

    Usage:
        parser = ValueObjectParser()
        vos = parser.parse(yaml_string)
    """

    def __init__(self) -> None:
        """Khởi tạo ValueObjectParser."""
        pass

    def parse(self, yaml_content: str) -> list[ValueObject]:
        """
        Parse YAML content thành list ValueObject objects.

        Args:
            yaml_content: YAML string chứa value object definitions

        Returns:
            List của ValueObject objects

        Raises:
            MidicoderError: Nếu YAML không hợp lệ hoặc validation failed
        """
        # Parse YAML
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.DSL_YAML_PARSE_ERROR,
                error=str(e),
            )

        # Validate root structure
        if not data or "value_objects" not in data:
            EM.raise_error(
                ErrorCode.CP01_VALUE_OBJECT_NOT_FOUND,
                reason="Missing 'value_objects' key in YAML",
            )

        # Parse each value object
        vos = []
        for vo_def in data.get("value_objects", []):
            vo = self._parse_value_object(vo_def)
            vos.append(vo)

        return vos

    def _parse_value_object(self, vo_def: dict[str, Any]) -> ValueObject:
        """
        Parse value object definition dict thành ValueObject object.

        Args:
            vo_def: ValueObject definition dict

        Returns:
            ValueObject object

        Raises:
            MidicoderError: Nếu validation failed
        """
        # Validate required fields
        if not vo_def.get("id"):
            EM.raise_error(
                ErrorCode.CP01_VALUE_OBJECT_NOT_FOUND,
                reason="ValueObject 'id' is required",
            )

        vo_id = vo_def["id"]

        # Parse fields
        fields = []
        if "fields" in vo_def:
            fields = [self._parse_field(f) for f in vo_def["fields"]]

        # Build ValueObject
        vo = ValueObject(
            id=vo_id,
            description=vo_def.get("description", ""),
            fields=fields,
            immutable=bool(vo_def.get("immutable", False)),
            comparable=bool(vo_def.get("comparable", False)),
            extends=vo_def.get("extends"),
        )

        # Validate
        self._validate_value_object(vo)

        return vo

    def _parse_field(self, field_def: dict[str, Any]) -> VOField:
        """
        Parse field definition dict thành VOField object.

        Args:
            field_def: Field definition dict

        Returns:
            VOField object

        Raises:
            MidicoderError: Nếu field validation failed
        """
        # Validate required fields
        if not field_def.get("name"):
            EM.raise_error(
                ErrorCode.CP01_INVALID_FIELD_TYPE,
                reason="Field 'name' is required",
            )

        # Parse field type
        type_str = field_def.get("type", "string")
        field_type = self._parse_field_type(type_str)

        return VOField(
            name=field_def["name"],
            field_type=field_type,
            required=bool(field_def.get("required", False)),
            default=field_def.get("default"),
            description=field_def.get("description", ""),
            precision=field_def.get("precision"),
            scale=field_def.get("scale"),
            min_length=field_def.get("min_length"),
            max_length=field_def.get("max_length"),
            pattern=field_def.get("pattern"),
            enum_values=field_def.get("enum_values"),
        )

    def _parse_field_type(self, type_str: str) -> VOFieldType:
        """
        Parse string thành VOFieldType enum.

        Args:
            type_str: String type name

        Returns:
            VOFieldType enum value

        Raises:
            MidicoderError: Nếu type không hợp lệ
        """
        type_lower = type_str.lower()
        if type_lower not in VALID_FIELD_TYPES:
            EM.raise_error(
                ErrorCode.CP01_INVALID_FIELD_TYPE,
                field_type=type_str,
                supported_types=list(VALID_FIELD_TYPES),
            )

        return VOFieldType(type_lower)

    def _validate_value_object(self, vo: ValueObject) -> None:
        """
        Validate ValueObject object.

        Args:
            vo: ValueObject to validate

        Raises:
            MidicoderError: Nếu validation failed
        """
        # VO should have at least one field (optional, some VOs are markers)
        # No strict validation needed here


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "ValueObjectParser",
    "VALID_FIELD_TYPES",
]