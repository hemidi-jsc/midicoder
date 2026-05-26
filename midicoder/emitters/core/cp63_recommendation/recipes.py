# coding: utf-8
"""
Mô-đun recipes cho CP63 — Search & Recommendation Engine.

Cung cấp các recipe để build RecommendationIR cho các use case phổ biến:
- collaborative_filtering_recipe: User-user/item-item collaborative filtering
- content_based_recipe: Content-based recommendation với item features
- hybrid_recipe: Hybrid kết hợp collaborative + content-based weighted scoring
- popularity_recipe: Popularity-based fallback recommendation
- ab_test_recipe: A/B test cho multiple recommendation strategies

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp63_recommendation.parser import (
    RecommendationIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: RecommendationIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: RecommendationIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def collaborative_filtering_recipe() -> RecipeOutput:
    """Recipe: Collaborative filtering recommendation engine.

    Sử dụng user-user và item-item collaborative filtering để
    generate recommendations dựa trên hành vi tương tác của người dùng.
    Thuật toán tìm users/items tương tự và recommend items mà những
    users/items tương tự đó đã tương tác.

    Cấu hình:
    - Algorithm: collaborative_filtering
    - Item entity: Product
    - User entity: User
    - Rating field: rating
    - Top-K: 10 items
    - Min interactions: 5 (để đảm bảo độ tin cậy)
    - Cache: bật (TTL 3600s)
    - User preference: 30 ngày history window, loại bỏ items đã xem

    Returns:
        RecipeOutput chứa RecommendationIR
    """
    data = {
        "configs": [
            {
                "id": "cf_user_user",
                "name": "User-User Collaborative Filtering",
                "algorithm": "collaborative_filtering",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "rating",
                "top_k": 10,
                "min_interactions": 5,
                "ttl_seconds": 3600,
                "cache_enabled": True,
            }
        ],
        "preferences": [
            {
                "id": "user_pref_cf",
                "user_entity": "User",
                "entity_type": "user",
                "weight": 0.8,
                "history_window_days": 30,
                "exclude_viewed": True,
                "boost_categories": [],
            }
        ],
        "default_algorithm": "collaborative_filtering",
        "default_top_k": 10,
        "enable_cache": True,
        "enable_ab_testing": False,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="collaborative_filtering_recipe",
        description="Collaborative filtering — user-user CF với product ratings",
        ir=ir,
        raw_data=data,
    )


def content_based_recipe() -> RecipeOutput:
    """Recipe: Content-based recommendation với item features.

    Sử dụng item embeddings dựa trên các đặc trưng nội dung (tên,
    mô tả, category, tags) để tính toán độ tương đồng giữa items
    và recommend các items tương tự với những gì user đã tương tác.

    Cấu hình:
    - Algorithm: content_based
    - Item embedding với cosine similarity, 128 dimensions
    - Embedding fields: name, description, category, tags
    - Auto-train embedding model
    - Top-K: 10 items
    - User preference: 14 ngày history, boost categories

    Returns:
        RecipeOutput chứa RecommendationIR
    """
    data = {
        "configs": [
            {
                "id": "cb_content",
                "name": "Content-Based Recommendation",
                "algorithm": "content_based",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "interaction_score",
                "top_k": 10,
                "min_interactions": 3,
                "ttl_seconds": 7200,
                "cache_enabled": True,
            }
        ],
        "embeddings": [
            {
                "id": "product_embedding",
                "item_type": "product",
                "embedding_fields": ["name", "description", "category", "tags"],
                "similarity_metric": "cosine",
                "dimension": 128,
                "auto_train": True,
            }
        ],
        "preferences": [
            {
                "id": "user_pref_cb",
                "user_entity": "User",
                "entity_type": "user",
                "weight": 1.0,
                "history_window_days": 14,
                "exclude_viewed": True,
                "boost_categories": ["electronics", "accessories"],
            }
        ],
        "default_algorithm": "content_based",
        "default_top_k": 10,
        "enable_cache": True,
        "enable_ab_testing": False,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="content_based_recipe",
        description="Content-based recommendation — item embeddings với cosine similarity",
        ir=ir,
        raw_data=data,
    )


def hybrid_recipe() -> RecipeOutput:
    """Recipe: Hybrid recommendation (collaborative + content-based).

    Kết hợp collaborative filtering và content-based recommendation
    thông qua weighted scoring. Hybrid approach giúp giảm cold-start
    problem: khi không đủ dữ liệu tương tác, content-based sẽ đảm nhiệm;
    khi có đủ dữ liệu, collaborative filtering sẽ đóng vai trò chính.

    Cấu hình:
    - Primary: hybrid (collaborative 70% + content-based 30%)
    - Fallback: content_based khi collaborative không đủ data
    - Item embedding: 256 dimensions, dot product
    - Top-K: 15 items
    - Cache: bật (TTL 1800s)
    - User preference: 60 ngày history, loại bỏ items đã xem
    - Boost categories: electronics, books

    Returns:
        RecipeOutput chứa RecommendationIR
    """
    data = {
        "configs": [
            {
                "id": "hybrid_primary",
                "name": "Hybrid Recommendation Engine",
                "algorithm": "hybrid",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "composite_score",
                "top_k": 15,
                "min_interactions": 5,
                "ttl_seconds": 1800,
                "cache_enabled": True,
                "metadata": {
                    "collaborative_weight": 0.7,
                    "content_weight": 0.3,
                },
            },
            {
                "id": "cf_fallback",
                "name": "Collaborative Filtering Fallback",
                "algorithm": "collaborative_filtering",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "rating",
                "top_k": 15,
                "min_interactions": 10,
                "ttl_seconds": 3600,
                "cache_enabled": True,
            },
        ],
        "embeddings": [
            {
                "id": "product_embedding_hybrid",
                "item_type": "product",
                "embedding_fields": ["name", "description", "category", "tags", "brand"],
                "similarity_metric": "dot_product",
                "dimension": 256,
                "auto_train": True,
            }
        ],
        "preferences": [
            {
                "id": "user_pref_hybrid",
                "user_entity": "User",
                "entity_type": "user",
                "weight": 0.9,
                "history_window_days": 60,
                "exclude_viewed": True,
                "boost_categories": ["electronics", "books"],
            }
        ],
        "default_algorithm": "hybrid",
        "default_top_k": 15,
        "enable_cache": True,
        "enable_ab_testing": False,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="hybrid_recipe",
        description="Hybrid recommendation — collaborative 70% + content-based 30% weighted scoring",
        ir=ir,
        raw_data=data,
    )


def popularity_recipe() -> RecipeOutput:
    """Recipe: Popularity-based fallback recommendation.

    Sử dụng popularity-based recommendation làm fallback khi các
    thuật toán khác không thể generate kết quả (cold start, không
    đủ data, hoặc hệ thống quá tải). Recommendations dựa trên
    số lượng views, ratings, hoặc purchases gần đây.

    Cấu hình:
    - Algorithm: popularity
    - Top-K: 20 items (nhiều hơn các algorithm khác)
    - Min interactions: 0 (không cần data training)
    - Cache: bật (TTL 86400s = 24h)
    - Không cần embedding hay preference phức tạp

    Returns:
        RecipeOutput chứa RecommendationIR
    """
    data = {
        "configs": [
            {
                "id": "popularity_fallback",
                "name": "Popularity Fallback",
                "algorithm": "popularity",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "view_count",
                "top_k": 20,
                "min_interactions": 0,
                "ttl_seconds": 86400,
                "cache_enabled": True,
                "metadata": {
                    "popularity_metric": "weighted_score",
                    "view_weight": 0.2,
                    "rating_weight": 0.5,
                    "purchase_weight": 0.3,
                    "time_decay_hours": 168,
                },
            }
        ],
        "default_algorithm": "popularity",
        "default_top_k": 20,
        "enable_cache": True,
        "enable_ab_testing": False,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="popularity_recipe",
        description="Popularity-based fallback — weighted view/rating/purchase score với time decay",
        ir=ir,
        raw_data=data,
    )


def ab_test_recipe() -> RecipeOutput:
    """Recipe: A/B test cho multiple recommendation strategies.

    Cấu hình A/B test để so sánh hiệu quả của các thuật toán
    recommendation khác nhau. Traffic được chia đều cho các
    variations: collaborative filtering, content-based, và hybrid.
    Metric đánh giá: click_through_rate.

    Cấu hình:
    - 3 variations: collaborative_filtering, content_based, hybrid
    - Traffic split: 33.3% mỗi variation
    - Success metric: click_through_rate
    - Min sample size: 5000
    - Mỗi variation có config riêng

    Returns:
        RecipeOutput chứa RecommendationIR
    """
    data = {
        "configs": [
            {
                "id": "ab_cf",
                "name": "A/B Test — Collaborative Filtering",
                "algorithm": "collaborative_filtering",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "rating",
                "top_k": 10,
                "min_interactions": 5,
                "ttl_seconds": 3600,
                "cache_enabled": True,
            },
            {
                "id": "ab_cb",
                "name": "A/B Test — Content-Based",
                "algorithm": "content_based",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "interaction_score",
                "top_k": 10,
                "min_interactions": 3,
                "ttl_seconds": 3600,
                "cache_enabled": True,
            },
            {
                "id": "ab_hybrid",
                "name": "A/B Test — Hybrid",
                "algorithm": "hybrid",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "composite_score",
                "top_k": 10,
                "min_interactions": 5,
                "ttl_seconds": 3600,
                "cache_enabled": True,
            },
        ],
        "embeddings": [
            {
                "id": "ab_product_embedding",
                "item_type": "product",
                "embedding_fields": ["name", "description", "category", "tags"],
                "similarity_metric": "cosine",
                "dimension": 128,
                "auto_train": True,
            }
        ],
        "ab_tests": [
            {
                "id": "rec_algo_comparison",
                "name": "Recommendation Algorithm Comparison",
                "variations": ["collaborative_filtering", "content_based", "hybrid"],
                "traffic_split": [0.333, 0.333, 0.334],
                "success_metric": "click_through_rate",
                "min_sample_size": 5000,
            }
        ],
        "preferences": [
            {
                "id": "user_pref_ab",
                "user_entity": "User",
                "entity_type": "user",
                "weight": 1.0,
                "history_window_days": 30,
                "exclude_viewed": True,
                "boost_categories": [],
            }
        ],
        "default_algorithm": "hybrid",
        "default_top_k": 10,
        "enable_cache": True,
        "enable_ab_testing": True,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="ab_test_recipe",
        description="A/B test — so sánh CF, Content-Based, Hybrid với CTR metric",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "collaborative_filtering_recipe",
    "content_based_recipe",
    "hybrid_recipe",
    "popularity_recipe",
    "ab_test_recipe",
]
