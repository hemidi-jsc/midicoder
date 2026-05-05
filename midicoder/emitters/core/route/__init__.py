# coding: utf-8
"""
Core Route Emitter Package (CP06).

Package này chứa các models, parser và emitter cho API routes:
- HTTP REST routes
- GraphQL resolvers
- Webhook handlers

Exports:
    Models: Route, GraphQLResolver, WebhookHandler, RouteCollection
    Parser: RouteParser
    FastAPI: FastAPIRouteEmitter, FastAPIGraphQLResolverEmitter, FastAPIWebhookEmitter
    NestJS: NestJSRouteEmitter, NestJSGraphQLResolverEmitter, NestJSWebhookEmitter
"""

# Models
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

# Parser
from midicoder.emitters.core.route.parser import RouteParser

# FastAPI Emitters
from midicoder.emitters.core.route.fastapi import (
    FastAPIRouteEmitter,
    FastAPIGraphQLResolverEmitter,
    FastAPIWebhookEmitter,
)

# NestJS Emitters
from midicoder.emitters.core.route.nestjs import (
    NestJSRouteEmitter,
    NestJSGraphQLResolverEmitter,
    NestJSWebhookEmitter,
)

__all__ = [
    # Models
    "Route",
    "RouteCollection",
    "RouteAuthConfig",
    "RouteParam",
    "QueryParam",
    "SchemaField",
    "HttpMethod",
    "AuthMode",
    "GraphQLResolver",
    "GraphQLArg",
    "GraphQLField",
    "GraphQLOperation",
    "WebhookHandler",
    "WebhookAuthConfig",
    "WebhookPayloadField",
    "WebhookAuthType",
    # Parser
    "RouteParser",
    # FastAPI Emitters
    "FastAPIRouteEmitter",
    "FastAPIGraphQLResolverEmitter",
    "FastAPIWebhookEmitter",
    # NestJS Emitters
    "NestJSRouteEmitter",
    "NestJSGraphQLResolverEmitter",
    "NestJSWebhookEmitter",
]