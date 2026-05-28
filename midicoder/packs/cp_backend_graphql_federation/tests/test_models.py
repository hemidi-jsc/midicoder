# coding: utf-8
"""Tests cho CP57 — GraphQL Federation models."""

import pytest
from midicoder.packs.cp_backend_graphql_federation.models import (
    FederationService,
    FederatedField,
    FederatedType,
    FederatedResolver,
    GatewayConfig,
)


# =============================================================================
# FederationService
# =============================================================================

class TestFederationService:
    def test_creation_with_defaults(self):
        svc = FederationService(id="svc-1", name="user-service", url="http://localhost:4001")
        assert svc.id == "svc-1"
        assert svc.name == "user-service"
        assert svc.url == "http://localhost:4001"
        assert svc.schema_path == ""
        assert svc.health_check == "/health"
        assert svc.port == 4001
        assert svc.entity_ownerships == []

    def test_creation_with_all_fields(self):
        svc = FederationService(
            id="svc-2",
            name="order-service",
            url="http://localhost:4002",
            schema_path="schema.graphql",
            health_check="/ready",
            port=8080,
            entity_ownerships=["Order", "OrderItem"],
        )
        assert svc.id == "svc-2"
        assert svc.name == "order-service"
        assert svc.url == "http://localhost:4002"
        assert svc.schema_path == "schema.graphql"
        assert svc.health_check == "/ready"
        assert svc.port == 8080
        assert svc.entity_ownerships == ["Order", "OrderItem"]

    def test_to_dict(self):
        svc = FederationService(
            id="svc-3",
            name="product-service",
            url="http://localhost:4003",
            entity_ownerships=["Product"],
        )
        d = svc.to_dict()
        assert d["id"] == "svc-3"
        assert d["name"] == "product-service"
        assert d["url"] == "http://localhost:4003"
        assert d["schema_path"] == ""
        assert d["health_check"] == "/health"
        assert d["port"] == 4001
        assert d["entity_ownerships"] == ["Product"]

    def test_from_dict_minimal(self):
        svc = FederationService.from_dict({"id": "svc-4", "name": "minimal-svc"})
        assert svc.id == "svc-4"
        assert svc.name == "minimal-svc"
        assert svc.url == ""
        assert svc.schema_path == ""
        assert svc.health_check == "/health"
        assert svc.port == 4001
        assert svc.entity_ownerships == []

    def test_from_dict_full(self):
        data = {
            "id": "svc-5",
            "name": "full-svc",
            "url": "http://example.com",
            "schema_path": "schema.graphql",
            "health_check": "/ping",
            "port": 9090,
            "entity_ownerships": ["A", "B"],
        }
        svc = FederationService.from_dict(data)
        assert svc.id == "svc-5"
        assert svc.name == "full-svc"
        assert svc.url == "http://example.com"
        assert svc.schema_path == "schema.graphql"
        assert svc.health_check == "/ping"
        assert svc.port == 9090
        assert svc.entity_ownerships == ["A", "B"]

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            FederationService(id="", name="svc", url="http://x")

    def test_validation_error_whitespace_id(self):
        with pytest.raises(Exception):
            FederationService(id="   ", name="svc", url="http://x")

    def test_validation_error_empty_name(self):
        with pytest.raises(Exception):
            FederationService(id="svc-6", name="", url="http://x")

    def test_validation_error_port_too_low(self):
        with pytest.raises(Exception):
            FederationService(id="svc-7", name="svc", url="http://x", port=0)

    def test_validation_error_port_too_high(self):
        with pytest.raises(Exception):
            FederationService(id="svc-8", name="svc", url="http://x", port=65536)

    def test_roundtrip(self):
        original = FederationService(
            id="rt-1", name="roundtrip", url="http://rt", port=5000, entity_ownerships=["X"]
        )
        d = original.to_dict()
        restored = FederationService.from_dict(d)
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.url == original.url
        assert restored.port == original.port
        assert restored.entity_ownerships == original.entity_ownerships


# =============================================================================
# FederatedField
# =============================================================================

class TestFederatedField:
    def test_creation_with_defaults(self):
        fld = FederatedField(id="f-1", name="email", type_str="String!")
        assert fld.id == "f-1"
        assert fld.name == "email"
        assert fld.type_str == "String!"
        assert fld.args == []
        assert fld.resolve_reference is False
        assert fld.deprecation_reason is None

    def test_creation_with_all_fields(self):
        fld = FederatedField(
            id="f-2",
            name="users",
            type_str="[User]",
            args=[{"name": "limit", "type": "Int"}],
            resolve_reference=True,
            deprecation_reason="Use getUsers instead",
        )
        assert fld.id == "f-2"
        assert fld.name == "users"
        assert fld.type_str == "[User]"
        assert len(fld.args) == 1
        assert fld.resolve_reference is True
        assert fld.deprecation_reason == "Use getUsers instead"

    def test_to_dict(self):
        fld = FederatedField(id="f-3", name="name", type_str="String", resolve_reference=True)
        d = fld.to_dict()
        assert d["id"] == "f-3"
        assert d["name"] == "name"
        assert d["type_str"] == "String"
        assert d["resolve_reference"] is True
        assert d["deprecation_reason"] is None

    def test_from_dict_minimal(self):
        fld = FederatedField.from_dict({"id": "f-4", "name": "id"})
        assert fld.id == "f-4"
        assert fld.name == "id"
        assert fld.type_str == "String"
        assert fld.args == []

    def test_from_dict_full(self):
        data = {
            "id": "f-5",
            "name": "orders",
            "type_str": "[Order!]",
            "args": [{"name": "page", "type": "Int"}],
            "resolve_reference": True,
            "deprecation_reason": "old",
        }
        fld = FederatedField.from_dict(data)
        assert fld.id == "f-5"
        assert fld.type_str == "[Order!]"
        assert fld.resolve_reference is True
        assert fld.deprecation_reason == "old"

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            FederatedField(id="", name="x", type_str="String")

    def test_validation_error_empty_name(self):
        with pytest.raises(Exception):
            FederatedField(id="f-6", name="", type_str="String")

    def test_roundtrip(self):
        original = FederatedField(
            id="rt-f", name="tags", type_str="[String!]", args=[{"k": "v"}],
            resolve_reference=True, deprecation_reason="test",
        )
        d = original.to_dict()
        restored = FederatedField.from_dict(d)
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.type_str == original.type_str
        assert restored.args == original.args
        assert restored.resolve_reference == original.resolve_reference
        assert restored.deprecation_reason == original.deprecation_reason


# =============================================================================
# FederatedType
# =============================================================================

class TestFederatedType:
    def test_creation_with_defaults(self):
        ft = FederatedType(id="t-1", name="User", key_fields=["id"])
        assert ft.id == "t-1"
        assert ft.name == "User"
        assert ft.fields == []
        assert ft.key_fields == ["id"]
        assert ft.owning_service == ""
        assert ft.extensions == []

    def test_creation_with_all_fields(self):
        field = FederatedField(id="f-1", name="id", type_str="ID!")
        ft = FederatedType(
            id="t-2",
            name="Product",
            fields=[field],
            key_fields=["id", "sku"],
            owning_service="product-service",
            extensions=["order-service"],
        )
        assert len(ft.fields) == 1
        assert ft.key_fields == ["id", "sku"]
        assert ft.owning_service == "product-service"
        assert ft.extensions == ["order-service"]

    def test_to_dict(self):
        field = FederatedField(id="f-1", name="id", type_str="ID!")
        ft = FederatedType(id="t-3", name="Order", fields=[field], key_fields=["id"])
        d = ft.to_dict()
        assert d["id"] == "t-3"
        assert d["name"] == "Order"
        assert len(d["fields"]) == 1
        assert d["fields"][0]["name"] == "id"
        assert d["key_fields"] == ["id"]

    def test_from_dict_with_fields(self):
        data = {
            "id": "t-4",
            "name": "Review",
            "fields": [{"id": "f-1", "name": "score", "type_str": "Int"}],
            "key_fields": ["id"],
            "owning_service": "review-service",
            "extensions": [],
        }
        ft = FederatedType.from_dict(data)
        assert ft.id == "t-4"
        assert ft.name == "Review"
        assert len(ft.fields) == 1
        assert ft.fields[0].name == "score"

    def test_from_dict_empty_fields(self):
        data = {"id": "t-5", "name": "Simple", "key_fields": ["id"]}
        ft = FederatedType.from_dict(data)
        assert ft.id == "t-5"
        assert ft.fields == []

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            FederatedType(id="", name="X", key_fields=["id"])

    def test_validation_error_empty_name(self):
        with pytest.raises(Exception):
            FederatedType(id="t-6", name="", key_fields=["id"])

    def test_validation_error_empty_key_fields(self):
        with pytest.raises(Exception):
            FederatedType(id="t-7", name="NoKey", key_fields=[])

    def test_roundtrip(self):
        field = FederatedField(id="f-1", name="id", type_str="ID!")
        original = FederatedType(
            id="rt-t", name="Customer", fields=[field], key_fields=["id"],
            owning_service="cs", extensions=["ext1"],
        )
        d = original.to_dict()
        restored = FederatedType.from_dict(d)
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.key_fields == original.key_fields
        assert restored.owning_service == original.owning_service
        assert restored.extensions == original.extensions
        assert len(restored.fields) == 1
        assert restored.fields[0].id == "f-1"


# =============================================================================
# FederatedResolver
# =============================================================================

class TestFederatedResolver:
    def test_creation_with_defaults(self):
        res = FederatedResolver(id="r-1", entity_type="User")
        assert res.id == "r-1"
        assert res.entity_type == "User"
        assert res.resolve_reference_query == ""
        assert res.resolve_reference_service == ""

    def test_creation_with_all_fields(self):
        res = FederatedResolver(
            id="r-2",
            entity_type="Product",
            resolve_reference_query="query { _entities(reps: $reps) { ... on Product { id name } } }",
            resolve_reference_service="product-service",
        )
        assert res.entity_type == "Product"
        assert "Product" in res.resolve_reference_query
        assert res.resolve_reference_service == "product-service"

    def test_to_dict(self):
        res = FederatedResolver(
            id="r-3", entity_type="Order", resolve_reference_query="q", resolve_reference_service="s"
        )
        d = res.to_dict()
        assert d["id"] == "r-3"
        assert d["entity_type"] == "Order"
        assert d["resolve_reference_query"] == "q"
        assert d["resolve_reference_service"] == "s"

    def test_from_dict_minimal(self):
        res = FederatedResolver.from_dict({"id": "r-4", "entity_type": "User"})
        assert res.id == "r-4"
        assert res.entity_type == "User"

    def test_from_dict_full(self):
        data = {
            "id": "r-5",
            "entity_type": "Review",
            "resolve_reference_query": "query R",
            "resolve_reference_service": "review-svc",
        }
        res = FederatedResolver.from_dict(data)
        assert res.resolve_reference_service == "review-svc"

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            FederatedResolver(id="", entity_type="X")

    def test_validation_error_empty_entity_type(self):
        with pytest.raises(Exception):
            FederatedResolver(id="r-6", entity_type="")

    def test_roundtrip(self):
        original = FederatedResolver(
            id="rt-r", entity_type="Item",
            resolve_reference_query="q", resolve_reference_service="svc",
        )
        d = original.to_dict()
        restored = FederatedResolver.from_dict(d)
        assert restored.id == original.id
        assert restored.entity_type == original.entity_type
        assert restored.resolve_reference_query == original.resolve_reference_query
        assert restored.resolve_reference_service == original.resolve_reference_service


# =============================================================================
# GatewayConfig
# =============================================================================

class TestGatewayConfig:
    def test_creation_with_defaults(self):
        gw = GatewayConfig(id="gw-1")
        assert gw.id == "gw-1"
        assert gw.services == []
        assert gw.persisted_queries_enabled is False
        assert gw.introspection_enabled is True
        assert gw.cors_origins == []
        assert gw.rate_limit_rps == 100

    def test_creation_with_all_fields(self):
        svc = FederationService(id="svc-1", name="s1", url="http://s1")
        gw = GatewayConfig(
            id="gw-2",
            services=[svc],
            persisted_queries_enabled=True,
            introspection_enabled=False,
            cors_origins=["http://localhost:3000"],
            rate_limit_rps=500,
        )
        assert len(gw.services) == 1
        assert gw.persisted_queries_enabled is True
        assert gw.introspection_enabled is False
        assert gw.cors_origins == ["http://localhost:3000"]
        assert gw.rate_limit_rps == 500

    def test_to_dict(self):
        svc = FederationService(id="svc-1", name="s1", url="http://s1")
        gw = GatewayConfig(id="gw-3", services=[svc], rate_limit_rps=200)
        d = gw.to_dict()
        assert d["id"] == "gw-3"
        assert len(d["services"]) == 1
        assert d["services"][0]["id"] == "svc-1"
        assert d["rate_limit_rps"] == 200

    def test_from_dict_minimal(self):
        gw = GatewayConfig.from_dict({"id": "gw-4"})
        assert gw.id == "gw-4"
        assert gw.services == []
        assert gw.introspection_enabled is True

    def test_from_dict_with_services(self):
        data = {
            "id": "gw-5",
            "services": [{"id": "svc-a", "name": "sa"}],
            "persisted_queries_enabled": True,
            "cors_origins": ["*"],
            "rate_limit_rps": 1000,
        }
        gw = GatewayConfig.from_dict(data)
        assert len(gw.services) == 1
        assert gw.services[0].id == "svc-a"
        assert gw.persisted_queries_enabled is True

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            GatewayConfig(id="")

    def test_validation_error_rate_limit_zero(self):
        with pytest.raises(Exception):
            GatewayConfig(id="gw-6", rate_limit_rps=0)

    def test_validation_error_rate_limit_negative(self):
        with pytest.raises(Exception):
            GatewayConfig(id="gw-7", rate_limit_rps=-1)

    def test_roundtrip(self):
        svc = FederationService(id="s1", name="svc1", url="http://u")
        original = GatewayConfig(
            id="rt-gw", services=[svc], persisted_queries_enabled=True,
            cors_origins=["http://x"], rate_limit_rps=300,
        )
        d = original.to_dict()
        restored = GatewayConfig.from_dict(d)
        assert restored.id == original.id
        assert restored.persisted_queries_enabled == original.persisted_queries_enabled
        assert restored.cors_origins == original.cors_origins
        assert restored.rate_limit_rps == original.rate_limit_rps
        assert len(restored.services) == 1
        assert restored.services[0].id == "s1"
