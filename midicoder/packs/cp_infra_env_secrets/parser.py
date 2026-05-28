# coding: utf-8
"""
Mô-đun parser cho I04 — Environment & Secret Management.

Parse DSL dict (từ contract YAML) sang EnvIR — Intermediate Representation
cho environment configurations, secret management, vault setup, và KMS config.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp_infra_env_secrets.models import (
    ConfigMapRef,
    EnvConfig,
    EnvName,
    KMSConfig,
    KMSProvider,
    SecretConfig,
    SecretType,
    VaultConfig,
)


@dataclass
class EnvIR:
    """Intermediate Representation cho CP56.

    Gom tập tất cả cấu hình environment và secret management từ DSL,
    bao gồm env configs, secret configs, vault configs, KMS configs,
    và ConfigMap references.

    Attributes:
        env_configs: Danh sách cấu hình biến môi trường
        secret_configs: Danh sách cấu hình secret management
        vault_configs: Danh sách cấu hình HashiCorp Vault
        kms_configs: Danh sách cấu hình KMS
        configmap_refs: Danh sách tham chiếu Kubernetes ConfigMap
    """
    env_configs: list[EnvConfig] = field(default_factory=list)
    secret_configs: list[SecretConfig] = field(default_factory=list)
    vault_configs: list[VaultConfig] = field(default_factory=list)
    kms_configs: list[KMSConfig] = field(default_factory=list)
    configmap_refs: list[ConfigMapRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển EnvIR sang dict."""
        return {
            "env_configs": [e.to_dict() for e in self.env_configs],
            "secret_configs": [s.to_dict() for s in self.secret_configs],
            "vault_configs": [v.to_dict() for v in self.vault_configs],
            "kms_configs": [k.to_dict() for k in self.kms_configs],
            "configmap_refs": [c.to_dict() for c in self.configmap_refs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnvIR":
        """Tạo EnvIR từ dict."""
        env_configs = [EnvConfig.from_dict(e) for e in data.get("env_configs", [])]
        secret_configs = [SecretConfig.from_dict(s) for s in data.get("secret_configs", [])]
        vault_configs = [VaultConfig.from_dict(v) for v in data.get("vault_configs", [])]
        kms_configs = [KMSConfig.from_dict(k) for k in data.get("kms_configs", [])]
        configmap_refs = [ConfigMapRef.from_dict(c) for c in data.get("configmap_refs", [])]
        return cls(
            env_configs=env_configs,
            secret_configs=secret_configs,
            vault_configs=vault_configs,
            kms_configs=kms_configs,
            configmap_refs=configmap_refs,
        )


def parse_env_configs(data: dict[str, Any]) -> list[EnvConfig]:
    """Parse danh sách env configurations từ DSL dict.

    Args:
        data: DSL dict với key 'env_configs' hoặc 'environments'

    Returns:
        Danh sách EnvConfig
    """
    raw = data.get("env_configs", data.get("environments", []))
    configs = []
    for e_data in raw:
        configs.append(EnvConfig(
            id=e_data.get("id", e_data.get("env_id", "")),
            name=e_data.get("name", e_data.get("id", "")),
            env_name=EnvName(e_data.get("env_name", e_data.get("environment", "dev"))),
            variables=e_data.get("variables", e_data.get("vars", {})),
            required_vars=e_data.get("required_vars", e_data.get("required", [])),
            export_to_dotenv=e_data.get("export_to_dotenv", True),
        ))
    return configs


def parse_secret_configs(data: dict[str, Any]) -> list[SecretConfig]:
    """Parse danh sách secret configurations từ DSL dict.

    Args:
        data: DSL dict với key 'secret_configs' hoặc 'secrets'

    Returns:
        Danh sách SecretConfig
    """
    raw = data.get("secret_configs", data.get("secrets", []))
    configs = []
    for s_data in raw:
        configs.append(SecretConfig(
            id=s_data.get("id", s_data.get("secret_id", "")),
            name=s_data.get("name", s_data.get("id", "")),
            secret_type=SecretType(s_data.get("secret_type", s_data.get("type", "local"))),
            key_path=s_data.get("key_path", ""),
            engine_version=s_data.get("engine_version", 2),
            path=s_data.get("path", ""),
            access_policy=s_data.get("access_policy", "read-only"),
        ))
    return configs


def parse_vault_configs(data: dict[str, Any]) -> list[VaultConfig]:
    """Parse danh sách Vault configurations từ DSL dict.

    Args:
        data: DSL dict với key 'vault_configs' hoặc 'vaults'

    Returns:
        Danh sách VaultConfig
    """
    raw = data.get("vault_configs", data.get("vaults", []))
    configs = []
    for v_data in raw:
        configs.append(VaultConfig(
            id=v_data.get("id", v_data.get("vault_id", "")),
            address=v_data.get("address", ""),
            engine_version=v_data.get("engine_version", 2),
            paths=v_data.get("paths", []),
            auto_auth=v_data.get("auto_auth", {}),
        ))
    return configs


def parse_kms_configs(data: dict[str, Any]) -> list[KMSConfig]:
    """Parse danh sách KMS configurations từ DSL dict.

    Args:
        data: DSL dict với key 'kms_configs' hoặc 'kms'

    Returns:
        Danh sách KMSConfig
    """
    raw = data.get("kms_configs", data.get("kms", []))
    configs = []
    for k_data in raw:
        configs.append(KMSConfig(
            id=k_data.get("id", k_data.get("kms_id", "")),
            provider=KMSProvider(k_data.get("provider", "aws")),
            key_id=k_data.get("key_id", ""),
            region=k_data.get("region", ""),
            encryption_context=k_data.get("encryption_context", {}),
        ))
    return configs


def parse_configmap_refs(data: dict[str, Any]) -> list[ConfigMapRef]:
    """Parse danh sách ConfigMap references từ DSL dict.

    Args:
        data: DSL dict với key 'configmap_refs' hoặc 'configmaps'

    Returns:
        Danh sách ConfigMapRef
    """
    raw = data.get("configmap_refs", data.get("configmaps", []))
    refs = []
    for c_data in raw:
        refs.append(ConfigMapRef(
            id=c_data.get("id", c_data.get("configmap_id", "")),
            k8s_configmap=c_data.get("k8s_configmap", c_data.get("configmap", "")),
            mount_path=c_data.get("mount_path", ""),
            env_prefix=c_data.get("env_prefix", ""),
        ))
    return refs


def parse_to_ir(data: dict[str, Any]) -> EnvIR:
    """Parse DSL dict thành EnvIR.

    Args:
        data: DSL dict với env_configs, secret_configs, vault_configs, kms_configs

    Returns:
        EnvIR gom tập tất cả parsed data
    """
    return EnvIR(
        env_configs=parse_env_configs(data),
        secret_configs=parse_secret_configs(data),
        vault_configs=parse_vault_configs(data),
        kms_configs=parse_kms_configs(data),
        configmap_refs=parse_configmap_refs(data),
    )


__all__ = [
    "EnvIR",
    "parse_env_configs",
    "parse_secret_configs",
    "parse_vault_configs",
    "parse_kms_configs",
    "parse_configmap_refs",
    "parse_to_ir",
]
