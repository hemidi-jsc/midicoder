"""Test CP13 guards và effects — base evaluation/execution."""

import pytest
from unittest import TestCase
from uuid import uuid4


class TestGuardEvaluator(TestCase):
    """Kiểm tra GuardEvaluator ABC và factory."""

    def test_guard_evaluator_exists(self):
        """GuardEvaluator ABC tồn tại."""
        from midicoder.packs.cp13_workflow_runtime.guards.base import GuardEvaluator
        self.assertTrue(hasattr(GuardEvaluator, 'evaluate'))
        self.assertTrue(hasattr(GuardEvaluator, 'create_evaluator'))

    def test_create_permission_evaluator(self):
        """Tạo PermissionEvaluator từ factory."""
        from midicoder.packs.cp13_workflow_runtime.guards.base import GuardEvaluator
        from midicoder.packs.cp13_workflow_runtime.models import GuardType
        evaluator = GuardEvaluator.create_evaluator(GuardType.PERMISSION)
        self.assertIsNotNone(evaluator)

    def test_create_business_evaluator(self):
        """Tạo BusinessEvaluator từ factory."""
        from midicoder.packs.cp13_workflow_runtime.guards.base import GuardEvaluator
        from midicoder.packs.cp13_workflow_runtime.models import GuardType
        evaluator = GuardEvaluator.create_evaluator(GuardType.BUSINESS)
        self.assertIsNotNone(evaluator)

    def test_create_compliance_evaluator(self):
        """Tạo ComplianceEvaluator từ factory."""
        from midicoder.packs.cp13_workflow_runtime.guards.base import GuardEvaluator
        from midicoder.packs.cp13_workflow_runtime.models import GuardType
        evaluator = GuardEvaluator.create_evaluator(GuardType.COMPLIANCE)
        self.assertIsNotNone(evaluator)

    def test_create_role_evaluator(self):
        """Tạo RoleEvaluator từ factory."""
        from midicoder.packs.cp13_workflow_runtime.guards.base import GuardEvaluator
        from midicoder.packs.cp13_workflow_runtime.models import GuardType
        evaluator = GuardEvaluator.create_evaluator(GuardType.ROLE)
        self.assertIsNotNone(evaluator)

    def test_create_state_evaluator(self):
        """Tạo StateEvaluator từ factory."""
        from midicoder.packs.cp13_workflow_runtime.guards.base import GuardEvaluator
        from midicoder.packs.cp13_workflow_runtime.models import GuardType
        evaluator = GuardEvaluator.create_evaluator(GuardType.STATE)
        self.assertIsNotNone(evaluator)


class TestPermissionGuard(TestCase):
    """Kiểm tra PermissionGuard."""

    def test_permission_guard_evaluate(self):
        """PermissionGuard.evaluate trả về bool."""
        from midicoder.packs.cp13_workflow_runtime.guards.permission import PermissionGuard
        guard = PermissionGuard(permission="read:orders")
        result = guard.evaluate(context={})
        self.assertIsInstance(result, bool)


class TestBusinessGuard(TestCase):
    """Kiểm tra BusinessGuard."""

    def test_business_guard_evaluate(self):
        """BusinessGuard.evaluate trả về bool."""
        from midicoder.packs.cp13_workflow_runtime.guards.business import BusinessGuard
        guard = BusinessGuard(condition="amount > 100")
        result = guard.evaluate(context={"amount": 200})
        self.assertIsInstance(result, bool)


class TestComplianceGuard(TestCase):
    """Kiểm tra ComplianceGuard."""

    def test_compliance_guard_evaluate(self):
        """ComplianceGuard.evaluate trả về bool."""
        from midicoder.packs.cp13_workflow_runtime.guards.compliance import ComplianceGuard
        guard = ComplianceGuard(check="GDPR")
        result = guard.evaluate(context={})
        self.assertIsInstance(result, bool)


class TestRoleGuard(TestCase):
    """Kiểm tra RoleGuard."""

    def test_role_guard_evaluate(self):
        """RoleGuard.evaluate trả về bool."""
        from midicoder.packs.cp13_workflow_runtime.guards.role import RoleGuard
        guard = RoleGuard(roles=["admin", "manager"])
        result = guard.evaluate(context={"user_roles": ["admin"]})
        self.assertIsInstance(result, bool)


class TestStateGuard(TestCase):
    """Kiểm tra StateGuard."""

    def test_state_guard_evaluate(self):
        """StateGuard.evaluate trả về bool."""
        from midicoder.packs.cp13_workflow_runtime.guards.state import StateGuard
        guard = StateGuard(condition="state == 'submitted'")
        result = guard.evaluate(context={"state": "submitted"})
        self.assertIsInstance(result, bool)


class TestEffectExecutor(TestCase):
    """Kiểm tra EffectExecutor ABC và factory."""

    def test_effect_executor_exists(self):
        """EffectExecutor ABC tồn tại."""
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectExecutor
        self.assertTrue(hasattr(EffectExecutor, 'execute'))
        self.assertTrue(hasattr(EffectExecutor, 'create_executor'))
        self.assertTrue(hasattr(EffectExecutor, 'success'))
        self.assertTrue(hasattr(EffectExecutor, 'failure'))

    def test_success_helper(self):
        """EffectExecutor.success() tạo result thành công."""
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectExecutor, EffectResult
        result = EffectExecutor.success(data={"ok": True})
        self.assertIsInstance(result, EffectResult)
        self.assertTrue(result.success)

    def test_failure_helper(self):
        """EffectExecutor.failure() tạo result thất bại."""
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectExecutor, EffectResult
        result = EffectExecutor.failure("Lỗi xảy ra")
        self.assertIsInstance(result, EffectResult)
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Lỗi xảy ra")

    def test_create_event_executor(self):
        """Tạo EventExecutor từ factory."""
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectExecutor
        from midicoder.packs.cp13_workflow_runtime.models import EffectType
        executor = EffectExecutor.create_executor(EffectType.EVENT)
        self.assertIsNotNone(executor)

    def test_create_command_executor(self):
        """Tạo CommandExecutor từ factory."""
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectExecutor
        from midicoder.packs.cp13_workflow_runtime.models import EffectType
        executor = EffectExecutor.create_executor(EffectType.COMMAND)
        self.assertIsNotNone(executor)

    def test_create_notification_executor(self):
        """Tạo NotificationExecutor từ factory."""
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectExecutor
        from midicoder.packs.cp13_workflow_runtime.models import EffectType
        executor = EffectExecutor.create_executor(EffectType.NOTIFICATION)
        self.assertIsNotNone(executor)

    def test_create_audit_executor(self):
        """Tạo AuditExecutor từ factory."""
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectExecutor
        from midicoder.packs.cp13_workflow_runtime.models import EffectType
        executor = EffectExecutor.create_executor(EffectType.AUDIT)
        self.assertIsNotNone(executor)

    def test_create_compensation_executor(self):
        """Tạo CompensationExecutor từ factory."""
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectExecutor
        from midicoder.packs.cp13_workflow_runtime.models import EffectType
        executor = EffectExecutor.create_executor(EffectType.COMPENSATION)
        self.assertIsNotNone(executor)


class TestEventEffect(TestCase):
    """Kiểm tra EventEffect."""

    def test_event_effect_execute(self):
        """EventEffect.execute trả về EffectResult."""
        from midicoder.packs.cp13_workflow_runtime.effects.event import EventEffect
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectResult
        effect = EventEffect(publish="order.created")
        result = effect.execute(data={"order_id": "123"})
        self.assertIsInstance(result, EffectResult)


class TestCommandEffect(TestCase):
    """Kiểm tra CommandEffect."""

    def test_command_effect_execute(self):
        """CommandEffect.execute trả về EffectResult."""
        from midicoder.packs.cp13_workflow_runtime.effects.command import CommandEffect
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectResult
        effect = CommandEffect(execute="approve_order")
        result = effect.execute(data={"order_id": "123"})
        self.assertIsInstance(result, EffectResult)


class TestNotificationEffect(TestCase):
    """Kiểm tra NotificationEffect."""

    def test_notification_effect_execute(self):
        """NotificationEffect.execute trả về EffectResult."""
        from midicoder.packs.cp13_workflow_runtime.effects.notification import NotificationEffect
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectResult
        effect = NotificationEffect(channel="email")
        result = effect.execute(data={"recipient": "user@test.com"})
        self.assertIsInstance(result, EffectResult)


class TestAuditEffect(TestCase):
    """Kiểm tra AuditEffect."""

    def test_audit_effect_execute(self):
        """AuditEffect.execute trả về EffectResult."""
        from midicoder.packs.cp13_workflow_runtime.effects.audit import AuditEffect
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectResult
        effect = AuditEffect(action="workflow_transition")
        result = effect.execute(data={"from": "draft", "to": "submitted"})
        self.assertIsInstance(result, EffectResult)


class TestCompensationEffect(TestCase):
    """Kiểm tra CompensationEffect."""

    def test_compensation_effect_execute(self):
        """CompensationEffect.execute trả về EffectResult."""
        from midicoder.packs.cp13_workflow_runtime.effects.compensation import CompensationEffect
        from midicoder.packs.cp13_workflow_runtime.effects.base import EffectResult
        effect = CompensationEffect(rollback="cancel_order")
        result = effect.execute(data={"order_id": "123"})
        self.assertIsInstance(result, EffectResult)
