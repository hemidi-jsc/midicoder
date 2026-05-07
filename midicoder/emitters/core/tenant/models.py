# coding: utf-8
"""
Mô-đun models cho CP02 Multi-Tenant Architecture Generator.

Dinh nghia cac dataclass bieu dien:
- TenantMode: Enum cac chieu cway tenant isolation (schema/row/subdomain)
- TenantConfig: Cau hinh tenant cho ung dung
- TenantContext: Context tenant trong request
- TenantResolver: Giai thich tenant ID tu cac nguon khac nhau

KPI-029: Tenant Isolation - bat buoc cho tat ca operations.

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
    Enum cac chieu cway tenant isolation.

    - SCHEMA: Moi tenant co PostgreSQL schema rieng
    - ROW: Tat ca tenant chia will bang, phan biet bang tenant_id column
    - SUBDOMAIN: Moi tenant co subdomain rieng (tenant1.app.com)
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
    Cau hinh tenant cho ung dung.

    Attributes:
        mode: Chieu cway tenant isolation (SCHEMA, ROW, SUBDOMAIN)
        tenant_id_column: Ten column chua tenant ID (cho ROW mode)
        default_tenant_id: Tenant ID mac dinh cho requests khong co tenant
        schema_prefix: Prefix cho schema names (cho SCHEMA mode)
        domain: Domain cuoi cung (cho SUBDOMAIN mode)
        cache_ttl: Thoi gian cache tenant resolution (giay)
    """
    mode: TenantMode
    tenant_id_column: str = "tenant_id"
    default_tenant_id: str = "default"
    schema_prefix: str = "tenant_"
    domain: str = ""
    cache_ttl: int = 300

    def __post_init__(self) -> None:
        """Validate tenant config sau khi khoi tao."""
        # Kiem tra tenant_id_column khong duoc de trong cho ROW mode
        if self.mode == TenantMode.ROW and not self.tenant_id_column.strip():
            EM.raise_error(
                ErrorCode.CP02_TENANT_FILTER_MISSING,
                mode=self.mode.value,
                message="tenant_id_column khong duoc de trong cho ROW mode"
            )
        # Kiem tra domain khong duoc de trong cho SUBDOMAIN mode
        if self.mode == TenantMode.SUBDOMAIN and not self.domain.strip():
            EM.raise_error(
                ErrorCode.CP02_TENANT_MODE_INVALID,
                mode=self.mode.value,
                message="domain khong duoc de trong cho SUBDOMAIN mode"
            )
        # Cache ttl phai >= 0
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
        """Tao TenantConfig tu dict."""
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

    Luu tru thong tin tenant hien tai trong request context.
    Duoc su dung de enforce tenant isolation cho tat ca operations.

    Attributes:
        tenant_id: Tenant ID hien tai
        user_id: User ID hien tai (optional)
        mode: Chieu cway tenant isolation
        headers: Request headers (optional, cho debugging)
    """
    tenant_id: str | None
    user_id: str | None = None
    mode: TenantMode = TenantMode.ROW
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate tenant context sau khi khoi tao."""
        # Tenant ID khong duoc de trong hoac None
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
    Giai thich tenant ID tu cac nguon khac nhau.

    Thuc hien logic de xac dinh tenant ID tu:
    1. Request header (X-Tenant-ID)
    2. JWT claims (tenant_id claim)
    3. Subdomain (tenant.app.com)
    4. Default tenant id

    Thu tu uu tien: Header > JWT > Subdomain > Default

    Attributes:
        domain: Domain cuoi cung de extract subdomain (cho SUBDOMAIN mode)
        default_tenant_id: Tenant ID mac dinh neu khong tim thay
        _cache: Cache da resolve tenant IDs
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
        Resolve tenant ID tu cac nguon khac nhau.

        Thu tu uu tien:
        1. Request header (X-Tenant-ID)
        2. JWT claims (tenant_id)
        3. Subdomain (neu co domain)
        4. Default tenant ID

        Args:
            headers: Request headers
            jwt_claims: JWT claims
            host: Host header (cho subdomain resolution)

        Returns:
            Tenant ID da resolve

        Raises:
            MidicoderError: Neu khong the resolve tenant ID (MDC-CP02-002)
        """
        headers = headers or {}
        jwt_claims = jwt_claims or {}

        # 1. Kiem tra cache truoc
        cache_key = f"{headers.get('X-Tenant-ID', '')}:{host}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        tenant_id: str = ""

        # 2. Resolve tu header (uu tien nhat)
        if not tenant_id:
            tenant_id = headers.get("X-Tenant-ID", "")

        # 3. Resolve tu JWT claims
        if not tenant_id:
            tenant_id = jwt_claims.get("tenant_id", "")

        # 4. Resolve tu subdomain
        if not tenant_id and self.domain and host:
            tenant_id = self._extract_subdomain(host)

        # 5. Neu van khong co, throw error
        if not tenant_id:
            EM.raise_error(
                ErrorCode.CP02_TENANT_ID_MISSING,
                headers_provided=bool(headers),
                jwt_provided=bool(jwt_claims),
                host=host,
            )

        # Cache ket qua
        self._cache[cache_key] = tenant_id
        return tenant_id

    def _extract_subdomain(self, host: str) -> str:
        """
        Extract subdomain tu host.

        Vi du:
            - "tenant1.app.example.com" voi domain="app.example.com" -> "tenant1"
            - "app.example.com" voi domain="app.example.com" -> ""

        Args:
            host: Host header

        Returns:
            Subdomain hoac string rong neu khong tim thay
        """
        if not self.domain or not host:
            return ""

        # Loai bo port neu co
        host_clean = host.split(":")[0]
        domain_clean = self.domain.split(":")[0]

        # Kiem tra host co ket thoi bang domain khong
        if host_clean.endswith("." + domain_clean):
            subdomain = host_clean[:-(len(domain_clean) + 1)]
            return subdomain

        return ""

    def clear_cache(self) -> None:
        """Xoa cache tenant resolutions."""
        self._cache.clear()