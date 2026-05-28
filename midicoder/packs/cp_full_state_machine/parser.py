"""
State Machine DSL Parser — parse YAML/dict sang model objects.

Module này cung cấp StateMachineParser để convert YAML/dict
thành StateMachineDefinition models.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Optional

from midicoder.packs.cp_full_state_machine.models import (
    StateMachineDefinition,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class StateMachineParser:
    """Parser cho state machine DSL.

    Convert YAML/dict sang typed StateMachineDefinition.

    Ví dụ:
        >>> parser = StateMachineParser()
        >>> data = {
        ...     "machine_id": "order-lifecycle",
        ...     "entity_type": "Order",
        ...     "states": ["DRAFT", "SUBMITTED", "APPROVED", "FULFILLED"],
        ...     "initial_state": "DRAFT",
        ...     "transitions": {
        ...         "DRAFT": ["SUBMITTED"],
        ...         "SUBMITTED": ["APPROVED"],
        ...     },
        ... }
        >>> sm = parser.parse(data)
        >>> isinstance(sm, StateMachineDefinition)
        True
    """

    def parse(self, data: dict[str, Any]) -> StateMachineDefinition:
        """Parse một dict thành StateMachineDefinition.

        Args:
            data: Dict chứa state machine data.

        Returns:
            StateMachineDefinition.

        Raises:
            MidicoderError: Nếu data invalid hoặc thiếu field bắt buộc.
        """
        if not data or not isinstance(data, dict):
            raise EM.raise_error(
                ErrorCode.MDC-F13_DSL_PARSE_ERROR,
                reason="Data phải là dict không rỗng",
            )

        # Ưu tiên field machine_id để auto-detect
        machine_id = data.get("machine_id", data.get("id", ""))

        if not machine_id:
            raise EM.raise_error(
                ErrorCode.MDC-F13_DSL_PARSE_ERROR,
                reason="Thiếu field 'machine_id' hoặc 'id'",
            )

        return self._parse_definition(data)

    def parse_list(self, data: list[dict[str, Any]]) -> list[StateMachineDefinition]:
        """Parse danh sách state machine definitions.

        Args:
            data: Danh sách dict.

        Returns:
            Danh sách StateMachineDefinition.

        Raises:
            MidicoderError: Nếu data không phải list.
        """
        if not isinstance(data, list):
            raise EM.raise_error(
                ErrorCode.MDC-F13_DSL_PARSE_ERROR,
                reason="Data phải là list",
            )

        results = []
        for item in data:
            results.append(self.parse(item))
        return results

    def _parse_definition(self, data: dict[str, Any]) -> StateMachineDefinition:
        """Parse dict thành StateMachineDefinition.

        Args:
            data: Dict đã validate cơ bản.

        Returns:
            StateMachineDefinition.

        Raises:
            MidicoderError: Nếu thiếu field bắt buộc.
        """
        machine_id = data.get("machine_id", data.get("id", ""))
        entity_type = data.get("entity_type", data.get("entity", ""))

        if not entity_type:
            raise EM.raise_error(
                ErrorCode.MDC-F13_DSL_PARSE_ERROR,
                machine_id=machine_id,
                reason="Thiếu field 'entity_type'",
            )

        states = data.get("states", [])
        if not states:
            raise EM.raise_error(
                ErrorCode.MDC-F13_DSL_PARSE_ERROR,
                machine_id=machine_id,
                reason="Thiếu field 'states' hoặc danh sách rỗng",
            )

        initial_state = data.get("initial_state", data.get("start_state", states[0]))

        # Parse transitions — support cả dict và list format
        raw_transitions = data.get("transitions", {})
        transitions = self._parse_transitions(raw_transitions)

        final_states = data.get("final_states", [])

        return StateMachineDefinition(
            machine_id=machine_id,
            entity_type=entity_type,
            states=states,
            initial_state=initial_state,
            transitions=transitions,
            final_states=final_states,
            metadata=data.get("metadata", {}),
        )

    def _parse_transitions(self, raw: Any) -> dict[str, list[str]]:
        """Parse transitions từ nhiều format.

        Support:
        - Dict: {"DRAFT": ["SUBMITTED", "CANCELLED"]}
        - List: [{"from": "DRAFT", "to": ["SUBMITTED", "CANCELLED"]}]
        - Mixed: list của dict {"from_state": ..., "to_states": ...}

        Args:
            raw: Raw transition data.

        Returns:
            Dict {from_state: [to_states]}.
        """
        if isinstance(raw, dict):
            return {k: (v if isinstance(v, list) else [v]) for k, v in raw.items()}
        elif isinstance(raw, list):
            result = {}
            for item in raw:
                if isinstance(item, dict):
                    from_state = item.get("from", item.get("from_state", ""))
                    to_states = item.get("to", item.get("to_states", []))
                    if isinstance(to_states, str):
                        to_states = [to_states]
                    if from_state:
                        result[from_state] = to_states
            return result
        else:
            return {}
