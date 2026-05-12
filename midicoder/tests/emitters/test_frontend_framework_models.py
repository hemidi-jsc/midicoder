# coding: utf-8
"""
Tests cho models của Frontend Framework Generator (CP18).

Module: midicoder/emitters/core/component/models.py
Features: FrontendApp, RouteDefinition, StateStoreConfig + enums

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.errors import MidicoderError, ErrorCode


class TestFrontendFramework:
    """Tests cho FrontendFramework enum."""

    def test_frontend_framework_values(self):
        """Test enum values."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendFramework
        assert FrontendFramework.ANGULAR.value == "angular"
        assert FrontendFramework.REACT.value == "react"

    def test_frontend_framework_from_string(self):
        """Test tạo enum từ string."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendFramework
        assert FrontendFramework("angular") == FrontendFramework.ANGULAR
        assert FrontendFramework("react") == FrontendFramework.REACT


class TestStateStoreType:
    """Tests cho StateStoreType enum."""

    def test_state_store_type_values(self):
        """Test enum values."""
        from midicoder.emitters.core.cp18_frontend_framework.models import StateStoreType
        assert StateStoreType.ANGULAR_SIGNALS.value == "angular_signals"
        assert StateStoreType.ZUSTAND.value == "zustand"
        assert StateStoreType.NGXS.value == "ngxs"
        assert StateStoreType.REDUX.value == "redux"


class TestRouterStrategy:
    """Tests cho RouterStrategy enum."""

    def test_router_strategy_values(self):
        """Test enum values."""
        from midicoder.emitters.core.cp18_frontend_framework.models import RouterStrategy
        assert RouterStrategy.EAGER.value == "eager"
        assert RouterStrategy.LAZY.value == "lazy"


class TestAppShellLayout:
    """Tests cho AppShellLayout enum."""

    def test_app_shell_layout_values(self):
        """Test enum values."""
        from midicoder.emitters.core.cp18_frontend_framework.models import AppShellLayout
        assert AppShellLayout.SIDEBAR.value == "sidebar"
        assert AppShellLayout.TOPNAV.value == "topnav"
        assert AppShellLayout.SPLIT.value == "split"


class TestFrontendApp:
    """Tests cho FrontendApp dataclass."""

    def test_frontend_app_creation(self):
        """Test tạo FrontendApp hợp lệ."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendApp, FrontendFramework
        app = FrontendApp(
            name="my-app",
            framework=FrontendFramework.ANGULAR,
            ui_framework="material",
        )
        assert app.name == "my-app"
        assert app.framework == FrontendFramework.ANGULAR
        assert app.ui_framework == "material"

    def test_frontend_app_empty_name_raises(self):
        """Test lỗi khi name rỗng."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendApp
        with pytest.raises(MidicoderError) as exc_info:
            FrontendApp(name="")
        assert exc_info.value.code == ErrorCode.CP18_EMPTY_APP_NAME

    def test_frontend_app_whitespace_name_raises(self):
        """Test lỗi khi name là whitespace."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendApp
        with pytest.raises(MidicoderError) as exc_info:
            FrontendApp(name="   ")
        assert exc_info.value.code == ErrorCode.CP18_EMPTY_APP_NAME

    def test_frontend_app_invalid_ui_framework_raises(self):
        """Test lỗi khi UI framework không hợp lệ."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendApp
        with pytest.raises(MidicoderError) as exc_info:
            FrontendApp(name="test-app", ui_framework="invalid_framework")
        assert exc_info.value.code == ErrorCode.CP18_INVALID_UI_FRAMEWORK

    def test_frontend_app_supported_ui_frameworks(self):
        """Test các UI framework được hỗ trợ."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendApp
        for fw in ["material", "tailwind", "bootstrap", "antd", "carbon"]:
            app = FrontendApp(name="test-app", ui_framework=fw)
            assert app.ui_framework == fw

    def test_frontend_app_default_values(self):
        """Test giá trị mặc định."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendApp, FrontendFramework
        app = FrontendApp(name="test-app")
        assert app.framework == FrontendFramework.REACT
        assert app.ui_framework == "material"
        assert app.routes == []
        assert app.state_store is None

    def test_frontend_app_to_dict(self):
        """Test chuyển sang dict."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendApp, FrontendFramework
        app = FrontendApp(name="my-app", framework=FrontendFramework.ANGULAR)
        d = app.to_dict()
        assert d["name"] == "my-app"
        assert d["framework"] == "angular"
        assert d["ui_framework"] == "material"

    def test_frontend_app_from_dict(self):
        """Test tạo từ dict."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendApp, FrontendFramework
        data = {
            "name": "my-app",
            "framework": "angular",
            "ui_framework": "tailwind",
        }
        app = FrontendApp.from_dict(data)
        assert app.name == "my-app"
        assert app.framework == FrontendFramework.ANGULAR
        assert app.ui_framework == "tailwind"

    def test_frontend_app_with_routes(self):
        """Test FrontendApp có routes."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendApp, RouteDefinition
        route = RouteDefinition(path="/orders", component="OrderList")
        app = FrontendApp(name="test-app", routes=[route])
        assert len(app.routes) == 1
        assert app.routes[0].path == "/orders"


class TestRouteDefinition:
    """Tests cho RouteDefinition dataclass."""

    def test_route_definition_creation(self):
        """Test tạo RouteDefinition hợp lệ."""
        from midicoder.emitters.core.cp18_frontend_framework.models import RouteDefinition
        route = RouteDefinition(
            path="/orders",
            component="OrderList",
        )
        assert route.path == "/orders"
        assert route.component == "OrderList"
        assert route.is_lazy is False
        assert route.children == []

    def test_route_definition_empty_path_raises(self):
        """Test lỗi khi path rỗng."""
        from midicoder.emitters.core.cp18_frontend_framework.models import RouteDefinition
        with pytest.raises(MidicoderError) as exc_info:
            RouteDefinition(path="", component="Test")
        assert exc_info.value.code == ErrorCode.CP18_INVALID_ROUTE_PATH

    def test_route_definition_path_not_starting_with_slash_raises(self):
        """Test lỗi khi path không bắt đầu bằng /."""
        from midicoder.emitters.core.cp18_frontend_framework.models import RouteDefinition
        with pytest.raises(MidicoderError) as exc_info:
            RouteDefinition(path="orders", component="Test")
        assert exc_info.value.code == ErrorCode.CP18_INVALID_ROUTE_PATH

    def test_route_definition_empty_component_raises(self):
        """Test lỗi khi component rỗng."""
        from midicoder.emitters.core.cp18_frontend_framework.models import RouteDefinition
        with pytest.raises(MidicoderError) as exc_info:
            RouteDefinition(path="/test", component="")
        assert exc_info.value.code == ErrorCode.CP18_EMPTY_ROUTE_COMPONENT

    def test_route_definition_with_children(self):
        """Test route có children."""
        from midicoder.emitters.core.cp18_frontend_framework.models import RouteDefinition
        child = RouteDefinition(path="/orders/:id", component="OrderDetail")
        parent = RouteDefinition(
            path="/orders",
            component="OrderList",
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].path == "/orders/:id"

    def test_route_definition_lazy(self):
        """Test route lazy loading."""
        from midicoder.emitters.core.cp18_frontend_framework.models import RouteDefinition
        route = RouteDefinition(
            path="/admin",
            component="AdminPanel",
            is_lazy=True,
        )
        assert route.is_lazy is True

    def test_route_definition_to_dict(self):
        """Test chuyển sang dict."""
        from midicoder.emitters.core.cp18_frontend_framework.models import RouteDefinition
        route = RouteDefinition(
            path="/orders",
            component="OrderList",
            is_lazy=True,
        )
        d = route.to_dict()
        assert d["path"] == "/orders"
        assert d["component"] == "OrderList"
        assert d["is_lazy"] is True

    def test_route_definition_from_dict(self):
        """Test tạo từ dict."""
        from midicoder.emitters.core.cp18_frontend_framework.models import RouteDefinition
        data = {
            "path": "/products",
            "component": "ProductList",
            "is_lazy": True,
        }
        route = RouteDefinition.from_dict(data)
        assert route.path == "/products"
        assert route.component == "ProductList"
        assert route.is_lazy is True

    def test_route_definition_root_path(self):
        """Test root path (/)."""
        from midicoder.emitters.core.cp18_frontend_framework.models import RouteDefinition
        route = RouteDefinition(path="/", component="Home")
        assert route.path == "/"

    def test_route_definition_with_params(self):
        """Test route với path parameters."""
        from midicoder.emitters.core.cp18_frontend_framework.models import RouteDefinition
        route = RouteDefinition(
            path="/orders/:orderId/items/:itemId",
            component="OrderItemDetail",
        )
        assert route.path == "/orders/:orderId/items/:itemId"

    def test_duplicate_routes_detection(self):
        """Test phát hiện route trùng lặp."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendApp, RouteDefinition
        routes = [
            RouteDefinition(path="/orders", component="OrderList"),
            RouteDefinition(path="/orders", component="AnotherComponent"),
        ]
        with pytest.raises(MidicoderError) as exc_info:
            FrontendApp(name="test-app", routes=routes)
        assert exc_info.value.code == ErrorCode.CP18_DUPLICATE_ROUTE


class TestStateStoreConfig:
    """Tests cho StateStoreConfig dataclass."""

    def test_state_store_config_creation(self):
        """Test tạo StateStoreConfig hợp lệ."""
        from midicoder.emitters.core.cp18_frontend_framework.models import StateStoreConfig, StateStoreType
        config = StateStoreConfig(
            store_type=StateStoreType.ANGULAR_SIGNALS,
            entities=["Order", "Product"],
        )
        assert config.store_type == StateStoreType.ANGULAR_SIGNALS
        assert config.entities == ["Order", "Product"]

    def test_state_store_config_empty_entities(self):
        """Test StateStoreConfig không có entities."""
        from midicoder.emitters.core.cp18_frontend_framework.models import StateStoreConfig, StateStoreType
        config = StateStoreConfig(store_type=StateStoreType.ZUSTAND)
        assert config.entities == []

    def test_state_store_config_to_dict(self):
        """Test chuyển sang dict."""
        from midicoder.emitters.core.cp18_frontend_framework.models import StateStoreConfig, StateStoreType
        config = StateStoreConfig(
            store_type=StateStoreType.ZUSTAND,
            entities=["User", "Order"],
        )
        d = config.to_dict()
        assert d["store_type"] == "zustand"
        assert d["entities"] == ["User", "Order"]

    def test_state_store_config_from_dict(self):
        """Test tạo từ dict."""
        from midicoder.emitters.core.cp18_frontend_framework.models import StateStoreConfig, StateStoreType
        data = {
            "store_type": "zustand",
            "entities": ["Product", "Category"],
        }
        config = StateStoreConfig.from_dict(data)
        assert config.store_type == StateStoreType.ZUSTAND
        assert config.entities == ["Product", "Category"]

    def test_state_store_config_with_selectors(self):
        """Test StateStoreConfig có selectors tùy chỉnh."""
        from midicoder.emitters.core.cp18_frontend_framework.models import StateStoreConfig, StateStoreType
        config = StateStoreConfig(
            store_type=StateStoreType.ZUSTAND,
            entities=["Order"],
            selectors=["selectOrders", "selectOrderCount"],
        )
        assert "selectOrders" in config.selectors

    def test_state_store_config_invalid_type_raises(self):
        """Test lỗi khi store_type không hợp lệ."""
        from midicoder.emitters.core.cp18_frontend_framework.models import StateStoreConfig
        with pytest.raises(MidicoderError) as exc_info:
            StateStoreConfig(store_type="invalid_type")
        assert exc_info.value.code == ErrorCode.CP18_INVALID_STATE_STORE


class TestFrontendAppGenerateRoutes:
    """Tests cho generate_routes method."""

    def test_generate_routes_from_entities(self):
        """Test tự động generate routes từ entities."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendApp
        app = FrontendApp(name="test-app")
        entities = [
            {"id": "Order", "fields": [{"name": "total", "type": "float"}]},
            {"id": "Product", "fields": [{"name": "name", "type": "str"}]},
        ]
        routes = app.generate_routes(entities)
        # / (home) + /orders, /orders/:id + /products, /products/:id = 5 routes
        assert len(routes) == 5
        paths = [r.path for r in routes]
        assert "/" in paths
        assert "/orders" in paths
        assert "/orders/:id" in paths
        assert "/products" in paths
        assert "/products/:id" in paths

    def test_generate_routes_includes_routes_detail(self):
        """Test routes bao gồm list và detail."""
        from midicoder.emitters.core.cp18_frontend_framework.models import FrontendApp
        app = FrontendApp(name="test-app")
        entities = [{"id": "Order", "fields": []}]
        routes = app.generate_routes(entities)
        paths = [r.path for r in routes]
        assert "/orders" in paths
        assert "/orders/:id" in paths


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
