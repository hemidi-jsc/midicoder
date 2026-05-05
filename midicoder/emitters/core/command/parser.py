"""
Command Parser Module.

Module này cung cấp CommandParser để parse Command DSL YAML:
- Parse YAML → Command models
- Validate fields, types, và required keys
- Error handling với MidicoderError

Sử dụng:
    from midicoder.emitters.core.command.parser import CommandParser
    
    parser = CommandParser()
    commands = parser.parse(yaml_string)
    # commands: list[Command]

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import yaml
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

from .models import Command, Field, FieldType


# ============================================================================
# Valid Field Types
# ============================================================================

VALID_FIELD_TYPES = {ft.value for ft in FieldType}


# ============================================================================
# CommandParser Class
# ============================================================================

class CommandParser:
    """
    Parser cho Command DSL YAML.

    Parse YAML string thành list của Command objects với validation.

    Usage:
        parser = CommandParser()
        commands = parser.parse(yaml_string)
    """

    def __init__(self) -> None:
        """Khởi tạo CommandParser."""
        pass

    def parse(self, yaml_content: str) -> list[Command]:
        """
        Parse YAML content thành list Command objects.

        Args:
            yaml_content: YAML string chứa command definitions

        Returns:
            List của Command objects

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
        if not data or "commands" not in data:
            EM.raise_error(
                ErrorCode.CP01_COMMAND_NOT_FOUND,
                reason="Missing 'commands' key in YAML",
            )

        # Parse each command
        commands = []
        for cmd_def in data.get("commands", []):
            command = self._parse_command(cmd_def)
            commands.append(command)

        return commands

    def _parse_command(self, cmd_def: dict[str, Any]) -> Command:
        """
        Parse command definition dict thành Command object.

        Args:
            cmd_def: Command definition dict

        Returns:
            Command object

        Raises:
            MidicoderError: Nếu validation failed
        """
        # Validate required fields
        if not cmd_def.get("id"):
            EM.raise_error(
                ErrorCode.CP01_COMMAND_NOT_FOUND,
                reason="Command 'id' is required",
            )

        cmd_id = cmd_def["id"]

        # Parse input fields
        input_fields = []
        if "input" in cmd_def:
            input_fields = [self._parse_field(f) for f in cmd_def["input"]]

        # Parse returns fields
        return_fields = []
        if "returns" in cmd_def:
            return_fields = [self._parse_field(r) for r in cmd_def["returns"]]

        # Build Command object
        command = Command(
            id=cmd_id,
            description=cmd_def.get("description", ""),
            input=input_fields,
            fetches=cmd_def.get("fetches", []),
            guards=cmd_def.get("guards", []),
            effects=cmd_def.get("effects", []),
            errors=cmd_def.get("errors", []),
            returns=return_fields,
            category=cmd_def.get("category", "custom"),
            emits=cmd_def.get("emits", []),
            required_roles=cmd_def.get("required_roles", []),
            required_permissions=cmd_def.get("required_permissions", []),
            writes_to=cmd_def.get("writes_to", []),
            transaction_required=bool(cmd_def.get("transaction", False)),
            tenant_scope=cmd_def.get("tenant_scope", "global"),
        )

        # Validate command
        self._validate_command(command)

        return command

    def _parse_field(self, field_def: dict[str, Any]) -> Field:
        """
        Parse field definition dict thành Field object.

        Args:
            field_def: Field definition dict

        Returns:
            Field object

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

        return Field(
            name=field_def["name"],
            field_type=field_type,
            required=bool(field_def.get("required", False)),
            default=field_def.get("default"),
            description=field_def.get("description", ""),
            nullable=bool(field_def.get("nullable", True)),
            unique=bool(field_def.get("unique", False)),
            primary_key=bool(field_def.get("primary_key", False)),
            index=bool(field_def.get("index", False)),
            server_default=field_def.get("server_default", ""),
            length=field_def.get("length"),
            precision=field_def.get("precision"),
            scale=field_def.get("scale"),
            enum_values=field_def.get("enum_values"),
        )

    def _parse_field_type(self, type_str: str) -> FieldType:
        """
        Parse string thành FieldType enum.

        Args:
            type_str: String type name

        Returns:
            FieldType enum value

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

        return FieldType(type_lower)

    def _validate_command(self, command: Command) -> None:
        """
        Validate Command object.

        Args:
            command: Command to validate

        Raises:
            MidicoderError: Nếu validation failed
        """
        # Command phải có writes_to hoặc reads_from
        if not command.writes_to:
            EM.raise_error(
                ErrorCode.CP01_COMMAND_NOT_FOUND,
                command_id=command.id,
                reason="Command must have at least one 'writes_to' entity",
            )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "CommandParser",
    "VALID_FIELD_TYPES",
]