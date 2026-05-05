# coding: utf-8
"""
Route Parser - Parse ProjectionTree nodes thành RouteCollection.

Module này chứa RouteParser class để parse các nodes:
- HTTP_ROUTE → Route
- GRAPHQL_RESOLVER → GraphQLResolver  
- WEBHOOK → WebhookHandler

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.dsl.projection import ProjectionTree, NodeKind, ProjectionNode
from midicoder.emitters.core.route.models import (
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


class RouteParser:
    """
    Parser để convert ProjectionTree nodes thành RouteCollection.

    Traversal ProjectionTree, tìm các nodes với kind:
    - HTTP_ROUTE → Route
    - GRAPHQL_RESOLVER → GraphQLResolver
    - WEBHOOK → WebhookHandler

    Ví dụ:
        parser = RouteParser()
        collection = parser.parse(tree)
        # collection.routes: [Route, Route, ...]
        # collection.resolvers: [GraphQLResolver, ...]
        # collection.webhooks: [WebhookHandler, ...]
    """

    def parse(self, tree: ProjectionTree) -> RouteCollection:
        """
        Parse ProjectionTree thành RouteCollection.

        Traversal toàn bộ tree, tìm các API nodes và convert
        thành typed models.

        Args:
            tree: ProjectionTree chứa API nodes

        Returns:
            RouteCollection với routes, resolvers, webhooks
        """
        collection = RouteCollection()

        # Duyệt tất cả nodes trong tree
        for node_id, node in tree.nodes.items():
            kind = node.kind

            if kind == NodeKind.HTTP_ROUTE:
                route = self._parse_route_node(node)
                collection.add_route(route)

            elif kind == NodeKind.GRAPHQL_RESOLVER:
                resolver = self._parse_graphql_node(node)
                collection.add_resolver(resolver)

            elif kind == NodeKind.WEBHOOK:
                webhook = self._parse_webhook_node(node)
                collection.add_webhook(webhook)

        return collection

    def _parse_route_node(self, node: ProjectionNode) -> Route:
        """
        Parse HTTP_ROUTE node thành Route model.

        Args:
            node: HTTP_ROUTE ProjectionNode

        Returns:
            Route instance
        """
        params = node.params or {}

        # Parse auth config
        auth_data = params.get("auth")
        auth = None
        if auth_data:
            auth = RouteAuthConfig(
                mode=AuthMode(auth_data.get("mode", "jwt")),
                required_roles=auth_data.get("required_roles", []),
                required_permissions=auth_data.get("required_permissions", []),
                tenant_scoped=auth_data.get("tenant_scoped", True),
            )

        return Route(
            id=node.id,
            description=params.get("description", ""),
            method=HttpMethod(params.get("method", "GET")),
            path=params.get("path", "/"),
            handler_type="command" if params.get("command_id") else "query",
            handler_id=params.get("command_id") or params.get("query_id", ""),
            tags=params.get("tags", []),
            auth=auth,
            path_params=[
                RouteParam(**p) for p in params.get("path_params", [])
            ],
            query_params=[
                QueryParam(**p) for p in params.get("query_params", [])
            ],
            request_schema=[
                SchemaField(**f) for f in params.get("request_schema", [])
            ],
            response_schema=[
                SchemaField(**f) for f in params.get("response_schema", [])
            ],
            response_status=params.get("response_status", 200),
            deprecated=params.get("deprecated", False),
        )

    def _parse_graphql_node(self, node: ProjectionNode) -> GraphQLResolver:
        """
        Parse GRAPHQL_RESOLVER node thành GraphQLResolver model.

        Args:
            node: GRAPHQL_RESOLVER ProjectionNode

        Returns:
            GraphQLResolver instance
        """
        params = node.params or {}

        return GraphQLResolver(
            id=node.id,
            description=params.get("description", ""),
            operation=GraphQLOperation(params.get("operation", "query")),
            type_name=params.get("type_name", "Query"),
            field_name=params.get("field_name", node.id),
            handler_id=params.get("handler_id") or params.get("command_id") or params.get("query_id", ""),
            args=[
                GraphQLArg(**a) for a in params.get("args", [])
            ],
            returns=[
                GraphQLField(**f) for f in params.get("returns", [])
            ],
            auth_required=params.get("auth_required", True),
            tenant_scoped=params.get("tenant_scoped", True),
            tags=params.get("tags", []),
        )

    def _parse_webhook_node(self, node: ProjectionNode) -> WebhookHandler:
        """
        Parse WEBHOOK node thành WebhookHandler model.

        Args:
            node: WEBHOOK ProjectionNode

        Returns:
            WebhookHandler instance
        """
        params = node.params or {}

        # Parse auth config
        auth_data = params.get("auth_config")
        auth_config = None
        if auth_data:
            auth_config = WebhookAuthConfig(
                auth_type=WebhookAuthType(auth_data.get("auth_type", "hmac_signature")),
                header_name=auth_data.get("header_name", "X-Signature"),
                secret_env=auth_data.get("secret_env", "WEBHOOK_SECRET"),
                algorithm=auth_data.get("algorithm", "sha256"),
            )

        return WebhookHandler(
            id=node.id,
            description=params.get("description", ""),
            path=params.get("path", "/webhook"),
            event_type=params.get("event_type", "generic"),
            handler_id=params.get("handler_id", ""),
            auth_config=auth_config,
            verify_signature=params.get("verify_signature", True),
            payload_schema=[
                WebhookPayloadField(**f) for f in params.get("payload_schema", [])
            ],
            tags=params.get("tags", []),
        )

    def parse_from_metadata(
        self,
        routes_data: list[dict[str, Any]] | None = None,
        graphql_data: list[dict[str, Any]] | None = None,
        webhooks_data: list[dict[str, Any]] | None = None,
    ) -> RouteCollection:
        """
        Parse route data từ MIR metadata (dict format).

        Dùng khi data được lưu trong MIR metadata thay vì ProjectionTree.

        Args:
            routes_data: List route dicts từ MIR metadata
            graphql_data: List graphql dicts từ MIR metadata
            webhooks_data: List webhook dicts từ MIR metadata

        Returns:
            RouteCollection instance
        """
        collection = RouteCollection()

        # Parse routes
        if routes_data:
            for route_dict in routes_data:
                collection.add_route(Route.from_dict(route_dict))

        # Parse graphql resolvers
        if graphql_data:
            for resolver_dict in graphql_data:
                collection.add_resolver(GraphQLResolver.from_dict(resolver_dict))

        # Parse webhooks
        if webhooks_data:
            for webhook_dict in webhooks_data:
                collection.add_webhook(WebhookHandler.from_dict(webhook_dict))

        return collection