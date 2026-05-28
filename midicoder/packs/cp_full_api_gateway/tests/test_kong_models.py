# coding: utf-8
"""
Tests cho Kong/Consul models của CP06.

Kiểm tra:
- Validation (__post_init__)
- to_dict / from_dict
- Edge cases

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.packs.cp_full_api_gateway.models import (
    KongGateway,
    KongService,
    KongRoute,
    KongUpstream,
    KongTarget,
    KongPlugin,
    PluginName,
    ConsulService,
    ConsulHealthCheck,
    ConsulConnect,
    ConsulUpstream,
    ConsulServiceMesh,
    HealthCheckType,
)


# ===========================================================================
# KongGateway Tests
# ===========================================================================

class TestKongGateway:
    """Tests cho KongGateway model."""

    def test_create_valid_gateway(self):
        """Tạo gateway hợp lệ."""
        gw = KongGateway(name="main-gateway", listen_port=8000)
        assert gw.name == "main-gateway"
        assert gw.listen_port == 8000
        assert gw.ssl is False
        assert gw.admin_listen_port == 8001

    def test_gateway_empty_name_raises(self):
        """Tên gateway rỗng throw error."""
        with pytest.raises(ValueError, match="không được để trống"):
            KongGateway(name="")

    def test_gateway_whitespace_name_raises(self):
        """Tên gateway chỉ whitespace throw error."""
        with pytest.raises(ValueError, match="không được để trống"):
            KongGateway(name="   ")

    def test_gateway_invalid_port_raises(self):
        """Port ngoài range throw error."""
        with pytest.raises(ValueError, match="phải từ 1 đến 65535"):
            KongGateway(name="gw", listen_port=0)

        with pytest.raises(ValueError, match="phải từ 1 đến 65535"):
            KongGateway(name="gw", listen_port=70000)

    def test_gateway_to_dict(self):
        """to_dict trả về dict đầy đủ fields."""
        gw = KongGateway(name="test", listen_port=9000, ssl=True)
        d = gw.to_dict()
        assert d["name"] == "test"
        assert d["listen_port"] == 9000
        assert d["ssl"] is True

    def test_gateway_from_dict(self):
        """from_dict tạo gateway từ dict."""
        d = {"name": "from-dict", "listen_port": 8080, "ssl": True, "admin_listen_port": 8081}
        gw = KongGateway.from_dict(d)
        assert gw.name == "from-dict"
        assert gw.listen_port == 8080
        assert gw.ssl is True
        assert gw.admin_listen_port == 8081


# ===========================================================================
# KongService Tests
# ===========================================================================

class TestKongService:
    """Tests cho KongService model."""

    def test_create_valid_service(self):
        """Tạo service hợp lệ."""
        svc = KongService(name="order-service")
        assert svc.name == "order-service"
        assert svc.url == "http://localhost:3000"
        assert svc.protocol == "http"
        assert svc.port == 3000

    def test_service_empty_name_raises(self):
        """Tên service rỗng throw error."""
        with pytest.raises(ValueError, match="không được để trống"):
            KongService(name="")

    def test_service_invalid_protocol_raises(self):
        """Protocol không hợp lệ throw error."""
        with pytest.raises(ValueError, match="phải là một trong"):
            KongService(name="svc", protocol="invalid_proto")

    def test_service_valid_protocols(self):
        """Tất cả protocols hợp lệ."""
        for proto in ("http", "https", "grpc", "grpcs", "tcp", "tls"):
            svc = KongService(name="svc", protocol=proto)
            assert svc.protocol == proto

    def test_service_to_dict_from_dict(self):
        """Round-trip to_dict/from_dict."""
        svc = KongService(name="svc", url="http://backend:8080", protocol="https", port=8080)
        d = svc.to_dict()
        svc2 = KongService.from_dict(d)
        assert svc2.name == svc.name
        assert svc2.url == svc.url
        assert svc2.protocol == svc.protocol
        assert svc2.port == svc.port


# ===========================================================================
# KongRoute Tests
# ===========================================================================

class TestKongRoute:
    """Tests cho KongRoute model."""

    def test_create_valid_route(self):
        """Tạo route hợp lệ."""
        rt = KongRoute(name="order-route", paths=["/api/orders"])
        assert rt.name == "order-route"
        assert rt.paths == ["/api/orders"]
        assert "GET" in rt.methods
        assert rt.strip_path is True

    def test_route_empty_name_raises(self):
        """Tên route rỗng throw error."""
        with pytest.raises(ValueError, match="không được để trống"):
            KongRoute(name="")

    def test_route_invalid_method_raises(self):
        """HTTP method không hợp lệ throw error."""
        with pytest.raises(ValueError, match="không hợp lệ"):
            KongRoute(name="rt", methods=["INVALID_METHOD"])

    def test_route_valid_methods(self):
        """Tất cả HTTP methods hợp lệ."""
        for method in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
            rt = KongRoute(name="rt", methods=[method])
            assert method in rt.methods

    def test_route_to_dict_from_dict(self):
        """Round-trip to_dict/from_dict."""
        rt = KongRoute(name="rt", paths=["/api"], service="svc", preserve_host=True)
        d = rt.to_dict()
        rt2 = KongRoute.from_dict(d)
        assert rt2.name == rt.name
        assert rt2.service == rt.service
        assert rt2.preserve_host is True


# ===========================================================================
# KongUpstream Tests
# ===========================================================================

class TestKongUpstream:
    """Tests cho KongUpstream model."""

    def test_create_valid_upstream(self):
        """Tạo upstream hợp lệ."""
        upstream = KongUpstream(name="order-upstream")
        assert upstream.name == "order-upstream"
        assert upstream.algorithm == "round-robin"
        assert upstream.slots == 10000

    def test_upstream_empty_name_raises(self):
        """Tên upstream rỗng throw error."""
        with pytest.raises(ValueError, match="không được để trống"):
            KongUpstream(name="")

    def test_upstream_invalid_algorithm_raises(self):
        """Algorithm không hợp lệ throw error."""
        with pytest.raises(ValueError, match="phải là một trong"):
            KongUpstream(name="up", algorithm="invalid_algo")

    def test_upstream_valid_algorithms(self):
        """Tất cả algorithms hợp lệ."""
        for algo in ("round-robin", "least-connections", "consistent-hashing"):
            upstream = KongUpstream(name="up", algorithm=algo)
            assert upstream.algorithm == algo

    def test_upstream_with_targets(self):
        """Upstream với targets."""
        targets = [KongTarget(target="localhost:8001"), KongTarget(target="localhost:8002")]
        upstream = KongUpstream(name="up", targets=targets)
        assert len(upstream.targets) == 2

    def test_upstream_to_dict_with_targets(self):
        """to_dict serialize targets đúng cách."""
        targets = [KongTarget(target="localhost:8001")]
        upstream = KongUpstream(name="up", targets=targets)
        d = upstream.to_dict()
        assert d["targets"] == [{"target": "localhost:8001", "weight": 100}]

    def test_upstream_from_dict_with_targets(self):
        """from_dict deserialize targets đúng cách."""
        d = {"name": "up", "targets": [{"target": "localhost:8001", "weight": 50}]}
        upstream = KongUpstream.from_dict(d)
        assert isinstance(upstream.targets[0], KongTarget)
        assert upstream.targets[0].target == "localhost:8001"
        assert upstream.targets[0].weight == 50


# ===========================================================================
# KongTarget Tests
# ===========================================================================

class TestKongTarget:
    """Tests cho KongTarget model."""

    def test_create_valid_target(self):
        """Tạo target hợp lệ."""
        t = KongTarget(target="localhost:8001", weight=100)
        assert t.target == "localhost:8001"
        assert t.weight == 100

    def test_target_empty_raises(self):
        """Target rỗng throw error."""
        with pytest.raises(ValueError, match="không được để trống"):
            KongTarget(target="")

    def test_target_invalid_weight_raises(self):
        """Weight ngoài range throw error."""
        with pytest.raises(ValueError, match="phải từ 1 đến 1000"):
            KongTarget(target="localhost:8001", weight=0)

        with pytest.raises(ValueError, match="phải từ 1 đến 1000"):
            KongTarget(target="localhost:8001", weight=1001)


# ===========================================================================
# KongPlugin Tests
# ===========================================================================

class TestKongPlugin:
    """Tests cho KongPlugin model."""

    def test_create_valid_plugin(self):
        """Tạo plugin hợp lệ."""
        plugin = KongPlugin(name="rate-limiting", config={"minute": 100})
        assert plugin.name == "rate-limiting"
        assert plugin.enabled is True

    def test_plugin_empty_name_raises(self):
        """Tên plugin rỗng throw error."""
        with pytest.raises(ValueError, match="không được để trống"):
            KongPlugin(name="")

    def test_plugin_to_dict_excludes_none(self):
        """to_dict loại bỏ fields là None."""
        plugin = KongPlugin(name="cors", config={})
        d = plugin.to_dict()
        assert "service" not in d  # None fields excluded
        assert "name" in d

    def test_plugin_with_scope(self):
        """Plugin với service scope."""
        plugin = KongPlugin(name="jwt", service="order-service")
        assert plugin.service == "order-service"

    def test_plugin_from_dict(self):
        """from_dict tạo plugin từ dict."""
        d = {"name": "cors", "config": {"origins": "*"}, "enabled": True}
        plugin = KongPlugin.from_dict(d)
        assert plugin.name == "cors"
        assert plugin.enabled is True


# ===========================================================================
# PluginName Enum Tests
# ===========================================================================

class TestPluginName:
    """Tests cho PluginName enum."""

    def test_plugin_name_values(self):
        """Tất cả plugin names tồn tại."""
        assert PluginName.RATE_LIMITING.value == "rate-limiting"
        assert PluginName.CORS.value == "cors"
        assert PluginName.AUTH_JWT.value == "jwt"


# ===========================================================================
# ConsulService Tests
# ===========================================================================

class TestConsulService:
    """Tests cho ConsulService model."""

    def test_create_valid_service(self):
        """Tạo Consul service hợp lệ."""
        svc = ConsulService(name="order-service", port=8080)
        assert svc.name == "order-service"
        assert svc.port == 8080
        assert svc.service_id == "order-service-8080"  # auto-generated

    def test_service_custom_id(self):
        """Service với custom ID."""
        svc = ConsulService(name="svc", service_id="custom-id")
        assert svc.service_id == "custom-id"

    def test_service_empty_name_raises(self):
        """Tên service rỗng throw error."""
        with pytest.raises(ValueError, match="không được để trống"):
            ConsulService(name="")

    def test_service_invalid_port_raises(self):
        """Port ngoài range throw error."""
        with pytest.raises(ValueError, match="phải từ 1 đến 65535"):
            ConsulService(name="svc", port=0)

    def test_service_to_dict_from_dict(self):
        """Round-trip to_dict/from_dict."""
        svc = ConsulService(name="svc", port=9090, tags=["v1", "production"])
        d = svc.to_dict()
        svc2 = ConsulService.from_dict(d)
        assert svc2.name == svc.name
        assert svc2.tags == ["v1", "production"]


# ===========================================================================
# ConsulHealthCheck Tests
# ===========================================================================

class TestConsulHealthCheck:
    """Tests cho ConsulHealthCheck model."""

    def test_create_valid_http_check(self):
        """Tạo HTTP health check hợp lệ."""
        check = ConsulHealthCheck(
            id="check-1",
            check_type=HealthCheckType.HTTP,
            http="http://localhost:8080/health",
        )
        assert check.id == "check-1"
        assert check.check_type == HealthCheckType.HTTP
        assert check.http == "http://localhost:8080/health"

    def test_create_valid_tcp_check(self):
        """Tạo TCP health check hợp lệ."""
        check = ConsulHealthCheck(
            id="check-tcp",
            check_type=HealthCheckType.TCP,
            tcp="localhost:8080",
        )
        assert check.tcp == "localhost:8080"

    def test_create_valid_exec_check(self):
        """Tạo exec health check hợp lệ."""
        check = ConsulHealthCheck(
            id="check-exec",
            check_type=HealthCheckType.EXEC,
            exec="/usr/bin/check-health",
        )
        assert check.exec == "/usr/bin/check-health"

    def test_create_valid_ttl_check(self):
        """Tạo TTL health check hợp lệ."""
        check = ConsulHealthCheck(
            id="check-ttl",
            check_type=HealthCheckType.TTL,
            ttl="30s",
        )
        assert check.ttl == "30s"

    def test_http_check_without_url_raises(self):
        """HTTP check không có URL throw error."""
        with pytest.raises(ValueError, match="cần có URL"):
            ConsulHealthCheck(id="bad", check_type=HealthCheckType.HTTP)

    def test_tcp_check_without_address_raises(self):
        """TCP check không có address throw error."""
        with pytest.raises(ValueError, match="cần có address"):
            ConsulHealthCheck(id="bad", check_type=HealthCheckType.TCP)

    def test_empty_id_raises(self):
        """ID rỗng throw error."""
        with pytest.raises(ValueError, match="không được để trống"):
            ConsulHealthCheck(id="")

    def test_invalid_interval_format_raises(self):
        """Interval format không hợp lệ throw error."""
        with pytest.raises(ValueError, match="format không hợp lệ"):
            ConsulHealthCheck(id="bad", interval="invalid")

    def test_to_dict_includes_type_value(self):
        """to_dict serialize check_type thành value."""
        check = ConsulHealthCheck(
            id="check-1",
            check_type=HealthCheckType.HTTP,
            http="http://localhost/health",
        )
        d = check.to_dict()
        assert d["check_type"] == "http"

    def test_from_dict_with_string_type(self):
        """from_dict parse check_type từ string."""
        d = {
            "id": "check-1",
            "check_type": "tcp",
            "tcp": "localhost:8080",
        }
        check = ConsulHealthCheck.from_dict(d)
        assert check.check_type == HealthCheckType.TCP


# ===========================================================================
# ConsulConnect Tests
# ===========================================================================

class TestConsulConnect:
    """Tests cho ConsulConnect model."""

    def test_create_valid_connect(self):
        """Tạo Connect config hợp lệ."""
        connect = ConsulConnect(service="order-service")
        assert connect.service == "order-service"

    def test_connect_empty_service_raises(self):
        """Service rỗng throw error."""
        with pytest.raises(ValueError, match="không được để trống"):
            ConsulConnect(service="")

    def test_connect_with_upstreams(self):
        """Connect với upstreams."""
        upstreams = [ConsulUpstream(destination_name="payment-service", local_bind_port=9001)]
        connect = ConsulConnect(service="order-service", upstreams=upstreams)
        assert len(connect.upstreams) == 1

    def test_connect_to_dict(self):
        """to_dict serialize upstreams đúng cách."""
        upstreams = [ConsulUpstream(destination_name="payment", local_bind_port=9001)]
        connect = ConsulConnect(service="order", upstreams=upstreams)
        d = connect.to_dict()
        assert d["upstreams"] == [{"destination_name": "payment", "local_bind_port": 9001}]

    def test_connect_from_dict(self):
        """from_dict deserialize upstreams đúng cách."""
        d = {
            "service": "order",
            "upstreams": [{"destination_name": "payment", "local_bind_port": 9001}],
        }
        connect = ConsulConnect.from_dict(d)
        assert isinstance(connect.upstreams[0], ConsulUpstream)


# ===========================================================================
# ConsulUpstream Tests
# ===========================================================================

class TestConsulUpstream:
    """Tests cho ConsulUpstream model."""

    def test_create_valid_upstream(self):
        """Tạo Consul upstream hợp lệ."""
        up = ConsulUpstream(destination_name="payment", local_bind_port=9001)
        assert up.destination_name == "payment"
        assert up.local_bind_port == 9001

    def test_upstream_empty_dest_raises(self):
        """Destination rỗng throw error."""
        with pytest.raises(ValueError, match="không được để trống"):
            ConsulUpstream(destination_name="")

    def test_upstream_to_dict_from_dict(self):
        """Round-trip to_dict/from_dict."""
        up = ConsulUpstream(destination_name="svc", local_bind_port=8080)
        d = up.to_dict()
        up2 = ConsulUpstream.from_dict(d)
        assert up2.destination_name == up.destination_name
        assert up2.local_bind_port == up.local_bind_port


# ===========================================================================
# ConsulServiceMesh Tests
# ===========================================================================

class TestConsulServiceMesh:
    """Tests cho ConsulServiceMesh model."""

    def test_create_valid_mesh(self):
        """Tạo service mesh hợp lệ."""
        mesh = ConsulServiceMesh(name="main-mesh")
        assert mesh.name == "main-mesh"
        assert mesh.datacenter == "dc1"
        assert mesh.protocol == "http"

    def test_mesh_empty_name_raises(self):
        """Tên mesh rỗng throw error."""
        with pytest.raises(ValueError, match="không được để trống"):
            ConsulServiceMesh(name="")

    def test_mesh_to_dict_from_dict(self):
        """Round-trip to_dict/from_dict."""
        mesh = ConsulServiceMesh(name="mesh", datacenter="us-east-1", protocol="grpc")
        d = mesh.to_dict()
        mesh2 = ConsulServiceMesh.from_dict(d)
        assert mesh2.name == mesh.name
        assert mesh2.datacenter == mesh.datacenter
        assert mesh2.protocol == mesh.protocol
