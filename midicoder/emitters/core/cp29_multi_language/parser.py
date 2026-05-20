# coding: utf-8
"""
Mô-đun parser cho CP29 — Multi-Language Support Generator.

Chuyển đổi MIR metadata (entities, commands, queries, events) thành
I18nKeyset (danh sách i18n keys theo dotted namespace convention).

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from typing import Any

from midicoder.emitters.core.cp29_multi_language.models import I18nKey, I18nKeyset


class I18nParser:
    """Parser chuyển MIR metadata thành I18nKeyset.

    Auto-extract i18n keys từ:
    - Entity fields: entity.{entity_snake}.field.{field_snake}
    - Commands: command.{command_snake}
    - Queries: query.{query_snake}
    - Events: event.{event_snake}
    """

    def parse_from_metadata(self, metadata: dict[str, Any] | None) -> I18nKeyset:
        """Parse MIR metadata và extract i18n keys.

        Args:
            metadata: Dict từ MIR chứa entities[], commands[], queries[], events[].

        Returns:
            I18nKeyset với các keys đã extract và sorted.
        """
        if metadata is None:
            return I18nKeyset()

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

    def _parse_entity(self, entity: dict[str, Any]) -> list[I18nKey]:
        """Extract i18n keys từ entity và các field của nó.

        Args:
            entity: Dict chứa id, fields[].

        Returns:
            Danh sách I18nKey cho mỗi field.
        """
        keys: list[I18nKey] = []
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

    def _parse_command(self, command: dict[str, Any]) -> I18nKey | None:
        """Extract i18n key từ command.

        Args:
            command: Dict chứa id, description.

        Returns:
            I18nKey hoặc None nếu command không hợp lệ.
        """
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

    def _parse_query(self, query: dict[str, Any]) -> I18nKey | None:
        """Extract i18n key từ query.

        Args:
            query: Dict chứa id, description.

        Returns:
            I18nKey hoặc None nếu query không hợp lệ.
        """
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

    def _parse_event(self, event: dict[str, Any]) -> I18nKey | None:
        """Extract i18n key từ event.

        Args:
            event: Dict chứa id, description.

        Returns:
            I18nKey hoặc None nếu event không hợp lệ.
        """
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
        """Chuyển PascalCase/camelCase sang snake_case.

        Args:
            name: Tên cần convert.

        Returns:
            Tên đã chuyển sang snake_case.

        Examples:
            >>> _to_snake_case("CustomerName")
            'customer_name'
            >>> _to_snake_case("customerName")
            'customer_name'
            >>> _to_snake_case("customer_name")
            'customer_name'
        """
        # Insérer underscore trước chữ hoa (ngoại trừ ký tự đầu)
        s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        result = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s1).lower()
        # Thay thế ký tự đặc biệt bằng underscore
        result = re.sub(r"[-\s]+", "_", result)
        return result
