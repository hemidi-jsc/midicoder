# coding: utf-8
"""
Cache Parser - Parse MIR metadata thanh CacheCollection.

Module nay chua CacheParser de parse cache config tu MIR metadata.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from midicoder.emitters.core.cache.models import (
    CacheProfile,
    CacheStrategy,
    CacheInvalidationRule,
    CacheBackend,
    InvalidationStrategy,
    CacheCollection,
)

# Mapping tu backend string sang CacheBackend enum
_BACKEND_MAP = {
    "redis": CacheBackend.REDIS,
    "memory": CacheBackend.MEMORY,
}

# Mapping tu strategy string sang InvalidationStrategy enum
_STRATEGY_MAP = {
    "pattern": InvalidationStrategy.PATTERN,
    "tag": InvalidationStrategy.TAG,
    "event": InvalidationStrategy.EVENT,
}


@dataclass
class CacheParser:
    """Parser de convert MIR metadata thanh CacheCollection."""

    def parse_from_metadata(self, metadata: dict[str, Any]) -> CacheCollection:
        """Parse cache config tu MIR metadata."""
        collection = CacheCollection()

        for profile_data in metadata.get("cache_profiles", []):
            try:
                collection.add_profile(self._parse_profile(profile_data))
            except Exception:
                continue

        for strategy_data in metadata.get("strategies", []):
            try:
                collection.add_strategy(self._parse_strategy(strategy_data))
            except Exception:
                continue

        for rule_data in metadata.get("invalidation_rules", []):
            try:
                collection.add_invalidation_rule(self._parse_rule(rule_data))
            except Exception:
                continue

        return collection

    def _parse_profile(self, data: dict[str, Any]) -> CacheProfile:
        """Parse mot cache profile."""
        backend = _BACKEND_MAP.get(data.get("backend", "redis"), CacheBackend.REDIS)
        return CacheProfile(
            id=data.get("id", ""),
            backend=backend,
            ttl=data.get("ttl", 300),
            max_size=data.get("max_size"),
            serializer=data.get("serializer", "json"),
            key_prefix=data.get("key_prefix", ""),
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )

    def _parse_strategy(self, data: dict[str, Any]) -> CacheStrategy:
        """Parse mot cache strategy."""
        return CacheStrategy(
            profile_id=data.get("profile_id", ""),
            strategy_type=data.get("strategy_type", "cache_aside"),
            load_from=data.get("load_from", ""),
            tenant_scoped=data.get("tenant_scoped", True),
            description=data.get("description", ""),
        )

    def _parse_rule(self, data: dict[str, Any]) -> CacheInvalidationRule:
        """Parse mot invalidation rule."""
        strategy = _STRATEGY_MAP.get(data.get("strategy", "pattern"), InvalidationStrategy.PATTERN)
        return CacheInvalidationRule(
            profile_id=data.get("profile_id", ""),
            pattern=data.get("pattern", ""),
            tags=data.get("tags", []),
            events=data.get("events", []),
            strategy=strategy,
            tenant_scoped=data.get("tenant_scoped", True),
            description=data.get("description", ""),
        )