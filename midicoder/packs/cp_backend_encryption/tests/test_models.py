# coding: utf-8
"""Tests cho CP58 — Data Encryption at Rest models."""

import pytest
from midicoder.packs.cp_backend_encryption.models import (
    EncryptionAlgorithm,
    EncryptionConfig,
    EncryptedField,
    EncryptionKey,
    EncryptionPolicy,
    KeyManagementType,
    KeyStatus,
)


# =============================================================================
# Enums
# =============================================================================

class TestEncryptionAlgorithm:
    def test_enum_values(self):
        assert EncryptionAlgorithm.AES256_GCM.value == "AES256_GCM"
        assert EncryptionAlgorithm.CHACHA20.value == "ChaCha20"
        assert EncryptionAlgorithm.RSA4096.value == "RSA4096"

    def test_enum_count(self):
        assert len(EncryptionAlgorithm) == 3

    def test_enum_from_string(self):
        assert EncryptionAlgorithm("AES256_GCM") == EncryptionAlgorithm.AES256_GCM
        assert EncryptionAlgorithm("ChaCha20") == EncryptionAlgorithm.CHACHA20
        assert EncryptionAlgorithm("RSA4096") == EncryptionAlgorithm.RSA4096


class TestKeyManagementType:
    def test_enum_values(self):
        assert KeyManagementType.LOCAL.value == "local"
        assert KeyManagementType.AWS_KMS.value == "aws_kms"
        assert KeyManagementType.GCP_KMS.value == "gcp_kms"
        assert KeyManagementType.AZURE_KEYVAULT.value == "azure_keyvault"
        assert KeyManagementType.HASHICORP_VAULT.value == "hashicorp_vault"

    def test_enum_count(self):
        assert len(KeyManagementType) == 5


class TestKeyStatus:
    def test_enum_values(self):
        assert KeyStatus.ACTIVE.value == "active"
        assert KeyStatus.ROTATING.value == "rotating"
        assert KeyStatus.RETIRED.value == "retired"

    def test_enum_count(self):
        assert len(KeyStatus) == 3


# =============================================================================
# EncryptionConfig
# =============================================================================

class TestEncryptionConfig:
    def test_creation_with_defaults(self):
        ec = EncryptionConfig(id="ec-1", name="default", algorithm=EncryptionAlgorithm.AES256_GCM)
        assert ec.id == "ec-1"
        assert ec.name == "default"
        assert ec.algorithm == EncryptionAlgorithm.AES256_GCM
        assert ec.key_size == 256
        assert ec.mode == "GCM"
        assert ec.key_management == KeyManagementType.LOCAL

    def test_creation_with_all_fields(self):
        ec = EncryptionConfig(
            id="ec-2",
            name="kms-config",
            algorithm=EncryptionAlgorithm.CHACHA20,
            key_size=512,
            mode="CTR",
            key_management=KeyManagementType.AWS_KMS,
        )
        assert ec.algorithm == EncryptionAlgorithm.CHACHA20
        assert ec.key_size == 512
        assert ec.mode == "CTR"
        assert ec.key_management == KeyManagementType.AWS_KMS

    def test_to_dict(self):
        ec = EncryptionConfig(id="ec-3", name="test", algorithm=EncryptionAlgorithm.AES256_GCM)
        d = ec.to_dict()
        assert d["id"] == "ec-3"
        assert d["algorithm"] == "AES256_GCM"
        assert d["key_size"] == 256
        assert d["mode"] == "GCM"
        assert d["key_management"] == "local"

    def test_from_dict_minimal(self):
        ec = EncryptionConfig.from_dict({"id": "ec-4", "name": "from-dict"})
        assert ec.id == "ec-4"
        assert ec.name == "from-dict"
        assert ec.algorithm == EncryptionAlgorithm.AES256_GCM

    def test_from_dict_full(self):
        data = {
            "id": "ec-5", "name": "full", "algorithm": "ChaCha20",
            "key_size": 512, "mode": "CBC", "key_management": "aws_kms",
        }
        ec = EncryptionConfig.from_dict(data)
        assert ec.algorithm == EncryptionAlgorithm.CHACHA20
        assert ec.key_size == 512
        assert ec.key_management == KeyManagementType.AWS_KMS

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            EncryptionConfig(id="", name="x", algorithm=EncryptionAlgorithm.AES256_GCM)

    def test_validation_error_key_size_too_small(self):
        with pytest.raises(Exception):
            EncryptionConfig(id="ec-6", name="x", algorithm=EncryptionAlgorithm.AES256_GCM, key_size=64)

    def test_roundtrip(self):
        original = EncryptionConfig(
            id="rt-ec", name="roundtrip", algorithm=EncryptionAlgorithm.RSA4096,
            key_size=4096, key_management=KeyManagementType.HASHICORP_VAULT,
        )
        d = original.to_dict()
        restored = EncryptionConfig.from_dict(d)
        assert restored.id == original.id
        assert restored.algorithm == original.algorithm
        assert restored.key_size == original.key_size
        assert restored.key_management == original.key_management


# =============================================================================
# EncryptedField
# =============================================================================

class TestEncryptedField:
    def test_creation_with_defaults(self):
        ef = EncryptedField(id="ef-1", entity_id="e1", field_name="ssn", algorithm=EncryptionAlgorithm.AES256_GCM, key_id="k1")
        assert ef.id == "ef-1"
        assert ef.entity_id == "e1"
        assert ef.field_name == "ssn"
        assert ef.auto_encrypt is True
        assert ef.auto_decrypt is True

    def test_creation_with_all_fields(self):
        ef = EncryptedField(
            id="ef-2", entity_id="e2", field_name="credit_card",
            algorithm=EncryptionAlgorithm.CHACHA20, key_id="k2",
            auto_encrypt=False, auto_decrypt=False,
        )
        assert ef.auto_encrypt is False
        assert ef.auto_decrypt is False

    def test_to_dict(self):
        ef = EncryptedField(id="ef-3", entity_id="e", field_name="pin", algorithm=EncryptionAlgorithm.AES256_GCM, key_id="k")
        d = ef.to_dict()
        assert d["id"] == "ef-3"
        assert d["field_name"] == "pin"
        assert d["algorithm"] == "AES256_GCM"

    def test_from_dict(self):
        data = {
            "id": "ef-4", "entity_id": "e", "field_name": "email",
            "algorithm": "ChaCha20", "key_id": "k", "auto_encrypt": False,
        }
        ef = EncryptedField.from_dict(data)
        assert ef.field_name == "email"
        assert ef.algorithm == EncryptionAlgorithm.CHACHA20
        assert ef.auto_encrypt is False

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            EncryptedField(id="", entity_id="e", field_name="x", algorithm=EncryptionAlgorithm.AES256_GCM, key_id="k")

    def test_validation_error_empty_field_name(self):
        with pytest.raises(Exception):
            EncryptedField(id="ef-5", entity_id="e", field_name="", algorithm=EncryptionAlgorithm.AES256_GCM, key_id="k")

    def test_roundtrip(self):
        original = EncryptedField(
            id="rt-ef", entity_id="e1", field_name="token",
            algorithm=EncryptionAlgorithm.AES256_GCM, key_id="k1",
            auto_encrypt=True, auto_decrypt=False,
        )
        d = original.to_dict()
        restored = EncryptedField.from_dict(d)
        assert restored.id == original.id
        assert restored.field_name == original.field_name
        assert restored.auto_decrypt == original.auto_decrypt


# =============================================================================
# EncryptionKey
# =============================================================================

class TestEncryptionKey:
    def test_creation_with_defaults(self):
        ek = EncryptionKey(
            id="ek-1", name="main-key",
            algorithm=EncryptionAlgorithm.AES256_GCM, key_id="arn:aws:kms",
            provider=KeyManagementType.LOCAL,
        )
        assert ek.id == "ek-1"
        assert ek.status == KeyStatus.ACTIVE
        assert ek.created_at is not None

    def test_is_usable_active(self):
        ek = EncryptionKey(
            id="ek-2", name="x", algorithm=EncryptionAlgorithm.AES256_GCM,
            key_id="k", provider=KeyManagementType.LOCAL, status=KeyStatus.ACTIVE,
        )
        assert ek.is_usable is True
        assert ek.can_decrypt is True

    def test_is_usable_rotating(self):
        ek = EncryptionKey(
            id="ek-3", name="x", algorithm=EncryptionAlgorithm.AES256_GCM,
            key_id="k", provider=KeyManagementType.LOCAL, status=KeyStatus.ROTATING,
        )
        assert ek.is_usable is False
        assert ek.can_decrypt is True

    def test_is_usable_retired(self):
        ek = EncryptionKey(
            id="ek-4", name="x", algorithm=EncryptionAlgorithm.AES256_GCM,
            key_id="k", provider=KeyManagementType.LOCAL, status=KeyStatus.RETIRED,
        )
        assert ek.is_usable is False
        assert ek.can_decrypt is False

    def test_to_dict(self):
        ek = EncryptionKey(
            id="ek-5", name="dict-key", algorithm=EncryptionAlgorithm.AES256_GCM,
            key_id="k", provider=KeyManagementType.AWS_KMS,
        )
        d = ek.to_dict()
        assert d["id"] == "ek-5"
        assert d["algorithm"] == "AES256_GCM"
        assert d["provider"] == "aws_kms"
        assert d["status"] == "active"

    def test_from_dict(self):
        data = {
            "id": "ek-6", "name": "from-dict", "algorithm": "RSA4096",
            "key_id": "k", "provider": "azure_keyvault", "status": "rotating",
        }
        ek = EncryptionKey.from_dict(data)
        assert ek.algorithm == EncryptionAlgorithm.RSA4096
        assert ek.provider == KeyManagementType.AZURE_KEYVAULT
        assert ek.status == KeyStatus.ROTATING

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            EncryptionKey(id="", name="x", algorithm=EncryptionAlgorithm.AES256_GCM, key_id="k", provider=KeyManagementType.LOCAL)

    def test_roundtrip(self):
        original = EncryptionKey(
            id="rt-ek", name="rt", algorithm=EncryptionAlgorithm.AES256_GCM,
            key_id="k", provider=KeyManagementType.LOCAL,
        )
        d = original.to_dict()
        restored = EncryptionKey.from_dict(d)
        assert restored.id == original.id
        assert restored.algorithm == original.algorithm
        assert restored.provider == original.provider


# =============================================================================
# EncryptionPolicy
# =============================================================================

class TestEncryptionPolicy:
    def test_creation_with_defaults(self):
        ep = EncryptionPolicy(id="ep-1", name="default-policy")
        assert ep.id == "ep-1"
        assert ep.name == "default-policy"
        assert ep.at_rest is True
        assert ep.in_transit is True
        assert ep.algorithm == EncryptionAlgorithm.AES256_GCM
        assert ep.key_rotation_days == 90
        assert ep.compliance_standards == []

    def test_creation_with_all_fields(self):
        ep = EncryptionPolicy(
            id="ep-2", name="hipaa", at_rest=True, in_transit=True,
            algorithm=EncryptionAlgorithm.CHACHA20, key_rotation_days=30,
            compliance_standards=["HIPAA", "PCI-DSS"],
        )
        assert ep.key_rotation_days == 30
        assert "HIPAA" in ep.compliance_standards

    def test_to_dict(self):
        ep = EncryptionPolicy(id="ep-3", name="test", compliance_standards=["SOX"])
        d = ep.to_dict()
        assert d["id"] == "ep-3"
        assert d["at_rest"] is True
        assert d["compliance_standards"] == ["SOX"]

    def test_from_dict(self):
        data = {
            "id": "ep-4", "name": "strict", "at_rest": False,
            "key_rotation_days": 60, "compliance_standards": ["HIPAA"],
        }
        ep = EncryptionPolicy.from_dict(data)
        assert ep.at_rest is False
        assert ep.key_rotation_days == 60

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            EncryptionPolicy(id="", name="x")

    def test_validation_error_zero_rotation_days(self):
        with pytest.raises(Exception):
            EncryptionPolicy(id="ep-5", name="x", key_rotation_days=0)

    def test_roundtrip(self):
        original = EncryptionPolicy(
            id="rt-ep", name="rt", at_rest=True, in_transit=False,
            key_rotation_days=45, compliance_standards=["PCI-DSS"],
        )
        d = original.to_dict()
        restored = EncryptionPolicy.from_dict(d)
        assert restored.id == original.id
        assert restored.at_rest == original.at_rest
        assert restored.in_transit == original.in_transit
        assert restored.key_rotation_days == original.key_rotation_days
        assert restored.compliance_standards == original.compliance_standards
