# coding: utf-8
"""
Mô-đun parser cho CP57 — GraphQL Schema Federation.

Parse DSL dict (từ contract YAML) sang GraphQLIR — Intermediate Representation
cho GraphQL Federation configurations, federated types, resolvers,
và gateway aggregation settings.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp57_graphql_federation.models import (
    FederationService,
    FederatedField,
    FederatedResolver,
    FederatedType,
    GatewayConfig,
)


@dataclass
class GraphQLIR:
    """Intermediate Representation cho CP57 — GraphQL Schema Federation.

    Gom tập tất cả cấu hình GraphQL Federation từ DSL, bao gồm
    services, federated types, fields, resolvers, và gateway config.

    Attributes:
        services: Danh sách federation services
        types: Danh sách federated types
        fields: Danh sách federated fields
        resolvers: Danh sách federated resolvers
        gateway_config: Cấu hình gateway aggregation
    """
    services: list[FederationService] = field(default_factory=list)
    types: list[FederatedType] = field(default_factory=list)
    fields: list[FederatedField] = field(default_factory=list)
    resolvers: list[FederatedResolver] = field(default_factory=list)
    gateway_config: GatewayConfig | None = None

    def to_dict(self) -> dict[str, Any]:
        """Chuyển GraphQLIR sang dict."""
        return {
            "services": [s.to_dict() for s in self.services],
            "types": [t.to_dict() for t in self.types],
            "fields": [f.to_dict() for f in self.fields],
            "resolvers": [r.to_dict() for r in self.resolvers],
            "gateway_config": self.gateway_config.to_dict() if self.gateway_config else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphQLIR":
        """Tạo GraphQLIR từ dict."""
        services = [FederationService.from_dict(s) for s in data.get("services", [])]
        types = [FederatedType.from_dict(t) for t in data.get("types", [])]
        fields = [FederatedField.from_dict(f) for f in data.get("fields", [])]
        resolvers = [FederatedResolver.from_dict(r) for r in data.get("resolvers", [])]
        gw_raw = data.get("gateway_config")
        gateway_config = GatewayConfig.from_dict(gw_raw) if gw_raw else None
        return cls(
            services=services,
            types=types,
            fields=fields,
            resolvers=resolvers,
            gateway_config=gateway_config,
        )


def parse_services(data: dict[str, Any]) -> list[FederationService]:
    """Parse danh sách federation services từ DSL dict.

    Args:
        data: DSL dict với key 'services' hoặc 'federation_services'

    Returns:
        Danh sách FederationService
    """
    raw = data.get("services", data.get("federation_services", []))
    services = []
    for s_data in raw:
        services.append(FederationService(
            id=s_data.get("id", ""),
            name=s_data.get("name", s_data.get("id", "")),
            url=s_data.get("url", ""),
            schema_path=s_data.get("schema_path", ""),
            health_check=s_data.get("health_check", "/health"),
            port=s_data.get("port", 4001),
            entity_ownerships=s_data.get("entity_ownerships", []),
        ))
    return services


def parse_types(data: dict[str, Any]) -> list[FederatedType]:
    """Parse danh sách federated types từ DSL dict.

    Args:
        data: DSL dict với key 'types' hoặc 'federated_types'

    Returns:
        Danh sách FederatedType
    """
    raw = data.get("types", data.get("federated_types", []))
    types = []
    for t_data in raw:
        raw_fields = t_data.get("fields", [])
        fields = [FederatedField.from_dict(f) for f in raw_fields if isinstance(f, dict)]
        types.append(FederatedType(
            id=t_data.get("id", ""),
            name=t_data.get("name", t_data.get("id", "")),
            fields=fields,
            key_fields=t_data.get("key_fields", []),
            owning_service=t_data.get("owning_service", ""),
            extensions=t_data.get("extensions", []),
        ))
    return types


def parse_resolvers(data: dict[str, Any]) -> list[FederatedResolver]:
    """Parse danh sách federated resolvers từ DSL dict.

    Args:
        data: DSL dict với key 'resolvers' hoặc 'federated_resolvers'

    Returns:
        Danh sách FederatedResolver
    """
    raw = data.get("resolvers", data.get("federated_resolvers", []))
    resolvers = []
    for r_data in raw:
        resolvers.append(FederatedResolver(
            id=r_data.get("id", ""),
            entity_type=r_data.get("entity_type", ""),
            resolve_reference_query=r_data.get("resolve_reference_query", ""),
            resolve_reference_service=r_data.get("resolve_reference_service", ""),
        ))
    return resolvers


def parse_gateway_config(data: dict[str, Any]) -> GatewayConfig | None:
    """Parse gateway config từ DSL dict.

    Args:
        data: DSL dict với key 'gateway_config' hoặc 'gateway'

    Returns:
        GatewayConfig hoặc None
    """
    raw = data.get("gateway_config", data.get("gateway"))
    if not raw:
        return None
    return GatewayConfig(
        id=raw.get("id", "default_gateway"),
        services=parse_services(raw) if "services" in raw else [],
        persisted_queries_enabled=raw.get("persisted_queries_enabled", False),
        introspection_enabled=raw.get("introspection_enabled", True),
        cors_origins=raw.get("cors_origins", []),
        rate_limit_rps=raw.get("rate_limit_rps", 100),
    )


def parse_to_ir(data: dict[str, Any]) -> GraphQLIR:
    """Parse DSL dict thành GraphQLIR.

    Args:
        data: DSL dict với services, types, resolvers, gateway_config

    Returns:
        GraphQLIR gom tập tất cả parsed data
    """
    services = parse_services(data)
    types = parse_types(data)
    resolvers = parse_resolvers(data)
    gateway = parse_gateway_config(data)

    # Tập hợp tất cả fields từ types
    all_fields: list[FederatedField] = []
    for t in types:
        all_fields.extend(t.fields)

    return GraphQLIR(
        services=services,
        types=types,
        fields=all_fields,
        resolvers=resolvers,
        gateway_config=gateway,
    )


__all__ = [
    "GraphQLIR",
    "parse_services",
    "parse_types",
    "parse_resolvers",
    "parse_gateway_config",
    "parse_to_ir",
]
