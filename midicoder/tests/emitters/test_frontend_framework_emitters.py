# coding: utf-8
"""
Tests cho 4 emitters của Frontend Framework Generator (CP18).

Module: midicoder/emitters/core/component/{angular,react,fastapi,nestjs}.py
Features: emit_routes(), emit_state_store(), generate()

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
import tempfile
from pathlib import Path

from midicoder.emitters.core.cp18_frontend_framework.angular import AngularComponentEmitter
from midicoder.emitters.core.cp18_frontend_framework.react import ReactComponentEmitter
from midicoder.emitters.core.cp18_frontend_framework.fastapi import FastAPIFrontendEmitter
from midicoder.emitters.core.cp18_frontend_framework.nestjs import NestJSFrontendEmitter
from midicoder.emitters.core.cp18_frontend_framework.models import (
    FrontendApp,
    FrontendFramework,
    RouteDefinition,
    StateStoreConfig,
    StateStoreType,
)


class TestAngularEmitter:
    """Tests cho AngularComponentEmitter emit_routes + emit_state_store."""

    def test_emit_routes_basic(self):
        """Test emit routes cơ bản."""
        routes = [
            RouteDefinition(path="/", component="Home"),
            RouteDefinition(path="/orders", component="OrderList"),
            RouteDefinition(path="/orders/:id", component="OrderDetail"),
        ]
        emitter = AngularComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_routes(routes, Path(tmpdir))
            assert len(files) == 1
            assert "Routes" in files[0].content
            assert "orders" in files[0].content

    def test_emit_routes_with_children(self):
        """Test emit routes với nested children."""
        routes = [
            RouteDefinition(
                path="/admin",
                component="AdminLayout",
                children=[
                    RouteDefinition(path="/admin/users", component="UserManagement"),
                    RouteDefinition(path="/admin/settings", component="Settings"),
                ],
            ),
        ]
        emitter = AngularComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_routes(routes, Path(tmpdir))
            content = files[0].content
            assert "children:" in content
            assert "users" in content

    def test_emit_state_store_angular_signals(self):
        """Test emit state store Angular Signals."""
        store = StateStoreConfig(
            store_type=StateStoreType.ANGULAR_SIGNALS,
            entities=["Order", "Product"],
            selectors=["selectOrders"],
            actions=["loadOrders"],
        )
        emitter = AngularComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_state_store(store, Path(tmpdir))
            content = files[0].content
            assert "signal" in content
            assert "ordersState" in content
            assert "addOrder" in content
            assert "selectOrders" in content

    def test_emit_state_store_empty(self):
        """Test emit state store rỗng."""
        store = StateStoreConfig(
            store_type=StateStoreType.ANGULAR_SIGNALS,
            entities=[],
        )
        emitter = AngularComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_state_store(store, Path(tmpdir))
            assert len(files) == 1


class TestReactEmitter:
    """Tests cho ReactComponentEmitter emit_routes + emit_state_store."""

    def test_emit_routes_basic(self):
        """Test emit routes cơ bản."""
        routes = [
            RouteDefinition(path="/", component="Home"),
            RouteDefinition(path="/products", component="ProductList"),
        ]
        emitter = ReactComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_routes(routes, Path(tmpdir))
            assert len(files) == 1
            content = files[0].content
            assert "createBrowserRouter" in content
            assert "products" in content

    def test_emit_routes_with_children(self):
        """Test emit routes với nested children."""
        routes = [
            RouteDefinition(
                path="/dashboard",
                component="Dashboard",
                children=[
                    RouteDefinition(path="/dashboard/stats", component="Stats"),
                ],
            ),
        ]
        emitter = ReactComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_routes(routes, Path(tmpdir))
            content = files[0].content
            assert "children:" in content
            assert "stats" in content

    def test_emit_state_store_zustand(self):
        """Test emit state store Zustand."""
        store = StateStoreConfig(
            store_type=StateStoreType.ZUSTAND,
            entities=["Order", "Product"],
            selectors=["selectOrders"],
            actions=["loadOrders"],
        )
        emitter = ReactComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_state_store(store, Path(tmpdir))
            content = files[0].content
            assert "zustand" in content
            assert "useStore" in content
            assert "orders" in content
            assert "addOrder" in content
            assert "selectOrders" in content

    def test_emit_state_store_redux(self):
        """Test emit state store Redux."""
        store = StateStoreConfig(
            store_type=StateStoreType.REDUX,
            entities=["User"],
        )
        emitter = ReactComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_state_store(store, Path(tmpdir))
            assert len(files) == 1


class TestFastAPIEmitter:
    """Tests cho FastAPIFrontendEmitter generate()."""

    def test_generate_creates_files(self):
        """Test generate tạo ra 2 files."""
        app = FrontendApp(name="test-app", framework=FrontendFramework.REACT)
        emitter = FastAPIFrontendEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.generate(app, Path(tmpdir))
            assert len(files) == 2
            filenames = [str(f.path) for f in files]
            assert "frontend_config_service.py" in filenames
            assert "frontend_router.py" in filenames

    def test_generate_config_service_content(self):
        """Test content của config service."""
        app = FrontendApp(
            name="my-ecommerce",
            framework=FrontendFramework.ANGULAR,
            ui_framework="material",
        )
        emitter = FastAPIFrontendEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.generate(app, Path(tmpdir))
            config_file = [f for f in files if "config_service" in str(f.path)][0]
            content = config_file.content
            assert "my-ecommerce" in content
            assert "Pydantic" in content or "BaseModel" in content
            assert "ConfigService" in content

    def test_generate_router_content(self):
        """Test content của router."""
        app = FrontendApp(name="test-app")
        emitter = FastAPIFrontendEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.generate(app, Path(tmpdir))
            router_file = [f for f in files if "router" in str(f.path)][0]
            content = router_file.content
            assert "APIRouter" in content
            assert "/config" in content
            assert "/routes" in content
            assert "spa_fallback" in content

    def test_generate_all_frameworks(self):
        """Test generate với tất cả framework."""
        for fw in FrontendFramework:
            app = FrontendApp(name="test-app", framework=fw)
            emitter = FastAPIFrontendEmitter()
            with tempfile.TemporaryDirectory() as tmpdir:
                files = emitter.generate(app, Path(tmpdir))
                assert len(files) == 2


class TestNestJSEmitter:
    """Tests cho NestJSFrontendEmitter generate()."""

    def test_generate_creates_files(self):
        """Test generate tạo ra 3 files."""
        app = FrontendApp(name="test-app", framework=FrontendFramework.ANGULAR)
        emitter = NestJSFrontendEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.generate(app, Path(tmpdir))
            assert len(files) == 3
            filenames = [str(f.path) for f in files]
            assert "frontend-config.module.ts" in filenames
            assert "frontend-config.service.ts" in filenames
            assert "frontend-config.controller.ts" in filenames

    def test_generate_module_content(self):
        """Test content của module."""
        app = FrontendApp(name="my-app")
        emitter = NestJSFrontendEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.generate(app, Path(tmpdir))
            module_file = [f for f in files if "module" in str(f.path)][0]
            content = module_file.content
            assert "@Module" in content
            assert "FrontendConfigModule" in content
            assert "FrontendConfigService" in content

    def test_generate_service_content(self):
        """Test content của service."""
        app = FrontendApp(
            name="test-app",
            framework=FrontendFramework.ANGULAR,
            ui_framework="material",
        )
        emitter = NestJSFrontendEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.generate(app, Path(tmpdir))
            service_file = [f for f in files if "service" in str(f.path)][0]
            content = service_file.content
            assert "@Injectable" in content
            assert "test-app" in content
            assert "getAppConfig" in content

    def test_generate_controller_content(self):
        """Test content của controller."""
        app = FrontendApp(name="test-app")
        emitter = NestJSFrontendEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.generate(app, Path(tmpdir))
            controller_file = [f for f in files if "controller" in str(f.path)][0]
            content = controller_file.content
            assert "@Controller" in content
            assert 'api/frontend' in content
            assert '"config"' in content
            assert '"routes"' in content
            assert '"state-store"' in content

    def test_generate_all_frameworks(self):
        """Test generate với tất cả framework."""
        for fw in FrontendFramework:
            app = FrontendApp(name="test-app", framework=fw)
            emitter = NestJSFrontendEmitter()
            with tempfile.TemporaryDirectory() as tmpdir:
                files = emitter.generate(app, Path(tmpdir))
                assert len(files) == 3


class TestEmitterCollaboration:
    """Tests cho emitter collaboration."""

    def test_angular_emit_routes_from_parser(self):
        """Test Angular emit_routes từ parser result."""
        from midicoder.emitters.core.cp18_frontend_framework.parser import FrontendFrameworkParser

        yaml_str = """
name: test-app
framework: angular
routes:
  - path: /
    component: Home
  - path: /orders
    component: OrderList
"""
        parser = FrontendFrameworkParser()
        result = parser.parse(yaml_str)

        emitter = AngularComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_routes(result["routes"], Path(tmpdir))
            assert len(files) == 1
            # Component names are lowercased in import paths
            assert "home" in files[0].content

    def test_react_emit_state_store_from_parser(self):
        """Test React emit_state_store từ parser result."""
        from midicoder.emitters.core.cp18_frontend_framework.parser import FrontendFrameworkParser

        yaml_str = """
name: test-app
framework: react
state_store:
  store_type: zustand
  entities:
    - Order
    - Product
  selectors:
    - selectOrders
"""
        parser = FrontendFrameworkParser()
        result = parser.parse(yaml_str)

        assert result["state_store"] is not None
        emitter = ReactComponentEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.emit_state_store(result["state_store"], Path(tmpdir))
            assert len(files) == 1
            assert "useStore" in files[0].content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
