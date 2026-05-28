"""
Tests cho CP12 Template Engine.

Test coverage:
- TemplateRenderer: 8 tests
- TemplateValidator: 6 tests
- RenderedTemplate: 2 tests

Tổng: 16 tests
"""

from __future__ import annotations

import pytest
from datetime import datetime


# ============================================================================
# Test TemplateRenderer
# ============================================================================


class TestTemplateRenderer:
    """Tests cho TemplateRenderer class."""

    def test_render_simple_variable(self):
        """Render simple variable {{name}}."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateRenderer

        renderer = TemplateRenderer()
        result = renderer.render_string("Xin chào {{name}}!", {"name": "Minh"})
        assert result == "Xin chào Minh!"

    def test_render_multiple_variables(self):
        """Render nhiều variables."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateRenderer

        renderer = TemplateRenderer()
        result = renderer.render_string(
            "{{name}}, {{email}}",
            {"name": "Minh", "email": "minh@test.com"}
        )
        assert "Minh" in result
        assert "minh@test.com" in result

    def test_render_nested_variable(self):
        """Render nested variable {{user.name}}."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateRenderer

        renderer = TemplateRenderer()
        result = renderer.render_string(
            "{{user.name}}",
            {"user": {"name": "Minh"}}
        )
        assert result == "Minh"

    def test_render_filter_uppercase(self):
        """Render filter uppercase."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateRenderer

        renderer = TemplateRenderer()
        result = renderer.render_string("{{name|uppercase}}", {"name": "minh"})
        assert result == "MINH"

    def test_render_filter_currency(self):
        """Render filter currency."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateRenderer

        renderer = TemplateRenderer()
        result = renderer.render_string("{{price|currency}}", {"price": "1000"})
        assert "VND" in result

    def test_render_missing_variable_keeps_original(self):
        """Giữ nguyên variable nếu không có trong data."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateRenderer

        renderer = TemplateRenderer()
        result = renderer.render_string("{{missing}}", {})
        assert result == "{{missing}}"

    def test_render_notification_template(self):
        """Render NotificationTemplate hoàn chỉnh."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateRenderer
        from midicoder.packs.cp_full_notification.models import NotificationTemplate, NotificationChannel

        renderer = TemplateRenderer()
        template = NotificationTemplate(
            template_id="welcome",
            channel=NotificationChannel.EMAIL,
            subject="Chào {{name}}",
            body_html="<p>{{name}}</p>",
            body_text="Chào {{name}}",
        )
        rendered = renderer.render(template, {"name": "Minh"})
        assert rendered.subject == "Chào Minh"
        assert rendered.body_html == "<p>Minh</p>"

    def test_render_no_variables(self):
        """Render string không có variable."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateRenderer

        renderer = TemplateRenderer()
        result = renderer.render_string("Xin chào thế giới!", {})
        assert result == "Xin chào thế giới!"


# ============================================================================
# Test TemplateValidator
# ============================================================================


class TestTemplateValidator:
    """Tests cho TemplateValidator class."""

    def test_validate_syntax_valid(self):
        """Validate syntax với template hợp lệ."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateValidator

        validator = TemplateValidator()
        errors = validator.validate_syntax("Xin chào {{name}}!")
        assert len(errors) == 0

    def test_validate_syntax_unclosed(self):
        """Validate syntax với template unclosed."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateValidator

        validator = TemplateValidator()
        errors = validator.validate_syntax("Xin chào {{name")
        assert len(errors) > 0

    def test_extract_variables(self):
        """Extract variables từ template."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateValidator

        validator = TemplateValidator()
        vars = validator.extract_variables("Xin chào {{name}}, email: {{email}}")
        assert "name" in vars
        assert "email" in vars
        assert len(vars) == 2

    def test_extract_variables_with_filters(self):
        """Extract variables có filter."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateValidator

        validator = TemplateValidator()
        vars = validator.extract_variables("{{price|currency}}, {{name|uppercase}}")
        assert "price" in vars
        assert "name" in vars

    def test_validate_payload_valid(self):
        """Validate payload đầy đủ."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateValidator

        validator = TemplateValidator()
        errors = validator.validate_payload(
            "Xin chào {{name}}",
            {"name": "Minh"}
        )
        assert len(errors) == 0

    def test_validate_payload_missing(self):
        """Validate payload thiếu variable."""
        from midicoder.packs.cp_full_notification.template_engine import TemplateValidator

        validator = TemplateValidator()
        errors = validator.validate_payload(
            "Xin chào {{name}}, email: {{email}}",
            {"name": "Minh"}
        )
        assert len(errors) > 0


# ============================================================================
# Test RenderedTemplate
# ============================================================================


class TestRenderedTemplate:
    """Tests cho RenderedTemplate dataclass."""

    def test_rendered_template_creation(self):
        """Tạo RenderedTemplate."""
        from midicoder.packs.cp_full_notification.template_engine import RenderedTemplate

        rt = RenderedTemplate(
            template_id="welcome",
            subject="Chào Minh",
            body_html="<p>Chào Minh</p>",
            body_text="Chào Minh",
        )
        assert rt.template_id == "welcome"
        assert rt.subject == "Chào Minh"

    def test_rendered_template_to_dict(self):
        """RenderedTemplate.to_dict() trả về dict đúng."""
        from midicoder.packs.cp_full_notification.template_engine import RenderedTemplate

        rt = RenderedTemplate(
            template_id="t1",
            subject="S",
            body_html="H",
            body_text="T",
        )
        d = rt.to_dict()
        assert d["template_id"] == "t1"
        assert d["subject"] == "S"
