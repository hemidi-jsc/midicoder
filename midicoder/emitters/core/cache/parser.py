# coding: utf-8
"""
Cache Parser - Parse MIR metadata thành CacheCollection.

Module này chứa CacheParser để parse cache config từ MIR metadata
và từ YAML string thành CacheCollection.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.emitters.core.cache.models import (
    CacheProfile,
    CacheStrategy,
    CacheInvalidationRule,
    CacheWarmConfig,
    CacheMetrics,
    CacheBackend,
    InvalidationStrategy,
    CacheCollection,
    _BACKEND_MAP,
    _STRATEGY_MAP,
)


class CacheParser:
    """
    Parser để convert MIR metadata và YAML string thành CacheCollection.

    Support:
    - Parse từ MIR metadata (dict)
    - Parse từ YAML string
    - Validation và error throwing
    """

    def parse(self, raw: str) -> list[CacheProfile]:
        """
        Parse YAML string thành danh sách CacheProfile.

        Args:
            raw: YAML string chứa cache profiles

        Returns:
            Danh sách CacheProfile

        Raises:
            MidicoderError: Nếu YAML không hợp lệ
        """
        from midicoder.errors import MidicoderErrorManager as EM

        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            EM.raise_error("DSL_YAML_PARSE_ERROR", detail=str(e))

        if not isinstance(data, dict):
            EM.raise_error("DSL_YAML_PARSE_ERROR", detail="YAML phải là dict")

        collection = self.parse_from_metadata(data)
        return collection.profiles

    def parse_from_metadata(self, metadata: dict[str, Any]) -> CacheCollection:
        """
        Parse cache config từ MIR metadata.

        Args:
            metadata: Dict chứa cache_profiles, strategies, invalidation_rules,
                      warm_configs, metrics

        Returns:
            CacheCollection đầy đủ
        """
        collection = CacheCollection()

        # Parse profiles
        for profile_data in metadata.get("cache_profiles", []):
            try:
                collection.add_profile(self._parse_profile(profile_data))
            except Exception:
                continue

        # Parse strategies
        for strategy_data in metadata.get("strategies", []):
            try:
                collection.add_strategy(self._parse_strategy(strategy_data))
            except Exception:
                continue

        # Parse invalidation rules
        for rule_data in metadata.get("invalidation_rules", []):
            try:
                collection.add_invalidation_rule(self._parse_rule(rule_data))
            except Exception:
                continue

        # Parse warm configs
        for warm_data in metadata.get("warm_configs", []):
            try:
                collection.add_warm_config(self._parse_warm_config(warm_data))
            except Exception:
                continue

        # Parse metrics
        for metrics_data in metadata.get("metrics", []):
            try:
                collection.add_metrics(self._parse_metrics(metrics_data))
            except Exception:
                continue

        return collection

    def _parse_profile(self, data: dict[str, Any]) -> CacheProfile:
        """Parse một cache profile."""
        from midicoder.errors import MidicoderErrorManager as EM

        profile_id = data.get("id", "")
        if not profile_id:
            EM.raise_error("CP09_KEY_EMPTY", detail="Profile id không được để trống")

        backend_str = data.get("backend", "redis")
        backend = _BACKEND_MAP.get(backend_str)
        if backend is None:
            EM.raise_error(
                "CP09_BACKEND_INVALID",
                profile_id=profile_id,
                backend=backend_str,
            )

        return CacheProfile(
            id=profile_id,
            backend=backend,
            ttl=data.get("ttl", 300),
            max_size=data.get("max_size"),
            serializer=data.get("serializer", "json"),
            key_prefix=data.get("key_prefix", ""),
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )

    def _parse_strategy(self, data: dict[str, Any]) -> CacheStrategy:
        """Parse một cache strategy."""
        return CacheStrategy(
            profile_id=data.get("profile_id", ""),
            strategy_type=data.get("strategy_type", "cache_aside"),
            load_from=data.get("load_from", ""),
            tenant_scoped=data.get("tenant_scoped", True),
            description=data.get("description", ""),
        )

    def _parse_rule(self, data: dict[str, Any]) -> CacheInvalidationRule:
        """Parse một invalidation rule."""
        strategy_str = data.get("strategy", "pattern")
        strategy = _STRATEGY_MAP.get(strategy_str, InvalidationStrategy.PATTERN)
        return CacheInvalidationRule(
            profile_id=data.get("profile_id", ""),
            pattern=data.get("pattern", ""),
            tags=data.get("tags", []),
            events=data.get("events", []),
            strategy=strategy,
            tenant_scoped=data.get("tenant_scoped", True),
            description=data.get("description", ""),
        )

    def _parse_warm_config(self, data: dict[str, Any]) -> CacheWarmConfig:
        """Parse một warm config."""
        return CacheWarmConfig(
            profile_id=data.get("profile_id", ""),
            keys=data.get("keys", []),
            pattern=data.get("pattern", ""),
            schedule=data.get("schedule", ""),
            priority=data.get("priority", 5),
            tenant_scoped=data.get("tenant_scoped", True),
            description=data.get("description", ""),
        )

    def _parse_metrics(self, data: dict[str, Any]) -> CacheMetrics:
        """Parse một metrics."""
        return CacheMetrics(
            profile_id=data.get("profile_id", ""),
            hit_count=data.get("hit_count", 0),
            miss_count=data.get("miss_count", 0),
            eviction_count=data.get("eviction_count", 0),
            avg_latency_ms=data.get("avg_latency_ms", 0.0),
            peak_memory_mb=data.get("peak_memory_mb", 0.0),
            tenant_scoped=data.get("tenant_scoped", True),
        )
