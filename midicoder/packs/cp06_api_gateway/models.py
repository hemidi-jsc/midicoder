# coding: utf-8
"""
Mô-đun models cho Kong Gateway & Consul Service Mesh (CP06).

Định nghĩa các dataclass biểu diễn:
- KongGateway: Cấu hình gateway chính
- KongService: Backend service trong Kong
- KongRoute: Route mapping trong Kong
- KongUpstream: Load balancing upstream
- KongPlugin: Plugin cấu hình (rate-limiting, circuit-breaker...)
- ConsulService: Service đăng ký trong Consul
- ConsulHealthCheck: Health check định nghĩa
- ConsulConnect: Connect proxy configuration

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


# ===========================================================================
# Kong Gateway Models
# ===========================================================================


@dataclass
class KongGateway:
    """
    Cấu hình Kong Gateway chính.

    Attributes:
        name: Tên gateway instance
        listen_port: Cổng listener cho traffic
        ssl: Có bật SSL không
        admin_listen_port: Cổng admin API
    """
    name: str
    listen_port: int = 8000
    ssl: bool = False
    admin_listen_port: int = 8001

    def __post_init__(self) -> None:
        """Validate cấu hình gateway sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            raise ValueError("Tên gateway không được để trống")
        if not (1 <= self.listen_port <= 65535):
            raise ValueError("Cổng listen_port phải từ 1 đến 65535")
        if not (1 <= self.admin_listen_port <= 65535):
            raise ValueError("Cổng admin_listen_port phải từ 1 đến 65535")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển gateway config sang dict format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KongGateway":
        """Tạo KongGateway từ dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class KongService:
    """
    Backend service trong Kong Gateway.

    Attributes:
        name: Tên service
        url: URL backend service
        protocol: Protocol (http, https, grpc, grpcs)
        port: Cổng backend
        host: Host backend
        connect_timeout: Timeout kết nối (ms)
        write_timeout: Timeout ghi (ms)
        read_timeout: Timeout đọc (ms)
    """
    name: str
    url: str = "http://localhost:3000"
    protocol: str = "http"
    port: int = 3000
    host: str = "localhost"
    connect_timeout: int = 60000
    write_timeout: int = 60000
    read_timeout: int = 60000

    def __post_init__(self) -> None:
        """Validate cấu hình service sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            raise ValueError("Tên service không được để trống")
        valid_protocols = ("http", "https", "grpc", "grpcs", "tcp", "tls")
        if self.protocol not in valid_protocols:
            raise ValueError(f"Protocol phải là một trong: {valid_protocols}")
        if not (1 <= self.port <= 65535):
            raise ValueError("Cổng port phải từ 1 đến 65535")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển service config sang dict format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KongService":
        """Tạo KongService từ dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class KongRoute:
    """
    Route mapping trong Kong Gateway.

    Attributes:
        name: Tên route
        paths: Danh sách URL paths
        methods: Danh sách HTTP methods được phép
        service: Reference đến KongService
        strip_path: Có strip prefix path không
        preserve_host: Có giữ header Host gốc không
        hosts: Danh sách host patterns
        headers: Header matching conditions
    """
    name: str
    paths: list[str] = field(default_factory=list)
    methods: list[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    )
    service: Optional[str] = None
    strip_path: bool = True
    preserve_host: bool = False
    hosts: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate cấu hình route sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            raise ValueError("Tên route không được để trống")
        valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
        for method in self.methods:
            if method.upper() not in valid_methods:
                raise ValueError(f"HTTP method '{method}' không hợp lệ")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển route config sang dict format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KongRoute":
        """Tạo KongRoute từ dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class KongTarget:
    """
    Target trong Kong Upstream (backend instance).

    Attributes:
        target: Address của backend (host:port)
        weight: Weight cho load balancing (1-1000)
    """
    target: str
    weight: int = 100

    def __post_init__(self) -> None:
        """Validate target sau khi khởi tạo."""
        if not self.target or not self.target.strip():
            raise ValueError("Target address không được để trống")
        if not (1 <= self.weight <= 1000):
            raise ValueError("Weight phải từ 1 đến 1000")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển target sang dict format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KongTarget":
        """Tạo KongTarget từ dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class KongUpstream:
    """
    Load balancing upstream trong Kong.

    Attributes:
        name: Tên upstream
        algorithm: Thuật toán load balancing
        hash_fallback: Fallback algorithm
        slots: Số slots cho consistent hashing
        targets: Danh sách backend targets
        healthchecks: Cấu hình health check
    """
    name: str
    algorithm: str = "round-robin"
    hash_fallback: str = "round-robin"
    slots: int = 10000
    targets: list[KongTarget] = field(default_factory=list)
    healthchecks: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate upstream sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            raise ValueError("Tên upstream không được để trống")
        valid_algorithms = ("round-robin", "least-connections", "consistent-hashing")
        if self.algorithm not in valid_algorithms:
            raise ValueError(f"Algorithm phải là một trong: {valid_algorithms}")
        if not (100 <= self.slots <= 100000):
            raise ValueError("Slots phải từ 100 đến 100000")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển upstream config sang dict format."""
        d = asdict(self)
        d["targets"] = [t.to_dict() if isinstance(t, KongTarget) else t for t in self.targets]
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KongUpstream":
        """Tạo KongUpstream từ dict."""
        targets_data = data.pop("targets", [])
        upstream = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        if targets_data:
            upstream.targets = [
                KongTarget.from_dict(t) if isinstance(t, dict) else t for t in targets_data
            ]
        return upstream


class PluginName(str, Enum):
    """Enum các plugin Kong được hỗ trợ."""
    RATE_LIMITING = "rate-limiting"
    CORS = "cors"
    AUTH_KEYAUTH = "key-auth"
    AUTH_JWT = "jwt"
    BASIC_AUTH = "basic-auth"
    OAUTH2 = "oauth2"
    REQUEST_TRANSFORMER = "request-transformer"
    RESPONSE_TRANSFORMER = "response-transformer"
    IP_RESTRICTION = "ip-restriction"
    ACL = "acl"
    BOT_DETECTION = "bot-detection"
    CORRELATION_ID = "correlation-id"
    FILE_LOG = "file-log"
    REQUEST_SIZELIMITER = "request-size-limiting"
    NATIVE_AUTH = "openid-connect"


@dataclass
class KongPlugin:
    """
    Plugin cấu hình trong Kong Gateway.

    Attributes:
        name: Tên plugin
        config: Config parameters của plugin
        service: Apply vào service cụ thể (optional)
        route: Apply vào route cụ thể (optional)
        consumer: Apply vào consumer cụ thể (optional)
        enabled: Có bật plugin không
    """
    name: str
    config: dict[str, Any] = field(default_factory=dict)
    service: Optional[str] = None
    route: Optional[str] = None
    consumer: Optional[str] = None
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate plugin sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            raise ValueError("Tên plugin không được để trống")
        # Kiểm tra plugin có apply vào ít nhất 1 scope (service/route/consumer) hoặc global
        # Không bắt buộc — global plugin không cần scope

    def to_dict(self) -> dict[str, Any]:
        """Chuyển plugin config sang dict format."""
        d = asdict(self)
        # Loại bỏ optional fields là None
        d = {k: v for k, v in d.items() if v is not None}
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KongPlugin":
        """Tạo KongPlugin từ dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ===========================================================================
# Consul Service Mesh Models
# ===========================================================================


@dataclass
class ConsulService:
    """
    Service đăng ký trong Consul Service Catalog.

    Attributes:
        name: Tên service
        service_id: ID duy nhất của service instance
        port: Cổng service
        address: Address của service
        tags: Danh sách tags
        meta: Metadata key-value
        weight_healthy: Weight cho healthy instance
        weight_unhealthy: Weight cho unhealthy instance
    """
    name: str
    service_id: Optional[str] = None
    port: int = 80
    address: str = "localhost"
    tags: list[str] = field(default_factory=list)
    meta: dict[str, str] = field(default_factory=dict)
    weight_healthy: int = 1
    weight_unhealthy: int = 0

    def __post_init__(self) -> None:
        """Validate service sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            raise ValueError("Tên service không được để trống")
        if not (1 <= self.port <= 65535):
            raise ValueError("Cổng port phải từ 1 đến 65535")
        if not (0 <= self.weight_healthy <= 100):
            raise ValueError("weight_healthy phải từ 0 đến 100")
        if not (0 <= self.weight_unhealthy <= 100):
            raise ValueError("weight_unhealthy phải từ 0 đến 100")
        # Auto-generate service_id nếu không có
        if not self.service_id:
            self.service_id = f"{self.name}-{self.port}"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển service config sang dict format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsulService":
        """Tạo ConsulService từ dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class HealthCheckType(str, Enum):
    """Enum các loại health check trong Consul."""
    HTTP = "http"
    TCP = "tcp"
    EXEC = "exec"
    TTL = "ttl"
    DOTCLRI = "dotclr"


@dataclass
class ConsulHealthCheck:
    """
    Health check định nghĩa trong Consul.

    Attributes:
        id: ID duy nhất của health check
        name: Tên hiển thị
        service_id: Reference đến service
        check_type: Loại health check (http/tcp/exec/ttl)
        interval: Khoảng thời gian giữa các checks
        timeout: Timeout cho mỗi check
        http: URL cho HTTP check
        tcp: Address cho TCP check
        exec: Command cho exec check
        ttl: TTL duration
        deregister_critical_service_after: Auto-deregister sau bao lâu critical
        notes: Ghi chú cho operators
        status: Trạng thái hiện tại
        tags: Danh sách tags
    """
    id: str
    name: str = ""
    service_id: Optional[str] = None
    check_type: HealthCheckType = HealthCheckType.HTTP
    interval: str = "10s"
    timeout: str = "5s"
    http: Optional[str] = None
    tcp: Optional[str] = None
    exec: Optional[str] = None
    ttl: Optional[str] = None
    deregister_critical_service_after: Optional[str] = None
    notes: str = ""
    status: str = "passing"
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate health check sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise ValueError("ID health check không được để trống")
        # Validate interval/timeout format (Consul duration format)
        if not re.match(r"^\d+(\.\d+)?(ms|s|m|h)$", self.interval):
            raise ValueError(f"Interval format không hợp lệ: {self.interval} (dùng '10s', '1m', '500ms')")
        if not re.match(r"^\d+(\.\d+)?(ms|s|m|h)$", self.timeout):
            raise ValueError(f"Timeout format không hợp lệ: {self.timeout}")
        # HTTP check cần có http URL
        if self.check_type == HealthCheckType.HTTP and not self.http:
            raise ValueError("HTTP health check cần có URL")
        # TCP check cần có tcp address
        if self.check_type == HealthCheckType.TCP and not self.tcp:
            raise ValueError("TCP health check cần có address")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển health check sang dict format."""
        d = asdict(self)
        d["check_type"] = self.check_type.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsulHealthCheck":
        """Tạo ConsulHealthCheck từ dict."""
        check_type = data.get("check_type", "http")
        if not isinstance(check_type, HealthCheckType):
            check_type = HealthCheckType(check_type)
        data["check_type"] = check_type
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ConsulUpstream:
    """
    Upstream definition cho Consul Connect proxy.

    Attributes:
        destination_name: Tên dịch vụ đích
        local_bind_port: Cổng local bind
    """
    destination_name: str
    local_bind_port: int = 0

    def __post_init__(self) -> None:
        """Validate upstream sau khi khởi tạo."""
        if not self.destination_name or not self.destination_name.strip():
            raise ValueError("Destination name không được để trống")
        if not (0 <= self.local_bind_port <= 65535):
            raise ValueError("Cổng local_bind_port phải từ 0 đến 65535")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển upstream sang dict format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsulUpstream":
        """Tạo ConsulUpstream từ dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ConsulConnect:
    """
    Connect proxy configuration trong Consul.

    Attributes:
        service: Tên service dùng Connect
        upstreams: Danh sách upstream services
    """
    service: str
    upstreams: list[ConsulUpstream] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate connect config sau khi khởi tạo."""
        if not self.service or not self.service.strip():
            raise ValueError("Service name không được để trống")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển connect config sang dict format."""
        d = asdict(self)
        d["upstreams"] = [
            u.to_dict() if isinstance(u, ConsulUpstream) else u for u in self.upstreams
        ]
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsulConnect":
        """Tạo ConsulConnect từ dict."""
        upstreams_data = data.get("upstreams", [])
        connect = cls(
            service=data.get("service", ""),
        )
        if upstreams_data:
            connect.upstreams = [
                ConsulUpstream.from_dict(u) if isinstance(u, dict) else u
                for u in upstreams_data
            ]
        return connect


@dataclass
class ConsulServiceMesh:
    """
    Service Mesh configuration tổng thể.

    Attributes:
        name: Tên mesh
        datacenter: Datacenter
        protocol: Protocol mặc định
    """
    name: str
    datacenter: str = "dc1"
    protocol: str = "http"

    def __post_init__(self) -> None:
        """Validate mesh config sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            raise ValueError("Tên mesh không được để trống")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển mesh config sang dict format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsulServiceMesh":
        """Tạo ConsulServiceMesh từ dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ===========================================================================
# HTTP Route Models
# ===========================================================================


class HttpMethod(str, Enum):
    """
    Enum các HTTP methods được hỗ trợ.
    """
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AuthMode(str, Enum):
    """
    Enum các chế độ authentication cho routes.
    """
    NONE = "none"
    JWT = "jwt"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    SESSION = "session"


@dataclass
class RouteParam:
    """
    Tham số đường dẫn route (path parameter).

    Attributes:
        name: Tên tham số
        param_type: Kiểu dữ liệu (str, int, uuid, etc.)
        required: Có bắt buộc không
        description: Mô tả tham số
    """
    name: str
    param_type: str = "str"
    required: bool = True
    description: str = ""


@dataclass
class QueryParam:
    """
    Query parameter cho route.

    Attributes:
        name: Tên tham số
        param_type: Kiểu dữ liệu
        required: Có bắt buộc không
        default: Giá trị mặc định
        description: Mô tả tham số
    """
    name: str
    param_type: str = "str"
    required: bool = False
    default: Any = None
    description: str = ""


@dataclass
class SchemaField:
    """
    Field trong request/response schema.

    Attributes:
        name: Tên field
        field_type: Kiểu dữ liệu (str, int, bool, etc.)
        required: Có bắt buộc không
        description: Mô tả field
        example: Ví dụ giá trị
    """
    name: str
    field_type: str = "str"
    required: bool = False
    description: str = ""
    example: Any = None


@dataclass
class RouteAuthConfig:
    """
    Cấu hình authentication cho route.

    Attributes:
        mode: Chế độ auth (JWT, OAuth2, API_KEY, ...)
        required_roles: Danh sách roles được phép
        required_permissions: Danh sách permissions được phép
        tenant_scoped: Có enforce tenant scope không (KPI-029)
    """
    mode: AuthMode = AuthMode.JWT
    required_roles: list[str] = field(default_factory=list)
    required_permissions: list[str] = field(default_factory=list)
    tenant_scoped: bool = True  # KPI-029: mặc định tenant_scoped


@dataclass
class Route:
    """
    HTTP REST Route model.

    Biểu diễn một HTTP route với đầy đủ thông tin:
    method, path, handler binding, auth config, schemas.

    Attributes:
        id: Định danh duy nhất của route
        description: Mô tả route (tiếng Việt)
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        path: URL path (ví dụ: /api/v1/orders/{order_id})
        handler_type: Loại handler (command hoặc query)
        handler_id: ID của command/query handler
        tags: Danh sách tags để group routes
        auth: Auth config cho route
        path_params: Các path parameters
        query_params: Các query parameters
        request_schema: Schema cho request body
        response_schema: Schema cho response body
        response_status: HTTP status code mặc định (200, 201, 204)
        deprecated: Route có deprecated không
    """
    id: str
    description: str = ""
    method: HttpMethod = HttpMethod.GET
    path: str = ""
    handler_type: str = "query"
    handler_id: str = ""
    tags: list[str] = field(default_factory=list)
    auth: Optional[RouteAuthConfig] = None
    path_params: list[RouteParam] = field(default_factory=list)
    query_params: list[QueryParam] = field(default_factory=list)
    request_schema: list[SchemaField] = field(default_factory=list)
    response_schema: list[SchemaField] = field(default_factory=list)
    response_status: int = 200
    deprecated: bool = False

    def is_write_operation(self) -> bool:
        """
        Kiểm tra route có phải là write operation không.

        Returns:
            True nếu method là POST, PUT, PATCH, DELETE
        """
        return self.method in (
            HttpMethod.POST,
            HttpMethod.PUT,
            HttpMethod.PATCH,
            HttpMethod.DELETE,
        )

    def is_read_operation(self) -> bool:
        """
        Kiểm tra route có phải là read operation không.

        Returns:
            True nếu method là GET, HEAD, OPTIONS
        """
        return self.method in (
            HttpMethod.GET,
            HttpMethod.HEAD,
            HttpMethod.OPTIONS,
        )

    def requires_auth(self) -> bool:
        """
        Kiểm tra route có cần authentication không.

        Returns:
            True nếu auth config tồn tại và mode != NONE
        """
        return self.auth is not None and self.auth.mode != AuthMode.NONE

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển route sang dict format (cho MIR metadata).

        Returns:
            Dictionary representation của route
        """
        return {
            "id": self.id,
            "description": self.description,
            "method": self.method.value,
            "path": self.path,
            "handler_type": self.handler_type,
            "handler_id": self.handler_id,
            "tags": self.tags,
            "auth": {
                "mode": self.auth.mode.value,
                "required_roles": self.auth.required_roles,
                "required_permissions": self.auth.required_permissions,
                "tenant_scoped": self.auth.tenant_scoped,
            }
            if self.auth
            else None,
            "path_params": [
                {"name": p.name, "type": p.param_type, "required": p.required}
                for p in self.path_params
            ],
            "query_params": [
                {"name": p.name, "type": p.param_type, "required": p.required}
                for p in self.query_params
            ],
            "request_schema": [
                {"name": f.name, "type": f.field_type, "required": f.required}
                for f in self.request_schema
            ],
            "response_schema": [
                {"name": f.name, "type": f.field_type, "required": f.required}
                for f in self.response_schema
            ],
            "response_status": self.response_status,
            "deprecated": self.deprecated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Route":
        """
        Tạo Route từ dict (từ MIR metadata).

        Args:
            data: Dictionary chứa route data

        Returns:
            Route instance
        """
        auth_data = data.get("auth")
        auth = None
        if auth_data:
            auth = RouteAuthConfig(
                mode=AuthMode(auth_data.get("mode", "jwt")),
                required_roles=auth_data.get("required_roles", []),
                required_permissions=auth_data.get("required_permissions", []),
                tenant_scoped=auth_data.get("tenant_scoped", True),
            )

        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            method=HttpMethod(data.get("method", "GET")),
            path=data.get("path", ""),
            handler_type=data.get("handler_type", "query"),
            handler_id=data.get("handler_id", ""),
            tags=data.get("tags", []),
            auth=auth,
            path_params=[
                RouteParam(
                    name=p["name"],
                    param_type=p.get("type", p.get("param_type", "str")),
                    required=p.get("required", True),
                )
                for p in data.get("path_params", [])
            ],
            query_params=[
                QueryParam(
                    name=p["name"],
                    param_type=p.get("type", p.get("param_type", "str")),
                    required=p.get("required", False),
                )
                for p in data.get("query_params", [])
            ],
            request_schema=[
                SchemaField(
                    name=f["name"],
                    field_type=f.get("type", f.get("field_type", "str")),
                    required=f.get("required", False),
                )
                for f in data.get("request_schema", [])
            ],
            response_schema=[
                SchemaField(
                    name=f["name"],
                    field_type=f.get("type", f.get("field_type", "str")),
                    required=f.get("required", False),
                )
                for f in data.get("response_schema", [])
            ],
            response_status=data.get("response_status", 200),
            deprecated=data.get("deprecated", False),
        )


# ===========================================================================
# GraphQL Resolver Models
# ===========================================================================


class GraphQLOperation(str, Enum):
    """
    Enum các GraphQL operation types.
    """
    QUERY = "query"
    MUTATION = "mutation"
    SUBSCRIPTION = "subscription"


@dataclass
class GraphQLArg:
    """
    Argument cho GraphQL resolver.

    Attributes:
        name: Tên argument
        arg_type: Kiểu dữ liệu GraphQL (String, Int, Boolean, ID, ...)
        required: Có bắt buộc không
        description: Mô tả argument
    """
    name: str
    arg_type: str = "String"
    required: bool = False
    description: str = ""


@dataclass
class GraphQLField:
    """
    Field trong GraphQL return type.

    Attributes:
        name: Tên field
        field_type: Kiểu dữ liệu GraphQL
        description: Mô tả field
    """
    name: str
    field_type: str = "String"
    description: str = ""


@dataclass
class GraphQLResolver:
    """
    GraphQL Resolver model.

    Biểu diễn một GraphQL resolver (query/mutation/subscription).

    Attributes:
        id: Định danh duy nhất
        description: Mô tả resolver
        operation: Loại operation (query, mutation, subscription)
        type_name: Tên GraphQL type (Query, Mutation, ...)
        field_name: Tên field trong type
        handler_id: ID của command/query handler phía backend
        args: Danh sách arguments
        returns: Return schema (fields)
        auth_required: Có cần auth không
        tenant_scoped: Có enforce tenant scope không (KPI-029)
        tags: Danh sách tags
    """
    id: str
    description: str = ""
    operation: GraphQLOperation = GraphQLOperation.QUERY
    type_name: str = "Query"
    field_name: str = ""
    handler_id: str = ""
    args: list[GraphQLArg] = field(default_factory=list)
    returns: list[GraphQLField] = field(default_factory=list)
    auth_required: bool = True
    tenant_scoped: bool = True  # KPI-029
    tags: list[str] = field(default_factory=list)

    def is_mutation(self) -> bool:
        """
        Kiểm tra resolver có phải là mutation không.

        Returns:
            True nếu operation là MUTATION
        """
        return self.operation == GraphQLOperation.MUTATION

    def is_subscription(self) -> bool:
        """
        Kiểm tra resolver có phải là subscription không.

        Returns:
            True nếu operation là SUBSCRIPTION
        """
        return self.operation == GraphQLOperation.SUBSCRIPTION

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển resolver sang dict format.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "description": self.description,
            "operation": self.operation.value,
            "type_name": self.type_name,
            "field_name": self.field_name,
            "handler_id": self.handler_id,
            "args": [
                {"name": a.name, "type": a.arg_type, "required": a.required}
                for a in self.args
            ],
            "returns": [
                {"name": f.name, "type": f.field_type}
                for f in self.returns
            ],
            "auth_required": self.auth_required,
            "tenant_scoped": self.tenant_scoped,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphQLResolver":
        """
        Tạo GraphQLResolver từ dict.

        Args:
            data: Dictionary chứa resolver data

        Returns:
            GraphQLResolver instance
        """
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            operation=GraphQLOperation(data.get("operation", "query")),
            type_name=data.get("type_name", "Query"),
            field_name=data.get("field_name", ""),
            handler_id=data.get("handler_id", ""),
            args=[
                GraphQLArg(
                    name=a["name"],
                    arg_type=a.get("type", a.get("arg_type", "String")),
                    required=a.get("required", False),
                )
                for a in data.get("args", [])
            ],
            returns=[
                GraphQLField(
                    name=f["name"],
                    field_type=f.get("type", f.get("field_type", "String")),
                )
                for f in data.get("returns", [])
            ],
            auth_required=data.get("auth_required", True),
            tenant_scoped=data.get("tenant_scoped", True),
            tags=data.get("tags", []),
        )


# ===========================================================================
# Webhook Handler Models
# ===========================================================================


class WebhookAuthType(str, Enum):
    """
    Enum các loại authentication cho webhook.
    """
    NONE = "none"
    HMAC_SIGNATURE = "hmac_signature"
    BEARER_TOKEN = "bearer_token"
    CUSTOM_HEADER = "custom_header"


@dataclass
class WebhookAuthConfig:
    """
    Cấu hình authentication cho webhook.

    Attributes:
        auth_type: Loại auth
        header_name: Tên header chứa auth data
        secret_env: Tên env var chứa secret key
        algorithm: Algorithm cho HMAC signing
    """
    auth_type: WebhookAuthType = WebhookAuthType.HMAC_SIGNATURE
    header_name: str = "X-Signature"
    secret_env: str = "WEBHOOK_SECRET"
    algorithm: str = "sha256"


@dataclass
class WebhookPayloadField:
    """
    Field trong webhook payload schema.

    Attributes:
        name: Tên field
        field_type: Kiểu dữ liệu
        required: Có bắt buộc không
        description: Mô tả field
    """
    name: str
    field_type: str = "str"
    required: bool = False
    description: str = ""


@dataclass
class WebhookHandler:
    """
    Webhook Handler model.

    Biểu diễn một webhook endpoint để nhận incoming events từ external systems.

    Attributes:
        id: Định danh duy nhất
        description: Mô tả webhook
        path: URL path để receive webhook
        event_type: Loại event từ webhook
        handler_id: ID của command/handler để process webhook
        auth_config: Auth config cho webhook
        verify_signature: Có verify signature không
        payload_schema: Schema cho payload
        tags: Danh sách tags
    """
    id: str
    description: str = ""
    path: str = ""
    event_type: str = ""
    handler_id: str = ""
    auth_config: Optional[WebhookAuthConfig] = None
    verify_signature: bool = True
    payload_schema: list[WebhookPayloadField] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển webhook handler sang dict format.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "description": self.description,
            "path": self.path,
            "event_type": self.event_type,
            "handler_id": self.handler_id,
            "auth_config": {
                "auth_type": self.auth_config.auth_type.value,
                "header_name": self.auth_config.header_name,
                "secret_env": self.auth_config.secret_env,
                "algorithm": self.auth_config.algorithm,
            }
            if self.auth_config
            else None,
            "verify_signature": self.verify_signature,
            "payload_schema": [
                {"name": f.name, "type": f.field_type, "required": f.required}
                for f in self.payload_schema
            ],
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookHandler":
        """
        Tạo WebhookHandler từ dict.

        Args:
            data: Dictionary chứa webhook data

        Returns:
            WebhookHandler instance
        """
        auth_data = data.get("auth_config")
        auth_config = None
        if auth_data:
            auth_config = WebhookAuthConfig(
                auth_type=WebhookAuthType(auth_data.get("auth_type", "hmac_signature")),
                header_name=auth_data.get("header_name", "X-Signature"),
                secret_env=auth_data.get("secret_env", "WEBHOOK_SECRET"),
                algorithm=auth_data.get("algorithm", "sha256"),
            )

        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            path=data.get("path", ""),
            event_type=data.get("event_type", ""),
            handler_id=data.get("handler_id", ""),
            auth_config=auth_config,
            verify_signature=data.get("verify_signature", True),
            payload_schema=[
                WebhookPayloadField(
                    name=f["name"],
                    field_type=f.get("type", f.get("field_type", "str")),
                    required=f.get("required", False),
                )
                for f in data.get("payload_schema", [])
            ],
            tags=data.get("tags", []),
        )


# ===========================================================================
# Route Collection
# ===========================================================================


@dataclass
class RouteCollection:
    """
    Collection chứa tất cả routes, resolvers, và webhooks.

    Dùng làm output của RouteParser và input cho Stack Emitters.

    Attributes:
        routes: Danh sách HTTP routes
        resolvers: Danh sách GraphQL resolvers
        webhooks: Danh sách webhook handlers
    """
    routes: list[Route] = field(default_factory=list)
    resolvers: list[GraphQLResolver] = field(default_factory=list)
    webhooks: list[WebhookHandler] = field(default_factory=list)

    def add_route(self, route: Route) -> None:
        """
        Thêm HTTP route vào collection.

        Args:
            route: Route instance
        """
        self.routes.append(route)

    def add_resolver(self, resolver: GraphQLResolver) -> None:
        """
        Thêm GraphQL resolver vào collection.

        Args:
            resolver: GraphQLResolver instance
        """
        self.resolvers.append(resolver)

    def add_webhook(self, webhook: WebhookHandler) -> None:
        """
        Thêm webhook handler vào collection.

        Args:
            webhook: WebhookHandler instance
        """
        self.webhooks.append(webhook)

    @property
    def total_count(self) -> int:
        """
        Tổng số items trong collection.

        Returns:
            Tổng số routes + resolvers + webhooks
        """
        return len(self.routes) + len(self.resolvers) + len(self.webhooks)

    def get_by_tag(self, tag: str) -> RouteCollection:
        """
        Lọc collection theo tag.

        Args:
            tag: Tag cần lọc

        Returns:
            RouteCollection chỉ chứa items có tag khớp
        """
        result = RouteCollection()
        result.routes = [r for r in self.routes if tag in r.tags]
        result.resolvers = [r for r in self.resolvers if tag in r.tags]
        result.webhooks = [w for w in self.webhooks if tag in w.tags]
        return result

    def group_routes_by_tag(self) -> dict[str, list[Route]]:
        """
        Nhóm routes theo tag.

        Returns:
            Dictionary {tag: [routes]}
        """
        groups: dict[str, list[Route]] = {}
        for route in self.routes:
            for tag in route.tags:
                if tag not in groups:
                    groups[tag] = []
                groups[tag].append(route)
        return groups

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển collection sang dict format.

        Returns:
            Dictionary representation
        """
        return {
            "routes": [r.to_dict() for r in self.routes],
            "resolvers": [r.to_dict() for r in self.resolvers],
            "webhooks": [w.to_dict() for w in self.webhooks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RouteCollection":
        """
        Tạo RouteCollection từ dict.

        Args:
            data: Dictionary chứa collection data

        Returns:
            RouteCollection instance
        """
        result = cls()
        result.routes = [Route.from_dict(r) for r in data.get("routes", [])]
        result.resolvers = [GraphQLResolver.from_dict(r) for r in data.get("resolvers", [])]
        result.webhooks = [WebhookHandler.from_dict(w) for w in data.get("webhooks", [])]
        return result


# ===========================================================================
# Circuit Breaker (Application-level)
# ===========================================================================


class CircuitState(str, Enum):
    """
    Enum các trạng thái của circuit breaker.

    Values:
        CLOSED: Circuit đóng — traffic đi qua bình thường
        OPEN: Circuit mở — traffic bị chặn, fallback được gọi
        HALF_OPEN: Circuit nửa mở — cho phép một số thử nghiệm probe
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerPolicy(str, Enum):
    """
    Enum các chính sách kích hoạt circuit breaker.

    Values:
        CONSECUTIVE_FAILURES: Kích hoạt khi có N lỗi liên tiếp
        FAILURE_RATE: Kích hoạt khi tỷ lệ lỗi vượt ngưỡng
        AVG_RESPONSE_TIME: Kích hoạt khi thời gian phản hồi trung bình vượt ngưỡng
    """
    CONSECUTIVE_FAILURES = "consecutive_failures"
    FAILURE_RATE = "failure_rate"
    AVG_RESPONSE_TIME = "avg_response_time"


@dataclass
class CircuitBreakerConfig:
    """
    Cấu hình circuit breaker (application-level).

    Bảo vệ các cuộc gọi đến service backend khỏi failure cascade
    bằng cách tạm thời chặn traffic khi service không phản hồi.

    Attributes:
        id: Định danh duy nhất của circuit breaker
        name: Tên hiển thị
        target_service: Tên service backend được bảo vệ
        policy: Chính sách kích hoạt breaker
        threshold: Ngưỡng kích hoạt (số lỗi liên tiếp, tỷ lệ %, ms)
        timeout_seconds: Thời gian ở trạng thái OPEN trước khi chuyển HALF_OPEN
        half_open_max_calls: Số probe calls cho phép trong HALF_OPEN
        success_threshold: Số probe calls thành công để chuyển về CLOSED
        fallback_function: Tên fallback function để gọi khi circuit OPEN
        monitored_exceptions: Danh sách exception types theo dõi
        metadata: Metadata bổ sung
    """
    id: str
    name: str
    target_service: str
    policy: CircuitBreakerPolicy = CircuitBreakerPolicy.CONSECUTIVE_FAILURES
    threshold: float = 5.0
    timeout_seconds: int = 30
    half_open_max_calls: int = 3
    success_threshold: int = 2
    fallback_function: str = ""
    monitored_exceptions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate circuit breaker config sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise ValueError("CircuitBreakerConfig.id không được để trống")
        if self.threshold <= 0:
            raise ValueError("threshold phải lớn hơn 0")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds phải lớn hơn 0")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển circuit breaker config sang dict format."""
        return {
            "id": self.id,
            "name": self.name,
            "target_service": self.target_service,
            "policy": self.policy.value,
            "threshold": self.threshold,
            "timeout_seconds": self.timeout_seconds,
            "half_open_max_calls": self.half_open_max_calls,
            "success_threshold": self.success_threshold,
            "fallback_function": self.fallback_function,
            "monitored_exceptions": self.monitored_exceptions,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CircuitBreakerConfig":
        """Tạo CircuitBreakerConfig từ dict."""
        policy = data.get("policy", "consecutive_failures")
        if not isinstance(policy, CircuitBreakerPolicy):
            policy = CircuitBreakerPolicy(policy)
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            target_service=data.get("target_service", ""),
            policy=policy,
            threshold=data.get("threshold", 5.0),
            timeout_seconds=data.get("timeout_seconds", 30),
            half_open_max_calls=data.get("half_open_max_calls", 3),
            success_threshold=data.get("success_threshold", 2),
            fallback_function=data.get("fallback_function", ""),
            monitored_exceptions=data.get("monitored_exceptions", []),
            metadata=data.get("metadata", {}),
        )
