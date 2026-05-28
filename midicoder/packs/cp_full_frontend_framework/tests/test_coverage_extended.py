# coding: utf-8
"""
Extended test coverage cho CP18 — edge cases, private methods, error paths.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
import tempfile
from pathlib import Path

from ..models import (
    FrontendApp,
    FrontendFramework,
    RouteDefinition,
    RouterStrategy,
    StateStoreConfig,
    StateStoreType,
    AppShellLayout,
)
from ..parser import FrontendFrameworkParser, parse_frontend_dsl
from ..angular import AngularComponentEmitter
from ..react import ReactComponentEmitter
from ..fastapi import FastAPIFrontendEmitter
from ..nestjs import NestJSFrontendEmitter
from midicoder.errors import MidicoderError, ErrorCode


class TestRouterStrategyValidation:
    """Test RouterStrategy validation trong FrontendApp.__post_init__."""

    def test_router_strategy_default_is_lazy(self):
        """Default router_strategy là LAZY."""
        app = FrontendApp(name="test")
        assert app.router_strategy == RouterStrategy.LAZY

    def test_router_strategy_eager(self):
        """RouterStrategy EAGER hợp lệ."""
        app = FrontendApp(name="test", router_strategy=RouterStrategy.EAGER)
        assert app.router_strategy == RouterStrategy.EAGER

    def test_router_strategy_invalid_raises(self):
        """RouterStrategy không hợp lệ throw MDC-CP18-010."""
        with pytest.raises(MidicoderError) as exc_info:
            FrontendApp(name="test", router_strategy="invalid_strategy")
        assert exc_info.value.code == ErrorCode.MDC-F04_INVALID_ROUTER_STRATEGY


class TestFrontendAppGenerateRoutes:
    """Test FrontendApp.generate_routes() edge cases."""

    def test_generate_routes_empty_entities(self):
        """Generate routes với danh sách entities rỗng."""
        app = FrontendApp(name="test")
        routes = app.generate_routes([])
        # Chỉ có route home
        assert len(routes) == 1
        assert routes[0].path == "/"
        assert routes[0].component == "Dashboard"

    def test_generate_routes_single_entity(self):
        """Generate routes với 1 entity."""
        app = FrontendApp(name="test")
        routes = app.generate_routes([{"id": "User"}])
        # / + /users + /users/:id = 3
        assert len(routes) == 3
        paths = [r.path for r in routes]
        assert "/" in paths
        assert "/users" in paths
        assert "/users/:id" in paths

    def test_generate_routes_entity_without_id(self):
        """Entity không có id được skip."""
        app = FrontendApp(name="test")
        routes = app.generate_routes([{"name": "no_id_field"}])
        assert len(routes) == 1  # chỉ route home

    def test_generate_routes_multiple_entities(self):
        """Generate routes với nhiều entities."""
        app = FrontendApp(name="test")
        routes = app.generate_routes([
            {"id": "Order"},
            {"id": "Product"},
            {"id": "Customer"},
        ])
        # / + 3×2 = 7
        assert len(routes) == 7


class TestRouterStrategyRoundTrip:
    """Test to_dict/from_dict roundtrip cho router_strategy."""

    def test_to_dict_includes_router_strategy(self):
        """to_dict bao gồm router_strategy."""
        app = FrontendApp(name="test", router_strategy=RouterStrategy.EAGER)
        d = app.to_dict()
        assert d["router_strategy"] == "eager"

    def test_from_dict_roundtrip_router_strategy(self):
        """from_dict → to_dict roundtrip với router_strategy."""
        d = {
            "name": "test-app",
            "framework": "react",
            "router_strategy": "eager",
        }
        app = FrontendApp.from_dict(d)
        assert app.router_strategy == RouterStrategy.EAGER
        assert app.to_dict()["router_strategy"] == "eager"


class TestReactEmitterEdgeCases:
    """Test ReactComponentEmitter edge cases."""

    def test_emit_empty_entities(self):
        """Emit với danh sách entities rỗng."""
        emitter = ReactComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit([], Path(tmpdir))
            # Dashboard + Layout = 2
            assert len(files) >= 2

    def test_emit_routes_empty_list(self):
        """emit_routes với danh sách rỗng."""
        emitter = ReactComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_routes([], Path(tmpdir))
            assert len(files) == 1

    def test_emit_state_store(self):
        """emit_state_store generate file."""
        emitter = ReactComponentEmitter()
        config = StateStoreConfig(
            store_type=StateStoreType.ZUSTAND,
            entities=["Order", "Product"],
            selectors=["selectOrders"],
            actions=["fetchOrders"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_state_store(config, Path(tmpdir))
            assert len(files) == 1

    def test_invalid_ui_framework_raises(self):
        """UI framework không hợp lệ throw ValueError."""
        with pytest.raises(ValueError):
            ReactComponentEmitter(ui_framework="unknown_framework")

    def test_all_supported_frameworks(self):
        """Tất cả 5 UI frameworks khởi tạo được."""
        for fw in ["material", "tailwind", "bootstrap", "antd", "carbon"]:
            emitter = ReactComponentEmitter(ui_framework=fw)
            assert emitter.ui_framework == fw

    def test_template_not_found_fallback(self):
        """Template không tồn tại trả về fallback comment."""
        emitter = ReactComponentEmitter()
        result = emitter._render_template("nonexistent.jinja2", {})
        assert "template not found" in result


class TestAngularEmitterEdgeCases:
    """Test AngularComponentEmitter edge cases."""

    def test_emit_empty_entities(self):
        """Emit với danh sách entities rỗng."""
        emitter = AngularComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit([], Path(tmpdir))
            # Dashboard + Shell = 2
            assert len(files) >= 2

    def test_emit_routes_empty_list(self):
        """emit_routes với danh sách rỗng."""
        emitter = AngularComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_routes([], Path(tmpdir))
            assert len(files) == 1

    def test_emit_state_store(self):
        """emit_state_store generate file."""
        emitter = AngularComponentEmitter()
        config = StateStoreConfig(
            store_type=StateStoreType.ANGULAR_SIGNALS,
            entities=["Order"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_state_store(config, Path(tmpdir))
            assert len(files) == 1

    def test_invalid_ui_framework_raises(self):
        """UI framework không hợp lệ throw ValueError."""
        with pytest.raises(ValueError):
            AngularComponentEmitter(ui_framework="unknown_framework")

    def test_all_supported_frameworks(self):
        """Tất cả 5 UI frameworks khởi tạo được."""
        for fw in ["material", "tailwind", "bootstrap", "antd", "carbon"]:
            emitter = AngularComponentEmitter(ui_framework=fw)
            assert emitter.ui_framework == fw

    def test_template_not_found_fallback(self):
        """Template không tồn tại trả về fallback comment."""
        emitter = AngularComponentEmitter()
        result = emitter._render_template("nonexistent.jinja2", {})
        assert "template not found" in result

    def test_ui_import_tailwind_empty(self):
        """Tailwind không cần UI import."""
        emitter = AngularComponentEmitter(ui_framework="tailwind")
        assert emitter._get_ui_import() == ""


class TestFastAPIEmitter:
    """Test FastAPIFrontendEmitter."""

    def test_generate_with_app(self):
        """Generate với FrontendApp."""
        app = FrontendApp(
            name="test-app",
            framework=FrontendFramework.REACT,
            ui_framework="material",
            layout=AppShellLayout.SIDEBAR,
        )
        emitter = FastAPIFrontendEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.generate(app, Path(tmpdir))
            assert len(files) == 2

    def test_generate_template_not_found_fallback(self):
        """Template không tồn tại fallback."""
        emitter = FastAPIFrontendEmitter()
        result = emitter._render("nonexistent.jinja2", {})
        assert "template not found" in result


class TestNestJSEmitter:
    """Test NestJSFrontendEmitter."""

    def test_generate_with_app(self):
        """Generate với FrontendApp."""
        app = FrontendApp(
            name="test-app",
            framework=FrontendFramework.ANGULAR,
            ui_framework="tailwind",
            layout=AppShellLayout.TOPNAV,
        )
        emitter = NestJSFrontendEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.generate(app, Path(tmpdir))
            assert len(files) == 3

    def test_generate_template_not_found_fallback(self):
        """Template không tồn tại fallback."""
        emitter = NestJSFrontendEmitter()
        result = emitter._render("nonexistent.jinja2", {})
        assert "template not found" in result


class TestParseFrontendDslConvenience:
    """Test module-level convenience function parse_frontend_dsl."""

    def test_convenience_function(self):
        """parse_frontend_dsl trả về kết quả đúng."""
        result = parse_frontend_dsl("name: test-app\nframework: react")
        assert result["frontend_app"] is not None
        assert result["frontend_app"].name == "test-app"

    def test_convenience_empty_input(self):
        """parse_frontend_dsl với input rỗng."""
        result = parse_frontend_dsl("")
        assert result["frontend_app"] is None
        assert result["routes"] == []


class TestEnumValidation:
    """Test tất cả enum values và validation."""

    def test_state_store_type_values(self):
        """StateStoreType có đủ 4 values."""
        assert StateStoreType.ANGULAR_SIGNALS.value == "angular_signals"
        assert StateStoreType.ZUSTAND.value == "zustand"
        assert StateStoreType.NGXS.value == "ngxs"
        assert StateStoreType.REDUX.value == "redux"

    def test_app_shell_layout_values(self):
        """AppShellLayout có đủ 3 values."""
        assert AppShellLayout.SIDEBAR.value == "sidebar"
        assert AppShellLayout.TOPNAV.value == "topnav"
        assert AppShellLayout.SPLIT.value == "split"

    def test_frontend_framework_values(self):
        """FrontendFramework có đủ 2 values."""
        assert FrontendFramework.ANGULAR.value == "angular"
        assert FrontendFramework.REACT.value == "react"

    def test_router_strategy_values(self):
        """RouterStrategy có đủ 2 values."""
        assert RouterStrategy.EAGER.value == "eager"
        assert RouterStrategy.LAZY.value == "lazy"


class TestStateStoreConfigRoundTrip:
    """Test StateStoreConfig to_dict/from_dict."""

    def test_roundtrip(self):
        """to_dict → from_dict roundtrip."""
        config = StateStoreConfig(
            store_type=StateStoreType.REDUX,
            entities=["User", "Order"],
            selectors=["selectUsers"],
            actions=["fetchUsers"],
        )
        d = config.to_dict()
        restored = StateStoreConfig.from_dict(d)
        assert restored.store_type == StateStoreType.REDUX
        assert restored.entities == ["User", "Order"]
        assert restored.selectors == ["selectUsers"]
        assert restored.actions == ["fetchUsers"]


class TestRouteDefinitionRoundTrip:
    """Test RouteDefinition to_dict/from_dict."""

    def test_roundtrip_with_children(self):
        """to_dict → from_dict roundtrip với nested children."""
        route = RouteDefinition(
            path="/admin",
            component="AdminLayout",
            children=[
                RouteDefinition(path="/admin/users", component="UserList"),
            ],
        )
        d = route.to_dict()
        restored = RouteDefinition.from_dict(d)
        assert restored.path == "/admin"
        assert len(restored.children) == 1
        assert restored.children[0].path == "/admin/users"

    def test_roundtrip_empty_children(self):
        """Roundtrip với children rỗng."""
        route = RouteDefinition(path="/test", component="Test")
        d = route.to_dict()
        restored = RouteDefinition.from_dict(d)
        assert restored.children == []


class TestReactRouteBuilder:
    """Test _build_routes_jsx và _route_to_jsx trong React emitter."""

    def test_build_routes_jsx_single_route(self):
        """Build routes với 1 route."""
        emitter = ReactComponentEmitter()
        routes = [RouteDefinition(path="/home", component="Home")]
        lines = emitter._build_routes_jsx(routes, Path("."))
        content = "\n".join(lines)
        assert "createBrowserRouter" in content
        assert "home" in content.lower()

    def test_build_routes_jsx_with_children(self):
        """Build routes với nested children."""
        emitter = ReactComponentEmitter()
        routes = [
            RouteDefinition(
                path="/admin",
                component="Admin",
                children=[
                    RouteDefinition(path="/admin/users", component="Users"),
                ],
            )
        ]
        lines = emitter._build_routes_jsx(routes, Path("."))
        content = "\n".join(lines)
        assert "admin" in content.lower()
        assert "Users" in content


class TestAngularRouteBuilder:
    """Test _build_routes_ts và _route_to_ts trong Angular emitter."""

    def test_build_routes_ts_single_route(self):
        """Build routes với 1 route."""
        emitter = AngularComponentEmitter()
        routes = [RouteDefinition(path="/home", component="Home")]
        lines = emitter._build_routes_ts(routes, Path("."))
        content = "\n".join(lines)
        assert "Routes" in content
        assert "home" in content.lower()

    def test_build_routes_ts_with_children(self):
        """Build routes với nested children."""
        emitter = AngularComponentEmitter()
        routes = [
            RouteDefinition(
                path="/admin",
                component="Admin",
                children=[
                    RouteDefinition(path="/admin/settings", component="Settings"),
                ],
            )
        ]
        lines = emitter._build_routes_ts(routes, Path("."))
        content = "\n".join(lines)
        assert "admin" in content.lower()
        assert "settings" in content.lower()


class TestReactZustandStoreBuilder:
    """Test _build_zustand_store trong React emitter."""

    def test_build_zustand_store(self):
        """Build Zustand store với entities."""
        emitter = ReactComponentEmitter()
        config = StateStoreConfig(
            store_type=StateStoreType.ZUSTAND,
            entities=["Order", "Product"],
        )
        lines = emitter._build_zustand_store(config, Path("."))
        content = "\n".join(lines)
        assert 'from "zustand"' in content
        assert "orders" in content
        assert "products" in content
        assert "setOrders" in content or "orders" in content
        assert "addOrder" in content


class TestAngularSignalsStoreBuilder:
    """Test _build_signals_store trong Angular emitter."""

    def test_build_signals_store(self):
        """Build Signals store với entities."""
        emitter = AngularComponentEmitter()
        config = StateStoreConfig(
            store_type=StateStoreType.ANGULAR_SIGNALS,
            entities=["Customer"],
        )
        lines = emitter._build_signals_store(config, Path("."))
        content = "\n".join(lines)
        assert 'from "@angular/core"' in content
        assert "customersState" in content
        assert "customers" in content
