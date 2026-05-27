# coding: utf-8
"""
Mô-đun SLI runtime engine (CP16).

Cung cấp:
- SLIMonitor: Monitor cho SLI definitions — đọc từ CP15 MetricRegistry

SLI check logic:
- availability: current >= target → healthy
- latency: current <= target → healthy
- error_rate: current <= target → healthy

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from midicoder.packs.cp16_monitoring.models import (
    SLIDefinition,
    SLIMetricType,
    SLIStatus,
)


class SLIMonitor:
    """Monitor cho SLI definitions — đọc từ CP15 MetricRegistry.

    Cung cấp:
    - register_sli(definition) → đăng ký SLI
    - unregister_sli(name) → hủy đăng ký SLI
    - check_sli(registry) → kiểm tra tất cả SLIs từ CP15
    - get_sli_status(name) → lấy status của 1 SLI
    - get_all_sli_status() → lấy tất cả statuses
    - is_all_healthy() → tất cả SLIs có healthy không

    SLI check logic:
    - availability: current >= target → healthy
    - latency: current <= target → healthy
    - error_rate: current <= target → healthy
    """

    def __init__(self) -> None:
        """Khởi tạo SLIMonitor."""
        self._definitions: dict[str, SLIDefinition] = {}
        self._statuses: dict[str, SLIStatus] = {}

    def register_sli(self, definition: SLIDefinition) -> None:
        """Đăng ký SLI definition.

        Args:
            definition: SLIDefinition để đăng ký
        """
        self._definitions[definition.name] = definition

    def unregister_sli(self, name: str) -> bool:
        """Hủy đăng ký SLI. Returns True nếu thành công.

        Args:
            name: Tên SLI

        Returns:
            True nếu SLI tồn tại và đã hủy, False nếu không tìm thấy
        """
        if name in self._definitions:
            del self._definitions[name]
            self._statuses.pop(name, None)
            return True
        return False

    def check_sli(
        self,
        registry: Any,
        sli_name: str | None = None,
    ) -> dict[str, SLIStatus]:
        """Kiểm tra SLI từ CP15 MetricRegistry.

        Nếu sli_name được cung cấp, chỉ kiểm tra 1 SLI.
        Nếu không, kiểm tra tất cả.

        Args:
            registry: CP15 MetricRegistry instance
            sli_name: Tên SLI cụ thể (tùy chọn)

        Returns:
            Dict mapping SLI name → SLIStatus
        """
        results: dict[str, SLIStatus] = {}
        now = datetime.now(timezone.utc)

        if sli_name:
            # Chỉ kiểm tra 1 SLI cụ thể
            definitions_to_check = {sli_name: self._definitions[sli_name]}
        else:
            # Kiểm tra tất cả SLIs
            definitions_to_check = self._definitions

        for name, definition in definitions_to_check.items():
            # Lấy giá trị metric từ CP15 MetricRegistry
            entries = registry.get(definition.metric_name, definition.labels if definition.labels else None)

            if entries:
                current_value = entries[-1].value
            else:
                # Không có dữ liệu metric, dùng 0
                current_value = 0.0

            # Đánh giá health dựa trên loại metric
            is_healthy = self._evaluate_health(definition, current_value)

            status = SLIStatus(
                sli_name=name,
                metric_type=definition.metric_type.value,
                current_value=current_value,
                target=definition.target,
                is_healthy=is_healthy,
                evaluated_at=now,
            )

            results[name] = status
            self._statuses[name] = status

        return results

    def _evaluate_health(self, definition: SLIDefinition, current_value: float) -> bool:
        """Đánh giá health của SLI dựa trên loại metric.

        Args:
            definition: SLIDefinition
            current_value: Giá trị hiện tại của metric

        Returns:
            True nếu SLI đạt target (healthy)
        """
        if definition.metric_type == SLIMetricType.AVAILABILITY:
            return self._evaluate_availability(definition, current_value)
        elif definition.metric_type == SLIMetricType.LATENCY:
            return self._evaluate_latency(definition, current_value)
        elif definition.metric_type == SLIMetricType.ERROR_RATE:
            return self._evaluate_error_rate(definition, current_value)
        return False

    def _evaluate_availability(self, definition: SLIDefinition, current_value: float) -> bool:
        """Kiểm tra availability SLI: current >= target → healthy.

        Args:
            definition: SLIDefinition
            current_value: Giá trị hiện tại

        Returns:
            True nếu current >= target
        """
        return current_value >= definition.target

    def _evaluate_latency(self, definition: SLIDefinition, current_value: float) -> bool:
        """Kiểm tra latency SLI: current <= target → healthy.

        Args:
            definition: SLIDefinition
            current_value: Giá trị hiện tại

        Returns:
            True nếu current <= target
        """
        return current_value <= definition.target

    def _evaluate_error_rate(self, definition: SLIDefinition, current_value: float) -> bool:
        """Kiểm tra error_rate SLI: current <= target → healthy.

        Args:
            definition: SLIDefinition
            current_value: Giá trị hiện tại

        Returns:
            True nếu current <= target
        """
        return current_value <= definition.target

    def get_sli_status(self, name: str) -> SLIStatus | None:
        """Lấy status của 1 SLI.

        Args:
            name: Tên SLI

        Returns:
            SLIStatus hoặc None nếu không tìm thấy
        """
        return self._statuses.get(name)

    def get_all_sli_status(self) -> dict[str, SLIStatus]:
        """Lấy tất cả statuses.

        Returns:
            Dict mapping SLI name → SLIStatus
        """
        return dict(self._statuses)

    def is_all_healthy(self) -> bool:
        """Tất cả SLIs có healthy không.

        Returns:
            True nếu tất cả SLIs đều healthy, False nếu có SLI nào không healthy.
            Nếu không có SLI nào được đăng ký, trả về True.
        """
        if not self._statuses:
            return True
        return all(status.is_healthy for status in self._statuses.values())
