"""
Tests cho CP12 I18n Template Registry.

Test coverage: 12 tests
"""

from __future__ import annotations

import pytest
from midicoder.packs.cp_full_notification.models import (
    NotificationChannel,
    NotificationTemplate,
)
from midicoder.packs.cp_full_notification.i18n import I18nTemplateRegistry


class TestI18nTemplateRegistry:
    """Tests cho I18nTemplateRegistry."""

    def _make_template(self, tid: str, locale: str) -> NotificationTemplate:
        return NotificationTemplate(
            template_id=tid,
            channel=NotificationChannel.EMAIL,
            subject=f"Subject ({locale})",
            body_html=f"<p>Body ({locale})</p>",
            locale=locale,
        )

    def test_register_and_resolve_exact(self):
        """Resolve exact locale match."""
        reg = I18nTemplateRegistry()
        reg.register("welcome", "vi-VN", self._make_template("welcome", "vi-VN"))
        result = reg.resolve("welcome", "vi-VN")
        assert result is not None
        assert result.subject == "Subject (vi-VN)"

    def test_resolve_language_only_fallback(self):
        """Fallback từ vi-VN → vi."""
        reg = I18nTemplateRegistry()
        reg.register("welcome", "vi", self._make_template("welcome", "vi"))
        result = reg.resolve("welcome", "vi-VN")
        assert result is not None
        assert result.locale == "vi"

    def test_resolve_english_fallback(self):
        """Fallback từ fr-CA → fr → en."""
        reg = I18nTemplateRegistry()
        reg.register("welcome", "en", self._make_template("welcome", "en"))
        result = reg.resolve("welcome", "fr-CA")
        assert result is not None
        assert result.locale == "en"

    def test_resolve_default_template(self):
        """Fallback → default template."""
        reg = I18nTemplateRegistry()
        default = self._make_template("welcome", "default")
        reg.register_default("welcome", default)
        result = reg.resolve("welcome", "zh-CN")
        assert result is not None

    def test_resolve_not_found(self):
        """Return None khi không có template nào."""
        reg = I18nTemplateRegistry()
        result = reg.resolve("nonexistent", "en")
        assert result is None

    def test_get_available_locales(self):
        """Lấy danh sách locales available."""
        reg = I18nTemplateRegistry()
        reg.register("welcome", "vi", self._make_template("welcome", "vi"))
        reg.register("welcome", "en", self._make_template("welcome", "en"))
        locales = reg.get_available_locales("welcome")
        assert "en" in locales
        assert "vi" in locales

    def test_has_template_exact(self):
        """has_template với locale cụ thể."""
        reg = I18nTemplateRegistry()
        reg.register("welcome", "vi", self._make_template("welcome", "vi"))
        assert reg.has_template("welcome", "vi") is True
        assert reg.has_template("welcome", "en") is False

    def test_has_template_any_locale(self):
        """has_template bất kỳ locale."""
        reg = I18nTemplateRegistry()
        reg.register("welcome", "vi", self._make_template("welcome", "vi"))
        assert reg.has_template("welcome") is True
        assert reg.has_template("nonexistent") is False

    def test_has_template_default_only(self):
        """has_template với default template."""
        reg = I18nTemplateRegistry()
        reg.register_default("welcome", self._make_template("welcome", "default"))
        assert reg.has_template("welcome") is True

    def test_template_count(self):
        """Đếm số locales cho template."""
        reg = I18nTemplateRegistry()
        reg.register("welcome", "vi", self._make_template("welcome", "vi"))
        reg.register("welcome", "en", self._make_template("welcome", "en"))
        reg.register("welcome", "fr", self._make_template("welcome", "fr"))
        assert reg.template_count("welcome") == 3

    def test_template_count_with_default(self):
        """Đếm bao gồm default template."""
        reg = I18nTemplateRegistry()
        reg.register("welcome", "vi", self._make_template("welcome", "vi"))
        reg.register_default("welcome", self._make_template("welcome", "default"))
        assert reg.template_count("welcome") == 2

    def test_fallback_chain_order(self):
        """Fallback chain đúng thứ tự: exact → lang → en → default."""
        reg = I18nTemplateRegistry()
        reg.register("t", "en", self._make_template("t", "en"))
        reg.register("t", "vi", self._make_template("t", "vi"))
        reg.register_default("t", self._make_template("t", "default"))

        # Exact match
        assert reg.resolve("t", "vi").locale == "vi"
        # English fallback (không có fr)
        assert reg.resolve("t", "fr-CA").locale == "en"
