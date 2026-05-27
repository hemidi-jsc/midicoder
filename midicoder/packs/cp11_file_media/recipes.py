# coding: utf-8
"""
Recipes cho CP11 File Storage & Media Processing.

Recipe = gán giá trị cụ thể vào pattern vocabulary (không phải domain-specific).

Scope: AWS (S3, CloudFront) + Local (filesystem). Không hỗ trợ GCP/Azure.

Author: Midicoder Team
Version: 1.1.0
"""

from __future__ import annotations

from midicoder.packs.cp11_file_media.models import (
    StorageProfile,
    UploadPolicy,
    MediaTransform,
    CDNIntegration,
    PresignedURLPolicy,
    FileStorageCollection,
    StorageBackend,
    TransformType,
)


# ===========================================================================
# S3 Storage Recipe
# ===========================================================================


def S3StorageRecipe(
    name: str = "s3_default",
    bucket: str = "app-uploads",
    region: str = "us-east-1",
    endpoint_url: str | None = None,
    tenant_isolation: bool = True,
    description: str = "AWS S3 storage recipe",
) -> StorageProfile:
    """
    Recipe: tạo StorageProfile cấu hình sẵn cho AWS S3.

    Gán concrete values vào StorageProfile pattern.

    Args:
        name: Định danh profile
        bucket: S3 bucket name
        region: AWS region
        endpoint_url: Custom endpoint (MinIO/S3-compatible) — None cho AWS S3
        tenant_isolation: Enforce tenant isolation (KPI-029)
        description: Mô tả

    Returns:
        StorageProfile đã cấu hình sẵn cho S3
    """
    return StorageProfile(
        name=name,
        backend_type=StorageBackend.S3,
        bucket=bucket,
        region=region,
        endpoint_url=endpoint_url,
        tenant_isolation=tenant_isolation,
        description=description,
    )


def MinIORecipe(
    name: str = "minio",
    bucket: str = "app-uploads",
    endpoint: str = "http://localhost:9000",
    region: str = "us-east-1",
    tenant_isolation: bool = True,
    description: str = "MinIO self-hosted S3-compatible recipe",
) -> StorageProfile:
    """
    Recipe: tạo StorageProfile cho MinIO (S3-compatible, self-hosted).

    Args:
        name: Định danh profile
        bucket: Bucket name
        endpoint: MinIO endpoint URL
        region: Region
        tenant_isolation: Enforce tenant isolation
        description: Mô tả

    Returns:
        StorageProfile đã cấu hình cho MinIO
    """
    return StorageProfile(
        name=name,
        backend_type=StorageBackend.S3,
        bucket=bucket,
        region=region,
        endpoint_url=endpoint,
        tenant_isolation=tenant_isolation,
        description=description,
    )


# ===========================================================================
# Local Storage Recipe
# ===========================================================================


def LocalStorageRecipe(
    name: str = "local_default",
    description: str = "Local filesystem storage recipe",
) -> StorageProfile:
    """
    Recipe: tạo StorageProfile cấu hình sẵn cho local filesystem.

    Gán concrete values vào StorageProfile pattern.

    Args:
        name: Định danh profile
        description: Mô tả

    Returns:
        StorageProfile đã cấu hình sẵn cho local storage
    """
    return StorageProfile(
        name=name,
        backend_type=StorageBackend.LOCAL,
        description=description,
    )


# ===========================================================================
# Upload Policy Recipes
# ===========================================================================


def ImageUploadRecipe(
    name: str = "images",
    max_file_size: int = 10 * 1024 * 1024,
    default_storage_profile: str = "",
    description: str = "Image upload policy (JPG, PNG, GIF, WebP)",
) -> UploadPolicy:
    """
    Recipe: UploadPolicy cho image uploads.

    Args:
        name: Định danh policy
        max_file_size: Kích thước tối đa (bytes)
        default_storage_profile: Tên StorageProfile mặc định
        description: Mô tả

    Returns:
        UploadPolicy cho images
    """
    return UploadPolicy(
        name=name,
        allowed_content_types=["image/jpeg", "image/png", "image/gif", "image/webp"],
        max_file_size=max_file_size,
        allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"],
        default_storage_profile=default_storage_profile,
        description=description,
    )


def DocumentUploadRecipe(
    name: str = "documents",
    max_file_size: int = 25 * 1024 * 1024,
    default_storage_profile: str = "",
    description: str = "Document upload policy (PDF, DOC, XLS)",
) -> UploadPolicy:
    """
    Recipe: UploadPolicy cho document uploads.

    Args:
        name: Định danh policy
        max_file_size: Kích thước tối đa (bytes)
        default_storage_profile: Tên StorageProfile mặc định
        description: Mô tả

    Returns:
        UploadPolicy cho documents
    """
    return UploadPolicy(
        name=name,
        allowed_content_types=[
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ],
        max_file_size=max_file_size,
        allowed_extensions=["pdf", "doc", "docx", "xls", "xlsx"],
        default_storage_profile=default_storage_profile,
        description=description,
    )


def VideoUploadRecipe(
    name: str = "videos",
    max_file_size: int = 500 * 1024 * 1024,
    default_storage_profile: str = "",
    description: str = "Video upload policy (MP4, WebM)",
) -> UploadPolicy:
    """
    Recipe: UploadPolicy cho video uploads.

    Args:
        name: Định danh policy
        max_file_size: Kích thước tối đa (bytes)
        default_storage_profile: Tên StorageProfile mặc định
        description: Mô tả

    Returns:
        UploadPolicy cho videos
    """
    return UploadPolicy(
        name=name,
        allowed_content_types=["video/mp4", "video/webm"],
        max_file_size=max_file_size,
        allowed_extensions=["mp4", "webm"],
        default_storage_profile=default_storage_profile,
        description=description,
    )


# ===========================================================================
# Media Transform Recipes
# ===========================================================================


def ImageResizeRecipe(
    name: str = "resize",
    width: int = 800,
    height: int = 600,
    quality: int = 80,
    description: str = "Image resize transform",
) -> MediaTransform:
    """Recipe: MediaTransform cho image resize."""
    return MediaTransform(
        name=name,
        transform_type=TransformType.RESIZE,
        width=width,
        height=height,
        quality=quality,
        description=description,
    )


def ThumbnailRecipe(
    name: str = "thumbnail",
    size: int = 150,
    quality: int = 75,
    description: str = "Image thumbnail transform",
) -> MediaTransform:
    """Recipe: MediaTransform cho image thumbnail."""
    return MediaTransform(
        name=name,
        transform_type=TransformType.THUMBNAIL,
        width=size,
        height=size,
        quality=quality,
        description=description,
    )


def ImageTranscodeRecipe(
    name: str = "transcode",
    output_format: str = "jpeg",
    quality: int = 85,
    description: str = "Image format transcode",
) -> MediaTransform:
    """Recipe: MediaTransform cho image format transcode."""
    return MediaTransform(
        name=name,
        transform_type=TransformType.TRANSCODE,
        format=output_format,
        quality=quality,
        description=description,
    )


# ===========================================================================
# CloudFront CDN Recipe
# ===========================================================================


def CloudFrontRecipe(
    name: str = "cloudfront",
    distribution_id: str | None = None,
    domain: str | None = None,
    origin_bucket: str | None = None,
    origin_access_identity: str | None = None,
    signed_url: bool = False,
    default_ttl: int = 86400,
    max_ttl: int = 31536000,
    behavior_path: str = "/*",
    description: str = "AWS CloudFront CDN integration recipe",
) -> CDNIntegration:
    """
    Recipe: tạo CDNIntegration cấu hình sẵn cho AWS CloudFront.

    Gán concrete values vào CDNIntegration pattern.

    Args:
        name: Định danh CDN config
        distribution_id: CloudFront distribution ID
        domain: CloudFront domain (e.g., d1234.cloudfront.net)
        origin_bucket: S3 bucket origin
        origin_access_identity: CloudFront OAI S3 canonical UID
        signed_url: Dùng signed URL/cookies
        default_ttl: Default TTL (giây)
        max_ttl: Max TTL (giây)
        behavior_path: Cache behavior path pattern
        description: Mô tả

    Returns:
        CDNIntegration đã cấu hình cho CloudFront
    """
    return CDNIntegration(
        name=name,
        distribution_id=distribution_id,
        domain=domain,
        origin_bucket=origin_bucket,
        origin_access_identity=origin_access_identity,
        signed_url=signed_url,
        default_ttl=default_ttl,
        max_ttl=max_ttl,
        behavior_path=behavior_path,
        description=description,
    )


def PresignedURLRecipe(
    name: str = "default",
    expiration: int = 3600,
    max_expiration: int = 604800,
    use_cdn_signed_url: bool = False,
) -> PresignedURLPolicy:
    """
    Recipe: tạo PresignedURLPolicy với các giá trị mặc định hợp lý.

    Args:
        name: Định danh policy
        expiration: Thời hạn mặc định (giây)
        max_expiration: Thời hạn tối đa (giây)
        use_cdn_signed_url: Dùng CloudFront signed URL

    Returns:
        PresignedURLPolicy đã cấu hình
    """
    return PresignedURLPolicy(
        name=name,
        expiration=expiration,
        max_expiration=max_expiration,
        allowed_operations=["get_object", "put_object"],
        use_cdn_signed_url=use_cdn_signed_url,
    )


# ===========================================================================
# Composite Recipe (Full stack)
# ===========================================================================


def FullStorageRecipe(
    bucket: str = "app-uploads",
    region: str = "us-east-1",
    cdn_domain: str | None = None,
    cdn_distribution_id: str | None = None,
) -> FileStorageCollection:
    """
    Recipe composite: tạo FileStorageCollection đầy đủ với S3 + CDN + policies.

    Args:
        bucket: S3 bucket
        region: AWS region
        cdn_domain: CloudFront domain (optional)
        cdn_distribution_id: CloudFront distribution ID (optional)

    Returns:
        FileStorageCollection với S3 profile, image/document policies,
        thumbnail/resize transforms, và optional CDN config
    """
    collection = FileStorageCollection()

    # Storage profile
    collection.add_profile(S3StorageRecipe(bucket=bucket, region=region))

    # Upload policies
    collection.add_policy(ImageUploadRecipe(default_storage_profile="s3_default"))
    collection.add_policy(DocumentUploadRecipe(default_storage_profile="s3_default"))

    # Media transforms
    collection.add_transform(ThumbnailRecipe())
    collection.add_transform(ImageResizeRecipe())

    # CDN (optional)
    if cdn_domain:
        collection.set_cdn_config(
            CloudFrontRecipe(
                distribution_id=cdn_distribution_id,
                domain=cdn_domain,
                origin_bucket=bucket,
            )
        )
        collection.presigned_policy = PresignedURLRecipe(use_cdn_signed_url=True)

    return collection
