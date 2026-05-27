# coding: utf-8
"""
Mô-đun recipes cho CP29 — Multi-Language Support Generator.

Tạo i18n bundles và language profile từ MIR metadata.
Pipeline gọi auto_generate_i18n_from_mir() để generate context cho templates.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.packs.cp29_multi_language.models import (
    I18nBundle,
    I18nKeyset,
    LanguageProfile,
)
from midicoder.packs.cp29_multi_language.parser import I18nParser

# Locales mặc định
_DEFAULT_LOCALES: list[str] = ["en", "vi"]
_DEFAULT_LOCALE: str = "en"

__all__ = [
    "auto_generate_i18n_from_mir",
    "generate_language_profile",
    "generate_i18n_bundles",
]


def generate_language_profile(
    locales: list[str] | None = None,
    default_locale: str | None = None,
) -> LanguageProfile:
    """Tạo language profile mặc định.

    Args:
        locales: Danh sách locales (mặc định ["en", "vi"]).
        default_locale: Locale mặc định (mặc định "en").

    Returns:
        LanguageProfile đã cấu hình.
    """
    return LanguageProfile(
        id="default",
        locales=locales or _DEFAULT_LOCALES,
        default_locale=default_locale or _DEFAULT_LOCALE,
    )


def generate_i18n_bundles(
    keyset: I18nKeyset,
    locales: list[str] | None = None,
) -> list[I18nBundle]:
    """Tạo i18n bundles cho từng locale từ keyset.

    - Locale "en": dùng description từ DSL làm default translation
    - Locale khác: để trống string (để user điền)

    Args:
        keyset: I18nKeyset chứa các keys đã extract.
        locales: Danh sách locales cần generate bundle.

    Returns:
        Danh sách I18nBundle (1 bundle per locale).
    """
    bundles: list[I18nBundle] = []
    target_locales = locales or _DEFAULT_LOCALES

    for locale in target_locales:
        bundle_keys = []
        for k in keyset.keys:
            if locale == "en":
                # English: dùng description từ DSL
                bundle_keys.append(k)
            else:
                # Các locale khác: key tương tự nhưng description trống
                from midicoder.packs.cp29_multi_language.models import I18nKey

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
) -> I18nKeyset:
    """Master recipe: từ MIR metadata → I18nKeyset hoàn chỉnh.

    Quy trình:
    1. Parse MIR metadata → extract i18n keys
    2. Tạo language profile (default: en + vi)
    3. Tạo i18n bundles per locale

    Args:
        metadata: Dict từ MIR (entities[], commands[], queries[], events[]).

    Returns:
        I18nKeyset với keys và bundles đã generate.
    """
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
