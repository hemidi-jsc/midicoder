# coding: utf-8
"""
Mô-đun models cho CP54 — Kubernetes & Cloud Native Deployment.

Định nghĩa các dataclass biểu diễn:
- K8sDeployment: Deployment resource trên Kubernetes
- K8sService: Service resource (ClusterIP, NodePort, LoadBalancer)
- K8sIngress: Ingress resource cho external traffic routing
- K8sHPA: Horizontal Pod Autoscaler
- K8sConfigMap: ConfigMap cho configuration data
- K8sSecret: Secret cho sensitive data
- K8sPersistentVolume: PersistentVolumeClaim cho persistent storage
- K8sResources: Resource limits/requests cho container

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ===========================================================================
# Resource Quota
# ===========================================================================


@dataclass
class K8sResources:
    """Tài nguyên CPU và memory cho container.

    Attributes:
        cpu: Số lượng CPU (vd: "250m", "1", "2")
        memory: Lượng memory (vd: "256Mi", "1Gi", "512Mi")
    """
    cpu: str = "250m"
    memory: str = "256Mi"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển K8sResources sang dict."""
        return {
            "cpu": self.cpu,
            "memory": self.memory,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sResources":
        """Tạo K8sResources từ dict."""
        return cls(
            cpu=data.get("cpu", "250m"),
            memory=data.get("memory", "256Mi"),
        )


# ===========================================================================
# Environment Variable
# ===========================================================================


@dataclass
class K8sEnvVar:
    """Biến môi trường cho container.

    Attributes:
        name: Tên biến môi trường
        value: Giá trị tĩnh
        value_from: Reference đến ConfigMap hoặc Secret (key_ref)
    """
    name: str
    value: str | None = None
    value_from: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "value_from": self.value_from,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sEnvVar":
        return cls(
            name=data["name"],
            value=data.get("value"),
            value_from=data.get("value_from"),
        )


# ===========================================================================
# Volume Mount
# ===========================================================================


@dataclass
class K8sVolumeMount:
    """Volume mount cho container.

    Attributes:
        name: Tên volume
        mount_path: Đường dẫn mount trong container
        read_only: Có mount read-only không
    """
    name: str
    mount_path: str
    read_only: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "mount_path": self.mount_path,
            "read_only": self.read_only,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sVolumeMount":
        return cls(
            name=data["name"],
            mount_path=data["mount_path"],
            read_only=data.get("read_only", False),
        )


# ===========================================================================
# Port
# ===========================================================================


@dataclass
class K8sPort:
    """Port exposure cho container hoặc Service.

    Attributes:
        container_port: Port trong container
        protocol: Giao thức (TCP/UDP)
        name: Tên port (tùy chọn)
    """
    container_port: int
    protocol: str = "TCP"
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"container_port": self.container_port, "protocol": self.protocol}
        if self.name:
            d["name"] = self.name
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sPort":
        return cls(
            container_port=data["container_port"],
            protocol=data.get("protocol", "TCP"),
            name=data.get("name", ""),
        )


# ===========================================================================
# K8sDeployment
# ===========================================================================


@dataclass
class K8sDeployment:
    """Deployment resource trên Kubernetes.

    Đại diện cho một workload được quản lý bởi Deployment controller,
    bao gồm số lượng replica, container image, ports, resources,
    strategy và labels.

    Attributes:
        id: ID duy nhất của deployment
        name: Tên deployment trong Kubernetes
        replicas: Số lượng pod replicas
        image: Container image (vd: "myapp:latest")
        ports: Danh sách port exposure
        resources: Resource limits/requests
        strategy: Deployment strategy (RollingUpdate/Recreate)
        labels: Labels cho selector
        env: Danh sách biến môi trường
        volume_mounts: Danh sách volume mounts
    """
    id: str
    name: str
    replicas: int = 1
    image: str = ""
    ports: list[K8sPort] = field(default_factory=list)
    resources: K8sResources = field(default_factory=K8sResources)
    strategy: str = "RollingUpdate"
    labels: dict[str, str] = field(default_factory=dict)
    env: list[K8sEnvVar] = field(default_factory=list)
    volume_mounts: list[K8sVolumeMount] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển K8sDeployment sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "replicas": self.replicas,
            "image": self.image,
            "ports": [p.to_dict() for p in self.ports],
            "resources": self.resources.to_dict(),
            "strategy": self.strategy,
            "labels": self.labels,
            "env": [e.to_dict() for e in self.env],
            "volume_mounts": [v.to_dict() for v in self.volume_mounts],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sDeployment":
        """Tạo K8sDeployment từ dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            replicas=data.get("replicas", 1),
            image=data.get("image", ""),
            ports=[K8sPort.from_dict(p) for p in data.get("ports", [])],
            resources=K8sResources.from_dict(data.get("resources", {})),
            strategy=data.get("strategy", "RollingUpdate"),
            labels=data.get("labels", {}),
            env=[K8sEnvVar.from_dict(e) for e in data.get("env", [])],
            volume_mounts=[K8sVolumeMount.from_dict(v) for v in data.get("volume_mounts", [])],
        )


# ===========================================================================
# K8sService
# ===========================================================================


@dataclass
class K8sService:
    """Service resource trên Kubernetes.

    Đại diện cho service discovery và load balancing cho các pods,
    hỗ trợ các loại ClusterIP, NodePort, và LoadBalancer.

    Attributes:
        id: ID duy nhất của service
        name: Tên service trong Kubernetes
        type: Loại service (ClusterIP/NodePort/LoadBalancer)
        ports: Danh sách port mapping
        selector: Labels selector để match pods
    """
    id: str
    name: str
    type: str = "ClusterIP"
    ports: list[K8sPort] = field(default_factory=list)
    selector: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate service type."""
        valid_types = {"ClusterIP", "NodePort", "LoadBalancer", "ExternalName"}
        if self.type not in valid_types:
            raise ValueError(
                f"Service type '{self.type}' không hợp lệ. "
                f"Phải là một trong: {', '.join(valid_types)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển K8sService sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "ports": [p.to_dict() for p in self.ports],
            "selector": self.selector,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sService":
        """Tạo K8sService từ dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            type=data.get("type", "ClusterIP"),
            ports=[K8sPort.from_dict(p) for p in data.get("ports", [])],
            selector=data.get("selector", {}),
        )


# ===========================================================================
# K8sIngress
# ===========================================================================


@dataclass
class K8sIngressPath:
    """Path rule cho Ingress.

    Attributes:
        path: URL path pattern
        path_type: Path matching type (Prefix/Exact/ImplementationSpecific)
        service_name: Tên service backend
        service_port: Port của service backend
    """
    path: str = "/"
    path_type: str = "Prefix"
    service_name: str = ""
    service_port: int = 80

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "path_type": self.path_type,
            "service_name": self.service_name,
            "service_port": self.service_port,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sIngressPath":
        return cls(
            path=data.get("path", "/"),
            path_type=data.get("path_type", "Prefix"),
            service_name=data.get("service_name", ""),
            service_port=data.get("service_port", 80),
        )


@dataclass
class K8sIngress:
    """Ingress resource trên Kubernetes.

    Đại diện cho external HTTP/HTTPS routing vào cluster,
    bao gồm host, paths, TLS configuration và annotations.

    Attributes:
        id: ID duy nhất của ingress
        name: Tên ingress trong Kubernetes
        host: Hostname (vd: "app.example.com")
        paths: Danh sách path rules
        tls: TLS configuration (secret_name)
        annotations: Ingress annotations (vd: nginx.ingress.kubernetes.io/*)
    """
    id: str
    name: str
    host: str = ""
    paths: list[K8sIngressPath] = field(default_factory=list)
    tls: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển K8sIngress sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "paths": [p.to_dict() for p in self.paths],
            "tls": self.tls,
            "annotations": self.annotations,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sIngress":
        """Tạo K8sIngress từ dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            host=data.get("host", ""),
            paths=[K8sIngressPath.from_dict(p) for p in data.get("paths", [])],
            tls=data.get("tls", {}),
            annotations=data.get("annotations", {}),
        )


# ===========================================================================
# K8sHPA
# ===========================================================================


@dataclass
class K8sHPA:
    """Horizontal Pod Autoscaler resource.

    Tự động scale số lượng pods dựa trên CPU/memory usage metrics.

    Attributes:
        id: ID duy nhất của HPA
        deployment_id: ID của deployment cần scale
        min_replicas: Số replicas tối thiểu
        max_replicas: Số replicas tối đa
        target_cpu: Target CPU usage percentage
        target_memory: Target memory usage percentage
    """
    id: str
    deployment_id: str
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu: int = 70
    target_memory: int = 80

    def to_dict(self) -> dict[str, Any]:
        """Chuyển K8sHPA sang dict."""
        return {
            "id": self.id,
            "deployment_id": self.deployment_id,
            "min_replicas": self.min_replicas,
            "max_replicas": self.max_replicas,
            "target_cpu": self.target_cpu,
            "target_memory": self.target_memory,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sHPA":
        """Tạo K8sHPA từ dict."""
        return cls(
            id=data["id"],
            deployment_id=data["deployment_id"],
            min_replicas=data.get("min_replicas", 1),
            max_replicas=data.get("max_replicas", 10),
            target_cpu=data.get("target_cpu", 70),
            target_memory=data.get("target_memory", 80),
        )


# ===========================================================================
# K8sConfigMap
# ===========================================================================


@dataclass
class K8sConfigMap:
    """ConfigMap resource trên Kubernetes.

    Lưu trữ non-sensitive configuration data dưới dạng key-value pairs,
    có thể được mount vào pod như environment variables hoặc files.

    Attributes:
        id: ID duy nhất của ConfigMap
        name: Tên ConfigMap trong Kubernetes
        data: Key-value pairs cho configuration data
    """
    id: str
    name: str
    data: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển K8sConfigMap sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sConfigMap":
        """Tạo K8sConfigMap từ dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            data=data.get("data", {}),
        )


# ===========================================================================
# K8sSecret
# ===========================================================================


@dataclass
class K8sSecret:
    """Secret resource trên Kubernetes.

    Lưu trữ sensitive data (passwords, tokens, certificates)
    dưới dạng base64-encoded values.

    Attributes:
        id: ID duy nhất của Secret
        name: Tên Secret trong Kubernetes
        secret_type: Loại secret (Opaque/TLS)
        data: Key-value pairs (giá trị đã base64 encode)
    """
    id: str
    name: str
    secret_type: str = "Opaque"
    data: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate secret type."""
        valid_types = {"Opaque", "TLS", "kubernetes.io/service-account-token", "kubernetes.io/dockercfg"}
        if self.secret_type not in valid_types:
            raise ValueError(
                f"Secret type '{self.secret_type}' không hợp lệ. "
                f"Phải là một trong: {', '.join(valid_types)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển K8sSecret sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "secret_type": self.secret_type,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sSecret":
        """Tạo K8sSecret từ dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            secret_type=data.get("secret_type", "Opaque"),
            data=data.get("data", {}),
        )


# ===========================================================================
# K8sPersistentVolume
# ===========================================================================


@dataclass
class K8sPersistentVolume:
    """PersistentVolumeClaim resource trên Kubernetes.

    Đại diện cho yêu cầu storage persistent, bao gồm storage class,
    kích thước, access mode, và mount path.

    Attributes:
        id: ID duy nhất của PVC
        name: Tên PVC trong Kubernetes
        storage_class: Storage class name (vd: "standard", "ssd")
        size_gb: Kích thước storage (GB)
        access_mode: Access mode (ReadWriteOnce/ReadWriteMany/ReadOnlyMany)
        mount_path: Đường dẫn mount trong container
    """
    id: str
    name: str
    storage_class: str = "standard"
    size_gb: int = 1
    access_mode: str = "ReadWriteOnce"
    mount_path: str = "/data"

    def __post_init__(self) -> None:
        """Validate access mode."""
        valid_modes = {"ReadWriteOnce", "ReadOnlyMany", "ReadWriteMany"}
        if self.access_mode not in valid_modes:
            raise ValueError(
                f"Access mode '{self.access_mode}' không hợp lệ. "
                f"Phải là một trong: {', '.join(valid_modes)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển K8sPersistentVolume sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "storage_class": self.storage_class,
            "size_gb": self.size_gb,
            "access_mode": self.access_mode,
            "mount_path": self.mount_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sPersistentVolume":
        """Tạo K8sPersistentVolume từ dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            storage_class=data.get("storage_class", "standard"),
            size_gb=data.get("size_gb", 1),
            access_mode=data.get("access_mode", "ReadWriteOnce"),
            mount_path=data.get("mount_path", "/data"),
        )
