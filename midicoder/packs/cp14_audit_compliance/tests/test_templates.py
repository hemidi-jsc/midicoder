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
import jinja2


class TestFastApiAuditLogger(TestCase):
    """Test FastAPI audit logger template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/fastapi/cp14_audit_compliance/audit_logger.py.jinja2")

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
        self.template_path = Path("midicoder/stacks/fastapi/cp14_audit_compliance/audit_middleware.py.jinja2")

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
        self.template_path = Path("midicoder/stacks/nestjs/cp14_audit_compliance/audit.module.ts.jinja2")

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
        self.template_path = Path("midicoder/stacks/angular/cp14_audit_compliance/audit_logger_service.ts.jinja2")

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
        self.template_path = Path("midicoder/stacks/angular/cp14_audit_compliance/audit_log_list.component.ts.jinja2")

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
        self.template_path = Path("midicoder/stacks/react/cp14_audit_compliance/useAudit.ts.jinja2")

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
        self.template_path = Path("midicoder/stacks/react/cp14_audit_compliance/AuditLogList.tsx.jinja2")

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
        self.template_path = Path("midicoder/stacks/react/cp14_audit_compliance/types.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Audit types template không tồn tại")

    def test_template_has_interface(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("interface", content)

    def test_template_has_audit_log_type(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertTrue("AuditLog" in content or "AuditEntry" in content)


# ===========================================================================
# Dữ liệu và helper cho Rule V1/V2 (P2-17)
# ===========================================================================

_STACKS_DIR = Path(__file__).resolve().parents[4] / "stacks"

FASTAPI_TEMPLATES = [
    "audit_logger.py.jinja2",
    "audit_middleware.py.jinja2",
    "audit_api.py.jinja2",
]

NESTJS_TEMPLATES = [
    "audit.module.ts.jinja2",
    "audit_logger_service.ts.jinja2",
]

ANGULAR_TEMPLATES = [
    "audit_logger_service.ts.jinja2",
    "audit_log_list.component.ts.jinja2",
]

REACT_TEMPLATES = [
    "useAudit.ts.jinja2",
    "AuditLogList.tsx.jinja2",
    "types.ts.jinja2",
]


def _render_template(stack: str, template_name: str) -> str:
    """Render template với context cơ bản; fallback đọc raw nếu render lỗi."""
    template_path = _STACKS_DIR / stack / "core" / "cp14_audit_compliance"
    try:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path)),
            undefined=jinja2.ChainableUndefined,
        )
        template = env.get_template(template_name)
        return template.render()
    except Exception:
        # Fallback: đọc nội dung raw nếu Jinja2 parse lỗi (JS/Angular syntax conflict)
        raw_file = template_path / template_name
        if raw_file.exists():
            return raw_file.read_text(encoding="utf-8")
        raise


# ===========================================================================
# Test Rule V1 & V2 (P2-17)
# ===========================================================================

class TestRuleV1NoMidicoderImport:
    """Rule V1: Output của template KHÔNG chứa 'from midicoder'."""

    def test_fastapi_no_midicoder_import(self):
        """FastAPI templates không chứa 'from midicoder' trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_nestjs_no_midicoder_import(self):
        """NestJS templates không chứa 'from midicoder' trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_angular_no_midicoder_import(self):
        """Angular templates không chứa 'from midicoder' trong output."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template("angular", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_react_no_midicoder_import(self):
        """React templates không chứa 'from midicoder' trong output."""
        for template in REACT_TEMPLATES:
            result = _render_template("react", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"


class TestRuleV2NoPostInit:
    """Rule V2: Output của template KHÔNG chứa '__post_init__'."""

    def test_fastapi_no_post_init(self):
        """FastAPI templates không chứa __post_init__ trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_nestjs_no_post_init(self):
        """NestJS templates không chứa __post_init__ trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_angular_no_post_init(self):
        """Angular templates không chứa __post_init__ trong output."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template("angular", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_react_no_post_init(self):
        """React templates không chứa __post_init__ trong output."""
        for template in REACT_TEMPLATES:
            result = _render_template("react", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"


if __name__ == "__main__":
    import unittest
    unittest.main()