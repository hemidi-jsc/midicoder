"""
Test suite cho Kong Gateway YAML emitter.

Test coverage cho:
- KongGatewayEmitter class
- Generate Kong YAML configuration
- Gateway, Services, Routes, Upstreams, Plugins
- Consul service mesh integration

Tổng cộng: 15+ tests

Mục tiêu coverage: >80%
"""

from unittest import TestCase
from pathlib import Path

from midicoder.dsl.projection import ProjectionTree, NodeKind, ProjectionNode
from midicoder.packs.cp_full_api_gateway.kong_gateway import KongGatewayEmitter


class TestKongGatewayEmitter(TestCase):
    """Test Kong Gateway YAML emitter."""

    def setUp(self):
        """Thiết lập test fixtures trước mỗi test."""
        self.emitter = KongGatewayEmitter()

    def test_emitter_initialization(self):
        """Test emitter khởi tạo thành công."""
        self.assertIsNotNone(self.emitter)

    def test_generate_empty_tree(self):
        """Test generate với tree rỗng."""
        tree = ProjectionTree()
        result = self.emitter.generate(tree)
        
        # Kết quả nên có cấu trúc cơ bản
        self.assertIn("services", result)
        self.assertIsInstance(result["services"], list)
        self.assertEqual(len(result["services"]), 0)

    def test_generate_gateway_node(self):
        """Test generate từ Kong gateway node."""
        tree = ProjectionTree()
        
        # Thêm gateway node - required fields: id, version
        gateway = ProjectionNode(
            id="api-gateway",
            kind=NodeKind.KONG_GATEWAY,
            params={
                "id": "api-gateway",
                "version": "3.0",
                "listen_port": 8000,
                "ssl": False,
                "name": "api-gateway"
            }
        )
        tree.add_node(gateway)
        
        result = self.emitter.generate(tree)
        
        # Verify gateway config
        self.assertIn("gateway", result)
        self.assertEqual(result["gateway"]["name"], "api-gateway")
        self.assertEqual(result["gateway"]["listen_port"], 8000)

    def test_generate_service_node(self):
        """Test generate từ Kong service node."""
        tree = ProjectionTree()
        
        # Thêm service node - required fields: id, name, protocol, host, port
        service = ProjectionNode(
            id="user-service",
            kind=NodeKind.KONG_SERVICE,
            params={
                "id": "user-service",
                "name": "user-service",
                "protocol": "http",
                "host": "user-service",
                "port": 3000,
                "url": "http://user-service:3000"
            }
        )
        tree.add_node(service)
        
        result = self.emitter.generate(tree)
        
        # Verify service
        self.assertIn("services", result)
        services = result["services"]
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]["name"], "user-service")
        self.assertEqual(services[0]["url"], "http://user-service:3000")

    def test_generate_route_node(self):
        """Test generate từ Kong route node."""
        tree = ProjectionTree()
        
        # Thêm route node - required fields: id, name, paths
        route = ProjectionNode(
            id="user-route",
            kind=NodeKind.KONG_ROUTE,
            params={
                "id": "user-route",
                "name": "user-route",
                "paths": ["/users"],
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "service": "user-service"
            }
        )
        tree.add_node(route)
        
        result = self.emitter.generate(tree)
        
        # Verify route
        self.assertIn("routes", result)
        routes = result["routes"]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["name"], "user-route")
        self.assertIn("/users", routes[0]["paths"])

    def test_generate_upstream_node(self):
        """Test generate từ Kong upstream node."""
        tree = ProjectionTree()
        
        # Thêm upstream node - required fields: id, name, type
        upstream = ProjectionNode(
            id="user-upstream",
            kind=NodeKind.KONG_UPSTREAM,
            params={
                "id": "user-upstream",
                "name": "user-upstream",
                "type": "round-robin",
                "algorithm": "round-robin",
                "hash_fallback": "round-robin",
                "slots": 10000,
                "targets": [
                    {"target": "user-service-1:3000", "weight": 100},
                    {"target": "user-service-2:3000", "weight": 100}
                ]
            }
        )
        tree.add_node(upstream)
        
        result = self.emitter.generate(tree)
        
        # Verify upstream
        self.assertIn("upstreams", result)
        upstreams = result["upstreams"]
        self.assertEqual(len(upstreams), 1)
        self.assertEqual(upstreams[0]["name"], "user-upstream")
        self.assertEqual(upstreams[0]["algorithm"], "round-robin")

    def test_generate_plugin_node(self):
        """Test generate từ Kong plugin node."""
        tree = ProjectionTree()
        
        # Thêm plugin node - required fields: id, name
        plugin = ProjectionNode(
            id="rate-limiting-plugin",
            kind=NodeKind.KONG_PLUGIN,
            params={
                "id": "rate-limiting",
                "name": "rate-limiting",
                "service": "user-service",
                "config": {
                    "second": 100,
                    "minute": 1000,
                    "hour": 10000,
                    "day": 100000,
                    "month": 1000000
                }
            }
        )
        tree.add_node(plugin)
        
        result = self.emitter.generate(tree)
        
        # Verify plugin
        self.assertIn("plugins", result)
        plugins = result["plugins"]
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0]["name"], "rate-limiting")

    def test_generate_circuit_breaker_plugin(self):
        """Test generate circuit breaker plugin."""
        tree = ProjectionTree()
        
        # Thêm circuit breaker plugin - required fields: id, name
        plugin = ProjectionNode(
            id="circuit-breaker-plugin",
            kind=NodeKind.KONG_PLUGIN,
            params={
                "id": "circuit-breaker",
                "name": "circuit-breaker",
                "service": "user-service",
                "config": {
                    "healthy": {
                        "http_failures": 0,
                        "tcp_failures": 0,
                        "timeouts": 0,
                        "http_statuses": [429, 500, 501, 502, 503, 504, 505],
                        "window": 10,
                        "success_rate": 0
                    },
                    "unhealthy": {
                        "http_failures": 5,
                        "tcp_failures": 5,
                        "timeouts": 5,
                        "http_statuses": [429, 500, 501, 502, 503, 504, 505],
                        "window": 10,
                        "success_rate": 50
                    },
                    "reset_timeout": 30
                }
            }
        )
        tree.add_node(plugin)
        
        result = self.emitter.generate(tree)
        
        plugins = result["plugins"]
        circuit_breaker = next((p for p in plugins if p["name"] == "circuit-breaker"), None)
        self.assertIsNotNone(circuit_breaker)
        self.assertIn("config", circuit_breaker)

    def test_generate_full_kong_config(self):
        """Test generate full Kong configuration."""
        tree = ProjectionTree()
        
        # Gateway - required: id, version
        tree.add_node(ProjectionNode(
            id="main-gateway",
            kind=NodeKind.KONG_GATEWAY,
            params={
                "id": "main-gateway",
                "version": "3.0",
                "listen_port": 8000,
                "ssl": False,
                "name": "main-gateway"
            }
        ))
        
        # Service - required: id, name, protocol, host, port
        tree.add_node(ProjectionNode(
            id="order-service",
            kind=NodeKind.KONG_SERVICE,
            params={
                "id": "order-service",
                "name": "order-service",
                "protocol": "http",
                "host": "order-service",
                "port": 3000,
                "url": "http://order-service:3000"
            }
        ))
        
        # Route - required: id, name, paths
        tree.add_node(ProjectionNode(
            id="order-route",
            kind=NodeKind.KONG_ROUTE,
            params={
                "id": "order-route",
                "name": "order-route",
                "paths": ["/orders"],
                "methods": ["GET", "POST"],
                "service": "order-service"
            }
        ))
        
        result = self.emitter.generate(tree)
        
        # Verify all sections
        self.assertIn("gateway", result)
        self.assertIn("services", result)
        self.assertIn("routes", result)
        self.assertEqual(len(result["services"]), 1)
        self.assertEqual(len(result["routes"]), 1)

    def test_to_yaml_output(self):
        """Test convert config sang YAML string."""
        tree = ProjectionTree()
        
        # Service - required: id, name, protocol, host, port
        tree.add_node(ProjectionNode(
            id="test-service",
            kind=NodeKind.KONG_SERVICE,
            params={
                "id": "test-service",
                "name": "test-service",
                "protocol": "http",
                "host": "test-service",
                "port": 3000,
                "url": "http://test-service:3000"
            }
        ))
        
        yaml_output = self.emitter.to_yaml(tree)
        
        # Verify YAML output
        self.assertIsInstance(yaml_output, str)
        self.assertIn("services:", yaml_output)
        self.assertIn("test-service", yaml_output)

    def test_generate_consul_service_mesh(self):
        """Test generate Consul service mesh configuration."""
        tree = ProjectionTree()
        
        # Consul service mesh - required: id, datacenter
        tree.add_node(ProjectionNode(
            id="service-mesh",
            kind=NodeKind.CONSUL_SERVICE_MESH,
            params={
                "id": "service-mesh",
                "datacenter": "dc1",
                "name": "service-mesh",
                "protocol": "http"
            }
        ))
        
        # Consul service - required: id, name, port
        tree.add_node(ProjectionNode(
            id="payment-service",
            kind=NodeKind.CONSUL_SERVICE,
            params={
                "id": "payment-service-1",
                "name": "payment-service",
                "port": 3001,
                "address": "payment-service",
                "tags": ["v1", "primary"],
                "meta": {"version": "1.0.0"}
            }
        ))
        
        result = self.emitter.generate(tree)
        
        # Verify Consul config
        self.assertIn("consul", result)
        self.assertIn("services", result["consul"])

    def test_generate_health_check(self):
        """Test generate health check configuration."""
        tree = ProjectionTree()
        
        # Consul health check - required: id, type
        tree.add_node(ProjectionNode(
            id="payment-health-check",
            kind=NodeKind.CONSUL_HEALTH_CHECK,
            params={
                "id": "payment-health-check",
                "type": "http",
                "service": "payment-service",
                "http": "http://payment-service:3001/health",
                "interval": "10s",
                "timeout": "5s",
                "deregister_critical_service_after": "30s"
            }
        ))
        
        result = self.emitter.generate(tree)
        
        health_checks = result.get("consul", {}).get("health_checks", [])
        self.assertEqual(len(health_checks), 1)
        self.assertEqual(health_checks[0]["service"], "payment-service")

    def test_generate_connect_proxy(self):
        """Test generate Consul Connect proxy configuration."""
        tree = ProjectionTree()
        
        # Consul Connect - required: id, service_id
        tree.add_node(ProjectionNode(
            id="payment-connect",
            kind=NodeKind.CONSUL_CONNECT,
            params={
                "id": "payment-connect",
                "service_id": "payment-service",
                "service": "payment-service",
                "proxy": {
                    "upstreams": [
                        {"destination_name": "database-service", "local_bind_port": 5432}
                    ]
                }
            }
        ))
        
        result = self.emitter.generate(tree)
        
        connects = result.get("consul", {}).get("connects", [])
        self.assertEqual(len(connects), 1)

    def test_save_to_file(self):
        """Test save config ra file."""
        tree = ProjectionTree()
        
        # Service - required: id, name, protocol, host, port
        tree.add_node(ProjectionNode(
            id="file-test-service",
            kind=NodeKind.KONG_SERVICE,
            params={
                "id": "file-test-service",
                "name": "file-test-service",
                "protocol": "http",
                "host": "file-test",
                "port": 3000,
                "url": "http://file-test:3000"
            }
        ))
        
        # Tạo temp file path
        output_path = Path("/tmp/test_kong_config.yaml")
        
        # Save và verify
        self.emitter.save(tree, output_path)
        
        # Verify file được tạo
        self.assertTrue(output_path.exists())
        
        # Đọc lại file và verify
        content = output_path.read_text()
        self.assertIn("services:", content)
        
        # Clean up
        output_path.unlink()

    def test_multiple_services_aggregation(self):
        """Test aggregate multiple services."""
        tree = ProjectionTree()
        
        # Thêm nhiều services - required: id, name, protocol, host, port
        for i in range(3):
            tree.add_node(ProjectionNode(
                id=f"service-{i}",
                kind=NodeKind.KONG_SERVICE,
                params={
                    "id": f"service-{i}",
                    "name": f"service-{i}",
                    "protocol": "http",
                    "host": f"service-{i}",
                    "port": 3000 + i,
                    "url": f"http://service-{i}:300{i}"
                }
            ))
        
        result = self.emitter.generate(tree)

        self.assertEqual(len(result["services"]), 3)

    def test_save_consul_hcl(self):
        """Test save Consul configuration ra file HCL."""
        tree = ProjectionTree()

        # Thêm Consul service - required: id, name, port
        tree.add_node(ProjectionNode(
            id="hcl-service",
            kind=NodeKind.CONSUL_SERVICE,
            params={
                "id": "hcl-service-1",
                "name": "hcl-service",
                "port": 8080,
                "address": "hcl-service.local",
                "tags": ["v1", "production"]
            }
        ))

        # Thêm health check
        tree.add_node(ProjectionNode(
            id="hcl-health-check",
            kind=NodeKind.CONSUL_HEALTH_CHECK,
            params={
                "id": "hcl-health",
                "type": "http",
                "service": "hcl-service",
                "http": "http://hcl-service.local:8080/health",
                "interval": "10s",
                "timeout": "5s"
            }
        ))

        # Thêm connect proxy
        tree.add_node(ProjectionNode(
            id="hcl-connect",
            kind=NodeKind.CONSUL_CONNECT,
            params={
                "id": "hcl-connect",
                "service_id": "hcl-service",
                "service": "hcl-service",
                "proxy": {
                    "upstreams": [
                        {"destination_name": "db-service", "local_bind_port": 5432}
                    ]
                }
            }
        ))

        # Save HCL
        output_path = Path("/tmp/test_consul_hcl.hcl")
        self.emitter.save_consul_hcl(tree, output_path)

        # Verify file được tạo
        self.assertTrue(output_path.exists())

        # Đọc và verify HCL content
        content = output_path.read_text()
        self.assertIn('service "hcl-service"', content)
        self.assertIn("port = 8080", content)
        self.assertIn("address = \"hcl-service.local\"", content)
        self.assertIn("tags = [", content)
        self.assertIn('id = "hcl-health"', content)
        self.assertIn('http = "http://hcl-service.local:8080/health"', content)
        self.assertIn('connect "hcl-service"', content)
        self.assertIn('destination_name = "db-service"', content)

        # Clean up
        output_path.unlink()

    def test_render_consul_hcl_empty(self):
        """Test render HCL với config rỗng."""
        hcl = self.emitter._render_consul_hcl({})
        self.assertEqual(hcl, "")

    def test_render_consul_hcl_services_only(self):
        """Test render HCL chỉ với services."""
        consul_config = {
            "services": [
                {"name": "test-svc", "port": 9090, "address": "test.local"}
            ]
        }
        hcl = self.emitter._render_consul_hcl(consul_config)
        self.assertIn('service "test-svc"', hcl)
        self.assertIn("port = 9090", hcl)

    def test_render_consul_hcl_health_checks_only(self):
        """Test render HCL chỉ với health checks."""
        consul_config = {
            "health_checks": [
                {
                    "id": "hc-1",
                    "name": "health-check",
                    "service": "svc",
                    "interval": "15s",
                    "timeout": "3s",
                    "http": "http://svc/health"
                }
            ]
        }
        hcl = self.emitter._render_consul_hcl(consul_config)
        self.assertIn('id = "hc-1"', hcl)
        self.assertIn('http = "http://svc/health"', hcl)

    def test_render_consul_hcl_connects_only(self):
        """Test render HCL chỉ với connects."""
        consul_config = {
            "connects": [
                {
                    "service": "proxy-svc",
                    "proxy": {
                        "upstreams": [
                            {"destination_name": "upstream-svc", "local_bind_port": 3306}
                        ]
                    }
                }
            ]
        }
        hcl = self.emitter._render_consul_hcl(consul_config)
        self.assertIn('connect "proxy-svc"', hcl)
        self.assertIn('destination_name = "upstream-svc"', hcl)
        self.assertIn("local_bind_port = 3306", hcl)

    def test_generate_plugin_with_route_scope(self):
        """Test generate plugin với scope là route."""
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="route-plugin",
            kind=NodeKind.KONG_PLUGIN,
            params={
                "id": "cors-plugin",
                "name": "cors",
                "route": "user-route",
                "config": {"origins": ["https://example.com"]}
            }
        ))
        result = self.emitter.generate(tree)
        plugins = result["plugins"]
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0]["route"], "user-route")

    def test_generate_plugin_with_consumer_scope(self):
        """Test generate plugin với scope là consumer."""
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="consumer-plugin",
            kind=NodeKind.KONG_PLUGIN,
            params={
                "id": "rate-limit",
                "name": "rate-limiting",
                "consumer": "admin-user",
                "config": {"second": 50}
            }
        ))
        result = self.emitter.generate(tree)
        plugins = result["plugins"]
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0]["consumer"], "admin-user")

    def test_generate_plugin_global_no_scope(self):
        """Test generate plugin global (không có scope)."""
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="global-plugin",
            kind=NodeKind.KONG_PLUGIN,
            params={
                "id": "global-req-transform",
                "name": "request-transformer",
                "config": {"add": {"headers": {"X-Global": "true"}}}
            }
        ))
        result = self.emitter.generate(tree)
        plugins = result["plugins"]
        self.assertEqual(len(plugins), 1)
        self.assertNotIn("service", plugins[0])
        self.assertNotIn("route", plugins[0])
        self.assertNotIn("consumer", plugins[0])

    def test_health_check_with_all_options(self):
        """Test generate health check với tất cả options."""
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="full-health-check",
            kind=NodeKind.CONSUL_HEALTH_CHECK,
            params={
                "id": "full-hc",
                "type": "http",
                "service": "full-svc",
                "http": "http://full-svc/health",
                "tcp": "full-svc:8080",
                "exec": "/bin/check.sh",
                "ttl": "30s",
                "interval": "10s",
                "timeout": "5s",
                "deregister_critical_service_after": "90s",
                "notes": "Full health check",
                "tags": ["critical"]
            }
        ))
        result = self.emitter.generate(tree)
        checks = result["consul"]["health_checks"]
        self.assertEqual(len(checks), 1)
        check = checks[0]
        self.assertEqual(check["http"], "http://full-svc/health")
        self.assertEqual(check["tcp"], "full-svc:8080")
        self.assertEqual(check["exec"], "/bin/check.sh")
        self.assertEqual(check["ttl"], "30s")
        self.assertEqual(check["deregister_critical_service_after"], "90s")
        self.assertEqual(check["notes"], "Full health check")
        self.assertEqual(check["tags"], ["critical"])

    def test_consul_service_with_weight(self):
        """Test generate Consul service với weight."""
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="weighted-service",
            kind=NodeKind.CONSUL_SERVICE,
            params={
                "id": "weighted-svc-1",
                "name": "weighted-service",
                "port": 8080,
                "address": "weighted.local",
                "tags": ["v1"],
                "meta": {"version": "1.0"},
                "weight": 75
            }
        ))
        result = self.emitter.generate(tree)
        services = result["consul"]["services"]
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]["weight"], 75)
