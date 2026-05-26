# coding: utf-8
"""
Mô-đun models cho CP58 — Data Encryption at Rest.

Định nghĩa các dataclass biểu diễn:
- EncryptionAlgorithm: Loại thuật toán mã hóa (AES256_GCM, ChaCha20, RSA4096)
- KeyManagementType: Loại hệ thống quản lý khóa (local, AWS KMS, GCP KMS, Azure Key Vault, HashiCorp Vault)
- KeyStatus: Trạng thái khóa (active, rotating, retired)
- EncryptionConfig: Cấu hình mã hóa tổng thể
- EncryptedField: Trường dữ liệu được mã hóa từng field
- EncryptionKey: Khóa mã hóa với vòng đời quản lý
- EncryptionPolicy: Chính sách mã hóa với compliance standards

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP58).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class EncryptionAlgorithm(str, Enum):
    """Loại thuật toán mã hóa.

    - AES256_GCM: AES-256 trong chế độ GCM (Authenticated Encryption)
    - CHACHA20: ChaCha20-Poly1305 (Authenticated Encryption)
    - RSA4096: RSA-4096 (Asymmetric, dùng cho key wrapping)
    """
    AES256_GCM = "AES256_GCM"
    CHACHA20 = "ChaCha20"
    RSA4096 = "RSA4096"


class KeyManagementType(str, Enum):
    """Loại hệ thống quản lý khóa.

    - LOCAL: Quản lý khóa tại chỗ (file/env)
    - AWS_KMS: AWS Key Management Service
    - GCP_KMS: Google Cloud Key Management
    - AZURE_KEYVAULT: Azure Key Vault
    - HASHICORP_VAULT: HashiCorp Vault
    """
    LOCAL = "local"
    AWS_KMS = "aws_kms"
    GCP_KMS = "gcp_kms"
    AZURE_KEYVAULT = "azure_keyvault"
    HASHICORP_VAULT = "hashicorp_vault"


class KeyStatus(str, Enum):
    """Trạng thái khóa mã hóa.

    State machine: active → rotating → retired

    - ACTIVE: Khóa đang được sử dụng cho cả encrypt và decrypt
    - ROTATING: Khóa đang trong quá trình rotation (chỉ decrypt, không encrypt mới)
    - RETIRED: Khóa đã nghỉ hưu (chỉ dùng để decrypt dữ liệu cũ)
    """
    ACTIVE = "active"
    ROTATING = "rotating"
    RETIRED = "retired"


# ===========================================================================
# EncryptionConfig
# ===========================================================================


@dataclass
class EncryptionConfig:
    """Cấu hình mã hóa tổng thể.

    Xác định thuật toán, kích thước khóa, chế độ hoạt động,
    và hệ thống quản lý khóa cho một scope cụ thể.

    Attributes:
        id: ID duy nhất của cấu hình
        name: Tên mô tả của cấu hình
        algorithm: Thuật toán mã hóa được sử dụng
        key_size: Kích thước khóa (bit)
        mode: Chế độ hoạt động (GCM, CTR, CBC, v.v.)
        key_management: Hệ thống quản lý khóa
    """
    id: str
    name: str
    algorithm: EncryptionAlgorithm
    key_size: int = 256
    mode: str = "GCM"
    key_management: KeyManagementType = KeyManagementType.LOCAL

    def __post_init__(self) -> None:
        """Validate cấu hình sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.CP58_ENCRYPTION_CONFIG_NOT_FOUND,
                reason="id bắt buộc và không được để trống",
            )
        if self.key_size < 128:
            raise EM.raise_error(
                ErrorCode.CP58_INVALID_ENCRYPTION_CONFIG,
                reason=f"key_size phải >= 128 bit, nhận được: {self.key_size}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển EncryptionConfig sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "algorithm": self.algorithm.value,
            "key_size": self.key_size,
            "mode": self.mode,
            "key_management": self.key_management.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EncryptionConfig":
        """Tạo EncryptionConfig từ dict."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            algorithm=EncryptionAlgorithm(data.get("algorithm", "AES256_GCM")),
            key_size=data.get("key_size", 256),
            mode=data.get("mode", "GCM"),
            key_management=KeyManagementType(data.get("key_management", "local")),
        )


# ===========================================================================
# EncryptedField
# ===========================================================================


@dataclass
class EncryptedField:
    """Trường dữ liệu được mã hóa.

    Xác định một field cụ thể trong entity cần được mã hóa,
    cùng với thuật toán, khóa, và chính sách auto encrypt/decrypt.

    Attributes:
        id: ID duy nhất của encrypted field
        entity_id: ID của entity chứa field này
        field_name: Tên field cần mã hóa
        algorithm: Thuật toán mã hóa cho field
        key_id: ID của khóa mã hóa được sử dụng
        auto_encrypt: Tự động mã hóa khi write
        auto_decrypt: Tự động giải mã khi read
    """
    id: str
    entity_id: str
    field_name: str
    algorithm: EncryptionAlgorithm
    key_id: str
    auto_encrypt: bool = True
    auto_decrypt: bool = True

    def __post_init__(self) -> None:
        """Validate encrypted field sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.CP58_ENCRYPTED_FIELD_NOT_FOUND,
                reason="id bắt buộc và không được để trống",
            )
        if not self.field_name or not self.field_name.strip():
            raise EM.raise_error(
                ErrorCode.CP58_ENCRYPTED_FIELD_NOT_FOUND,
                reason="field_name bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển EncryptedField sang dict."""
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "field_name": self.field_name,
            "algorithm": self.algorithm.value,
            "key_id": self.key_id,
            "auto_encrypt": self.auto_encrypt,
            "auto_decrypt": self.auto_decrypt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EncryptedField":
        """Tạo EncryptedField từ dict."""
        return cls(
            id=data["id"],
            entity_id=data.get("entity_id", ""),
            field_name=data.get("field_name", ""),
            algorithm=EncryptionAlgorithm(data.get("algorithm", "AES256_GCM")),
            key_id=data.get("key_id", ""),
            auto_encrypt=data.get("auto_encrypt", True),
            auto_decrypt=data.get("auto_decrypt", True),
        )


# ===========================================================================
# EncryptionKey
# ===========================================================================


@dataclass
class EncryptionKey:
    """Khóa mã hóa với vòng đời quản lý.

    Đại diện cho một khóa mã hóa, bao gồm thuật toán, provider,
    thời gian tạo, thời gian rotation, và trạng thái hiện tại.

    State machine: active → rotating → retired

    Attributes:
        id: ID duy nhất của khóa
        name: Tên mô tả của khóa
        algorithm: Thuật toán mã hóa của khóa
        key_id: Key identifier từ provider (vd: AWS KMS Key ARN)
        provider: Provider quản lý khóa
        created_at: Thời điểm tạo khóa
        rotated_at: Thời điểm rotation lần cuối
        status: Trạng thái hiện tại của khóa
    """
    id: str
    name: str
    algorithm: EncryptionAlgorithm
    key_id: str
    provider: KeyManagementType
    created_at: datetime | None = None
    rotated_at: datetime | None = None
    status: KeyStatus = KeyStatus.ACTIVE

    def __post_init__(self) -> None:
        """Validate encryption key sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.CP58_ENCRYPTION_KEY_NOT_FOUND,
                reason="id bắt buộc và không được để trống",
            )
        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now

    @property
    def is_usable(self) -> bool:
        """Trả về True nếu khóa có thể dùng để encrypt."""
        return self.status == KeyStatus.ACTIVE

    @property
    def can_decrypt(self) -> bool:
        """Trả về True nếu khóa có thể dùng để decrypt."""
        return self.status in (KeyStatus.ACTIVE, KeyStatus.ROTATING)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển EncryptionKey sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "algorithm": self.algorithm.value,
            "key_id": self.key_id,
            "provider": self.provider.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "rotated_at": self.rotated_at.isoformat() if self.rotated_at else None,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EncryptionKey":
        """Tạo EncryptionKey từ dict."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            algorithm=EncryptionAlgorithm(data.get("algorithm", "AES256_GCM")),
            key_id=data.get("key_id", ""),
            provider=KeyManagementType(data.get("provider", "local")),
            status=KeyStatus(data.get("status", "active")),
        )


# ===========================================================================
# EncryptionPolicy
# ===========================================================================


@dataclass
class EncryptionPolicy:
    """Chính sách mã hóa với compliance standards.

    Xác định chính sách mã hóa bao gồm mã hóa at-rest, in-transit,
    thuật toán, chu kỳ rotation, và các tiêu chuẩn tuân thủ.

    Attributes:
        id: ID duy nhất của chính sách
        name: Tên mô tả của chính sách
        at_rest: Có mã hóa dữ liệu at-rest không
        in_transit: Có mã hóa dữ liệu in-transit không
        algorithm: Thuật toán mặc định
        key_rotation_days: Số ngày giữa các lần rotation
        compliance_standards: Danh sách tiêu chuẩn tuân thủ (HIPAA, SOX, PCI-DSS)
    """
    id: str
    name: str
    at_rest: bool = True
    in_transit: bool = True
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES256_GCM
    key_rotation_days: int = 90
    compliance_standards: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate encryption policy sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.CP58_ENCRYPTION_POLICY_NOT_FOUND,
                reason="id bắt buộc và không được để trống",
            )
        if self.key_rotation_days < 1:
            raise EM.raise_error(
                ErrorCode.CP58_INVALID_ENCRYPTION_CONFIG,
                reason=f"key_rotation_days phải > 0, nhận được: {self.key_rotation_days}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển EncryptionPolicy sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "at_rest": self.at_rest,
            "in_transit": self.in_transit,
            "algorithm": self.algorithm.value,
            "key_rotation_days": self.key_rotation_days,
            "compliance_standards": self.compliance_standards,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EncryptionPolicy":
        """Tạo EncryptionPolicy từ dict."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            at_rest=data.get("at_rest", True),
            in_transit=data.get("in_transit", True),
            algorithm=EncryptionAlgorithm(data.get("algorithm", "AES256_GCM")),
            key_rotation_days=data.get("key_rotation_days", 90),
            compliance_standards=data.get("compliance_standards", []),
        )
