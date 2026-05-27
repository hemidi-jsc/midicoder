# coding: utf-8
"""
Mô-đun recipes cho CP60 — Service Discovery & Config Center.

Cung cấp các recipe để build ServiceDiscoveryIR cho các use case phổ biến:
- consul_service_discovery_recipe: Consul-based với health checks
- config_center_recipe: Centralized config với environment override
- dynamic_config_recipe: Runtime config updates với watchers
- load_balancing_recipe: Service load balancing với health checks

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp60_service_discovery.parser import (
    ServiceDiscoveryIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: ServiceDiscoveryIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: ServiceDiscoveryIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def consul_service_discovery_recipe() -> RecipeOutput:
    """Recipe: Consul-based service discovery với health checks.

    - Consul registry với 3 peer nodes
    - 2 service instances cho "order-service"
    - Health check path mặc định
    - Session TTL 30 giây

    Returns:
        RecipeOutput chứa ServiceDiscoveryIR
    """
    data = {
        "registries": [
            {
                "registry_id": "consul_primary",
                "name": "Primary Consul Cluster",
                "provider": "consul",
                "quorum_size": 3,
                "session_ttl": 30,
                "peer_nodes": [
                    "consul-1.internal:8500",
                    "consul-2.internal:8500",
                    "consul-3.internal:8500",
                ],
            }
        ],
        "instances": [
            {
                "instance_id": "order-svc-001",
                "service_name": "order-service",
                "host": "10.0.1.10",
                "port": 8080,
                "protocol": "http",
                "health_check_path": "/health",
                "metadata": {"version": "1.2.0", "region": "ap-southeast-1"},
                "tags": ["production", "order"],
            },
            {
                "instance_id": "order-svc-002",
                "service_name": "order-service",
                "host": "10.0.1.11",
                "port": 8080,
                "protocol": "http",
                "health_check_path": "/health",
                "metadata": {"version": "1.2.0", "region": "ap-southeast-1"},
                "tags": ["production", "order"],
            },
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="consul_service_discovery_recipe",
        description="Service discovery qua Consul với health checks cho order-service",
        ir=ir,
        raw_data=data,
    )


def config_center_recipe() -> RecipeOutput:
    """Recipe: Centralized config với environment override.

    - Config entries cho database, cache, và rate limit
    - Mỗi entry có environment-specific (dev, staging, prod)
    - Các giá trị nhạy cảm được encrypted

    Returns:
        RecipeOutput chứa ServiceDiscoveryIR
    """
    data = {
        "configs": [
            {
                "entry_id": "cfg_db_url",
                "key": "database.url",
                "value": "postgres://devhost:5432/appdb",
                "environment": "dev",
                "encrypted": False,
                "version": 1,
            },
            {
                "entry_id": "cfg_db_url_staging",
                "key": "database.url",
                "value": "postgres://staging-host:5432/appdb",
                "environment": "staging",
                "encrypted": False,
                "version": 1,
            },
            {
                "entry_id": "cfg_db_url_prod",
                "key": "database.url",
                "value": "postgres://prod-host:5432/appdb",
                "environment": "prod",
                "encrypted": True,
                "version": 2,
            },
            {
                "entry_id": "cfg_db_password",
                "key": "database.password",
                "value": "enc:AES256:xxxxx",
                "environment": "prod",
                "encrypted": True,
                "version": 1,
            },
            {
                "entry_id": "cfg_cache_url",
                "key": "cache.url",
                "value": "redis://devhost:6379",
                "environment": "dev",
                "encrypted": False,
                "version": 1,
            },
            {
                "entry_id": "cfg_rate_limit",
                "key": "rate_limit.requests_per_minute",
                "value": "1000",
                "environment": "prod",
                "encrypted": False,
                "version": 3,
            },
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="config_center_recipe",
        description="Config center tập trung với environment override và encryption",
        ir=ir,
        raw_data=data,
    )


def dynamic_config_recipe() -> RecipeOutput:
    """Recipe: Runtime config updates với watchers.

    - Config entries cho feature flags và threshold
    - Config watchers với callback URLs
    - Polling interval 15 giây
    - Trigger on change enabled

    Returns:
        RecipeOutput chứa ServiceDiscoveryIR
    """
    data = {
        "configs": [
            {
                "entry_id": "cfg_feature_dark_mode",
                "key": "feature.dark_mode_enabled",
                "value": "true",
                "environment": "prod",
                "encrypted": False,
                "version": 1,
                "watchers": ["watch-dark-mode"],
            },
            {
                "entry_id": "cfg_threshold_cpu",
                "key": "threshold.cpu_warning_percent",
                "value": "80",
                "environment": "prod",
                "encrypted": False,
                "version": 2,
                "watchers": ["watch-cpu-threshold"],
            },
            {
                "entry_id": "cfg_log_level",
                "key": "logging.level",
                "value": "INFO",
                "environment": "prod",
                "encrypted": False,
                "version": 1,
                "watchers": ["watch-log-level"],
            },
        ],
        "watches": [
            {
                "watch_id": "watch-dark-mode",
                "config_key": "feature.dark_mode_enabled",
                "callback_url": "http://frontend-service:3000/api/config/reload",
                "polling_interval_seconds": 15,
                "trigger_on_change": True,
            },
            {
                "watch_id": "watch-cpu-threshold",
                "config_key": "threshold.cpu_warning_percent",
                "callback_url": "http://monitoring-service:9090/api/threshold/update",
                "polling_interval_seconds": 10,
                "trigger_on_change": True,
            },
            {
                "watch_id": "watch-log-level",
                "config_key": "logging.level",
                "callback_url": "http://config-reloader:8080/api/reload-logging",
                "polling_interval_seconds": 30,
                "trigger_on_change": True,
            },
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="dynamic_config_recipe",
        description="Runtime config updates với watcher callbacks cho feature flags và thresholds",
        ir=ir,
        raw_data=data,
    )


def load_balancing_recipe() -> RecipeOutput:
    """Recipe: Service load balancing với health checks.

    - Multiple service instances
    - Load balancing với round-robin và least-connections
    - Health check interval 15 giây
    - Max retries 3

    Returns:
        RecipeOutput chứa ServiceDiscoveryIR
    """
    data = {
        "instances": [
            {
                "instance_id": "user-svc-001",
                "service_name": "user-service",
                "host": "10.0.2.10",
                "port": 8081,
                "protocol": "http",
                "health_check_path": "/health",
                "metadata": {"version": "2.0.1", "weight": "10"},
                "tags": ["production", "user"],
            },
            {
                "instance_id": "user-svc-002",
                "service_name": "user-service",
                "host": "10.0.2.11",
                "port": 8081,
                "protocol": "http",
                "health_check_path": "/health",
                "metadata": {"version": "2.0.1", "weight": "10"},
                "tags": ["production", "user"],
            },
            {
                "instance_id": "user-svc-003",
                "service_name": "user-service",
                "host": "10.0.2.12",
                "port": 8081,
                "protocol": "grpc",
                "health_check_path": "/grpc.health.v1.Health/Check",
                "metadata": {"version": "2.0.1", "weight": "5"},
                "tags": ["production", "user", "grpc"],
            },
            {
                "instance_id": "payment-svc-001",
                "service_name": "payment-service",
                "host": "10.0.3.10",
                "port": 8443,
                "protocol": "https",
                "health_check_path": "/health",
                "metadata": {"version": "1.5.0", "region": "ap-southeast-1"},
                "tags": ["production", "payment"],
            },
            {
                "instance_id": "payment-svc-002",
                "service_name": "payment-service",
                "host": "10.0.3.11",
                "port": 8443,
                "protocol": "https",
                "health_check_path": "/health",
                "metadata": {"version": "1.5.0", "region": "ap-southeast-1"},
                "tags": ["production", "payment"],
            },
        ],
        "load_balancers": [
            {
                "config_id": "lb-user",
                "service_name": "user-service",
                "strategy": "round_robin",
                "health_check_interval": 15,
                "max_retries": 3,
            },
            {
                "config_id": "lb-payment",
                "service_name": "payment-service",
                "strategy": "least_connections",
                "health_check_interval": 10,
                "max_retries": 5,
            },
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="load_balancing_recipe",
        description="Service load balancing với health checks — round_robin cho user, least_connections cho payment",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "consul_service_discovery_recipe",
    "config_center_recipe",
    "dynamic_config_recipe",
    "load_balancing_recipe",
]
