"""
Mô-đun data models cho CP29 — Multi-Language Support Generator.

Định nghĩa:
- I18nKey: Một cặp key-value cho translation (dotted namespace convention)
- LanguageProfile: Cấu hình ngôn ngữ hỗ trợ (locales, default, fallback)
- I18nBundle: Tập keys + translations cho 1 locale cụ thể
- I18nKeyset: Collection quản lý toàn bộ keys và bundles
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager

EM = MidicoderErrorManager()

# Không chạy bởi pytest
__test__ = False

# Catalog: namespace hợp lệ cho i18n key
_VALID_NAMESPACES: set[str] = {"entity", "command", "query", "event"}


@dataclass(frozen=False)
class I18nKey:
    """Một i18n key theo dotted namespace convention.

    Convention đặt tên:
    - Entity field: entity.{entity_snake}.field.{field_snake}
    - Command: command.{command_snake}
    - Query: query.{query_snake}
    - Event: event.{event_snake}

    Attributes:
        key: Dotted key (vd: "entity.customer.field.name")
        namespace: Namespace (entity/command/query/event)
        entity_id: ID của entity/command/query/event trong DSL
        category: Loại key (field, action, label)
        path: Đường dẫn field (chỉ dùng khi namespace="entity")
        description: Mô tả — dùng làm default translation (en)
    """

    key: str
    namespace: str
    entity_id: str
    category: str
    path: str | None = None
    description: str = ""

    __test__ = False  # Không chạy bởi pytest

    def __post_init__(self) -> None:
        """Validate key và namespace."""
        if not self.key or not self.key.strip():
            raise EM.raise_error(ErrorCode.CP29_EMPTY_KEY)

        if self.namespace not in _VALID_NAMESPACES:
            raise EM.raise_error(
                ErrorCode.CP29_INVALID_KEY_FORMAT,
                namespace=self.namespace,
                valid=list(_VALID_NAMESPACES),
            )


@dataclass(frozen=False)
class LanguageProfile:
    """Cấu hình ngôn ngữ hỗ trợ cho hệ thống.

    Attributes:
        id: Profile identifier
        locales: Danh sách locale hỗ trợ (vd: ["en", "vi"])
        default_locale: Locale mặc định
        fallback_chain: Thứ tự fallback khi không tìm thấy translation
    """

    id: str
    locales: list[str]
    default_locale: str
    fallback_chain: list[str] | None = None

    __test__ = False  # Không chạy bởi pytest

    def __post_init__(self) -> None:
        """Validate profile configuration."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(ErrorCode.CP29_EMPTY_PROFILE_ID)

        if not self.locales:
            raise EM.raise_error(
                ErrorCode.CP29_INVALID_LOCALE,
                detail="Locales list cannot be empty",
            )

        # Kiểm tra duplicate locale
        if len(self.locales) != len(set(self.locales)):
            raise EM.raise_error(
                ErrorCode.CP29_DUPLICATE_LOCALE,
                locales=self.locales,
            )

        # Default locale phải nằm trong danh sách locales
        if self.default_locale not in self.locales:
            raise EM.raise_error(
                ErrorCode.CP29_INVALID_LOCALE,
                default_locale=self.default_locale,
                available=self.locales,
            )

        # Fallback chain mặc định
        if self.fallback_chain is None:
            object.__setattr__(self, "fallback_chain", [self.default_locale])


@dataclass(frozen=False)
class I18nBundle:
    """Tập keys + translations cho 1 locale cụ thể.

    Mỗi bundle đại diện cho 1 file translation (vd: messages.en.po, common.vi.json).

    Attributes:
        locale: Locale code (vd: "en", "vi")
        keys: Danh sách I18nKey trong bundle này
    """

    locale: str
    keys: list[I18nKey]

    __test__ = False  # Không chạy bởi pytest

    def __post_init__(self) -> None:
        """Validate locale code."""
        if not self.locale or not self.locale.strip():
            raise EM.raise_error(
                ErrorCode.CP29_INVALID_LOCALE,
                detail="Locale code cannot be empty",
            )

    def get_translation(self, key: str) -> str | None:
        """Lấy translation (description) của 1 key.

        Args:
            key: Dotted key cần tìm.

        Returns:
            Description của key (dùng làm default translation), hoặc None nếu không tìm thấy.
        """
        for k in self.keys:
            if k.key == key:
                return k.description
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize bundle sang dict (dotted key → description).

        Returns:
            Dict có "locale" và "keys" (dict mapping key → description).
        """
        keys_dict: dict[str, str] = {}
        for k in self.keys:
            keys_dict[k.key] = k.description
        return {"locale": self.locale, "keys": keys_dict}


@dataclass(frozen=False)
class I18nKeyset:
    """Collection quản lý toàn bộ i18n keys và bundles.

    Keys được tự động sắp xếp theo alphabet để đảm bảo deterministic output.

    Attributes:
        keys: Tất cả i18n keys đã extract từ MIR metadata
        bundles: Các bundle per-locale
    """

    keys: list[I18nKey] = field(default_factory=list)
    bundles: list[I18nBundle] = field(default_factory=list)

    __test__ = False  # Không chạy bởi pytest

    def add_key(self, key: I18nKey) -> None:
        """Thêm key vào collection (sorted, detect duplicate).

        Args:
            key: I18nKey cần thêm.

        Raises:
            MidicoderError: Nếu key đã tồn tại (MDC-CP29-004).
        """
        # Kiểm tra duplicate
        if any(existing.key == key.key for existing in self.keys):
            raise EM.raise_error(ErrorCode.CP29_KEY_CONFLICT, key=key.key)

        self.keys.append(key)
        # Giữ sorted theo key
        self.keys.sort(key=lambda k: k.key)

    def get_key_by_id(self, key_id: str) -> I18nKey | None:
        """Lấy key theo dotted key ID.

        Args:
            key_id: Dotted key (vd: "entity.customer.field.name").

        Returns:
            I18nKey hoặc None nếu không tìm thấy.
        """
        for k in self.keys:
            if k.key == key_id:
                return k
        return None

    def add_bundle(self, bundle: I18nBundle) -> None:
        """Thêm bundle vào collection.

        Args:
            bundle: I18nBundle cần thêm.
        """
        self.bundles.append(bundle)

    def get_bundle_by_locale(self, locale: str) -> I18nBundle | None:
        """Lấy bundle theo locale code.

        Args:
            locale: Locale code (vd: "en", "vi").

        Returns:
            I18nBundle hoặc None nếu không tìm thấy.
        """
        for b in self.bundles:
            if b.locale == locale:
                return b
        return None

    def has_duplicate_keys(self) -> bool:
        """Kiểm tra xem có key trùng lặp trong collection không.

        Returns:
            True nếu có duplicate, False nếu không.
        """
        key_ids = [k.key for k in self.keys]
        return len(key_ids) != len(set(key_ids))

    def to_dict(self) -> dict[str, Any]:
        """Serialize keyset sang dict.

        Returns:
            Dict có "keys" và "bundles".
        """
        return {
            "keys": [self._key_to_dict(k) for k in self.keys],
            "bundles": [b.to_dict() for b in self.bundles],
        }

    @staticmethod
    def _key_to_dict(k: I18nKey) -> dict[str, Any]:
        """Chuyển I18nKey sang dict."""
        return {
            "key": k.key,
            "namespace": k.namespace,
            "entity_id": k.entity_id,
            "category": k.category,
            "path": k.path,
            "description": k.description,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> I18nKeyset:
        """Deserialize dict thành I18nKeyset.

        Args:
            data: Dict có "keys" (list of dicts).

        Returns:
            I18nKeyset với keys đã được thêm vào.
        """
        keyset = I18nKeyset()
        for kd in data.get("keys", []):
            keyset.add_key(I18nKey(**kd))
        return keyset
