# coding: utf-8
"""
Mô-đun models cho Frontend Framework Generator (CP18).

Định nghĩa các dataclass và enum biểu diễn:
- FrontendApp: Cấu hình app frontend (framework, UI, state store)
- RouteDefinition: Định nghĩa route (path, component, lazy loading)
- StateStoreConfig: Cấu hình state store (Signals, Zustand, NgRx, Redux)
- FrontendFramework: Enum chọn Angular hay React
- StateStoreType: Enum loại state store
- RouterStrategy: Enum chiến lược route (eager/lazy)
- AppShellLayout: Enum layout app shell (sidebar/topnav/split)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class FrontendFramework(str, Enum):
    """Framework frontend để generate."""
    ANGULAR = "angular"    # Angular (v17+, standalone)
    REACT = "react"        # React (functional components + hooks)


class StateStoreType(str, Enum):
    """Loại state store cho frontend app."""
    ANGULAR_SIGNALS = "angular_signals"  # Angular Signals (v17+)
    ZUSTAND = "zustand"                   # Zustand (React, lightweight)
    NGXS = "ngxs"                         # NgRx/NGXS (Angular)
    REDUX = "redux"                       # Redux/RTK (React)


class RouterStrategy(str, Enum):
    """Chiến lược routing."""
    EAGER = "eager"   # Load ngay khi khởi tạo app
    LAZY = "lazy"     # Lazy loading theo route


class AppShellLayout(str, Enum):
    """Loại layout cho app shell."""
    SIDEBAR = "sidebar"  # Sidebar navigation (mặc định)
    TOPNAV = "topnav"    # Top navigation bar
    SPLIT = "split"      # Split pane (sidebar + topnav)


# ===========================================================================
# Danh sách UI framework được hỗ trợ
# ===========================================================================

SUPPORTED_UI_FRAMEWORKS = ["material", "tailwind", "bootstrap", "antd", "carbon"]


# ===========================================================================
# RouteDefinition
# ===========================================================================


@dataclass
class RouteDefinition:
    """Định nghĩa route — cấu hình path, component, lazy loading, children.

    Attributes:
        path: Route path (bắt đầu bằng /, vd: /orders, /orders/:id)
        component: Tên component để render tại route này
        is_lazy: Có lazy load route này không
        children: Danh sách sub-routes (nested routes)
        data: Metadata tùy chỉnh gắn kèm route

    Validation:
        - path không rỗng, phải bắt đầu bằng /
        - component không rỗng
    """
    path: str
    component: str
    is_lazy: bool = False
    children: list = field(default_factory=list)
    data: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate route definition sau khi khởi tạo."""
        # Path không được để trống
        if not self.path or not self.path.strip():
            EM.raise_error(
                ErrorCode.CP18_INVALID_ROUTE_PATH,
                field="path"
            )
        # Path phải bắt đầu bằng /
        if not self.path.startswith("/"):
            EM.raise_error(
                ErrorCode.CP18_INVALID_ROUTE_PATH,
                field="path",
                value=self.path
            )
        # Component không được để trống
        if not self.component or not self.component.strip():
            EM.raise_error(
                ErrorCode.CP18_EMPTY_ROUTE_COMPONENT,
                field="component",
                path=self.path
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RouteDefinition sang dict format."""
        return {
            "path": self.path,
            "component": self.component,
            "is_lazy": self.is_lazy,
            "children": [c.to_dict() for c in self.children],
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RouteDefinition":
        """Tạo RouteDefinition từ dict."""
        raw_children = data.get("children", [])
        children = [cls.from_dict(c) for c in raw_children] if isinstance(raw_children, list) else []
        return cls(
            path=data.get("path", ""),
            component=data.get("component", ""),
            is_lazy=data.get("is_lazy", False),
            children=children,
            data=data.get("data", {}),
        )


# ===========================================================================
# StateStoreConfig
# ===========================================================================


@dataclass
class StateStoreConfig:
    """Cấu hình state store — định nghĩa loại store và entities cần quản lý state.

    Attributes:
        store_type: Loại state store (angular_signals, zustand, ngxs, redux)
        entities: Danh sách entity names cần create state slices
        selectors: Danh sách selector names tùy chỉnh
        actions: Danh sách action names tùy chỉnh

    Validation:
        - store_type phải là giá trị hợp lệ của StateStoreType
    """
    store_type: StateStoreType
    entities: list = field(default_factory=list)
    selectors: list = field(default_factory=list)
    actions: list = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate state store config sau khi khởi tạo."""
        # store_type phải là StateStoreType enum
        if not isinstance(self.store_type, StateStoreType):
            EM.raise_error(
                ErrorCode.CP18_INVALID_STATE_STORE,
                store_type=self.store_type,
                valid_types=[t.value for t in StateStoreType]
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển StateStoreConfig sang dict format."""
        return {
            "store_type": self.store_type.value,
            "entities": self.entities,
            "selectors": self.selectors,
            "actions": self.actions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateStoreConfig":
        """Tạo StateStoreConfig từ dict."""
        store_type_str = data.get("store_type", "zustand")
        return cls(
            store_type=StateStoreType(store_type_str),
            entities=data.get("entities", []),
            selectors=data.get("selectors", []),
            actions=data.get("actions", []),
        )


# ===========================================================================
# FrontendApp
# ===========================================================================


@dataclass
class FrontendApp:
    """Cấu hình frontend app — định nghĩa framework, UI, routes, state store.

    Attributes:
        name: Tên app (bắt buộc, không rỗng)
        framework: Frontend framework (angular, react)
        ui_framework: UI framework (material, tailwind, bootstrap, antd, carbon)
        routes: Danh sách route definitions
        state_store: Config cho state store (tùy chọn)
        layout: Loại layout cho app shell
        description: Mô tả app

    Validation:
        - name không rỗng
        - ui_framework phải thuộc SUPPORTED_UI_FRAMEWORKS
        - routes không được có path trùng lặp

    Obligation: route uniqueness — mỗi route path phải là duy nhất
    """
    name: str
    framework: FrontendFramework = FrontendFramework.REACT
    ui_framework: str = "material"
    routes: list = field(default_factory=list)
    state_store: StateStoreConfig | None = None
    layout: AppShellLayout = AppShellLayout.SIDEBAR
    description: str = ""

    def __post_init__(self) -> None:
        """Validate frontend app sau khi khởi tạo."""
        # Tên app không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP18_EMPTY_APP_NAME,
                field="name"
            )
        # UI framework phải được hỗ trợ
        if self.ui_framework not in SUPPORTED_UI_FRAMEWORKS:
            EM.raise_error(
                ErrorCode.CP18_INVALID_UI_FRAMEWORK,
                ui_framework=self.ui_framework,
                valid_frameworks=SUPPORTED_UI_FRAMEWORKS
            )
        # Kiểm tra route path không trùng lặp
        self._validate_unique_routes()

    def _validate_unique_routes(self) -> None:
        """Kiểm tra route paths là duy nhất."""
        seen_paths: set[str] = set()
        for route in self.routes:
            if isinstance(route, RouteDefinition):
                if route.path in seen_paths:
                    EM.raise_error(
                        ErrorCode.CP18_DUPLICATE_ROUTE,
                        path=route.path
                    )
                seen_paths.add(route.path)
                # Kiểm tra cả children
                for child in route.children:
                    if child.path in seen_paths:
                        EM.raise_error(
                            ErrorCode.CP18_DUPLICATE_ROUTE,
                            path=child.path
                        )
                    seen_paths.add(child.path)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển FrontendApp sang dict format."""
        return {
            "name": self.name,
            "framework": self.framework.value,
            "ui_framework": self.ui_framework,
            "routes": [r.to_dict() for r in self.routes],
            "state_store": self.state_store.to_dict() if self.state_store else None,
            "layout": self.layout.value,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FrontendApp":
        """Tạo FrontendApp từ dict."""
        # Parse routes
        raw_routes = data.get("routes", [])
        routes = [RouteDefinition.from_dict(r) for r in raw_routes] if isinstance(raw_routes, list) else []

        # Parse state store
        raw_store = data.get("state_store")
        state_store = None
        if raw_store and isinstance(raw_store, dict):
            state_store = StateStoreConfig.from_dict(raw_store)

        # Parse framework
        framework_str = data.get("framework", "react")
        framework = FrontendFramework(framework_str)

        # Parse layout
        layout_str = data.get("layout", "sidebar")
        layout = AppShellLayout(layout_str)

        return cls(
            name=data.get("name", ""),
            framework=framework,
            ui_framework=data.get("ui_framework", "material"),
            routes=routes,
            state_store=state_store,
            layout=layout,
            description=data.get("description", ""),
        )

    def generate_routes(self, entities: list[dict[str, Any]]) -> list[RouteDefinition]:
        """Tự động generate routes từ danh sách entities.

        Tạo routes cho CRUD: list, detail cho mỗi entity.
        Ví dụ: entity "Order" → /orders, /orders/:id

        Args:
            entities: Danh sách entities với id và fields

        Returns:
            Danh sách RouteDefinition đã generate
        """
        routes: list[RouteDefinition] = []

        # Route home
        routes.append(RouteDefinition(path="/", component="Dashboard"))

        # Tạo routes cho mỗi entity
        for entity in entities:
            entity_id = entity.get("id", "")
            if not entity_id:
                continue
            entity_lower = entity_id.lower()
            entity_plural = entity_lower + "s"

            # List route
            routes.append(RouteDefinition(
                path=f"/{entity_plural}",
                component=f"{entity_id}List",
            ))

            # Detail route
            routes.append(RouteDefinition(
                path=f"/{entity_plural}/:id",
                component=f"{entity_id}Detail",
            ))

        return routes
