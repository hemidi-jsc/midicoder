"""
Unit tests cho StateMachineParser.
"""

import pytest

from midicoder.packs.cp32_state_machine.parser import StateMachineParser
from midicoder.packs.cp32_state_machine.models import StateMachineDefinition
from midicoder.errors import MidicoderError


class TestStateMachineParser:
    """Test StateMachineParser."""

    def setup_method(self):
        """Setup test fixture."""
        self.parser = StateMachineParser()

    def test_parse_valid_definition(self):
        """Parse definition hợp lệ."""
        data = {
            "machine_id": "order-lifecycle",
            "entity_type": "Order",
            "states": ["DRAFT", "SUBMITTED", "APPROVED"],
            "initial_state": "DRAFT",
            "transitions": {
                "DRAFT": ["SUBMITTED"],
                "SUBMITTED": ["APPROVED"],
            },
        }
        result = self.parser.parse(data)
        assert isinstance(result, StateMachineDefinition)
        assert result.machine_id == "order-lifecycle"
        assert result.entity_type == "Order"
        assert len(result.states) == 3

    def test_parse_with_final_states(self):
        """Parse với final_states."""
        data = {
            "machine_id": "test",
            "entity_type": "Invoice",
            "states": ["DRAFT", "PAID", "VOID"],
            "initial_state": "DRAFT",
            "transitions": {"DRAFT": ["PAID", "VOID"]},
            "final_states": ["PAID", "VOID"],
        }
        result = self.parser.parse(data)
        assert result.final_states == ["PAID", "VOID"]

    def test_parse_with_id_alias(self):
        """Parse với 'id' thay vì 'machine_id'."""
        data = {
            "id": "invoice-lifecycle",
            "entity_type": "Invoice",
            "states": ["DRAFT", "SENT"],
            "initial_state": "DRAFT",
            "transitions": {"DRAFT": ["SENT"]},
        }
        result = self.parser.parse(data)
        assert result.machine_id == "invoice-lifecycle"

    def test_parse_list_format_transitions(self):
        """Parse transitions format list."""
        data = {
            "machine_id": "test",
            "entity_type": "Order",
            "states": ["A", "B", "C"],
            "initial_state": "A",
            "transitions": [
                {"from": "A", "to": ["B", "C"]},
                {"from": "B", "to": ["C"]},
            ],
        }
        result = self.parser.parse(data)
        assert result.transitions == {"A": ["B", "C"], "B": ["C"]}

    def test_parse_empty_data_raises_error(self):
        """Empty data throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse({})

    def test_parse_none_raises_error(self):
        """None data throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse(None)

    def test_parse_missing_machine_id_raises_error(self):
        """Thiếu machine_id throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse({"entity_type": "Order"})

    def test_parse_missing_entity_type_raises_error(self):
        """Thiếu entity_type throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse({"machine_id": "test"})

    def test_parse_empty_states_raises_error(self):
        """Thiếu states throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse({
                "machine_id": "test",
                "entity_type": "Order",
                "states": [],
                "initial_state": "DRAFT",
            })

    def test_parse_list(self):
        """Parse danh sách definitions."""
        data = [
            {
                "machine_id": "order",
                "entity_type": "Order",
                "states": ["DRAFT", "SUBMITTED"],
                "initial_state": "DRAFT",
                "transitions": {"DRAFT": ["SUBMITTED"]},
            },
            {
                "machine_id": "invoice",
                "entity_type": "Invoice",
                "states": ["DRAFT", "SENT"],
                "initial_state": "DRAFT",
                "transitions": {"DRAFT": ["SENT"]},
            },
        ]
        results = self.parser.parse_list(data)
        assert len(results) == 2
        assert all(isinstance(r, StateMachineDefinition) for r in results)
        assert results[0].entity_type == "Order"
        assert results[1].entity_type == "Invoice"

    def test_parse_list_not_list_raises_error(self):
        """Data không phải list throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse_list({"machine_id": "test"})
