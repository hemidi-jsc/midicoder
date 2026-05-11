# coding: utf-8
"""
Mô-đun alert runtime engine (CP16).

Cung cấp:
- AlertEngine: Engine cho alert rules — evaluate từ CP15 MetricRegistry

Obligation: evaluation_interval — alert chỉ fire nếu đủ khoảng thời gian.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from midicoder.emitters.core.monitoring.models import (
    AlertCondition,
    AlertRule,
    FiredAlert,
)


class AlertEngine:
    """Engine cho alert rules — evaluate từ CP15 MetricRegistry.

    Cung cấp:
    - add_rule(rule) → thêm alert rule
    - remove_rule(name) → xóa alert rule
    - evaluate(registry) → đánh giá tất cả rules từ CP15 MetricRegistry
    - fire_alert(rule, current_value) → kích hoạt alert
    - get_fired_alerts() → lấy danh sách alerts đang active
    - clear_alerts() → xóa tất cả alerts

    Obligation: evaluation_interval — alert chỉ fire nếu đủ khoảng thời gian
    """

    def __init__(self) -> None:
        """Khởi tạo AlertEngine."""
        self._rules: dict[str, AlertRule] = {}
        self._fired_alerts: list[FiredAlert] = []
        self._last_evaluations: dict[str, datetime] = {}

    def add_rule(self, rule: AlertRule) -> None:
        """Thêm alert rule.

        Args:
            rule: AlertRule definition
        """
        self._rules[rule.name] = rule
        # Khởi tạo thời điểm evaluate cuối cùng cho rule mới
        self._last_evaluations[rule.name] = datetime.now(timezone.utc)

    def remove_rule(self, name: str) -> bool:
        """Xóa alert rule. Returns True nếu xóa thành công.

        Args:
            name: Tên rule

        Returns:
            True nếu rule tồn tại và đã xóa, False nếu không tìm thấy
        """
        if name in self._rules:
            del self._rules[name]
            # Cũng xóa thời điểm evaluate
            self._last_evaluations.pop(name, None)
            return True
        return False

    def evaluate(self, registry: Any) -> list[FiredAlert]:
        """Đánh giá tất cả rules từ CP15 MetricRegistry.

        Với mỗi rule:
        1. Check đủ evaluation_interval kể từ lần evaluate trước
        2. Lấy giá trị metric từ registry.get(rule.metric_name)
        3. So sánh với condition + threshold
        4. Nếu vượt ngưỡng → fire_alert()

        Args:
            registry: CP15 MetricRegistry instance

        Returns:
            Danh sách FiredAlert mới được kích hoạt trong lần evaluate này
        """
        newly_fired: list[FiredAlert] = []
        now = datetime.now(timezone.utc)

        for rule in self._rules.values():
            # Kiểm tra đủ khoảng thời gian kể từ lần evaluate trước
            last_eval = self._last_evaluations.get(rule.name)
            if last_eval is not None:
                elapsed = (now - last_eval).total_seconds()
                if elapsed < rule.evaluation_interval:
                    # Chưa đủ khoảng thời gian, bỏ qua rule này
                    continue

            # Cập nhật thời điểm evaluate hiện tại
            self._last_evaluations[rule.name] = now

            # Lấy giá trị metric từ CP15 MetricRegistry
            entries = registry.get(rule.metric_name, rule.labels if rule.labels else None)

            if not entries:
                # Không có dữ liệu metric, bỏ qua
                continue

            # Lấy giá trị mới nhất
            current_value = entries[-1].value

            # Kiểm tra condition
            if self._check_condition(current_value, rule.condition, rule.threshold):
                alert = self.fire_alert(rule, current_value)
                newly_fired.append(alert)

        return newly_fired

    def _check_condition(
        self,
        current_value: float,
        condition: AlertCondition,
        threshold: float,
    ) -> bool:
        """Kiểm tra condition: greater_than, less_than, equals, not_equals.

        Args:
            current_value: Giá trị hiện tại của metric
            condition: Điều kiện so sánh
            threshold: Ngưỡng

        Returns:
            True nếu điều kiện được đáp ứng (alert nên fire)
        """
        if condition == AlertCondition.GREATER_THAN:
            return current_value > threshold
        elif condition == AlertCondition.LESS_THAN:
            return current_value < threshold
        elif condition == AlertCondition.EQUALS:
            return current_value == threshold
        elif condition == AlertCondition.NOT_EQUALS:
            return current_value != threshold
        return False

    def fire_alert(self, rule: AlertRule, current_value: float) -> FiredAlert:
        """Kích hoạt alert. Returns FiredAlert.

        Args:
            rule: AlertRule đã được trigger
            current_value: Giá trị hiện tại của metric

        Returns:
            FiredAlert vừa tạo
        """
        alert = FiredAlert(
            rule_name=rule.name,
            metric_name=rule.metric_name,
            current_value=current_value,
            threshold=rule.threshold,
            severity=rule.severity.value,
            fired_at=datetime.now(timezone.utc),
            condition=rule.condition.value,
        )
        self._fired_alerts.append(alert)
        return alert

    def get_fired_alerts(self) -> list[FiredAlert]:
        """Lấy danh sách alerts đang active.

        Returns:
            Danh sách FiredAlert
        """
        return list(self._fired_alerts)

    def clear_alerts(self) -> int:
        """Xóa tất cả alerts. Returns số alerts đã xóa.

        Returns:
            Số alerts đã bị xóa
        """
        count = len(self._fired_alerts)
        self._fired_alerts.clear()
        return count
