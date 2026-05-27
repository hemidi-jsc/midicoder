# coding: utf-8
"""
Test FastAPI emitter cho CP11 File Storage.

Kiem tra:
- FastAPIFileStorageEmitter sinh ra dung dict output
- Cac file co du routes, services, policy enforcement
"""

from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from midicoder.packs.cp11_file_media.fastapi import FastAPIFileStorageEmitter
from midicoder.packs.cp11_file_media.models import (
    FileStorageCollection,
    MediaTransform,
    StorageBackend,
    StorageProfile,
    TransformType,
    UploadPolicy,
)


def make_collection():
    """Tao FileStorageCollection mau."""
    coll = FileStorageCollection()
    coll.add_profile(
        StorageProfile(
            name='default-s3',
            backend_type=StorageBackend.S3,
            bucket='test-bucket',
            region='us-east-1',
            tenant_isolation=True,
        )
    )
    coll.add_policy(
        UploadPolicy(
            name='images',
            allowed_content_types={'image/jpeg', 'image/png'},
            max_file_size=5 * 1024 * 1024,
            allowed_extensions={'jpg', 'jpeg', 'png'},
        )
    )
    coll.add_transform(
        MediaTransform(
            name='thumbnail',
            transform_type=TransformType.THUMBNAIL,
            width=100,
            height=100,
            quality=80,
        )
    )
    return coll


class TestFastAPIEmitterBasic(TestCase):
    """Kiem tra FastAPI emitter co ban."""

    def test_emitter_class_exists(self):
        """FastAPIFileStorageEmitter ton tai."""
        self.assertIsNotNone(FastAPIFileStorageEmitter)

    def test_generate_returns_dict(self):
        """Generate tra ve dict."""
        emitter = FastAPIFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.generate(make_collection(), Path('/tmp'))
        self.assertIsInstance(files, dict)

    def test_generate_empty_collection(self):
        """Generate voi collection rong tra ve dict rong."""
        emitter = FastAPIFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.generate(FileStorageCollection(), Path('/tmp'))
        self.assertEqual(files, {})

    def test_generate_has_s3_config(self):
        """Sinh ra file s3_config."""
        emitter = FastAPIFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.generate(make_collection(), Path('/tmp'))
        self.assertIn('storage/s3_config.py', files)

    def test_generate_has_upload_service(self):
        """Sinh ra file upload service."""
        emitter = FastAPIFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.generate(make_collection(), Path('/tmp'))
        self.assertIn('storage/file_upload_service.py', files)

    def test_generate_has_media_transform(self):
        """Sinh ra file media transform service."""
        emitter = FastAPIFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.generate(make_collection(), Path('/tmp'))
        self.assertIn('storage/media_transform_service.py', files)

    def test_generate_has_router(self):
        """Sinh ra file storage router."""
        emitter = FastAPIFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.generate(make_collection(), Path('/tmp'))
        self.assertIn('storage/storage_router.py', files)


class TestFastAPIEmitterContent(TestCase):
    """Kiem tra noi dung FastAPI generated code."""

    def setUp(self):
        self.emitter = FastAPIFileStorageEmitter(stack_dir=Path('.'))
        self.files = self.emitter.generate(make_collection(), Path('/tmp'))

    def test_s3_config_has_tenant_isolation(self):
        """S3 config co tenant isolation."""
        content = self.files['storage/s3_config.py']
        self.assertIn('S3_TENANT_ISOLATION', content)
        self.assertIn('get_tenant_s3_client', content)

    def test_s3_config_has_boto3(self):
        """S3 config import boto3."""
        content = self.files['storage/s3_config.py']
        self.assertIn('boto3', content)

    def test_s3_config_has_vietnamese_comments(self):
        """S3 config co comment tieng Viet."""
        content = self.files['storage/s3_config.py']
        self.assertIn('#', content)

    def test_upload_service_has_policy_enforcement(self):
        """Upload service co UploadPolicy enforcement."""
        content = self.files['storage/file_upload_service.py']
        self.assertIn('_enforce_policy', content)
        self.assertIn('UPLOAD_POLICIES', content)

    def test_upload_service_has_policy_name(self):
        """Upload service co policy ten 'images'."""
        content = self.files['storage/file_upload_service.py']
        self.assertIn('images', content)

    def test_upload_service_has_tenant_folder(self):
        """Upload service co tenant folder (KPI-029)."""
        content = self.files['storage/file_upload_service.py']
        self.assertIn('_get_tenant_folder', content)

    def test_router_has_upload_route(self):
        """Router co route /upload."""
        content = self.files['storage/storage_router.py']
        self.assertIn('/upload', content)

    def test_router_has_download_route(self):
        """Router co route /download."""
        content = self.files['storage/storage_router.py']
        self.assertIn('/download', content)

    def test_router_has_delete_route(self):
        """Router co route /delete."""
        content = self.files['storage/storage_router.py']
        self.assertIn('/delete', content)

    def test_router_has_presigned_route(self):
        """Router co route /presigned."""
        content = self.files['storage/storage_router.py']
        self.assertIn('/presigned', content)

    def test_media_transform_has_resize(self):
        """Media transform co resize method."""
        content = self.files['storage/media_transform_service.py']
        self.assertIn('resize_image', content)

    def test_media_transform_has_thumbnail(self):
        """Media transform co thumbnail method."""
        content = self.files['storage/media_transform_service.py']
        self.assertIn('create_thumbnail', content)

    def test_media_transform_has_pillow_import(self):
        """Media transform import Pillow."""
        content = self.files['storage/media_transform_service.py']
        self.assertIn('PIL', content)
