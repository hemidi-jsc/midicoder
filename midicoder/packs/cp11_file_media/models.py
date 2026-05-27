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
# CDNIntegration (AWS CloudFront)
# ===========================================================================


@dataclass
class CDNIntegration:
    """
    Cấu hình CDN integration — AWS CloudFront.

    Scope: chỉ AWS CloudFront (không hỗ trợ Cloudflare, Akamai).

    Attributes:
        name: Định danh duy nhất của CDN config
        distribution_id: CloudFront distribution ID
        domain: CloudFront domain (e.g., d1234.cloudfront.net)
        origin_bucket: S3 bucket origin
        origin_access_identity: CloudFront OAI (Origin Access Identity) S3 canonical UID
        signed_url: Có dùng signed URL (CloudFront signed cookies URLs) không
        default_ttl: Default TTL (giây), mặc định 86400 (24h)
        max_ttl: Max TTL (giây), mặc định 31536000 (1 năm)
        behavior_path: Path pattern cho cache behavior (mặc định /*)
    """
    name: str = "default"
    distribution_id: Optional[str] = None
    domain: Optional[str] = None
    origin_bucket: Optional[str] = None
    origin_access_identity: Optional[str] = None
    signed_url: bool = False
    default_ttl: int = 86400
    max_ttl: int = 31536000
    behavior_path: str = "/*"
    description: str = ""

    def __post_init__(self):
        """
        Validation sau khi khởi tạo.

        Throw MidicoderError nếu:
        - distribution_id không hợp lệ (MDC-CP11-011)
        - domain không hợp lệ (MDC-CP11-012)
        - TTL < 0 (MDC-CP11-013)
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Validate distribution_id
        if self.distribution_id and not self.distribution_id.strip():
            EM.raise_error(
                ErrorCode.CP11_TRANSFORM_INVALID_PARAM,
                detail="CDNIntegration distribution_id không được để trống nếu có giá trị",
            )

        # Validate domain
        if self.domain and not self.domain.strip():
            EM.raise_error(
                ErrorCode.CP11_TRANSFORM_INVALID_PARAM,
                detail="CDNIntegration domain không được để trống nếu có giá trị",
            )

        # Validate TTL >= 0
        if self.default_ttl < 0:
            EM.raise_error(
                ErrorCode.CP11_TRANSFORM_INVALID_PARAM,
                detail="CDNIntegration default_ttl không được âm",
            )
        if self.max_ttl < 0:
            EM.raise_error(
                ErrorCode.CP11_TRANSFORM_INVALID_PARAM,
                detail="CDNIntegration max_ttl không được âm",
            )
        if self.default_ttl > self.max_ttl:
            EM.raise_error(
                ErrorCode.CP11_TRANSFORM_INVALID_PARAM,
                detail="CDNIntegration default_ttl không được lớn hơn max_ttl",
            )

    def get_cdn_url(self, key: str) -> str:
        """
        Trả về CDN URL cho một key.

        Nếu CDN chưa cấu hình (không có domain) — trả về rỗng.

        Args:
            key: Key của file trong S3

        Returns:
            CDN URL string hoặc empty string nếu CDN chưa cấu hình
        """
        if not self.domain:
            return ""
        return f"https://{self.domain}/{key.lstrip('/')}"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển CDN config sang dict format."""
        return {
            "name": self.name,
            "distribution_id": self.distribution_id,
            "domain": self.domain,
            "origin_bucket": self.origin_bucket,
            "origin_access_identity": self.origin_access_identity,
            "signed_url": self.signed_url,
            "default_ttl": self.default_ttl,
            "max_ttl": self.max_ttl,
            "behavior_path": self.behavior_path,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CDNIntegration":
        """Tạo CDNIntegration từ dict."""
        return cls(
            name=data.get("name", "default"),
            distribution_id=data.get("distribution_id"),
            domain=data.get("domain"),
            origin_bucket=data.get("origin_bucket"),
            origin_access_identity=data.get("origin_access_identity"),
            signed_url=data.get("signed_url", False),
            default_ttl=data.get("default_ttl", 86400),
            max_ttl=data.get("max_ttl", 31536000),
            behavior_path=data.get("behavior_path", "/*"),
            description=data.get("description", ""),
        )


# ===========================================================================
# PresignedURLPolicy
# ===========================================================================


@dataclass
class PresignedURLPolicy:
    """
    Policy cho presigned URL — kiểm soát thời hạn và loại operation.

    Attributes:
        name: Định danh duy nhất của policy
        expiration: Thời hạn mặc định (giây), mặc định 3600s = 1 giờ
        max_expiration: Thời hạn tối đa (giây), mặc định 604800s = 7 ngày
        allowed_operations: Operations được phép (get_object, put_object)
        use_cdn_signed_url: Dùng CloudFront signed URL thay vì S3 presigned
    """
    name: str = "default"
    expiration: int = 3600
    max_expiration: int = 604800
    allowed_operations: list[str] = field(default_factory=lambda: ["get_object"])
    use_cdn_signed_url: bool = False

    def __post_init__(self):
        """
        Validation sau khi khởi tạo.

        Throw MidicoderError nếu:
        - expiration <= 0 (MDC-CP11-005)
        - expiration > max_expiration (MDC-CP11-005)
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if self.expiration <= 0:
            EM.raise_error(
                ErrorCode.CP11_FILE_SIZE_EXCEEDED,
                detail=f"PresignedURLPolicy '{self.name}': expiration phải > 0",
            )
        if self.expiration > self.max_expiration:
            EM.raise_error(
                ErrorCode.CP11_FILE_SIZE_EXCEEDED,
                detail=f"PresignedURLPolicy '{self.name}': expiration không được > max_expiration",
            )
        if not self.allowed_operations:
            EM.raise_error(
                ErrorCode.CP11_INVALID_CONTENT_TYPE,
                detail=f"PresignedURLPolicy '{self.name}': allowed_operations không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "expiration": self.expiration,
            "max_expiration": self.max_expiration,
            "allowed_operations": self.allowed_operations,
            "use_cdn_signed_url": self.use_cdn_signed_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PresignedURLPolicy":
        return cls(
            name=data.get("name", "default"),
            expiration=data.get("expiration", 3600),
            max_expiration=data.get("max_expiration", 604800),
            allowed_operations=data.get("allowed_operations", ["get_object"]),
            use_cdn_signed_url=data.get("use_cdn_signed_url", False),
        )


# ===========================================================================
# FileStorageCollection
# ===========================================================================


@dataclass
class FileStorageCollection:
    """
    Collection chứa tất cả storage profiles, upload policies, media transforms,
    CDN config và presigned URL policies.

    Attributes:
        profiles: Danh sách storage profiles
        policies: Danh sách upload policies
        transforms: Danh sách media transforms
        cdn_config: Cấu hình CDN (CloudFront) — None nếu không dùng CDN
        presigned_policy: Policy cho presigned URLs
    """
    profiles: list[StorageProfile] = field(default_factory=list)
    policies: list[UploadPolicy] = field(default_factory=list)
    transforms: list[MediaTransform] = field(default_factory=list)
    cdn_config: Optional[CDNIntegration] = None
    presigned_policy: Optional[PresignedURLPolicy] = None

    def add_profile(self, profile: StorageProfile) -> None:
        """Thêm profile vào collection."""
        self.profiles.append(profile)

    def add_policy(self, policy: UploadPolicy) -> None:
        """Thêm policy vào collection."""
        self.policies.append(policy)

    def add_transform(self, transform: MediaTransform) -> None:
        """Thêm transform vào collection."""
        self.transforms.append(transform)

    def set_cdn_config(self, config: CDNIntegration) -> None:
        """Set CDN configuration."""
        self.cdn_config = config

    def has_cdn(self) -> bool:
        """Trả về True nếu CDN được cấu hình."""
        return self.cdn_config is not None and bool(self.cdn_config.domain)

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
        result: dict[str, Any] = {
            "profiles": [p.to_dict() for p in self.profiles],
            "policies": [pol.to_dict() for pol in self.policies],
            "transforms": [t.to_dict() for t in self.transforms],
        }
        if self.cdn_config:
            result["cdn_config"] = self.cdn_config.to_dict()
        if self.presigned_policy:
            result["presigned_policy"] = self.presigned_policy.to_dict()
        return result

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
        if "cdn_config" in data and data["cdn_config"]:
            result.cdn_config = CDNIntegration.from_dict(data["cdn_config"])
        if "presigned_policy" in data and data["presigned_policy"]:
            result.presigned_policy = PresignedURLPolicy.from_dict(data["presigned_policy"])
        return result
