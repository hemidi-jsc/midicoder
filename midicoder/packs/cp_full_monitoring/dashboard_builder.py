# coding: utf-8
"""
Mô-đun dashboard builder runtime engine (CP17 — merged into cp_full_monitoring).

Cung cấp:
- Widget: Widget trong dashboard
- DashboardBuilder: Builder cho BI dashboards — tạo, quản lý, export, refresh

Đọc dữ liệu metric từ CP15 MetricRegistry.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from midicoder.packs.cp_full_monitoring.models import DashboardDefinition
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Widget
# ===========================================================================


@dataclass
class Widget:
    """Widget trong dashboard.

    Attributes:
        name: Tên widget
        visualization_type: Loại visualization (line/bar/pie/table/gauge)
        metric_name: Metric name từ CP15 MetricRegistry
        title: Tiêu đề hiển thị
        data: Dữ liệu hiện tại
    """
    name: str
    visualization_type: str
    metric_name: str
    title: str = ""
    data: list = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển Widget sang dict format."""
        return {
            "name": self.name,
            "visualization_type": self.visualization_type,
            "metric_name": self.metric_name,
            "title": self.title,
            "data": self.data,
        }


# ===========================================================================
# DashboardBuilder
# ===========================================================================


class DashboardBuilder:
    """Builder cho BI dashboards.

    Cung cấp:
    - create_dashboard(definition) → tạo dashboard
    - add_widget(dashboard_id, widget_def) → thêm widget
    - get_dashboard(dashboard_id) → lấy dashboard
    - list_dashboards() → lấy tất cả dashboards
    - export_dashboard(dashboard_id) → export JSON
    - refresh_dashboard(dashboard_id, registry) → refresh data từ CP15

    Đọc dữ liệu metric từ CP15 MetricRegistry
    """

    def __init__(self) -> None:
        """Khởi tạo DashboardBuilder."""
        self._dashboards: dict[str, DashboardDefinition] = {}
        self._widgets: dict[str, list[Widget]] = {}
        self._refresh_times: dict[str, datetime] = {}

    def create_dashboard(self, definition: DashboardDefinition) -> DashboardDefinition:
        """Tạo BI dashboard.

        Args:
            definition: DashboardDefinition cần tạo

        Returns:
            DashboardDefinition vừa tạo
        """
        self._dashboards[definition.name] = definition
        self._widgets[definition.name] = []
        self._refresh_times[definition.name] = datetime.now(timezone.utc)
        return definition

    def add_widget(self, dashboard_name: str, widget_def: dict) -> Widget:
        """Thêm widget vào dashboard.

        Args:
            dashboard_name: Tên dashboard
            widget_def: Dictionary định nghĩa widget với keys:
                name, visualization_type, metric_name, title (tùy chọn), data (tùy chọn)

        Returns:
            Widget vừa thêm

        Raises:
            KeyError: Nếu dashboard không tồn tại
        """
        if dashboard_name not in self._dashboards:
            raise KeyError(
                f"Dashboard '{dashboard_name}' không tồn tại. "
                f"Tạo dashboard trước khi thêm widget."
            )

        widget = Widget(
            name=widget_def["name"],
            visualization_type=widget_def["visualization_type"],
            metric_name=widget_def["metric_name"],
            title=widget_def.get("title", ""),
            data=widget_def.get("data", []),
        )

        self._widgets[dashboard_name].append(widget)
        return widget

    def get_dashboard(self, name: str) -> DashboardDefinition | None:
        """Lấy dashboard theo tên.

        Args:
            name: Tên dashboard

        Returns:
            DashboardDefinition hoặc None nếu không tìm thấy
        """
        return self._dashboards.get(name)

    def list_dashboards(self) -> list[DashboardDefinition]:
        """Lấy tất cả dashboards.

        Returns:
            Danh sách DashboardDefinition
        """
        return list(self._dashboards.values())

    def export_dashboard(self, name: str) -> str:
        """Export dashboard làm JSON.

        Xuất dashboard cùng với danh sách widgets.

        Args:
            name: Tên dashboard

        Returns:
            Chuỗi JSON chứa dashboard và widgets

        Raises:
            KeyError: Nếu dashboard không tồn tại
        """
        if name not in self._dashboards:
            raise KeyError(
                f"Dashboard '{name}' không tồn tại. "
                f"Không thể export."
            )

        dashboard = self._dashboards[name]
        widgets = self._widgets.get(name, [])

        export_data = {
            "dashboard": dashboard.to_dict(),
            "widgets": [w.to_dict() for w in widgets],
            "last_refresh": self._refresh_times.get(name).isoformat()
            if name in self._refresh_times else None,
        }

        return json.dumps(export_data, indent=2, default=str)

    def refresh_dashboard(self, name: str, registry: Any) -> None:
        """Refresh data từ CP15 MetricRegistry.

        Đọc giá trị hiện tại của metric từ registry.get(metric_name) cho
        từng widget trong dashboard.

        Args:
            name: Tên dashboard
            registry: CP15 MetricRegistry instance

        Raises:
            KeyError: Nếu dashboard không tồn tại
        """
        if name not in self._dashboards:
            raise KeyError(
                f"Dashboard '{name}' không tồn tại. "
                f"Không thể refresh."
            )

        widgets = self._widgets.get(name, [])

        for widget in widgets:
            # Lấy giá trị từ CP15 MetricRegistry
            entries = registry.get(widget.metric_name, None)

            if entries:
                # Chuyển entries thành data list — lấy giá trị từ mỗi entry
                widget.data = [
                    {
                        "value": entry.value,
                        "timestamp": entry.timestamp.isoformat()
                        if hasattr(entry, "timestamp") else None,
                    }
                    for entry in entries
                ]
            else:
                # Nếu không có entry, đặt data rỗng
                widget.data = []

        # Cập nhật thời gian refresh
        self._refresh_times[name] = datetime.now(timezone.utc)

    def get_widgets(self, dashboard_name: str) -> list[Widget]:
        """Lấy danh sách widgets của một dashboard.

        Args:
            dashboard_name: Tên dashboard

        Returns:
            Danh sách Widget. Trả về danh sách rỗng nếu dashboard không tồn tại.
        """
        return self._widgets.get(dashboard_name, [])
