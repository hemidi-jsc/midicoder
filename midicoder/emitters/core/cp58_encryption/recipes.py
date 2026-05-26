# coding: utf-8
"""
Mô-đun recipes cho CP58 — Data Encryption at Rest.

Cung cấp các recipe để build EncryptionIR cho các use case phổ biến:
- aes256_field_encryption_recipe: Mã hóa từng field với AES-256-GCM
- table_encryption_recipe: Mã hóa toàn bộ bảng/cột với TDE
- key_rotation_recipe: Chính sách key rotation tự động
- compliance_encryption_recipe: Mã hóa tuân thủ HIPAA/SOX/PCI với audit

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp58_encryption.models import (
    EncryptionAlgorithm,
    EncryptionConfig,
    EncryptionKey,
    EncryptionPolicy,
    EncryptedField,
    KeyManagementType,
    KeyStatus,
)
from midicoder.emitters.core.cp58_encryption.parser import (
    EncryptionIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: EncryptionIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: EncryptionIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def aes256_field_encryption_recipe() -> RecipeOutput:
    """Recipe: Mã hóa từng field với AES-256-GCM.

    Áp dụng mã hóa per-field cho các trường nhạy cảm (SSN, card_number,
    medical_record) với AES-256-GCM và quản lý khóa local.
    Phù hợp cho ứng dụng cần mã hóa granular ở tầng ORM/model.

    - 1 config: AES-256-GCM, local key management
    - 3 encrypted fields: ssn, card_number, medical_record
    - 1 encryption key: active, local
    - Auto encrypt/decrypt: bật

    Returns:
        RecipeOutput chứa EncryptionIR
    """
    data = {
        "configs": [
            {
                "id": "aes256_field_config",
                "name": "AES-256-GCM Per-Field Encryption",
                "algorithm": "AES256_GCM",
                "key_size": 256,
                "mode": "GCM",
                "key_management": "local",
            }
        ],
        "fields": [
            {
                "id": "enc_ssn",
                "entity_id": "User",
                "field_name": "ssn",
                "algorithm": "AES256_GCM",
                "key_id": "key_aes256_main",
                "auto_encrypt": True,
                "auto_decrypt": True,
            },
            {
                "id": "enc_card_number",
                "entity_id": "PaymentMethod",
                "field_name": "card_number",
                "algorithm": "AES256_GCM",
                "key_id": "key_aes256_main",
                "auto_encrypt": True,
                "auto_decrypt": True,
            },
            {
                "id": "enc_medical_record",
                "entity_id": "Patient",
                "field_name": "medical_record",
                "algorithm": "AES256_GCM",
                "key_id": "key_aes256_main",
                "auto_encrypt": True,
                "auto_decrypt": True,
            },
        ],
        "keys": [
            {
                "id": "key_aes256_main",
                "name": "AES-256 Main Key",
                "algorithm": "AES256_GCM",
                "key_id": "arn:aws:kms:us-east-1:000000000000:key/main-aes256",
                "provider": "local",
                "status": "active",
            }
        ],
        "default_algorithm": "AES256_GCM",
        "default_key_management": "local",
        "enable_auto_encrypt": True,
        "enable_auto_decrypt": True,
        "enable_key_rotation": False,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="aes256_field_encryption_recipe",
        description="Mã hóa per-field với AES-256-GCM cho các trường nhạy cảm",
        ir=ir,
        raw_data=data,
    )


def table_encryption_recipe() -> RecipeOutput:
    """Recipe: Mã hóa toàn bộ bảng/cột với TDE.

    Áp dụng Transparent Data Encryption (TDE) ở tầng database,
    mã hóa toàn bộ bảng chứa dữ liệu nhạy cảm. Sử dụng AWS KMS
    cho key management với rotation tự động.

    - 1 config: AES-256-GCM, AWS KMS key management
    - 2 encrypted fields: toàn bộ bảng user_data và payment_data
    - 2 encryption keys: một active, một rotating
    - Auto encrypt/decrypt: bật

    Returns:
        RecipeOutput chứa EncryptionIR
    """
    data = {
        "configs": [
            {
                "id": "tde_table_config",
                "name": "Transparent Data Encryption — Table Level",
                "algorithm": "AES256_GCM",
                "key_size": 256,
                "mode": "GCM",
                "key_management": "aws_kms",
            }
        ],
        "fields": [
            {
                "id": "enc_user_table",
                "entity_id": "User",
                "field_name": "*ALL_COLUMNS*",
                "algorithm": "AES256_GCM",
                "key_id": "key_tde_active",
                "auto_encrypt": True,
                "auto_decrypt": True,
            },
            {
                "id": "enc_payment_table",
                "entity_id": "Payment",
                "field_name": "*ALL_COLUMNS*",
                "algorithm": "AES256_GCM",
                "key_id": "key_tde_active",
                "auto_encrypt": True,
                "auto_decrypt": True,
            },
        ],
        "keys": [
            {
                "id": "key_tde_active",
                "name": "TDE Active Key",
                "algorithm": "AES256_GCM",
                "key_id": "arn:aws:kms:us-east-1:000000000000:key/tde-active",
                "provider": "aws_kms",
                "status": "active",
            },
            {
                "id": "key_tde_rotating",
                "name": "TDE Rotating Key",
                "algorithm": "AES256_GCM",
                "key_id": "arn:aws:kms:us-east-1:000000000000:key/tde-previous",
                "provider": "aws_kms",
                "status": "rotating",
            },
        ],
        "default_algorithm": "AES256_GCM",
        "default_key_management": "aws_kms",
        "enable_auto_encrypt": True,
        "enable_auto_decrypt": True,
        "enable_key_rotation": True,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="table_encryption_recipe",
        description="Mã hóa toàn bộ bảng/cột với TDE và AWS KMS",
        ir=ir,
        raw_data=data,
    )


def key_rotation_recipe() -> RecipeOutput:
    """Recipe: Chính sách key rotation tự động.

    Thiết lập chính sách key rotation tự động với chu kỳ 90 ngày,
    sử dụng HashiCorp Vault cho key management. Bao gồm audit
    trail cho tất cả hoạt động xoay khóa.

    - 1 config: AES-256-GCM, HashiCorp Vault
    - 3 encryption keys: active, rotating, retired
    - 1 policy: key rotation 90 ngày, audit enabled

    Returns:
        RecipeOutput chứa EncryptionIR
    """
    data = {
        "configs": [
            {
                "id": "rotation_config",
                "name": "Automated Key Rotation Config",
                "algorithm": "AES256_GCM",
                "key_size": 256,
                "mode": "GCM",
                "key_management": "hashicorp_vault",
            }
        ],
        "fields": [],
        "keys": [
            {
                "id": "key_rotation_active",
                "name": "Active Rotation Key",
                "algorithm": "AES256_GCM",
                "key_id": "vault:secret/data/encryption/active",
                "provider": "hashicorp_vault",
                "status": "active",
            },
            {
                "id": "key_rotation_rotating",
                "name": "Rotating Key — decrypt only",
                "algorithm": "AES256_GCM",
                "key_id": "vault:secret/data/encryption/rotating",
                "provider": "hashicorp_vault",
                "status": "rotating",
            },
            {
                "id": "key_rotation_retired",
                "name": "Retired Key — legacy decrypt",
                "algorithm": "AES256_GCM",
                "key_id": "vault:secret/data/encryption/retired",
                "provider": "hashicorp_vault",
                "status": "retired",
            },
        ],
        "policies": [
            {
                "id": "rotation_policy",
                "name": "90-Day Key Rotation Policy",
                "at_rest": True,
                "in_transit": True,
                "algorithm": "AES256_GCM",
                "key_rotation_days": 90,
                "compliance_standards": ["SOC2"],
            }
        ],
        "default_algorithm": "AES256_GCM",
        "default_key_management": "hashicorp_vault",
        "enable_auto_encrypt": True,
        "enable_auto_decrypt": True,
        "enable_key_rotation": True,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="key_rotation_recipe",
        description="Chính sách key rotation tự động 90 ngày với HashiCorp Vault",
        ir=ir,
        raw_data=data,
    )


def compliance_encryption_recipe() -> RecipeOutput:
    """Recipe: Mã hóa tuân thủ HIPAA/SOX/PCI với audit.

    Cấu hình mã hóa hoàn chỉnh cho các tiêu chuẩn tuân thủ:
    HIPAA (sức khỏe), SOX (tài chính), PCI-DSS (thanh toán).
    Bao gồm cả mã hóa at-rest và in-transit với audit trail.

    - 2 configs: AES-256-GCM (at-rest), RSA-4096 (key wrapping)
    - 3 encrypted fields: patient_record, financial_report, card_token
    - 2 encryption keys: AES-256 + RSA-4096
    - 1 policy: đa tiêu chuẩn (HIPAA, SOX, PCI-DSS), rotation 30 ngày

    Returns:
        RecipeOutput chứa EncryptionIR
    """
    data = {
        "configs": [
            {
                "id": "compliance_aes_config",
                "name": "Compliance AES-256-GCM At-Rest",
                "algorithm": "AES256_GCM",
                "key_size": 256,
                "mode": "GCM",
                "key_management": "aws_kms",
            },
            {
                "id": "compliance_rsa_config",
                "name": "Compliance RSA-4096 Key Wrapping",
                "algorithm": "RSA4096",
                "key_size": 4096,
                "mode": "PKCS1",
                "key_management": "aws_kms",
            },
        ],
        "fields": [
            {
                "id": "enc_patient_record",
                "entity_id": "Patient",
                "field_name": "medical_record",
                "algorithm": "AES256_GCM",
                "key_id": "key_compliance_aes",
                "auto_encrypt": True,
                "auto_decrypt": True,
            },
            {
                "id": "enc_financial_report",
                "entity_id": "FinancialReport",
                "field_name": "revenue_data",
                "algorithm": "AES256_GCM",
                "key_id": "key_compliance_aes",
                "auto_encrypt": True,
                "auto_decrypt": True,
            },
            {
                "id": "enc_card_token",
                "entity_id": "PaymentMethod",
                "field_name": "card_token",
                "algorithm": "AES256_GCM",
                "key_id": "key_compliance_aes",
                "auto_encrypt": True,
                "auto_decrypt": True,
            },
        ],
        "keys": [
            {
                "id": "key_compliance_aes",
                "name": "Compliance AES-256 Key",
                "algorithm": "AES256_GCM",
                "key_id": "arn:aws:kms:us-east-1:000000000000:key/compliance-aes256",
                "provider": "aws_kms",
                "status": "active",
            },
            {
                "id": "key_compliance_rsa",
                "name": "Compliance RSA-4096 Key Wrapping",
                "algorithm": "RSA4096",
                "key_id": "arn:aws:kms:us-east-1:000000000000:key/compliance-rsa4096",
                "provider": "aws_kms",
                "status": "active",
            },
        ],
        "policies": [
            {
                "id": "compliance_policy",
                "name": "Multi-Standard Compliance Encryption",
                "at_rest": True,
                "in_transit": True,
                "algorithm": "AES256_GCM",
                "key_rotation_days": 30,
                "compliance_standards": ["HIPAA", "SOX", "PCI-DSS"],
            }
        ],
        "default_algorithm": "AES256_GCM",
        "default_key_management": "aws_kms",
        "enable_auto_encrypt": True,
        "enable_auto_decrypt": True,
        "enable_key_rotation": True,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="compliance_encryption_recipe",
        description="Mã hóa tuân thủ HIPAA/SOX/PCI-DSS với audit trail và rotation 30 ngày",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "aes256_field_encryption_recipe",
    "table_encryption_recipe",
    "key_rotation_recipe",
    "compliance_encryption_recipe",
]
