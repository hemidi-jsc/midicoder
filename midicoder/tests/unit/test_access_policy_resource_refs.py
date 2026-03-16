from __future__ import annotations

from midicoder.dsl.schemas.access_policy_model import Permission


def test_permission_resource_normalizes_legacy_entity_ref() -> None:
    permission = Permission(
        id="view_order",
        description="view order",
        resource="Entity:Order",
        action="read",
    )

    assert permission.resource == "entity:Order"


def test_permission_resource_accepts_namespaced_api_ref() -> None:
    permission = Permission(
        id="call_order_api",
        description="call order api",
        resource="api:/orders/{id}",
        action="read",
    )

    assert permission.resource == "api:/orders/{id}"
