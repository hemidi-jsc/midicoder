# coding: utf-8
"""
Mô-đun models cho CP56 — Environment & Secret Management.

Định nghĩa các dataclass biểu diễn:
- EnvName: Môi trường (dev, staging, prod)
- SecretType: Loại secret storage (vault, aws_kms, gcp_kms, local)
- KMSProvider: Provider KMS (aws, gcp, azure)
- EnvConfig: Cấu hình biến môi trường theo môi trường
- SecretConfig: Cấu hình quản lý secret (Vault, KMS, local)
- VaultConfig: Cấu hình HashiCorp Vault
- KMSConfig: Cấu hình Key Management Service (AWS/GCP/Azure)
- ConfigMapRef: Tham chiếu Kubernetes ConfigMap

KPI: CP Obligations Coverage (>= 2 obligations cho CP56).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class EnvName(str, Enum):
    """Tên môi trường triển khai.

    - DEV: Môi trường phát triển local
    - STAGING: Môi trường staging/preview
    - PROD: Môi trường production
    """
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class SecretType(str, Enum):
    """Loại cơ chế lưu trữ secret.

    - VAULT: HashiCorp Vault
    - AWS_KMS: AWS Key Management Service
    - GCP_KMS: Google Cloud KMS
    - LOCAL: Lưu local (.env file)
    """
    VAULT = "vault"
    AWS_KMS = "aws_kms"
    GCP_KMS = "gcp_kms"
    LOCAL = "local"


class KMSProvider(str, Enum):
    """Provider Key Management Service.

    - AWS: AWS KMS
    - GCP: Google Cloud KMS
    - AZURE: Azure Key Vault
    """
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


# ===========================================================================
# EnvConfig
# ===========================================================================


@dataclass
class EnvConfig:
    """Cấu hình biến môi trường cho một môi trường cụ thể.

    Quản lý các biến môi trường theo từng môi trường triển khai,
    bao gồm các giá trị mặc định, biến bắt buộc, và cấu hình export.

    Attributes:
        id: ID duy nhất của cấu hình môi trường
        name: Tên hiển thị của cấu hình
        env_name: Tên môi trường (dev|staging|prod)
        variables: Danh sách các biến môi trường {key: value}
        required_vars: Danh sách các biến bắt buộc phải có giá trị
        export_to_dotenv: Có xuất ra file .env không
    """
    id: str
    name: str
    env_name: EnvName = EnvName.DEV
    variables: dict[str, str] = field(default_factory=dict)
    required_vars: list[str] = field(default_factory=list)
    export_to_dotenv: bool = True

    def __post_init__(self) -> None:
        """Validate EnvConfig sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.CP56_ENV_CONFIG_INVALID,
                reason="id bắt buộc và không được để trống",
            )
        if not self.name or not self.name.strip():
            raise EM.raise_error(
                ErrorCode.CP56_ENV_CONFIG_INVALID,
                reason="name bắt buộc và không được để trống",
            )

    def get_required_missing(self) -> list[str]:
        """Trả về danh sách các biến bắt buộc chưa có giá trị.

        Returns:
            Danh sách tên biến bắt buộc chưa được định nghĩa
        """
        return [v for v in self.required_vars if v not in self.variables]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển EnvConfig sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "env_name": self.env_name.value,
            "variables": dict(self.variables),
            "required_vars": list(self.required_vars),
            "export_to_dotenv": self.export_to_dotenv,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnvConfig":
        """Tạo EnvConfig từ dict."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            env_name=EnvName(data.get("env_name", "dev")),
            variables=data.get("variables", {}),
            required_vars=data.get("required_vars", []),
            export_to_dotenv=data.get("export_to_dotenv", True),
        )


# ===========================================================================
# SecretConfig
# ===========================================================================


@dataclass
class SecretConfig:
    """Cấu hình quản lý secret cho một loại secret.

    Định nghĩa cách lưu trữ và truy cập secret, bao gồm loại
    storage backend, đường dẫn truy cập, và chính sách bảo mật.

    Attributes:
        id: ID duy nhất của cấu hình secret
        name: Tên hiển thị
        secret_type: Loại cơ chế lưu trữ secret
        key_path: Đường dẫn khóa/secret trong backend
        engine_version: Phiên bản engine (cho Vault KV v1/v2)
        path: Đường dẫn mount/access trong backend
        access_policy: Chính sách truy cập (read-only, read-write, admin)
    """
    id: str
    name: str
    secret_type: SecretType = SecretType.LOCAL
    key_path: str = ""
    engine_version: int = 2
    path: str = ""
    access_policy: str = "read-only"

    def __post_init__(self) -> None:
        """Validate SecretConfig sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.CP56_SECRET_CONFIG_INVALID,
                reason="id bắt buộc và không được để trống",
            )
        if self.engine_version not in (1, 2):
            raise EM.raise_error(
                ErrorCode.CP56_SECRET_CONFIG_INVALID,
                reason=f"engine_version phải là 1 hoặc 2, nhận được: {self.engine_version}",
            )

    def is_remote(self) -> bool:
        """Trả về True nếu secret được lưu ở backend từ xa."""
        return self.secret_type != SecretType.LOCAL

    def to_dict(self) -> dict[str, Any]:
        """Chuyển SecretConfig sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "secret_type": self.secret_type.value,
            "key_path": self.key_path,
            "engine_version": self.engine_version,
            "path": self.path,
            "access_policy": self.access_policy,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SecretConfig":
        """Tạo SecretConfig từ dict."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            secret_type=SecretType(data.get("secret_type", "local")),
            key_path=data.get("key_path", ""),
            engine_version=data.get("engine_version", 2),
            path=data.get("path", ""),
            access_policy=data.get("access_policy", "read-only"),
        )


# ===========================================================================
# VaultConfig
# ===========================================================================


@dataclass
class VaultConfig:
    """Cấu hình HashiCorp Vault.

    Định nghĩa kết nối và cấu hình cho HashiCorp Vault, bao gồm
    địa chỉ server, phiên bản engine KV, các đường dẫn mount,
    và cấu hình tự động xác thực.

    Attributes:
        id: ID duy nhất của Vault config
        address: Địa chỉ Vault server (http/https://host:port)
        engine_version: Phiên bản KV engine (1 hoặc 2)
        paths: Danh sách các đường dẫn KV mount
        auto_auth: Cấu hình tự động xác thực {type, mount_role, ...}
    """
    id: str
    address: str = ""
    engine_version: int = 2
    paths: list[str] = field(default_factory=list)
    auto_auth: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate VaultConfig sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.CP56_VAULT_CONFIG_INVALID,
                reason="id bắt buộc và không được để trống",
            )
        if not self.address or not self.address.strip():
            raise EM.raise_error(
                ErrorCode.CP56_VAULT_CONFIG_INVALID,
                reason="address bắt buộc cho Vault config",
            )
        if self.engine_version not in (1, 2):
            raise EM.raise_error(
                ErrorCode.CP56_VAULT_CONFIG_INVALID,
                reason=f"engine_version phải là 1 hoặc 2, nhận được: {self.engine_version}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển VaultConfig sang dict."""
        return {
            "id": self.id,
            "address": self.address,
            "engine_version": self.engine_version,
            "paths": list(self.paths),
            "auto_auth": dict(self.auto_auth),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VaultConfig":
        """Tạo VaultConfig từ dict."""
        return cls(
            id=data["id"],
            address=data.get("address", ""),
            engine_version=data.get("engine_version", 2),
            paths=data.get("paths", []),
            auto_auth=data.get("auto_auth", {}),
        )


# ===========================================================================
# KMSConfig
# ===========================================================================


@dataclass
class KMSConfig:
    """Cấu hình Key Management Service.

    Định nghĩa cấu hình KMS (AWS/GCP/Azure) cho việc mã hóa
    và quản lý khóa mật mã.

    Attributes:
        id: ID duy nhất của KMS config
        provider: Provider KMS (aws, gcp, azure)
        key_id: ID của khóa KMS
        region: Khu vực/cloud region
        encryption_context: Bối cảnh mã hóa thêm (key-value pairs)
    """
    id: str
    provider: KMSProvider = KMSProvider.AWS
    key_id: str = ""
    region: str = ""
    encryption_context: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate KMSConfig sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.CP56_KMS_CONFIG_INVALID,
                reason="id bắt buộc và không được để trống",
            )
        if not self.key_id or not self.key_id.strip():
            raise EM.raise_error(
                ErrorCode.CP56_KMS_CONFIG_INVALID,
                reason="key_id bắt buộc cho KMS config",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển KMSConfig sang dict."""
        return {
            "id": self.id,
            "provider": self.provider.value,
            "key_id": self.key_id,
            "region": self.region,
            "encryption_context": dict(self.encryption_context),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KMSConfig":
        """Tạo KMSConfig từ dict."""
        return cls(
            id=data["id"],
            provider=KMSProvider(data.get("provider", "aws")),
            key_id=data.get("key_id", ""),
            region=data.get("region", ""),
            encryption_context=data.get("encryption_context", {}),
        )


# ===========================================================================
# ConfigMapRef
# ===========================================================================


@dataclass
class ConfigMapRef:
    """Tham chiếu Kubernetes ConfigMap.

    Ánh xạ ConfigMap của Kubernetes đến mount path và
    tiền tố biến môi trường khi inject vào container.

    Attributes:
        id: ID duy nhất của ConfigMap ref
        k8s_configmap: Tên ConfigMap trong Kubernetes
        mount_path: Đường dẫn mount trong container
        env_prefix: Tiền tố biến môi trường khi inject
    """
    id: str
    k8s_configmap: str = ""
    mount_path: str = ""
    env_prefix: str = ""

    def __post_init__(self) -> None:
        """Validate ConfigMapRef sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.CP56_CONFIGMAP_REF_INVALID,
                reason="id bắt buộc và không được để trống",
            )
        if not self.k8s_configmap or not self.k8s_configmap.strip():
            raise EM.raise_error(
                ErrorCode.CP56_CONFIGMAP_REF_INVALID,
                reason="k8s_configmap bắt buộc cho ConfigMap ref",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ConfigMapRef sang dict."""
        return {
            "id": self.id,
            "k8s_configmap": self.k8s_configmap,
            "mount_path": self.mount_path,
            "env_prefix": self.env_prefix,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfigMapRef":
        """Tạo ConfigMapRef từ dict."""
        return cls(
            id=data["id"],
            k8s_configmap=data.get("k8s_configmap", ""),
            mount_path=data.get("mount_path", ""),
            env_prefix=data.get("env_prefix", ""),
        )
