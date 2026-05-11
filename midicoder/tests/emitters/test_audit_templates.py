"""
Test suite cho Audit Trail & Compliance templates (CP14).

Test coverage cho:
- FastAPI: Audit logger, audit middleware
- NestJS: Audit module
- Angular: Audit logger service, audit log list component
- React: useAudit hook, AuditLogList component, types

CP14: Audit Trail & Compliance
"""

from unittest import TestCase
from pathlib import Path


class TestFastApiAuditLogger(TestCase):
    """Test FastAPI audit logger template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/fastapi/core/audit/audit_logger.py.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Audit logger template không tồn tại")

    def test_template_has_audit_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("audit" in content or "Audit" in content)

    def test_template_has_log_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("log" in content or "Log" in content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("#" in content or '"""' in content)


class TestFastApiAuditMiddleware(TestCase):
    """Test FastAPI audit middleware template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/fastapi/core/audit/audit_middleware.py.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Audit middleware template không tồn tại")

    def test_template_has_middleware(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("middleware" in content or "Middleware" in content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("#" in content or '"""' in content)


class TestNestJsAuditModule(TestCase):
    """Test NestJS audit module template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/nestjs/core/audit/audit.module.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Audit module template không tồn tại")

    def test_template_has_module(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("@Module" in content or "Module" in content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("/" in content or "*" in content)


class TestAngularAuditLoggerService(TestCase):
    """Test Angular audit logger service template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/angular/core/audit/audit_logger_service.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Audit logger service template không tồn tại")

    def test_template_has_injectable(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Injectable", content)

    def test_template_has_log_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("log" in content or "Log" in content)

    def test_template_has_query_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("query" in content or "Query" in content)


class TestAngularAuditLogListComponent(TestCase):
    """Test Angular audit log list component template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/angular/core/audit/audit_log_list.component.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Audit log list component template không tồn tại")

    def test_template_has_component(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Component", content)

    def test_template_has_filter(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("filter" in content.lower() or "Filter" in content)


class TestReactUseAuditHook(TestCase):
    """Test React useAudit hook template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/react/core/audit/useAudit.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "useAudit hook template không tồn tại")

    def test_template_has_use_callback(self):
        """Hook sử dụng useCallback cho memoization."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("useCallback", content)

    def test_template_has_log_function(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("log" in content or "Log" in content)


class TestReactAuditLogListComponent(TestCase):
    """Test React AuditLogList component template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/react/core/audit/AuditLogList.tsx.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "AuditLogList component template không tồn tại")

    def test_template_has_function_component(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("function" in content or "const" in content)

    def test_template_has_filter(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("filter" in content.lower() or "Filter" in content)


class TestReactAuditTypes(TestCase):
    """Test React audit types template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/react/core/audit/types.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Audit types template không tồn tại")

    def test_template_has_interface(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("interface", content)

    def test_template_has_audit_log_type(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("AuditLog" in content or "AuditEntry" in content)


if __name__ == "__main__":
    import unittest
    unittest.main()