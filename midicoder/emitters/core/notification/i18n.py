"""
I18n Template Registry Module.

Module này cung cấp I18nTemplateRegistry:
- register(): Dang ky template theo locale
- resolve(): Resolve template voi fallback chain (vi-VN -> en -> default)
- Support BCP 47 locale codes (vi-VN, en-US, fr-FR, etc.)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.emitters.core.notification.models import (
    NotificationTemplate,
)


# Template key format: (template_id, locale)
_TEMPLATE_KEY = tuple[str, str]


class I18nTemplateRegistry:
    """
    Registry cho multi-language notification templates.

    Support fallback chain theo BCP 47 locale codes:
    - vi-VN -> vi -> en -> default template
    - fr-CA -> fr -> en -> default template
    - en-US -> en -> default template

    Example:
        >>> registry = I18nTemplateRegistry()
        >>> registry.register("welcome", "vi-VN", template_vi)
        >>> registry.register("welcome", "en", template_en)
        >>> result = registry.resolve("welcome", "vi-VN")
    """

    def __init__(self) -> None:
        """Khởi tạo I18nTemplateRegistry rỗng."""
        self._templates: dict[_TEMPLATE_KEY, NotificationTemplate] = {}
        self._default_templates: dict[str, NotificationTemplate] = {}

    def register(
        self,
        template_id: str,
        locale: str,
        template: NotificationTemplate,
    ) -> None:
        """
        Đăng ký notification template cho locale cụ thể.

        Args:
            template_id: Định danh duy nhất của template
            locale: BCP 47 locale code (vi-VN, en-US, fr-FR, etc.)
            template: NotificationTemplate instance
        """
        key: _TEMPLATE_KEY = (template_id, locale)
        self._templates[key] = template

        # Nếu locale là "en", cũng xem là default fallback
        if locale == "en":
            self._default_templates[template_id] = template

    def register_default(
        self,
        template_id: str,
        template: NotificationTemplate,
    ) -> None:
        """
        Đăng ký default template (fallback cuối cùng).

        Default template được sử dụng khi không tìm thấy
        template cho locale cụ thể.

        Args:
            template_id: Định danh duy nhất của template
            template: NotificationTemplate instance (default)
        """
        self._default_templates[template_id] = template

    def resolve(
        self,
        template_id: str,
        preferred_locale: str,
    ) -> NotificationTemplate | None:
        """
        Resolve template theo preferred locale với fallback chain.

        Fallback chain:
        1. Exact match: vi-VN
        2. Language only: vi
        3. English: en
        4. Default template

        Args:
            template_id: Định danh duy nhất của template
            preferred_locale: Preferred locale (BCP 47)

        Returns:
            NotificationTemplate nếu tìm thấy, None nếu không có template nào
        """
        # 1. Exact match: vi-VN
        exact_key: _TEMPLATE_KEY = (template_id, preferred_locale)
        if exact_key in self._templates:
            return self._templates[exact_key]

        # 2. Language only: vi-VN -> vi
        if "-" in preferred_locale:
            language_only = preferred_locale.split("-")[0]
            lang_key: _TEMPLATE_KEY = (template_id, language_only)
            if lang_key in self._templates:
                return self._templates[lang_key]

        # 3. English fallback: en
        en_key: _TEMPLATE_KEY = (template_id, "en")
        if en_key in self._templates:
            return self._templates[en_key]

        # 4. Default template
        if template_id in self._default_templates:
            return self._default_templates[template_id]

        return None

    def get_available_locales(self, template_id: str) -> list[str]:
        """
        Lấy danh sách locales có sẵn cho template_id.

        Args:
            template_id: Định danh duy nhất của template

        Returns:
            List of locale codes available for this template
        """
        locales: list[str] = []
        for (tid, locale), _template in self._templates.items():
            if tid == template_id and locale not in locales:
                locales.append(locale)

        if template_id in self._default_templates:
            default_locale = self._default_templates[template_id].locale
            if default_locale not in locales:
                locales.append(default_locale)

        return sorted(locales)

    def has_template(self, template_id: str, locale: str | None = None) -> bool:
        """
        Kiểm tra template có tồn tại không.

        Args:
            template_id: Định danh duy nhất của template
            locale: Locale code (nếu None, kiểm tra bất kỳ locale nào)

        Returns:
            True nếu template tồn tại
        """
        if locale is not None:
            key: _TEMPLATE_KEY = (template_id, locale)
            return key in self._templates

        # Kiểm tra bất kỳ locale nào
        for (tid, _locale) in self._templates.keys():
            if tid == template_id:
                return True

        return template_id in self._default_templates

    def template_count(self, template_id: str) -> int:
        """
        Đếm số locales có sẵn cho template_id.

        Args:
            template_id: Định danh duy nhất của template

        Returns:
            Số lượng locales available
        """
        count = sum(
            1 for (tid, _locale) in self._templates.keys() if tid == template_id
        )
        if template_id in self._default_templates:
            # Default template được tính nếu không trùng với locales khác
            default_locale = self._default_templates[template_id].locale
            if (template_id, default_locale) not in self._templates:
                count += 1
        return count