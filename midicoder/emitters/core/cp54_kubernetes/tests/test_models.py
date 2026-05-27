# coding: utf-8
"""
Tests cho CP54 — Kubernetes & Cloud Native Deployment models.

Phạm vi: toàn bộ dataclasses: K8sResources, K8sEnvVar, K8sVolumeMount,
K8sPort, K8sDeployment, K8sService, K8sIngressPath, K8sIngress,
K8sHPA, K8sConfigMap, K8sSecret, K8sPersistentVolume.

Mỗi dataclass được test: creation, to_dict, from_dict, defaults,
validation (nếu có __post_init__).
"""

import pytest
from midicoder.emitters.core.cp54_kubernetes.models import (
    K8sResources,
    K8sEnvVar,
    K8sVolumeMount,
    K8sPort,
    K8sDeployment,
    K8sService,
    K8sIngressPath,
    K8sIngress,
    K8sHPA,
    K8sConfigMap,
    K8sSecret,
    K8sPersistentVolume,
)


# ---------------------------------------------------------------------------
# K8sResources
# ---------------------------------------------------------------------------

class TestK8sResources:
    def test_defaults(self):
        r = K8sResources()
        assert r.cpu == "250m"
        assert r.memory == "256Mi"

    def test_creation(self):
        r = K8sResources(cpu="1", memory="2Gi")
        assert r.cpu == "1"
        assert r.memory == "2Gi"

    def test_to_dict(self):
        r = K8sResources(cpu="500m", memory="512Mi")
        d = r.to_dict()
        assert d == {"cpu": "500m", "memory": "512Mi"}

    def test_from_dict(self):
        r = K8sResources.from_dict({"cpu": "2", "memory": "4Gi"})
        assert r.cpu == "2"
        assert r.memory == "4Gi"

    def test_from_dict_defaults(self):
        r = K8sResources.from_dict({})
        assert r.cpu == "250m"
        assert r.memory == "256Mi"

    def test_roundtrip(self):
        original = K8sResources(cpu="100m", memory="128Mi")
        restored = K8sResources.from_dict(original.to_dict())
        assert restored.cpu == original.cpu
        assert restored.memory == original.memory


# ---------------------------------------------------------------------------
# K8sEnvVar
# ---------------------------------------------------------------------------

class TestK8sEnvVar:
    def test_creation_static(self):
        e = K8sEnvVar(name="DATABASE_URL", value="postgres://localhost/db")
        assert e.value == "postgres://localhost/db"
        assert e.value_from is None

    def test_creation_ref(self):
        e = K8sEnvVar(
            name="SECRET",
            value_from={
                "secretKeyRef": {"name": "my-secret", "key": "password"}
            },
        )
        assert e.value is None
        assert e.value_from["secretKeyRef"]["name"] == "my-secret"

    def test_to_dict(self):
        e = K8sEnvVar(name="APP_ENV", value="production")
        d = e.to_dict()
        assert d["name"] == "APP_ENV"
        assert d["value"] == "production"

    def test_from_dict(self):
        e = K8sEnvVar.from_dict({"name": "X", "value": "1"})
        assert e.name == "X"
        assert e.value == "1"

    def test_from_dict_with_ref(self):
        data = {
            "name": "TOKEN",
            "value_from": {"configMapKeyRef": {"name": "cm", "key": "t"}},
        }
        e = K8sEnvVar.from_dict(data)
        assert e.value_from["configMapKeyRef"]["name"] == "cm"

    def test_roundtrip(self):
        original = K8sEnvVar(name="VAR", value="val")
        restored = K8sEnvVar.from_dict(original.to_dict())
        assert restored.name == "VAR"
        assert restored.value == "val"


# ---------------------------------------------------------------------------
# K8sVolumeMount
# ---------------------------------------------------------------------------

class TestK8sVolumeMount:
    def test_creation(self):
        vm = K8sVolumeMount(name="data", mount_path="/data")
        assert vm.read_only is False

    def test_read_only(self):
        vm = K8sVolumeMount(name="config", mount_path="/etc/config", read_only=True)
        assert vm.read_only is True

    def test_to_dict(self):
        vm = K8sVolumeMount(name="log", mount_path="/var/log", read_only=False)
        d = vm.to_dict()
        assert d["read_only"] is False

    def test_from_dict(self):
        vm = K8sVolumeMount.from_dict({"name": "v", "mount_path": "/mnt", "read_only": True})
        assert vm.read_only is True

    def test_roundtrip(self):
        original = K8sVolumeMount(name="pvc", mount_path="/storage", read_only=True)
        restored = K8sVolumeMount.from_dict(original.to_dict())
        assert restored.name == "pvc"
        assert restored.read_only is True


# ---------------------------------------------------------------------------
# K8sPort
# ---------------------------------------------------------------------------

class TestK8sPort:
    def test_defaults(self):
        p = K8sPort(container_port=8080)
        assert p.protocol == "TCP"
        assert p.name == ""

    def test_creation(self):
        p = K8sPort(container_port=443, protocol="TCP", name="https")
        assert p.container_port == 443

    def test_to_dict(self):
        p = K8sPort(container_port=80, name="http")
        d = p.to_dict()
        assert "name" in d
        assert d["name"] == "http"

    def test_to_dict_no_name(self):
        p = K8sPort(container_port=8080)
        d = p.to_dict()
        assert "name" not in d

    def test_from_dict(self):
        p = K8sPort.from_dict({"container_port": 3000, "protocol": "UDP"})
        assert p.protocol == "UDP"

    def test_roundtrip(self):
        original = K8sPort(container_port=9090, protocol="TCP", name="metrics")
        restored = K8sPort.from_dict(original.to_dict())
        assert restored.container_port == 9090
        assert restored.name == "metrics"


# ---------------------------------------------------------------------------
# K8sDeployment
# ---------------------------------------------------------------------------

class TestK8sDeployment:
    def _full(self) -> K8sDeployment:
        return K8sDeployment(
            id="dep-001",
            name="web-app",
            replicas=3,
            image="myapp:v1.2.0",
            ports=[K8sPort(container_port=8080, name="http")],
            resources=K8sResources(cpu="500m", memory="512Mi"),
            strategy="RollingUpdate",
            labels={"app": "web"},
            env=[K8sEnvVar(name="ENV", value="prod")],
            volume_mounts=[K8sVolumeMount(name="data", mount_path="/data")],
        )

    def test_defaults(self):
        d = K8sDeployment(id="d1", name="n")
        assert d.replicas == 1
        assert d.image == ""
        assert d.strategy == "RollingUpdate"
        assert d.ports == []
        assert d.labels == {}

    def test_creation(self):
        d = self._full()
        assert d.replicas == 3
        assert len(d.ports) == 1
        assert len(d.env) == 1

    def test_to_dict(self):
        d = self._full()
        result = d.to_dict()
        assert result["id"] == "dep-001"
        assert result["replicas"] == 3
        assert len(result["ports"]) == 1
        assert result["ports"][0]["name"] == "http"
        assert result["resources"]["cpu"] == "500m"
        assert result["labels"]["app"] == "web"

    def test_from_dict(self):
        data = {
            "id": "dep-002",
            "name": "api",
            "replicas": 2,
            "image": "api:v1",
            "ports": [{"container_port": 3000, "protocol": "TCP"}],
            "resources": {"cpu": "250m", "memory": "256Mi"},
            "env": [{"name": "NODE_ENV", "value": "production"}],
            "volume_mounts": [{"name": "v", "mount_path": "/mnt"}],
        }
        d = K8sDeployment.from_dict(data)
        assert d.replicas == 2
        assert len(d.ports) == 1
        assert d.ports[0].container_port == 3000

    def test_roundtrip(self):
        original = self._full()
        restored = K8sDeployment.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.replicas == original.replicas
        assert restored.image == original.image
        assert len(restored.ports) == len(original.ports)
        assert len(restored.env) == len(original.env)


# ---------------------------------------------------------------------------
# K8sService
# ---------------------------------------------------------------------------

class TestK8sService:
    def test_defaults(self):
        s = K8sService(id="svc-001", name="web-svc")
        assert s.type == "ClusterIP"
        assert s.selector == {}

    def test_creation(self):
        s = K8sService(
            id="svc-002",
            name="lb",
            type="LoadBalancer",
            ports=[K8sPort(container_port=80)],
            selector={"app": "web"},
        )
        assert s.type == "LoadBalancer"

    def test_to_dict(self):
        s = K8sService(id="s1", name="n", type="NodePort", selector={"x": "y"})
        d = s.to_dict()
        assert d["type"] == "NodePort"
        assert d["selector"] == {"x": "y"}

    def test_from_dict(self):
        s = K8sService.from_dict({
            "id": "s2",
            "name": "api",
            "type": "ClusterIP",
            "ports": [{"container_port": 8080}],
        })
        assert s.type == "ClusterIP"
        assert len(s.ports) == 1

    def test_roundtrip(self):
        original = K8sService(
            id="svc-001",
            name="web",
            type="LoadBalancer",
            ports=[K8sPort(container_port=443, name="https")],
            selector={"app": "web"},
        )
        restored = K8sService.from_dict(original.to_dict())
        assert restored.type == "LoadBalancer"
        assert restored.selector == {"app": "web"}

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            K8sService(id="s", name="n", type="InvalidType")

    def test_all_valid_types(self):
        for t in ("ClusterIP", "NodePort", "LoadBalancer", "ExternalName"):
            s = K8sService(id="s", name="n", type=t)
            assert s.type == t


# ---------------------------------------------------------------------------
# K8sIngressPath
# ---------------------------------------------------------------------------

class TestK8sIngressPath:
    def test_defaults(self):
        p = K8sIngressPath()
        assert p.path == "/"
        assert p.path_type == "Prefix"
        assert p.service_port == 80

    def test_creation(self):
        p = K8sIngressPath(
            path="/api",
            path_type="Exact",
            service_name="api-svc",
            service_port=3000,
        )
        assert p.path == "/api"

    def test_to_dict(self):
        p = K8sIngressPath(path="/v1", service_name="svc")
        d = p.to_dict()
        assert d["service_name"] == "svc"

    def test_from_dict(self):
        p = K8sIngressPath.from_dict({"path": "/x", "service_port": 9090})
        assert p.service_port == 9090

    def test_roundtrip(self):
        original = K8sIngressPath(path="/app", service_name="app", service_port=8080)
        restored = K8sIngressPath.from_dict(original.to_dict())
        assert restored.path == "/app"


# ---------------------------------------------------------------------------
# K8sIngress
# ---------------------------------------------------------------------------

class TestK8sIngress:
    def test_defaults(self):
        i = K8sIngress(id="ing-001", name="web-ingress")
        assert i.host == ""
        assert i.paths == []
        assert i.tls == {}

    def test_creation(self):
        i = K8sIngress(
            id="ing-002",
            name="api-ingress",
            host="api.example.com",
            paths=[K8sIngressPath(path="/api", service_name="api-svc")],
            tls={"secret_name": "tls-cert"},
            annotations={"nginx.ingress.kubernetes.io/ssl-redirect": "true"},
        )
        assert i.host == "api.example.com"
        assert len(i.paths) == 1

    def test_to_dict(self):
        i = K8sIngress(id="i1", name="n", host="x.com", tls={"s": "c"})
        d = i.to_dict()
        assert d["host"] == "x.com"
        assert d["tls"]["s"] == "c"

    def test_from_dict(self):
        data = {
            "id": "i2",
            "name": "ing",
            "host": "h.com",
            "paths": [{"path": "/api", "service_name": "svc", "service_port": 80}],
        }
        i = K8sIngress.from_dict(data)
        assert i.host == "h.com"
        assert len(i.paths) == 1

    def test_roundtrip(self):
        original = K8sIngress(
            id="ing-001",
            name="ing",
            host="app.com",
            paths=[K8sIngressPath(path="/", service_name="web")],
            annotations={"k": "v"},
        )
        restored = K8sIngress.from_dict(original.to_dict())
        assert restored.host == "app.com"
        assert len(restored.paths) == 1


# ---------------------------------------------------------------------------
# K8sHPA
# ---------------------------------------------------------------------------

class TestK8sHPA:
    def test_defaults(self):
        h = K8sHPA(id="hpa-001", deployment_id="dep-001")
        assert h.min_replicas == 1
        assert h.max_replicas == 10
        assert h.target_cpu == 70
        assert h.target_memory == 80

    def test_creation(self):
        h = K8sHPA(
            id="hpa-002",
            deployment_id="dep-002",
            min_replicas=2,
            max_replicas=20,
            target_cpu=50,
            target_memory=60,
        )
        assert h.min_replicas == 2
        assert h.target_cpu == 50

    def test_to_dict(self):
        h = K8sHPA(id="h", deployment_id="d", max_replicas=5)
        d = h.to_dict()
        assert d["max_replicas"] == 5

    def test_from_dict(self):
        h = K8sHPA.from_dict({
            "id": "h2",
            "deployment_id": "d2",
            "target_cpu": 90,
        })
        assert h.target_cpu == 90

    def test_roundtrip(self):
        original = K8sHPA(id="hpa-001", deployment_id="dep", min_replicas=3, max_replicas=15)
        restored = K8sHPA.from_dict(original.to_dict())
        assert restored.min_replicas == 3
        assert restored.max_replicas == 15


# ---------------------------------------------------------------------------
# K8sConfigMap
# ---------------------------------------------------------------------------

class TestK8sConfigMap:
    def test_defaults(self):
        cm = K8sConfigMap(id="cm-001", name="app-config")
        assert cm.data == {}

    def test_creation(self):
        cm = K8sConfigMap(
            id="cm-002",
            name="db-config",
            data={"DB_HOST": "localhost", "DB_PORT": "5432"},
        )
        assert cm.data["DB_HOST"] == "localhost"

    def test_to_dict(self):
        cm = K8sConfigMap(id="cm1", name="n", data={"k": "v"})
        d = cm.to_dict()
        assert d["data"]["k"] == "v"

    def test_from_dict(self):
        cm = K8sConfigMap.from_dict({
            "id": "cm2",
            "name": "cfg",
            "data": {"A": "1"},
        })
        assert cm.data["A"] == "1"

    def test_roundtrip(self):
        original = K8sConfigMap(id="cm-001", name="cfg", data={"X": "Y"})
        restored = K8sConfigMap.from_dict(original.to_dict())
        assert restored.data == {"X": "Y"}


# ---------------------------------------------------------------------------
# K8sSecret
# ---------------------------------------------------------------------------

class TestK8sSecret:
    def test_defaults(self):
        s = K8sSecret(id="sec-001", name="app-secret")
        assert s.secret_type == "Opaque"
        assert s.data == {}

    def test_creation(self):
        s = K8sSecret(
            id="sec-002",
            name="tls-secret",
            secret_type="TLS",
            data={"tls.crt": "base64data", "tls.key": "base64key"},
        )
        assert s.secret_type == "TLS"

    def test_to_dict(self):
        s = K8sSecret(id="s1", name="n", secret_type="Opaque", data={"k": "v"})
        d = s.to_dict()
        assert d["secret_type"] == "Opaque"

    def test_from_dict(self):
        s = K8sSecret.from_dict({"id": "s2", "name": "secret", "secret_type": "TLS"})
        assert s.secret_type == "TLS"

    def test_roundtrip(self):
        original = K8sSecret(id="sec-001", name="sec", data={"pw": "cGFzcw=="})
        restored = K8sSecret.from_dict(original.to_dict())
        assert restored.data["pw"] == "cGFzcw=="

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            K8sSecret(id="s", name="n", secret_type="BadType")

    def test_all_valid_types(self):
        for t in ("Opaque", "TLS", "kubernetes.io/service-account-token", "kubernetes.io/dockercfg"):
            s = K8sSecret(id="s", name="n", secret_type=t)
            assert s.secret_type == t


# ---------------------------------------------------------------------------
# K8sPersistentVolume
# ---------------------------------------------------------------------------

class TestK8sPersistentVolume:
    def test_defaults(self):
        pv = K8sPersistentVolume(id="pv-001", name="data-pvc")
        assert pv.storage_class == "standard"
        assert pv.size_gb == 1
        assert pv.access_mode == "ReadWriteOnce"
        assert pv.mount_path == "/data"

    def test_creation(self):
        pv = K8sPersistentVolume(
            id="pv-002",
            name="log-pvc",
            storage_class="ssd",
            size_gb=50,
            access_mode="ReadWriteMany",
            mount_path="/var/log",
        )
        assert pv.size_gb == 50
        assert pv.access_mode == "ReadWriteMany"

    def test_to_dict(self):
        pv = K8sPersistentVolume(id="pv1", name="n", size_gb=10)
        d = pv.to_dict()
        assert d["size_gb"] == 10

    def test_from_dict(self):
        pv = K8sPersistentVolume.from_dict({
            "id": "pv2",
            "name": "logs",
            "storage_class": "premium",
            "size_gb": 100,
        })
        assert pv.storage_class == "premium"

    def test_roundtrip(self):
        original = K8sPersistentVolume(
            id="pv-001",
            name="data",
            storage_class="nfs",
            size_gb=25,
            access_mode="ReadOnlyMany",
            mount_path="/ro",
        )
        restored = K8sPersistentVolume.from_dict(original.to_dict())
        assert restored.size_gb == 25
        assert restored.access_mode == "ReadOnlyMany"

    def test_invalid_access_mode_raises(self):
        with pytest.raises(ValueError):
            K8sPersistentVolume(id="pv", name="n", access_mode="BadMode")

    def test_all_valid_modes(self):
        for m in ("ReadWriteOnce", "ReadOnlyMany", "ReadWriteMany"):
            pv = K8sPersistentVolume(id="pv", name="n", access_mode=m)
            assert pv.access_mode == m
