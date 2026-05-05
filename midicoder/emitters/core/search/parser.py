# coding: utf-8
"""
Search Parser - Parse MIR metadata thanh SearchCollection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from midicoder.emitters.core.search.models import (
    SearchIndex,
    SearchIndexColumn,
    SearchProviderType,
    SyncStrategy,
    SyncTrigger,
    SearchCollection,
)

_PROVIDER_MAP = {
    "elasticsearch": SearchProviderType.ELASTICSEARCH,
    "meilisearch": SearchProviderType.MEILISEARCH,
}

_STRATEGY_MAP = {
    "realtime": SyncStrategy.REALTIME,
    "near_realtime": SyncStrategy.NEAR_REALTIME,
    "batch": SyncStrategy.BATCH,
}

_TRIGGER_MAP = {
    "event": SyncTrigger.EVENT,
    "polling": SyncTrigger.POLLING,
}


@dataclass
class SearchParser:
    """Parser de convert MIR metadata thanh SearchCollection."""

    def parse_from_metadata(self, metadata: dict[str, Any]) -> SearchCollection:
        """Parse search indices tu MIR metadata."""
        collection = SearchCollection()
        for index_data in metadata.get("search_indices", []):
            try:
                collection.add_index(self._parse_index(index_data))
            except Exception:
                continue
        return collection

    def _parse_index(self, data: dict[str, Any]) -> SearchIndex:
        """Parse mot search index."""
        provider = _PROVIDER_MAP.get(data.get("provider", "elasticsearch"), SearchProviderType.ELASTICSEARCH)
        sync_strategy = _STRATEGY_MAP.get(data.get("sync_strategy", "near_realtime"), SyncStrategy.NEAR_REALTIME)
        sync_trigger = _TRIGGER_MAP.get(data.get("sync_trigger", "event"), SyncTrigger.EVENT)
        columns = []
        for col_data in data.get("columns", []):
            columns.append(SearchIndexColumn(
                name=col_data.get("name", ""),
                column_type=col_data.get("type", "text"),
                searchable=col_data.get("searchable", False),
                filterable=col_data.get("filterable", False),
                sortable=col_data.get("sortable", False),
                analyser=col_data.get("analyser", ""),
                description=col_data.get("description", ""),
            ))
        return SearchIndex(
            id=data.get("id", ""),
            provider=provider,
            columns=columns,
            sync_strategy=sync_strategy,
            sync_trigger=sync_trigger,
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )