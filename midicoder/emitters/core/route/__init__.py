# coding: utf-8
"""
Compat re-export for route/ — now part of CP06 gateway/.

All imports from midicoder.emitters.core.route now resolve via gateway.
This module exists solely as a migration bridge.
"""

from midicoder.emitters.core.gateway.route_models import (
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
from midicoder.emitters.core.gateway.route_parser import RouteParser
from midicoder.emitters.core.gateway.route_fastapi import (
    FastAPIRouteEmitter,
    FastAPIGraphQLResolverEmitter,
    FastAPIWebhookEmitter,
)
from midicoder.emitters.core.gateway.route_nestjs import (
    NestJSRouteEmitter,
    NestJSGraphQLResolverEmitter,
    NestJSWebhookEmitter,
)

__all__ = [
    "Route", "RouteCollection", "RouteAuthConfig", "RouteParam", "QueryParam",
    "SchemaField", "HttpMethod", "AuthMode",
    "GraphQLResolver", "GraphQLArg", "GraphQLField", "GraphQLOperation",
    "WebhookHandler", "WebhookAuthConfig", "WebhookPayloadField", "WebhookAuthType",
    "RouteParser",
    "FastAPIRouteEmitter", "FastAPIGraphQLResolverEmitter", "FastAPIWebhookEmitter",
    "NestJSRouteEmitter", "NestJSGraphQLResolverEmitter", "NestJSWebhookEmitter",
]
