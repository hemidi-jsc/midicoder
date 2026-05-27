# coding: utf-8
"""
Mô-đun recipes cho CP56 — Environment & Secret Management.

Cung cấp các recipe để build EnvIR cho các use case phổ biến:
- dev_env_recipe: Cấu hình môi trường phát triển local (.env file)
- prod_env_recipe: Cấu hình production với Vault + KMS
- vault_recipe: HashiCorp Vault setup với KV v2 engine
- aws_kms_recipe: AWS KMS với envelope encryption

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp56_env_secrets.parser import (
    EnvIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: EnvIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: EnvIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def dev_env_recipe() -> RecipeOutput:
    """Recipe: Cấu hình môi trường phát triển local.

    - 1 env config (dev)
    - Local .env file cho biến môi trường
    - Secret type: local
    - Export ra .env file

    Returns:
        RecipeOutput chứa EnvIR
    """
    data = {
        "env_configs": [
            {
                "id": "dev_env",
                "name": "Development Environment",
                "env_name": "dev",
                "variables": {
                    "APP_NAME": "myapp-dev",
                    "APP_ENV": "development",
                    "DEBUG": "true",
                    "LOG_LEVEL": "debug",
                    "DATABASE_URL": "sqlite:///./dev.db",
                    "REDIS_URL": "redis://localhost:6379/0",
                    "SECRET_KEY": "dev-secret-key-change-me",
                    "CORS_ORIGINS": "http://localhost:3000,http://localhost:8080",
                },
                "required_vars": [
                    "SECRET_KEY",
                    "DATABASE_URL",
                ],
                "export_to_dotenv": True,
            }
        ],
        "secret_configs": [
            {
                "id": "dev_secrets",
                "name": "Development Secrets",
                "secret_type": "local",
                "key_path": "",
                "engine_version": 2,
                "path": "",
                "access_policy": "read-write",
            }
        ],
        "vault_configs": [],
        "kms_configs": [],
        "configmap_refs": [],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="dev_env_recipe",
        description="Môi trường phát triển local — .env file, local secrets",
        ir=ir,
        raw_data=data,
    )


def prod_env_recipe() -> RecipeOutput:
    """Recipe: Cấu hình production với Vault + KMS.

    - 3 env configs (dev, staging, prod)
    - HashiCorp Vault cho secret management
    - AWS KMS cho encryption
    - Kubernetes ConfigMap refs
    - Chính sách truy cập nghiêm ngặt

    Returns:
        RecipeOutput chứa EnvIR
    """
    data = {
        "env_configs": [
            {
                "id": "dev_env",
                "name": "Development Environment",
                "env_name": "dev",
                "variables": {
                    "APP_NAME": "myapp-dev",
                    "APP_ENV": "development",
                    "DEBUG": "true",
                    "LOG_LEVEL": "debug",
                },
                "required_vars": [
                    "SECRET_KEY",
                    "DATABASE_URL",
                ],
                "export_to_dotenv": True,
            },
            {
                "id": "staging_env",
                "name": "Staging Environment",
                "env_name": "staging",
                "variables": {
                    "APP_NAME": "myapp-staging",
                    "APP_ENV": "staging",
                    "DEBUG": "false",
                    "LOG_LEVEL": "info",
                },
                "required_vars": [
                    "SECRET_KEY",
                    "DATABASE_URL",
                    "VAULT_ADDR",
                ],
                "export_to_dotenv": False,
            },
            {
                "id": "prod_env",
                "name": "Production Environment",
                "env_name": "prod",
                "variables": {
                    "APP_NAME": "myapp-prod",
                    "APP_ENV": "production",
                    "DEBUG": "false",
                    "LOG_LEVEL": "warning",
                },
                "required_vars": [
                    "SECRET_KEY",
                    "DATABASE_URL",
                    "VAULT_ADDR",
                    "KMS_KEY_ID",
                ],
                "export_to_dotenv": False,
            },
        ],
        "secret_configs": [
            {
                "id": "vault_secrets",
                "name": "Vault Managed Secrets",
                "secret_type": "vault",
                "key_path": "secret/data/app",
                "engine_version": 2,
                "path": "secret",
                "access_policy": "read-only",
            },
            {
                "id": "kms_encrypted_secrets",
                "name": "KMS Encrypted Secrets",
                "secret_type": "aws_kms",
                "key_path": "arn:aws:kms:us-east-1:123456789:key/abc-123",
                "engine_version": 2,
                "path": "",
                "access_policy": "read-only",
            },
        ],
        "vault_configs": [
            {
                "id": "prod_vault",
                "address": "https://vault.production.internal:8200",
                "engine_version": 2,
                "paths": [
                    "secret/data/app",
                    "secret/data/database",
                    "secret/data/api-keys",
                ],
                "auto_auth": {
                    "type": "kubernetes",
                    "mount_role": "app-role",
                    "token_reviewer_jwt": "/var/run/secrets/kubernetes.io/serviceaccount/token",
                },
            }
        ],
        "kms_configs": [
            {
                "id": "prod_kms",
                "provider": "aws",
                "key_id": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
                "region": "us-east-1",
                "encryption_context": {
                    "purpose": "env-secret-encryption",
                    "environment": "production",
                },
            }
        ],
        "configmap_refs": [
            {
                "id": "app_configmap",
                "k8s_configmap": "app-config",
                "mount_path": "/etc/config",
                "env_prefix": "APP_",
            },
            {
                "id": "infra_configmap",
                "k8s_configmap": "infra-config",
                "mount_path": "/etc/infra",
                "env_prefix": "INFRA_",
            },
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="prod_env_recipe",
        description="Production — 3 environments, Vault + KMS, ConfigMap refs",
        ir=ir,
        raw_data=data,
    )


def vault_recipe() -> RecipeOutput:
    """Recipe: HashiCorp Vault setup với KV v2 engine.

    - Vault config với KV v2 engine
    - Kubernetes auto-auth
    - Các path mount cho secret namespaces
    - Vault secret config

    Returns:
        RecipeOutput chứa EnvIR
    """
    data = {
        "env_configs": [],
        "secret_configs": [
            {
                "id": "vault_app_secrets",
                "name": "Application Secrets in Vault",
                "secret_type": "vault",
                "key_path": "secret/data/app",
                "engine_version": 2,
                "path": "secret",
                "access_policy": "read-only",
            },
            {
                "id": "vault_db_secrets",
                "name": "Database Credentials in Vault",
                "secret_type": "vault",
                "key_path": "secret/data/database",
                "engine_version": 2,
                "path": "secret",
                "access_policy": "read-only",
            },
        ],
        "vault_configs": [
            {
                "id": "primary_vault",
                "address": "https://vault.example.com:8200",
                "engine_version": 2,
                "paths": [
                    "secret/data/app",
                    "secret/data/database",
                    "secret/data/api-keys",
                    "secret/data/certificates",
                ],
                "auto_auth": {
                    "type": "kubernetes",
                    "mount_role": "app-role",
                    "token_reviewer_jwt": "/var/run/secrets/kubernetes.io/serviceaccount/token",
                    "ca_cert": "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                },
            },
            {
                "id": "dev_vault",
                "address": "http://vault.dev.local:8200",
                "engine_version": 2,
                "paths": [
                    "secret/data/app",
                ],
                "auto_auth": {
                    "type": "token",
                    "token": "${VAULT_TOKEN}",
                },
            },
        ],
        "kms_configs": [],
        "configmap_refs": [],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="vault_recipe",
        description="HashiCorp Vault — KV v2 engine, Kubernetes auto-auth, multiple paths",
        ir=ir,
        raw_data=data,
    )


def aws_kms_recipe() -> RecipeOutput:
    """Recipe: AWS KMS với envelope encryption.

    - AWS KMS config với envelope encryption
    - Encryption context cho audit trail
    - KMS secret config

    Returns:
        RecipeOutput chứa EnvIR
    """
    data = {
        "env_configs": [
            {
                "id": "kms_prod_env",
                "name": "KMS Production Environment",
                "env_name": "prod",
                "variables": {
                    "AWS_REGION": "us-east-1",
                    "KMS_KEY_ID": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
                    "APP_ENV": "production",
                    "DEBUG": "false",
                },
                "required_vars": [
                    "KMS_KEY_ID",
                    "AWS_REGION",
                ],
                "export_to_dotenv": False,
            }
        ],
        "secret_configs": [
            {
                "id": "aws_kms_secrets",
                "name": "AWS KMS Encrypted Secrets",
                "secret_type": "aws_kms",
                "key_path": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
                "engine_version": 2,
                "path": "",
                "access_policy": "read-only",
            }
        ],
        "vault_configs": [],
        "kms_configs": [
            {
                "id": "aws_kms_primary",
                "provider": "aws",
                "key_id": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
                "region": "us-east-1",
                "encryption_context": {
                    "purpose": "envelope-encryption",
                    "application": "midicoder-ce",
                    "environment": "production",
                    "owner": "platform-team",
                },
            },
            {
                "id": "aws_kms_staging",
                "provider": "aws",
                "key_id": "arn:aws:kms:us-west-2:123456789012:key/87654321-4321-4321-4321-210987654321",
                "region": "us-west-2",
                "encryption_context": {
                    "purpose": "envelope-encryption",
                    "application": "midicoder-ce",
                    "environment": "staging",
                    "owner": "platform-team",
                },
            },
        ],
        "configmap_refs": [],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="aws_kms_recipe",
        description="AWS KMS — Envelope encryption, multi-region, encryption context",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "dev_env_recipe",
    "prod_env_recipe",
    "vault_recipe",
    "aws_kms_recipe",
]
