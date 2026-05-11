# coding: utf-8
"""
Test emitter generation cho CP11 File Storage.

Kiểm tra các emitter sinh ra đúng dict output với key hợp lệ.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from midicoder.emitters.core.file_storage.fastapi import FastAPIFileStorageEmitter
from midicoder.emitters.core.file_storage.models import (
    FileStorageCollection,
    MediaTransform,
    StorageBackend,
    StorageProfile,
    TransformType,
    UploadPolicy,
)


@pytest.fixture
def collection():
    """Tạo FileStorageCollection mẫu."""
    coll = FileStorageCollection()
    coll.add_profile(
        StorageProfile(
            name="default-s3",
            backend_type=StorageBackend.S3,
            bucket="test-bucket",
            region="us-east-1",
            tenant_isolation=True,
        )
    )
    coll.add_policy(
        UploadPolicy(
            name="images",
            allowed_content_types={"image/jpeg", "image/png"},
            max_file_size=5 * 1024 * 1024,
            allowed_extensions={"jpg", "jpeg", "png"},
        )
    )
    coll.add_transform(
        MediaTransform(
            name="thumbnail",
            transform_type=TransformType.THUMBNAIL,
            width=100,
            height=100,
            quality=80,
        )
    )
    return coll


class TestFastAPIFileStorageEmitter:
    """Kiểm tra FastAPIFileStorageEmitter sinh output đúng."""

    def test_generate_with_s3_profile(self, collection):
        emitter = FastAPIFileStorageEmitter(stack_dir=Path("."))
        files = emitter.generate(collection, Path("/tmp"))
        assert "storage/s3_config.py" in files
        assert "storage/file_upload_service.py" in files
        assert "storage/storage_router.py" in files

    def test_s3_config_has_tenant_isolation(self, collection):
        emitter = FastAPIFileStorageEmitter(stack_dir=Path("."))
        files = emitter.generate(collection, Path("/tmp"))
        s3_content = files["storage/s3_config.py"]
        assert "S3_TENANT_ISOLATION" in s3_content
        assert "get_tenant_s3_client" in s3_content

    def test_file_upload_service_has_policy_enforcement(self, collection):
        emitter = FastAPIFileStorageEmitter(stack_dir=Path("."))
        files = emitter.generate(collection, Path("/tmp"))
        upload_content = files["storage/file_upload_service.py"]
        assert "_enforce_policy" in upload_content
        assert "UPLOAD_POLICIES" in upload_content
        assert "images" in upload_content

    def test_storage_router_has_routes(self, collection):
        emitter = FastAPIFileStorageEmitter(stack_dir=Path("."))
        files = emitter.generate(collection, Path("/tmp"))
        router_content = files["storage/storage_router.py"]
        assert '/upload' in router_content
        assert '/download' in router_content
        assert '/delete' in router_content
        assert '/presigned' in router_content

    def test_generate_empty_collection_returns_empty(self):
        emitter = FastAPIFileStorageEmitter(stack_dir=Path("."))
        empty_coll = FileStorageCollection()
        files = emitter.generate(empty_coll, Path("/tmp"))
        assert files == {}

    def test_media_transform_has_resize(self, collection):
        emitter = FastAPIFileStorageEmitter(stack_dir=Path("."))
        files = emitter.generate(collection, Path("/tmp"))
        transform_content = files["storage/media_transform_service.py"]
        assert "resize_image" in transform_content
        assert "create_thumbnail" in transform_content


class TestNestJSFileStorageEmitter:
    """Kiểm tra NestJSFileStorageEmitter sinh output đúng."""

    def test_nestjs_imports(self):
        from midicoder.emitters.core.file_storage.nestjs import NestJSFileStorageEmitter
        assert NestJSFileStorageEmitter is not None

    def test_nestjs_generate(self, collection):
        from midicoder.emitters.core.file_storage.nestjs import NestJSFileStorageEmitter

        emitter = NestJSFileStorageEmitter(stack_dir=Path("."))
        files = emitter.generate(collection, Path("/tmp"))
        assert isinstance(files, dict)
