# coding: utf-8
"""
Mô-đun metrics runtime engine (CP15).

Cung cấp:
- MetricEntry: Một entry metric đã ghi — immutable sau khi tạo
- MetricRegistry: Registry cho metrics — lưu trữ và export metrics

Obligation: metric retention — metrics chỉ append, không sửa giá trị cũ

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from midicoder.packs.cp_core_observability.models import MetricType
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


@dataclass(frozen=True)
class MetricEntry:
    """Một entry metric đã ghi — immutable sau khi tạo."""

    name: str
    value: float
    metric_type: str
    labels: dict
    timestamp: datetime


class MetricRegistry:
    """Registry cho metrics — lưu trữ và export metrics.

    Cung cấp:
    - counter(name, labels) -> tăng counter
    - gauge(name, value, labels) -> set gauge value
    - histogram(name, value, labels) -> ghi histogram bucket
    - record(name, value, labels) -> ghi metric chung
    - get(name, labels) -> lấy giá trị hiện tại
    - export_prometheus() -> export format Prometheus
    - retention_check(older_than_days) -> xóa metrics cũ

    Obligation: metric retention — metrics chỉ append, không sửa giá trị cũ
    """

    def __init__(self, retention_days: int = 30) -> None:
        """Khởi tạo MetricRegistry.

        Args:
            retention_days: Số ngày lưu trữ metric (phải >= 1)

        Raises:
            ValueError: Nếu retention_days < 1
        """
        if retention_days < 1:
            raise EM.raise_error(
                ErrorCode.MDC-C03_METRIC_RETENTION_INVALID,
                retention_days=retention_days,
                minimum=1,
            )
        self._retention_days: int = retention_days
        self._entries: list[MetricEntry] = []

    def counter(self, name: str, labels: Optional[dict] = None) -> float:
        """Tăng counter 1 đơn vị. Returns value sau khi tăng.

        Counter hoạt động bằng cách cộng dồn tất cả các entry có cùng
        name và labels. Mỗi lần gọi sẽ append một entry mới với value=1.

        Args:
            name: Tên counter
            labels: Các label để phân biệt counter (tùy chọn)

        Returns:
            Giá trị tổng cộng sau khi tăng
        """
        labels = labels or {}
        self._entries.append(MetricEntry(
            name=name,
            value=1.0,
            metric_type=MetricType.COUNTER.value,
            labels=dict(labels),
            timestamp=datetime.now(timezone.utc),
        ))
        return self._sum_for_key(name, labels, MetricType.COUNTER.value)

    def gauge(self, name: str, value: float, labels: Optional[dict] = None) -> float:
        """Set gauge value. Returns value.

        Gauge lưu giá trị mới nhất. Mỗi lần gọi sẽ append một entry mới —
        các entry cũ vẫn được giữ lại cho mục đích retention.

        Args:
            name: Tên gauge
            value: Giá trị gauge
            labels: Các label để phân biệt gauge (tùy chọn)

        Returns:
            Giá trị gauge vừa đặt
        """
        labels = labels or {}
        self._entries.append(MetricEntry(
            name=name,
            value=float(value),
            metric_type=MetricType.GAUGE.value,
            labels=dict(labels),
            timestamp=datetime.now(timezone.utc),
        ))
        return float(value)

    def histogram(self, name: str, value: float, labels: Optional[dict] = None) -> None:
        """Ghi histogram observation.

        Mỗi observation được lưu như một entry riêng biệt.

        Args:
            name: Tên histogram
            value: Giá trị observation
            labels: Các label để phân biệt histogram (tùy chọn)
        """
        labels = labels or {}
        self._entries.append(MetricEntry(
            name=name,
            value=float(value),
            metric_type=MetricType.HISTOGRAM.value,
            labels=dict(labels),
            timestamp=datetime.now(timezone.utc),
        ))

    def record(self, name: str, value: float, labels: Optional[dict] = None) -> MetricEntry:
        """Ghi metric entry chung. Returns entry.

        Args:
            name: Tên metric
            value: Giá trị metric
            labels: Các label (tùy chọn)

        Returns:
            MetricEntry vừa tạo
        """
        labels = labels or {}
        entry = MetricEntry(
            name=name,
            value=float(value),
            metric_type=MetricType.GAUGE.value,
            labels=dict(labels),
            timestamp=datetime.now(timezone.utc),
        )
        self._entries.append(entry)
        return entry

    def get(self, name: str, labels: Optional[dict] = None) -> list[MetricEntry]:
        """Lấy tất cả entries cho metric name.

        Nếu labels được cung cấp, chỉ trả về entries khớp với labels.

        Args:
            name: Tên metric
            labels: Các label để lọc (tùy chọn)

        Returns:
            Danh sách MetricEntry khớp với tiêu chí
        """
        results: list[MetricEntry] = []
        for entry in self._entries:
            if entry.name != name:
                continue
            if labels is not None:
                if not self._labels_match(entry.labels, labels):
                    continue
            results.append(entry)
        return results

    def export_prometheus(self) -> str:
        """Export metrics sang Prometheus text format.

        Format: metric_name{labels} value\\n

        Đối với counter: tổng hợp tất cả entries có cùng name+labels.
        Đối với gauge: lấy giá trị mới nhất.
        Đối với histogram: xuất mỗi observation riêng.

        Returns:
            Chuỗi text format Prometheus
        """
        lines: list[str] = []

        # Xử lý counter — tổng hợp theo name+labels
        counter_totals: dict[tuple[str, str], float] = {}
        gauge_latest: dict[tuple[str, str], float] = {}

        for entry in self._entries:
            label_key = self._label_key(entry.labels)
            entry_type = entry.metric_type

            if entry_type == MetricType.COUNTER.value:
                key = (entry.name, label_key)
                counter_totals[key] = counter_totals.get(key, 0.0) + entry.value
            elif entry_type == MetricType.GAUGE.value:
                key = (entry.name, label_key)
                gauge_latest[key] = entry.value
            elif entry_type == MetricType.HISTOGRAM.value:  # pragma: no branch
                label_str = self._format_labels(entry.labels)
                lines.append(f"{entry.name}{label_str} {entry.value}")  # noqa: PLC1901

        # Xuất counter totals
        for (name, label_key), total in sorted(counter_totals.items()):
            label_str = self._key_to_label_str(label_key)
            lines.append(f"{name}{label_str} {total}")

        # Xuất gauge latest
        for (name, label_key), value in sorted(gauge_latest.items()):
            label_str = self._key_to_label_str(label_key)
            lines.append(f"{name}{label_str} {value}")

        return "\n".join(lines) + "\n" if lines else ""

    def retention_check(self, older_than_days: Optional[int] = None) -> int:
        """Xóa entries cũ hơn retention_days. Returns số entries đã xóa.

        Args:
            older_than_days: Số ngày (override retention_days mặc định)

        Returns:
            Số entries đã bị xóa
        """
        if older_than_days is None:
            older_than_days = self._retention_days

        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        remaining: list[MetricEntry] = []
        deleted_count = 0

        for entry in self._entries:
            if entry.timestamp >= cutoff:
                remaining.append(entry)
            else:
                deleted_count += 1

        self._entries = remaining
        return deleted_count

    # -------------------------------------------------------------------------
    # Phương thức nội bộ
    # -------------------------------------------------------------------------

    def _sum_for_key(self, name: str, labels: dict, metric_type: str) -> float:
        """Tính tổng value cho tất cả entries khớp name, labels, metric_type."""
        total = 0.0
        for entry in self._entries:
            if entry.name == name and entry.metric_type == metric_type:
                if self._labels_match(entry.labels, labels):
                    total += entry.value
        return total

    def _labels_match(self, entry_labels: dict, filter_labels: dict) -> bool:
        """Kiểm tra entry_labels có khớp với filter_labels không."""
        for key, value in filter_labels.items():
            if entry_labels.get(key) != value:
                return False
        return True

    def _label_key(self, labels: dict) -> str:
        """Tạo key chuỗi từ labels đã sorted."""
        if not labels:
            return ""
        return json.dumps(labels, sort_keys=True)

    def _key_to_label_str(self, key: str) -> str:
        """Chuyển label key thành chuỗi label cho Prometheus format."""
        if not key:
            return ""
        labels = json.loads(key)
        return self._format_labels(labels)

    def _format_labels(self, labels: dict) -> str:
        """Format labels thành Prometheus label string."""
        if not labels:
            return ""
        parts = []
        for k in sorted(labels.keys()):
            parts.append(f'{k}="{labels[k]}"')
        return "{" + ",".join(parts) + "}"
