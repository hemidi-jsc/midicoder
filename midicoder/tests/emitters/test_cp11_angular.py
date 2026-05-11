# coding: utf-8
"""
Test Angular emitter cho CP11 File Storage.

Kiem tra:
- AngularFileStorageEmitter sinh ra dung output
- Cac file co du service, component, module, models
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


class TestAngularEmitterBasic(TestCase):
    """Kiem tra Angular emitter co ban."""

    def test_emitter_class_exists(self):
        """AngularFileStorageEmitter ton tai."""
        from midicoder.emitters.core.file_storage.angular import AngularFileStorageEmitter
        self.assertIsNotNone(AngularFileStorageEmitter)

    def test_emit_returns_list(self):
        """emit() tra ve list GeneratedFile."""
        from midicoder.emitters.core.file_storage.angular import AngularFileStorageEmitter
        emitter = AngularFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        self.assertIsInstance(files, list)

    def test_emit_has_service(self):
        """Sinh ra file-storage.service.ts."""
        from midicoder.emitters.core.file_storage.angular import AngularFileStorageEmitter
        emitter = AngularFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        paths = [f.path.name for f in files]
        self.assertIn('file-storage.service.ts', paths)

    def test_emit_has_component(self):
        """Sinh ra file-upload.component.ts."""
        from midicoder.emitters.core.file_storage.angular import AngularFileStorageEmitter
        emitter = AngularFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        paths = [f.path.name for f in files]
        self.assertIn('file-upload.component.ts', paths)

    def test_emit_has_module(self):
        """Sinh ra file-storage.module.ts."""
        from midicoder.emitters.core.file_storage.angular import AngularFileStorageEmitter
        emitter = AngularFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        paths = [f.path.name for f in files]
        self.assertIn('file-storage.module.ts', paths)

    def test_emit_has_models(self):
        """Sinh ra file-storage.models.ts."""
        from midicoder.emitters.core.file_storage.angular import AngularFileStorageEmitter
        emitter = AngularFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        paths = [f.path.name for f in files]
        self.assertIn('file-storage.models.ts', paths)

    def test_emit_has_index(self):
        """Sinh ra index.ts."""
        from midicoder.emitters.core.file_storage.angular import AngularFileStorageEmitter
        emitter = AngularFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        paths = [f.path.name for f in files]
        self.assertIn('index.ts', paths)


class TestAngularEmitterContent(TestCase):
    """Kiem tra noi dung Angular generated code."""

    def setUp(self):
        from midicoder.emitters.core.file_storage.angular import AngularFileStorageEmitter
        self.emitter = AngularFileStorageEmitter(stack_dir=Path('.'))
        self.files = self.emitter.emit(make_collection(), Path('/tmp'))

    def _get_content(self, name: str) -> str:
        for f in self.files:
            if f.path.name == name:
                return f.content
        return ''

    def test_service_has_injectable(self):
        """Service co @Injectable."""
        content = self._get_content('file-storage.service.ts')
        self.assertIn('@Injectable', content)

    def test_service_has_upload_method(self):
        """Service co upload method."""
        content = self._get_content('file-storage.service.ts')
        self.assertIn('upload', content)

    def test_service_has_tenant_header(self):
        """Service co KPI-029 tenant header."""
        content = self._get_content('file-storage.service.ts')
        self.assertIn('x-tenant-id', content.lower()) or self.assertIn('tenantId', content)

    def test_component_has_component_decorator(self):
        """Component co @Component."""
        content = self._get_content('file-upload.component.ts')
        self.assertIn('@Component', content)

    def test_component_has_drag_drop(self):
        """Component co drag-drop."""
        content = self._get_content('file-upload.component.ts')
        self.assertIn('drop', content.lower()) or self.assertIn('drag', content.lower())

    def test_module_has_ng_module(self):
        """Module co @NgModule."""
        content = self._get_content('file-storage.module.ts')
        self.assertIn('@NgModule', content)

    def test_models_has_interfaces(self):
        """Models co interfaces."""
        content = self._get_content('file-storage.models.ts')
        self.assertIn('interface', content)


class TestAngularGeneratedFile(TestCase):
    """Kiem tra GeneratedFile objects."""

    def test_generated_file_has_capability(self):
        """GeneratedFile co capability = CP11."""
        from midicoder.emitters.core.file_storage.angular import AngularFileStorageEmitter
        emitter = AngularFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        for f in files:
            self.assertEqual(f.capability, 'CP11')
