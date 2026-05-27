# coding: utf-8
"""
Tests cho unified gateway emitters (CP06).

Bao gồm:
- FastAPIGatewayEmitter
- NestJSGatewayEmitter
- AngularGatewayEmitter
- ReactGatewayEmitter
- RouteParser.parse_from_metadata
"""

import pytest
from pathlib import Path

from midicoder.packs.cp06_api_gateway.models import (
    Route,
    RouteCollection,
    RouteAuthConfig,
    HttpMethod,
    AuthMode,
    GraphQLResolver,
    GraphQLOperation,
    GraphQLField,
    WebhookHandler,
    WebhookAuthConfig,
    WebhookAuthType,
)
from midicoder.packs.cp06_api_gateway.fastapi import FastAPIGatewayEmitter
from midicoder.packs.cp06_api_gateway.nestjs import NestJSGatewayEmitter
from midicoder.packs.cp06_api_gateway.angular import AngularGatewayEmitter
from midicoder.packs.cp06_api_gateway.react import ReactGatewayEmitter
from midicoder.packs.cp06_api_gateway.route_parser import RouteParser


# ===========================================================================
# RouteParser.parse_from_metadata Tests
# ===========================================================================


class TestRouteParserFromMetadata:
    """Tests cho RouteParser.parse_from_metadata."""

    def test_parse_routes_only(self):
        """Parse chỉ routes."""
        parser = RouteParser()
        collection = parser.parse_from_metadata(
            routes_data=[
                {
                    "id": "GetUsers",
                    "method": "GET",
                    "path": "/api/users",
                    "handler_type": "query",
                    "handler_id": "list_users",
                    "tags": ["users"],
                },
            ],
        )
        assert isinstance(collection, RouteCollection)
        assert len(collection.routes) == 1
        assert collection.routes[0].method == HttpMethod.GET

    def test_parse_graphql_only(self):
        """Parse chỉ GraphQL resolvers."""
        parser = RouteParser()
        collection = parser.parse_from_metadata(
            graphql_data=[
                {
                    "id": "GetUser",
                    "operation": "query",
                    "field_name": "user",
                    "handler_id": "get_user",
                },
            ],
        )
        assert len(collection.resolvers) == 1
        assert collection.resolvers[0].operation == GraphQLOperation.QUERY

    def test_parse_webhooks_only(self):
        """Parse chỉ webhooks."""
        parser = RouteParser()
        collection = parser.parse_from_metadata(
            webhooks_data=[
                {
                    "id": "stripe",
                    "path": "/webhooks/stripe",
                    "event_type": "payment",
                    "handler_id": "handle_stripe",
                },
            ],
        )
        assert len(collection.webhooks) == 1

    def test_parse_all_three(self):
        """Parse routes, GraphQL, và webhooks cùng lúc."""
        parser = RouteParser()
        collection = parser.parse_from_metadata(
            routes_data=[{"id": "r1", "method": "GET", "path": "/a"}],
            graphql_data=[{"id": "g1", "operation": "query", "field_name": "x"}],
            webhooks_data=[{"id": "w1", "path": "/w", "event_type": "e1"}],
        )
        assert collection.total_count == 3

    def test_parse_empty(self):
        """Parse với dữ liệu rỗng."""
        parser = RouteParser()
        collection = parser.parse_from_metadata()
        assert collection.total_count == 0


# ===========================================================================
# FastAPIGatewayEmitter Tests
# ===========================================================================


class TestFastAPIGatewayEmitter:
    """Tests cho FastAPIGatewayEmitter."""

    def test_init(self):
        """Emitter khởi tạo thành công."""
        emitter = FastAPIGatewayEmitter()
        assert emitter is not None

    def test_generate_empty_collection(self):
        """Generate với collection rỗng."""
        emitter = FastAPIGatewayEmitter()
        result = emitter.generate(RouteCollection())
        assert result == {}

    def test_generate_routes_only(self):
        """Generate chỉ routes."""
        collection = RouteCollection()
        collection.add_route(Route(
            id="GetUsers",
            method=HttpMethod.GET,
            path="/api/users",
            handler_type="query",
            handler_id="list_users",
            tags=["users"],
        ))

        emitter = FastAPIGatewayEmitter()
        result = emitter.generate(collection)

        assert isinstance(result, dict)
        # routes được emit
        assert any("users_routes.py" in k for k in result)

    def test_generate_full_collection(self):
        """Generate routes + resolvers + webhooks."""
        collection = RouteCollection()
        collection.add_route(Route(
            id="GetUsers",
            method=HttpMethod.GET,
            path="/api/users",
            handler_type="query",
            handler_id="list_users",
            tags=["users"],
        ))
        collection.add_resolver(GraphQLResolver(
            id="GetUser",
            operation=GraphQLOperation.QUERY,
            field_name="user",
            handler_id="get_user",
        ))
        collection.add_webhook(WebhookHandler(
            id="stripe",
            path="/webhooks/stripe",
            event_type="payment",
            handler_id="handle_stripe",
        ))

        emitter = FastAPIGatewayEmitter()
        result = emitter.generate(collection)

        assert isinstance(result, dict)
        assert len(result) >= 3  # routes + graphql + webhooks


# ===========================================================================
# NestJSGatewayEmitter Tests
# ===========================================================================


class TestNestJSGatewayEmitter:
    """Tests cho NestJSGatewayEmitter."""

    def test_init(self):
        """Emitter khởi tạo thành công."""
        emitter = NestJSGatewayEmitter()
        assert emitter is not None

    def test_generate_empty_collection(self):
        """Generate với collection rỗng."""
        emitter = NestJSGatewayEmitter()
        result = emitter.generate(RouteCollection())
        assert result == {}

    def test_generate_routes_only(self):
        """Generate chỉ routes."""
        collection = RouteCollection()
        collection.add_route(Route(
            id="GetUsers",
            method=HttpMethod.GET,
            path="/api/users",
            handler_type="query",
            handler_id="listUsers",
            tags=["users"],
        ))

        emitter = NestJSGatewayEmitter()
        result = emitter.generate(collection)

        assert isinstance(result, dict)

    def test_generate_full_collection(self):
        """Generate routes + resolvers + webhooks."""
        collection = RouteCollection()
        collection.add_route(Route(
            id="GetUsers",
            method=HttpMethod.GET,
            path="/api/users",
            handler_type="query",
            handler_id="listUsers",
            tags=["users"],
        ))
        collection.add_resolver(GraphQLResolver(
            id="GetUser",
            operation=GraphQLOperation.QUERY,
            field_name="user",
            handler_id="getUser",
        ))
        collection.add_webhook(WebhookHandler(
            id="stripe",
            path="/webhooks/stripe",
            event_type="payment",
            handler_id="handleStripe",
        ))

        emitter = NestJSGatewayEmitter()
        result = emitter.generate(collection)

        assert isinstance(result, dict)
        assert len(result) >= 3


# ===========================================================================
# AngularGatewayEmitter Tests
# ===========================================================================


class TestAngularGatewayEmitter:
    """Tests cho AngularGatewayEmitter."""

    def test_init(self):
        """Emitter khởi tạo thành công."""
        emitter = AngularGatewayEmitter()
        assert emitter is not None

    def test_generate_empty_collection(self):
        """Generate với collection rỗng."""
        emitter = AngularGatewayEmitter()
        result = emitter.generate(RouteCollection())
        assert result == {}

    def test_generate_with_routes(self, tmp_path):
        """Generate với routes có stack_dir."""
        collection = RouteCollection()
        collection.add_route(Route(
            id="GetUsers",
            method=HttpMethod.GET,
            path="/api/users",
            tags=["users"],
        ))

        # Tạo mock template dir
        template_dir = tmp_path / "core" / "cp06_api_gateway"
        template_dir.mkdir(parents=True)
        (template_dir / "gateway.module.ts.jinja2").write_text("// gateway module")
        (template_dir / "api-client.service.ts.jinja2").write_text("// api client")
        (template_dir / "route-guard.service.ts.jinja2").write_text("// route guard")

        emitter = AngularGatewayEmitter(stack_dir=template_dir.parent)
        result = emitter.generate(collection)

        assert isinstance(result, dict)


# ===========================================================================
# ReactGatewayEmitter Tests
# ===========================================================================


class TestReactGatewayEmitter:
    """Tests cho ReactGatewayEmitter."""

    def test_init(self):
        """Emitter khởi tạo thành công."""
        emitter = ReactGatewayEmitter()
        assert emitter is not None

    def test_generate_empty_collection(self):
        """Generate với collection rỗng."""
        emitter = ReactGatewayEmitter()
        result = emitter.generate(RouteCollection())
        assert result == {}

    def test_generate_with_routes(self, tmp_path):
        """Generate với routes có stack_dir."""
        collection = RouteCollection()
        collection.add_route(Route(
            id="GetUsers",
            method=HttpMethod.GET,
            path="/api/users",
            tags=["users"],
        ))

        # Tạo mock template dir
        template_dir = tmp_path / "core" / "cp06_api_gateway"
        template_dir.mkdir(parents=True)
        (template_dir / "api-client.ts.jinja2").write_text("// api client")
        (template_dir / "route-guard.tsx.jinja2").write_text("// route guard")
        (template_dir / "types.ts.jinja2").write_text("// types")

        emitter = ReactGatewayEmitter(stack_dir=template_dir.parent)
        result = emitter.generate(collection)

        assert isinstance(result, dict)


# ===========================================================================
# Pipeline Integration Tests (pack_emitter_router)
# ===========================================================================


class TestPipelineIntegration:
    """Tests cho integration với pack_emitter_router."""

    def test_parser_registry_has_cp06(self):
        """CP06 parser được registered."""
        from midicoder.pipeline.pack_emitter_router import PARSER_REGISTRY
        assert "cp06_gateway" in PARSER_REGISTRY

    def test_emitter_registry_has_cp06(self):
        """CP06 emitters được registered."""
        from midicoder.pipeline.pack_emitter_router import EMITTER_REGISTRY
        assert "cp06.gateway.fastapi" in EMITTER_REGISTRY
        assert "cp06.gateway.nestjs" in EMITTER_REGISTRY
        assert "cp06.gateway.angular" in EMITTER_REGISTRY
        assert "cp06.gateway.react" in EMITTER_REGISTRY

    def test_parse_gateway_dict(self):
        """Test _parse_gateway_dict."""
        from midicoder.pipeline.pack_emitter_router import _parse_gateway_dict

        raw = {
            "routes": [
                {"id": "r1", "method": "GET", "path": "/test"},
            ],
            "graphql": [
                {"id": "g1", "operation": "query", "field_name": "x"},
            ],
            "webhooks": [
                {"id": "w1", "path": "/w", "event_type": "e1"},
            ],
        }
        collection = _parse_gateway_dict(raw)
        assert isinstance(collection, RouteCollection)
        assert collection.total_count == 3

    def test_dispatch_gateway_fastapi(self):
        """Test dispatch cp06.gateway.fastapi."""
        from midicoder.pipeline.pack_emitter_router import PackEmitterRouter

        file_spec = {
            "path": "app/gateway/",
            "context": {
                "routes": [
                    {"id": "r1", "method": "GET", "path": "/test", "tags": ["test"]},
                ],
                "graphql": [],
                "webhooks": [],
            },
        }
        results = PackEmitterRouter.dispatch("cp06.gateway.fastapi", file_spec, "fastapi")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_dispatch_gateway_nestjs(self):
        """Test dispatch cp06.gateway.nestjs."""
        from midicoder.pipeline.pack_emitter_router import PackEmitterRouter

        file_spec = {
            "path": "src/gateway/",
            "context": {
                "routes": [
                    {"id": "r1", "method": "GET", "path": "/test", "tags": ["test"]},
                ],
            },
        }
        results = PackEmitterRouter.dispatch("cp06.gateway.nestjs", file_spec, "nestjs")
        assert isinstance(results, list)
