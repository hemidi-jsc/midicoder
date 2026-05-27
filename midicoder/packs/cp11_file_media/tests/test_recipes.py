# coding: utf-8
"""
Test suite cho CP11 Recipes.

Kiểm tra tất cả recipe functions:
- S3StorageRecipe, LocalStorageRecipe, MinIORecipe
- ImageUploadRecipe, DocumentUploadRecipe, VideoUploadRecipe
- ImageResizeRecipe, ThumbnailRecipe, ImageTranscodeRecipe
- CloudFrontRecipe, PresignedURLRecipe
- FullStorageRecipe (composite)
"""

import pytest
from midicoder.packs.cp11_file_media.recipes import (
    S3StorageRecipe,
    LocalStorageRecipe,
    MinIORecipe,
    ImageUploadRecipe,
    DocumentUploadRecipe,
    VideoUploadRecipe,
    ImageResizeRecipe,
    ThumbnailRecipe,
    ImageTranscodeRecipe,
    CloudFrontRecipe,
    PresignedURLRecipe,
    FullStorageRecipe,
)
from midicoder.packs.cp11_file_media.models import (
    StorageBackend,
    TransformType,
)


class TestS3StorageRecipe:
    def test_default_values(self):
        p = S3StorageRecipe()
        assert p.name == "s3_default"
        assert p.backend_type == StorageBackend.S3
        assert p.bucket == "app-uploads"
        assert p.region == "us-east-1"
        assert p.tenant_isolation is True

    def test_custom_values(self):
        p = S3StorageRecipe(name="prod", bucket="my-bucket", region="ap-southeast-1")
        assert p.name == "prod"
        assert p.bucket == "my-bucket"
        assert p.region == "ap-southeast-1"


class TestLocalStorageRecipe:
    def test_default_values(self):
        p = LocalStorageRecipe()
        assert p.name == "local_default"
        assert p.backend_type == StorageBackend.LOCAL

    def test_custom_name(self):
        p = LocalStorageRecipe(name="dev_local")
        assert p.name == "dev_local"


class TestMinIORecipe:
    def test_default_values(self):
        p = MinIORecipe()
        assert p.backend_type == StorageBackend.S3
        assert p.endpoint_url == "http://localhost:9000"

    def test_custom_endpoint(self):
        p = MinIORecipe(endpoint="http://minio.internal:9000")
        assert p.endpoint_url == "http://minio.internal:9000"


class TestImageUploadRecipe:
    def test_allowed_types(self):
        p = ImageUploadRecipe()
        assert "image/jpeg" in p.allowed_content_types
        assert "image/png" in p.allowed_content_types
        assert "image/webp" in p.allowed_content_types

    def test_allowed_extensions(self):
        p = ImageUploadRecipe()
        assert "jpg" in p.allowed_extensions
        assert "png" in p.allowed_extensions
        assert "webp" in p.allowed_extensions

    def test_default_max_size(self):
        p = ImageUploadRecipe()
        assert p.max_file_size == 10 * 1024 * 1024


class TestDocumentUploadRecipe:
    def test_allowed_types(self):
        p = DocumentUploadRecipe()
        assert "application/pdf" in p.allowed_content_types

    def test_allowed_extensions(self):
        p = DocumentUploadRecipe()
        assert "pdf" in p.allowed_extensions
        assert "docx" in p.allowed_extensions
        assert "xlsx" in p.allowed_extensions


class TestVideoUploadRecipe:
    def test_allowed_types(self):
        p = VideoUploadRecipe()
        assert "video/mp4" in p.allowed_content_types
        assert "video/webm" in p.allowed_content_types

    def test_default_max_size(self):
        p = VideoUploadRecipe()
        assert p.max_file_size == 500 * 1024 * 1024


class TestImageResizeRecipe:
    def test_default_values(self):
        t = ImageResizeRecipe()
        assert t.transform_type == TransformType.RESIZE
        assert t.width == 800
        assert t.height == 600
        assert t.quality == 80


class TestThumbnailRecipe:
    def test_default_values(self):
        t = ThumbnailRecipe()
        assert t.transform_type == TransformType.THUMBNAIL
        assert t.width == 150
        assert t.height == 150


class TestImageTranscodeRecipe:
    def test_default_values(self):
        t = ImageTranscodeRecipe()
        assert t.transform_type == TransformType.TRANSCODE
        assert t.format == "jpeg"


class TestCloudFrontRecipe:
    def test_default_values(self):
        c = CloudFrontRecipe()
        assert c.name == "cloudfront"
        assert c.signed_url is False
        assert c.default_ttl == 86400
        assert c.behavior_path == "/*"

    def test_with_distribution(self):
        c = CloudFrontRecipe(
            distribution_id="E1234567890",
            domain="d1234.cloudfront.net",
            signed_url=True,
        )
        assert c.distribution_id == "E1234567890"
        assert c.signed_url is True


class TestPresignedURLRecipe:
    def test_default_values(self):
        p = PresignedURLRecipe()
        assert p.expiration == 3600
        assert p.max_expiration == 604800
        assert "get_object" in p.allowed_operations

    def test_with_cdn(self):
        p = PresignedURLRecipe(use_cdn_signed_url=True)
        assert p.use_cdn_signed_url is True


class TestFullStorageRecipe:
    def test_without_cdn(self):
        coll = FullStorageRecipe()
        assert len(coll.profiles) >= 1
        assert len(coll.policies) >= 2
        assert len(coll.transforms) >= 2
        assert coll.has_cdn() is False

    def test_with_cdn(self):
        coll = FullStorageRecipe(
            bucket="my-bucket",
            cdn_domain="d1234.cloudfront.net",
            cdn_distribution_id="E123",
        )
        assert coll.has_cdn() is True
        assert coll.cdn_config.domain == "d1234.cloudfront.net"
        assert coll.presigned_policy is not None
        assert coll.presigned_policy.use_cdn_signed_url is True
