# coding: utf-8
"""
Core Gateway Emitter Package (CP06) — Unified.

Merged gateway/ (Kong + Consul) + route/ (HTTP/GraphQL/Webhook) into a single pack.

Package này chứa các models và emitter cho API Gateway & Service Mesh:
- Kong Gateway configuration
- Consul Service Mesh integration
- Route management (HTTP REST, GraphQL, Webhook)

Exports:
    Kong Models: KongGateway, KongService, KongRoute, KongUpstream, KongPlugin, KongTarget, PluginName
    Consul Models: ConsulService, ConsulHealthCheck, ConsulConnect, ConsulUpstream, ConsulServiceMesh, HealthCheckType
    Route Models: Route, RouteCollection, RouteAuthConfig, RouteParam, QueryParam, SchemaField, HttpMethod, AuthMode
    GraphQL Models: GraphQLResolver, GraphQLArg, GraphQLField, GraphQLOperation
    Webhook Models: WebhookHandler, WebhookAuthConfig, WebhookPayloadField, WebhookAuthType
    Emitter: KongGatewayEmitter, FastAPIRouteEmitter, NestJSRouteEmitter, RouteParser
"""

# ===========================================================================
# Kong Gateway Models
# ===========================================================================
from midicoder.emitters.core.cp06_api_gateway.models import (
    KongGateway,
    KongService,
    KongRoute,
    KongUpstream,
    KongTarget,
    KongPlugin,
    PluginName,
    # Consul Service Mesh Models
    ConsulService,
    ConsulHealthCheck,
    ConsulConnect,
    ConsulUpstream,
    ConsulServiceMesh,
    HealthCheckType,
)

# Kong Gateway Emitter
from midicoder.emitters.core.cp06_api_gateway.kong_gateway import KongGatewayEmitter

# ===========================================================================
# Route Models (merged from route/)
# ===========================================================================
from midicoder.emitters.core.cp06_api_gateway.route_models import (
    Route,
    RouteCollection,
    RouteAuthConfig,
    RouteParam,
    QueryParam,
    SchemaField,
    HttpMethod,
    AuthMode,
    # GraphQL
    GraphQLResolver,
    GraphQLArg,
    GraphQLField,
    GraphQLOperation,
    # Webhook
    WebhookHandler,
    WebhookAuthConfig,
    WebhookPayloadField,
    WebhookAuthType,
)

# Route Parser
from midicoder.emitters.core.cp06_api_gateway.route_parser import RouteParser

# Route Emitters
from midicoder.emitters.core.cp06_api_gateway.route_fastapi import (
    FastAPIRouteEmitter,
    FastAPIGraphQLResolverEmitter,
    FastAPIWebhookEmitter,
)
from midicoder.emitters.core.cp06_api_gateway.route_nestjs import (
    NestJSRouteEmitter,
    NestJSGraphQLResolverEmitter,
    NestJSWebhookEmitter,
)

# ===========================================================================
# Public API
# ===========================================================================
__all__ = [
    # -- Kong Models --
    "KongGateway",
    "KongService",
    "KongRoute",
    "KongUpstream",
    "KongTarget",
    "KongPlugin",
    "PluginName",
    # -- Consul Models --
    "ConsulService",
    "ConsulHealthCheck",
    "ConsulConnect",
    "ConsulUpstream",
    "ConsulServiceMesh",
    "HealthCheckType",
    # -- Emitter --
    "KongGatewayEmitter",
    # -- Route Models --
    "Route",
    "RouteCollection",
    "RouteAuthConfig",
    "RouteParam",
    "QueryParam",
    "SchemaField",
    "HttpMethod",
    "AuthMode",
    # -- GraphQL --
    "GraphQLResolver",
    "GraphQLArg",
    "GraphQLField",
    "GraphQLOperation",
    # -- Webhook --
    "WebhookHandler",
    "WebhookAuthConfig",
    "WebhookPayloadField",
    "WebhookAuthType",
    # -- Parser --
    "RouteParser",
    # -- FastAPI Emitters --
    "FastAPIRouteEmitter",
    "FastAPIGraphQLResolverEmitter",
    "FastAPIWebhookEmitter",
    # -- NestJS Emitters --
    "NestJSRouteEmitter",
    "NestJSGraphQLResolverEmitter",
    "NestJSWebhookEmitter",
]
