# coding: utf-8
"""
Mô-đun models cho CP60 — Service Discovery & Config Center.

Định nghĩa các dataclass biểu diễn:
- ServiceInstance: Thực thể service với host, port, protocol, health check
- ServiceRegistry: Registry quản lý service (Consul, etcd, ZooKeeper, Eureka)
- ConfigEntry: mục cấu hình theo môi trường với encryption và versioning
- ConfigWatch: watcher theo dõi thay đổi config và gọi callback
- LoadBalancingConfig: Cấu hình load balancing với health check

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP60).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class Protocol(str, Enum):
    """Giao thức communication.

    - HTTP: Giao thức HTTP thông thường
    - HTTPS: Giao thức HTTP over TLS
    - GRPC: gRPC protocol
    """
    HTTP = "http"
    HTTPS = "https"
    GRPC = "grpc"


class RegistryProvider(str, Enum):
    """Nhà cung cấp service registry.

    - CONSUL: HashiCorp Consul
    - ETCD: CoreOS etcd
    - ZOOKEEPER: Apache ZooKeeper
    - EUREKA: Netflix Eureka
    """
    CONSUL = "consul"
    ETCD = "etcd"
    ZOOKEEPER = "zookeeper"
    EUREKA = "eureka"


class Environment(str, Enum):
    """Môi trường triển khai.

    - DEV: Môi trường phát triển
    - STAGING: Môi trường kiểm thử
    - PROD: Môi trường sản xuất
    """
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class LBStrategy(str, Enum):
    """Chiến lược load balancing.

    - ROUND_ROBIN: Phân phối lần lượt
    - LEAST_CONNECTIONS: Ưu tiên instance ít kết nối nhất
    - RANDOM: Phân phối ngẫu nhiên
    - WEIGHTED: Phân phối theo trọng số
    """
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED = "weighted"


# ===========================================================================
# ServiceInstance
# ===========================================================================


@dataclass
class ServiceInstance:
    """Thực thể service đang hoạt động.

    Đại diện cho một instance của service được đăng ký vào registry,
    bao gồm thông tin kết nối, health check, và metadata bổ sung.

    Attributes:
        instance_id: ID duy nhất của instance
        service_name: Tên service (vd: "order-service")
        host: Địa chỉ host
        port: Cổng mạng
        protocol: Giao thức (http, https, grpc)
        metadata: Metadata bổ sung (version, region, v.v.)
        health_check_path: Đường dẫn health check endpoint
        tags: Danh sách tags để phân loại
        registered_at: Thời điểm đăng ký
        last_heartbeat: Thời điểm heartbeat cuối
    """
    instance_id: str
    service_name: str
    host: str
    port: int
    protocol: Protocol = Protocol.HTTP
    metadata: dict[str, Any] = field(default_factory=dict)
    health_check_path: str = "/health"
    tags: list[str] = field(default_factory=list)
    registered_at: datetime | None = None
    last_heartbeat: datetime | None = None

    def __post_init__(self) -> None:
        """Validate ServiceInstance sau khi khởi tạo."""
        if not self.instance_id or not self.instance_id.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="instance_id bắt buộc và không được để trống",
            )
        if not self.service_name or not self.service_name.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="service_name bắt buộc và không được để trống",
            )
        if self.port < 1 or self.port > 65535:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"port phải nằm trong khoảng 1-65535, nhận được: {self.port}",
            )
        now = datetime.now(timezone.utc)
        if self.registered_at is None:
            self.registered_at = now
        if self.last_heartbeat is None:
            self.last_heartbeat = now

    @property
    def address(self) -> str:
        """Trả về địa chỉ đầy đủ của instance."""
        return f"{self.protocol.value}://{self.host}:{self.port}"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ServiceInstance sang dict."""
        return {
            "instance_id": self.instance_id,
            "service_name": self.service_name,
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol.value,
            "metadata": self.metadata,
            "health_check_path": self.health_check_path,
            "tags": self.tags,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceInstance":
        """Tạo ServiceInstance từ dict."""
        return cls(
            instance_id=data["instance_id"],
            service_name=data["service_name"],
            host=data["host"],
            port=data["port"],
            protocol=Protocol(data.get("protocol", "http")),
            metadata=data.get("metadata", {}),
            health_check_path=data.get("health_check_path", "/health"),
            tags=data.get("tags", []),
        )


# ===========================================================================
# ServiceRegistry
# ===========================================================================


@dataclass
class ServiceRegistry:
    """Registry quản lý service discovery.

    Cấu hình registry provider để quản lý việc đăng ký và phát hiện service,
    bao gồm thông tin quorum, session TTL, và danh sách peer nodes.

    Attributes:
        registry_id: ID duy nhất của registry
        name: Tên registry
        provider: Nhà cung cấp registry (consul, etcd, zookeeper, eureka)
        quorum_size: Số node tối thiểu cho quorum
        session_ttl: Thời gian sống của session (giây)
        peer_nodes: Danh sách địa chỉ peer nodes
        metadata: Metadata bổ sung
    """
    registry_id: str
    name: str
    provider: RegistryProvider = RegistryProvider.CONSUL
    quorum_size: int = 3
    session_ttl: int = 30
    peer_nodes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate ServiceRegistry sau khi khởi tạo."""
        if not self.registry_id or not self.registry_id.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="registry_id bắt buộc và không được để trống",
            )
        if self.quorum_size < 1:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"quorum_size phải lớn hơn 0, nhận được: {self.quorum_size}",
            )
        if self.session_ttl < 1:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"session_ttl phải lớn hơn 0, nhận được: {self.session_ttl}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ServiceRegistry sang dict."""
        return {
            "registry_id": self.registry_id,
            "name": self.name,
            "provider": self.provider.value,
            "quorum_size": self.quorum_size,
            "session_ttl": self.session_ttl,
            "peer_nodes": self.peer_nodes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceRegistry":
        """Tạo ServiceRegistry từ dict."""
        return cls(
            registry_id=data["registry_id"],
            name=data["name"],
            provider=RegistryProvider(data.get("provider", "consul")),
            quorum_size=data.get("quorum_size", 3),
            session_ttl=data.get("session_ttl", 30),
            peer_nodes=data.get("peer_nodes", []),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# ConfigEntry
# ===========================================================================


@dataclass
class ConfigEntry:
    """Mục cấu hình theo môi trường.

    Lưu trữ một mục cấu hình với hỗ trợ environment-specific override,
    encryption, versioning, và watcher notification.

    Attributes:
        entry_id: ID duy nhất của config entry
        key: Key của cấu hình (vd: "database.url")
        value: Giá trị cấu hình
        environment: Môi trường áp dụng (dev, staging, prod)
        encrypted: Có được mã hóa không
        version: Số phiên bản
        watchers: Danh sách watcher IDs đang theo dõi
        metadata: Metadata bổ sung
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
    """
    entry_id: str
    key: str
    value: str
    environment: Environment = Environment.DEV
    encrypted: bool = False
    version: int = 1
    watchers: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate ConfigEntry sau khi khởi tạo."""
        if not self.entry_id or not self.entry_id.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="entry_id bắt buộc và không được để trống",
            )
        if not self.key or not self.key.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="key bắt buộc và không được để trống",
            )
        if self.version < 1:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"version phải lớn hơn hoặc bằng 1, nhận được: {self.version}",
            )
        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @property
    def masked_value(self) -> str:
        """Trả về giá trị đã mask nếu encrypted."""
        if self.encrypted and self.value:
            if len(self.value) <= 4:
                return "****"
            return f"****{self.value[-4:]}"
        return self.value

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ConfigEntry sang dict."""
        return {
            "entry_id": self.entry_id,
            "key": self.key,
            "value": self.masked_value,
            "environment": self.environment.value,
            "encrypted": self.encrypted,
            "version": self.version,
            "watchers": self.watchers,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfigEntry":
        """Tạo ConfigEntry từ dict."""
        return cls(
            entry_id=data["entry_id"],
            key=data["key"],
            value=data.get("value", ""),
            environment=Environment(data.get("environment", "dev")),
            encrypted=data.get("encrypted", False),
            version=data.get("version", 1),
            watchers=data.get("watchers", []),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# ConfigWatch
# ===========================================================================


@dataclass
class ConfigWatch:
    """Watcher theo dõi thay đổi config.

    Đăng ký một watcher để nhận thông báo khi config entry thay đổi,
    với khả năng polling hoặc event-driven notification.

    Attributes:
        watch_id: ID duy nhất của watcher
        config_key: Key của config đang theo dõi
        callback_url: URL nhận callback khi config thay đổi
        polling_interval_seconds: Khoảng thời gian polling (giây)
        trigger_on_change: Có kích hoạt khi config thay đổi không
        metadata: Metadata bổ sung
    """
    watch_id: str
    config_key: str
    callback_url: str
    polling_interval_seconds: int = 30
    trigger_on_change: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate ConfigWatch sau khi khởi tạo."""
        if not self.watch_id or not self.watch_id.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="watch_id bắt buộc và không được để trống",
            )
        if not self.config_key or not self.config_key.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="config_key bắt buộc và không được để trống",
            )
        if not self.callback_url or not self.callback_url.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="callback_url bắt buộc và không được để trống",
            )
        if self.polling_interval_seconds < 1:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"polling_interval_seconds phải lớn hơn 0, nhận được: {self.polling_interval_seconds}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ConfigWatch sang dict."""
        return {
            "watch_id": self.watch_id,
            "config_key": self.config_key,
            "callback_url": self.callback_url,
            "polling_interval_seconds": self.polling_interval_seconds,
            "trigger_on_change": self.trigger_on_change,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfigWatch":
        """Tạo ConfigWatch từ dict."""
        return cls(
            watch_id=data["watch_id"],
            config_key=data["config_key"],
            callback_url=data["callback_url"],
            polling_interval_seconds=data.get("polling_interval_seconds", 30),
            trigger_on_change=data.get("trigger_on_change", True),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# LoadBalancingConfig
# ===========================================================================


@dataclass
class LoadBalancingConfig:
    """Cấu hình load balancing cho service.

    Định nghĩa chiến lược phân phối traffic giữa các instance của service,
    kèm health check interval và retry policy.

    Attributes:
        config_id: ID duy nhất của cấu hình
        service_name: Tên service áp dụng load balancing
        strategy: Chiến lược load balancing
        health_check_interval: Khoảng thời gian health check (giây)
        max_retries: Số lần retry tối đa khi instance không phản hồi
        metadata: Metadata bổ sung
    """
    config_id: str
    service_name: str
    strategy: LBStrategy = LBStrategy.ROUND_ROBIN
    health_check_interval: int = 15
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate LoadBalancingConfig sau khi khởi tạo."""
        if not self.config_id or not self.config_id.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="config_id bắt buộc và không được để trống",
            )
        if not self.service_name or not self.service_name.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="service_name bắt buộc và không được để trống",
            )
        if self.health_check_interval < 1:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"health_check_interval phải lớn hơn 0, nhận được: {self.health_check_interval}",
            )
        if self.max_retries < 0:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"max_retries phải lớn hơn hoặc bằng 0, nhận được: {self.max_retries}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển LoadBalancingConfig sang dict."""
        return {
            "config_id": self.config_id,
            "service_name": self.service_name,
            "strategy": self.strategy.value,
            "health_check_interval": self.health_check_interval,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LoadBalancingConfig":
        """Tạo LoadBalancingConfig từ dict."""
        return cls(
            config_id=data["config_id"],
            service_name=data["service_name"],
            strategy=LBStrategy(data.get("strategy", "round_robin")),
            health_check_interval=data.get("health_check_interval", 15),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {}),
        )
