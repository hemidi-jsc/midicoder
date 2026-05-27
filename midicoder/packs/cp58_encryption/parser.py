# coding: utf-8
"""
Mô-đun parser cho CP58 — Data Encryption at Rest.

Parse DSL dict (từ contract YAML) sang EncryptionIR — Intermediate Representation
cho encryption configs, encrypted fields, encryption keys, và encryption policies.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp58_encryption.models import (
    EncryptionAlgorithm,
    EncryptionConfig,
    EncryptionKey,
    EncryptionPolicy,
    EncryptedField,
    KeyManagementType,
    KeyStatus,
)


@dataclass
class EncryptionIR:
    """Intermediate Representation cho CP58.

    Gom tập tất cả cấu hình encryption tại rest từ DSL, bao gồm
    encryption configs, encrypted fields, encryption keys,
    và encryption policies.

    Attributes:
        configs: Danh sách encryption configurations
        fields: Danh sách encrypted fields
        keys: Danh sách encryption keys
        policies: Danh sách encryption policies
        default_algorithm: Thuật toán mặc định
        default_key_management: Hệ thống quản lý khóa mặc định
        enable_auto_encrypt: Có bật auto-encrypt không
        enable_auto_decrypt: Có bật auto-decrypt không
        enable_key_rotation: Có bật key rotation tự động không
    """
    configs: list[EncryptionConfig] = field(default_factory=list)
    fields: list[EncryptedField] = field(default_factory=list)
    keys: list[EncryptionKey] = field(default_factory=list)
    policies: list[EncryptionPolicy] = field(default_factory=list)
    default_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES256_GCM
    default_key_management: KeyManagementType = KeyManagementType.LOCAL
    enable_auto_encrypt: bool = True
    enable_auto_decrypt: bool = True
    enable_key_rotation: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Chuyển EncryptionIR sang dict."""
        return {
            "configs": [c.to_dict() for c in self.configs],
            "fields": [f.to_dict() for f in self.fields],
            "keys": [k.to_dict() for k in self.keys],
            "policies": [p.to_dict() for p in self.policies],
            "default_algorithm": self.default_algorithm.value,
            "default_key_management": self.default_key_management.value,
            "enable_auto_encrypt": self.enable_auto_encrypt,
            "enable_auto_decrypt": self.enable_auto_decrypt,
            "enable_key_rotation": self.enable_key_rotation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EncryptionIR":
        """Tạo EncryptionIR từ dict."""
        configs = [EncryptionConfig.from_dict(c) for c in data.get("configs", [])]
        enc_fields = [EncryptedField.from_dict(f) for f in data.get("fields", [])]
        enc_keys = [EncryptionKey.from_dict(k) for k in data.get("keys", [])]
        pols = [EncryptionPolicy.from_dict(p) for p in data.get("policies", [])]
        return cls(
            configs=configs,
            fields=enc_fields,
            keys=enc_keys,
            policies=pols,
            default_algorithm=EncryptionAlgorithm(data.get("default_algorithm", "AES256_GCM")),
            default_key_management=KeyManagementType(data.get("default_key_management", "local")),
            enable_auto_encrypt=data.get("enable_auto_encrypt", True),
            enable_auto_decrypt=data.get("enable_auto_decrypt", True),
            enable_key_rotation=data.get("enable_key_rotation", True),
        )


def parse_configs(data: dict[str, Any]) -> list[EncryptionConfig]:
    """Parse danh sách encryption configurations từ DSL dict.

    Args:
        data: DSL dict với key 'configs' hoặc 'encryption_configs'

    Returns:
        Danh sách EncryptionConfig
    """
    raw = data.get("configs", data.get("encryption_configs", []))
    configs = []
    for c_data in raw:
        configs.append(EncryptionConfig(
            id=c_data.get("id", ""),
            name=c_data.get("name", c_data.get("id", "")),
            algorithm=EncryptionAlgorithm(c_data.get("algorithm", "AES256_GCM")),
            key_size=c_data.get("key_size", 256),
            mode=c_data.get("mode", "GCM"),
            key_management=KeyManagementType(c_data.get("key_management", "local")),
        ))
    return configs


def parse_encrypted_fields(data: dict[str, Any]) -> list[EncryptedField]:
    """Parse danh sách encrypted fields từ DSL dict.

    Args:
        data: DSL dict với key 'fields' hoặc 'encrypted_fields'

    Returns:
        Danh sách EncryptedField
    """
    raw = data.get("fields", data.get("encrypted_fields", []))
    ef_list = []
    for f_data in raw:
        ef_list.append(EncryptedField(
            id=f_data.get("id", ""),
            entity_id=f_data.get("entity_id", ""),
            field_name=f_data.get("field_name", ""),
            algorithm=EncryptionAlgorithm(f_data.get("algorithm", "AES256_GCM")),
            key_id=f_data.get("key_id", ""),
            auto_encrypt=f_data.get("auto_encrypt", True),
            auto_decrypt=f_data.get("auto_decrypt", True),
        ))
    return ef_list


def parse_encryption_keys(data: dict[str, Any]) -> list[EncryptionKey]:
    """Parse danh sách encryption keys từ DSL dict.

    Args:
        data: DSL dict với key 'keys' hoặc 'encryption_keys'

    Returns:
        Danh sách EncryptionKey
    """
    raw = data.get("keys", data.get("encryption_keys", []))
    key_list = []
    for k_data in raw:
        key_list.append(EncryptionKey(
            id=k_data.get("id", ""),
            name=k_data.get("name", k_data.get("id", "")),
            algorithm=EncryptionAlgorithm(k_data.get("algorithm", "AES256_GCM")),
            key_id=k_data.get("key_id", ""),
            provider=KeyManagementType(k_data.get("provider", "local")),
            status=KeyStatus(k_data.get("status", "active")),
        ))
    return key_list


def parse_encryption_policies(data: dict[str, Any]) -> list[EncryptionPolicy]:
    """Parse danh sách encryption policies từ DSL dict.

    Args:
        data: DSL dict với key 'policies' hoặc 'encryption_policies'

    Returns:
        Danh sách EncryptionPolicy
    """
    raw = data.get("policies", data.get("encryption_policies", []))
    pol_list = []
    for p_data in raw:
        pol_list.append(EncryptionPolicy(
            id=p_data.get("id", ""),
            name=p_data.get("name", p_data.get("id", "")),
            at_rest=p_data.get("at_rest", True),
            in_transit=p_data.get("in_transit", True),
            algorithm=EncryptionAlgorithm(p_data.get("algorithm", "AES256_GCM")),
            key_rotation_days=p_data.get("key_rotation_days", 90),
            compliance_standards=p_data.get("compliance_standards", []),
        ))
    return pol_list


def parse_to_ir(data: dict[str, Any]) -> EncryptionIR:
    """Parse DSL dict thành EncryptionIR.

    Args:
        data: DSL dict với configs, fields, keys, policies

    Returns:
        EncryptionIR gom tập tất cả parsed data
    """
    configs = parse_configs(data)
    fields = parse_encrypted_fields(data)
    keys = parse_encryption_keys(data)
    policies = parse_encryption_policies(data)

    return EncryptionIR(
        configs=configs,
        fields=fields,
        keys=keys,
        policies=policies,
        default_algorithm=EncryptionAlgorithm(data.get("default_algorithm", "AES256_GCM")),
        default_key_management=KeyManagementType(data.get("default_key_management", "local")),
        enable_auto_encrypt=data.get("enable_auto_encrypt", True),
        enable_auto_decrypt=data.get("enable_auto_decrypt", True),
        enable_key_rotation=data.get("enable_key_rotation", True),
    )


__all__ = [
    "EncryptionIR",
    "parse_configs",
    "parse_encrypted_fields",
    "parse_encryption_keys",
    "parse_encryption_policies",
    "parse_to_ir",
]
