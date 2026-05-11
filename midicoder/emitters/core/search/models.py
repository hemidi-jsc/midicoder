# coding: utf-8
"""
Mô-đun models cho Search & Indexing Emitter (CP10).

Định nghĩa các dataclass biểu diễn:
- SearchProviderType: Enum các search providers (Elasticsearch, MeiliSearch)
- SyncStrategy: Enum các strategies đồng bộ data (realtime, near_realtime, batch)
- SyncTrigger: Enum các triggers đồng bộ (event, polling)
- SearchIndexColumn: Column trong search index với type, searchable, filterable
- SearchIndex: Search index với provider, columns, sync config, tenant_isolated
- SearchCollection: Collection chứa tất cả search indices

KPI-029: Tenant Isolation — tenant_isolated=True mặc định cho mọi index.
ValidationError: Dùng MDC-CP10 error codes (MDC-CP10-001 ~ MDC-CP10-005).

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class SearchProviderType(str, Enum):
    """Enum các search providers hỗ trợ."""
    ELASTICSEARCH = "elasticsearch"
    MEILISEARCH = "meilisearch"


class SyncStrategy(str, Enum):
    """Enum các strategies đồng bộ data vào search index."""
    REALTIME = "realtime"
    NEAR_REALTIME = "near_realtime"
    BATCH = "batch"


class SyncTrigger(str, Enum):
    """Enum các triggers cho data synchronization."""
    EVENT = "event"
    POLLING = "polling"


# Danh sách các column types hợp lệ
_VALID_COLUMN_TYPES = {"text", "keyword", "numeric", "date", "geo"}


@dataclass
class SearchIndexColumn:
    """
    Column trong search index.

    Attributes:
        name: Tên column (không được để trống).
        column_type: Kiểu dữ liệu (text, keyword, numeric, date, geo).
        searchable: Có tham gia full-text search không.
        filterable: Có dùng để filter không.
        sortable: Có dùng để sort không.
        analyser: Analyzer cho text columns (vi, en, vn).
        description: Mô tả column.

    Raises:
        MidicoderError: Nếu name rỗng (MDC-CP10-001) hoặc
            column_type không hợp lệ (MDC-CP10-004).
    """
    name: str
    column_type: str = "text"
    searchable: bool = False
    filterable: bool = False
    sortable: bool = False
    analyser: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate các trường bắt buộc sau khi khởi tạo."""
        # Kiểm tra name không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP10_EMPTY_INDEX_NAME,
                name=self.name,
            )
        # Kiểm tra column_type hợp lệ
        if self.column_type not in _VALID_COLUMN_TYPES:
            EM.raise_error(
                ErrorCode.CP10_INVALID_COLUMN_TYPE,
                name=self.name,
                column_type=self.column_type,
                valid_types=list(_VALID_COLUMN_TYPES),
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển column sang dict format."""
        return {
            "name": self.name,
            "type": self.column_type,
            "searchable": self.searchable,
            "filterable": self.filterable,
            "sortable": self.sortable,
            "analyser": self.analyser,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchIndexColumn":
        """Tạo SearchIndexColumn từ dict."""
        return cls(
            name=data.get("name", ""),
            column_type=data.get("type", data.get("column_type", "text")),
            searchable=data.get("searchable", False),
            filterable=data.get("filterable", False),
            sortable=data.get("sortable", False),
            analyser=data.get("analyser", ""),
            description=data.get("description", ""),
        )


@dataclass
class SearchIndex:
    """
    Search index definition.

    Attributes:
        id: Định danh duy nhất của index (không được để trống).
        provider: Search provider (ELASTICSEARCH, MEILISEARCH).
        columns: Danh sách columns trong index.
        sync_strategy: Strategy đồng bộ data (mac dinh: near_realtime).
        sync_trigger: Trigger cho synchronization (mac dinh: event).
        tenant_isolated: Co enforce tenant isolation khong (KPI-029, mac dinh: True).
        description: Mô tả index.

    Raises:
        MidicoderError: Nếu id rỗng (MDC-CP10-001).
    """
    id: str
    provider: SearchProviderType = SearchProviderType.ELASTICSEARCH
    columns: list[SearchIndexColumn] = field(default_factory=list)
    sync_strategy: SyncStrategy = SyncStrategy.NEAR_REALTIME
    sync_trigger: SyncTrigger = SyncTrigger.EVENT
    tenant_isolated: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        """Validate các trường bắt buộc sau khi khởi tạo."""
        # Kiểm tra id không được để trống
        if not self.id or not self.id.strip():
            EM.raise_error(
                ErrorCode.CP10_EMPTY_INDEX_NAME,
                index_id=self.id,
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển index sang dict format."""
        return {
            "id": self.id,
            "provider": self.provider.value,
            "columns": [c.to_dict() for c in self.columns],
            "sync_strategy": self.sync_strategy.value,
            "sync_trigger": self.sync_trigger.value,
            "tenant_isolated": self.tenant_isolated,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchIndex":
        """Tạo SearchIndex từ dict."""
        return cls(
            id=data.get("id", ""),
            provider=SearchProviderType(data.get("provider", "elasticsearch")),
            columns=[SearchIndexColumn.from_dict(c) for c in data.get("columns", [])],
            sync_strategy=SyncStrategy(data.get("sync_strategy", "near_realtime")),
            sync_trigger=SyncTrigger(data.get("sync_trigger", "event")),
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )


@dataclass
class SearchCollection:
    """
    Collection chứa tất cả search indices.

    Attributes:
        indices: Danh sách search indices.
    """
    indices: list[SearchIndex] = field(default_factory=list)

    def add_index(self, index: SearchIndex) -> None:
        """Thêm index vào collection."""
        self.indices.append(index)

    @property
    def total_count(self) -> int:
        """Tổng số indices trong collection."""
        return len(self.indices)

    def get_by_id(self, index_id: str) -> Optional[SearchIndex]:
        """Tìm index theo ID."""
        for index in self.indices:
            if index.id == index_id:
                return index
        return None

    def tenant_isolated_indices(self) -> list[SearchIndex]:
        """Lọc các indices có tenant isolation (KPI-029)."""
        return [i for i in self.indices if i.tenant_isolated]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "indices": [i.to_dict() for i in self.indices],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchCollection":
        """Tạo SearchCollection từ dict."""
        result = cls()
        result.indices = [SearchIndex.from_dict(i) for i in data.get("indices", [])]
        return result
