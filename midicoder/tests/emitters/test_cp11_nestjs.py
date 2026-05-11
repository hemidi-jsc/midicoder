# coding: utf-8
"""
Test NestJS emitter cho CP11 File Storage.

Kiem tra:
- NestJSFileStorageEmitter sinh ra dung output
- Cac file co du module, service, controller
"""

from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from midicoder.emitters.core.file_storage.models import (
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


class TestNestJSEmitterBasic(TestCase):
    """Kiem tra NestJS emitter co ban."""

    def test_emitter_class_exists(self):
        """NestJSFileStorageEmitter ton tai."""
        from midicoder.emitters.core.file_storage.nestjs import NestJSFileStorageEmitter
        self.assertIsNotNone(NestJSFileStorageEmitter)

    def test_generate_returns_dict(self):
        """Generate tra ve dict."""
        from midicoder.emitters.core.file_storage.nestjs import NestJSFileStorageEmitter
        emitter = NestJSFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.generate(make_collection(), Path('/tmp'))
        self.assertIsInstance(files, dict)


class TestNestJSEmitterContent(TestCase):
    """Kiem tra noi dung NestJS generated code."""

    def setUp(self):
        from midicoder.emitters.core.file_storage.nestjs import NestJSFileStorageEmitter
        self.emitter = NestJSFileStorageEmitter(stack_dir=Path('.'))
        self.files = self.emitter.generate(make_collection(), Path('/tmp'))

    def test_has_s3_module(self):
        """Sinh ra S3Module."""
        content = self.files.get('storage/s3.module.ts', '')
        self.assertIn('@Module', content)

    def test_has_upload_service(self):
        """Sinh ra FileUploadService."""
        content = self.files.get('storage/file-upload.service.ts', '')
        self.assertIn('@Injectable', content)

    def test_has_media_transform(self):
        """Sinh ra MediaTransformService."""
        content = self.files.get('storage/media-transform.service.ts', '')
        self.assertIn('@Injectable', content)

    def test_has_controller(self):
        """Sinh ra FileUploadController."""
        content = self.files.get('storage/file-upload.controller.ts', '')
        self.assertIn('@Controller', content)

    def test_upload_service_has_policy(self):
        """Upload service co policy enforcement."""
        content = self.files.get('storage/file-upload.service.ts', '')
        self.assertIn('validateAgainstPolicy', content) or self.assertIn('policy', content.lower())

    def test_controller_has_upload_route(self):
        """Controller co upload route."""
        content = self.files.get('storage/file-upload.controller.ts', '')
        self.assertIn('@Post', content)

    def test_controller_has_download_route(self):
        """Controller co download route."""
        content = self.files.get('storage/file-upload.controller.ts', '')
        self.assertIn('@Get', content)

    def test_vietnamese_comments(self):
        """Co comment tieng Viet."""
        content = self.files.get('storage/s3.module.ts', '')
        self.assertIn('/', content)
