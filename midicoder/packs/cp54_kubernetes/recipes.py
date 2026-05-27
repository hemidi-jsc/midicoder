# coding: utf-8
"""
Mô-đun recipes cho CP54 — Kubernetes & Cloud Native Deployment.

Cung cấp các recipe để build K8sIR cho các use case phổ biến:
- basic_deployment_recipe: Deployment đơn giản + ClusterIP Service
- full_stack_recipe: Deployment + HPA + Ingress + Service + ConfigMap
- helm_chart_recipe: Full stack + Secret + PVC

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp54_kubernetes.parser import (
    K8sIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: K8sIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: K8sIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def basic_deployment_recipe() -> RecipeOutput:
    """Recipe: Deployment đơn giản + ClusterIP Service.

    - 1 deployment (1 replica, image mặc định)
    - 1 ClusterIP service

    Returns:
        RecipeOutput chứa K8sIR
    """
    data = {
        "deployments": [
            {
                "id": "app-deployment",
                "name": "app",
                "replicas": 1,
                "image": "myapp:latest",
                "ports": [
                    {"container_port": 8000, "protocol": "TCP", "name": "http"}
                ],
                "resources": {"cpu": "250m", "memory": "256Mi"},
                "strategy": "RollingUpdate",
                "labels": {"app": "myapp"},
                "env": [],
                "volume_mounts": [],
            }
        ],
        "services": [
            {
                "id": "app-service",
                "name": "app",
                "type": "ClusterIP",
                "ports": [
                    {"container_port": 80, "protocol": "TCP", "name": "http"}
                ],
                "selector": {"app": "myapp"},
            }
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="basic_deployment_recipe",
        description="Deployment đơn giản — 1 replica + ClusterIP Service",
        ir=ir,
        raw_data=data,
    )


def full_stack_recipe() -> RecipeOutput:
    """Recipe: Full stack — Deployment + HPA + Ingress + Service + ConfigMap.

    - 1 deployment (2 replicas)
    - 1 LoadBalancer service
    - 1 HPA (min=2, max=10)
    - 1 Ingress (host + path)
    - 1 ConfigMap (app config)

    Returns:
        RecipeOutput chứa K8sIR
    """
    data = {
        "deployments": [
            {
                "id": "app-deployment",
                "name": "app",
                "replicas": 2,
                "image": "myapp:latest",
                "ports": [
                    {"container_port": 8000, "protocol": "TCP", "name": "http"}
                ],
                "resources": {"cpu": "500m", "memory": "512Mi"},
                "strategy": "RollingUpdate",
                "labels": {"app": "myapp"},
                "env": [
                    {
                        "name": "APP_ENV",
                        "value_from": {
                            "config_map_key_ref": {
                                "name": "app-config",
                                "key": "APP_ENV",
                            }
                        }
                    }
                ],
                "volume_mounts": [],
            }
        ],
        "services": [
            {
                "id": "app-service",
                "name": "app",
                "type": "LoadBalancer",
                "ports": [
                    {"container_port": 80, "protocol": "TCP", "name": "http"}
                ],
                "selector": {"app": "myapp"},
            }
        ],
        "ingresses": [
            {
                "id": "app-ingress",
                "name": "app",
                "host": "app.example.com",
                "paths": [
                    {
                        "path": "/",
                        "path_type": "Prefix",
                        "service_name": "app",
                        "service_port": 80,
                    }
                ],
                "tls": {"secret_name": "app-tls"},
                "annotations": {
                    "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                },
            }
        ],
        "hpas": [
            {
                "id": "app-hpa",
                "deployment_id": "app-deployment",
                "min_replicas": 2,
                "max_replicas": 10,
                "target_cpu": 70,
                "target_memory": 80,
            }
        ],
        "configmaps": [
            {
                "id": "app-config",
                "name": "app-config",
                "data": {
                    "APP_ENV": "production",
                    "LOG_LEVEL": "info",
                },
            }
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="full_stack_recipe",
        description="Full stack — Deployment + HPA + Ingress + Service + ConfigMap",
        ir=ir,
        raw_data=data,
    )


def helm_chart_recipe() -> RecipeOutput:
    """Recipe: Helm chart — Full stack + Secret + PVC.

    - 1 deployment (3 replicas)
    - 1 LoadBalancer service
    - 1 HPA (min=3, max=20)
    - 1 Ingress (host + path + TLS)
    - 1 ConfigMap (app config)
    - 1 Secret (database credentials)
    - 1 PersistentVolumeClaim (data storage)

    Returns:
        RecipeOutput chứa K8sIR
    """
    data = {
        "deployments": [
            {
                "id": "app-deployment",
                "name": "app",
                "replicas": 3,
                "image": "myapp:latest",
                "ports": [
                    {"container_port": 8000, "protocol": "TCP", "name": "http"}
                ],
                "resources": {"cpu": "1", "memory": "1Gi"},
                "strategy": "RollingUpdate",
                "labels": {"app": "myapp"},
                "env": [
                    {
                        "name": "DB_PASSWORD",
                        "value_from": {
                            "secret_key_ref": {
                                "name": "db-credentials",
                                "key": "password",
                            }
                        }
                    }
                ],
                "volume_mounts": [
                    {
                        "name": "data-volume",
                        "mount_path": "/app/data",
                        "read_only": False,
                    }
                ],
            }
        ],
        "services": [
            {
                "id": "app-service",
                "name": "app",
                "type": "LoadBalancer",
                "ports": [
                    {"container_port": 80, "protocol": "TCP", "name": "http"}
                ],
                "selector": {"app": "myapp"},
            }
        ],
        "ingresses": [
            {
                "id": "app-ingress",
                "name": "app",
                "host": "app.example.com",
                "paths": [
                    {
                        "path": "/",
                        "path_type": "Prefix",
                        "service_name": "app",
                        "service_port": 80,
                    }
                ],
                "tls": {"secret_name": "app-tls"},
                "annotations": {
                    "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                    "nginx.ingress.kubernetes.io/proxy-body-size": "50m",
                },
            }
        ],
        "hpas": [
            {
                "id": "app-hpa",
                "deployment_id": "app-deployment",
                "min_replicas": 3,
                "max_replicas": 20,
                "target_cpu": 70,
                "target_memory": 80,
            }
        ],
        "configmaps": [
            {
                "id": "app-config",
                "name": "app-config",
                "data": {
                    "APP_ENV": "production",
                    "LOG_LEVEL": "info",
                    "DB_HOST": "postgres-service",
                },
            }
        ],
        "secrets": [
            {
                "id": "db-credentials",
                "name": "db-credentials",
                "secret_type": "Opaque",
                "data": {
                    "username": "YWRtaW4=",  # base64: admin
                    "password": "cGFzc3dvcmQ=",  # base64: password
                },
            }
        ],
        "pvcs": [
            {
                "id": "data-pvc",
                "name": "data-pvc",
                "storage_class": "standard",
                "size_gb": 10,
                "access_mode": "ReadWriteOnce",
                "mount_path": "/app/data",
            }
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="helm_chart_recipe",
        description="Helm chart — Full stack + Secret + PVC",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "basic_deployment_recipe",
    "full_stack_recipe",
    "helm_chart_recipe",
]
