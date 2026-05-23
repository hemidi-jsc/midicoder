# coding: utf-8
"""
Test cho CP43 Jinja2 templates — verify templates tồn tại và parse OK.
"""

import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError


# Đường dẫn đến stacks directory
STACKS_DIR = Path(__file__).parent.parent.parent.parent.parent / "stacks"


class TestFastAPITemplates:
    """Test cho FastAPI Jinja2 templates."""

    def test_version_mixin_template_exists(self) -> None:
        """Kiểm tra version_mixin template tồn tại."""
        template_path = STACKS_DIR / "fastapi" / "core" / "cp43_versioning" / "version_mixin.py.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_soft_delete_mixin_template_exists(self) -> None:
        """Kiểm tra soft_delete_mixin template tồn tại."""
        template_path = STACKS_DIR / "fastapi" / "core" / "cp43_versioning" / "soft_delete_mixin.py.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_entity_history_template_exists(self) -> None:
        """Kiểm tra entity_history template tồn tại."""
        template_path = STACKS_DIR / "fastapi" / "core" / "cp43_versioning" / "entity_history.py.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_history_repository_template_exists(self) -> None:
        """Kiểm tra history_repository template tồn tại."""
        template_path = STACKS_DIR / "fastapi" / "core" / "cp43_versioning" / "history_repository.py.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_audit_logger_template_exists(self) -> None:
        """Kiểm tra version_audit_logger template tồn tại."""
        template_path = STACKS_DIR / "fastapi" / "core" / "cp43_versioning" / "version_audit_logger.py.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_all_fastapi_templates_parse_ok(self) -> None:
        """Kiểm tra tất cả FastAPI templates parse OK (không có TemplateSyntaxError)."""
        template_dir = STACKS_DIR / "fastapi" / "core" / "cp43_versioning"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        for template_file in template_dir.glob("*.jinja2"):
            try:
                template = env.get_template(template_file.name)
                template.render({})
            except TemplateSyntaxError as e:
                pytest.fail(f"Template {template_file.name} có syntax error: {e}")


class TestNestJSTemplates:
    """Test cho NestJS Jinja2 templates."""

    def test_versioned_decorator_template_exists(self) -> None:
        """Kiểm tra versioned decorator template tồn tại."""
        template_path = STACKS_DIR / "nestjs" / "core" / "cp43_versioning" / "versioned.decorator.ts.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_soft_delete_decorator_template_exists(self) -> None:
        """Kiểm tra soft-delete decorator template tồn tại."""
        template_path = STACKS_DIR / "nestjs" / "core" / "cp43_versioning" / "soft-delete.decorator.ts.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_history_entity_template_exists(self) -> None:
        """Kiểm tra history entity template tồn tại."""
        template_path = STACKS_DIR / "nestjs" / "core" / "cp43_versioning" / "history-entity.ts.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_history_service_template_exists(self) -> None:
        """Kiểm tra history service template tồn tại."""
        template_path = STACKS_DIR / "nestjs" / "core" / "cp43_versioning" / "history.service.ts.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_all_nestjs_templates_parse_ok(self) -> None:
        """Kiểm tra tất cả NestJS templates parse OK."""
        template_dir = STACKS_DIR / "nestjs" / "core" / "cp43_versioning"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        for template_file in template_dir.glob("*.jinja2"):
            try:
                template = env.get_template(template_file.name)
                template.render({})
            except TemplateSyntaxError as e:
                pytest.fail(f"Template {template_file.name} có syntax error: {e}")


class TestAngularTemplates:
    """Test cho Angular Jinja2 templates."""

    def test_version_history_service_template_exists(self) -> None:
        """Kiểm tra version history service template tồn tại."""
        template_path = STACKS_DIR / "angular" / "core" / "cp43_versioning" / "version-history.service.ts.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_version_history_component_template_exists(self) -> None:
        """Kiểm tra version history component template tồn tại."""
        template_path = STACKS_DIR / "angular" / "core" / "cp43_versioning" / "version-history.component.ts.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_soft_delete_indicator_template_exists(self) -> None:
        """Kiểm tra soft delete indicator template tồn tại."""
        template_path = STACKS_DIR / "angular" / "core" / "cp43_versioning" / "soft-delete-indicator.component.ts.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_all_angular_templates_parse_ok(self) -> None:
        """Kiểm tra tất cả Angular templates parse OK."""
        template_dir = STACKS_DIR / "angular" / "core" / "cp43_versioning"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        for template_file in template_dir.glob("*.jinja2"):
            try:
                template = env.get_template(template_file.name)
                template.render({})
            except TemplateSyntaxError as e:
                pytest.fail(f"Template {template_file.name} có syntax error: {e}")


class TestReactTemplates:
    """Test cho React Jinja2 templates."""

    def test_types_template_exists(self) -> None:
        """Kiểm tra types template tồn tại."""
        template_path = STACKS_DIR / "react" / "core" / "cp43_versioning" / "types.ts.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_use_version_history_template_exists(self) -> None:
        """Kiểm tra useVersionHistory template tồn tại."""
        template_path = STACKS_DIR / "react" / "core" / "cp43_versioning" / "useVersionHistory.ts.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_version_history_component_template_exists(self) -> None:
        """Kiểm tra VersionHistory template tồn tại."""
        template_path = STACKS_DIR / "react" / "core" / "cp43_versioning" / "VersionHistory.tsx.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_soft_delete_indicator_template_exists(self) -> None:
        """Kiểm tra SoftDeleteIndicator template tồn tại."""
        template_path = STACKS_DIR / "react" / "core" / "cp43_versioning" / "SoftDeleteIndicator.tsx.jinja2"
        assert template_path.exists(), f"Template không tồn tại: {template_path}"

    def test_all_react_templates_parse_ok(self) -> None:
        """Kiểm tra tất cả React templates parse OK."""
        template_dir = STACKS_DIR / "react" / "core" / "cp43_versioning"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        for template_file in template_dir.glob("*.jinja2"):
            try:
                template = env.get_template(template_file.name)
                template.render({})
            except TemplateSyntaxError as e:
                pytest.fail(f"Template {template_file.name} có syntax error: {e}")


class TestTemplateContent:
    """Test cho nội dung templates."""

    def test_no_from_midicoder_in_templates(self) -> None:
        """Kiểm tra templates không có 'from midicoder'."""
        for stack in ["fastapi", "nestjs", "angular", "react"]:
            template_dir = STACKS_DIR / stack / "core" / "cp43_versioning"
            for template_file in template_dir.glob("*.jinja2"):
                content = template_file.read_text(encoding="utf-8")
                assert "from midicoder" not in content, (
                    f"Template {stack}/{template_file.name} chứa 'from midicoder'"
                )

    def test_no_post_init_in_templates(self) -> None:
        """Kiểm tra templates không có __post_init__."""
        for stack in ["fastapi", "nestjs", "angular", "react"]:
            template_dir = STACKS_DIR / stack / "core" / "cp43_versioning"
            for template_file in template_dir.glob("*.jinja2"):
                content = template_file.read_text(encoding="utf-8")
                assert "__post_init__" not in content, (
                    f"Template {stack}/{template_file.name} chứa '__post_init__'"
                )

    def test_fastapi_templates_have_vietnamese_comments(self) -> None:
        """Kiểm tra FastAPI templates có comments tiếng Việt."""
        template_dir = STACKS_DIR / "fastapi" / "core" / "cp43_versioning"
        for template_file in template_dir.glob("*.jinja2"):
            content = template_file.read_text(encoding="utf-8")
            # Kiểm tra có ít nhất 1 comment/docstring tiếng Việt
            assert any(char in content for char in ["ă", "â", "ê", "ô", "ơ", "ư", "đ", "à", "á", "ạ", "ả", "ã", "ầ", "ấ", "ậ", "ẩ", "ẫ", "ẫ", "ằ", "ắ", "ặ", "ẳ", "ẵ", "è", "é", "ẹ", "ẻ", "ẽ", "ề", "ế", "ệ", "ể", "ễ", "ì", "í", "ị", "ỉ", "ĩ", "ò", "ó", "ọ", "ỏ", "õ", "ồ", "ố", "ộ", "ổ", "ỗ", "ờ", "ớ", "ợ", "ở", "ỡ", "ù", "ú", "ụ", "ủ", "ũ", "ừ", "ứ", "ự", "ử", "ữ", "ỳ", "ý", "ỵ", "ỷ", "ỹ"]), (
                f"Template {template_file.name} thiếu comments tiếng Việt"
            )
