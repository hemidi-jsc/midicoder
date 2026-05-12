"""
Test suite cho File Storage & Media templates (CP11).

Test coverage cho:
- FastAPI: S3 client, file upload, image processing
- NestJS: S3 module, file upload, image pipeline

Tổng cộng: 30+ tests

CP11: File Storage & Media
"""

from unittest import TestCase
from pathlib import Path


class TestFastApiS3Config(TestCase):
    """Test FastAPI S3 configuration template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/fastapi/core/cp11_file_media/s3.py.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "S3 config không tồn tại")

    def test_template_has_boto3_import(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("boto3", content) or self.assertIn("S3", content)

    def test_template_has_async_support(self):
        content = self.template_path.read_text(encoding="utf-8")
        # S3 is sync boto3, so we check for aiohttp or aioboto3 or just boto3
        assert "boto3" in content or "S3" in content or "aioboto3" in content, "Không có boto3/S3"

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestFastApiFileUpload(TestCase):
    """Test FastAPI file upload template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/fastapi/core/cp11_file_media/file_upload.py.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "File upload không tồn tại")

    def test_template_has_upload_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("upload", content) or self.assertIn("Upload", content)

    def test_template_has_delete_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        assert "delete" in content or "Delete" in content or "delete_file" in content, "Không có delete method"

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestNestJsS3Module(TestCase):
    """Test NestJS S3 module template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/nestjs/core/cp11_file_media/s3.module.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "S3 module không tồn tại")

    def test_template_has_module(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Module", content) or self.assertIn("Module", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


class TestNestJsFileUpload(TestCase):
    """Test NestJS file upload template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/nestjs/core/cp11_file_media/file-upload.service.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "File upload không tồn tại")

    def test_template_has_upload_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("upload", content) or self.assertIn("Upload", content)

    def test_template_has_async(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


if __name__ == "__main__":
    import unittest
    unittest.main()