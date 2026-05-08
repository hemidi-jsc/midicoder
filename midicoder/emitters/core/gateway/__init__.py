# coding: utf-8
"""
Core Gateway Emitter Package (CP06).

Package này chứa các models và emitter cho API Gateway & Service Mesh:
- Kong Gateway configuration
- Consul Service Mesh integration
- Route management (HTTP, GraphQL, Webhook)

Exports:
    Kong Models: KongGateway, KongService, KongRoute, KongUpstream, KongPlugin, KongTarget, PluginName
    Consul Models: ConsulService, ConsulHealthCheck, ConsulConnect, ConsulUpstream, ConsulServiceMesh, HealthCheckType
    Emitter: KongGatewayEmitter
"""

# Kong Gateway Models
from midicoder.emitters.core.gateway.models import (
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
from midicoder.emitters.core.gateway.kong_gateway import KongGatewayEmitter

__all__ = [
    # Kong Models
    "KongGateway",
    "KongService",
    "KongRoute",
    "KongUpstream",
    "KongTarget",
    "KongPlugin",
    "PluginName",
    # Consul Models
    "ConsulService",
    "ConsulHealthCheck",
    "ConsulConnect",
    "ConsulUpstream",
    "ConsulServiceMesh",
    "HealthCheckType",
    # Emitter
    "KongGatewayEmitter",
]
