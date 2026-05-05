# coding: utf-8
"""
Mô-đun models cho Search Emitter (CP10).

Định nghĩa các dataclass biểu diễn:
- SearchProviderType: Enum các search providers (Elasticsearch, MeiliSearch)
- SyncStrategy: Enum các strategies đồng bộ data (realtime, near_realtime, batch)
- SyncTrigger: Enum các triggers đồng bộ (event, polling)
- SearchIndexColumn: Column trong search index với type, searchable, filterable
- SearchIndex: Search index với provider, columns, sync config, tenant_isolated
- SearchCollection: Collection chứa tất cả search indices

KPI-029: Tenant Isolation - tenant_isolated=True mặc định

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class SearchProviderType(str, Enum):
    """Enum các search providers."""
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


@dataclass
class SearchIndexColumn:
    """
    Column trong search index.

    Attributes:
        name: Tên column
        column_type: Kiểu dữ liệu (text, keyword, numeric, date, geo)
        searchable: Có tham gia full-text search không
        filterable: Có dùng để filter không
        sortable: Có dùng để sort không
        analyser: Analyzer cho text columns (vi, en, vn)
        description: Mô tả column
    """
    name: str
    column_type: str = "text"
    searchable: bool = False
    filterable: bool = False
    sortable: bool = False
    analyser: str = ""
    description: str = ""

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
        id: Định danh duy nhất của index
        provider: Search provider (ELASTICSEARCH, MEILISEARCH)
        columns: Danh sách columns trong index
        sync_strategy: Strategy đồng bộ data
        sync_trigger: Trigger cho synchronization
        tenant_isolated: Có enforce tenant isolation không (KPI-029)
        description: Mô tả index
    """
    id: str
    provider: SearchProviderType = SearchProviderType.ELASTICSEARCH
    columns: list[SearchIndexColumn] = field(default_factory=list)
    sync_strategy: SyncStrategy = SyncStrategy.NEAR_REALTIME
    sync_trigger: SyncTrigger = SyncTrigger.EVENT
    tenant_isolated: bool = True
    description: str = ""

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
        indices: Danh sách search indices
    """
    indices: list[SearchIndex] = field(default_factory=list)

    def add_index(self, index: SearchIndex) -> None:
        """Them index vao collection."""
        self.indices.append(index)

    @property
    def total_count(self) -> int:
        """Tong so indices trong collection."""
        return len(self.indices)

    def get_by_id(self, index_id: str) -> Optional[SearchIndex]:
        """Tim index theo ID."""
        for index in self.indices:
            if index.id == index_id:
                return index
        return None

    def tenant_isolated_indices(self) -> list[SearchIndex]:
        """Loc cac indices co tenant isolation (KPI-029)."""
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