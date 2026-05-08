"""
Tests cho CP04: RBAC & Policy Engine — Integration Tests.

Viết theo TDD, test thực với real implementations.
Test: RBACParser, PolicyEngine, RBACEngine, và 4 emitters.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import pytest
from pathlib import Path
import tempfile

from midicoder.emitters.core.rbac.models import (
    Role, Policy, PolicyEffect,
    PolicyContext,
    PolicyDecision,
    PolicyRule,
    RBACConfig,
)
from midicoder.emitters.core.rbac.parser import RBACParser
from midicoder.emitters.core.rbac.rbac_engine import RBACEngine
from midicoder.emitters.core.rbac.policy_engine import PolicyEngine
from midicoder.emitters.core.rbac.fastapi import FastAPIRBACEmitter
from midicoder.emitters.core.rbac.nestjs import NestJSRBACEmitter
from midicoder.emitters.core.rbac.angular import AngularRBACEmitter
from midicoder.emitters.core.rbac.react import ReactRBACEmitter


# ============================================================================
# Test RBACParser
# ============================================================================


class TestRBACParser:
    """Tests cho RBACParser."""

    def test_parse_empty_yaml(self) -> None:
        """Parse empty YAML trả về list rỗng."""
        parser = RBACParser()
        result = parser.parse("")
        assert result == []

    def test_parse_roles_only(self) -> None:
        """Parse YAML chỉ có roles."""
        parser = RBACParser()
        yaml_str = """
roles:
  - id: admin
    permissions:
      - order:*
      - user:*
  - id: viewer
    permissions:
      - order:read
"""
        result = parser.parse(yaml_str)
        assert len(result) == 2
        assert isinstance(result[0], Role)
        assert result[0].name == "admin"
        assert "order:*" in result[0].permissions

    def test_parse_policies_only(self) -> None:
        """Parse YAML chỉ có guards/policies."""
        parser = RBACParser()
        yaml_str = """
guards:
  - id: tenant_isolation
    type: rbac
    effect: allow
    condition: resource.tenant_id == user.tenant_id
    resource_type: Order
    actions:
      - read
      - update
"""
        result = parser.parse(yaml_str)
        assert len(result) == 1
        assert isinstance(result[0], PolicyRule)
        assert result[0].id == "tenant_isolation"

    def test_parse_config(self) -> None:
        """Parse config hoàn chỉnh."""
        parser = RBACParser()
        yaml_str = """
roles:
  - id: admin
    permissions:
      - order:*
guards:
  - id: admin_policy
    type: rbac
    effect: allow
    condition: user.role == 'admin'
"""
        config = parser.parse_config(yaml_str)
        assert len(config.roles) == 1
        assert len(config.policies) == 1
        assert config.roles[0].name == "admin"


# ============================================================================
# Test PolicyEngine
# ============================================================================


class TestPolicyEngine:
    """Tests cho PolicyEngine (ABAC expression DSL)."""

    def test_simple_equality_allow(self) -> None:
        """Test condition: user.role == 'admin'."""
        config = RBACConfig(policies=[
            PolicyRule(id="admin_access", condition="user.role == 'admin'"),
        ])
        engine = PolicyEngine(config)
        context = PolicyContext(
            action="read",
            user_attributes={"role": "admin"},
        )
        decision = engine.evaluate(context)
        assert decision.allowed is True
        assert decision.policy_id == "admin_access"

    def test_simple_equality_deny(self) -> None:
        """Test condition không match."""
        config = RBACConfig(policies=[
            PolicyRule(id="admin_access", condition="user.role == 'admin'"),
        ])
        engine = PolicyEngine(config)
        context = PolicyContext(
            action="read",
            user_attributes={"role": "user"},
        )
        decision = engine.evaluate(context)
        assert decision.allowed is False

    def test_tenant_isolation(self) -> None:
        """Test tenant isolation: resource.tenant_id == user.tenant_id."""
        config = RBACConfig(policies=[
            PolicyRule(
                id="tenant_iso",
                condition="resource.tenant_id == user.tenant_id",
            ),
        ])
        engine = PolicyEngine(config)
        context = PolicyContext(
            action="read",
            user_attributes={"tenant_id": "t-001"},
            resource_attributes={"tenant_id": "t-001"},
        )
        decision = engine.evaluate(context)
        assert decision.allowed is True

    def test_deny_takes_precedence(self) -> None:
        """Test DENY policy có precedence cao hơn ALLOW."""
        config = RBACConfig(policies=[
            PolicyRule(id="allow_all", condition="user.role == 'user'"),
            PolicyRule(id="deny_banned", effect="deny", condition="user.is_banned == true"),
        ])
        engine = PolicyEngine(config)
        context = PolicyContext(
            action="read",
            user_attributes={"role": "user", "is_banned": True},
        )
        decision = engine.evaluate(context)
        assert decision.allowed is False
        assert decision.policy_id == "deny_banned"

    def test_and_condition(self) -> None:
        """Test AND condition."""
        config = RBACConfig(policies=[
            PolicyRule(
                id="combo",
                condition="user.role == 'manager' AND resource.tenant_id == user.tenant_id",
            ),
        ])
        engine = PolicyEngine(config)
        context = PolicyContext(
            action="update",
            user_attributes={"role": "manager", "tenant_id": "t-001"},
            resource_attributes={"tenant_id": "t-001"},
        )
        decision = engine.evaluate(context)
        assert decision.allowed is True

    def test_or_condition(self) -> None:
        """Test OR condition."""
        config = RBACConfig(policies=[
            PolicyRule(
                id="admin_or_owner",
                condition="user.role == 'admin' OR resource.owner == user.id",
            ),
        ])
        engine = PolicyEngine(config)
        context = PolicyContext(
            action="delete",
            user_attributes={"role": "user", "id": "u-123"},
            resource_attributes={"owner": "u-123"},
        )
        decision = engine.evaluate(context)
        assert decision.allowed is True

    def test_ne_operator(self) -> None:
        """Test != operator."""
        config = RBACConfig(policies=[
            PolicyRule(id="not_guest", condition="user.role != 'guest'"),
        ])
        engine = PolicyEngine(config)
        context = PolicyContext(
            action="read",
            user_attributes={"role": "admin"},
        )
        decision = engine.evaluate(context)
        assert decision.allowed is True

    def test_number_comparison(self) -> None:
        """Test số (<, >, <=, >=)."""
        config = RBACConfig(policies=[
            PolicyRule(id="hour_check", condition="env.hour >= 8 AND env.hour <= 18"),
        ])
        engine = PolicyEngine(config)
        context = PolicyContext(
            action="read",
            environment={"hour": 14},
        )
        decision = engine.evaluate(context)
        assert decision.allowed is True

    def test_single_policy_evaluate(self) -> None:
        """Test evaluate_single."""
        config = RBACConfig()
        engine = PolicyEngine(config)
        policy = PolicyRule(id="test", condition="user.role == 'admin'")
        context = PolicyContext(
            action="read",
            user_attributes={"role": "admin"},
        )
        decision = engine.evaluate_single(policy, context)
        assert decision.allowed is True

    def test_default_deny(self) -> None:
        """Test default deny khi không có policy match."""
        config = RBACConfig(policies=[])
        engine = PolicyEngine(config)
        context = PolicyContext(action="read")
        decision = engine.evaluate(context)
        assert decision.allowed is False


# ============================================================================
# Test RBACEngine
# ============================================================================


class TestRBACEngine:
    """Tests cho RBACEngine (role hierarchy)."""

    def test_direct_role_match(self) -> None:
        """Test role match trực tiếp."""
        config = RBACConfig(roles=[Role(name="admin")])
        engine = RBACEngine(config)
        assert engine.check_role(["admin"], "admin") is True

    def test_role_no_match(self) -> None:
        """Test role không match."""
        config = RBACConfig(roles=[Role(name="admin")])
        engine = RBACEngine(config)
        assert engine.check_role(["user"], "admin") is False

    def test_role_inheritance(self) -> None:
        """Test role inheritance (superadmin extends admin)."""
        config = RBACConfig(roles=[
            Role(name="admin"),
            Role(name="superadmin", parent_roles=["admin"]),
        ])
        engine = RBACEngine(config)
        # superadmin có admin (qua inheritance)
        assert engine.check_role(["superadmin"], "admin") is True

    def test_permission_check(self) -> None:
        """Test permission check."""
        config = RBACConfig(roles=[
            Role(name="admin", permissions=["order.create", "order.read"]),
        ])
        engine = RBACEngine(config)
        assert engine.check_permission(["admin"], "Order", "create") is True
        assert engine.check_permission(["admin"], "Order", "delete") is False

    def test_permission_inheritance(self) -> None:
        """Test permission inheritance."""
        config = RBACConfig(roles=[
            Role(name="viewer", permissions=["order.read"]),
            Role(name="editor", permissions=["order.create"], parent_roles=["viewer"]),
        ])
        engine = RBACEngine(config)
        # editor thừa kế order.read từ viewer
        assert engine.check_permission(["editor"], "Order", "read") is True
        assert engine.check_permission(["editor"], "Order", "create") is True

    def test_effective_roles(self) -> None:
        """Test get_effective_roles."""
        config = RBACConfig(roles=[
            Role(name="member", permissions=["order.read"]),
            Role(name="user", permissions=["order.create"], parent_roles=["member"]),
        ])
        engine = RBACEngine(config)
        effective = engine.get_effective_roles(["user"])
        assert "user" in effective
        assert "member" in effective


# ============================================================================
# Test Emitters
# ============================================================================


class TestFastAPIRBACEmitter:
    """Tests cho FastAPIRBACEmitter."""

    def test_generate(self) -> None:
        """Test generate code."""
        emitter = FastAPIRBACEmitter(None)
        result = emitter.generate()
        assert "app/core/rbac/__init__.py" in result
        assert "app/core/rbac/service.py" in result
        assert "app/core/rbac/guards.py" in result

    def test_emit(self) -> None:
        """Test emit files."""
        emitter = FastAPIRBACEmitter(None)
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit(Path(tmpdir))
            assert len(files) == 3
            for f in files:
                assert f.path.exists()


class TestNestJSRBACEmitter:
    """Tests cho NestJSRBACEmitter."""

    def test_generate(self) -> None:
        """Test generate code."""
        emitter = NestJSRBACEmitter(None)
        result = emitter.generate()
        assert len(result) == 5
        assert "src/core/rbac/rbac.module.ts" in result


class TestAngularRBACEmitter:
    """Tests cho AngularRBACEmitter."""

    def test_generate(self) -> None:
        """Test generate code."""
        emitter = AngularRBACEmitter(None)
        result = emitter.generate()
        assert len(result) == 3
        assert "src/app/core/rbac/rbac.service.ts" in result


class TestReactRBACEmitter:
    """Tests cho ReactRBACEmitter."""

    def test_generate(self) -> None:
        """Test generate code."""
        emitter = ReactRBACEmitter(None)
        result = emitter.generate()
        assert len(result) == 3
        assert "src/core/rbac/useAuth.ts" in result

    def test_emit(self) -> None:
        """Test emit files."""
        emitter = ReactRBACEmitter(None)
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit(Path(tmpdir))
            assert len(files) == 3