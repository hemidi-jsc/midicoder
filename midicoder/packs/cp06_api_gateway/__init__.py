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
    Circuit Breaker Models: CircuitState, CircuitBreakerPolicy, CircuitBreakerConfig
    Emitter: KongGatewayEmitter, FastAPIGatewayEmitter, NestJSGatewayEmitter, AngularGatewayEmitter, ReactGatewayEmitter
    Parser: RouteParser, GatewayIR, parse_circuit_breakers
    Recipe: RecipeOutput, circuit_breaker_recipe
"""

# ===========================================================================
# Kong Gateway Models
# ===========================================================================
from midicoder.packs.cp06_api_gateway.models import (
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
from midicoder.packs.cp06_api_gateway.kong_gateway import KongGatewayEmitter

# ===========================================================================
# Route Models (merged from route/)
# ===========================================================================
from midicoder.packs.cp06_api_gateway.models import (
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
    # Circuit Breaker
    CircuitState,
    CircuitBreakerPolicy,
    CircuitBreakerConfig,
)

# Route Parser
from midicoder.packs.cp06_api_gateway.route_parser import RouteParser

# Gateway Parser (IR)
from midicoder.packs.cp06_api_gateway.parser import GatewayIR, parse_circuit_breakers

# Recipes
from midicoder.packs.cp06_api_gateway.recipes import (
    RecipeOutput,
    circuit_breaker_recipe,
)

# Unified Gateway Emitters (all stacks)
from midicoder.packs.cp06_api_gateway.fastapi import FastAPIGatewayEmitter
from midicoder.packs.cp06_api_gateway.nestjs import NestJSGatewayEmitter
from midicoder.packs.cp06_api_gateway.angular import AngularGatewayEmitter
from midicoder.packs.cp06_api_gateway.react import ReactGatewayEmitter

# Legacy sub-emitters (kept for backward compatibility)
from midicoder.packs.cp06_api_gateway.route_fastapi import (
    FastAPIRouteEmitter,
    FastAPIGraphQLResolverEmitter,
    FastAPIWebhookEmitter,
)
from midicoder.packs.cp06_api_gateway.route_nestjs import (
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
    # -- Kong Emitter --
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
    # -- Circuit Breaker --
    "CircuitState",
    "CircuitBreakerPolicy",
    "CircuitBreakerConfig",
    # -- Parser --
    "RouteParser",
    "GatewayIR",
    "parse_circuit_breakers",
    # -- Recipes --
    "RecipeOutput",
    "circuit_breaker_recipe",
    # -- Unified Gateway Emitters --
    "FastAPIGatewayEmitter",
    "NestJSGatewayEmitter",
    "AngularGatewayEmitter",
    "ReactGatewayEmitter",
    # -- Legacy Sub-emitters --
    "FastAPIRouteEmitter",
    "FastAPIGraphQLResolverEmitter",
    "FastAPIWebhookEmitter",
    "NestJSRouteEmitter",
    "NestJSGraphQLResolverEmitter",
    "NestJSWebhookEmitter",
]
