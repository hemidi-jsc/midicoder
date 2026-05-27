# coding: utf-8
"""Tests cho CP63 — Search & Recommendation Engine models."""

import pytest
from midicoder.packs.cp63_recommendation.models import (
    ABTestConfig,
    ItemEmbedding,
    RecommendationAlgorithm,
    RecommendationCache,
    RecommendationConfig,
    SimilarityMetric,
    UserPreference,
)


# =============================================================================
# Enums
# =============================================================================

class TestRecommendationAlgorithm:
    def test_enum_values(self):
        assert RecommendationAlgorithm.COLLABORATIVE_FILTERING.value == "collaborative_filtering"
        assert RecommendationAlgorithm.CONTENT_BASED.value == "content_based"
        assert RecommendationAlgorithm.HYBRID.value == "hybrid"
        assert RecommendationAlgorithm.POPULARITY.value == "popularity"
        assert RecommendationAlgorithm.RANDOM.value == "random"

    def test_enum_count(self):
        assert len(RecommendationAlgorithm) == 5


class TestSimilarityMetric:
    def test_enum_values(self):
        assert SimilarityMetric.COSINE.value == "cosine"
        assert SimilarityMetric.EUCLIDEAN.value == "euclidean"
        assert SimilarityMetric.DOT_PRODUCT.value == "dot_product"

    def test_enum_count(self):
        assert len(SimilarityMetric) == 3


# =============================================================================
# RecommendationConfig
# =============================================================================

class TestRecommendationConfig:
    def test_creation_with_defaults(self):
        rc = RecommendationConfig(id="rc-1", name="default", algorithm=RecommendationAlgorithm.HYBRID)
        assert rc.item_entity == "Product"
        assert rc.user_entity == "User"
        assert rc.rating_field == "rating"
        assert rc.top_k == 10
        assert rc.min_interactions == 5
        assert rc.ttl_seconds == 3600
        assert rc.cache_enabled is True

    def test_creation_with_all_fields(self):
        rc = RecommendationConfig(
            id="rc-2", name="product-recommend",
            algorithm=RecommendationAlgorithm.COLLABORATIVE_FILTERING,
            item_entity="Article", user_entity="Subscriber",
            rating_field="score", top_k=20, min_interactions=10,
            ttl_seconds=7200, cache_enabled=False,
        )
        assert rc.item_entity == "Article"
        assert rc.top_k == 20
        assert rc.cache_enabled is False

    def test_to_dict(self):
        rc = RecommendationConfig(id="rc-3", name="test", algorithm=RecommendationAlgorithm.POPULARITY)
        d = rc.to_dict()
        assert d["id"] == "rc-3"
        assert d["algorithm"] == "popularity"
        assert d["top_k"] == 10

    def test_from_dict(self):
        data = {
            "id": "rc-4", "name": "from-dict",
            "algorithm": "content_based", "top_k": 50,
            "cache_enabled": False,
        }
        rc = RecommendationConfig.from_dict(data)
        assert rc.algorithm == RecommendationAlgorithm.CONTENT_BASED
        assert rc.top_k == 50
        assert rc.cache_enabled is False

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            RecommendationConfig(id="", name="x", algorithm=RecommendationAlgorithm.HYBRID)

    def test_validation_error_zero_top_k(self):
        with pytest.raises(Exception):
            RecommendationConfig(id="rc-5", name="x", algorithm=RecommendationAlgorithm.HYBRID, top_k=0)

    def test_validation_error_negative_min_interactions(self):
        with pytest.raises(Exception):
            RecommendationConfig(id="rc-6", name="x", algorithm=RecommendationAlgorithm.HYBRID, min_interactions=-1)

    def test_validation_error_negative_ttl(self):
        with pytest.raises(Exception):
            RecommendationConfig(id="rc-7", name="x", algorithm=RecommendationAlgorithm.HYBRID, ttl_seconds=-1)

    def test_roundtrip(self):
        original = RecommendationConfig(
            id="rt-rc", name="rt", algorithm=RecommendationAlgorithm.HYBRID,
            top_k=15, min_interactions=8,
        )
        d = original.to_dict()
        restored = RecommendationConfig.from_dict(d)
        assert restored.id == original.id
        assert restored.algorithm == original.algorithm
        assert restored.top_k == original.top_k
        assert restored.min_interactions == original.min_interactions


# =============================================================================
# ItemEmbedding
# =============================================================================

class TestItemEmbedding:
    def test_creation_with_defaults(self):
        ie = ItemEmbedding(id="ie-1", item_type="product")
        assert ie.embedding_fields == []
        assert ie.similarity_metric == SimilarityMetric.COSINE
        assert ie.dimension == 128
        assert ie.auto_train is True

    def test_creation_with_all_fields(self):
        ie = ItemEmbedding(
            id="ie-2", item_type="article",
            embedding_fields=["title", "description", "tags"],
            similarity_metric=SimilarityMetric.EUCLIDEAN,
            dimension=256, auto_train=False,
        )
        assert len(ie.embedding_fields) == 3
        assert ie.dimension == 256

    def test_to_dict(self):
        ie = ItemEmbedding(id="ie-3", item_type="video", similarity_metric=SimilarityMetric.DOT_PRODUCT)
        d = ie.to_dict()
        assert d["item_type"] == "video"
        assert d["similarity_metric"] == "dot_product"

    def test_from_dict(self):
        data = {
            "id": "ie-4", "item_type": "song",
            "embedding_fields": ["genre", "artist"],
            "dimension": 512, "auto_train": False,
        }
        ie = ItemEmbedding.from_dict(data)
        assert ie.item_type == "song"
        assert ie.dimension == 512
        assert ie.auto_train is False

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            ItemEmbedding(id="", item_type="x")

    def test_validation_error_empty_item_type(self):
        with pytest.raises(Exception):
            ItemEmbedding(id="ie-5", item_type="")

    def test_validation_error_zero_dimension(self):
        with pytest.raises(Exception):
            ItemEmbedding(id="ie-6", item_type="x", dimension=0)

    def test_roundtrip(self):
        original = ItemEmbedding(
            id="rt-ie", item_type="product",
            embedding_fields=["name"], similarity_metric=SimilarityMetric.COSINE,
            dimension=64,
        )
        d = original.to_dict()
        restored = ItemEmbedding.from_dict(d)
        assert restored.id == original.id
        assert restored.item_type == original.item_type
        assert restored.dimension == original.dimension


# =============================================================================
# UserPreference
# =============================================================================

class TestUserPreference:
    def test_creation_with_defaults(self):
        up = UserPreference(id="up-1")
        assert up.user_entity == "User"
        assert up.entity_type == "user"
        assert up.weight == 1.0
        assert up.history_window_days == 30
        assert up.exclude_viewed is True

    def test_creation_with_all_fields(self):
        up = UserPreference(
            id="up-2", user_entity="Subscriber", entity_type="premium_user",
            weight=0.8, history_window_days=60, exclude_viewed=False,
            boost_categories=["electronics", "books"],
        )
        assert up.weight == 0.8
        assert "electronics" in up.boost_categories

    def test_to_dict(self):
        up = UserPreference(id="up-3", weight=0.5)
        d = up.to_dict()
        assert d["weight"] == 0.5
        assert d["exclude_viewed"] is True

    def test_from_dict(self):
        data = {
            "id": "up-4", "weight": 0.3, "history_window_days": 90,
            "exclude_viewed": False, "boost_categories": ["sports"],
        }
        up = UserPreference.from_dict(data)
        assert up.weight == 0.3
        assert up.history_window_days == 90
        assert up.exclude_viewed is False

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            UserPreference(id="")

    def test_validation_error_weight_over_one(self):
        with pytest.raises(Exception):
            UserPreference(id="up-5", weight=1.5)

    def test_validation_error_negative_weight(self):
        with pytest.raises(Exception):
            UserPreference(id="up-6", weight=-0.1)

    def test_validation_error_zero_history_window(self):
        with pytest.raises(Exception):
            UserPreference(id="up-7", history_window_days=0)

    def test_roundtrip(self):
        original = UserPreference(
            id="rt-up", weight=0.75, history_window_days=45,
            boost_categories=["tech"],
        )
        d = original.to_dict()
        restored = UserPreference.from_dict(d)
        assert restored.id == original.id
        assert restored.weight == original.weight
        assert restored.history_window_days == original.history_window_days
        assert restored.boost_categories == original.boost_categories


# =============================================================================
# RecommendationCache
# =============================================================================

class TestRecommendationCache:
    def test_creation_with_defaults(self):
        rcache = RecommendationCache(id="rc-1", user_id="u1", item_type="product")
        assert rcache.items == []
        assert rcache.score == 0.0
        assert rcache.generated_at is not None
        assert rcache.ttl_seconds == 3600

    def test_creation_with_all_fields(self):
        rcache = RecommendationCache(
            id="rc-2", user_id="u2", item_type="article",
            items=["item-1", "item-2", "item-3"],
            score=0.95, ttl_seconds=1800,
        )
        assert len(rcache.items) == 3
        assert rcache.score == 0.95

    def test_to_dict(self):
        rcache = RecommendationCache(id="rc-3", user_id="u3", item_type="video", items=["v1"])
        d = rcache.to_dict()
        assert d["user_id"] == "u3"
        assert d["items"] == ["v1"]
        assert d["ttl_seconds"] == 3600

    def test_from_dict(self):
        data = {
            "id": "rc-4", "user_id": "u4", "item_type": "song",
            "items": ["s1", "s2"], "score": 0.8,
        }
        rcache = RecommendationCache.from_dict(data)
        assert rcache.user_id == "u4"
        assert rcache.items == ["s1", "s2"]

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            RecommendationCache(id="", user_id="u", item_type="x")

    def test_roundtrip(self):
        original = RecommendationCache(
            id="rt-rc", user_id="u1", item_type="product",
            items=["p1", "p2"], score=0.7,
        )
        d = original.to_dict()
        restored = RecommendationCache.from_dict(d)
        assert restored.id == original.id
        assert restored.user_id == original.user_id
        assert restored.items == original.items
        assert restored.score == original.score


# =============================================================================
# ABTestConfig
# =============================================================================

class TestABTestConfig:
    def test_creation_with_defaults(self):
        ab = ABTestConfig(id="ab-1", name="baseline")
        assert ab.success_metric == "click_through_rate"
        assert ab.min_sample_size == 1000
        assert ab.variations == []
        assert ab.traffic_split == []

    def test_creation_with_valid_split(self):
        ab = ABTestConfig(
            id="ab-2", name="algo-compare",
            variations=["hybrid", "collaborative"],
            traffic_split=[0.5, 0.5],
        )
        assert len(ab.variations) == 2
        assert sum(ab.traffic_split) == 1.0

    def test_to_dict(self):
        ab = ABTestConfig(
            id="ab-3", name="test",
            variations=["a", "b"], traffic_split=[0.6, 0.4],
        )
        d = ab.to_dict()
        assert d["name"] == "test"
        assert d["traffic_split"] == [0.6, 0.4]
        assert d["success_metric"] == "click_through_rate"

    def test_from_dict(self):
        data = {
            "id": "ab-4", "name": "from-dict",
            "variations": ["cf", "cb"],
            "traffic_split": [0.7, 0.3],
            "success_metric": "conversion_rate",
        }
        ab = ABTestConfig.from_dict(data)
        assert ab.variations == ["cf", "cb"]
        assert ab.success_metric == "conversion_rate"

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            ABTestConfig(id="", name="x")

    def test_validation_error_mismatched_lengths(self):
        with pytest.raises(Exception):
            ABTestConfig(id="ab-5", name="x", variations=["a", "b"], traffic_split=[0.5])

    def test_validation_error_split_not_one(self):
        with pytest.raises(Exception):
            ABTestConfig(id="ab-6", name="x", variations=["a", "b"], traffic_split=[0.5, 0.6])

    def test_roundtrip(self):
        original = ABTestConfig(
            id="rt-ab", name="rt",
            variations=["v1", "v2"], traffic_split=[0.5, 0.5],
            min_sample_size=5000,
        )
        d = original.to_dict()
        restored = ABTestConfig.from_dict(d)
        assert restored.id == original.id
        assert restored.variations == original.variations
        assert restored.traffic_split == original.traffic_split
        assert restored.min_sample_size == original.min_sample_size
