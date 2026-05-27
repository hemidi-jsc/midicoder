"""
Test suite cho Workflow NestJS Emitter.

Mô-đun này test các chức năng emit code cho NestJS:
- WorkflowNestJSEmitter.emit()
- Module generation
- Entity generation (TypeORM)
- Engine generation
- Guards generation
- Effects generation

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from midicoder.packs.cp13_workflow_runtime.nestjs import WorkflowNestJSEmitter
from midicoder.packs.cp13_workflow_runtime.models import (
    WorkflowDefinition,
    Transition,
    Guard,
    GuardType,
    Effect,
    EffectType,
)


class TestWorkflowNestJSEmitterInit:
    """Test WorkflowNestJSEmitter initialization."""

    def test_emitter_init(self):
        """Khởi tạo emitter."""
        emitter = WorkflowNestJSEmitter()
        
        assert emitter is not None


class TestWorkflowNestJSEmitterModule:
    """Test module generation cho NestJS."""

    def test_emit_module_creates_file(self):
        """Emit module tạo file workflows.module.ts."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "src" / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_module(workflows, domain_path, generated_files)
            
            module_path = domain_path / "workflows.module.ts"
            assert module_path.exists()

    def test_emit_module_contains_nestjs_module(self):
        """Module chứa NestJS @Module decorator."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "src" / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_module(workflows, domain_path, generated_files)
            
            content = (domain_path / "workflows.module.ts").read_text()
            
            assert "@Module" in content
            assert "export class WorkflowsModule" in content


class TestWorkflowNestJSEmitterEntity:
    """Test entity generation cho NestJS."""

    def test_emit_entity_creates_file(self):
        """Emit entity tạo file workflows.entity.ts."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "src" / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_entity(domain_path, generated_files)
            
            entity_path = domain_path / "workflows.entity.ts"
            assert entity_path.exists()

    def test_emit_entity_contains_typeorm_entity(self):
        """Entity chứa TypeORM @Entity decorator."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "src" / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_entity(domain_path, generated_files)
            
            content = (domain_path / "workflows.entity.ts").read_text()
            
            assert "@Entity" in content
            assert "class WorkflowEntity" in content
            assert "workflowName" in content
            assert "currentState" in content

    def test_emit_entity_has_tenant_id(self):
        """Entity có tenantId field cho multi-tenant."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "src" / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_entity(domain_path, generated_files)
            
            content = (domain_path / "workflows.entity.ts").read_text()
            
            assert "tenantId" in content


class TestWorkflowNestJSEmitterEngine:
    """Test engine generation cho NestJS."""

    def test_emit_engine_creates_file(self):
        """Emit engine tạo file workflow.engine.ts."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "src" / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_engine(workflows, domain_path, generated_files)
            
            engine_path = domain_path / "workflow.engine.ts"
            assert engine_path.exists()

    def test_emit_engine_contains_workflow_engine(self):
        """Engine chứa WorkflowEngine class."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "src" / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_engine(workflows, domain_path, generated_files)
            
            content = (domain_path / "workflow.engine.ts").read_text()
            
            assert "@Injectable()" in content
            assert "export class WorkflowEngine" in content
            assert "async transition" in content

    def test_emit_engine_has_transition_result(self):
        """Engine chứa TransitionResult class."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "src" / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_engine(workflows, domain_path, generated_files)
            
            content = (domain_path / "workflow.engine.ts").read_text()
            
            assert "class TransitionResult" in content or "TransitionResult" in content


class TestWorkflowNestJSEmitterGuards:
    """Test guards generation cho NestJS."""

    def test_emit_guards_creates_file(self):
        """Emit guards tạo file workflow.guard.ts."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "src" / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_guards(workflows, domain_path, generated_files)
            
            guard_path = domain_path / "guards" / "permission.guard.ts"
            assert guard_path.exists()

    def test_emit_guards_contains_canactivate(self):
        """Guards chứa NestJS CanActivate interface."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "src" / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_guards(workflows, domain_path, generated_files)
            
            content = (domain_path / "guards" / "permission.guard.ts").read_text()
            
            assert "CanActivate" in content
            assert "canActivate" in content


class TestWorkflowNestJSEmitterEffects:
    """Test effects generation cho NestJS."""

    def test_emit_effects_creates_file(self):
        """Emit effects tạo file workflow.effects.ts."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "src" / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_effects(workflows, domain_path, generated_files)
            
            effects_path = domain_path / "effects" / "workflow.effects.ts"
            assert effects_path.exists()

    def test_emit_effects_contains_workflow_effects(self):
        """Effects chứa WorkflowEffects class."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "src" / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_effects(workflows, domain_path, generated_files)
            
            content = (domain_path / "effects" / "workflow.effects.ts").read_text()
            
            assert "@Injectable()" in content
            assert "export class WorkflowEffects" in content
            assert "publishEvent" in content
            assert "executeCommand" in content


class TestWorkflowNestJSEmitterFullEmit:
    """Test full emit pipeline cho NestJS."""

    def test_emit_creates_all_files(self):
        """Emit tạo tất cả files cần thiết."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="order_lifecycle",
                entity="Order",
                states=["draft", "submitted", "approved", "shipped"],
                initial_state="draft",
                transitions=[
                    Transition(
                        id="submit",
                        from_state="draft",
                        to_state="submitted",
                        event="submit_order",
                        guards=[
                            Guard(type=GuardType.PERMISSION, permission="order.submit"),
                        ],
                        effects=[
                            Effect(type=EffectType.EVENT, publish="OrderSubmitted"),
                        ],
                    )
                ],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            generated_files = emitter.emit(workflows, output_path)
            
            # Check that files were generated
            assert len(generated_files) > 0
            
            # Check directory structure
            domain_path = output_path / "src" / "domain" / "workflows"
            assert (domain_path / "workflows.module.ts").exists()
            assert (domain_path / "workflows.entity.ts").exists()
            assert (domain_path / "workflow.engine.ts").exists()
            assert (domain_path / "guards" / "permission.guard.ts").exists()
            assert (domain_path / "effects" / "workflow.effects.ts").exists()

    def test_emit_multiple_workflows(self):
        """Emit xử lý nhiều workflows."""
        emitter = WorkflowNestJSEmitter()
        workflows = [
            WorkflowDefinition(
                name="order_lifecycle",
                states=["draft", "submitted"],
                initial_state="draft",
                transitions=[],
            ),
            WorkflowDefinition(
                name="payment_lifecycle",
                states=["pending", "completed", "failed"],
                initial_state="pending",
                transitions=[],
            ),
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            generated_files = emitter.emit(workflows, output_path)
            
            # Should generate files for both workflows
            assert len(generated_files) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])