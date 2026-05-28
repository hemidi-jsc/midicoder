# coding: utf-8
"""
Mô-đun parser cho I02 — Kubernetes & Cloud Native Deployment.

Parse DSL dict (từ contract YAML) sang K8sIR — Intermediate Representation
cho Kubernetes resources: deployments, services, ingresses, HPAs,
configmaps, secrets, và persistent volume claims.

Tác giả: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp_infra_kubernetes.models import (
    K8sConfigMap,
    K8sDeployment,
    K8sHPA,
    K8sIngress,
    K8sPersistentVolume,
    K8sSecret,
    K8sService,
)


@dataclass
class K8sIR:
    """Intermediate Representation cho CP54.

    Gom tập tất cả cấu hình Kubernetes từ DSL, bao gồm
    deployments, services, ingresses, HPAs, configmaps,
    secrets, và persistent volume claims.

    Attributes:
        deployments: Danh sách Deployment resources
        services: Danh sách Service resources
        ingresses: Danh sách Ingress resources
        hpas: Danh sách HPA resources
        configmaps: Danh sách ConfigMap resources
        secrets: Danh sách Secret resources
        pvcs: Danh sách PersistentVolumeClaim resources
    """
    deployments: list[K8sDeployment] = field(default_factory=list)
    services: list[K8sService] = field(default_factory=list)
    ingresses: list[K8sIngress] = field(default_factory=list)
    hpas: list[K8sHPA] = field(default_factory=list)
    configmaps: list[K8sConfigMap] = field(default_factory=list)
    secrets: list[K8sSecret] = field(default_factory=list)
    pvcs: list[K8sPersistentVolume] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển K8sIR sang dict."""
        return {
            "deployments": [d.to_dict() for d in self.deployments],
            "services": [s.to_dict() for s in self.services],
            "ingresses": [i.to_dict() for i in self.ingresses],
            "hpas": [h.to_dict() for h in self.hpas],
            "configmaps": [c.to_dict() for c in self.configmaps],
            "secrets": [s.to_dict() for s in self.secrets],
            "pvcs": [p.to_dict() for p in self.pvcs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K8sIR":
        """Tạo K8sIR từ dict."""
        return cls(
            deployments=[K8sDeployment.from_dict(d) for d in data.get("deployments", [])],
            services=[K8sService.from_dict(s) for s in data.get("services", [])],
            ingresses=[K8sIngress.from_dict(i) for i in data.get("ingresses", [])],
            hpas=[K8sHPA.from_dict(h) for h in data.get("hpas", [])],
            configmaps=[K8sConfigMap.from_dict(c) for c in data.get("configmaps", [])],
            secrets=[K8sSecret.from_dict(s) for s in data.get("secrets", [])],
            pvcs=[K8sPersistentVolume.from_dict(p) for p in data.get("pvcs", [])],
        )


def parse_deployments(data: dict[str, Any]) -> list[K8sDeployment]:
    """Parse danh sách deployments từ DSL dict.

    Args:
        data: DSL dict với key 'deployments'

    Returns:
        Danh sách K8sDeployment
    """
    raw = data.get("deployments", [])
    return [K8sDeployment.from_dict(d) for d in raw]


def parse_services(data: dict[str, Any]) -> list[K8sService]:
    """Parse danh sách services từ DSL dict.

    Args:
        data: DSL dict với key 'services'

    Returns:
        Danh sách K8sService
    """
    raw = data.get("services", [])
    return [K8sService.from_dict(s) for s in raw]


def parse_ingresses(data: dict[str, Any]) -> list[K8sIngress]:
    """Parse danh sách ingresses từ DSL dict.

    Args:
        data: DSL dict với key 'ingresses'

    Returns:
        Danh sách K8sIngress
    """
    raw = data.get("ingresses", [])
    return [K8sIngress.from_dict(i) for i in raw]


def parse_hpacs(data: dict[str, Any]) -> list[K8sHPA]:
    """Parse danh sách HPAs từ DSL dict.

    Args:
        data: DSL dict với key 'hpas'

    Returns:
        Danh sách K8sHPA
    """
    raw = data.get("hpas", [])
    return [K8sHPA.from_dict(h) for h in raw]


def parse_configmaps(data: dict[str, Any]) -> list[K8sConfigMap]:
    """Parse danh sách ConfigMaps từ DSL dict.

    Args:
        data: DSL dict với key 'configmaps'

    Returns:
        Danh sách K8sConfigMap
    """
    raw = data.get("configmaps", [])
    return [K8sConfigMap.from_dict(c) for c in raw]


def parse_secrets(data: dict[str, Any]) -> list[K8sSecret]:
    """Parse danh sách Secrets từ DSL dict.

    Args:
        data: DSL dict với key 'secrets'

    Returns:
        Danh sách K8sSecret
    """
    raw = data.get("secrets", [])
    return [K8sSecret.from_dict(s) for s in raw]


def parse_pvcs(data: dict[str, Any]) -> list[K8sPersistentVolume]:
    """Parse danh sách PersistentVolumeClaims từ DSL dict.

    Args:
        data: DSL dict với key 'pvcs'

    Returns:
        Danh sách K8sPersistentVolume
    """
    raw = data.get("pvcs", [])
    return [K8sPersistentVolume.from_dict(p) for p in raw]


def parse_to_ir(data: dict[str, Any]) -> K8sIR:
    """Parse DSL dict thành K8sIR.

    Args:
        data: DSL dict với deployments, services, ingresses, hpas,
              configmaps, secrets, pvcs

    Returns:
        K8sIR gom tập tất cả parsed data
    """
    return K8sIR(
        deployments=parse_deployments(data),
        services=parse_services(data),
        ingresses=parse_ingresses(data),
        hpas=parse_hpacs(data),
        configmaps=parse_configmaps(data),
        secrets=parse_secrets(data),
        pvcs=parse_pvcs(data),
    )


__all__ = [
    "K8sIR",
    "parse_deployments",
    "parse_services",
    "parse_ingresses",
    "parse_hpacs",
    "parse_configmaps",
    "parse_secrets",
    "parse_pvcs",
    "parse_to_ir",
]
