# coding: utf-8
"""
Mô-đun parser cho CP63 — Search & Recommendation Engine.

Parse DSL dict (từ contract YAML) sang RecommendationIR — Intermediate Representation
cho recommendation configurations, item embeddings, user preferences,
cache settings, và A/B test configs.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp63_recommendation.models import (
    ABTestConfig,
    ItemEmbedding,
    RecommendationAlgorithm,
    RecommendationCache,
    RecommendationConfig,
    SimilarityMetric,
    UserPreference,
)


@dataclass
class RecommendationIR:
    """Intermediate Representation cho CP63.

    Gom tập tất cả cấu hình recommendation engine từ DSL, bao gồm
    recommendation configs, item embeddings, user preferences,
    cache settings, và A/B test configurations.

    Attributes:
        configs: Danh sách recommendation configurations
        embeddings: Danh sách item embedding configs
        preferences: Danh sách user preference configs
        caches: Danh sách recommendation cache entries
        ab_tests: Danh sách A/B test configurations
        default_algorithm: Thuật toán mặc định
        default_top_k: Số lượng items mặc định
        enable_cache: Có bật cache toàn cục không
        enable_ab_testing: Có bật A/B testing không
    """
    configs: list[RecommendationConfig] = field(default_factory=list)
    embeddings: list[ItemEmbedding] = field(default_factory=list)
    preferences: list[UserPreference] = field(default_factory=list)
    caches: list[RecommendationCache] = field(default_factory=list)
    ab_tests: list[ABTestConfig] = field(default_factory=list)
    default_algorithm: RecommendationAlgorithm = RecommendationAlgorithm.HYBRID
    default_top_k: int = 10
    enable_cache: bool = True
    enable_ab_testing: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecommendationIR sang dict."""
        return {
            "configs": [c.to_dict() for c in self.configs],
            "embeddings": [e.to_dict() for e in self.embeddings],
            "preferences": [p.to_dict() for p in self.preferences],
            "caches": [c.to_dict() for c in self.caches],
            "ab_tests": [a.to_dict() for a in self.ab_tests],
            "default_algorithm": self.default_algorithm.value,
            "default_top_k": self.default_top_k,
            "enable_cache": self.enable_cache,
            "enable_ab_testing": self.enable_ab_testing,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecommendationIR":
        """Tạo RecommendationIR từ dict."""
        configs = [RecommendationConfig.from_dict(c) for c in data.get("configs", [])]
        embeddings = [ItemEmbedding.from_dict(e) for e in data.get("embeddings", [])]
        preferences = [UserPreference.from_dict(p) for p in data.get("preferences", [])]
        caches = [RecommendationCache.from_dict(c) for c in data.get("caches", [])]
        ab_tests = [ABTestConfig.from_dict(a) for a in data.get("ab_tests", [])]
        return cls(
            configs=configs,
            embeddings=embeddings,
            preferences=preferences,
            caches=caches,
            ab_tests=ab_tests,
            default_algorithm=RecommendationAlgorithm(data.get("default_algorithm", "hybrid")),
            default_top_k=data.get("default_top_k", 10),
            enable_cache=data.get("enable_cache", True),
            enable_ab_testing=data.get("enable_ab_testing", False),
        )


def parse_configs(data: dict[str, Any]) -> list[RecommendationConfig]:
    """Parse danh sách recommendation configs từ DSL dict.

    Args:
        data: DSL dict với key 'configs' hoặc 'recommendation_configs'

    Returns:
        Danh sách RecommendationConfig
    """
    raw = data.get("configs", data.get("recommendation_configs", []))
    return [RecommendationConfig.from_dict(c) for c in raw]


def parse_embeddings(data: dict[str, Any]) -> list[ItemEmbedding]:
    """Parse danh sách item embeddings từ DSL dict.

    Args:
        data: DSL dict với key 'embeddings' hoặc 'item_embeddings'

    Returns:
        Danh sách ItemEmbedding
    """
    raw = data.get("embeddings", data.get("item_embeddings", []))
    return [ItemEmbedding.from_dict(e) for e in raw]


def parse_preferences(data: dict[str, Any]) -> list[UserPreference]:
    """Parse danh sách user preferences từ DSL dict.

    Args:
        data: DSL dict với key 'preferences' hoặc 'user_preferences'

    Returns:
        Danh sách UserPreference
    """
    raw = data.get("preferences", data.get("user_preferences", []))
    return [UserPreference.from_dict(p) for p in raw]


def parse_ab_tests(data: dict[str, Any]) -> list[ABTestConfig]:
    """Parse danh sách A/B test configs từ DSL dict.

    Args:
        data: DSL dict với key 'ab_tests' hoặc 'experiments'

    Returns:
        Danh sách ABTestConfig
    """
    raw = data.get("ab_tests", data.get("experiments", []))
    return [ABTestConfig.from_dict(a) for a in raw]


def parse_to_ir(data: dict[str, Any]) -> RecommendationIR:
    """Parse DSL dict thành RecommendationIR.

    Args:
        data: DSL dict với configs, embeddings, preferences, ab_tests

    Returns:
        RecommendationIR gom tập tất cả parsed data
    """
    configs = parse_configs(data)
    embeddings = parse_embeddings(data)
    preferences = parse_preferences(data)
    caches = [RecommendationCache.from_dict(c) for c in data.get("caches", [])]
    ab_tests = parse_ab_tests(data)

    return RecommendationIR(
        configs=configs,
        embeddings=embeddings,
        preferences=preferences,
        caches=caches,
        ab_tests=ab_tests,
        default_algorithm=RecommendationAlgorithm(data.get("default_algorithm", "hybrid")),
        default_top_k=data.get("default_top_k", 10),
        enable_cache=data.get("enable_cache", True),
        enable_ab_testing=data.get("enable_ab_testing", False),
    )


__all__ = [
    "RecommendationIR",
    "parse_configs",
    "parse_embeddings",
    "parse_preferences",
    "parse_ab_tests",
    "parse_to_ir",
]
