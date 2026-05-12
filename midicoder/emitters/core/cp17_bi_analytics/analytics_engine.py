# coding: utf-8
"""
Mô-đun analytics runtime engine (CP17).

Cung cấp:
- QueryResult: Kết quả của một query analytics — immutable
- AnalyticsEngine: Engine cho analytics — query, aggregation từ CP15 MetricRegistry

Obligation: data freshness — mỗi query có last_refresh, không stale hơn max_stale_seconds

Đọc dữ liệu metric từ CP15 MetricRegistry.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from midicoder.emitters.core.cp17_bi_analytics.models import AnalyticsModel
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# QueryResult
# ===========================================================================


@dataclass(frozen=True)
class QueryResult:
    """Kết quả của một query analytics — immutable.

    Attributes:
        model_name: Tên model đã query
        filters: Bộ lọc đã dùng
        aggregations: Kết quả aggregation {aggregation_type: value}
        row_count: Số lượng rows trả về
        last_refresh: Thời điểm refresh cuối cùng
        hash_value: SHA-256 hash của kết quả (obligation: data freshness)
    """
    model_name: str
    filters: dict
    aggregations: dict
    row_count: int
    last_refresh: datetime
    hash_value: str

    def to_dict(self) -> dict[str, Any]:
        """Chuyển QueryResult sang dict format."""
        return {
            "model_name": self.model_name,
            "filters": self.filters,
            "aggregations": self.aggregations,
            "row_count": self.row_count,
            "last_refresh": self.last_refresh.isoformat(),
            "hash_value": self.hash_value,
        }


# ===========================================================================
# AnalyticsEngine
# ===========================================================================


class AnalyticsEngine:
    """Engine cho analytics — query, aggregation từ CP15 MetricRegistry.

    Cung cấp:
    - register_model(model) → đăng ký analytics model
    - unregister_model(name) → hủy đăng ký model
    - query(model_name, filters, aggregations, registry) → thực hiện query + aggregation
    - get_available_models() → lấy danh sách models
    - is_stale(model_name) → kiểm tra kết quả có stale không

    Obligation: data freshness — mỗi query có last_refresh, không stale hơn max_stale_seconds

    Đọc dữ liệu metric từ CP15 MetricRegistry
    """

    def __init__(self) -> None:
        """Khởi tạo AnalyticsEngine."""
        self._models: dict[str, AnalyticsModel] = {}
        self._cache: dict[str, QueryResult] = {}

    def register_model(self, model: AnalyticsModel) -> None:
        """Đăng ký analytics model.

        Args:
            model: AnalyticsModel cần đăng ký
        """
        self._models[model.name] = model

    def unregister_model(self, name: str) -> bool:
        """Hủy đăng ký model.

        Args:
            name: Tên model cần hủy đăng ký

        Returns:
            True nếu thành công, False nếu model không tồn tại
        """
        if name not in self._models:
            return False
        del self._models[name]
        # Xóa cache liên quan
        self._cache.pop(name, None)
        return True

    def query(
        self,
        model_name: str,
        filters: dict | None = None,
        aggregations: list | None = None,
        registry: Any = None,
    ) -> QueryResult:
        """Thực hiện query + aggregation.

        Query dữ liệu từ CP15 MetricRegistry cho model đã đăng ký.
        Nếu không có registry, trả về kết quả rỗng.

        Args:
            model_name: Tên model đã đăng ký
            filters: Bộ lọc (tùy chọn)
            aggregations: Danh sách aggregation types (sum, average, count, max, min)
            registry: CP15 MetricRegistry (tùy chọn, cho test)

        Returns:
            QueryResult với kết quả aggregation

        Raises:
            KeyError: Nếu model không tồn tại
        """
        if model_name not in self._models:
            raise KeyError(
                f"Model '{model_name}' không tồn tại. "
                f"Đăng ký model trước khi query."
            )

        model = self._models[model_name]
        filters = filters or {}
        aggregations = aggregations or model.aggregations or ["count"]

        # Lấy dữ liệu từ registry
        values: list[float] = []
        if registry is not None:
            for metric_name in model.metric_names:
                entries = registry.get(metric_name, filters if filters else None)
                for entry in entries:
                    values.append(entry.value)

        # Thực hiện aggregation cho từng loại
        agg_results: dict[str, float] = {}
        for agg_type in aggregations:
            agg_results[agg_type] = self._aggregate(values, agg_type)

        # Tính hash cho kết quả — obligation: data freshness
        now = datetime.now(timezone.utc)
        hash_input = json.dumps({
            "model_name": model_name,
            "filters": filters,
            "aggregations": agg_results,
            "row_count": len(values),
            "last_refresh": now.isoformat(),
        }, sort_keys=True)
        hash_value = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        result = QueryResult(
            model_name=model_name,
            filters=filters,
            aggregations=agg_results,
            row_count=len(values),
            last_refresh=now,
            hash_value=hash_value,
        )

        # Lưu vào cache
        self._cache[model_name] = result

        return result

    def _aggregate(self, values: list[float], agg_type: str) -> float:
        """Thực hiện aggregation: sum, average, count, max, min.

        Args:
            values: Danh sách giá trị để aggregate
            agg_type: Loại aggregation (sum, average, count, max, min)

        Returns:
            Kết quả aggregation. Trả về 0 nếu values rỗng.
        """
        if not values:
            return 0.0

        if agg_type == "sum":
            return sum(values)
        elif agg_type == "average":
            return sum(values) / len(values)
        elif agg_type == "count":
            return float(len(values))
        elif agg_type == "max":
            return max(values)
        elif agg_type == "min":
            return min(values)
        else:
            # Loại aggregation không xác định — trả về count mặc định
            return float(len(values))

    def get_available_models(self) -> list[AnalyticsModel]:
        """Lấy danh sách models đã đăng ký.

        Returns:
            Danh sách AnalyticsModel
        """
        return list(self._models.values())

    def is_stale(self, model_name: str) -> bool:
        """Kiểm tra kết quả có stale không.

        So sánh thời gian last_refresh với max_stale_seconds của model.

        Args:
            model_name: Tên model

        Returns:
            True nếu stale (không có cache hoặc quá thời gian stale)
        """
        if model_name not in self._models:
            return True

        if model_name not in self._cache:
            return True

        model = self._models[model_name]
        cached = self._cache[model_name]
        now = datetime.now(timezone.utc)
        elapsed = (now - cached.last_refresh).total_seconds()

        return elapsed > model.max_stale_seconds
