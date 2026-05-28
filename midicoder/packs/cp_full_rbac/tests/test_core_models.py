"""
Tests cho CP04: Models — Permission, Role, PolicyCondition, Policy, PolicyEvaluationResult.

Test thực với real implementations. Không dùng mock.
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp_full_rbac.models import (
    Policy,
    PolicyCondition,
    PolicyEffect,
    PolicyEvaluationResult,
    Permission,
    Role,
)


class TestPermission:
    def test_create_minimal(self) -> None:
        p = Permission(id="order.create", resource="Order", action="create")
        assert p.id == "order.create"
        assert p.resource == "Order"
        assert p.action == "create"
        assert p.description is None

    def test_create_full(self) -> None:
        p = Permission(id="x", resource="R", action="a", description="desc")
        assert p.description == "desc"

    def test_to_dict_and_from_dict_roundtrip(self) -> None:
        p = Permission(id="a.b", resource="A", action="b", description="d")
        rd = p.from_dict(p.to_dict())
        assert rd.id == "a.b"
        assert rd.resource == "A"
        assert rd.action == "b"
        assert rd.description == "d"

    def test_str_contains_id(self) -> None:
        assert "order.create" in str(Permission(id="order.create", resource="O", action="c"))

    def test_equality(self) -> None:
        a = Permission(id="x", resource="R", action="A")
        b = Permission(id="x", resource="R", action="A")
        c = Permission(id="y", resource="R", action="A")
        assert a == b
        assert a != c
        assert a != "not a permission"

    def test_format_id_lowercases_resource(self) -> None:
        assert Permission.format_id("Order", "create") == "order.create"
        assert Permission.format_id("Customer", "read") == "customer.read"


class TestRole:
    def test_create_minimal(self) -> None:
        r = Role(name="admin")
        assert r.permissions == []
        assert r.parent_roles == []

    def test_create_full(self) -> None:
        r = Role(name="admin", description="Admin", permissions=["p1"], parent_roles=["base"])
        assert r.description == "Admin"
        assert r.permissions == ["p1"]
        assert r.parent_roles == ["base"]

    def test_add_permission_no_duplicate(self) -> None:
        r = Role(name="x", permissions=["p1"])
        r.add_permission("p1")  # dup
        r.add_permission("p2")
        assert r.permissions == ["p1", "p2"]

    def test_remove_permission(self) -> None:
        r = Role(name="x", permissions=["p1", "p2"])
        r.remove_permission("p1")
        assert r.permissions == ["p2"]
        r.remove_permission("nonexistent")  # no-op

    def test_has_permission(self) -> None:
        r = Role(name="x", permissions=["p1"])
        assert r.has_permission("p1") is True
        assert r.has_permission("p2") is False

    def test_add_parent_role_no_duplicate(self) -> None:
        r = Role(name="x", parent_roles=["base"])
        r.add_parent_role("base")  # dup
        r.add_parent_role("super")
        assert r.parent_roles == ["base", "super"]

    def test_inheritance(self) -> None:
        base = Role(name="base", permissions=["read"])
        child = Role(name="child", permissions=["write"], parent_roles=["base"])
        all_perms = child.get_all_permissions({"base": base})
        assert "read" in all_perms
        assert "write" in all_perms

    def test_deep_inheritance(self) -> None:
        a = Role(name="a", permissions=["a"])
        b = Role(name="b", permissions=["b"], parent_roles=["a"])
        c = Role(name="c", permissions=["c"], parent_roles=["b"])
        ctx = {"a": a, "b": b, "c": c}
        assert c.get_all_permissions(ctx) == {"a", "b", "c"}

    def test_no_inheritance_when_parent_missing(self) -> None:
        r = Role(name="x", permissions=["p"], parent_roles=["missing"])
        assert r.get_all_permissions({}) == {"p"}

    def test_get_all_permissions_no_parent_roles_map(self) -> None:
        r = Role(name="x", permissions=["p"], parent_roles=["base"])
        assert r.get_all_permissions(None) == {"p"}

    def test_to_dict_from_dict_roundtrip(self) -> None:
        r = Role(name="x", description="d", permissions=["a"], parent_roles=["b"])
        rd = r.from_dict(r.to_dict())
        assert rd.name == "x"
        assert rd.description == "d"
        assert rd.permissions == ["a"]
        assert rd.parent_roles == ["b"]


class TestPolicyEffect:
    def test_enum_values(self) -> None:
        assert PolicyEffect.ALLOW.value == "allow"
        assert PolicyEffect.DENY.value == "deny"

    def test_from_string(self) -> None:
        assert PolicyEffect("allow") == PolicyEffect.ALLOW
        assert PolicyEffect("deny") == PolicyEffect.DENY


class TestPolicyCondition:
    def test_create_and_roundtrip(self) -> None:
        c = PolicyCondition(field="f", operator="eq", value="v")
        rd = PolicyCondition.from_dict(c.to_dict())
        assert rd.field == "f" and rd.operator == "eq" and rd.value == "v"


class TestPolicyEvaluationResult:
    def test_fields(self) -> None:
        r = PolicyEvaluationResult(policy_id="p1", matched=True, allowed=True, reason="ok")
        assert r.allowed is True
        assert r.policy_id == "p1"
        assert r.matched is True
        assert r.reason == "ok"

    def test_reason_optional(self) -> None:
        r = PolicyEvaluationResult(policy_id="p1", matched=False, allowed=False)
        assert r.reason is None


class TestPolicy:
    def test_create_allow(self) -> None:
        p = Policy(id="x", effect=PolicyEffect.ALLOW)
        assert p.effect == PolicyEffect.ALLOW
        assert p.conditions == []
        assert p.actions == []
        assert p.resources == []
        assert p.description is None

    def test_create_full(self) -> None:
        p = Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[
            PolicyCondition("f", "eq", "v"),
        ], actions=["a"], resources=["r"], description="desc")
        assert p.description == "desc"

    def test_evaluate_no_conditions_always_matches(self) -> None:
        p = Policy(id="x", effect=PolicyEffect.ALLOW)
        assert p.evaluate({}).matched is True
        assert p.evaluate({}).allowed is True

    def test_evaluate_deny(self) -> None:
        p = Policy(id="d", effect=PolicyEffect.DENY, conditions=[])
        assert p.evaluate({}).allowed is False
        assert p.evaluate({}).matched is True

    def test_evaluate_condition_eq_match(self) -> None:
        p = Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[
            PolicyCondition(field="role", operator="eq", value="admin"),
        ])
        assert p.evaluate({"role": "admin"}).matched is True

    def test_evaluate_condition_eq_no_match(self) -> None:
        p = Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[
            PolicyCondition(field="role", operator="eq", value="admin"),
        ])
        assert p.evaluate({"role": "user"}).matched is False

    def test_and_logic(self) -> None:
        p = Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[
            PolicyCondition(field="a", operator="eq", value=1),
            PolicyCondition(field="b", operator="eq", value=2),
        ])
        assert p.evaluate({"a": 1, "b": 2}).matched is True
        assert p.evaluate({"a": 1, "b": 9}).matched is False

    def test_all_operators(self) -> None:
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("v", "ne", 3)]).evaluate({"v": 5}).matched
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("v", "gt", 3)]).evaluate({"v": 5}).matched
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("v", "gte", 5)]).evaluate({"v": 5}).matched
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("v", "lt", 10)]).evaluate({"v": 5}).matched
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("v", "lte", 5)]).evaluate({"v": 5}).matched
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("v", "in", [1, 5, 9])]).evaluate({"v": 5}).matched
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("v", "not_in", [1, 2])]).evaluate({"v": 5}).matched
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("s", "contains", "world")]).evaluate({"s": "hello world"}).matched
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("s", "starts_with", "hello")]).evaluate({"s": "hello world"}).matched
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("s", "ends_with", "world")]).evaluate({"s": "hello world"}).matched

    def test_none_value_comparison(self) -> None:
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("v", "gt", 3)]).evaluate({"v": None}).matched is False

    def test_in_not_in_with_non_list(self) -> None:
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("v", "in", "not_list")]).evaluate({"v": 1}).matched is False

    def test_contains_starts_ends_with_empty_field(self) -> None:
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("s", "contains", "x")]).evaluate({"s": None}).matched is False
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("s", "starts_with", "x")]).evaluate({"s": None}).matched is False
        assert Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[PolicyCondition("s", "ends_with", "x")]).evaluate({"s": None}).matched is False

    def test_unknown_operator_returns_false(self) -> None:
        p = Policy(id="x", effect=PolicyEffect.ALLOW, conditions=[
            PolicyCondition(field="v", operator="unknown_op", value=1),
        ])
        assert p.evaluate({"v": 1}).matched is False

    def test_to_dict_from_dict_roundtrip(self) -> None:
        p = Policy(id="x", effect=PolicyEffect.DENY, conditions=[
            PolicyCondition("f", "eq", "v"),
        ], actions=["a"], resources=["r"], description="d")
        rd = Policy.from_dict(p.to_dict())
        assert rd.effect == PolicyEffect.DENY
        assert len(rd.conditions) == 1
        assert rd.actions == ["a"]
        assert rd.resources == ["r"]

    def test_from_dict_default_effect(self) -> None:
        rd = Policy.from_dict({"id": "x", "effect": "allow"})
        assert rd.effect == PolicyEffect.ALLOW
