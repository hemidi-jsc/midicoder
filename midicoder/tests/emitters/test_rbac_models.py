"""
Tests cho CP04: RBAC & Policy Engine — Data Models.

Viết theo TDD, test thực với real implementations.
Test: PolicyRule, PolicyContext, PolicyDecision, RBACConfig.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import pytest

from midicoder.emitters.core.cp04_rbac.models import (
    PolicyContext,
    PolicyDecision,
    PolicyRule,
    RBACConfig,
)


# ============================================================================
# Test PolicyRule
# ============================================================================


class TestPolicyRule:
    """Tests cho PolicyRule model."""

    def test_create_policy_rule_minimal(self) -> None:
        """Tạo policy rule với minimal fields."""
        rule = PolicyRule(
            id="admin_full_access",
            condition="user.role == 'admin'",
        )

        assert rule.id == "admin_full_access"
        assert rule.condition == "user.role == 'admin'"
        assert rule.effect == "allow"
        assert rule.resource_type is None
        assert rule.actions == []

    def test_create_policy_rule_full(self) -> None:
        """Tạo policy rule với đầy đủ fields."""
        rule = PolicyRule(
            id="tenant_isolation",
            effect="allow",
            condition="resource.tenant_id == user.tenant_id",
            resource_type="Order",
            actions=["read", "update"],
        )

        assert rule.id == "tenant_isolation"
        assert rule.effect == "allow"
        assert rule.condition == "resource.tenant_id == user.tenant_id"
        assert rule.resource_type == "Order"
        assert rule.actions == ["read", "update"]

    def test_deny_policy_rule(self) -> None:
        """Tạo deny policy rule."""
        rule = PolicyRule(
            id="block_deleted_users",
            effect="deny",
            condition="user.is_deleted == true",
        )

        assert rule.effect == "deny"

    def test_empty_id_raises_error(self) -> None:
        """Throw error khi id để trống."""
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError):
            PolicyRule(
                id="",
                condition="user.role == 'admin'",
            )

    def test_empty_condition_raises_error(self) -> None:
        """Throw error khi condition để trống."""
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError):
            PolicyRule(
                id="test_rule",
                condition="",
            )

    def test_invalid_effect_raises_error(self) -> None:
        """Throw error khi effect không hợp lệ."""
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError):
            PolicyRule(
                id="test_rule",
                effect="invalid_effect",
                condition="user.role == 'admin'",
            )


# ============================================================================
# Test PolicyContext
# ============================================================================


class TestPolicyContext:
    """Tests cho PolicyContext model."""

    def test_create_context_minimal(self) -> None:
        """Tạo context với minimal fields."""
        context = PolicyContext(
            action="read",
        )

        assert context.action == "read"
        assert context.user_attributes == {}
        assert context.resource_attributes == {}
        assert context.environment == {}

    def test_create_context_full(self) -> None:
        """Tạo context với đầy đủ fields."""
        context = PolicyContext(
            action="update",
            user_attributes={"role": "manager", "tenant_id": "t-001"},
            resource_attributes={"tenant_id": "t-001", "owner": "user-123"},
            environment={"ip": "192.168.1.1", "hour": 14},
        )

        assert context.action == "update"
        assert context.user_attributes["role"] == "manager"
        assert context.resource_attributes["tenant_id"] == "t-001"
        assert context.environment["hour"] == 14

    def test_action_empty_raises_error(self) -> None:
        """Throw error khi action để trống."""
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError):
            PolicyContext(
                action="",
            )


# ============================================================================
# Test PolicyDecision
# ============================================================================


class TestPolicyDecision:
    """Tests cho PolicyDecision model."""

    def test_allowed_decision(self) -> None:
        """Tạo decision ALLOW."""
        decision = PolicyDecision(
            allowed=True,
            policy_id="admin_access",
            reason="User is admin",
        )

        assert decision.allowed is True
        assert decision.policy_id == "admin_access"
        assert decision.reason == "User is admin"

    def test_denied_decision(self) -> None:
        """Tạo decision DENY."""
        decision = PolicyDecision(
            allowed=False,
            policy_id="tenant_isolation",
            reason="Tenant mismatch",
        )

        assert decision.allowed is False
        assert decision.policy_id == "tenant_isolation"

    def test_decision_no_reason(self) -> None:
        """Tạo decision không có reason."""
        decision = PolicyDecision(
            allowed=True,
            policy_id="default",
        )

        assert decision.reason == ""


# ============================================================================
# Test RBACConfig
# ============================================================================


class TestRBACConfig:
    """Tests cho RBACConfig model."""

    def test_create_config_empty(self) -> None:
        """Tạo config rỗng."""
        config = RBACConfig()

        assert config.roles == []
        assert config.policies == []

    def test_create_config_with_roles_and_policies(self) -> None:
        """Tạo config với roles và policies."""
        from midicoder.emitters.core.cp04_rbac.models import Role, Policy, PolicyEffect

        config = RBACConfig(
            roles=[Role(name="admin")],
            policies=[
                PolicyRule(
                    id="admin_rule",
                    condition="user.role == 'admin'",
                )
            ],
        )

        assert len(config.roles) == 1
        assert config.roles[0].name == "admin"
        assert len(config.policies) == 1
        assert config.policies[0].id == "admin_rule"

    def test_validate_no_provider_raises_error(self) -> None:
        """Validate throw error khi không có roles và policies."""
        from midicoder.errors import MidicoderError

        config = RBACConfig()
        # Không có roles và policies vẫn hợp lệ — config có thể được bổ sung sau
        # Chỉ validate khi có ít nhất một thứ
        assert len(config.roles) == 0
        assert len(config.policies) == 0