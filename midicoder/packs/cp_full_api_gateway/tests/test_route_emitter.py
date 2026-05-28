"""
Tests cho API Routes Emitter (CP06).

Bao gồm:
- Model tests (Route, GraphQLResolver, WebhookHandler)
- Parser tests (RouteParser)
- FastAPI emitter tests
- NestJS emitter tests
- RouteCollection tests
- Tenant isolation tests (KPI-029)
"""

import pytest
from pathlib import Path
from midicoder.packs.cp_full_api_gateway.models import (
    Route,
    RouteCollection,
    RouteAuthConfig,
    RouteParam,
    QueryParam,
    SchemaField,
    HttpMethod,
    AuthMode,
    GraphQLResolver,
    GraphQLArg,
    GraphQLField,
    GraphQLOperation,
    WebhookHandler,
    WebhookAuthConfig,
    WebhookPayloadField,
    WebhookAuthType,
)
from midicoder.packs.cp_full_api_gateway.route_parser import RouteParser
from midicoder.packs.cp_full_api_gateway.route_fastapi import (
    FastAPIRouteEmitter,
    FastAPIGraphQLResolverEmitter,
    FastAPIWebhookEmitter,
)
from midicoder.packs.cp_full_api_gateway.route_nestjs import (
    NestJSRouteEmitter,
    NestJSGraphQLResolverEmitter,
    NestJSWebhookEmitter,
)


# ====================================================================
# Model Tests
# ====================================================================


class TestRouteModel:
    """Tests cho Route model."""

    def test_create_route_default(self):
        """Tạo route với giá trị mặc định."""
        route = Route(id="test_route")
        assert route.id == "test_route"
        assert route.method == HttpMethod.GET
        assert route.path == ""
        assert route.handler_type == "query"

    def test_is_write_operation(self):
        """Kiểm tra write operations."""
        post = Route(id="create", method=HttpMethod.POST)
        put = Route(id="update", method=HttpMethod.PUT)
        patch = Route(id="patch", method=HttpMethod.PATCH)
        delete = Route(id="delete", method=HttpMethod.DELETE)

        assert post.is_write_operation()
        assert put.is_write_operation()
        assert patch.is_write_operation()
        assert delete.is_write_operation()

    def test_is_read_operation(self):
        """Kiểm tra read operations."""
        get = Route(id="list", method=HttpMethod.GET)
        head = Route(id="head", method=HttpMethod.HEAD)
        options = Route(id="options", method=HttpMethod.OPTIONS)

        assert get.is_read_operation()
        assert head.is_read_operation()
        assert options.is_read_operation()

    def test_requires_auth_with_config(self):
        """Kiểm tra auth requirements."""
        route_no_auth = Route(id="public", auth=None)
        route_jwt = Route(
            id="protected",
            auth=RouteAuthConfig(mode=AuthMode.JWT),
        )
        route_none = Route(
            id="explicit_none",
            auth=RouteAuthConfig(mode=AuthMode.NONE),
        )

        assert not route_no_auth.requires_auth()
        assert route_jwt.requires_auth()
        assert not route_none.requires_auth()

    def test_to_dict_and_from_dict(self):
        """Serialization và deserialization."""
        original = Route(
            id="CreateOrder",
            description="Tạo đơn hàng mới",
            method=HttpMethod.POST,
            path="/api/v1/orders",
            handler_type="command",
            handler_id="create_order",
            tags=["orders"],
            auth=RouteAuthConfig(
                mode=AuthMode.JWT,
                required_roles=["admin"],
                required_permissions=["order:create"],
                tenant_scoped=True,
            ),
            path_params=[],
            query_params=[],
            request_schema=[
                SchemaField(name="items", field_type="list", required=True),
            ],
            response_schema=[
                SchemaField(name="order_id", field_type="str"),
            ],
            response_status=201,
        )

        d = original.to_dict()
        restored = Route.from_dict(d)

        assert restored.id == original.id
        assert restored.method == original.method
        assert restored.path == original.path
        assert restored.auth is not None
        assert restored.auth.tenant_scoped is True
        assert len(restored.request_schema) == 1
        assert restored.response_status == 201


class TestGraphQLResolverModel:
    """Tests cho GraphQLResolver model."""

    def test_is_mutation(self):
        """Kiểm tra mutation type."""
        query = GraphQLResolver(id="GetOrders", operation=GraphQLOperation.QUERY)
        mutation = GraphQLResolver(id="CreateOrder", operation=GraphQLOperation.MUTATION)

        assert not query.is_mutation()
        assert mutation.is_mutation()

    def test_is_subscription(self):
        """Kiểm tra subscription type."""
        sub = GraphQLResolver(
            id="OrderUpdates",
            operation=GraphQLOperation.SUBSCRIPTION,
        )
        assert sub.is_subscription()

    def test_to_dict_and_from_dict(self):
        """Serialization và deserialization."""
        original = GraphQLResolver(
            id="GetOrders",
            description="Lấy danh sách đơn hàng",
            operation=GraphQLOperation.QUERY,
            type_name="Query",
            field_name="orders",
            handler_id="list_orders",
            args=[
                GraphQLArg(name="limit", arg_type="Int", required=False),
            ],
            returns=[
                GraphQLField(name="orders", field_type="[Order]"),
            ],
            auth_required=True,
            tenant_scoped=True,
        )

        d = original.to_dict()
        restored = GraphQLResolver.from_dict(d)

        assert restored.id == original.id
        assert restored.operation == original.operation
        assert restored.tenant_scoped is True


class TestWebhookHandlerModel:
    """Tests cho WebhookHandler model."""

    def test_to_dict_and_from_dict(self):
        """Serialization và deserialization."""
        original = WebhookHandler(
            id="stripe_payment",
            path="/webhooks/stripe",
            event_type="payment.completed",
            handler_id="handle_stripe_payment",
            auth_config=WebhookAuthConfig(
                auth_type=WebhookAuthType.HMAC_SIGNATURE,
                header_name="X-Stripe-Signature",
                secret_env="STRIPE_WEBHOOK_SECRET",
                algorithm="sha256",
            ),
            verify_signature=True,
            payload_schema=[
                WebhookPayloadField(name="amount", field_type="int", required=True),
            ],
        )

        d = original.to_dict()
        restored = WebhookHandler.from_dict(d)

        assert restored.id == original.id
        assert restored.auth_config is not None
        assert restored.auth_config.auth_type == WebhookAuthType.HMAC_SIGNATURE


class TestRouteCollection:
    """Tests cho RouteCollection."""

    def test_add_and_count(self):
        """Thêm items và đếm."""
        collection = RouteCollection()
        assert collection.total_count == 0

        collection.add_route(Route(id="r1", method=HttpMethod.GET))
        collection.add_route(Route(id="r2", method=HttpMethod.POST))
        collection.add_resolver(GraphQLResolver(id="g1"))
        collection.add_webhook(WebhookHandler(id="w1"))

        assert collection.total_count == 4
        assert len(collection.routes) == 2
        assert len(collection.resolvers) == 1
        assert len(collection.webhooks) == 1

    def test_group_routes_by_tag(self):
        """Nhóm routes theo tag."""
        collection = RouteCollection()
        collection.add_route(Route(id="r1", tags=["orders"]))
        collection.add_route(Route(id="r2", tags=["orders"]))
        collection.add_route(Route(id="r3", tags=["users"]))

        groups = collection.group_routes_by_tag()
        assert "orders" in groups
        assert "users" in groups
        assert len(groups["orders"]) == 2
        assert len(groups["users"]) == 1

    def test_get_by_tag(self):
        """Lọc collection theo tag."""
        collection = RouteCollection()
        collection.add_route(Route(id="r1", tags=["orders"]))
        collection.add_route(Route(id="r2", tags=["users"]))

        filtered = collection.get_by_tag("orders")
        assert len(filtered.routes) == 1
        assert filtered.routes[0].id == "r1"


# ====================================================================
# Parser Tests
# ====================================================================


class TestRouteParser:
    """Tests cho RouteParser."""

    def test_parse_from_metadata_routes(self):
        """Parse HTTP routes từ metadata."""
        parser = RouteParser()
        collection = parser.parse_from_metadata(
            routes_data=[
                {
                    "id": "GetOrders",
                    "method": "GET",
                    "path": "/api/v1/orders",
                    "handler_type": "query",
                    "handler_id": "list_orders",
                    "tags": ["orders"],
                    "auth": {"mode": "jwt", "tenant_scoped": True},
                    "path_params": [],
                    "query_params": [],
                    "request_schema": [],
                    "response_schema": [],
                },
            ],
        )

        assert len(collection.routes) == 1
        route = collection.routes[0]
        assert route.id == "GetOrders"
        assert route.method == HttpMethod.GET
        assert route.auth is not None

    def test_parse_from_metadata_graphql(self):
        """Parse GraphQL resolvers từ metadata."""
        parser = RouteParser()
        collection = parser.parse_from_metadata(
            graphql_data=[
                {
                    "id": "GetOrders",
                    "operation": "query",
                    "type_name": "Query",
                    "field_name": "orders",
                    "handler_id": "list_orders",
                    "args": [],
                    "returns": [{"name": "orders", "type": "[Order]"}],
                    "tenant_scoped": True,
                },
            ],
        )

        assert len(collection.resolvers) == 1
        resolver = collection.resolvers[0]
        assert resolver.operation == GraphQLOperation.QUERY

    def test_parse_from_metadata_webhooks(self):
        """Parse webhooks từ metadata."""
        parser = RouteParser()
        collection = parser.parse_from_metadata(
            webhooks_data=[
                {
                    "id": "stripe_payment",
                    "path": "/webhooks/stripe",
                    "event_type": "payment.completed",
                    "handler_id": "handle_stripe_payment",
                    "verify_signature": True,
                    "auth_config": {
                        "auth_type": "hmac_signature",
                        "header_name": "X-Stripe-Signature",
                    },
                    "payload_schema": [],
                },
            ],
        )

        assert len(collection.webhooks) == 1
        webhook = collection.webhooks[0]
        assert webhook.event_type == "payment.completed"


# ====================================================================
# FastAPI Emitter Tests
# ====================================================================


class TestFastAPIRouteEmitter:
    """Tests cho FastAPIRouteEmitter."""

    def test_emit_routes_creates_files(self, tmp_path):
        """Emit routes tạo đúng files."""
        collection = RouteCollection()
        collection.add_route(
            Route(
                id="GetOrders",
                method=HttpMethod.GET,
                path="/api/v1/orders",
                handler_type="query",
                handler_id="list_orders",
                tags=["orders"],
                auth=RouteAuthConfig(mode=AuthMode.JWT, tenant_scoped=True),
            )
        )

        emitter = FastAPIRouteEmitter()
        files = emitter.emit(collection, tmp_path)

        assert len(files) >= 2  # router file + __init__.py
        # Kiểm tra router file tồn tại
        assert any("orders_routes.py" in k for k in files)

    def test_emit_routes_includes_auth(self, tmp_path):
        """Routes với auth có auth imports."""
        collection = RouteCollection()
        collection.add_route(
            Route(
                id="CreateOrder",
                method=HttpMethod.POST,
                path="/api/v1/orders",
                handler_type="command",
                handler_id="create_order",
                tags=["orders"],
                auth=RouteAuthConfig(mode=AuthMode.JWT),
            )
        )

        emitter = FastAPIRouteEmitter()
        files = emitter.emit(collection, tmp_path)

        # Kiểm tra file có auth imports
        router_content = files.get("routes/orders_routes.py", "")
        assert "get_current_user" in router_content or "Depends" in router_content


class TestFastAPIGraphQLResolverEmitter:
    """Tests cho FastAPIGraphQLResolverEmitter."""

    def test_emit_creates_resolver_files(self, tmp_path):
        """Emit tạo resolver files."""
        collection = RouteCollection()
        collection.add_resolver(
            GraphQLResolver(
                id="GetOrders",
                operation=GraphQLOperation.QUERY,
                type_name="Query",
                field_name="orders",
                handler_id="list_orders",
                returns=[GraphQLField(name="orders", field_type="[Order]")],
            )
        )

        emitter = FastAPIGraphQLResolverEmitter()
        files = emitter.emit(collection, tmp_path)

        assert len(files) >= 2  # resolver + schema
        assert any("resolver.py" in k for k in files)


class TestFastAPIWebhookEmitter:
    """Tests cho FastAPIWebhookEmitter."""

    def test_emit_creates_webhook_files(self, tmp_path):
        """Emit tạo webhook files."""
        collection = RouteCollection()
        collection.add_webhook(
            WebhookHandler(
                id="stripe_payment",
                path="/webhooks/stripe",
                event_type="payment.completed",
                handler_id="handle_stripe_payment",
                verify_signature=True,
                auth_config=WebhookAuthConfig(
                    auth_type=WebhookAuthType.HMAC_SIGNATURE,
                    header_name="X-Stripe-Signature",
                ),
            )
        )

        emitter = FastAPIWebhookEmitter()
        files = emitter.emit(collection, tmp_path)

        assert len(files) >= 2  # handler + __init__.py
        assert any("handler.py" in k for k in files)


# ====================================================================
# NestJS Emitter Tests
# ====================================================================


class TestNestJSRouteEmitter:
    """Tests cho NestJSRouteEmitter."""

    def test_emit_creates_controller_files(self, tmp_path):
        """Emit tạo controller files."""
        collection = RouteCollection()
        collection.add_route(
            Route(
                id="GetOrders",
                method=HttpMethod.GET,
                path="/api/orders",
                handler_type="query",
                handler_id="listOrders",
                tags=["orders"],
            )
        )

        emitter = NestJSRouteEmitter()
        files = emitter.emit(collection, tmp_path)

        assert len(files) >= 1
        assert any("controller.ts" in k for k in files)


class TestNestJSGraphQLResolverEmitter:
    """Tests cho NestJSGraphQLResolverEmitter."""

    def test_emit_creates_resolver_files(self, tmp_path):
        """Emit tạo resolver files."""
        collection = RouteCollection()
        collection.add_resolver(
            GraphQLResolver(
                id="GetOrders",
                operation=GraphQLOperation.QUERY,
                handler_id="listOrders",
            )
        )

        emitter = NestJSGraphQLResolverEmitter()
        files = emitter.emit(collection, tmp_path)

        assert len(files) >= 1
        assert any("resolver.ts" in k for k in files)


class TestNestJSWebhookEmitter:
    """Tests cho NestJSWebhookEmitter."""

    def test_emit_creates_webhook_files(self, tmp_path):
        """Emit tạo webhook files."""
        collection = RouteCollection()
        collection.add_webhook(
            WebhookHandler(
                id="stripe",
                path="/api/webhooks/stripe",
                event_type="payment.completed",
                handler_id="handleStripePayment",
            )
        )

        emitter = NestJSWebhookEmitter()
        files = emitter.emit(collection, tmp_path)

        assert len(files) >= 1
        assert any("handler.ts" in k for k in files)


# ====================================================================
# KPI-029 Tenant Isolation Tests
# ====================================================================


class TestTenantIsolation:
    """Tests cho KPI-029: Tenant isolation."""

    def test_route_default_tenant_scoped(self):
        """Route auth mặc định tenant_scoped=True."""
        auth = RouteAuthConfig()
        assert auth.tenant_scoped is True

    def test_graphql_default_tenant_scoped(self):
        """GraphQL resolver mặc định tenant_scoped=True."""
        resolver = GraphQLResolver(id="test")
        assert resolver.tenant_scoped is True

    def test_route_from_dict_preserves_tenant_scoped(self):
        """from_dict bảo tồn tenant_scoped."""
        d = {
            "id": "test",
            "auth": {"mode": "jwt", "tenant_scoped": True},
        }
        route = Route.from_dict(d)
        assert route.auth.tenant_scoped is True