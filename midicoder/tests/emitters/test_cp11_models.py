# coding: utf-8
"""
Test suite cho CP11 models (StorageProfile, UploadPolicy, MediaTransform).

Test coverage cho:
- StorageProfile: __post_init__ validation, to_dict, from_dict
- UploadPolicy: __post_init__ validation, to_dict, from_dict
- MediaTransform: __post_init__ validation, to_dict, from_dict
- FileStorageCollection: add_* methods, query helpers, to_dict, from_dict
- Error codes: MDC-CP11-001~010

CP11: File Storage & Media Processing Generator
"""

import pytest
from pathlib import Path

from midicoder.errors import ErrorCode, MidicoderError


class TestStorageProfile:
    """Test StorageProfile model và validation."""

    def test_create_valid_s3_profile(self):
        """Tạo StorageProfile S3 hợp lệ."""
        from midicoder.emitters.core.cp11_file_media.models import StorageProfile, StorageBackend

        profile = StorageProfile(
            name="primary-s3",
            backend_type=StorageBackend.S3,
            bucket="my-bucket",
            region="us-east-1",
        )
        assert profile.name == "primary-s3"
        assert profile.backend_type == StorageBackend.S3
        assert profile.bucket == "my-bucket"
        assert profile.region == "us-east-1"
        assert profile.tenant_isolation is True  # mặc định

    def test_create_valid_local_profile(self):
        """Tạo StorageProfile local hợp lệ."""
        from midicoder.emitters.core.cp11_file_media.models import StorageProfile, StorageBackend

        profile = StorageProfile(
            name="local-dev",
            backend_type=StorageBackend.LOCAL,
        )
        assert profile.backend_type == StorageBackend.LOCAL
        assert profile.bucket is None

    def test_empty_name_raises_error(self):
        """Tên profile rỗng → MDC-CP11-001."""
        from midicoder.emitters.core.cp11_file_media.models import StorageProfile, StorageBackend

        with pytest.raises(MidicoderError) as exc_info:
            StorageProfile(
                name="",
                backend_type=StorageBackend.S3,
                bucket="test-bucket",
            )
        assert exc_info.value.code == ErrorCode.CP11_EMPTY_PROFILE_NAME

    def test_invalid_backend_type_raises_error(self):
        """Backend type không hợp lệ → MDC-CP11-002."""
        from midicoder.emitters.core.cp11_file_media.models import StorageProfile

        with pytest.raises(MidicoderError) as exc_info:
            StorageProfile(
                name="test",
                backend_type="invalid_backend",
            )
        assert exc_info.value.code == ErrorCode.CP11_INVALID_BACKEND_TYPE

    def test_s3_without_bucket_raises_error(self):
        """S3 không có bucket → MDC-CP11-003."""
        from midicoder.emitters.core.cp11_file_media.models import StorageProfile, StorageBackend

        with pytest.raises(MidicoderError) as exc_info:
            StorageProfile(
                name="test",
                backend_type=StorageBackend.S3,
                bucket="",
            )
        assert exc_info.value.code == ErrorCode.CP11_EMPTY_BUCKET_NAME

    def test_local_without_bucket_is_valid(self):
        """Local backend không cần bucket."""
        from midicoder.emitters.core.cp11_file_media.models import StorageProfile, StorageBackend

        profile = StorageProfile(
            name="local",
            backend_type=StorageBackend.LOCAL,
        )
        assert profile.bucket is None

    def test_to_dict(self):
        """Chuyển StorageProfile sang dict."""
        from midicoder.emitters.core.cp11_file_media.models import StorageProfile, StorageBackend

        profile = StorageProfile(
            name="test-s3",
            backend_type=StorageBackend.S3,
            bucket="test-bucket",
            region="ap-southeast-1",
            tenant_isolation=True,
        )
        d = profile.to_dict()
        assert d["name"] == "test-s3"
        assert d["backend_type"] == "s3"
        assert d["bucket"] == "test-bucket"
        assert d["tenant_isolation"] is True

    def test_from_dict(self):
        """Tạo StorageProfile từ dict."""
        from midicoder.emitters.core.cp11_file_media.models import StorageProfile, StorageBackend

        data = {
            "name": "from-dict",
            "backend_type": "s3",
            "bucket": "dict-bucket",
            "region": "eu-west-1",
        }
        profile = StorageProfile.from_dict(data)
        assert profile.name == "from-dict"
        assert profile.backend_type == StorageBackend.S3
        assert profile.bucket == "dict-bucket"


class TestUploadPolicy:
    """Test UploadPolicy model và validation."""

    def test_create_valid_policy(self):
        """Tạo UploadPolicy hợp lệ."""
        from midicoder.emitters.core.cp11_file_media.models import UploadPolicy

        policy = UploadPolicy(
            name="images-policy",
            allowed_content_types=["image/jpeg", "image/png"],
            max_file_size=10 * 1024 * 1024,
            allowed_extensions=["jpg", "jpeg", "png"],
            default_storage_profile="primary-s3",
        )
        assert policy.name == "images-policy"
        assert len(policy.allowed_content_types) == 2
        assert policy.max_file_size == 10 * 1024 * 1024

    def test_empty_name_raises_error(self):
        """Tên policy rỗng → error."""
        from midicoder.emitters.core.cp11_file_media.models import UploadPolicy

        with pytest.raises(MidicoderError) as exc_info:
            UploadPolicy(
                name="",
                allowed_content_types=["image/jpeg"],
                max_file_size=1024,
                allowed_extensions=["jpg"],
            )
        assert exc_info.value.code == ErrorCode.CP11_MISSING_POLICY

    def test_empty_content_types_raises_error(self):
        """Danh sách content types rỗng → MDC-CP11-004."""
        from midicoder.emitters.core.cp11_file_media.models import UploadPolicy

        with pytest.raises(MidicoderError) as exc_info:
            UploadPolicy(
                name="test",
                allowed_content_types=[],
                max_file_size=1024,
                allowed_extensions=["jpg"],
            )
        assert exc_info.value.code == ErrorCode.CP11_INVALID_CONTENT_TYPE

    def test_zero_max_size_raises_error(self):
        """max_file_size <= 0 → MDC-CP11-005."""
        from midicoder.emitters.core.cp11_file_media.models import UploadPolicy

        with pytest.raises(MidicoderError) as exc_info:
            UploadPolicy(
                name="test",
                allowed_content_types=["image/jpeg"],
                max_file_size=0,
                allowed_extensions=["jpg"],
            )
        assert exc_info.value.code == ErrorCode.CP11_FILE_SIZE_EXCEEDED

    def test_empty_extensions_raises_error(self):
        """Danh sách extensions rỗng → MDC-CP11-006."""
        from midicoder.emitters.core.cp11_file_media.models import UploadPolicy

        with pytest.raises(MidicoderError) as exc_info:
            UploadPolicy(
                name="test",
                allowed_content_types=["image/jpeg"],
                max_file_size=1024,
                allowed_extensions=[],
            )
        assert exc_info.value.code == ErrorCode.CP11_INVALID_EXTENSION

    def test_to_dict(self):
        """Chuyển UploadPolicy sang dict."""
        from midicoder.emitters.core.cp11_file_media.models import UploadPolicy

        policy = UploadPolicy(
            name="docs",
            allowed_content_types=["application/pdf"],
            max_file_size=5 * 1024 * 1024,
            allowed_extensions=["pdf"],
            default_storage_profile="s3-main",
        )
        d = policy.to_dict()
        assert d["name"] == "docs"
        assert d["allowed_content_types"] == ["application/pdf"]
        assert d["max_file_size"] == 5 * 1024 * 1024

    def test_from_dict(self):
        """Tạo UploadPolicy từ dict."""
        from midicoder.emitters.core.cp11_file_media.models import UploadPolicy

        data = {
            "name": "videos",
            "allowed_content_types": ["video/mp4"],
            "max_file_size": 100 * 1024 * 1024,
            "allowed_extensions": ["mp4"],
            "default_storage_profile": "s3-main",
        }
        policy = UploadPolicy.from_dict(data)
        assert policy.name == "videos"
        assert policy.max_file_size == 100 * 1024 * 1024


class TestMediaTransform:
    """Test MediaTransform model và validation."""

    def test_create_valid_resize(self):
        """Tạo MediaTransform resize hợp lệ."""
        from midicoder.emitters.core.cp11_file_media.models import MediaTransform, TransformType

        transform = MediaTransform(
            name="thumbnail-100",
            transform_type=TransformType.RESIZE,
            width=100,
            height=100,
            quality=80,
        )
        assert transform.transform_type == TransformType.RESIZE
        assert transform.width == 100
        assert transform.quality == 80

    def test_create_valid_thumbnail(self):
        """Tạo MediaTransform thumbnail hợp lệ."""
        from midicoder.emitters.core.cp11_file_media.models import MediaTransform, TransformType

        transform = MediaTransform(
            name="thumb-50",
            transform_type=TransformType.THUMBNAIL,
            width=50,
        )
        assert transform.transform_type == TransformType.THUMBNAIL

    def test_create_valid_transcode(self):
        """Tạo MediaTransform transcode hợp lệ."""
        from midicoder.emitters.core.cp11_file_media.models import MediaTransform, TransformType

        transform = MediaTransform(
            name="mp4-h264",
            transform_type=TransformType.TRANSCODE,
            format="mp4",
            quality=90,
        )
        assert transform.transform_type == TransformType.TRANSCODE
        assert transform.format == "mp4"

    def test_empty_name_raises_error(self):
        """Tên transform rỗng → error."""
        from midicoder.emitters.core.cp11_file_media.models import MediaTransform, TransformType

        with pytest.raises(MidicoderError) as exc_info:
            MediaTransform(
                name="",
                transform_type=TransformType.RESIZE,
                width=100,
            )
        assert exc_info.value.code == ErrorCode.CP11_TRANSFORM_INVALID_PARAM

    def test_invalid_transform_type_raises_error(self):
        """Transform type không hợp lệ → MDC-CP11-009."""
        from midicoder.emitters.core.cp11_file_media.models import MediaTransform

        with pytest.raises(MidicoderError) as exc_info:
            MediaTransform(
                name="test",
                transform_type="invalid_type",
            )
        assert exc_info.value.code == ErrorCode.CP11_TRANSFORM_INVALID_PARAM

    def test_quality_out_of_range_raises_error(self):
        """Quality ngoài range 1-100 → MDC-CP11-009."""
        from midicoder.emitters.core.cp11_file_media.models import MediaTransform, TransformType

        with pytest.raises(MidicoderError) as exc_info:
            MediaTransform(
                name="test",
                transform_type=TransformType.RESIZE,
                width=100,
                quality=150,
            )
        assert exc_info.value.code == ErrorCode.CP11_TRANSFORM_INVALID_PARAM

    def test_resize_without_dimensions_raises_error(self):
        """Resize không có width/height → MDC-CP11-009."""
        from midicoder.emitters.core.cp11_file_media.models import MediaTransform, TransformType

        with pytest.raises(MidicoderError) as exc_info:
            MediaTransform(
                name="test",
                transform_type=TransformType.RESIZE,
            )
        assert exc_info.value.code == ErrorCode.CP11_TRANSFORM_INVALID_PARAM

    def test_to_dict(self):
        """Chuyển MediaTransform sang dict."""
        from midicoder.emitters.core.cp11_file_media.models import MediaTransform, TransformType

        transform = MediaTransform(
            name="thumb",
            transform_type=TransformType.THUMBNAIL,
            width=200,
            height=200,
            quality=75,
        )
        d = transform.to_dict()
        assert d["name"] == "thumb"
        assert d["transform_type"] == "thumbnail"
        assert d["quality"] == 75

    def test_from_dict(self):
        """Tạo MediaTransform từ dict."""
        from midicoder.emitters.core.cp11_file_media.models import MediaTransform, TransformType

        data = {
            "name": "resize-800",
            "transform_type": "resize",
            "width": 800,
            "height": 600,
            "quality": 85,
        }
        transform = MediaTransform.from_dict(data)
        assert transform.transform_type == TransformType.RESIZE
        assert transform.width == 800
        assert transform.height == 600


class TestFileStorageCollection:
    """Test FileStorageCollection aggregate."""

    def test_add_profiles(self):
        """Thêm profiles vào collection."""
        from midicoder.emitters.core.cp11_file_media.models import (
            FileStorageCollection,
            StorageProfile,
            StorageBackend,
        )

        collection = FileStorageCollection()
        collection.add_profile(StorageProfile(name="s3", backend_type=StorageBackend.S3, bucket="b1"))
        collection.add_profile(StorageProfile(name="local", backend_type=StorageBackend.LOCAL))
        assert collection.total_count == 2

    def test_get_by_id(self):
        """Tìm profile theo ID."""
        from midicoder.emitters.core.cp11_file_media.models import (
            FileStorageCollection,
            StorageProfile,
            StorageBackend,
        )

        collection = FileStorageCollection()
        collection.add_profile(StorageProfile(name="s3-main", backend_type=StorageBackend.S3, bucket="b1"))
        profile = collection.get_by_id("s3-main")
        assert profile is not None
        assert profile.name == "s3-main"

    def test_get_by_id_not_found(self):
        """Tìm profile không tồn tại → None."""
        from midicoder.emitters.core.cp11_file_media.models import FileStorageCollection

        collection = FileStorageCollection()
        result = collection.get_by_id("nonexistent")
        assert result is None

    def test_add_policies(self):
        """Thêm policies vào collection."""
        from midicoder.emitters.core.cp11_file_media.models import (
            FileStorageCollection,
            UploadPolicy,
        )

        collection = FileStorageCollection()
        collection.add_policy(UploadPolicy(
            name="images",
            allowed_content_types=["image/jpeg"],
            max_file_size=1024,
            allowed_extensions=["jpg"],
        ))
        assert len(collection.policies) == 1

    def test_add_transforms(self):
        """Thêm transforms vào collection."""
        from midicoder.emitters.core.cp11_file_media.models import (
            FileStorageCollection,
            MediaTransform,
            TransformType,
        )

        collection = FileStorageCollection()
        collection.add_transform(MediaTransform(
            name="thumb",
            transform_type=TransformType.THUMBNAIL,
            width=100,
        ))
        assert len(collection.transforms) == 1

    def test_to_dict_from_dict(self):
        """Serialization round-trip."""
        from midicoder.emitters.core.cp11_file_media.models import (
            FileStorageCollection,
            StorageProfile,
            StorageBackend,
            UploadPolicy,
            MediaTransform,
            TransformType,
        )

        collection = FileStorageCollection()
        collection.add_profile(StorageProfile(name="s3", backend_type=StorageBackend.S3, bucket="b1"))
        collection.add_policy(UploadPolicy(
            name="images",
            allowed_content_types=["image/jpeg"],
            max_file_size=1024,
            allowed_extensions=["jpg"],
        ))
        collection.add_transform(MediaTransform(
            name="thumb",
            transform_type=TransformType.THUMBNAIL,
            width=100,
        ))

        data = collection.to_dict()
        restored = FileStorageCollection.from_dict(data)

        assert restored.total_count == 1
        assert len(restored.policies) == 1
        assert len(restored.transforms) == 1
