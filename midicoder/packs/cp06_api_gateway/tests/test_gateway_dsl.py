"""
Test suite cho CP06: API Gateway & Service Mesh DSL Nodes.

Test coverage cho:
- Kong Gateway DSL nodes (KongGateway, KongService, KongRoute, KongUpstream, KongPlugin)
- Consul Service Mesh DSL nodes (ConsulServiceMesh, ConsulService, ConsulConnect, ConsulHealthCheck)
- Validation rules cho gateway configs
- Multi-tenant support fields

Mục tiêu coverage: >80%
"""

from unittest import TestCase

from midicoder.dsl.projection import NodeKind, ProjectionNode


# ============================================================================
# Kong Gateway DSL Tests
# ============================================================================


class TestKongGatewayNode(TestCase):
    """Test KongGateway node creation và validation."""

    def test_create_kong_gateway_node(self):
        """Test tạo Kong Gateway node thành công."""
        node = ProjectionNode(
            id="main-gateway",
            kind=NodeKind.KONG_GATEWAY,
            params={
                "id": "main-gateway",
                "version": "3.0",
                "global_plugins": ["prometheus", "cors"],
                "tenant_scope": "global",
            },
        )
        self.assertEqual(node.id, "main-gateway")
        self.assertEqual(node.kind, NodeKind.KONG_GATEWAY)
        self.assertEqual(node.params["version"], "3.0")
        self.assertEqual(len(node.params["global_plugins"]), 2)

    def test_kong_gateway_missing_version(self):
        """Test Kong Gateway thiếu version field throw error."""
        with self.assertRaises(ValueError) as context:
            ProjectionNode(
                id="gateway",
                kind=NodeKind.KONG_GATEWAY,
                params={
                    "id": "gateway",
                    # Thiếu "version"
                },
            )
        self.assertIn("cần field", str(context.exception))

    def test_kong_gateway_with_tenant_scope(self):
        """Test Kong Gateway với tenant_scope field."""
        node = ProjectionNode(
            id="tenant-gateway",
            kind=NodeKind.KONG_GATEWAY,
            params={
                "id": "tenant-gateway",
                "version": "3.0",
                "tenant_scope": "tenant_isolated",
                "tags": ["production", "api"],
            },
        )
        self.assertEqual(node.params["tenant_scope"], "tenant_isolated")
        self.assertEqual(len(node.params["tags"]), 2)


class TestKongServiceNode(TestCase):
    """Test KongService node creation và validation."""

    def test_create_kong_service_node(self):
        """Test tạo Kong Service node thành công."""
        node = ProjectionNode(
            id="order-service",
            kind=NodeKind.KONG_SERVICE,
            params={
                "id": "order-service",
                "name": "order-service-api",
                "protocol": "http",
                "host": "order-service",
                "port": 8080,
                "connect_timeout": 60000,
                "write_timeout": 60000,
                "read_timeout": 60000,
                "retries": 3,
            },
        )
        self.assertEqual(node.id, "order-service")
        self.assertEqual(node.kind, NodeKind.KONG_SERVICE)
        self.assertEqual(node.params["protocol"], "http")
        self.assertEqual(node.params["port"], 8080)

    def test_kong_service_missing_required_fields(self):
        """Test Kong Service thiếu required fields throw error."""
        with self.assertRaises(ValueError) as context:
            ProjectionNode(
                id="service",
                kind=NodeKind.KONG_SERVICE,
                params={
                    "id": "service",
                    "name": "test",
                    # Thiếu protocol, host, port
                },
            )
        self.assertIn("cần field", str(context.exception))

    def test_kong_service_with_upstream_reference(self):
        """Test Kong Service với upstream reference."""
        node = ProjectionNode(
            id="payment-service",
            kind=NodeKind.KONG_SERVICE,
            params={
                "id": "payment-service",
                "name": "payment-service-api",
                "protocol": "http",
                "host": "payment-service",
                "port": 8081,
                "upstream_id": "payment-upstream",
                "tags": ["payment", "critical"],
            },
        )
        self.assertEqual(node.params["upstream_id"], "payment-upstream")

    def test_kong_service_with_tenant_scope(self):
        """Test Kong Service với tenant_scope cho multi-tenant."""
        node = ProjectionNode(
            id="tenant-service",
            kind=NodeKind.KONG_SERVICE,
            params={
                "id": "tenant-service",
                "name": "tenant-api",
                "protocol": "http",
                "host": "tenant-service",
                "port": 8082,
                "tenant_scope": "tenant_isolated",
            },
        )
        self.assertEqual(node.params["tenant_scope"], "tenant_isolated")


class TestKongRouteNode(TestCase):
    """Test KongRoute node creation và validation."""

    def test_create_kong_route_node(self):
        """Test tạo Kong Route node thành công."""
        node = ProjectionNode(
            id="orders-route",
            kind=NodeKind.KONG_ROUTE,
            params={
                "id": "orders-route",
                "name": "orders-api-route",
                "paths": ["/api/v1/orders"],
                "methods": ["GET", "POST"],
                "strip_path": True,
            },
        )
        self.assertEqual(node.id, "orders-route")
        self.assertEqual(node.kind, NodeKind.KONG_ROUTE)
        self.assertEqual(node.params["paths"], ["/api/v1/orders"])
        self.assertTrue(node.params["strip_path"])

    def test_kong_route_missing_paths(self):
        """Test Kong Route thiếu paths field throw error."""
        with self.assertRaises(ValueError) as context:
            ProjectionNode(
                id="route",
                kind=NodeKind.KONG_ROUTE,
                params={
                    "id": "route",
                    "name": "test-route",
                    # Thiếu "paths"
                },
            )
        self.assertIn("cần field", str(context.exception))

    def test_kong_route_with_plugins(self):
        """Test Kong Route với plugin references."""
        node = ProjectionNode(
            id="protected-route",
            kind=NodeKind.KONG_ROUTE,
            params={
                "id": "protected-route",
                "name": "protected-api",
                "paths": ["/api/v1/admin"],
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "plugin_ids": ["jwt-auth", "rate-limit"],
                "tags": ["admin", "protected"],
            },
        )
        self.assertEqual(len(node.params["plugin_ids"]), 2)

    def test_kong_route_with_rate_limiter_reference(self):
        """Test Kong Route với rate limiter reference."""
        node = ProjectionNode(
            id="rate-limited-route",
            kind=NodeKind.KONG_ROUTE,
            params={
                "id": "rate-limited-route",
                "name": "rate-limited-api",
                "paths": ["/api/v1/search"],
                "methods": ["GET"],
                "rate_limiter_id": "api_rate_limit",
            },
        )
        self.assertEqual(node.params["rate_limiter_id"], "api_rate_limit")


class TestKongUpstreamNode(TestCase):
    """Test KongUpstream node creation và validation."""

    def test_create_kong_upstream_node(self):
        """Test tạo Kong Upstream node thành công."""
        node = ProjectionNode(
            id="order-upstream",
            kind=NodeKind.KONG_UPSTREAM,
            params={
                "id": "order-upstream",
                "name": "order-service-upstream",
                "type": "round_robin",
                "healthchecks": {
                    "active": {
                        "type": "http",
                        "http_path": "/health",
                        "healthy": {"interval": 10, "successes": 5},
                        "unhealthy": {"interval": 10, "http_failures": 3},
                    }
                },
            },
        )
        self.assertEqual(node.id, "order-upstream")
        self.assertEqual(node.kind, NodeKind.KONG_UPSTREAM)
        self.assertEqual(node.params["type"], "round_robin")

    def test_kong_upstream_missing_type(self):
        """Test Kong Upstream thiếu type field throw error."""
        with self.assertRaises(ValueError) as context:
            ProjectionNode(
                id="upstream",
                kind=NodeKind.KONG_UPSTREAM,
                params={
                    "id": "upstream",
                    "name": "test-upstream",
                    # Thiếu "type"
                },
            )
        self.assertIn("cần field", str(context.exception))

    def test_kong_upstream_with_hashing(self):
        """Test Kong Upstream với consistent hashing."""
        node = ProjectionNode(
            id="session-upstream",
            kind=NodeKind.KONG_UPSTREAM,
            params={
                "id": "session-upstream",
                "name": "session-service-upstream",
                "type": "consistent_hash",
                "hashes": [
                    {
                        "header": "X-Client-IP",
                        "header_compatible": True,
                    }
                ],
            },
        )
        self.assertEqual(node.params["type"], "consistent_hash")
        self.assertEqual(len(node.params["hashes"]), 1)


class TestKongPluginNode(TestCase):
    """Test KongPlugin node creation và validation."""

    def test_create_kong_plugin_node(self):
        """Test tạo Kong Plugin node thành công."""
        node = ProjectionNode(
            id="rate-limit-plugin",
            kind=NodeKind.KONG_PLUGIN,
            params={
                "id": "rate-limit-plugin",
                "name": "rate-limiting",
                "config": {
                    "minute": 100,
                    "policy": "redis",
                    "hiding_headers": True,
                },
            },
        )
        self.assertEqual(node.id, "rate-limit-plugin")
        self.assertEqual(node.kind, NodeKind.KONG_PLUGIN)
        self.assertEqual(node.params["name"], "rate-limiting")
        self.assertEqual(node.params["config"]["minute"], 100)

    def test_kong_plugin_missing_name(self):
        """Test Kong Plugin thiếu name field throw error."""
        with self.assertRaises(ValueError) as context:
            ProjectionNode(
                id="plugin",
                kind=NodeKind.KONG_PLUGIN,
                params={
                    "id": "plugin",
                    # Thiếu "name"
                },
            )
        self.assertIn("cần field", str(context.exception))

    def test_kong_plugin_with_exempt_groups(self):
        """Test Kong Plugin với exempt groups."""
        node = ProjectionNode(
            id="rate-limit-with-exempt",
            kind=NodeKind.KONG_PLUGIN,
            params={
                "id": "rate-limit-with-exempt",
                "name": "rate-limiting",
                "config": {
                    "minute": 100,
                    "policy": "redis",
                    "exempt_groups": ["admins", "internal"],
                },
            },
        )
        self.assertEqual(len(node.params["config"]["exempt_groups"]), 2)


# ============================================================================
# Consul Service Mesh DSL Tests
# ============================================================================


class TestConsulServiceMeshNode(TestCase):
    """Test ConsulServiceMesh node creation và validation."""

    def test_create_consul_service_mesh_node(self):
        """Test tạo Consul Service Mesh node thành công."""
        node = ProjectionNode(
            id="main-mesh",
            kind=NodeKind.CONSUL_SERVICE_MESH,
            params={
                "id": "main-mesh",
                "datacenter": "dc1",
                "services": ["order-service", "payment-service"],
            },
        )
        self.assertEqual(node.id, "main-mesh")
        self.assertEqual(node.kind, NodeKind.CONSUL_SERVICE_MESH)
        self.assertEqual(node.params["datacenter"], "dc1")

    def test_consul_service_mesh_missing_datacenter(self):
        """Test Consul Service Mesh thiếu datacenter throw error."""
        with self.assertRaises(ValueError) as context:
            ProjectionNode(
                id="mesh",
                kind=NodeKind.CONSUL_SERVICE_MESH,
                params={
                    "id": "mesh",
                    # Thiếu "datacenter"
                },
            )
        self.assertIn("cần field", str(context.exception))

    def test_consul_service_mesh_multi_datacenter(self):
        """Test Consul Service Mesh với multi-datacenter."""
        node = ProjectionNode(
            id="multi-dc-mesh",
            kind=NodeKind.CONSUL_SERVICE_MESH,
            params={
                "id": "multi-dc-mesh",
                "datacenter": "dc1",
                "datacenters": ["dc1", "dc2", "dc3"],
                "services": ["order-service", "payment-service"],
            },
        )
        self.assertEqual(len(node.params["datacenters"]), 3)


class TestConsulServiceNode(TestCase):
    """Test ConsulService node creation và validation."""

    def test_create_consul_service_node(self):
        """Test tạo Consul Service node thành công."""
        node = ProjectionNode(
            id="order-service",
            kind=NodeKind.CONSUL_SERVICE,
            params={
                "id": "order-service",
                "name": "order-service",
                "port": 8080,
                "address": "order-service",
                "tags": ["version:v1", "env:production"],
            },
        )
        self.assertEqual(node.id, "order-service")
        self.assertEqual(node.kind, NodeKind.CONSUL_SERVICE)
        self.assertEqual(node.params["port"], 8080)

    def test_consul_service_missing_port(self):
        """Test Consul Service thiếu port field throw error."""
        with self.assertRaises(ValueError) as context:
            ProjectionNode(
                id="service",
                kind=NodeKind.CONSUL_SERVICE,
                params={
                    "id": "service",
                    "name": "test-service",
                    # Thiếu "port"
                },
            )
        self.assertIn("cần field", str(context.exception))

    def test_consul_service_with_health_checks(self):
        """Test Consul Service với health checks."""
        node = ProjectionNode(
            id="payment-service",
            kind=NodeKind.CONSUL_SERVICE,
            params={
                "id": "payment-service",
                "name": "payment-service",
                "port": 8081,
                "health_checks": [
                    {
                        "id": "api-health",
                        "type": "http",
                        "path": "/health",
                        "interval": "10s",
                        "timeout": "5s",
                    }
                ],
            },
        )
        self.assertEqual(len(node.params["health_checks"]), 1)

    def test_consul_service_with_connect_enabled(self):
        """Test Consul Service với Connect enabled."""
        node = ProjectionNode(
            id="gateway-service",
            kind=NodeKind.CONSUL_SERVICE,
            params={
                "id": "gateway-service",
                "name": "gateway-service",
                "port": 3000,
                "connect_enabled": True,
                "tags": ["gateway", "bff"],
            },
        )
        self.assertTrue(node.params["connect_enabled"])


class TestConsulConnectNode(TestCase):
    """Test ConsulConnect node creation và validation."""

    def test_create_consul_connect_node(self):
        """Test tạo Consul Connect node thành công."""
        node = ProjectionNode(
            id="order-service-connect",
            kind=NodeKind.CONSUL_CONNECT,
            params={
                "id": "order-service-connect",
                "service_id": "order-service",
                "proxy_port": 20000,
                "mtls_enabled": True,
                "verify_server_name": True,
            },
        )
        self.assertEqual(node.id, "order-service-connect")
        self.assertEqual(node.kind, NodeKind.CONSUL_CONNECT)
        self.assertTrue(node.params["mtls_enabled"])

    def test_consul_connect_missing_service_id(self):
        """Test Consul Connect thiếu service_id throw error."""
        with self.assertRaises(ValueError) as context:
            ProjectionNode(
                id="connect",
                kind=NodeKind.CONSUL_CONNECT,
                params={
                    "id": "connect",
                    # Thiếu "service_id"
                },
            )
        self.assertIn("cần field", str(context.exception))

    def test_consul_connect_with_rate_limit(self):
        """Test Consul Connect với rate limiting config."""
        node = ProjectionNode(
            id="payment-service-connect",
            kind=NodeKind.CONSUL_CONNECT,
            params={
                "id": "payment-service-connect",
                "service_id": "payment-service",
                "proxy_port": 21000,
                "mtls_enabled": True,
                "rate_limit": {
                    "requests_per_second": 100,
                    "burst": 200,
                },
            },
        )
        self.assertEqual(node.params["rate_limit"]["requests_per_second"], 100)

    def test_consul_connect_with_upstreams(self):
        """Test Consul Connect với upstream definitions."""
        node = ProjectionNode(
            id="gateway-connect",
            kind=NodeKind.CONSUL_CONNECT,
            params={
                "id": "gateway-connect",
                "service_id": "gateway-service",
                "proxy_port": 30000,
                "upstreams": [
                    {
                        "destination": "order-service",
                        "local_bind_port": 21000,
                        "connect_timeout": "5s",
                        "max_connections": 100,
                    }
                ],
            },
        )
        self.assertEqual(len(node.params["upstreams"]), 1)


class TestConsulHealthCheckNode(TestCase):
    """Test ConsulHealthCheck node creation và validation."""

    def test_create_consul_health_check_node(self):
        """Test tạo Consul Health Check node thành công."""
        node = ProjectionNode(
            id="order-service-health",
            kind=NodeKind.CONSUL_HEALTH_CHECK,
            params={
                "id": "order-service-health",
                "service_id": "order-service",
                "type": "http",
                "path": "/health",
                "interval": "10s",
                "timeout": "5s",
            },
        )
        self.assertEqual(node.id, "order-service-health")
        self.assertEqual(node.kind, NodeKind.CONSUL_HEALTH_CHECK)
        self.assertEqual(node.params["type"], "http")

    def test_consul_health_check_missing_type(self):
        """Test Consul Health Check thiếu type field throw error."""
        with self.assertRaises(ValueError) as context:
            ProjectionNode(
                id="healthcheck",
                kind=NodeKind.CONSUL_HEALTH_CHECK,
                params={
                    "id": "healthcheck",
                    # Thiếu "type"
                },
            )
        self.assertIn("cần field", str(context.exception))

    def test_consul_health_check_grpc(self):
        """Test Consul Health Check với gRPC type."""
        node = ProjectionNode(
            id="grpc-health",
            kind=NodeKind.CONSUL_HEALTH_CHECK,
            params={
                "id": "grpc-health",
                "service_id": "grpc-service",
                "type": "grpc",
                "address": "localhost:9090",
                "interval": "10s",
            },
        )
        self.assertEqual(node.params["type"], "grpc")

    def test_consul_health_check_with_thresholds(self):
        """Test Consul Health Check với healthy/unhealthy thresholds."""
        node = ProjectionNode(
            id="payment-health",
            kind=NodeKind.CONSUL_HEALTH_CHECK,
            params={
                "id": "payment-health",
                "service_id": "payment-service",
                "type": "http",
                "path": "/health",
                "interval": "10s",
                "healthy_threshold": 2,
                "unhealthy_threshold": 3,
            },
        )
        self.assertEqual(node.params["healthy_threshold"], 2)
        self.assertEqual(node.params["unhealthy_threshold"], 3)


# ============================================================================
# Cross-Validation Tests
# ============================================================================


class TestGatewayCrossValidation(TestCase):
    """Test cross-validation giữa Kong và Consul nodes."""

    def test_kong_service_references_upstream(self):
        """Test Kong Service reference Kong Upstream."""
        upstream = ProjectionNode(
            id="order-upstream",
            kind=NodeKind.KONG_UPSTREAM,
            params={
                "id": "order-upstream",
                "name": "order-upstream",
                "type": "round_robin",
            },
        )
        service = ProjectionNode(
            id="order-service",
            kind=NodeKind.KONG_SERVICE,
            params={
                "id": "order-service",
                "name": "order-service",
                "protocol": "http",
                "host": "order-service",
                "port": 8080,
                "upstream_id": "order-upstream",
            },
        )
        # Verify upstream_id reference
        self.assertEqual(service.params["upstream_id"], upstream.id)

    def test_consul_connect_references_service(self):
        """Test Consul Connect reference Consul Service."""
        service = ProjectionNode(
            id="order-service",
            kind=NodeKind.CONSUL_SERVICE,
            params={
                "id": "order-service",
                "name": "order-service",
                "port": 8080,
            },
        )
        connect = ProjectionNode(
            id="order-service-connect",
            kind=NodeKind.CONSUL_CONNECT,
            params={
                "id": "order-service-connect",
                "service_id": "order-service",
                "proxy_port": 20000,
                "mtls_enabled": True,
            },
        )
        # Verify service_id reference
        self.assertEqual(connect.params["service_id"], service.id)

    def test_consul_health_check_references_service(self):
        """Test Consul Health Check reference Consul Service."""
        service = ProjectionNode(
            id="payment-service",
            kind=NodeKind.CONSUL_SERVICE,
            params={
                "id": "payment-service",
                "name": "payment-service",
                "port": 8081,
            },
        )
        health_check = ProjectionNode(
            id="payment-health",
            kind=NodeKind.CONSUL_HEALTH_CHECK,
            params={
                "id": "payment-health",
                "service_id": "payment-service",
                "type": "http",
                "path": "/health",
                "interval": "10s",
            },
        )
        # Verify service_id reference
        self.assertEqual(health_check.params["service_id"], service.id)