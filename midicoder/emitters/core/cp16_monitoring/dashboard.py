# coding: utf-8
"""
Mô-đun dashboard runtime engine (CP16).

Cung cấp:
- DashboardManager: Manager cho dashboards — tạo, quản lý, export dashboard definitions

Reads from CP15 MetricRegistry for current metric values.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import json
from typing import Any

from midicoder.emitters.core.cp16_monitoring.models import (
    DashboardProfile,
    DashboardType,
    Panel,
)


class DashboardManager:
    """Manager cho dashboards — tạo, quản lý, export dashboard definitions.

    Cung cấp:
    - create_dashboard(name, panels, dashboard_type) → tạo dashboard mới
    - add_panel(dashboard_id, panel_def) → thêm panel vào dashboard
    - get_dashboard(dashboard_id) → lấy dashboard
    - list_dashboards() → lấy tất cả dashboards
    - export_json() → export tất cả dashboards làm JSON

    Reads from CP15 MetricRegistry for current metric values
    """

    def __init__(self) -> None:
        """Khởi tạo DashboardManager."""
        self._dashboards: dict[str, DashboardProfile] = {}
        self._panel_values: dict[str, dict] = {}

    def create_dashboard(
        self,
        name: str,
        panels: list[Panel] | None = None,
        dashboard_type: DashboardType = DashboardType.SYSTEM,
        refresh_interval_seconds: int = 30,
        description: str = "",
    ) -> DashboardProfile:
        """Tạo dashboard mới.

        Args:
            name: Tên dashboard
            panels: Danh sách panels (tùy chọn)
            dashboard_type: Loại dashboard
            refresh_interval_seconds: Khoảng thời gian refresh (giây)
            description: Mô tả dashboard

        Returns:
            DashboardProfile vừa tạo
        """
        dashboard = DashboardProfile(
            name=name,
            dashboard_type=dashboard_type,
            panels=panels or [],
            refresh_interval_seconds=refresh_interval_seconds,
            description=description,
        )
        self._dashboards[name] = dashboard

        # Khởi tạo panel_values cho mỗi panel trong dashboard
        for panel in dashboard.panels:
            panel_key = f"{name}:{panel.name}"
            self._panel_values[panel_key] = {
                "value": None,
                "metric_name": panel.metric_name,
            }

        return dashboard

    def add_panel(self, dashboard_name: str, panel: Panel) -> None:
        """Thêm panel vào dashboard.

        Args:
            dashboard_name: Tên dashboard
            panel: Panel definition

        Raises:
            KeyError: Nếu dashboard không tồn tại
        """
        if dashboard_name not in self._dashboards:
            raise KeyError(
                f"Dashboard '{dashboard_name}' không tồn tại. "
                f"Tạo dashboard trước khi thêm panel."
            )

        dashboard = self._dashboards[dashboard_name]
        dashboard.panels.append(panel)

        # Khởi tạo panel_value
        panel_key = f"{dashboard_name}:{panel.name}"
        self._panel_values[panel_key] = {
            "value": None,
            "metric_name": panel.metric_name,
        }

    def get_dashboard(self, name: str) -> DashboardProfile | None:
        """Lấy dashboard theo tên.

        Args:
            name: Tên dashboard

        Returns:
            DashboardProfile hoặc None nếu không tìm thấy
        """
        return self._dashboards.get(name)

    def list_dashboards(self) -> list[DashboardProfile]:
        """Lấy tất cả dashboards.

        Returns:
            Danh sách DashboardProfile
        """
        return list(self._dashboards.values())

    def update_panel_values(self, registry: Any) -> None:
        """Cập nhật giá trị panel từ CP15 MetricRegistry.

        Đọc giá trị hiện tại của metric từ registry.get(metric_name) và
        lưu vào panel_values.

        Args:
            registry: CP15 MetricRegistry instance
        """
        for dashboard_name, dashboard in self._dashboards.items():
            for panel in dashboard.panels:
                panel_key = f"{dashboard_name}:{panel.name}"

                # Lấy giá trị từ CP15 MetricRegistry
                entries = registry.get(panel.metric_name, panel.labels if panel.labels else None)

                if entries:
                    # Lấy entry mới nhất
                    latest = entries[-1]
                    self._panel_values[panel_key]["value"] = latest.value
                else:
                    # Nếu không có entry, giữ giá trị None
                    self._panel_values[panel_key]["value"] = None

    def export_json(self) -> str:
        """Export tất cả dashboards làm JSON.

        Returns:
            Chuỗi JSON chứa tất cả dashboards và panel values
        """
        export_data = {
            "dashboards": [],
            "panel_values": self._panel_values,
        }

        for dashboard in self._dashboards.values():
            dashboard_dict = dashboard.to_dict()

            # Thêm panel values vào dashboard
            panel_values = {}
            for panel in dashboard.panels:
                panel_key = f"{dashboard.name}:{panel.name}"
                panel_values[panel.name] = self._panel_values.get(panel_key, {})

            dashboard_dict["panel_values"] = panel_values
            export_data["dashboards"].append(dashboard_dict)

        return json.dumps(export_data, indent=2, default=str)

    def get_panel_values(self, dashboard_name: str) -> dict[str, Any]:
        """Lấy tất cả panel values của một dashboard.

        Args:
            dashboard_name: Tên dashboard

        Returns:
            Dict mapping panel name → panel value info
        """
        values: dict[str, Any] = {}
        dashboard = self._dashboards.get(dashboard_name)
        if dashboard:
            for panel in dashboard.panels:
                panel_key = f"{dashboard_name}:{panel.name}"
                values[panel.name] = self._panel_values.get(panel_key, {})
        return values
