# coding: utf-8
"""
Tests cho CP56 — Environment & Secret Management models.

Phạm vi: toàn bộ enums (EnvName, SecretType, KMSProvider) và dataclasses
(EnvConfig, SecretConfig, VaultConfig, KMSConfig, ConfigMapRef).

Mỗi class được test: creation, to_dict, from_dict, defaults,
validation errors, helper methods.
"""

import pytest
from midicoder.packs.cp56_env_secrets.models import (
    EnvName,
    SecretType,
    KMSProvider,
    EnvConfig,
    SecretConfig,
    VaultConfig,
    KMSConfig,
    ConfigMapRef,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TestEnvName:
    def test_enum_values(self):
        assert EnvName.DEV.value == "dev"
        assert EnvName.STAGING.value == "staging"
        assert EnvName.PROD.value == "prod"


class TestSecretType:
    def test_enum_values(self):
        assert SecretType.VAULT.value == "vault"
        assert SecretType.AWS_KMS.value == "aws_kms"
        assert SecretType.GCP_KMS.value == "gcp_kms"
        assert SecretType.LOCAL.value == "local"


class TestKMSProvider:
    def test_enum_values(self):
        assert KMSProvider.AWS.value == "aws"
        assert KMSProvider.GCP.value == "gcp"
        assert KMSProvider.AZURE.value == "azure"


# ---------------------------------------------------------------------------
# EnvConfig
# ---------------------------------------------------------------------------

class TestEnvConfig:
    def test_defaults(self):
        ec = EnvConfig(id="env-001", name="Dev Config")
        assert ec.env_name == EnvName.DEV
        assert ec.variables == {}
        assert ec.required_vars == []
        assert ec.export_to_dotenv is True

    def test_creation(self):
        ec = EnvConfig(
            id="env-002",
            name="Prod Config",
            env_name=EnvName.PROD,
            variables={"DB_HOST": "prod-db", "DB_PORT": "5432"},
            required_vars=["DB_HOST", "DB_PASSWORD"],
            export_to_dotenv=False,
        )
        assert ec.env_name == EnvName.PROD
        assert len(ec.variables) == 2

    def test_to_dict(self):
        ec = EnvConfig(id="env-001", name="Dev", env_name=EnvName.STAGING)
        d = ec.to_dict()
        assert d["env_name"] == "staging"
        assert d["export_to_dotenv"] is True

    def test_from_dict(self):
        data = {
            "id": "env-003",
            "name": "Staging",
            "env_name": "staging",
            "variables": {"X": "1"},
            "required_vars": ["X"],
        }
        ec = EnvConfig.from_dict(data)
        assert ec.env_name == EnvName.STAGING
        assert ec.variables["X"] == "1"

    def test_roundtrip(self):
        original = EnvConfig(
            id="env-001",
            name="Full Config",
            env_name=EnvName.PROD,
            variables={"K": "V"},
            required_vars=["K"],
            export_to_dotenv=False,
        )
        restored = EnvConfig.from_dict(original.to_dict())
        assert restored.env_name == EnvName.PROD
        assert restored.variables == {"K": "V"}
        assert restored.export_to_dotenv is False

    def test_get_required_missing_empty(self):
        ec = EnvConfig(
            id="e1",
            name="n",
            variables={"A": "1", "B": "2"},
            required_vars=["A", "B"],
        )
        assert ec.get_required_missing() == []

    def test_get_required_missing_some(self):
        ec = EnvConfig(
            id="e2",
            name="n",
            variables={"A": "1"},
            required_vars=["A", "B", "C"],
        )
        missing = ec.get_required_missing()
        assert "B" in missing
        assert "C" in missing
        assert "A" not in missing

    def test_empty_id_raises(self):
        with pytest.raises(Exception):
            EnvConfig(id="", name="n")

    def test_empty_name_raises(self):
        with pytest.raises(Exception):
            EnvConfig(id="e1", name="")


# ---------------------------------------------------------------------------
# SecretConfig
# ---------------------------------------------------------------------------

class TestSecretConfig:
    def test_defaults(self):
        sc = SecretConfig(id="sec-001", name="App Secrets")
        assert sc.secret_type == SecretType.LOCAL
        assert sc.engine_version == 2
        assert sc.access_policy == "read-only"

    def test_creation(self):
        sc = SecretConfig(
            id="sec-002",
            name="Vault Secrets",
            secret_type=SecretType.VAULT,
            key_path="secret/data/app",
            engine_version=2,
            path="secret/",
            access_policy="read-write",
        )
        assert sc.secret_type == SecretType.VAULT
        assert sc.access_policy == "read-write"

    def test_is_remote_true(self):
        sc = SecretConfig(id="s1", name="n", secret_type=SecretType.VAULT)
        assert sc.is_remote() is True

    def test_is_remote_false(self):
        sc = SecretConfig(id="s2", name="n", secret_type=SecretType.LOCAL)
        assert sc.is_remote() is False

    def test_to_dict(self):
        sc = SecretConfig(
            id="sec-001",
            name="n",
            secret_type=SecretType.AWS_KMS,
            key_path="arn:aws:kms:...",
            access_policy="admin",
        )
        d = sc.to_dict()
        assert d["secret_type"] == "aws_kms"
        assert d["access_policy"] == "admin"

    def test_from_dict(self):
        data = {
            "id": "sec-003",
            "name": "GCP Secrets",
            "secret_type": "gcp_kms",
            "engine_version": 1,
        }
        sc = SecretConfig.from_dict(data)
        assert sc.secret_type == SecretType.GCP_KMS
        assert sc.engine_version == 1

    def test_roundtrip(self):
        original = SecretConfig(
            id="sec-001",
            name="RT Secret",
            secret_type=SecretType.VAULT,
            key_path="kv/data/prod",
            engine_version=2,
            path="kv/",
            access_policy="read-only",
        )
        restored = SecretConfig.from_dict(original.to_dict())
        assert restored.secret_type == SecretType.VAULT
        assert restored.engine_version == 2

    def test_empty_id_raises(self):
        with pytest.raises(Exception):
            SecretConfig(id="", name="n")

    def test_invalid_engine_version_raises(self):
        with pytest.raises(Exception):
            SecretConfig(id="s1", name="n", engine_version=3)


# ---------------------------------------------------------------------------
# VaultConfig
# ---------------------------------------------------------------------------

class TestVaultConfig:
    def test_defaults(self):
        vc = VaultConfig(id="vault-001", address="https://vault.example.com:8200")
        assert vc.engine_version == 2
        assert vc.paths == []
        assert vc.auto_auth == {}

    def test_creation(self):
        vc = VaultConfig(
            id="vault-002",
            address="https://vault.prod.com:8200",
            engine_version=1,
            paths=["secret/data/app", "secret/data/db"],
            auto_auth={"type": "kubernetes", "mount_role": "app-role"},
        )
        assert vc.engine_version == 1
        assert len(vc.paths) == 2

    def test_to_dict(self):
        vc = VaultConfig(
            id="vault-001",
            address="https://v.com",
            paths=["p1"],
            auto_auth={"t": "k8s"},
        )
        d = vc.to_dict()
        assert d["address"] == "https://v.com"
        assert d["paths"] == ["p1"]

    def test_from_dict(self):
        data = {
            "id": "vault-003",
            "address": "https://vault.local",
            "engine_version": 1,
            "paths": ["secret/data"],
        }
        vc = VaultConfig.from_dict(data)
        assert vc.address == "https://vault.local"
        assert vc.engine_version == 1

    def test_roundtrip(self):
        original = VaultConfig(
            id="vault-001",
            address="https://vault.example.com",
            engine_version=2,
            paths=["secret/app"],
            auto_auth={"type": "kubernetes"},
        )
        restored = VaultConfig.from_dict(original.to_dict())
        assert restored.address == original.address
        assert restored.paths == original.paths

    def test_empty_id_raises(self):
        with pytest.raises(Exception):
            VaultConfig(id="", address="https://v.com")

    def test_empty_address_raises(self):
        with pytest.raises(Exception):
            VaultConfig(id="v1", address="")

    def test_invalid_engine_version_raises(self):
        with pytest.raises(Exception):
            VaultConfig(id="v1", address="https://v.com", engine_version=3)


# ---------------------------------------------------------------------------
# KMSConfig
# ---------------------------------------------------------------------------

class TestKMSConfig:
    def test_defaults(self):
        kc = KMSConfig(id="kms-001", key_id="arn:aws:kms:us-east-1:key/123")
        assert kc.provider == KMSProvider.AWS
        assert kc.region == ""
        assert kc.encryption_context == {}

    def test_creation(self):
        kc = KMSConfig(
            id="kms-002",
            provider=KMSProvider.GCP,
            key_id="projects/p/locations/global/keyRings/r/cryptoKeys/k",
            region="global",
            encryption_context={"purpose": "app-secrets"},
        )
        assert kc.provider == KMSProvider.GCP
        assert kc.encryption_context["purpose"] == "app-secrets"

    def test_to_dict(self):
        kc = KMSConfig(
            id="kms-001",
            provider=KMSProvider.AZURE,
            key_id="vault/key",
            region="westus",
        )
        d = kc.to_dict()
        assert d["provider"] == "azure"
        assert d["region"] == "westus"

    def test_from_dict(self):
        data = {
            "id": "kms-003",
            "provider": "gcp",
            "key_id": "gcp-key",
            "region": "us-central1",
        }
        kc = KMSConfig.from_dict(data)
        assert kc.provider == KMSProvider.GCP
        assert kc.region == "us-central1"

    def test_roundtrip(self):
        original = KMSConfig(
            id="kms-001",
            provider=KMSProvider.AWS,
            key_id="arn:aws:kms:key/abc",
            region="eu-west-1",
            encryption_context={"env": "prod"},
        )
        restored = KMSConfig.from_dict(original.to_dict())
        assert restored.provider == KMSProvider.AWS
        assert restored.region == "eu-west-1"

    def test_empty_id_raises(self):
        with pytest.raises(Exception):
            KMSConfig(id="", key_id="k")

    def test_empty_key_id_raises(self):
        with pytest.raises(Exception):
            KMSConfig(id="k1", key_id="")


# ---------------------------------------------------------------------------
# ConfigMapRef
# ---------------------------------------------------------------------------

class TestConfigMapRef:
    def test_defaults(self):
        cm = ConfigMapRef(id="cmr-001", k8s_configmap="app-config")
        assert cm.mount_path == ""
        assert cm.env_prefix == ""

    def test_creation(self):
        cm = ConfigMapRef(
            id="cmr-002",
            k8s_configmap="db-config",
            mount_path="/etc/config",
            env_prefix="DB_",
        )
        assert cm.mount_path == "/etc/config"
        assert cm.env_prefix == "DB_"

    def test_to_dict(self):
        cm = ConfigMapRef(id="cmr-001", k8s_configmap="cfg", mount_path="/m", env_prefix="P_")
        d = cm.to_dict()
        assert d["k8s_configmap"] == "cfg"
        assert d["env_prefix"] == "P_"

    def test_from_dict(self):
        data = {
            "id": "cmr-003",
            "k8s_configmap": "redis-config",
            "mount_path": "/etc/redis",
        }
        cm = ConfigMapRef.from_dict(data)
        assert cm.k8s_configmap == "redis-config"
        assert cm.mount_path == "/etc/redis"

    def test_roundtrip(self):
        original = ConfigMapRef(
            id="cmr-001",
            k8s_configmap="app-env",
            mount_path="/env",
            env_prefix="APP_",
        )
        restored = ConfigMapRef.from_dict(original.to_dict())
        assert restored.k8s_configmap == "app-env"
        assert restored.env_prefix == "APP_"

    def test_empty_id_raises(self):
        with pytest.raises(Exception):
            ConfigMapRef(id="", k8s_configmap="cfg")

    def test_empty_k8s_configmap_raises(self):
        with pytest.raises(Exception):
            ConfigMapRef(id="cmr-001", k8s_configmap="")
