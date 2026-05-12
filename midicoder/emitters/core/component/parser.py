# coding: utf-8
"""
Mô-đun parser cho CP18: Frontend Framework Generator.

Parse YAML DSL thành dict chứa các model objects:
- name, framework, ui_framework, layout, description → FrontendApp
- routes[] → list[RouteDefinition]
- state_store → StateStoreConfig

Sử dụng:
    parser = FrontendFrameworkParser()
    result = parser.parse(yaml_string)
    # result: dict với keys "frontend_app", "routes", "state_store"

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.emitters.core.component.models import (
    AppShellLayout,
    FrontendApp,
    FrontendFramework,
    RouteDefinition,
    StateStoreConfig,
    StateStoreType,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class FrontendFrameworkParser:
    """
    Parser cho frontend framework DSL (app config, routes, state store).

    Phân tích chuỗi YAML thành các đối tượng model:
    - name, framework, ui_framework, layout → FrontendApp
    - routes[] → list[RouteDefinition]
    - state_store → StateStoreConfig

    Usage:
        parser = FrontendFrameworkParser()
        result = parser.parse(yaml_string)
        # result: dict với các khóa "frontend_app", "routes", "state_store"
    """

    def parse(self, raw: str) -> dict:
        """
        Parse YAML DSL string thành frontend config.

        Args:
            raw: Chuỗi YAML đầu vào

        Returns:
            Dict với các khóa: "frontend_app", "routes", "state_store"

        Raises:
            MidicoderError: Nếu YAML không hợp lệ (MDC-CP18-009)
        """
        # Trường hợp rỗng hoặc whitespace-only
        if not raw or not raw.strip():
            return {
                "frontend_app": None,
                "routes": [],
                "state_store": None,
            }

        # Phân tích YAML
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.CP18_FRONTEND_PARSE_ERROR,
                message=f"Lỗi parse YAML frontend config: {e}",
                error=str(e),
            )

        # YAML comment-only hoặc null → treat as empty
        if data is None:
            return {
                "frontend_app": None,
                "routes": [],
                "state_store": None,
            }

        # YAML phải là dict/mapping
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP18_FRONTEND_PARSE_ERROR,
                message="DSL frontend phải là YAML mapping",
            )

        result: dict[str, Any] = {
            "frontend_app": None,
            "routes": [],
            "state_store": None,
        }

        # Phân tích routes
        raw_routes = data.get("routes", [])
        if isinstance(raw_routes, list):
            for route_data in raw_routes:
                route = self._parse_route(route_data)
                result["routes"].append(route)

        # Phân tích state_store
        raw_store = data.get("state_store")
        if raw_store and isinstance(raw_store, dict):
            result["state_store"] = self._parse_state_store(raw_store)

        # Tạo FrontendApp
        if "name" in data:
            app = self._parse_frontend_app(data, result["routes"], result["state_store"])
            result["frontend_app"] = app

        return result

    def _parse_frontend_app(
        self,
        data: dict[str, Any],
        routes: list[RouteDefinition],
        state_store: StateStoreConfig | None,
    ) -> FrontendApp:
        """
        Parse dict thành FrontendApp.

        Args:
            data: Dict chứa thông tin frontend app
            routes: Danh sách routes đã parse
            state_store: Config state store đã parse

        Returns:
            Thể hiện FrontendApp

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        # Parse framework
        framework_str = data.get("framework", "react")
        try:
            framework = FrontendFramework(framework_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP18_INVALID_FRAMEWORK,
                framework=framework_str,
                valid_frameworks=[f.value for f in FrontendFramework],
            )

        # Parse layout
        layout_str = data.get("layout", "sidebar")
        try:
            layout = AppShellLayout(layout_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP18_INVALID_LAYOUT,
                layout=layout_str,
                valid_layouts=[l.value for l in AppShellLayout],
            )

        return FrontendApp(
            name=data.get("name", ""),
            framework=framework,
            ui_framework=data.get("ui_framework", "material"),
            routes=routes,
            state_store=state_store,
            layout=layout,
            description=data.get("description", ""),
        )

    def _parse_route(self, data: dict[str, Any]) -> RouteDefinition:
        """
        Parse dict thành RouteDefinition.

        Args:
            data: Dict chứa thông tin route

        Returns:
            Thể hiện RouteDefinition

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP18_FRONTEND_PARSE_ERROR,
                message="Route entry phải là YAML mapping",
            )

        # Parse children
        raw_children = data.get("children", [])
        children: list[RouteDefinition] = []
        if isinstance(raw_children, list):
            for child_data in raw_children:
                children.append(self._parse_route(child_data))

        return RouteDefinition(
            path=data.get("path", ""),
            component=data.get("component", ""),
            is_lazy=data.get("is_lazy", False),
            children=children,
            data=data.get("data", {}),
        )

    def _parse_state_store(self, data: dict[str, Any]) -> StateStoreConfig:
        """
        Parse dict thành StateStoreConfig.

        Args:
            data: Dict chứa thông tin state store

        Returns:
            Thể hiện StateStoreConfig

        Raises:
            MidicoderError: Nếu store_type không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP18_FRONTEND_PARSE_ERROR,
                message="State store entry phải là YAML mapping",
            )

        # Parse store_type
        store_type_str = data.get("store_type", "zustand")
        try:
            store_type = StateStoreType(store_type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP18_INVALID_STATE_STORE,
                store_type=store_type_str,
                valid_types=[t.value for t in StateStoreType],
            )

        return StateStoreConfig(
            store_type=store_type,
            entities=data.get("entities", []),
            selectors=data.get("selectors", []),
            actions=data.get("actions", []),
        )


def parse_frontend_dsl(raw: str) -> dict:
    """
    Module-level convenience function để parse frontend DSL.

    Args:
        raw: Chuỗi YAML đầu vào

    Returns:
        Dict với các khóa: "frontend_app", "routes", "state_store"
    """
    parser = FrontendFrameworkParser()
    return parser.parse(raw)
