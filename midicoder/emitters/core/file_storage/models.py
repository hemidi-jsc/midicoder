# coding: utf-8
"""
Mô-đun models cho File Storage & Media Processing Emitter (CP11).

Định nghĩa các dataclass biểu diễn:
- StorageBackend: Enum các backend (s3, local)
- TransformType: Enum các loại media transform (resize, thumbnail, transcode)
- StorageProfile: Profile storage với backend, bucket, region, tenant_isolation
- UploadPolicy: Policy upload với allowed types, max size, extensions
- MediaTransform: Cấu hình media processing (resize, thumbnail, transcode)
- FileStorageCollection: Collection chứa tất cả storage profiles, policies, transforms

KPI-029: Tenant Isolation - tenant_isolation=True mặc định
Obligation: UploadPolicy validation mandatory trên mọi file upload

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ===========================================================================
# Enums
# ===========================================================================


class StorageBackend(str, Enum):
    """Enum các backend storage được hỗ trợ."""
    S3 = "s3"
    LOCAL = "local"


class TransformType(str, Enum):
    """Enum các loại media transform được hỗ trợ."""
    RESIZE = "resize"
    THUMBNAIL = "thumbnail"
    TRANSCODE = "transcode"


# Mapping từ string sang enum
_BACKEND_MAP = {
    "s3": StorageBackend.S3,
    "local": StorageBackend.LOCAL,
}

_TRANSFORM_MAP = {
    "resize": TransformType.RESIZE,
    "thumbnail": TransformType.THUMBNAIL,
    "transcode": TransformType.TRANSCODE,
}


# ===========================================================================
# StorageProfile
# ===========================================================================


@dataclass
class StorageProfile:
    """
    Profile định nghĩa cấu hình storage backend.

    Attributes:
        name: Định danh duy nhất của profile
        backend_type: Backend storage (S3, LOCAL)
        bucket: Bucket name (bắt buộc nếu backend=S3)
        region: AWS region (cho S3)
        endpoint_url: Custom endpoint URL (cho MinIO/S3-compatible)
        access_key: Access key (optional, ưu tiên dùng env)
        secret_key: Secret key (optional, ưu tiên dùng env)
        tenant_isolation: Có enforce tenant isolation không (KPI-029)
        description: Mô tả profile
    """
    name: str
    backend_type: StorageBackend
    bucket: Optional[str] = None
    region: str = "us-east-1"
    endpoint_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    tenant_isolation: bool = True  # KPI-029: mặc định isolate
    description: str = ""

    def __post_init__(self):
        """
        Validation sau khi khởi tạo.

        Throw MidicoderError nếu:
        - Name rỗng (MDC-CP11-001)
        - Backend type không hợp lệ (MDC-CP11-002)
        - S3 không có bucket (MDC-CP11-003)
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Validate name không rỗng
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP11_EMPTY_PROFILE_NAME,
                detail="StorageProfile name không được để trống",
            )

        # Validate backend_type
        if self.backend_type not in StorageBackend:
            EM.raise_error(
                ErrorCode.CP11_INVALID_BACKEND_TYPE,
                profile_name=self.name,
                backend_type=str(self.backend_type),
            )

        # Validate S3 phải có bucket
        if self.backend_type == StorageBackend.S3:
            if not self.bucket or not self.bucket.strip():
                EM.raise_error(
                    ErrorCode.CP11_EMPTY_BUCKET_NAME,
                    profile_name=self.name,
                )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển profile sang dict format."""
        return {
            "name": self.name,
            "backend_type": self.backend_type.value,
            "bucket": self.bucket,
            "region": self.region,
            "endpoint_url": self.endpoint_url,
            "access_key": self.access_key,
            "secret_key": self.secret_key,
            "tenant_isolation": self.tenant_isolation,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StorageProfile":
        """Tạo StorageProfile từ dict."""
        backend_val = data.get("backend_type", "s3")
        backend = _BACKEND_MAP.get(backend_val, StorageBackend.S3)
        return cls(
            name=data.get("name", ""),
            backend_type=backend,
            bucket=data.get("bucket"),
            region=data.get("region", "us-east-1"),
            endpoint_url=data.get("endpoint_url"),
            access_key=data.get("access_key"),
            secret_key=data.get("secret_key"),
            tenant_isolation=data.get("tenant_isolation", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# UploadPolicy
# ===========================================================================


@dataclass
class UploadPolicy:
    """
    Policy cho file upload — enforce validation trên mọi file upload operation.

    Obligation: UploadPolicy validation mandatory — mỗi file upload PHẢI qua
    content-type check, size limit check, và extension check.

    Attributes:
        name: Định danh duy nhất của policy
        allowed_content_types: Danh sách content types được phép
        max_file_size: Kích thước tối đa (bytes). Phải > 0
        allowed_extensions: Danh sách extensions được phép
        default_storage_profile: Tên StorageProfile mặc định để lưu file
        description: Mô tả policy
    """
    name: str
    allowed_content_types: list[str] = field(default_factory=list)
    max_file_size: int = 10 * 1024 * 1024  # mặc định 10MB
    allowed_extensions: list[str] = field(default_factory=list)
    default_storage_profile: str = ""
    description: str = ""

    def __post_init__(self):
        """
        Validation sau khi khởi tạo — Obligation enforcement.

        Throw MidicoderError nếu:
        - Name rỗng (MDC-CP11-008)
        - allowed_content_types rỗng (MDC-CP11-004)
        - max_file_size <= 0 (MDC-CP11-005)
        - allowed_extensions rỗng (MDC-CP11-006)
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Validate name không rỗng
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP11_MISSING_POLICY,
                detail="UploadPolicy name không được để trống",
            )

        # Validate allowed_content_types không rỗng
        if not self.allowed_content_types:
            EM.raise_error(
                ErrorCode.CP11_INVALID_CONTENT_TYPE,
                policy_name=self.name,
                detail="allowed_content_types không được để trống",
            )

        # Validate max_file_size > 0
        if self.max_file_size <= 0:
            EM.raise_error(
                ErrorCode.CP11_FILE_SIZE_EXCEEDED,
                policy_name=self.name,
                max_file_size=self.max_file_size,
                detail="max_file_size phải lớn hơn 0",
            )

        # Validate allowed_extensions không rỗng
        if not self.allowed_extensions:
            EM.raise_error(
                ErrorCode.CP11_INVALID_EXTENSION,
                policy_name=self.name,
                detail="allowed_extensions không được để trống",
            )

    def validate_upload(
        self,
        content_type: str,
        file_size: int,
        extension: str,
    ) -> None:
        """
        Validate một file upload theo policy — Obligation enforcement tại runtime.

        Args:
            content_type: MIME type của file
            file_size: Kích thước file (bytes)
            extension: Extension của file (không có dấu chấm)

        Raises:
            MidicoderError: Nếu vi phạm policy
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Content-type check
        if content_type not in self.allowed_content_types:
            EM.raise_error(
                ErrorCode.CP11_INVALID_CONTENT_TYPE,
                policy_name=self.name,
                content_type=content_type,
                allowed=self.allowed_content_types,
            )

        # Size check
        if file_size > self.max_file_size:
            EM.raise_error(
                ErrorCode.CP11_FILE_SIZE_EXCEEDED,
                policy_name=self.name,
                file_size=file_size,
                max_size=self.max_file_size,
            )

        # Extension check
        if extension not in self.allowed_extensions:
            EM.raise_error(
                ErrorCode.CP11_INVALID_EXTENSION,
                policy_name=self.name,
                extension=extension,
                allowed=self.allowed_extensions,
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển policy sang dict format."""
        return {
            "name": self.name,
            "allowed_content_types": self.allowed_content_types,
            "max_file_size": self.max_file_size,
            "allowed_extensions": self.allowed_extensions,
            "default_storage_profile": self.default_storage_profile,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UploadPolicy":
        """Tạo UploadPolicy từ dict."""
        return cls(
            name=data.get("name", ""),
            allowed_content_types=data.get("allowed_content_types", []),
            max_file_size=data.get("max_file_size", 10 * 1024 * 1024),
            allowed_extensions=data.get("allowed_extensions", []),
            default_storage_profile=data.get("default_storage_profile", ""),
            description=data.get("description", ""),
        )


# ===========================================================================
# MediaTransform
# ===========================================================================


@dataclass
class MediaTransform:
    """
    Cấu hình cho media processing operations.

    Attributes:
        name: Định danh duy nhất của transform
        transform_type: Loại transform (RESIZE, THUMBNAIL, TRANSCODE)
        width: Width target (cho resize/thumbnail)
        height: Height target (cho resize/thumbnail)
        format: Output format (cho transcode)
        quality: Quality level (1-100), mặc định 80
        description: Mô tả transform
    """
    name: str
    transform_type: TransformType
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    quality: int = 80
    description: str = ""

    def __post_init__(self):
        """
        Validation sau khi khởi tạo.

        Throw MidicoderError nếu:
        - Name rỗng (MDC-CP11-009)
        - Transform type không hợp lệ (MDC-CP11-009)
        - Quality ngoài range 1-100 (MDC-CP11-009)
        - Resize/thumbnail không có width và height (MDC-CP11-009)
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Validate name không rỗng
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP11_TRANSFORM_INVALID_PARAM,
                detail="MediaTransform name không được để trống",
            )

        # Validate transform_type
        if self.transform_type not in TransformType:
            EM.raise_error(
                ErrorCode.CP11_TRANSFORM_INVALID_PARAM,
                transform_name=self.name,
                transform_type=str(self.transform_type),
            )

        # Validate quality range 1-100
        if self.quality < 1 or self.quality > 100:
            EM.raise_error(
                ErrorCode.CP11_TRANSFORM_INVALID_PARAM,
                transform_name=self.name,
                quality=self.quality,
                detail="quality phải trong range 1-100",
            )

        # Validate resize/thumbnail cần có width hoặc height
        if self.transform_type in (TransformType.RESIZE, TransformType.THUMBNAIL):
            if not self.width and not self.height:
                EM.raise_error(
                    ErrorCode.CP11_TRANSFORM_INVALID_PARAM,
                    transform_name=self.name,
                    detail="resize/thumbnail phải có width hoặc height",
                )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển transform sang dict format."""
        return {
            "name": self.name,
            "transform_type": self.transform_type.value,
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "quality": self.quality,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MediaTransform":
        """Tạo MediaTransform từ dict."""
        transform_val = data.get("transform_type", "resize")
        transform_type = _TRANSFORM_MAP.get(transform_val, TransformType.RESIZE)
        return cls(
            name=data.get("name", ""),
            transform_type=transform_type,
            width=data.get("width"),
            height=data.get("height"),
            format=data.get("format"),
            quality=data.get("quality", 80),
            description=data.get("description", ""),
        )


# ===========================================================================
# FileStorageCollection
# ===========================================================================


@dataclass
class FileStorageCollection:
    """
    Collection chứa tất cả storage profiles, upload policies, và media transforms.

    Attributes:
        profiles: Danh sách storage profiles
        policies: Danh sách upload policies
        transforms: Danh sách media transforms
    """
    profiles: list[StorageProfile] = field(default_factory=list)
    policies: list[UploadPolicy] = field(default_factory=list)
    transforms: list[MediaTransform] = field(default_factory=list)

    def add_profile(self, profile: StorageProfile) -> None:
        """Thêm profile vào collection."""
        self.profiles.append(profile)

    def add_policy(self, policy: UploadPolicy) -> None:
        """Thêm policy vào collection."""
        self.policies.append(policy)

    def add_transform(self, transform: MediaTransform) -> None:
        """Thêm transform vào collection."""
        self.transforms.append(transform)

    @property
    def total_count(self) -> int:
        """Tổng số profiles trong collection."""
        return len(self.profiles)

    def get_by_id(self, profile_name: str) -> Optional[StorageProfile]:
        """Tìm profile theo tên."""
        for profile in self.profiles:
            if profile.name == profile_name:
                return profile
        return None

    def s3_profiles(self) -> list[StorageProfile]:
        """Lọc các profiles dùng S3 backend."""
        return [p for p in self.profiles if p.backend_type == StorageBackend.S3]

    def local_profiles(self) -> list[StorageProfile]:
        """Lọc các profiles dùng Local backend."""
        return [p for p in self.profiles if p.backend_type == StorageBackend.LOCAL]

    def tenant_isolated_profiles(self) -> list[StorageProfile]:
        """Lọc các profiles có tenant isolation (KPI-029)."""
        return [p for p in self.profiles if p.tenant_isolation]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "profiles": [p.to_dict() for p in self.profiles],
            "policies": [pol.to_dict() for pol in self.policies],
            "transforms": [t.to_dict() for t in self.transforms],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileStorageCollection":
        """Tạo FileStorageCollection từ dict."""
        result = cls()
        result.profiles = [
            StorageProfile.from_dict(p) for p in data.get("profiles", [])
        ]
        result.policies = [
            UploadPolicy.from_dict(pol) for pol in data.get("policies", [])
        ]
        result.transforms = [
            MediaTransform.from_dict(t) for t in data.get("transforms", [])
        ]
        return result
