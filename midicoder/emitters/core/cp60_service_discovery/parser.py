# coding: utf-8
"""
Mô-đun parser cho CP60 — Service Discovery & Config Center.

Parse DSL dict (từ contract YAML) sang ServiceDiscoveryIR — Intermediate Representation
cho service instances, registries, config entries, watches, và load balancing.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp60_service_discovery.models import (
    ConfigEntry,
    ConfigWatch,
    LoadBalancingConfig,
    ServiceInstance,
    ServiceRegistry,
)


@dataclass
class ServiceDiscoveryIR:
    """Intermediate Representation cho CP60.

    Gom tập tất cả cấu hình service discovery và config center từ DSL,
    bao gồm service instances, registry configs, config entries,
    config watches, và load balancing rules.

    Attributes:
        instances: Danh sách service instances
        registries: Danh sách service registries
        configs: Danh sách config entries
        watches: Danh sách config watches
        load_balancers: Danh sách load balancing configs
    """
    instances: list[ServiceInstance] = field(default_factory=list)
    registries: list[ServiceRegistry] = field(default_factory=list)
    configs: list[ConfigEntry] = field(default_factory=list)
    watches: list[ConfigWatch] = field(default_factory=list)
    load_balancers: list[LoadBalancingConfig] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ServiceDiscoveryIR sang dict."""
        return {
            "instances": [i.to_dict() for i in self.instances],
            "registries": [r.to_dict() for r in self.registries],
            "configs": [c.to_dict() for c in self.configs],
            "watches": [w.to_dict() for w in self.watches],
            "load_balancers": [lb.to_dict() for lb in self.load_balancers],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceDiscoveryIR":
        """Tạo ServiceDiscoveryIR từ dict."""
        instances = [ServiceInstance.from_dict(i) for i in data.get("instances", [])]
        registries = [ServiceRegistry.from_dict(r) for r in data.get("registries", [])]
        configs = [ConfigEntry.from_dict(c) for c in data.get("configs", [])]
        watches = [ConfigWatch.from_dict(w) for w in data.get("watches", [])]
        load_balancers = [LoadBalancingConfig.from_dict(lb) for lb in data.get("load_balancers", [])]
        return cls(
            instances=instances,
            registries=registries,
            configs=configs,
            watches=watches,
            load_balancers=load_balancers,
        )


def parse_instances(data: dict[str, Any]) -> list[ServiceInstance]:
    """Parse danh sách service instances từ DSL dict.

    Args:
        data: DSL dict với key 'instances' hoặc 'service_instances'

    Returns:
        Danh sách ServiceInstance
    """
    raw = data.get("instances", data.get("service_instances", []))
    instances = []
    for inst_data in raw:
        instances.append(ServiceInstance(
            instance_id=inst_data.get("instance_id", inst_data.get("id", "")),
            service_name=inst_data.get("service_name", inst_data.get("name", "")),
            host=inst_data.get("host", ""),
            port=inst_data.get("port", 8080),
            protocol=inst_data.get("protocol", "http"),
            metadata=inst_data.get("metadata", {}),
            health_check_path=inst_data.get("health_check_path", "/health"),
            tags=inst_data.get("tags", []),
        ))
    return instances


def parse_registries(data: dict[str, Any]) -> list[ServiceRegistry]:
    """Parse danh sách service registries từ DSL dict.

    Args:
        data: DSL dict với key 'registries' hoặc 'service_registries'

    Returns:
        Danh sách ServiceRegistry
    """
    raw = data.get("registries", data.get("service_registries", []))
    registries = []
    for reg_data in raw:
        registries.append(ServiceRegistry(
            registry_id=reg_data.get("registry_id", reg_data.get("id", "")),
            name=reg_data.get("name", ""),
            provider=reg_data.get("provider", "consul"),
            quorum_size=reg_data.get("quorum_size", 3),
            session_ttl=reg_data.get("session_ttl", 30),
            peer_nodes=reg_data.get("peer_nodes", []),
            metadata=reg_data.get("metadata", {}),
        ))
    return registries


def parse_configs(data: dict[str, Any]) -> list[ConfigEntry]:
    """Parse danh sách config entries từ DSL dict.

    Args:
        data: DSL dict với key 'configs' hoặc 'config_entries'

    Returns:
        Danh sách ConfigEntry
    """
    raw = data.get("configs", data.get("config_entries", []))
    configs = []
    for c_data in raw:
        configs.append(ConfigEntry(
            entry_id=c_data.get("entry_id", c_data.get("id", "")),
            key=c_data.get("key", ""),
            value=c_data.get("value", ""),
            environment=c_data.get("environment", "dev"),
            encrypted=c_data.get("encrypted", False),
            version=c_data.get("version", 1),
            watchers=c_data.get("watchers", []),
            metadata=c_data.get("metadata", {}),
        ))
    return configs


def parse_watches(data: dict[str, Any]) -> list[ConfigWatch]:
    """Parse danh sách config watches từ DSL dict.

    Args:
        data: DSL dict với key 'watches' hoặc 'config_watches'

    Returns:
        Danh sách ConfigWatch
    """
    raw = data.get("watches", data.get("config_watches", []))
    watches = []
    for w_data in raw:
        watches.append(ConfigWatch(
            watch_id=w_data.get("watch_id", w_data.get("id", "")),
            config_key=w_data.get("config_key", ""),
            callback_url=w_data.get("callback_url", ""),
            polling_interval_seconds=w_data.get("polling_interval_seconds", 30),
            trigger_on_change=w_data.get("trigger_on_change", True),
            metadata=w_data.get("metadata", {}),
        ))
    return watches


def parse_load_balancers(data: dict[str, Any]) -> list[LoadBalancingConfig]:
    """Parse danh sách load balancing configs từ DSL dict.

    Args:
        data: DSL dict với key 'load_balancers' hoặc 'load_balancing'

    Returns:
        Danh sách LoadBalancingConfig
    """
    raw = data.get("load_balancers", data.get("load_balancing", []))
    lbs = []
    for lb_data in raw:
        lbs.append(LoadBalancingConfig(
            config_id=lb_data.get("config_id", lb_data.get("id", "")),
            service_name=lb_data.get("service_name", ""),
            strategy=lb_data.get("strategy", "round_robin"),
            health_check_interval=lb_data.get("health_check_interval", 15),
            max_retries=lb_data.get("max_retries", 3),
            metadata=lb_data.get("metadata", {}),
        ))
    return lbs


def parse_to_ir(data: dict[str, Any]) -> ServiceDiscoveryIR:
    """Parse DSL dict thành ServiceDiscoveryIR.

    Args:
        data: DSL dict với instances, registries, configs, watches, load_balancers

    Returns:
        ServiceDiscoveryIR gom tập tất cả parsed data
    """
    return ServiceDiscoveryIR(
        instances=parse_instances(data),
        registries=parse_registries(data),
        configs=parse_configs(data),
        watches=parse_watches(data),
        load_balancers=parse_load_balancers(data),
    )


__all__ = [
    "ServiceDiscoveryIR",
    "parse_instances",
    "parse_registries",
    "parse_configs",
    "parse_watches",
    "parse_load_balancers",
    "parse_to_ir",
]
