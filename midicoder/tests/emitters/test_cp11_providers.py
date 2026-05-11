# coding: utf-8
"""
Test provider abstraction cho CP11 File Storage.

Kiem tra:
- StorageProvider ABC co du methods
- LocalProvider hoat dong va cung
- S3Provider import duoc (lazy import boto3)
"""

from __future__ import annotations

from pathlib import Path
from unittest import TestCase

import pytest

from midicoder.emitters.core.file_storage.providers.base import StorageProvider
from midicoder.emitters.core.file_storage.providers.local import LocalProvider


class TestStorageProviderABC(TestCase):
    """Kiem tra StorageProvider ABC."""

    def test_is_abstract(self):
        """StorageProvider la abstract class."""
        with self.assertRaises(TypeError):
            StorageProvider()

    def test_has_upload_method(self):
        """ABC co phuong thuc upload."""
        self.assertTrue(hasattr(StorageProvider, 'upload'))

    def test_has_download_method(self):
        """ABC co phuong thuc download."""
        self.assertTrue(hasattr(StorageProvider, 'download'))

    def test_has_delete_method(self):
        """ABC co phuong thuc delete."""
        self.assertTrue(hasattr(StorageProvider, 'delete'))

    def test_has_get_presigned_url_method(self):
        """ABC co phuong thuc get_presigned_url."""
        self.assertTrue(hasattr(StorageProvider, 'get_presigned_url'))

    def test_has_list_files_method(self):
        """ABC co phuong thuc list_files."""
        self.assertTrue(hasattr(StorageProvider, 'list_files'))


class TestS3ProviderImport(TestCase):
    """Kiem tra S3Provider import (lazy boto3)."""

    def test_s3_provider_importable(self):
        """S3Provider import duoc ma khong can boto3."""
        from midicoder.emitters.core.file_storage.providers.s3 import S3Provider
        self.assertIsNotNone(S3Provider)

    def test_s3_provider_inherits_storage_provider(self):
        """S3Provider ke thua tu StorageProvider."""
        from midicoder.emitters.core.file_storage.providers.s3 import S3Provider
        self.assertTrue(issubclass(S3Provider, StorageProvider))


class TestLocalProvider(TestCase):
    """Kiem tra LocalProvider."""

    def setUp(self):
        self.base_dir = Path(__file__).parent / '.local_test_storage'
        self.base_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Xoa test storage sau khi test xong."""
        import shutil
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)

    def test_create_provider(self):
        """Tao provider thanh cong."""
        provider = LocalProvider(base_path=str(self.base_dir))
        self.assertIsNotNone(provider)

    def test_upload_and_download(self):
        """Upload va download file."""
        provider = LocalProvider(base_path=str(self.base_dir))
        content = b'hello world'
        result = provider.upload(content, 'test.txt', 'text/plain')
        self.assertEqual(result['key'], 'test.txt')
        self.assertEqual(result['size'], len(content))

        downloaded = provider.download('test.txt')
        self.assertEqual(downloaded, content)

    def test_delete_file(self):
        """Xoa file."""
        provider = LocalProvider(base_path=str(self.base_dir))
        provider.upload(b'data', 'delete_me.txt', 'text/plain')
        deleted = provider.delete('delete_me.txt')
        self.assertTrue(deleted)

    def test_list_files(self):
        """Liet ke files."""
        provider = LocalProvider(base_path=str(self.base_dir))
        provider.upload(b'a', 'a.txt', 'text/plain')
        provider.upload(b'bb', 'b.txt', 'text/plain')
        files = provider.list_files('')
        self.assertEqual(len(files), 2)

    def test_download_nonexistent(self):
        """Download file khong ton tai sinh loi."""
        provider = LocalProvider(base_path=str(self.base_dir))
        with self.assertRaises(Exception):
            provider.download('not_found.txt')

    def test_delete_nonexistent(self):
        """Xoa file khong ton tai tra ve False."""
        provider = LocalProvider(base_path=str(self.base_dir))
        result = provider.delete('not_found.txt')
        self.assertFalse(result)

    def test_tenant_prefix(self):
        """KPI-029: Tenant prefix trong key."""
        provider = LocalProvider(base_path=str(self.base_dir), tenant_prefix='tenants/t1/')
        provider.upload(b'data', 'file.txt', 'text/plain')
        files = provider.list_files('')
        self.assertEqual(len(files), 1)
        # Key trong ket qua khong co tenant prefix
        self.assertEqual(files[0]['key'], 'file.txt')

    def test_invalid_content_type(self):
        """Content type rong sinh loi."""
        provider = LocalProvider(base_path=str(self.base_dir))
        with self.assertRaises(Exception):
            provider.upload(b'data', 'file.txt', '')

    def test_presigned_url(self):
        """Lay presigned URL (local provider tra ve local path)."""
        provider = LocalProvider(base_path=str(self.base_dir))
        provider.upload(b'data', 'presigned.txt', 'text/plain')
        url = provider.get_presigned_url('presigned.txt')
        self.assertIsInstance(url, str)
        self.assertTrue(len(url) > 0)
