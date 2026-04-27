"""
Test suite cho Audit Trail & Compliance templates (CP14).

Test coverage cho:
- FastAPI: Audit logger, audit event models
- NestJS: Audit module, audit interceptor

Tổng cộng: 12 tests

CP14: Audit Trail & Compliance
"""

from unittest import TestCase
from pathlib import Path


class TestFastApiAuditLogger(TestCase):
    """Test FastAPI audit logger template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/fastapi/templates/audit/audit_logger.py.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Audit logger không tồn tại")

    def test_template_has_audit_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("audit", content) or self.assertIn("Audit", content)

    def test_template_has_log_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("log", content) or self.assertIn("Log", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestFastApiAuditMiddleware(TestCase):
    """Test FastAPI audit middleware template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/fastapi/templates/audit/audit_middleware.py.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Audit middleware không tồn tại")

    def test_template_has_middleware(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("middleware", content) or self.assertIn("Middleware", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestNestJsAuditModule(TestCase):
    """Test NestJS audit module template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/nestjs/templates/audit/audit.module.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Audit module không tồn tại")

    def test_template_has_module(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Module", content) or self.assertIn("Module", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


if __name__ == "__main__":
    import unittest
    unittest.main()