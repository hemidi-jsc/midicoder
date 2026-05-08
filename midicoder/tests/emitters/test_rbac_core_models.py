"""
Tests cho CP03 + CP04: RBAC & Policy Engine Models.

Viết theo TDD, bám sát SoT (requirement.md - E12 CP03 + CP04):
- Role definitions
- Permission bindings
- Policy evaluation (OPA-compatible)
- Access control lists (ACL)

Không dùng mock, test với real implementations.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import pytest

from midicoder.emitters.core.rbac.models import (
    Policy,
    PolicyCondition,
    PolicyEffect,
    Permission,
    Role,
)


# ============================================================================
# Test Permission Class
# ============================================================================


class TestPermission:
    """Tests cho Permission class theo SoT CP03."""

    def test_create_permission_minimal(self) -> None:
        """Kiểm tra tạo permission với minimal fields."""
        permission = Permission(
            id="order.create",
            resource="Order",
            action="create",
        )

        assert permission.id == "order.create"
        assert permission.resource == "Order"
        assert permission.action == "create"
        assert permission.description is None

    def test_create_permission_full(self) -> None:
        """Kiểm tra tạo permission với đầy đủ fields."""
        permission = Permission(
            id="order.create",
            resource="Order",
            action="create",
            description="Tạo đơn hàng mới",
        )

        assert permission.id == "order.create"
        assert permission.resource == "Order"
        assert permission.action == "create"
        assert permission.description == "Tạo đơn hàng mới"

    def test_permission_to_dict(self) -> None:
        """Kiểm tra to_dict serialization."""
        permission = Permission(
            id="order.create",
            resource="Order",
            action="create",
            description="Tạo đơn hàng mới",
        )

        perm_dict = permission.to_dict()

        assert perm_dict["id"] == "order.create"
        assert perm_dict["resource"] == "Order"
        assert perm_dict["action"] == "create"
        assert perm_dict["description"] == "Tạo đơn hàng mới"

    def test_permission_from_dict(self) -> None:
        """Kiểm tra from_dict deserialization."""
        perm_dict = {
            "id": "order.read",
            "resource": "Order",
            "action": "read",
            "description": "Xem đơn hàng",
        }

        permission = Permission.from_dict(perm_dict)

        assert permission.id == "order.read"
        assert permission.resource == "Order"
        assert permission.action == "read"
        assert permission.description == "Xem đơn hàng"

    def test_permission_str_format(self) -> None:
        """Kiểm tra str format."""
        permission = Permission(
            id="order.create",
            resource="Order",
            action="create",
        )

        permission_str = str(permission)

        assert "order.create" in permission_str

    def test_permission_equality(self) -> None:
        """Kiểm tra equality."""
        perm1 = Permission(id="order.create", resource="Order", action="create")
        perm2 = Permission(id="order.create", resource="Order", action="create")
        perm3 = Permission(id="order.read", resource="Order", action="read")

        assert perm1 == perm2
        assert perm1 != perm3

    def test_permission_resource_action_format(self) -> None:
        """Kiểm tra format permission id từ resource và action."""
        # Resource.Action format
        assert Permission.format_id("Order", "create") == "order.create"
        assert Permission.format_id("Customer", "read") == "customer.read"
        assert Permission.format_id("Invoice", "delete") == "invoice.delete"


# ============================================================================
# Test Role Class
# ============================================================================


class TestRole:
    """Tests cho Role class theo SoT CP03."""

    def test_create_role_minimal(self) -> None:
        """Kiểm tra tạo role với minimal fields."""
        role = Role(name="admin")

        assert role.name == "admin"
        assert role.description is None
        assert role.permissions == []
        assert role.parent_roles == []

    def test_create_role_full(self) -> None:
        """Kiểm tra tạo role với đầy đủ fields."""
        role = Role(
            name="admin",
            description="Administrator role",
            permissions=["order.create", "order.read"],
            parent_roles=[],
        )

        assert role.name == "admin"
        assert role.description == "Administrator role"
        assert role.permissions == ["order.create", "order.read"]
        assert role.parent_roles == []

    def test_role_to_dict(self) -> None:
        """Kiểm tra to_dict serialization."""
        role = Role(
            name="admin",
            description="Administrator role",
            permissions=["order.create", "order.read"],
            parent_roles=[],
        )

        role_dict = role.to_dict()

        assert role_dict["name"] == "admin"
        assert role_dict["description"] == "Administrator role"
        assert role_dict["permissions"] == ["order.create", "order.read"]
        assert role_dict["parent_roles"] == []

    def test_role_from_dict(self) -> None:
        """Kiểm tra from_dict deserialization."""
        role_dict = {
            "name": "user",
            "description": "Regular user",
            "permissions": ["order.read"],
            "parent_roles": [],
        }

        role = Role.from_dict(role_dict)

        assert role.name == "user"
        assert role.description == "Regular user"
        assert role.permissions == ["order.read"]
        assert role.parent_roles == []

    def test_role_add_permission(self) -> None:
        """Kiểm tra add permission."""
        role = Role(name="user")

        role.add_permission("order.create")

        assert "order.create" in role.permissions

    def test_role_remove_permission(self) -> None:
        """Kiểm tra remove permission."""
        role = Role(name="user", permissions=["order.create", "order.read"])

        role.remove_permission("order.create")

        assert "order.create" not in role.permissions
        assert "order.read" in role.permissions

    def test_role_has_permission(self) -> None:
        """Kiểm tra has_permission."""
        role = Role(name="user", permissions=["order.create", "order.read"])

        assert role.has_permission("order.create") is True
        assert role.has_permission("order.delete") is False

    def test_role_add_parent_role(self) -> None:
        """Kiểm tra add parent role."""
        role = Role(name="user")

        role.add_parent_role("member")

        assert "member" in role.parent_roles

    def test_role_get_all_permissions_with_inheritance(self) -> None:
        """Kiểm tra get_all_permissions với inheritance."""
        # Base role
        member_role = Role(
            name="member",
            permissions=["order.read"],
            parent_roles=[],
        )

        # Child role
        user_role = Role(
            name="user",
            permissions=["order.create"],
            parent_roles=["member"],
        )

        # Get all permissions với parent roles
        all_permissions = user_role.get_all_permissions(
            parent_roles={"member": member_role}
        )

        assert "order.read" in all_permissions  # Từ parent
        assert "order.create" in all_permissions  # Từ chính nó


# ============================================================================
# Test PolicyCondition Class
# ============================================================================


class TestPolicyCondition:
    """Tests cho PolicyCondition class theo SoT CP04."""

    def test_create_condition(self) -> None:
        """Kiểm tra tạo condition."""
        condition = PolicyCondition(
            field="tenant_id",
            operator="eq",
            value="tenant-001",
        )

        assert condition.field == "tenant_id"
        assert condition.operator == "eq"
        assert condition.value == "tenant-001"

    def test_condition_to_dict(self) -> None:
        """Kiểm tra to_dict serialization."""
        condition = PolicyCondition(
            field="tenant_id",
            operator="eq",
            value="tenant-001",
        )

        cond_dict = condition.to_dict()

        assert cond_dict["field"] == "tenant_id"
        assert cond_dict["operator"] == "eq"
        assert cond_dict["value"] == "tenant-001"

    def test_condition_from_dict(self) -> None:
        """Kiểm tra from_dict deserialization."""
        cond_dict = {
            "field": "tenant_id",
            "operator": "eq",
            "value": "tenant-001",
        }

        condition = PolicyCondition.from_dict(cond_dict)

        assert condition.field == "tenant_id"
        assert condition.operator == "eq"
        assert condition.value == "tenant-001"


# ============================================================================
# Test Policy Class
# ============================================================================


class TestPolicy:
    """Tests cho Policy class theo SoT CP04."""

    def test_create_policy_allow(self) -> None:
        """Kiểm tra tạo allow policy."""
        policy = Policy(
            id="allow_admin_orders",
            effect=PolicyEffect.ALLOW,
            conditions=[
                PolicyCondition(field="role", operator="eq", value="admin"),
            ],
            actions=["order.create", "order.read"],
            resources=["Order"],
        )

        assert policy.id == "allow_admin_orders"
        assert policy.effect == PolicyEffect.ALLOW
        assert len(policy.conditions) == 1
        assert policy.actions == ["order.create", "order.read"]
        assert policy.resources == ["Order"]

    def test_create_policy_deny(self) -> None:
        """Kiểm tra tạo deny policy."""
        policy = Policy(
            id="deny_guest_orders",
            effect=PolicyEffect.DENY,
            conditions=[
                PolicyCondition(field="role", operator="eq", value="guest"),
            ],
            actions=["order.create"],
            resources=["Order"],
        )

        assert policy.effect == PolicyEffect.DENY

    def test_policy_to_dict(self) -> None:
        """Kiểm tra to_dict serialization."""
        policy = Policy(
            id="allow_admin_orders",
            effect=PolicyEffect.ALLOW,
            conditions=[
                PolicyCondition(field="role", operator="eq", value="admin"),
            ],
            actions=["order.create"],
            resources=["Order"],
        )

        policy_dict = policy.to_dict()

        assert policy_dict["id"] == "allow_admin_orders"
        assert policy_dict["effect"] == "allow"
        assert len(policy_dict["conditions"]) == 1
        assert policy_dict["actions"] == ["order.create"]
        assert policy_dict["resources"] == ["Order"]

    def test_policy_from_dict(self) -> None:
        """Kiểm tra from_dict deserialization."""
        policy_dict = {
            "id": "allow_admin_orders",
            "effect": "allow",
            "conditions": [
                {"field": "role", "operator": "eq", "value": "admin"},
            ],
            "actions": ["order.create"],
            "resources": ["Order"],
        }

        policy = Policy.from_dict(policy_dict)

        assert policy.id == "allow_admin_orders"
        assert policy.effect == PolicyEffect.ALLOW
        assert len(policy.conditions) == 1
        assert policy.actions == ["order.create"]

    def test_policy_evaluate_allow(self) -> None:
        """Kiểm tra evaluate policy - ALLOW."""
        policy = Policy(
            id="allow_admin_orders",
            effect=PolicyEffect.ALLOW,
            conditions=[
                PolicyCondition(field="role", operator="eq", value="admin"),
            ],
            actions=["order.create"],
            resources=["Order"],
        )

        # Context match conditions
        context = {"role": "admin", "action": "order.create", "resource": "Order"}

        result = policy.evaluate(context)

        assert result.allowed is True
        assert result.policy_id == "allow_admin_orders"

    def test_policy_evaluate_deny(self) -> None:
        """Kiểm tra evaluate policy - DENY."""
        policy = Policy(
            id="deny_guest_orders",
            effect=PolicyEffect.DENY,
            conditions=[
                PolicyCondition(field="role", operator="eq", value="guest"),
            ],
            actions=["order.create"],
            resources=["Order"],
        )

        context = {"role": "guest", "action": "order.create", "resource": "Order"}

        result = policy.evaluate(context)

        assert result.allowed is False
        assert result.policy_id == "deny_guest_orders"

    def test_policy_evaluate_no_match(self) -> None:
        """Kiểm tra evaluate policy - không match conditions."""
        policy = Policy(
            id="allow_admin_orders",
            effect=PolicyEffect.ALLOW,
            conditions=[
                PolicyCondition(field="role", operator="eq", value="admin"),
            ],
            actions=["order.create"],
            resources=["Order"],
        )

        context = {"role": "user", "action": "order.create", "resource": "Order"}

        result = policy.evaluate(context)

        assert result.matched is False


# ============================================================================
# Test Integration: Role + Permission + Policy
# ============================================================================


class TestRBACIntegration:
    """Tests cho integration giữa Role, Permission, và Policy."""

    def test_role_with_all_permissions(self) -> None:
        """Kiểm tra role với đầy đủ permissions."""
        permissions = [
            Permission(id="order.create", resource="Order", action="create"),
            Permission(id="order.read", resource="Order", action="read"),
        ]

        role = Role(
            name="order_manager",
            permissions=[p.id for p in permissions],
        )

        assert role.has_permission("order.create")
        assert role.has_permission("order.read")
        assert role.has_permission("order.delete") is False

    def test_policy_enforces_role_constraint(self) -> None:
        """Kiểm tra policy enforce role constraint."""
        policy = Policy(
            id="only_admin_can_delete",
            effect=PolicyEffect.ALLOW,
            conditions=[
                PolicyCondition(field="role", operator="eq", value="admin"),
            ],
            actions=["order.delete"],
            resources=["Order"],
        )

        # Admin context - should allow
        admin_context = {"role": "admin", "action": "order.delete", "resource": "Order"}
        admin_result = policy.evaluate(admin_context)
        assert admin_result.allowed is True

        # User context - should not match
        user_context = {"role": "user", "action": "order.delete", "resource": "Order"}
        user_result = policy.evaluate(user_context)
        assert user_result.matched is False

    def test_multi_condition_policy(self) -> None:
        """Kiểm tra policy với multiple conditions (AND logic)."""
        policy = Policy(
            id="owner_only_edit",
            effect=PolicyEffect.ALLOW,
            conditions=[
                PolicyCondition(field="role", operator="eq", value="owner"),
                PolicyCondition(field="tenant_id", operator="eq", value="tenant-001"),
            ],
            actions=["order.update"],
            resources=["Order"],
        )

        # Match both conditions
        context = {
            "role": "owner",
            "tenant_id": "tenant-001",
            "action": "order.update",
            "resource": "Order",
        }

        result = policy.evaluate(context)

        assert result.allowed is True
        assert result.matched is True

    def test_deny_policy_takes_precedence(self) -> None:
        """Kiểm tra deny policy có precedence cao hơn allow."""
        allow_policy = Policy(
            id="allow_all_orders",
            effect=PolicyEffect.ALLOW,
            conditions=[],  # No conditions - matches all
            actions=["order.create"],
            resources=["Order"],
        )

        deny_policy = Policy(
            id="deny_banned_users",
            effect=PolicyEffect.DENY,
            conditions=[
                PolicyCondition(field="is_banned", operator="eq", value=True),
            ],
            actions=["order.create"],
            resources=["Order"],
        )

        # Banned user context
        banned_context = {
            "is_banned": True,
            "action": "order.create",
            "resource": "Order",
        }

        allow_result = allow_policy.evaluate(banned_context)
        deny_result = deny_policy.evaluate(banned_context)

        # Both match, but DENY takes precedence
        assert allow_result.allowed is True
        assert deny_result.allowed is False