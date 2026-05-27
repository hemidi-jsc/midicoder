# coding: utf-8
"""
Mô-đun recipes cho CP39 — i18n/L10n Runtime.

Cung cấp các recipe patterns để generate i18n runtime với locales,
translations mẫu, và cache config theo common use cases.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from midicoder.packs.cp39_i18n_runtime.models import (
    CacheBackend,
    CacheConfig,
    LocaleConfig,
    TranslationEntry,
)
from midicoder.packs.cp39_i18n_runtime.parser import I18nRuntimeIR


@dataclass
class RecipeOutput:
    """Kết quả của recipe.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: I18nRuntimeIR kết quả
    """
    name: str
    description: str
    ir: I18nRuntimeIR


def basic_i18n_recipe() -> RecipeOutput:
    """Recipe: Cấu hình i18n cơ bản với 2 locales (en, vi) + memory cache.

    Tạo locales mặc định, translations mẫu cho namespace 'common',
    và memory cache — phù hợp cho dev/prototyping.

    Returns:
        RecipeOutput với cấu hình cơ bản
    """
    locales = [
        LocaleConfig(
            code="en",
            name="English",
            is_default=True,
            date_format="MM/dd/yyyy",
            number_format="1,000,000",
            currency_code="USD",
        ),
        LocaleConfig(
            code="vi",
            name="Tiếng Việt",
            is_default=False,
            date_format="dd/MM/yyyy",
            number_format="1.000.000",
            currency_code="VND",
            fallback_locale="en",
        ),
    ]

    translations = [
        # Common namespace
        TranslationEntry(key="welcome_message", namespace="common", locale="en", value="Welcome!"),
        TranslationEntry(key="welcome_message", namespace="common", locale="vi", value="Chào mừng!"),
        TranslationEntry(key="goodbye_message", namespace="common", locale="en", value="Goodbye!"),
        TranslationEntry(key="goodbye_message", namespace="common", locale="vi", value="Tạm biệt!"),
        TranslationEntry(key="save", namespace="common", locale="en", value="Save"),
        TranslationEntry(key="save", namespace="common", locale="vi", value="Lưu"),
        TranslationEntry(key="cancel", namespace="common", locale="en", value="Cancel"),
        TranslationEntry(key="cancel", namespace="common", locale="vi", value="Hủy"),
        TranslationEntry(key="delete", namespace="common", locale="en", value="Delete"),
        TranslationEntry(key="delete", namespace="common", locale="vi", value="Xóa"),
        TranslationEntry(key="search", namespace="common", locale="en", value="Search"),
        TranslationEntry(key="search", namespace="common", locale="vi", value="Tìm kiếm"),
        TranslationEntry(key="loading", namespace="common", locale="en", value="Loading..."),
        TranslationEntry(key="loading", namespace="common", locale="vi", value="Đang tải..."),
        TranslationEntry(key="error_occurred", namespace="common", locale="en", value="An error occurred"),
        TranslationEntry(key="error_occurred", namespace="common", locale="vi", value="Đã xảy ra lỗi"),
        # Auth namespace
        TranslationEntry(key="login", namespace="auth", locale="en", value="Login"),
        TranslationEntry(key="login", namespace="auth", locale="vi", value="Đăng nhập"),
        TranslationEntry(key="logout", namespace="auth", locale="en", value="Logout"),
        TranslationEntry(key="logout", namespace="auth", locale="vi", value="Đăng xuất"),
        TranslationEntry(key="register", namespace="auth", locale="en", value="Register"),
        TranslationEntry(key="register", namespace="auth", locale="vi", value="Đăng ký"),
        TranslationEntry(key="forgot_password", namespace="auth", locale="en", value="Forgot Password"),
        TranslationEntry(key="forgot_password", namespace="auth", locale="vi", value="Quên mật khẩu"),
    ]

    cache_config = CacheConfig(
        backend=CacheBackend.MEMORY,
        ttl_seconds=300,
        max_size=5000,
    )

    return RecipeOutput(
        name="basic_i18n",
        description="2 locales (en, vi), memory cache, basic translations",
        ir=I18nRuntimeIR(locales=locales, translations=translations, cache_config=cache_config),
    )


def multitenant_i18n_recipe() -> RecipeOutput:
    """Recipe: i18n đa ngôn ngữ + Redis cache + tenant override support.

    Tạo 3 locales (en, vi, fr), Redis cache production-ready,
    và translations mẫu cho tenant-specific overrides.

    Returns:
        RecipeOutput với cấu hình multi-tenant
    """
    locales = [
        LocaleConfig(
            code="en",
            name="English",
            is_default=True,
            date_format="MM/dd/yyyy",
            number_format="1,000,000",
            currency_code="USD",
        ),
        LocaleConfig(
            code="vi",
            name="Tiếng Việt",
            is_default=False,
            date_format="dd/MM/yyyy",
            number_format="1.000.000",
            currency_code="VND",
            fallback_locale="en",
        ),
        LocaleConfig(
            code="fr",
            name="Français",
            is_default=False,
            date_format="dd/MM/yyyy",
            number_format="1 000 000",
            currency_code="EUR",
            fallback_locale="en",
        ),
    ]

    translations = [
        # Global translations
        TranslationEntry(key="welcome_message", namespace="common", locale="en", value="Welcome!"),
        TranslationEntry(key="welcome_message", namespace="common", locale="vi", value="Chào mừng!"),
        TranslationEntry(key="welcome_message", namespace="common", locale="fr", value="Bienvenue!"),
        TranslationEntry(key="save", namespace="common", locale="en", value="Save"),
        TranslationEntry(key="save", namespace="common", locale="vi", value="Lưu"),
        TranslationEntry(key="save", namespace="common", locale="fr", value="Enregistrer"),
        TranslationEntry(key="cancel", namespace="common", locale="en", value="Cancel"),
        TranslationEntry(key="cancel", namespace="common", locale="vi", value="Hủy"),
        TranslationEntry(key="cancel", namespace="common", locale="fr", value="Annuler"),
        TranslationEntry(key="delete", namespace="common", locale="en", value="Delete"),
        TranslationEntry(key="delete", namespace="common", locale="vi", value="Xóa"),
        TranslationEntry(key="delete", namespace="common", locale="fr", value="Supprimer"),
        TranslationEntry(key="search", namespace="common", locale="en", value="Search"),
        TranslationEntry(key="search", namespace="common", locale="vi", value="Tìm kiếm"),
        TranslationEntry(key="search", namespace="common", locale="fr", value="Rechercher"),
        # Tenant-specific overrides
        TranslationEntry(
            key="welcome_message", namespace="common", locale="vi",
            value="Chào mừng bạn đến với cửa hàng!",
            tenant_id="tenant_demo",
        ),
        TranslationEntry(
            key="welcome_message", namespace="common", locale="fr",
            value="Bienvenue dans notre boutique!",
            tenant_id="tenant_demo",
        ),
    ]

    cache_config = CacheConfig(
        backend=CacheBackend.REDIS,
        ttl_seconds=600,
        max_size=50000,
        redis_url="redis://localhost:6379/0",
    )

    return RecipeOutput(
        name="multitenant_i18n",
        description="3 locales (en, vi, fr), Redis cache, tenant override support",
        ir=I18nRuntimeIR(locales=locales, translations=translations, cache_config=cache_config),
    )


__all__ = [
    "RecipeOutput",
    "basic_i18n_recipe",
    "multitenant_i18n_recipe",
]
