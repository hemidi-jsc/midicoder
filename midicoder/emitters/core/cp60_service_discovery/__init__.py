# coding: utf-8
"""
CP60: Service Discovery & Config Center.

Re-exports các models, parser, và recipes cho external consumers.
"""

from midicoder.emitters.core.cp60_service_discovery.models import (
    ConfigEntry,
    ConfigWatch,
    LoadBalancingConfig,
    ServiceInstance,
    ServiceRegistry,
)
from midicoder.emitters.core.cp60_service_discovery.parser import (
    ServiceDiscoveryIR,
    parse_to_ir,
)
from midicoder.emitters.core.cp60_service_discovery.recipes import (
    RecipeOutput,
    config_center_recipe,
    consul_service_discovery_recipe,
    dynamic_config_recipe,
    load_balancing_recipe,
)

__all__ = [
    # Models
    "ServiceInstance",
    "ServiceRegistry",
    "ConfigEntry",
    "ConfigWatch",
    "LoadBalancingConfig",
    # Parser
    "ServiceDiscoveryIR",
    "parse_to_ir",
    # Recipes
    "RecipeOutput",
    "consul_service_discovery_recipe",
    "config_center_recipe",
    "dynamic_config_recipe",
    "load_balancing_recipe",
]
