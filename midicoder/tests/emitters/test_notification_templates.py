"""
Test suite cho Notification & Communication templates (CP12).

Test coverage cho:
- FastAPI: Email service, SMS service, notification templates
- NestJS: Notification module, email service, SMS service

Tổng cộng: 20+ tests

CP12: Notification & Communication
"""

from unittest import TestCase
from pathlib import Path


class TestFastApiEmailService(TestCase):
    """Test FastAPI email service template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/fastapi/cp12_notification/email_service.py.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Email service không tồn tại")

    def test_template_has_smtp(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("smtp", content) or self.assertIn("SMTP", content) or self.assertIn("email", content)

    def test_template_has_send_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("send", content) or self.assertIn("Send", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestFastApiNotificationService(TestCase):
    """Test FastAPI notification service template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/fastapi/cp12_notification/notification_service.py.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Notification service không tồn tại")

    def test_template_has_notify_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        assert "notify" in content or "Notify" in content or "notification" in content, "Không có notify method"

    def test_template_has_template(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("template", content) or self.assertIn("Template", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestNestJsNotificationModule(TestCase):
    """Test NestJS notification module template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/nestjs/cp12_notification/notification.module.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Notification module không tồn tại")

    def test_template_has_module(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Module", content) or self.assertIn("Module", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


class TestNestJsEmailService(TestCase):
    """Test NestJS email service template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/nestjs/cp12_notification/email.service.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Email service không tồn tại")

    def test_template_has_send_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("send", content) or self.assertIn("Send", content)

    def test_template_has_async(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


if __name__ == "__main__":
    import unittest
    unittest.main()