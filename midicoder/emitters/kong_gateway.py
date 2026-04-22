"""
Kong Gateway YAML Emitter.

Module này chứa emitter để generate Kong Gateway configuration từ DSL ProjectionTree.
Support cho:
- Kong Gateway configuration
- Kong Services
- Kong Routes
- Kong Upstreams
- Kong Plugins (rate-limiting, circuit-breaker, v.v.)
- Consul Service Mesh integration
- Consul Health Checks
- Consul Connect proxies

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from midicoder.dsl.projection import ProjectionTree, NodeKind, ProjectionNode


@dataclass
class KongGatewayEmitter:
    """
    Emitter để generate Kong Gateway configuration.
    
    Converter ProjectionTree thành Kong YAML configuration.
    Hỗ trợ cả Kong Gateway và Consul Service Mesh.
    
    Attributes:
        output_dir: Directory để output config files
    """
    
    output_dir: Path = field(default_factory=lambda: Path("./kong"))
    
    def generate(self, tree: ProjectionTree) -> dict[str, Any]:
        """
        Generate Kong Gateway configuration từ ProjectionTree.
        
        Args:
            tree: ProjectionTree chứa Kong Gateway nodes
            
        Returns:
            Configuration dictionary cho Kong Gateway
        """
        config = {
            "gateway": None,
            "services": [],
            "routes": [],
            "upstreams": [],
            "plugins": [],
            "consul": {
                "services": [],
                "health_checks": [],
                "connects": []
            }
        }
        
        # Process tất cả nodes trong tree
        for node in tree.nodes.values():
            kind = node.kind
            
            if kind == NodeKind.KONG_GATEWAY:
                config["gateway"] = self._process_gateway_node(node)
            elif kind == NodeKind.KONG_SERVICE:
                config["services"].append(self._process_service_node(node))
            elif kind == NodeKind.KONG_ROUTE:
                config["routes"].append(self._process_route_node(node))
            elif kind == NodeKind.KONG_UPSTREAM:
                config["upstreams"].append(self._process_upstream_node(node))
            elif kind == NodeKind.KONG_PLUGIN:
                config["plugins"].append(self._process_plugin_node(node))
            elif kind == NodeKind.CONSUL_SERVICE_MESH:
                self._process_consul_service_mesh(node, config["consul"])
            elif kind == NodeKind.CONSUL_SERVICE:
                config["consul"]["services"].append(self._process_consul_service(node))
            elif kind == NodeKind.CONSUL_HEALTH_CHECK:
                config["consul"]["health_checks"].append(self._process_health_check(node))
            elif kind == NodeKind.CONSUL_CONNECT:
                config["consul"]["connects"].append(self._process_connect(node))
        
        return config
    
    def _process_gateway_node(self, node: ProjectionNode) -> dict[str, Any]:
        """
        Process Kong Gateway node.
        
        Args:
            node: Gateway ProjectionNode
            
        Returns:
            Gateway configuration dictionary
        """
        params = node.params or {}
        
        return {
            "name": params.get("name", node.id),
            "listen_port": params.get("listen_port", 8000),
            "ssl": params.get("ssl", False),
            "admin_listen_port": params.get("admin_listen_port", 8001)
        }
    
    def _process_service_node(self, node: ProjectionNode) -> dict[str, Any]:
        """
        Process Kong Service node.
        
        Args:
            node: Service ProjectionNode
            
        Returns:
            Service configuration dictionary
        """
        params = node.params or {}
        
        return {
            "name": params.get("name", node.id),
            "url": params.get("url", "http://localhost:3000"),
            "protocol": params.get("protocol", "http"),
            "port": params.get("port", 3000),
            "host": params.get("host", "localhost"),
            "connect_timeout": params.get("connect_timeout", 60000),
            "write_timeout": params.get("write_timeout", 60000),
            "read_timeout": params.get("read_timeout", 60000)
        }
    
    def _process_route_node(self, node: ProjectionNode) -> dict[str, Any]:
        """
        Process Kong Route node.
        
        Args:
            node: Route ProjectionNode
            
        Returns:
            Route configuration dictionary
        """
        params = node.params or {}
        
        return {
            "name": params.get("name", node.id),
            "paths": params.get("paths", []),
            "methods": params.get("methods", ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]),
            "service": params.get("service"),
            "strip_path": params.get("strip_path", True),
            "preserve_host": params.get("preserve_host", False),
            "hosts": params.get("hosts", []),
            "headers": params.get("headers", {})
        }
    
    def _process_upstream_node(self, node: ProjectionNode) -> dict[str, Any]:
        """
        Process Kong Upstream node.
        
        Args:
            node: Upstream ProjectionNode
            
        Returns:
            Upstream configuration dictionary
        """
        params = node.params or {}
        
        return {
            "name": params.get("name", node.id),
            "algorithm": params.get("algorithm", "round-robin"),
            "hash_fallback": params.get("hash_fallback", "round-robin"),
            "slots": params.get("slots", 10000),
            "targets": params.get("targets", []),
            "healthchecks": params.get("healthchecks", {})
        }
    
    def _process_plugin_node(self, node: ProjectionNode) -> dict[str, Any]:
        """
        Process Kong Plugin node.
        
        Args:
            node: Plugin ProjectionNode
            
        Returns:
            Plugin configuration dictionary
        """
        params = node.params or {}
        
        plugin_config = {
            "name": params.get("name", node.id.replace("-plugin", "")),
            "config": params.get("config", {})
        }
        
        # Add optional associations
        if params.get("service"):
            plugin_config["service"] = params["service"]
        if params.get("route"):
            plugin_config["route"] = params["route"]
        if params.get("consumer"):
            plugin_config["consumer"] = params["consumer"]
        
        return plugin_config
    
    def _process_consul_service_mesh(self, node: ProjectionNode, consul_config: dict) -> None:
        """
        Process Consul Service Mesh node.
        
        Args:
            node: Service Mesh ProjectionNode
            consul_config: Consul configuration dictionary để update
        """
        params = node.params or {}
        
        if "mesh" not in consul_config:
            consul_config["mesh"] = {
                "name": params.get("name", node.id),
                "datacenter": params.get("datacenter", "dc1"),
                "protocol": params.get("protocol", "http")
            }
    
    def _process_consul_service(self, node: ProjectionNode) -> dict[str, Any]:
        """
        Process Consul Service node.
        
        Args:
            node: Service ProjectionNode
            
        Returns:
            Consul service configuration dictionary
        """
        params = node.params or {}
        
        service_config = {
            "name": params.get("name", node.id),
            "port": params.get("port", 80),
            "address": params.get("address", "localhost"),
            "tags": params.get("tags", []),
            "meta": params.get("meta", {})
        }
        
        # Add optional fields
        if params.get("id"):
            service_config["id"] = params["id"]
        if params.get("weight"):
            service_config["weight"] = params["weight"]
        if params.get("address"):
            service_config["address"] = params["address"]
        
        return service_config
    
    def _process_health_check(self, node: ProjectionNode) -> dict[str, Any]:
        """
        Process Consul Health Check node.
        
        Args:
            node: Health Check ProjectionNode
            
        Returns:
            Health check configuration dictionary
        """
        params = node.params or {}
        
        health_check = {
            "id": params.get("id", node.id),
            "service": params.get("service"),
            "interval": params.get("interval", "10s"),
            "timeout": params.get("timeout", "5s")
        }
        
        # HTTP check
        if params.get("http"):
            health_check["http"] = params["http"]
        
        # TCP check
        if params.get("tcp"):
            health_check["tcp"] = params["tcp"]
        
        # Exec check
        if params.get("exec"):
            health_check["exec"] = params["exec"]
        
        # TTL check
        if params.get("ttl"):
            health_check["ttl"] = params["ttl"]
        
        # Optional fields
        if params.get("deregister_critical_service_after"):
            health_check["deregister_critical_service_after"] = params["deregister_critical_service_after"]
        if params.get("notes"):
            health_check["notes"] = params["notes"]
        if params.get("tags"):
            health_check["tags"] = params["tags"]
        
        return health_check
    
    def _process_connect(self, node: ProjectionNode) -> dict[str, Any]:
        """
        Process Consul Connect node.
        
        Args:
            node: Connect ProjectionNode
            
        Returns:
            Connect proxy configuration dictionary
        """
        params = node.params or {}
        
        return {
            "service": params.get("service"),
            "proxy": params.get("proxy", {})
        }
    
    def to_yaml(self, tree: ProjectionTree) -> str:
        """
        Convert ProjectionTree thành YAML string.
        
        Args:
            tree: ProjectionTree để convert
            
        Returns:
            YAML string của configuration
        """
        config = self.generate(tree)
        
        # Sử dụng yaml.dump với sort_keys=False để giữ thứ tự
        return yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    def save(self, tree: ProjectionTree, output_path: Path) -> None:
        """
        Save configuration ra file.
        
        Args:
            tree: ProjectionTree để generate
            output_path: Path của file output
        """
        yaml_content = self.to_yaml(tree)
        
        # Tạo directory nếu chưa tồn tại
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        output_path.write_text(yaml_content, encoding="utf-8")
    
    def save_consul_hcl(self, tree: ProjectionTree, output_path: Path) -> None:
        """
        Save Consul configuration dưới dạng HCL.
        
        Args:
            tree: ProjectionTree để generate
            output_path: Path của file output
        """
        config = self.generate(tree)
        consul_config = config.get("consul", {})
        
        hcl_content = self._render_consul_hcl(consul_config)
        
        # Tạo directory nếu chưa tồn tại
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        output_path.write_text(hcl_content, encoding="utf-8")
    
    def _render_consul_hcl(self, consul_config: dict[str, Any]) -> str:
        """
        Render Consul configuration thành HCL string.
        
        Args:
            consul_config: Consul configuration dictionary
            
        Returns:
            HCL string
        """
        lines = []
        
        # Services
        if consul_config.get("services"):
            lines.append("# Consul Services")
            for service in consul_config["services"]:
                lines.append(f'service "{{ service["name"] }}" {{')
                lines.append(f'  port = {service.get("port", 80)}')
                if service.get("address"):
                    lines.append(f'  address = "{service["address"]}"')
                if service.get("id"):
                    lines.append(f'  id = "{service["id"]}"')
                if service.get("tags"):
                    tags = ", ".join(f'"{t}"' for t in service["tags"])
                    lines.append(f'  tags = [{tags}]')
                lines.append("}")
                lines.append("")
        
        # Health Checks
        if consul_config.get("health_checks"):
            lines.append("# Health Checks")
            for check in consul_config["health_checks"]:
                lines.append("check {")
                lines.append(f'  id = "{check.get("id", "check")}"')
                lines.append(f'  name = "{check.get("name", "health")}"')
                lines.append(f'  service = "{check.get("service", "service")}"')
                lines.append(f'  interval = "{check.get("interval", "10s")}"')
                lines.append(f'  timeout = "{check.get("timeout", "5s")}"')
                if check.get("http"):
                    lines.append(f'  http = "{check["http"]}"')
                lines.append("}")
                lines.append("")
        
        # Connects
        if consul_config.get("connects"):
            lines.append("# Connect Proxies")
            for connect in consul_config["connects"]:
                lines.append(f'connect "{{ connect["service"] }}" {{')
                if connect.get("proxy"):
                    proxy = connect["proxy"]
                    if proxy.get("upstreams"):
                        lines.append("  upstreams {")
                        for upstream in proxy["upstreams"]:
                            lines.append(f'    destination_name = "{upstream.get("destination_name")}"')
                            lines.append(f'    local_bind_port = {upstream.get("local_bind_port", 0)}')
                        lines.append("  }")
                lines.append("}")
                lines.append("")
        
        return "\n".join(lines)