"""
Tests cho CP04: Data Models — PolicyRule, PolicyContext, PolicyDecision, RBACConfig.

Test thực với real implementations. Không dùng mock.
"""

from __future__ import annotations

import pytest

from midicoder.emitters.core.cp04_rbac.models import (
    PolicyContext,
    PolicyDecision,
    PolicyRule,
    RBACConfig,
    Role,
)
from midicoder.errors import MidicoderError


class TestPolicyRule:
    def test_create_minimal(self) -> None:
        rule = PolicyRule(id="admin_full_access", condition="user.role == 'admin'")
        assert rule.id == "admin_full_access"
        assert rule.condition == "user.role == 'admin'"
        assert rule.effect == "allow"
        assert rule.resource_type is None
        assert rule.actions == []

    def test_create_full(self) -> None:
        rule = PolicyRule(
            id="tenant_isolation",
            effect="allow",
            condition="resource.tenant_id == user.tenant_id",
            resource_type="Order",
            actions=["read", "update"],
        )
        assert rule.resource_type == "Order"
        assert rule.actions == ["read", "update"]

    def test_deny_rule(self) -> None:
        rule = PolicyRule(id="block", effect="deny", condition="user.banned == true")
        assert rule.effect == "deny"

    def test_empty_id_raises(self) -> None:
        with pytest.raises(MidicoderError):
            PolicyRule(id="", condition="x == 1")

    def test_empty_condition_raises(self) -> None:
        with pytest.raises(MidicoderError):
            PolicyRule(id="x", condition="")

    def test_invalid_effect_raises(self) -> None:
        with pytest.raises(MidicoderError):
            PolicyRule(id="x", effect="invalid", condition="x == 1")


class TestPolicyContext:
    def test_create_minimal(self) -> None:
        ctx = PolicyContext(action="read")
        assert ctx.action == "read"
        assert ctx.user_attributes == {}
        assert ctx.resource_attributes == {}
        assert ctx.environment == {}

    def test_create_full(self) -> None:
        ctx = PolicyContext(
            action="update",
            user_attributes={"role": "manager", "tenant_id": "t-001"},
            resource_attributes={"tenant_id": "t-001", "owner": "u-123"},
            environment={"ip": "192.168.1.1", "hour": 14},
        )
        assert ctx.user_attributes["role"] == "manager"
        assert ctx.resource_attributes["owner"] == "u-123"
        assert ctx.environment["hour"] == 14

    def test_action_empty_raises(self) -> None:
        with pytest.raises(MidicoderError):
            PolicyContext(action="")

    def test_get_priority_user_then_resource_then_env(self) -> None:
        ctx = PolicyContext(
            action="x",
            user_attributes={"k": "user_val"},
            resource_attributes={"k": "res_val"},
            environment={"k": "env_val"},
        )
        assert ctx.get("k") == "user_val"

    def test_get_from_resource_when_not_in_user(self) -> None:
        ctx = PolicyContext(
            action="x",
            resource_attributes={"k": "res_val"},
        )
        assert ctx.get("k") == "res_val"

    def test_get_from_env_when_not_in_user_or_resource(self) -> None:
        ctx = PolicyContext(action="x", environment={"k": "env_val"})
        assert ctx.get("k") == "env_val"

    def test_get_returns_none_for_missing_key(self) -> None:
        ctx = PolicyContext(action="x")
        assert ctx.get("missing") is None


class TestPolicyDecision:
    def test_allowed(self) -> None:
        d = PolicyDecision(allowed=True, policy_id="p1", reason="ok")
        assert d.allowed is True
        assert d.policy_id == "p1"
        assert d.reason == "ok"

    def test_denied(self) -> None:
        d = PolicyDecision(allowed=False, policy_id="p1", reason="deny")
        assert d.allowed is False

    def test_defaults(self) -> None:
        d = PolicyDecision(allowed=True)
        assert d.policy_id == ""
        assert d.reason == ""


class TestRBACConfig:
    def test_empty(self) -> None:
        c = RBACConfig()
        assert c.roles == []
        assert c.policies == []

    def test_with_data(self) -> None:
        c = RBACConfig(
            roles=[Role(name="admin")],
            policies=[PolicyRule(id="r1", condition="x == 1")],
        )
        assert len(c.roles) == 1
        assert len(c.policies) == 1

    def test_get_role_found(self) -> None:
        c = RBACConfig(roles=[Role(name="admin"), Role(name="user")])
        assert c.get_role("admin").name == "admin"

    def test_get_role_not_found(self) -> None:
        c = RBACConfig(roles=[Role(name="admin")])
        assert c.get_role("missing") is None

    def test_get_policy_found(self) -> None:
        c = RBACConfig(policies=[PolicyRule(id="r1", condition="x == 1")])
        assert c.get_policy("r1").id == "r1"

    def test_get_policy_not_found(self) -> None:
        c = RBACConfig(policies=[PolicyRule(id="r1", condition="x == 1")])
        assert c.get_policy("missing") is None

    def test_get_roles_with_permission(self) -> None:
        c = RBACConfig(roles=[
            Role(name="admin", permissions=["order.create"]),
            Role(name="user", permissions=["order.read"]),
            Role(name="editor", permissions=["order.create", "order.read"]),
        ])
        result = c.get_roles_with_permission("order.create")
        assert len(result) == 2
        names = {r.name for r in result}
        assert "admin" in names
        assert "editor" in names

    def test_get_roles_with_permission_empty(self) -> None:
        c = RBACConfig(roles=[Role(name="x", permissions=["a"])])
        assert c.get_roles_with_permission("missing") == []
