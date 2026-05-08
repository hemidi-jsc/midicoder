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
