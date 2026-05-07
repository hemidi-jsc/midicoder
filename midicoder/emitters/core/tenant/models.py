# coding: utf-8
"""
Mô-đun models cho CP02 Multi-Tenant Architecture Generator.

Định nghĩa các dataclass biểu diễn:
- TenantMode: Enum các chiều cách tenant isolation (schema/row/subdomain)
- TenantConfig: Cấu hình tenant cho ứng dụng
- TenantContext: Context tenant trong request
- TenantResolver: Giải thích tenant ID từ các nguồn khác nhau

KPI-029: Tenant Isolation - bắt buộc cho tất cả operations.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# TenantMode Enum
# ===========================================================================


class TenantMode(str, Enum):
    """
    Enum các cách tenant isolation.

    - SCHEMA: Mỗi tenant có PostgreSQL schema riêng
    - ROW: Tất cả tenant chia cùng bảng, phân biệt bằng tenant_id column
    - SUBDOMAIN: Mỗi tenant có subdomain riêng (tenant1.app.com)
    """
    SCHEMA = "schema"
    ROW = "row"
    SUBDOMAIN = "subdomain"


# ===========================================================================
# TenantConfig
# ===========================================================================


@dataclass
class TenantConfig:
    """
    Cấu hình tenant cho ứng dụng.

    Attributes:
        mode: Cách tenant isolation (SCHEMA, ROW, SUBDOMAIN)
        tenant_id_column: Tên column chứa tenant ID (cho ROW mode)
        default_tenant_id: Tenant ID mặc định cho requests không có tenant
        schema_prefix: Prefix cho schema names (cho SCHEMA mode)
        domain: Domain cuối cùng (cho SUBDOMAIN mode)
        cache_ttl: Thời gian cache tenant resolution (giây)
    """
    mode: TenantMode
    tenant_id_column: str = "tenant_id"
    default_tenant_id: str = "default"
    schema_prefix: str = "tenant_"
    domain: str = ""
    cache_ttl: int = 300

    def __post_init__(self) -> None:
        """Validate tenant config sau khi khoi tao."""
        # Kiểm tra tenant_id_column không được để trống cho ROW mode
        if self.mode == TenantMode.ROW and not self.tenant_id_column.strip():
            EM.raise_error(
                ErrorCode.CP02_TENANT_FILTER_MISSING,
                mode=self.mode.value,
                message="tenant_id_column không được để trống cho ROW mode"
            )
        # Kiểm tra domain không được để trống cho SUBDOMAIN mode
        if self.mode == TenantMode.SUBDOMAIN and not self.domain.strip():
            EM.raise_error(
                ErrorCode.CP02_TENANT_MODE_INVALID,
                mode=self.mode.value,
                message="domain không được để trống cho SUBDOMAIN mode"
            )
        # Cache ttl phải >= 0
        if self.cache_ttl < 0:
            self.cache_ttl = 0

    def to_dict(self) -> dict[str, Any]:
        """Chuyển tenant config sang dict format."""
        return {
            "mode": self.mode.value,
            "tenant_id_column": self.tenant_id_column,
            "default_tenant_id": self.default_tenant_id,
            "schema_prefix": self.schema_prefix,
            "domain": self.domain,
            "cache_ttl": self.cache_ttl,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TenantConfig":
        """Tạo TenantConfig từ dict."""
        return cls(
            mode=TenantMode(data.get("mode", "row")),
            tenant_id_column=data.get("tenant_id_column", "tenant_id"),
            default_tenant_id=data.get("default_tenant_id", "default"),
            schema_prefix=data.get("schema_prefix", "tenant_"),
            domain=data.get("domain", ""),
            cache_ttl=data.get("cache_ttl", 300),
        )


# ===========================================================================
# TenantContext
# ===========================================================================


@dataclass
class TenantContext:
    """
    Context tenant trong request.

    Lưu trữ thông tin tenant hiện tại trong request context.
    Được sử dụng để enforce tenant isolation cho tất cả operations.

    Attributes:
        tenant_id: Tenant ID hiện tại
        user_id: User ID hiện tại (optional)
        mode: Cách tenant isolation
        headers: Request headers (optional, cho debugging)
    """
    tenant_id: str | None
    user_id: str | None = None
    mode: TenantMode = TenantMode.ROW
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate tenant context sau khi khoi tao."""
        # Tenant ID không được để trống hoặc None
        if not self.tenant_id:
            EM.raise_error(
                ErrorCode.CP02_TENANT_ID_MISSING,
                user_id=self.user_id,
                mode=self.mode.value,
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển tenant context sang dict format."""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "mode": self.mode.value,
            "headers": self.headers,
        }


# ===========================================================================
# TenantResolver
# ===========================================================================


@dataclass
class TenantResolver:
    """
    Giải thích tenant ID từ các nguồn khác nhau.

    Thực hiện logic để xác định tenant ID từ:
    1. Request header (X-Tenant-ID)
    2. JWT claims (tenant_id claim)
    3. Subdomain (tenant.app.com)
    4. Default tenant id

    Thứ tự ưu tiên: Header > JWT > Subdomain > Default

    Attributes:
        domain: Domain cuối cùng để extract subdomain (cho SUBDOMAIN mode)
        default_tenant_id: Tenant ID mặc định nếu không tìm thấy
        _cache: Cache đã resolve tenant IDs
    """
    domain: str = ""
    default_tenant_id: str = "default"
    _cache: dict[str, str] = field(default_factory=dict, repr=False)

    def resolve(
        self,
        headers: dict[str, str] | None = None,
        jwt_claims: dict[str, Any] | None = None,
        host: str = "",
    ) -> str:
        """
        Resolve tenant ID từ các nguồn khác nhau.

        Thứ tự ưu tiên:
        1. Request header (X-Tenant-ID)
        2. JWT claims (tenant_id)
        3. Subdomain (nếu có domain)
        4. Default tenant ID

        Args:
            headers: Request headers
            jwt_claims: JWT claims
            host: Host header (cho subdomain resolution)

        Returns:
            Tenant ID đã resolve

        Raises:
            MidicoderError: Nếu không thể resolve tenant ID (MDC-CP02-002)
        """
        headers = headers or {}
        jwt_claims = jwt_claims or {}

        # 1. Kiểm tra cache trước
        cache_key = f"{headers.get('X-Tenant-ID', '')}:{host}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        tenant_id: str = ""

        # 2. Resolve từ header (ưu tiên nhất)
        if not tenant_id:
            tenant_id = headers.get("X-Tenant-ID", "")

        # 3. Resolve từ JWT claims
        if not tenant_id:
            tenant_id = jwt_claims.get("tenant_id", "")

        # 4. Resolve từ subdomain
        if not tenant_id and self.domain and host:
            tenant_id = self._extract_subdomain(host)

        # 5. Nếu vẫn không có, throw error
        if not tenant_id:
            EM.raise_error(
                ErrorCode.CP02_TENANT_ID_MISSING,
                headers_provided=bool(headers),
                jwt_provided=bool(jwt_claims),
                host=host,
            )

        # Cache kết quả
        self._cache[cache_key] = tenant_id
        return tenant_id

    def _extract_subdomain(self, host: str) -> str:
        """
        Extract subdomain từ host.

        Ví dụ:
            - "tenant1.app.example.com" với domain="app.example.com" -> "tenant1"
            - "app.example.com" với domain="app.example.com" -> ""

        Args:
            host: Host header

        Returns:
            Subdomain hoặc string rỗng nếu không tìm thấy
        """
        if not self.domain or not host:
            return ""

        # Loại bỏ port nếu có
        host_clean = host.split(":")[0]
        domain_clean = self.domain.split(":")[0]

        # Kiểm tra host có kết thúc bằng domain không
        if host_clean.endswith("." + domain_clean):
            subdomain = host_clean[:-(len(domain_clean) + 1)]
            return subdomain

        return ""

    def clear_cache(self) -> None:
        """Xóa cache tenant resolutions."""
        self._cache.clear()