"""
Test suite cho Workflow FastAPI Emitter.

Mô-đun này test các chức năng emit code cho FastAPI:
- WorkflowFastAPIEmitter.emit()
- Model generation (SQLAlchemy)
- Engine generation (State machine)
- Guards generation
- Effects generation
- Migration SQL generation

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from midicoder.emitters.core.cp13_workflow_runtime.fastapi import WorkflowFastAPIEmitter
from midicoder.emitters.core.cp13_workflow_runtime.models import (
    WorkflowDefinition,
    Transition,
    Guard,
    GuardType,
    Effect,
    EffectType,
)


class TestWorkflowFastAPIEmitterInit:
    """Test WorkflowFastAPIEmitter initialization."""

    def test_emitter_init_default(self):
        """Khởi tạo emitter với default templates path."""
        emitter = WorkflowFastAPIEmitter()
        
        assert emitter is not None

    def test_emitter_init_custom_path(self):
        """Khởi tạo emitter với custom templates path."""
        with TemporaryDirectory() as tmpdir:
            emitter = WorkflowFastAPIEmitter(templates_path=tmpdir)
            
            assert emitter is not None

    def test_snake_case_filter(self):
        """Test snake_case filter."""
        emitter = WorkflowFastAPIEmitter()
        
        assert emitter._snake_case("OrderLifecycle") == "order_lifecycle"
        assert emitter._snake_case("OrderLifecycleWorkflow") == "order_lifecycle_workflow"
        assert emitter._snake_case("already_snake_case") == "already_snake_case"

    def test_pascal_case_filter(self):
        """Test PascalCase filter."""
        emitter = WorkflowFastAPIEmitter()
        
        assert emitter._pascal_case("order_lifecycle") == "OrderLifecycle"
        assert emitter._pascal_case("order-lifecycle") == "OrderLifecycle"
        assert emitter._pascal_case("order lifecycle") == "OrderLifecycle"


class TestWorkflowFastAPIEmitterModels:
    """Test model generation cho FastAPI."""

    def test_emit_models_creates_file(self):
        """Emit models tạo file models.py."""
        emitter = WorkflowFastAPIEmitter()
        workflows = [
            WorkflowDefinition(
                name="order_lifecycle",
                states=["draft", "submitted", "approved", "shipped"],
                initial_state="draft",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_models(workflows, domain_path, generated_files)
            
            models_path = domain_path / "models.py"
            assert models_path.exists()
            assert len(generated_files) == 1

    def test_emit_models_contains_workflow_instance(self):
        """Models chứa WorkflowInstance class."""
        emitter = WorkflowFastAPIEmitter()
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
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_models(workflows, domain_path, generated_files)
            
            content = (domain_path / "models.py").read_text()
            
            assert "class WorkflowInstance" in content
            assert "workflow_name" in content
            assert "entity_type" in content
            assert "entity_id" in content
            assert "current_state" in content

    def test_emit_models_contains_workflow_event(self):
        """Models chứa WorkflowEvent class."""
        emitter = WorkflowFastAPIEmitter()
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
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_models(workflows, domain_path, generated_files)
            
            content = (domain_path / "models.py").read_text()
            
            assert "class WorkflowEvent" in content
            assert "instance_id" in content
            assert "event_name" in content
            assert "from_state" in content
            assert "to_state" in content

    def test_emit_models_contains_workflow_transition_log(self):
        """Models chứa WorkflowTransitionLog class."""
        emitter = WorkflowFastAPIEmitter()
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
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_models(workflows, domain_path, generated_files)
            
            content = (domain_path / "models.py").read_text()
            
            assert "class WorkflowTransitionLog" in content
            assert "guard_results" in content
            assert "effects_executed" in content
            assert "status" in content

    def test_emit_models_has_tenant_id(self):
        """Models có tenant_id field cho multi-tenant."""
        emitter = WorkflowFastAPIEmitter()
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
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_models(workflows, domain_path, generated_files)
            
            content = (domain_path / "models.py").read_text()
            
            # Check tenant_id trong tất cả models
            assert content.count("tenant_id") >= 3  # WorkflowInstance, WorkflowEvent, WorkflowTransitionLog


class TestWorkflowFastAPIEmitterEngine:
    """Test engine generation cho FastAPI."""

    def test_emit_engine_creates_file(self):
        """Emit engine tạo file engine.py."""
        emitter = WorkflowFastAPIEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a", "state_b"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_engine(workflows, domain_path, generated_files)
            
            engine_path = domain_path / "engine.py"
            assert engine_path.exists()

    def test_emit_engine_contains_workflow_engine_class(self):
        """Engine chứa WorkflowEngine class."""
        emitter = WorkflowFastAPIEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a", "state_b"],
                initial_state="state_a",
                transitions=[],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_engine(workflows, domain_path, generated_files)
            
            content = (domain_path / "engine.py").read_text()
            
            assert "class WorkflowEngine" in content
            assert "async def transition" in content

    def test_emit_engine_has_transition_result(self):
        """Engine chứa TransitionResult dataclass."""
        emitter = WorkflowFastAPIEmitter()
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
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_engine(workflows, domain_path, generated_files)
            
            content = (domain_path / "engine.py").read_text()
            
            assert "class TransitionResult" in content or "TransitionResult" in content


class TestWorkflowFastAPIEmitterGuards:
    """Test guards generation cho FastAPI."""

    def test_emit_guards_creates_directory(self):
        """Emit guards tạo directory và __init__.py."""
        emitter = WorkflowFastAPIEmitter()
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
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_guards(workflows, domain_path, generated_files)
            
            guards_init = domain_path / "guards" / "__init__.py"
            assert guards_init.exists()

    def test_emit_guards_contains_permission_guard(self):
        """Guards chứa PermissionGuard."""
        emitter = WorkflowFastAPIEmitter()
        workflows = [
            WorkflowDefinition(
                name="order_lifecycle",
                states=["draft", "submitted"],
                initial_state="draft",
                transitions=[
                    Transition(
                        from_state="draft",
                        to_state="submitted",
                        guards=[
                            Guard(type=GuardType.PERMISSION, permission="order.submit"),
                        ],
                    )
                ],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_guards(workflows, domain_path, generated_files)
            
            # Check guards __init__.py exports PermissionGuard
            content = (domain_path / "guards" / "__init__.py").read_text()
            assert "PermissionGuard" in content

    def test_emit_guards_contains_business_guard(self):
        """Guards chứa BusinessGuard."""
        emitter = WorkflowFastAPIEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a", "state_b"],
                initial_state="state_a",
                transitions=[
                    Transition(
                        from_state="state_a",
                        to_state="state_b",
                        guards=[
                            Guard(type=GuardType.BUSINESS, condition="value > 0"),
                        ],
                    )
                ],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_guards(workflows, domain_path, generated_files)
            
            content = (domain_path / "guards" / "__init__.py").read_text()
            assert "BusinessGuard" in content


class TestWorkflowFastAPIEmitterEffects:
    """Test effects generation cho FastAPI."""

    def test_emit_effects_creates_directory(self):
        """Emit effects tạo directory và __init__.py."""
        emitter = WorkflowFastAPIEmitter()
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
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_effects(workflows, domain_path, generated_files)
            
            effects_init = domain_path / "effects" / "__init__.py"
            assert effects_init.exists()

    def test_emit_effects_contains_event_effect(self):
        """Effects chứa EventEffect."""
        emitter = WorkflowFastAPIEmitter()
        workflows = [
            WorkflowDefinition(
                name="test",
                states=["state_a", "state_b"],
                initial_state="state_a",
                transitions=[
                    Transition(
                        from_state="state_a",
                        to_state="state_b",
                        effects=[
                            Effect(type=EffectType.EVENT, publish="OrderSubmitted"),
                        ],
                    )
                ],
            )
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_effects(workflows, domain_path, generated_files)
            
            content = (domain_path / "effects" / "__init__.py").read_text()
            assert "EventEffect" in content

    def test_emit_effects_contains_notification_effect(self):
        """Effects chứa NotificationEffect."""
        emitter = WorkflowFastAPIEmitter()
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
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_effects(workflows, domain_path, generated_files)
            
            content = (domain_path / "effects" / "__init__.py").read_text()
            assert "NotificationEffect" in content


class TestWorkflowFastAPIEmitterMigration:
    """Test migration SQL generation cho FastAPI."""

    def test_emit_migration_creates_file(self):
        """Emit migration tạo file SQL."""
        emitter = WorkflowFastAPIEmitter()
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
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_migration(workflows, domain_path, generated_files)
            
            migration_path = domain_path / "workflows.sql"
            assert migration_path.exists()

    def test_emit_migration_contains_workflow_instances_table(self):
        """Migration chứa CREATE TABLE workflow_instances."""
        emitter = WorkflowFastAPIEmitter()
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
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_migration(workflows, domain_path, generated_files)
            
            content = (domain_path / "workflows.sql").read_text()
            
            assert "CREATE TABLE" in content.upper()
            assert "workflow_instances" in content

    def test_emit_migration_contains_workflow_events_table(self):
        """Migration chứa CREATE TABLE workflow_events."""
        emitter = WorkflowFastAPIEmitter()
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
            domain_path = output_path / "domain" / "workflows"
            domain_path.mkdir(parents=True, exist_ok=True)
            
            generated_files = []
            emitter._emit_migration(workflows, domain_path, generated_files)
            
            content = (domain_path / "workflows.sql").read_text()
            
            assert "workflow_events" in content


class TestWorkflowFastAPIEmitterFullEmit:
    """Test full emit pipeline cho FastAPI."""

    def test_emit_creates_all_files(self):
        """Emit tạo tất cả files cần thiết."""
        emitter = WorkflowFastAPIEmitter()
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
            domain_path = output_path / "domain" / "workflows"
            assert (domain_path / "models.py").exists()
            assert (domain_path / "engine.py").exists()
            assert (domain_path / "guards" / "__init__.py").exists()
            assert (domain_path / "effects" / "__init__.py").exists()
            assert (domain_path / "workflows.sql").exists()

    def test_emit_multiple_workflows(self):
        """Emit xử lý nhiều workflows."""
        emitter = WorkflowFastAPIEmitter()
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