# coding: utf-8
"""
Test React emitter cho CP11 File Storage.

Kiem tra:
- ReactFileStorageEmitter sinh ra dung output
- Cac file co du hook, component, types, client
"""

from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from midicoder.emitters.core.cp11_file_media.models import (
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


class TestReactEmitterBasic(TestCase):
    """Kiem tra React emitter co ban."""

    def test_emitter_class_exists(self):
        """ReactFileStorageEmitter ton tai."""
        from midicoder.emitters.core.cp11_file_media.react import ReactFileStorageEmitter
        self.assertIsNotNone(ReactFileStorageEmitter)

    def test_emit_returns_list(self):
        """emit() tra ve list GeneratedFile."""
        from midicoder.emitters.core.cp11_file_media.react import ReactFileStorageEmitter
        emitter = ReactFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        self.assertIsInstance(files, list)

    def test_emit_has_types(self):
        """Sinh ra fileStorage.types.ts."""
        from midicoder.emitters.core.cp11_file_media.react import ReactFileStorageEmitter
        emitter = ReactFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        paths = [f.path.name for f in files]
        self.assertIn('fileStorage.types.ts', paths)

    def test_emit_has_client(self):
        """Sinh ra FileStorageProvider.tsx (client)."""
        from midicoder.emitters.core.cp11_file_media.react import ReactFileStorageEmitter
        emitter = ReactFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        paths = [f.path.name for f in files]
        self.assertIn('FileStorageProvider.tsx', paths)

    def test_emit_has_hook(self):
        """Sinh ra useFileStorage.ts."""
        from midicoder.emitters.core.cp11_file_media.react import ReactFileStorageEmitter
        emitter = ReactFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        paths = [f.path.name for f in files]
        self.assertIn('useFileStorage.ts', paths)

    def test_emit_has_component(self):
        """Sinh ra FileUpload.tsx."""
        from midicoder.emitters.core.cp11_file_media.react import ReactFileStorageEmitter
        emitter = ReactFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        paths = [f.path.name for f in files]
        self.assertIn('FileUpload.tsx', paths)

    def test_emit_has_index(self):
        """Sinh ra index.ts."""
        from midicoder.emitters.core.cp11_file_media.react import ReactFileStorageEmitter
        emitter = ReactFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        paths = [f.path.name for f in files]
        self.assertIn('index.ts', paths)


class TestReactEmitterContent(TestCase):
    """Kiem tra noi dung React generated code."""

    def setUp(self):
        from midicoder.emitters.core.cp11_file_media.react import ReactFileStorageEmitter
        self.emitter = ReactFileStorageEmitter(stack_dir=Path('.'))
        self.files = self.emitter.emit(make_collection(), Path('/tmp'))

    def _get_content(self, name: str) -> str:
        for f in self.files:
            if f.path.name == name:
                return f.content
        return ''

    def test_types_has_interfaces(self):
        """Types co interfaces."""
        content = self._get_content('fileStorage.types.ts')
        self.assertIn('interface', content)

    def test_types_has_upload_result(self):
        """Types co UploadResult."""
        content = self._get_content('fileStorage.types.ts')
        self.assertIn('UploadResult', content)

    def test_client_has_context(self):
        """Client (provider) co context."""
        content = self._get_content('FileStorageProvider.tsx')
        self.assertIn('context', content.lower()) or self.assertIn('Context', content)

    def test_client_has_upload(self):
        """Client (provider) co upload function."""
        content = self._get_content('FileStorageProvider.tsx')
        self.assertIn('upload', content)

    def test_hook_has_use_context(self):
        """Hook su dung useContext."""
        content = self._get_content('useFileStorage.ts')
        self.assertIn('useContext', content)

    def test_hook_returns_upload(self):
        """Hook return upload function."""
        content = self._get_content('useFileStorage.ts')
        self.assertIn('upload', content)

    def test_component_has_functional(self):
        """Component la functional component."""
        content = self._get_content('FileUpload.tsx')
        self.assertIn('function', content) or self.assertIn('const', content)

    def test_component_has_drag_drop(self):
        """Component co drag-drop."""
        content = self._get_content('FileUpload.tsx')
        self.assertIn('drop', content.lower()) or self.assertIn('drag', content.lower())

    def test_generated_file_has_capability(self):
        """GeneratedFile co capability = CP11."""
        for f in self.files:
            self.assertEqual(f.capability, 'CP11')


class TestReactGeneratedFile(TestCase):
    """Kiem tra GeneratedFile objects."""

    def test_all_files_have_correct_capability(self):
        """Tat ca GeneratedFile co capability = CP11."""
        from midicoder.emitters.core.cp11_file_media.react import ReactFileStorageEmitter
        emitter = ReactFileStorageEmitter(stack_dir=Path('.'))
        files = emitter.emit(make_collection(), Path('/tmp'))
        for f in files:
            self.assertEqual(f.capability, 'CP11')
            self.assertTrue(f.path.name.endswith('.ts') or f.path.name.endswith('.tsx'))
            self.assertTrue(len(f.content) > 10)
