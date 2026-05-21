"""
Unit tests cho StateMachineFastAPIEmitter.
"""

import pytest
from pathlib import Path
import tempfile

from midicoder.emitters.core.cp32_state_machine.fastapi import (
    StateMachineFastAPIEmitter,
    GeneratedFile,
)


class TestStateMachineFastAPIEmitter:
    """Test StateMachineFastAPIEmitter."""

    def setup_method(self):
        """Setup test fixture."""
        self.state_machines = [
            {
                "machine_id": "order-lifecycle",
                "entity_type": "Order",
                "states": ["DRAFT", "SUBMITTED", "APPROVED", "FULFILLED"],
                "initial_state": "DRAFT",
                "transitions": {
                    "DRAFT": ["SUBMITTED"],
                    "SUBMITTED": ["APPROVED"],
                    "APPROVED": ["FULFILLED"],
                },
                "final_states": ["FULFILLED"],
            }
        ]

    def test_emit_with_state_machines(self):
        """Emit với state machines có templates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path(tmpdir) / "stacks" / "fastapi" / "core"
            stack_dir.mkdir(parents=True)
            template_dir = stack_dir / "cp32_state_machine"
            template_dir.mkdir()

            # Tạo template dummy
            (template_dir / "state_machine.py.jinja2").write_text("# state_machine")
            (template_dir / "state_registry.py.jinja2").write_text("# state_registry")

            emitter = StateMachineFastAPIEmitter(stack_dir=str(stack_dir))
            files = emitter.emit(self.state_machines, output_dir=tmpdir)

            assert len(files) == 2
            assert isinstance(files[0], GeneratedFile)

    def test_emit_returns_empty_when_no_machines(self):
        """Emit khi không có state machines trả về empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path(tmpdir) / "stacks" / "fastapi" / "core"
            stack_dir.mkdir(parents=True)
            emitter = StateMachineFastAPIEmitter(stack_dir=str(stack_dir))
            files = emitter.emit([], output_dir=tmpdir)
            assert len(files) == 0

    def test_emit_file_paths_correct(self):
        """File paths đúng."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path(tmpdir) / "stacks" / "fastapi" / "core"
            stack_dir.mkdir(parents=True)
            template_dir = stack_dir / "cp32_state_machine"
            template_dir.mkdir()

            (template_dir / "state_machine.py.jinja2").write_text("# sm")
            (template_dir / "state_registry.py.jinja2").write_text("# reg")

            emitter = StateMachineFastAPIEmitter(stack_dir=str(stack_dir))
            files = emitter.emit(self.state_machines, output_dir=tmpdir)

            paths = [f.path for f in files]
            assert "app/state_machine/state_machine.py" in paths
            assert "app/state_machine/state_registry.py" in paths

    def test_emit_content_contains_entity_type(self):
        """Content chứa entity type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path(tmpdir) / "stacks" / "fastapi" / "core"
            stack_dir.mkdir(parents=True)
            template_dir = stack_dir / "cp32_state_machine"
            template_dir.mkdir()

            # Template chứa entity_type
            (template_dir / "state_machine.py.jinja2").write_text(
                "{% for sm in state_machines %}{{ sm.entity_type }}{% endfor %}"
            )
            (template_dir / "state_registry.py.jinja2").write_text("# reg")

            emitter = StateMachineFastAPIEmitter(stack_dir=str(stack_dir))
            files = emitter.emit(self.state_machines, output_dir=tmpdir)

            assert "Order" in files[0].content
