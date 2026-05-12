# coding: utf-8
"""
Search Parser - Parse MIR metadata thành SearchCollection.

Module này cung cấp SearchParser để convert MIR metadata (từ Pipeline layer 2)
thành SearchCollection (CP10 models). Parser hỗ trợ:
- Parse search_indices từ MIR metadata
- Parse providers (Elasticsearch, MeiliSearch)
- Parse sync strategies (realtime, near_realtime, batch)
- Parse sync triggers (event, polling)
- Parse columns với types, searchable, filterable, sortable
- KPI-029: Tenant isolation (mặc định True)

Error handling: Bỏ qua các entries không hợp lệ, tiếp tục parse các entries khác.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from midicoder.emitters.core.cp10_search.models import (
    SearchCollection,
    SearchIndex,
    SearchIndexColumn,
    SearchProviderType,
    SyncStrategy,
    SyncTrigger,
)

# Mapping provider string -> enum
_PROVIDER_MAP = {
    "elasticsearch": SearchProviderType.ELASTICSEARCH,
    "meilisearch": SearchProviderType.MEILISEARCH,
}

# Mapping sync strategy string -> enum
_STRATEGY_MAP = {
    "realtime": SyncStrategy.REALTIME,
    "near_realtime": SyncStrategy.NEAR_REALTIME,
    "batch": SyncStrategy.BATCH,
}

# Mapping sync trigger string -> enum
_TRIGGER_MAP = {
    "event": SyncTrigger.EVENT,
    "polling": SyncTrigger.POLLING,
}


@dataclass
class SearchParser:
    """
    Parser để convert MIR metadata thành SearchCollection.

    Parse search indices declarations từ MIR metadata và chuyển thành
    các SearchIndex objects. Hỗ trợ fallback cho các giá trị mặc định
    khi fields thiếu.
    """

    def parse_from_metadata(self, metadata: Optional[dict[str, Any]]) -> SearchCollection:
        """
        Parse search indices từ MIR metadata.

        Args:
            metadata: MIR metadata dictionary với key 'search_indices'.

        Returns:
            SearchCollection chứa các search indices đã parse.

        Raises:
            MidicoderError: Nếu metadata không hợp lệ (không raise, return empty collection).
        """
        collection = SearchCollection()

        # Handle None metadata
        if not metadata or not isinstance(metadata, dict):
            return collection

        # Lấy danh sách search indices từ metadata
        indices_data = metadata.get("search_indices", [])
        if not indices_data or not isinstance(indices_data, list):
            return collection

        # Parse từng index, bỏ qua các entries không hợp lệ
        for index_data in indices_data:
            try:
                if not isinstance(index_data, dict):
                    continue
                collection.add_index(self._parse_index(index_data))
            except Exception:
                # Bỏ qua entries không parse được, tiếp tục với entries khác
                continue

        return collection

    def _parse_index(self, data: dict[str, Any]) -> SearchIndex:
        """
        Parse một search index từ dictionary.

        Args:
            data: Dictionary chứa thông tin search index.

        Returns:
            SearchIndex instance đã parse.

        Raises:
            MidicoderError: Nếu index id rỗng (MDC-CP10-001).
        """
        # Parse provider — fallback default elasticsearch
        provider_str = data.get("provider", "elasticsearch")
        provider = _PROVIDER_MAP.get(provider_str, SearchProviderType.ELASTICSEARCH)

        # Parse sync strategy — fallback default near_realtime
        strategy_str = data.get("sync_strategy", "near_realtime")
        sync_strategy = _STRATEGY_MAP.get(strategy_str, SyncStrategy.NEAR_REALTIME)

        # Parse sync trigger — fallback default event
        trigger_str = data.get("sync_trigger", "event")
        sync_trigger = _TRIGGER_MAP.get(trigger_str, SyncTrigger.EVENT)

        # Parse columns
        columns = []
        columns_data = data.get("columns", [])
        if isinstance(columns_data, list):
            for col_data in columns_data:
                if isinstance(col_data, dict):
                    columns.append(SearchIndexColumn(
                        name=col_data.get("name", ""),
                        column_type=col_data.get("type", col_data.get("column_type", "text")),
                        searchable=col_data.get("searchable", False),
                        filterable=col_data.get("filterable", False),
                        sortable=col_data.get("sortable", False),
                        analyser=col_data.get("analyser", ""),
                        description=col_data.get("description", ""),
                    ))

        # Tạo SearchIndex — validation __post_init__ sẽ check id rỗng
        return SearchIndex(
            id=data.get("id", ""),
            provider=provider,
            columns=columns,
            sync_strategy=sync_strategy,
            sync_trigger=sync_trigger,
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )
