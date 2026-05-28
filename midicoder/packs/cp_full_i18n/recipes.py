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

from midicoder.packs.cp_full_i18n.models import (
    CacheBackend,
    CacheConfig,
    LocaleConfig,
    TranslationEntry,
)
from midicoder.packs.cp_full_i18n.parser import I18nRuntimeIR


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
    # CP29 merged exports
    "auto_generate_i18n_from_mir",
    "generate_language_profile",
    "generate_i18n_bundles",
]


# ===========================================================================
# CP29 — Key Extraction Recipes (merged from cp29_multi_language)
# ===========================================================================

# Locales mặc định
_DEFAULT_LOCALES: list[str] = ["en", "vi"]
_DEFAULT_LOCALE: str = "en"


def generate_language_profile(
    locales: list[str] | None = None,
    default_locale: str | None = None,
) -> "LanguageProfile":  # type: ignore[name-defined]
    """Tạo language profile mặc định.

    Args:
        locales: Danh sách locales (mặc định ["en", "vi"]).
        default_locale: Locale mặc định (mặc định "en").

    Returns:
        LanguageProfile đã cấu hình.
    """
    from midicoder.packs.cp_full_i18n.models import LanguageProfile

    return LanguageProfile(
        id="default",
        locales=locales or _DEFAULT_LOCALES,
        default_locale=default_locale or _DEFAULT_LOCALE,
    )


def generate_i18n_bundles(
    keyset: "I18nKeyset",  # type: ignore[name-defined]
    locales: list[str] | None = None,
) -> list:  # type: ignore[type-arg]
    """Tạo i18n bundles cho từng locale từ keyset.

    Args:
        keyset: I18nKeyset chứa các keys đã extract.
        locales: Danh sách locales cần generate bundle.

    Returns:
        Danh sách I18nBundle (1 bundle per locale).
    """
    from midicoder.packs.cp_full_i18n.models import I18nBundle, I18nKey

    bundles: list = []
    target_locales = locales or _DEFAULT_LOCALES

    for locale in target_locales:
        bundle_keys = []
        for k in keyset.keys:
            if locale == "en":
                bundle_keys.append(k)
            else:
                empty_key = I18nKey(
                    key=k.key,
                    namespace=k.namespace,
                    entity_id=k.entity_id,
                    category=k.category,
                    path=k.path,
                    description="",
                )
                bundle_keys.append(empty_key)

        bundle = I18nBundle(locale=locale, keys=bundle_keys)
        bundles.append(bundle)

    return bundles


def auto_generate_i18n_from_mir(
    metadata: dict[str, Any] | None,
) -> "I18nKeyset":  # type: ignore[name-defined]
    """Master recipe: từ MIR metadata → I18nKeyset hoàn chỉnh.

    Args:
        metadata: Dict từ MIR (entities[], commands[], queries[], events[]).

    Returns:
        I18nKeyset với keys và bundles đã generate.
    """
    from midicoder.packs.cp_full_i18n.models import I18nKeyset
    from midicoder.packs.cp_full_i18n.parser import I18nParser

    if metadata is None:
        return I18nKeyset()

    # Bước 1: Extract keys từ MIR metadata
    parser = I18nParser()
    keyset = parser.parse_from_metadata(metadata)

    # Bước 2: Tạo language profile
    profile = generate_language_profile()

    # Bước 3: Tạo bundles per locale
    bundles = generate_i18n_bundles(keyset, locales=profile.locales)
    for bundle in bundles:
        keyset.add_bundle(bundle)

    return keyset
