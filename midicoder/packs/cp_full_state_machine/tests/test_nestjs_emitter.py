"""
Unit tests cho StateMachineNestJSEmitter.
"""

import pytest
from pathlib import Path
import tempfile

from midicoder.packs.cp_full_state_machine.nestjs import (
    StateMachineNestJSEmitter,
    GeneratedFile,
)


class TestStateMachineNestJSEmitter:
    """Test StateMachineNestJSEmitter."""

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
            stack_dir = Path(tmpdir) / "stacks" / "nestjs" / "core"
            stack_dir.mkdir(parents=True)
            template_dir = stack_dir / "cp_full_state_machine"
            template_dir.mkdir()

            (template_dir / "state-machine.service.ts.jinja2").write_text("// service")
            (template_dir / "state-registry.service.ts.jinja2").write_text("// registry")

            emitter = StateMachineNestJSEmitter(stack_dir=str(stack_dir))
            files = emitter.emit(self.state_machines, output_dir=tmpdir)

            assert len(files) == 2
            assert isinstance(files[0], GeneratedFile)

    def test_emit_returns_empty_when_no_machines(self):
        """Emit khi không có state machines trả về empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path(tmpdir) / "stacks" / "nestjs" / "core"
            stack_dir.mkdir(parents=True)
            emitter = StateMachineNestJSEmitter(stack_dir=str(stack_dir))
            files = emitter.emit([], output_dir=tmpdir)
            assert len(files) == 0

    def test_emit_file_paths_correct(self):
        """File paths đúng."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path(tmpdir) / "stacks" / "nestjs" / "core"
            stack_dir.mkdir(parents=True)
            template_dir = stack_dir / "cp_full_state_machine"
            template_dir.mkdir()

            (template_dir / "state-machine.service.ts.jinja2").write_text("// svc")
            (template_dir / "state-registry.service.ts.jinja2").write_text("// reg")

            emitter = StateMachineNestJSEmitter(stack_dir=str(stack_dir))
            files = emitter.emit(self.state_machines, output_dir=tmpdir)

            paths = [f.path for f in files]
            assert "src/state-machine/state-machine.service.ts" in paths
            assert "src/state-machine/state-registry.service.ts" in paths

    def test_emit_content_contains_entity_type(self):
        """Content chứa entity type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path(tmpdir) / "stacks" / "nestjs" / "core"
            stack_dir.mkdir(parents=True)
            template_dir = stack_dir / "cp_full_state_machine"
            template_dir.mkdir()

            (template_dir / "state-machine.service.ts.jinja2").write_text(
                "{% for sm in state_machines %}{{ sm.entity_type }}{% endfor %}"
            )
            (template_dir / "state-registry.service.ts.jinja2").write_text("// reg")

            emitter = StateMachineNestJSEmitter(stack_dir=str(stack_dir))
            files = emitter.emit(self.state_machines, output_dir=tmpdir)

            assert "Order" in files[0].content
