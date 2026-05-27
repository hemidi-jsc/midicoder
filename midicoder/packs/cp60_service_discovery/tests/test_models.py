# coding: utf-8
"""Tests cho CP60 — Service Discovery & Config Center models."""

import pytest
from midicoder.packs.cp60_service_discovery.models import (
    ConfigEntry,
    ConfigWatch,
    Environment,
    LBStrategy,
    LoadBalancingConfig,
    Protocol,
    RegistryProvider,
    ServiceInstance,
    ServiceRegistry,
)


# =============================================================================
# Enums
# =============================================================================

class TestProtocol:
    def test_enum_values(self):
        assert Protocol.HTTP.value == "http"
        assert Protocol.HTTPS.value == "https"
        assert Protocol.GRPC.value == "grpc"

    def test_enum_count(self):
        assert len(Protocol) == 3


class TestRegistryProvider:
    def test_enum_values(self):
        assert RegistryProvider.CONSUL.value == "consul"
        assert RegistryProvider.ETCD.value == "etcd"
        assert RegistryProvider.ZOOKEEPER.value == "zookeeper"
        assert RegistryProvider.EUREKA.value == "eureka"

    def test_enum_count(self):
        assert len(RegistryProvider) == 4


class TestEnvironment:
    def test_enum_values(self):
        assert Environment.DEV.value == "dev"
        assert Environment.STAGING.value == "staging"
        assert Environment.PROD.value == "prod"

    def test_enum_count(self):
        assert len(Environment) == 3


class TestLBStrategy:
    def test_enum_values(self):
        assert LBStrategy.ROUND_ROBIN.value == "round_robin"
        assert LBStrategy.LEAST_CONNECTIONS.value == "least_connections"
        assert LBStrategy.RANDOM.value == "random"
        assert LBStrategy.WEIGHTED.value == "weighted"

    def test_enum_count(self):
        assert len(LBStrategy) == 4


# =============================================================================
# ServiceInstance
# =============================================================================

class TestServiceInstance:
    def test_creation_with_defaults(self):
        si = ServiceInstance(instance_id="si-1", service_name="order-svc", host="localhost", port=8080)
        assert si.instance_id == "si-1"
        assert si.protocol == Protocol.HTTP
        assert si.health_check_path == "/health"
        assert si.registered_at is not None
        assert si.last_heartbeat is not None

    def test_creation_with_all_fields(self):
        si = ServiceInstance(
            instance_id="si-2", service_name="user-svc", host="10.0.0.1", port=9090,
            protocol=Protocol.GRPC, metadata={"version": "1.0"},
            health_check_path="/ready", tags=["primary", "us-east"],
        )
        assert si.protocol == Protocol.GRPC
        assert "primary" in si.tags

    def test_address(self):
        si = ServiceInstance(instance_id="si-3", service_name="x", host="10.0.0.2", port=8443, protocol=Protocol.HTTPS)
        assert si.address == "https://10.0.0.2:8443"

    def test_address_grpc(self):
        si = ServiceInstance(instance_id="si-4", service_name="x", host="grpc.host", port=50051, protocol=Protocol.GRPC)
        assert si.address == "grpc://grpc.host:50051"

    def test_to_dict(self):
        si = ServiceInstance(instance_id="si-5", service_name="api", host="0.0.0.0", port=3000)
        d = si.to_dict()
        assert d["instance_id"] == "si-5"
        assert d["protocol"] == "http"
        assert d["tags"] == []

    def test_from_dict(self):
        data = {
            "instance_id": "si-6", "service_name": "web",
            "host": "web.host", "port": 443, "protocol": "https",
            "tags": ["production"],
        }
        si = ServiceInstance.from_dict(data)
        assert si.protocol == Protocol.HTTPS
        assert si.tags == ["production"]

    def test_validation_error_empty_instance_id(self):
        with pytest.raises(Exception):
            ServiceInstance(instance_id="", service_name="x", host="h", port=80)

    def test_validation_error_empty_service_name(self):
        with pytest.raises(Exception):
            ServiceInstance(instance_id="si-7", service_name="", host="h", port=80)

    def test_validation_error_port_zero(self):
        with pytest.raises(Exception):
            ServiceInstance(instance_id="si-8", service_name="x", host="h", port=0)

    def test_validation_error_port_too_high(self):
        with pytest.raises(Exception):
            ServiceInstance(instance_id="si-9", service_name="x", host="h", port=65536)

    def test_roundtrip(self):
        original = ServiceInstance(
            instance_id="rt-si", service_name="lb", host="10.0.0.5",
            port=8080, protocol=Protocol.GRPC, tags=["a"],
        )
        d = original.to_dict()
        restored = ServiceInstance.from_dict(d)
        assert restored.instance_id == original.instance_id
        assert restored.service_name == original.service_name
        assert restored.host == original.host
        assert restored.port == original.port
        assert restored.protocol == original.protocol
        assert restored.tags == original.tags


# =============================================================================
# ServiceRegistry
# =============================================================================

class TestServiceRegistry:
    def test_creation_with_defaults(self):
        sr = ServiceRegistry(registry_id="sr-1", name="main-registry")
        assert sr.provider == RegistryProvider.CONSUL
        assert sr.quorum_size == 3
        assert sr.session_ttl == 30

    def test_creation_with_all_fields(self):
        sr = ServiceRegistry(
            registry_id="sr-2", name="etcd-reg", provider=RegistryProvider.ETCD,
            quorum_size=5, session_ttl=60, peer_nodes=["node1", "node2"],
        )
        assert sr.provider == RegistryProvider.ETCD
        assert sr.quorum_size == 5
        assert sr.session_ttl == 60

    def test_to_dict(self):
        sr = ServiceRegistry(registry_id="sr-3", name="zk", provider=RegistryProvider.ZOOKEEPER)
        d = sr.to_dict()
        assert d["provider"] == "zookeeper"
        assert d["quorum_size"] == 3

    def test_from_dict(self):
        data = {
            "registry_id": "sr-4", "name": "eureka-reg",
            "provider": "eureka", "quorum_size": 1,
        }
        sr = ServiceRegistry.from_dict(data)
        assert sr.provider == RegistryProvider.EUREKA
        assert sr.quorum_size == 1

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            ServiceRegistry(registry_id="", name="x")

    def test_validation_error_zero_quorum(self):
        with pytest.raises(Exception):
            ServiceRegistry(registry_id="sr-5", name="x", quorum_size=0)

    def test_validation_error_zero_ttl(self):
        with pytest.raises(Exception):
            ServiceRegistry(registry_id="sr-6", name="x", session_ttl=0)

    def test_roundtrip(self):
        original = ServiceRegistry(
            registry_id="rt-sr", name="rt-reg", provider=RegistryProvider.CONSUL,
            quorum_size=3, peer_nodes=["n1"],
        )
        d = original.to_dict()
        restored = ServiceRegistry.from_dict(d)
        assert restored.registry_id == original.registry_id
        assert restored.provider == original.provider
        assert restored.peer_nodes == original.peer_nodes


# =============================================================================
# ConfigEntry
# =============================================================================

class TestConfigEntry:
    def test_creation_with_defaults(self):
        ce = ConfigEntry(entry_id="ce-1", key="db.url", value="postgres://localhost")
        assert ce.environment == Environment.DEV
        assert ce.encrypted is False
        assert ce.version == 1
        assert ce.created_at is not None

    def test_creation_with_all_fields(self):
        ce = ConfigEntry(
            entry_id="ce-2", key="secret.key", value="supersecret",
            environment=Environment.PROD, encrypted=True, version=3,
            watchers=["w1", "w2"],
        )
        assert ce.environment == Environment.PROD
        assert ce.encrypted is True
        assert ce.version == 3

    def test_masked_value_encrypted(self):
        ce = ConfigEntry(entry_id="ce-3", key="k", value="password123", encrypted=True)
        assert ce.masked_value.startswith("****")

    def test_masked_value_short_encrypted(self):
        ce = ConfigEntry(entry_id="ce-4", key="k", value="abc", encrypted=True)
        assert ce.masked_value == "****"

    def test_masked_value_not_encrypted(self):
        ce = ConfigEntry(entry_id="ce-5", key="k", value="visible", encrypted=False)
        assert ce.masked_value == "visible"

    def test_to_dict(self):
        ce = ConfigEntry(entry_id="ce-6", key="app.port", value="8080")
        d = ce.to_dict()
        assert d["entry_id"] == "ce-6"
        assert d["environment"] == "dev"
        assert d["version"] == 1

    def test_from_dict(self):
        data = {
            "entry_id": "ce-7", "key": "cache.ttl", "value": "3600",
            "environment": "prod", "encrypted": True, "version": 5,
        }
        ce = ConfigEntry.from_dict(data)
        assert ce.environment == Environment.PROD
        assert ce.encrypted is True

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            ConfigEntry(entry_id="", key="k", value="v")

    def test_validation_error_empty_key(self):
        with pytest.raises(Exception):
            ConfigEntry(entry_id="ce-8", key="", value="v")

    def test_validation_error_zero_version(self):
        with pytest.raises(Exception):
            ConfigEntry(entry_id="ce-9", key="k", value="v", version=0)

    def test_roundtrip(self):
        original = ConfigEntry(
            entry_id="rt-ce", key="rt.key", value="rt.val",
            environment=Environment.STAGING, encrypted=False, version=2,
        )
        d = original.to_dict()
        restored = ConfigEntry.from_dict(d)
        assert restored.entry_id == original.entry_id
        assert restored.key == original.key
        assert restored.environment == original.environment
        assert restored.version == original.version


# =============================================================================
# ConfigWatch
# =============================================================================

class TestConfigWatch:
    def test_creation_with_defaults(self):
        cw = ConfigWatch(watch_id="cw-1", config_key="db.url", callback_url="http://callback/notify")
        assert cw.polling_interval_seconds == 30
        assert cw.trigger_on_change is True

    def test_creation_with_all_fields(self):
        cw = ConfigWatch(
            watch_id="cw-2", config_key="cache.ttl", callback_url="http://cb",
            polling_interval_seconds=10, trigger_on_change=False,
        )
        assert cw.polling_interval_seconds == 10
        assert cw.trigger_on_change is False

    def test_to_dict(self):
        cw = ConfigWatch(watch_id="cw-3", config_key="k", callback_url="http://x")
        d = cw.to_dict()
        assert d["watch_id"] == "cw-3"
        assert d["config_key"] == "k"

    def test_from_dict(self):
        data = {
            "watch_id": "cw-4", "config_key": "feat.flag",
            "callback_url": "http://handler", "polling_interval_seconds": 5,
        }
        cw = ConfigWatch.from_dict(data)
        assert cw.config_key == "feat.flag"
        assert cw.polling_interval_seconds == 5

    def test_validation_error_empty_watch_id(self):
        with pytest.raises(Exception):
            ConfigWatch(watch_id="", config_key="k", callback_url="http://x")

    def test_validation_error_empty_config_key(self):
        with pytest.raises(Exception):
            ConfigWatch(watch_id="cw-5", config_key="", callback_url="http://x")

    def test_validation_error_empty_callback_url(self):
        with pytest.raises(Exception):
            ConfigWatch(watch_id="cw-6", config_key="k", callback_url="")

    def test_validation_error_zero_polling(self):
        with pytest.raises(Exception):
            ConfigWatch(watch_id="cw-7", config_key="k", callback_url="http://x", polling_interval_seconds=0)

    def test_roundtrip(self):
        original = ConfigWatch(
            watch_id="rt-cw", config_key="rt.k", callback_url="http://rt-cb",
            polling_interval_seconds=15, trigger_on_change=False,
        )
        d = original.to_dict()
        restored = ConfigWatch.from_dict(d)
        assert restored.watch_id == original.watch_id
        assert restored.config_key == original.config_key
        assert restored.polling_interval_seconds == original.polling_interval_seconds


# =============================================================================
# LoadBalancingConfig
# =============================================================================

class TestLoadBalancingConfig:
    def test_creation_with_defaults(self):
        lbc = LoadBalancingConfig(config_id="lbc-1", service_name="api-gw")
        assert lbc.strategy == LBStrategy.ROUND_ROBIN
        assert lbc.health_check_interval == 15
        assert lbc.max_retries == 3

    def test_creation_with_all_fields(self):
        lbc = LoadBalancingConfig(
            config_id="lbc-2", service_name="order-svc",
            strategy=LBStrategy.LEAST_CONNECTIONS,
            health_check_interval=5, max_retries=10,
        )
        assert lbc.strategy == LBStrategy.LEAST_CONNECTIONS
        assert lbc.health_check_interval == 5

    def test_to_dict(self):
        lbc = LoadBalancingConfig(config_id="lbc-3", service_name="x", strategy=LBStrategy.RANDOM)
        d = lbc.to_dict()
        assert d["strategy"] == "random"
        assert d["max_retries"] == 3

    def test_from_dict(self):
        data = {
            "config_id": "lbc-4", "service_name": "web",
            "strategy": "weighted", "max_retries": 0,
        }
        lbc = LoadBalancingConfig.from_dict(data)
        assert lbc.strategy == LBStrategy.WEIGHTED
        assert lbc.max_retries == 0

    def test_validation_error_empty_config_id(self):
        with pytest.raises(Exception):
            LoadBalancingConfig(config_id="", service_name="x")

    def test_validation_error_empty_service_name(self):
        with pytest.raises(Exception):
            LoadBalancingConfig(config_id="lbc-5", service_name="")

    def test_validation_error_zero_health_check(self):
        with pytest.raises(Exception):
            LoadBalancingConfig(config_id="lbc-6", service_name="x", health_check_interval=0)

    def test_validation_error_negative_retries(self):
        with pytest.raises(Exception):
            LoadBalancingConfig(config_id="lbc-7", service_name="x", max_retries=-1)

    def test_roundtrip(self):
        original = LoadBalancingConfig(
            config_id="rt-lbc", service_name="rt-svc",
            strategy=LBStrategy.LEAST_CONNECTIONS,
            max_retries=5,
        )
        d = original.to_dict()
        restored = LoadBalancingConfig.from_dict(d)
        assert restored.config_id == original.config_id
        assert restored.service_name == original.service_name
        assert restored.strategy == original.strategy
        assert restored.max_retries == original.max_retries
