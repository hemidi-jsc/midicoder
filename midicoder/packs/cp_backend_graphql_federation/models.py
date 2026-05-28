# coding: utf-8
"""
Mô-đun models cho CP57 — GraphQL Schema Federation.

Định nghĩa các dataclass biểu diễn:
- FederationService: Dịch vụ federation với @key directive
- FederatedType: Kiểu dữ liệu được share giữa các service
- FederatedField: Field trong federated type
- FederatedResolver: Resolver cho __resolveReference
- GatewayConfig: Cấu hình Apollo Gateway aggregation

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP57).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# FederationService
# ===========================================================================


@dataclass
class FederationService:
    """Dịch vụ trong GraphQL Federation.

    Đại diện cho một service tham gia vào federated graph, bao gồm
    URL, đường dẫn schema, health check, và danh sách các entity
    mà service này sở hữu.

    Attributes:
        id: ID duy nhất của service
        name: Tên service
        url: URL endpoint GraphQL của service
        schema_path: Đường dẫn đến SDL file (.graphql)
        health_check: Đường dẫn health check endpoint
        port: Port số của service
        entity_ownerships: Danh sách các entity type mà service sở hữu
    """
    id: str
    name: str
    url: str
    schema_path: str = ""
    health_check: str = "/health"
    port: int = 4001
    entity_ownerships: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate FederationService sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-BE04_FEDERATION_SERVICE_NOT_FOUND,
                reason="FederationService.id bắt buộc và không được để trống",
            )
        if not self.name or not self.name.strip():
            raise EM.raise_error(
                ErrorCode.MDC-BE04_FEDERATION_SERVICE_NOT_FOUND,
                reason="FederationService.name bắt buộc và không được để trống",
            )
        if self.port < 1 or self.port > 65535:
            raise EM.raise_error(
                ErrorCode.MDC-BE04_INVALID_GATEWAY_CONFIG,
                reason=f"FederationService.port phải trong khoảng 1-65535, nhận được: {self.port}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển FederationService sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "schema_path": self.schema_path,
            "health_check": self.health_check,
            "port": self.port,
            "entity_ownerships": self.entity_ownerships,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FederationService":
        """Tạo FederationService từ dict."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            url=data.get("url", ""),
            schema_path=data.get("schema_path", ""),
            health_check=data.get("health_check", "/health"),
            port=data.get("port", 4001),
            entity_ownerships=data.get("entity_ownerships", []),
        )


# ===========================================================================
# FederatedField
# ===========================================================================


@dataclass
class FederatedField:
    """Field trong một federated type.

    Đại diện cho một field thuộc về federated type, bao gồm
    tên, kiểu dữ liệu, arguments, và thông tin về resolve_reference.

    Attributes:
        id: ID duy nhất của field
        name: Tên field
        type_str: Kiểu dữ liệu (string như "String!", "Int", "[User]")
        args: Danh sách arguments cho field (dùng cho query/mutation)
        resolve_reference: Có cần __resolveReference không
        deprecation_reason: Lý do deprecate field (nếu có)
    """
    id: str
    name: str
    type_str: str
    args: list[dict[str, Any]] = field(default_factory=list)
    resolve_reference: bool = False
    deprecation_reason: str | None = None

    def __post_init__(self) -> None:
        """Validate FederatedField sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-BE04_INVALID_FEDERATED_TYPE,
                reason="FederatedField.id bắt buộc và không được để trống",
            )
        if not self.name or not self.name.strip():
            raise EM.raise_error(
                ErrorCode.MDC-BE04_INVALID_FEDERATED_TYPE,
                reason="FederatedField.name bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển FederatedField sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "type_str": self.type_str,
            "args": self.args,
            "resolve_reference": self.resolve_reference,
            "deprecation_reason": self.deprecation_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FederatedField":
        """Tạo FederatedField từ dict."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            type_str=data.get("type_str", "String"),
            args=data.get("args", []),
            resolve_reference=data.get("resolve_reference", False),
            deprecation_reason=data.get("deprecation_reason"),
        )


# ===========================================================================
# FederatedType
# ===========================================================================


@dataclass
class FederatedType:
    """Kiểu dữ liệu được share giữa các service trong federation.

    Đại diện cho một entity type với @key directive, bao gồm
    danh sách fields, key fields dùng để resolve reference,
    owning service, và các extension từ service khác.

    Attributes:
        id: ID duy nhất của type
        name: Tên type (PascalCase, vd: "User", "Product")
        fields: Danh sách các fields của type
        key_fields: Danh sách key fields cho @key directive
        owning_service: Service sở hữu type chính
        extensions: Danh sách service extensions (@extends)
    """
    id: str
    name: str
    fields: list[FederatedField] = field(default_factory=list)
    key_fields: list[str] = field(default_factory=list)
    owning_service: str = ""
    extensions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate FederatedType sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-BE04_INVALID_FEDERATED_TYPE,
                reason="FederatedType.id bắt buộc và không được để trống",
            )
        if not self.name or not self.name.strip():
            raise EM.raise_error(
                ErrorCode.MDC-BE04_INVALID_FEDERATED_TYPE,
                reason="FederatedType.name bắt buộc và không được để trống",
            )
        if not self.key_fields:
            raise EM.raise_error(
                ErrorCode.MDC-BE04_INVALID_FEDERATED_TYPE,
                reason=f"FederatedType '{self.name}' cần ít nhất một key field cho @key directive",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển FederatedType sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "fields": [f.to_dict() for f in self.fields],
            "key_fields": self.key_fields,
            "owning_service": self.owning_service,
            "extensions": self.extensions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FederatedType":
        """Tạo FederatedType từ dict."""
        raw_fields = data.get("fields", [])
        fields = [FederatedField.from_dict(f) for f in raw_fields if isinstance(f, dict)]
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            fields=fields,
            key_fields=data.get("key_fields", []),
            owning_service=data.get("owning_service", ""),
            extensions=data.get("extensions", []),
        )


# ===========================================================================
# FederatedResolver
# ===========================================================================


@dataclass
class FederatedResolver:
    """Resolver cho __resolveReference trong federation.

    Đại diện cho một resolver xử lý entity reference resolution,
    bao gồm entity type, query để resolve, và service thực hiện.

    Attributes:
        id: ID duy nhất của resolver
        entity_type: Tên entity type mà resolver xử lý
        resolve_reference_query: Query string để resolve reference
        resolve_reference_service: Service thực hiện resolver
    """
    id: str
    entity_type: str
    resolve_reference_query: str = ""
    resolve_reference_service: str = ""

    def __post_init__(self) -> None:
        """Validate FederatedResolver sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-BE04_INVALID_RESOLVER,
                reason="FederatedResolver.id bắt buộc và không được để trống",
            )
        if not self.entity_type or not self.entity_type.strip():
            raise EM.raise_error(
                ErrorCode.MDC-BE04_INVALID_RESOLVER,
                reason="FederatedResolver.entity_type bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển FederatedResolver sang dict."""
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "resolve_reference_query": self.resolve_reference_query,
            "resolve_reference_service": self.resolve_reference_service,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FederatedResolver":
        """Tạo FederatedResolver từ dict."""
        return cls(
            id=data["id"],
            entity_type=data.get("entity_type", ""),
            resolve_reference_query=data.get("resolve_reference_query", ""),
            resolve_reference_service=data.get("resolve_reference_service", ""),
        )


# ===========================================================================
# GatewayConfig
# ===========================================================================


@dataclass
class GatewayConfig:
    """Cấu hình Apollo Gateway aggregation.

    Chứa cấu hình cho GraphQL gateway, bao gồm danh sách services,
    persisted queries, introspection, CORS, và rate limiting.

    Attributes:
        id: ID duy nhất của gateway config
        services: Danh sách federation services
        persisted_queries_enabled: Có bật persisted queries không
        introspection_enabled: Có bật introspection không
        cors_origins: Danh sách CORS origins được phép
        rate_limit_rps: Giới hạn rate limit (requests per second)
    """
    id: str
    services: list[FederationService] = field(default_factory=list)
    persisted_queries_enabled: bool = False
    introspection_enabled: bool = True
    cors_origins: list[str] = field(default_factory=list)
    rate_limit_rps: int = 100

    def __post_init__(self) -> None:
        """Validate GatewayConfig sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-BE04_INVALID_GATEWAY_CONFIG,
                reason="GatewayConfig.id bắt buộc và không được để trống",
            )
        if self.rate_limit_rps < 1:
            raise EM.raise_error(
                ErrorCode.MDC-BE04_INVALID_GATEWAY_CONFIG,
                reason=f"GatewayConfig.rate_limit_rps phải lớn hơn 0, nhận được: {self.rate_limit_rps}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển GatewayConfig sang dict."""
        return {
            "id": self.id,
            "services": [s.to_dict() for s in self.services],
            "persisted_queries_enabled": self.persisted_queries_enabled,
            "introspection_enabled": self.introspection_enabled,
            "cors_origins": self.cors_origins,
            "rate_limit_rps": self.rate_limit_rps,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GatewayConfig":
        """Tạo GatewayConfig từ dict."""
        raw_services = data.get("services", [])
        services = [FederationService.from_dict(s) for s in raw_services if isinstance(s, dict)]
        return cls(
            id=data["id"],
            services=services,
            persisted_queries_enabled=data.get("persisted_queries_enabled", False),
            introspection_enabled=data.get("introspection_enabled", True),
            cors_origins=data.get("cors_origins", []),
            rate_limit_rps=data.get("rate_limit_rps", 100),
        )
