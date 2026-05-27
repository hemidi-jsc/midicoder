# coding: utf-8
"""
Mô-đun models cho CP39 — i18n/L10n Runtime.

Định nghĩa các dataclass biểu diễn:
- LocaleConfig: Cấu hình locale (BCP 47 code, date/number/currency format)
- TranslationEntry: Bản ghi translation (key, namespace, locale, value, tenant)
- DiscoverResult: Kết quả auto-discover translatable strings
- CacheConfig: Cấu hình cache (backend, TTL, max_size)
- TranslationStore: Abstract interface cho storage backend
- LocaleFormatter: Engine format date/number/currency theo locale
- TranslationEngine: Engine resolve translation (cache → DB → fallback → key)

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP39).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class PluralRule(str, Enum):
    """Quy tắc số nhiều cho locale.

    - SINGULAR: Dạng số ít (English: 1 item)
    - PLURAL: Dạng số nhiều (English: 2 items, Vietnamese: luôn dạng này)
    """
    SINGULAR = "singular"
    PLURAL = "plural"


class CacheBackend(str, Enum):
    """Backend cho translation cache.

    - MEMORY: In-memory cache (dev/testing)
    - REDIS: Redis cache (production)
    """
    MEMORY = "memory"
    REDIS = "redis"


class DiscoverSource(str, Enum):
    """Nguồn cho auto-discover translatable strings.

    - TEMPLATE: Jinja2 template files
    - HTML: HTML files
    - TSX: React TSX/JSX files
    - CODE: Python/TypeScript source code
    """
    TEMPLATE = "template"
    HTML = "html"
    TSX = "tsx"
    CODE = "code"


# ===========================================================================
# LocaleConfig
# ===========================================================================


@dataclass
class LocaleConfig:
    """Cấu hình cho một locale.

    Lưu trữ thông tin định dạng theo ngôn ngữ/vùng miền, bao gồm
    BCP 47 code, tên hiển thị, và patterns cho date/number/currency.

    Attributes:
        code: Locale code theo BCP 47 (ví dụ: 'vi', 'en-US', 'fr-FR')
        name: Tên hiển thị (ví dụ: 'Tiếng Việt', 'English (US)')
        is_default: Có phải là locale mặc định không
        date_format: Pattern format ngày (ví dụ: 'dd/MM/yyyy')
        number_format: Pattern format số (ví dụ: '1.000.000')
        currency_code: Mã tiền tệ ISO 4217 (ví dụ: 'VND', 'USD')
        plural_rule: Quy tắc số nhiều
        fallback_locale: Locale fallback nếu không tìm thấy translation
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
    """
    code: str
    name: str = ""
    is_default: bool = False
    date_format: str = "dd/MM/yyyy"
    number_format: str = ""
    currency_code: str = ""
    plural_rule: PluralRule = PluralRule.PLURAL
    fallback_locale: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate locale config sau khi khởi tạo."""
        if not self.code or not self.code.strip():
            EM.raise_error(ErrorCode.CP39_EMPTY_LOCALE_CODE)

        # Kiểm tra locale code hợp lệ (BCP 47: lowercase, có thể có hyphen)
        if not re.match(r'^[a-z]{2,3}(-[A-Za-z]{2,4})?$', self.code):
            EM.raise_error(
                ErrorCode.CP39_INVALID_LOCALE_CODE,
                locale_code=self.code,
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def to_dict(self) -> dict[str, Any]:
        """Chuyển LocaleConfig sang dict."""
        return {
            "code": self.code,
            "name": self.name,
            "is_default": self.is_default,
            "date_format": self.date_format,
            "number_format": self.number_format,
            "currency_code": self.currency_code,
            "plural_rule": self.plural_rule.value,
            "fallback_locale": self.fallback_locale,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocaleConfig":
        """Tạo LocaleConfig từ dict."""
        return cls(
            code=data.get("code", ""),
            name=data.get("name", ""),
            is_default=data.get("is_default", False),
            date_format=data.get("date_format", "dd/MM/yyyy"),
            number_format=data.get("number_format", ""),
            currency_code=data.get("currency_code", ""),
            plural_rule=PluralRule(data.get("plural_rule", "plural")),
            fallback_locale=data.get("fallback_locale"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# TranslationEntry
# ===========================================================================


@dataclass
class TranslationEntry:
    """Bản ghi translation.

    Lưu trữ một bản dịch cụ thể cho một key trong một namespace và locale.
    Hỗ trợ tenant-scoped translations với fallback chain.

    Attributes:
        key: Translation key (snake_case, duy nhất trong namespace+locale)
        namespace: Nhóm translation (ví dụ: 'common', 'auth', 'product')
        locale: Locale code (BCP 47)
        value: Giá trị bản dịch
        tenant_id: Tenant ID (nullable — None = global translation)
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
    """
    key: str
    namespace: str = "common"
    locale: str = "en"
    value: str = ""
    tenant_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate translation entry sau khi khởi tạo."""
        if not self.key or not self.key.strip():
            EM.raise_error(ErrorCode.CP39_EMPTY_TRANSLATION_KEY)

        # Kiểm tra namespace hợp lệ (snake_case)
        if self.namespace and not re.match(r'^[a-z][a-z0-9_]*$', self.namespace):
            EM.raise_error(ErrorCode.CP39_INVALID_NAMESPACE, namespace=self.namespace)

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def to_dict(self) -> dict[str, Any]:
        """Chuyển TranslationEntry sang dict."""
        return {
            "key": self.key,
            "namespace": self.namespace,
            "locale": self.locale,
            "value": self.value,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TranslationEntry":
        """Tạo TranslationEntry từ dict."""
        return cls(
            key=data.get("key", ""),
            namespace=data.get("namespace", "common"),
            locale=data.get("locale", "en"),
            value=data.get("value", ""),
            tenant_id=data.get("tenant_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# DiscoverResult
# ===========================================================================


@dataclass
class DiscoverResult:
    """Kết quả của auto-discover scan.

    Biểu diễn một string được phát hiện từ codebase cần translation.

    Attributes:
        key: Translation key đề xuất (tự động generate từ string)
        namespace: Namespace đề xuất (tự động derive từ file path)
        source_file: Đường dẫn file nguồn
        line_number: Số dòng trong file
        original_string: String gốc được phát hiện
    """
    key: str
    namespace: str = "common"
    source_file: str = ""
    line_number: int = 0
    original_string: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DiscoverResult sang dict."""
        return {
            "key": self.key,
            "namespace": self.namespace,
            "source_file": self.source_file,
            "line_number": self.line_number,
            "original_string": self.original_string,
        }


# ===========================================================================
# CacheConfig
# ===========================================================================


@dataclass
class CacheConfig:
    """Cấu hình cache cho translation lookup.

    Hỗ trợ memory (dev) và Redis (production) backend.

    Attributes:
        backend: Loại backend (memory/redis)
        ttl_seconds: Thời gian sống của cache entry (giây)
        max_size: Số lượng tối đa entries trong cache
        redis_url: URL kết nối Redis (chỉ dùng khi backend=redis)
    """
    backend: CacheBackend = CacheBackend.MEMORY
    ttl_seconds: int = 300
    max_size: int = 10000
    redis_url: str = ""

    def __post_init__(self) -> None:
        """Validate cache config sau khi khởi tạo."""
        if self.ttl_seconds <= 0:
            EM.raise_error(
                ErrorCode.CP39_CACHE_CONFIG_INVALID,
                reason=f"ttl_seconds phải > 0, nhận được: {self.ttl_seconds}",
            )
        if self.max_size <= 0:
            EM.raise_error(
                ErrorCode.CP39_CACHE_CONFIG_INVALID,
                reason=f"max_size phải > 0, nhận được: {self.max_size}",
            )
        if self.backend == CacheBackend.REDIS and not self.redis_url:
            EM.raise_error(
                ErrorCode.CP39_CACHE_CONFIG_INVALID,
                reason="redis_url bắt buộc khi backend=redis",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển CacheConfig sang dict."""
        return {
            "backend": self.backend.value,
            "ttl_seconds": self.ttl_seconds,
            "max_size": self.max_size,
            "redis_url": self.redis_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheConfig":
        """Tạo CacheConfig từ dict."""
        return cls(
            backend=CacheBackend(data.get("backend", "memory")),
            ttl_seconds=data.get("ttl_seconds", 300),
            max_size=data.get("max_size", 10000),
            redis_url=data.get("redis_url", ""),
        )


# ===========================================================================
# TranslationStore (ABC)
# ===========================================================================


class TranslationStore(ABC):
    """Abstract interface cho storage backend.

    Định nghĩa contract để implement các storage backends khác nhau
    (SQLite, PostgreSQL, in-memory, v.v.).
    """

    @abstractmethod
    def get(self, key: str, locale: str, namespace: str = "common", tenant_id: str | None = None) -> str | None:
        """Lấy translation value cho key/locale.

        Args:
            key: Translation key
            locale: Locale code
            namespace: Translation namespace
            tenant_id: Tenant ID (optional)

        Returns:
            Translation value, hoặc None nếu không tìm thấy
        """
        ...

    @abstractmethod
    def set(self, entry: TranslationEntry) -> None:
        """Lưu/coverwrite translation entry.

        Args:
            entry: TranslationEntry để lưu
        """
        ...

    @abstractmethod
    def delete(self, key: str, locale: str, namespace: str = "common") -> bool:
        """Xóa translation entry.

        Args:
            key: Translation key
            locale: Locale code
            namespace: Translation namespace

        Returns:
            True nếu entry bị xóa, False nếu không tìm thấy
        """
        ...

    @abstractmethod
    def list_by_locale(self, locale: str, namespace: str = "common") -> list[TranslationEntry]:
        """Liệt kê tất cả translations cho một locale.

        Args:
            locale: Locale code
            namespace: Translation namespace (optional)

        Returns:
            Danh sách TranslationEntry
        """
        ...

    @abstractmethod
    def missing_keys(self, locale: str, all_keys: list[str], namespace: str = "common") -> list[str]:
        """Tìm các key chưa có translation cho locale.

        Args:
            locale: Locale code
            all_keys: Danh sách tất cả keys
            namespace: Translation namespace

        Returns:
            Danh sách keys chưa có translation
        """
        ...


# ===========================================================================
# InMemoryTranslationStore (Implement TranslationStore)
# ===========================================================================


@dataclass
class InMemoryTranslationStore:
    """In-memory implementation của TranslationStore.

    Dùng cho dev/testing. Lưu translations trong dict.
    """
    _store: dict[tuple[str, str, str, Optional[str]], str] = field(default_factory=dict)

    def get(self, key: str, locale: str, namespace: str = "common", tenant_id: str | None = None) -> str | None:
        """Lấy translation value."""
        return self._store.get((key, locale, namespace, tenant_id))

    def set(self, entry: TranslationEntry) -> None:
        """Lưu translation entry."""
        self._store[(entry.key, entry.locale, entry.namespace, entry.tenant_id)] = entry.value

    def delete(self, key: str, locale: str, namespace: str = "common") -> bool:
        """Xóa translation entry."""
        for tenant_key in [(key, locale, namespace, None), (key, locale, namespace, "")]:
            if tenant_key in self._store:
                del self._store[tenant_key]
                return True
        return False

    def list_by_locale(self, locale: str, namespace: str = "common") -> list[TranslationEntry]:
        """Liệt kê translations cho locale."""
        entries = []
        for (k, loc, ns, tid), val in self._store.items():
            if loc == locale and (namespace == "common" or ns == namespace):
                entries.append(TranslationEntry(key=k, namespace=ns, locale=loc, value=val, tenant_id=tid or None))
        return entries

    def missing_keys(self, locale: str, all_keys: list[str], namespace: str = "common") -> list[str]:
        """Tìm keys chưa có translation."""
        missing = []
        for k in all_keys:
            found = False
            for (key, loc, ns, tid) in self._store:
                if key == k and loc == locale and (namespace == "common" or ns == namespace):
                    found = True
                    break
            if not found:
                missing.append(k)
        return missing


# ===========================================================================
# LocaleFormatter
# ===========================================================================


class LocaleFormatter:
    """Engine format date/number/currency theo locale.

    Cung cấp các method để format giá trị theo cấu hình locale cụ thể.

    Attributes:
        locales: Dict locale code -> LocaleConfig
    """

    def __init__(self, locales: list[LocaleConfig] | None = None):
        self.locales: dict[str, LocaleConfig] = {}
        if locales:
            for loc in locales:
                self.locales[loc.code] = loc

    def add_locale(self, locale: LocaleConfig) -> None:
        """Thêm locale config vào formatter."""
        self.locales[locale.code] = locale

    def format_date(self, dt: datetime, locale_code: str) -> str:
        """Format datetime theo locale.

        Args:
            dt: Datetime cần format
            locale_code: Locale code

        Returns:
            Formatted date string

        Raises:
            MidicoderError: Nếu locale không tồn tại
        """
        locale = self.locales.get(locale_code)
        if not locale:
            EM.raise_error(ErrorCode.CP39_FORMATTER_INVALID_LOCALE, locale_code=locale_code)

        date_format = locale.date_format
        day = dt.day
        month = dt.month
        year = dt.year

        formatted = date_format
        formatted = formatted.replace("dd", f"{day:02d}")
        formatted = formatted.replace("d", str(day))
        formatted = formatted.replace("MM", f"{month:02d}")
        formatted = formatted.replace("M", str(month))
        formatted = formatted.replace("yyyy", str(year))
        formatted = formatted.replace("yy", str(year)[2:])

        return formatted

    def format_number(self, value: float, locale_code: str) -> str:
        """Format số theo locale.

        Args:
            value: Giá trị số cần format
            locale_code: Locale code

        Returns:
            Formatted number string

        Raises:
            MidicoderError: Nếu locale không tồn tại
        """
        locale = self.locales.get(locale_code)
        if not locale:
            EM.raise_error(ErrorCode.CP39_FORMATTER_INVALID_LOCALE, locale_code=locale_code)

        # Việt Nam: 1.000.000 (dot separator)
        if locale.code == "vi":
            return f"{value:,.0f}".replace(",", ".")

        # Mặc định: 1,000,000 (comma separator)
        return f"{value:,.0f}"

    def format_currency(self, value: float, locale_code: str) -> str:
        """Format tiền tệ theo locale.

        Args:
            value: Giá trị tiền tệ cần format
            locale_code: Locale code

        Returns:
            Formatted currency string

        Raises:
            MidicoderError: Nếu locale không tồn tại
        """
        locale = self.locales.get(locale_code)
        if not locale:
            EM.raise_error(ErrorCode.CP39_FORMATTER_INVALID_LOCALE, locale_code=locale_code)

        currency = locale.currency_code or ""

        if locale.code == "vi":
            formatted_number = f"{value:,.0f}".replace(",", ".")
            return f"{formatted_number}{currency}"

        # Mặc định: USD style
        formatted_number = f"{value:,.2f}"
        return f"{currency}{formatted_number}"

    def format_relative_time(self, dt: datetime, locale_code: str) -> str:
        """Format thời gian tương đối theo locale.

        Args:
            dt: Datetime cần so sánh với hiện tại
            locale_code: Locale code

        Returns:
            Relative time string (ví dụ: "2 phút trước", "just now")
        """
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        diff_seconds = int((now - dt).total_seconds())

        if diff_seconds < 60:
            return "vừa xong" if locale_code == "vi" else "just now"

        diff_minutes = diff_seconds // 60
        if diff_minutes < 60:
            return f"{diff_minutes} phút trước" if locale_code == "vi" else f"{diff_minutes} minutes ago"

        diff_hours = diff_minutes // 60
        if diff_hours < 24:
            return f"{diff_hours} giờ trước" if locale_code == "vi" else f"{diff_hours} hours ago"

        diff_days = diff_hours // 24
        return f"{diff_days} ngày trước" if locale_code == "vi" else f"{diff_days} days ago"

    def pluralize(self, count: int, locale_code: str) -> str:
        """Xác định dạng số ít hay số nhiều.

        Args:
            count: Số lượng
            locale_code: Locale code

        Returns:
            'singular' hoặc 'plural'
        """
        locale = self.locales.get(locale_code)
        if not locale:
            return "singular" if count == 1 else "plural"

        # Vietnamese: luôn plural (không phân biệt số ít/nhiều)
        if locale.code == "vi":
            return PluralRule.PLURAL.value

        # English và các ngôn ngữ khác: 1 = singular
        return PluralRule.SINGULAR.value if count == 1 else PluralRule.PLURAL.value


# ===========================================================================
# TranslationEngine
# ===========================================================================


class TranslationEngine:
    """Engine resolve translation với fallback chain.

    Resolution order:
    1. Cache (nếu có)
    2. Tenant-specific translation
    3. Global translation
    4. Fallback locale translation
    5. Raw key (last resort)

    Attributes:
        store: TranslationStore backend
        locales: Dict locale code -> LocaleConfig
        cache_config: Cache configuration
    """

    def __init__(
        self,
        store: TranslationStore | None = None,
        locales: list[LocaleConfig] | None = None,
        cache_config: CacheConfig | None = None,
    ):
        self.store: TranslationStore = store or InMemoryTranslationStore()
        self.locales: dict[str, LocaleConfig] = {}
        if locales:
            for loc in locales:
                self.locales[loc.code] = loc
        self.cache_config = cache_config or CacheConfig()
        # Simple in-memory cache
        self._cache: dict[tuple[str, str, str], str] = {}
        self._cache_ttl: dict[tuple[str, str, str], datetime] = {}

    def translate(self, key: str, locale: str = "en", namespace: str = "common", tenant_id: str | None = None) -> str:
        """Resolve translation với fallback chain.

        Args:
            key: Translation key
            locale: Target locale
            namespace: Translation namespace
            tenant_id: Optional tenant ID

        Returns:
            Translated string, hoặc raw key nếu không tìm thấy
        """
        cache_key = (key, locale, namespace)

        # 1. Kiểm tra cache
        if cache_key in self._cache:
            ttl_time = self._cache_ttl.get(cache_key)
            if ttl_time and ttl_time > datetime.now(timezone.utc):
                return self._cache[cache_key]

        # 2. Tenant-specific translation
        if tenant_id:
            value = self.store.get(key, locale, namespace, tenant_id)
            if value:
                self._put_cache(cache_key, value)
                return value

        # 3. Global translation
        value = self.store.get(key, locale, namespace, None)
        if value:
            self._put_cache(cache_key, value)
            return value

        # 4. Fallback locale
        fallback = self._get_fallback_locale(locale)
        while fallback:
            value = self.store.get(key, fallback, namespace, None)
            if value:
                self._put_cache(cache_key, value)
                return value
            fallback = self._get_fallback_locale(fallback)

        # 5. Raw key (last resort — không throw error)
        return key

    def add_translation(self, entry: TranslationEntry) -> None:
        """Thêm/coverwrite translation và invalidate cache.

        Args:
            entry: TranslationEntry để lưu
        """
        self.store.set(entry)
        self._invalidate_cache(entry.key, entry.locale, entry.namespace)

    def add_bulk(self, entries: list[TranslationEntry]) -> None:
        """Bulk thêm translations.

        Args:
            entries: Danh sách TranslationEntry
        """
        for entry in entries:
            self.add_translation(entry)

    def _put_cache(self, key: tuple[str, str, str], value: str) -> None:
        """Lưu vào cache với TTL."""
        self._cache[key] = value
        ttl = datetime.now(timezone.utc).replace(
            minute=datetime.now(timezone.utc).minute + self.cache_config.ttl_seconds // 60
        )
        self._cache_ttl[key] = ttl

    def _invalidate_cache(self, key: str, locale: str, namespace: str) -> None:
        """Invalidate cache entry."""
        cache_key = (key, locale, namespace)
        self._cache.pop(cache_key, None)
        self._cache_ttl.pop(cache_key, None)

    def _get_fallback_locale(self, locale: str) -> str | None:
        """Lấy fallback locale.

        Args:
            locale: Current locale

        Returns:
            Fallback locale code, hoặc None
        """
        locale_config = self.locales.get(locale)
        if locale_config and locale_config.fallback_locale:
            return locale_config.fallback_locale

        # Fallback mặc định: 'en'
        if locale != "en" and "en" in self.locales:
            return "en"

        return None
