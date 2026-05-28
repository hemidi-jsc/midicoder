# coding: utf-8
"""
Cache Parser - Parse MIR metadata thành CacheCollection.

Module này chứa CacheParser để parse cache config từ MIR metadata
và từ YAML string thành CacheCollection.

Author: Midicoder Team
Version: 1.1.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.packs.cp_backend_cache.models import (
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
    CDNCacheLayer,
    StampedePrevention,
    CacheTier,
    CacheWarmupConfig,
    StampedePreventionStrategy,
    CacheWarmupStrategy,
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
                      warm_configs, metrics, cdn_layers, stampede_prevention,
                      tiers, warmup_config

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

        # Parse CDN layers
        for cdn_data in metadata.get("cdn_layers", []):
            try:
                collection.add_cdn_layer(self._parse_cdn_layer(cdn_data))
            except Exception:
                continue

        # Parse stampede prevention
        if "stampede_prevention" in metadata:
            try:
                collection.set_stampede_prevention(
                    self._parse_stampede_prevention(metadata["stampede_prevention"])
                )
            except Exception:
                pass

        # Parse cache tiers
        for tier_data in metadata.get("tiers", []):
            try:
                collection.add_tier(self._parse_tier(tier_data))
            except Exception:
                continue

        # Parse warmup config
        if "warmup_config" in metadata:
            try:
                collection.set_warmup_config(
                    self._parse_warmup_config(metadata["warmup_config"])
                )
            except Exception:
                pass

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

    # ------------------------------------------------------------------
    # Advanced model parsers
    # ------------------------------------------------------------------

    def _parse_cdn_layer(self, data: dict[str, Any]) -> CDNCacheLayer:
        """Parse một CDN cache layer."""
        return CDNCacheLayer.from_dict(data)

    def _parse_stampede_prevention(self, data: dict[str, Any]) -> StampedePrevention:
        """Parse stampede prevention config."""
        strategy_str = data.get("strategy", "mutex")
        try:
            strategy = StampedePreventionStrategy(strategy_str)
        except ValueError:
            strategy = StampedePreventionStrategy.MUTEX
        return StampedePrevention(
            enabled=data.get("enabled", True),
            strategy=strategy,
            lock_ttl=data.get("lock_ttl", 10),
            lock_timeout=data.get("lock_timeout", 5),
            early_refresh_threshold=data.get("early_refresh_threshold", 0.8),
            probabilistic_threshold=data.get("probabilistic_threshold", 0.1),
            max_waiters=data.get("max_waiters", 100),
            description=data.get("description", ""),
        )

    def _parse_tier(self, data: dict[str, Any]) -> CacheTier:
        """Parse một cache tier."""
        return CacheTier.from_dict(data)

    def _parse_warmup_config(self, data: dict[str, Any]) -> CacheWarmupConfig:
        """Parse cache warmup config."""
        strategy_str = data.get("strategy", "on_startup")
        try:
            strategy = CacheWarmupStrategy(strategy_str)
        except ValueError:
            strategy = CacheWarmupStrategy.ON_STARTUP
        return CacheWarmupConfig(
            strategy=strategy,
            schedule_cron=data.get("schedule_cron", ""),
            warmup_keys=data.get("warmup_keys", []),
            warmup_query=data.get("warmup_query", ""),
            batch_size=data.get("batch_size", 100),
            max_keys=data.get("max_keys", 10000),
            parallelism=data.get("parallelism", 4),
            description=data.get("description", ""),
        )
