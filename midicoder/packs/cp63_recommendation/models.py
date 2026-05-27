# coding: utf-8
"""
Mô-đun models cho CP63 — Search & Recommendation Engine.

Định nghĩa các dataclass biểu diễn:
- RecommendationAlgorithm: Loại thuật toán recommendation (collaborative_filtering, content_based, hybrid, popularity, random)
- SimilarityMetric: Phương pháp tính độ tương đồng (cosine, euclidean, dot_product)
- RecommendationConfig: Cấu hình recommendation engine
- ItemEmbedding: Embedding vector cho items
- UserPreference: Sở thích người dùng
- RecommendationCache: Cache kết quả recommendation
- ABTestConfig: Cấu hình A/B test cho recommendation strategies

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class RecommendationAlgorithm(str, Enum):
    """Loại thuật toán recommendation.

    - COLLABORATIVE_FILTERING: Collaborative filtering (user-user/item-item)
    - CONTENT_BASED: Content-based recommendation với item features
    - HYBRID: Hybrid kết hợp collaborative + content-based
    - POPULARITY: Popularity-based fallback
    - RANDOM: Random recommendation (cho A/B test control group)
    """
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    POPULARITY = "popularity"
    RANDOM = "random"


class SimilarityMetric(str, Enum):
    """Phương pháp tính độ tương đồng.

    - COSINE: Cosine similarity
    - EUCLIDEAN: Euclidean distance
    - DOT_PRODUCT: Dot product
    """
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"


# ===========================================================================
# RecommendationConfig
# ===========================================================================


@dataclass
class RecommendationConfig:
    """Cấu hình recommendation engine.

    Định nghĩa một recommendation engine với thuật toán, thực thể mục tiêu,
    và các tham số hiệu suất.

    Attributes:
        id: ID duy nhất của cấu hình recommendation
        name: Tên mô tả của cấu hình
        algorithm: Loại thuật toán recommendation
        item_entity: Tên entity của items được recommend (vd: "Product")
        user_entity: Tên entity của users nhận recommendation (vd: "User")
        rating_field: Trường rating/score để tính toán
        top_k: Số lượng items tối đa trả về
        min_interactions: Số tương tác tối thiểu để train model
        ttl_seconds: Time-to-live cho cached recommendations
        cache_enabled: Có bật cache không
        metadata: Dữ liệu bổ sung
    """
    id: str
    name: str
    algorithm: RecommendationAlgorithm
    item_entity: str = "Product"
    user_entity: str = "User"
    rating_field: str = "rating"
    top_k: int = 10
    min_interactions: int = 5
    ttl_seconds: int = 3600
    cache_enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate config sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="RecommendationConfig.id bắt buộc và không được để trống",
            )
        if self.top_k < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"top_k phải >= 1, nhận được: {self.top_k}",
            )
        if self.min_interactions < 0:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"min_interactions phải >= 0, nhận được: {self.min_interactions}",
            )
        if self.ttl_seconds < 0:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"ttl_seconds phải >= 0, nhận được: {self.ttl_seconds}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecommendationConfig sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "algorithm": self.algorithm.value,
            "item_entity": self.item_entity,
            "user_entity": self.user_entity,
            "rating_field": self.rating_field,
            "top_k": self.top_k,
            "min_interactions": self.min_interactions,
            "ttl_seconds": self.ttl_seconds,
            "cache_enabled": self.cache_enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecommendationConfig":
        """Tạo RecommendationConfig từ dict."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            algorithm=RecommendationAlgorithm(data.get("algorithm", "hybrid")),
            item_entity=data.get("item_entity", "Product"),
            user_entity=data.get("user_entity", "User"),
            rating_field=data.get("rating_field", "rating"),
            top_k=data.get("top_k", 10),
            min_interactions=data.get("min_interactions", 5),
            ttl_seconds=data.get("ttl_seconds", 3600),
            cache_enabled=data.get("cache_enabled", True),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# ItemEmbedding
# ===========================================================================


@dataclass
class ItemEmbedding:
    """Embedding vector cho items.

    Định nghĩa cách biểu diễn items dưới dạng vector để tính toán
    độ tương đồng, hỗ trợ content-based recommendation.

    Attributes:
        id: ID duy nhất của embedding config
        item_type: Loại item (vd: "product", "article", "video")
        embedding_fields: Danh sách các fields dùng để tạo embedding
        similarity_metric: Phương pháp tính độ tương đồng
        dimension: Số chiều của embedding vector
        auto_train: Có tự động train embedding model không
        metadata: Dữ liệu bổ sung
    """
    id: str
    item_type: str
    embedding_fields: list[str] = field(default_factory=list)
    similarity_metric: SimilarityMetric = SimilarityMetric.COSINE
    dimension: int = 128
    auto_train: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate item embedding sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="ItemEmbedding.id bắt buộc và không được để trống",
            )
        if not self.item_type or not self.item_type.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="ItemEmbedding.item_type bắt buộc",
            )
        if self.dimension < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"dimension phải >= 1, nhận được: {self.dimension}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ItemEmbedding sang dict."""
        return {
            "id": self.id,
            "item_type": self.item_type,
            "embedding_fields": self.embedding_fields,
            "similarity_metric": self.similarity_metric.value,
            "dimension": self.dimension,
            "auto_train": self.auto_train,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ItemEmbedding":
        """Tạo ItemEmbedding từ dict."""
        return cls(
            id=data["id"],
            item_type=data.get("item_type", ""),
            embedding_fields=data.get("embedding_fields", []),
            similarity_metric=SimilarityMetric(data.get("similarity_metric", "cosine")),
            dimension=data.get("dimension", 128),
            auto_train=data.get("auto_train", True),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# UserPreference
# ===========================================================================


@dataclass
class UserPreference:
    """Sở thích người dùng.

    Định nghĩa cách thu thập và trọng số hóa user preferences
    cho recommendation personalization.

    Attributes:
        id: ID duy nhất của preference config
        user_entity: Tên entity của user
        entity_type: Loại entity (vd: "user", "tenant_admin")
        weight: Trọng số của preference (0.0 - 1.0)
        history_window_days: Số ngày lịch sử tương tác để xem xét
        exclude_viewed: Có loại bỏ items đã xem không
        boost_categories: Danh sách categories ưu tiên
        metadata: Dữ liệu bổ sung
    """
    id: str
    user_entity: str = "User"
    entity_type: str = "user"
    weight: float = 1.0
    history_window_days: int = 30
    exclude_viewed: bool = True
    boost_categories: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate user preference sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="UserPreference.id bắt buộc và không được để trống",
            )
        if not 0.0 <= self.weight <= 1.0:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"weight phải trong khoảng [0.0, 1.0], nhận được: {self.weight}",
            )
        if self.history_window_days < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"history_window_days phải >= 1, nhận được: {self.history_window_days}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển UserPreference sang dict."""
        return {
            "id": self.id,
            "user_entity": self.user_entity,
            "entity_type": self.entity_type,
            "weight": self.weight,
            "history_window_days": self.history_window_days,
            "exclude_viewed": self.exclude_viewed,
            "boost_categories": self.boost_categories,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserPreference":
        """Tạo UserPreference từ dict."""
        return cls(
            id=data["id"],
            user_entity=data.get("user_entity", "User"),
            entity_type=data.get("entity_type", "user"),
            weight=data.get("weight", 1.0),
            history_window_days=data.get("history_window_days", 30),
            exclude_viewed=data.get("exclude_viewed", True),
            boost_categories=data.get("boost_categories", []),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# RecommendationCache
# ===========================================================================


@dataclass
class RecommendationCache:
    """Cache kết quả recommendation.

    Lưu trữ kết quả recommendation đã tính toán để giảm độ trễ
    và chi phí tính toán cho các request sau.

    Attributes:
        id: ID duy nhất của cache entry
        user_id: ID user nhận recommendation
        item_type: Loại item được recommend
        items: Danh sách item IDs được recommend
        score: Danh sách scores tương ứng
        generated_at: Thời điểm tạo recommendations
        ttl_seconds: Time-to-live của cache entry
    """
    id: str
    user_id: str
    item_type: str
    items: list[str] = field(default_factory=list)
    score: float = 0.0
    generated_at: datetime | None = None
    ttl_seconds: int = 3600

    def __post_init__(self) -> None:
        """Validate recommendation cache sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="RecommendationCache.id bắt buộc và không được để trống",
            )
        now = datetime.now(timezone.utc)
        if self.generated_at is None:
            self.generated_at = now

    @property
    def is_expired(self) -> bool:
        """Trả về True nếu cache đã hết hạn."""
        if self.generated_at is None:
            return True
        expiry = self.generated_at.timestamp() + self.ttl_seconds
        return datetime.now(timezone.utc).timestamp() > expiry

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecommendationCache sang dict."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "item_type": self.item_type,
            "items": self.items,
            "score": self.score,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "ttl_seconds": self.ttl_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecommendationCache":
        """Tạo RecommendationCache từ dict."""
        return cls(
            id=data["id"],
            user_id=data.get("user_id", ""),
            item_type=data.get("item_type", ""),
            items=data.get("items", []),
            score=data.get("score", 0.0),
            ttl_seconds=data.get("ttl_seconds", 3600),
        )


# ===========================================================================
# ABTestConfig
# ===========================================================================


@dataclass
class ABTestConfig:
    """Cấu hình A/B test cho recommendation strategies.

    Cho phép so sánh hiệu quả của các thuật toán recommendation
    khác nhau thông qua A/B testing với traffic splitting.

    Attributes:
        id: ID duy nhất của A/B test
        name: Tên mô tả của experiment
        variations: Danh sách recommendation variation names
        traffic_split: Tỷ lệ phân chia traffic (phải tổng = 1.0)
        success_metric: Metric đánh giá thành công (vd: "click_through_rate")
        min_sample_size: Số lượng mẫu tối thiểu để có ý nghĩa thống kê
        metadata: Dữ liệu bổ sung
    """
    id: str
    name: str
    variations: list[str] = field(default_factory=list)
    traffic_split: list[float] = field(default_factory=list)
    success_metric: str = "click_through_rate"
    min_sample_size: int = 1000
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate A/B test config sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="ABTestConfig.id bắt buộc và không được để trống",
            )
        if len(self.variations) != len(self.traffic_split):
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason="Số lượng variations phải bằng số lượng traffic_split",
            )
        if self.traffic_split and abs(sum(self.traffic_split) - 1.0) > 0.001:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"traffic_split phải tổng bằng 1.0, nhận được: {sum(self.traffic_split)}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ABTestConfig sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "variations": self.variations,
            "traffic_split": self.traffic_split,
            "success_metric": self.success_metric,
            "min_sample_size": self.min_sample_size,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ABTestConfig":
        """Tạo ABTestConfig từ dict."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            variations=data.get("variations", []),
            traffic_split=data.get("traffic_split", []),
            success_metric=data.get("success_metric", "click_through_rate"),
            min_sample_size=data.get("min_sample_size", 1000),
            metadata=data.get("metadata", {}),
        )
