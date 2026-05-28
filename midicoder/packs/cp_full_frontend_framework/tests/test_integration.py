# coding: utf-8
"""
Integration tests cho Frontend Framework Generator (CP18).

Test toàn bộ pipeline: YAML → Parser → Models → Emitter → Code output.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
import tempfile
from pathlib import Path

from ..parser import FrontendFrameworkParser
from ..angular import AngularComponentEmitter
from ..react import ReactComponentEmitter
from ..fastapi import FastAPIFrontendEmitter
from ..nestjs import NestJSFrontendEmitter


class TestFrontendFrameworkIntegration:
    """Integration tests cho CP18."""

    def test_full_pipeline_angular(self):
        """Test pipeline đầy đủ: YAML → Angular code."""
        yaml_str = """
name: ecommerce-app
framework: angular
ui_framework: material
layout: sidebar
routes:
  - path: /
    component: Dashboard
  - path: /orders
    component: OrderList
  - path: /orders/:id
    component: OrderDetail
"""
        parser = FrontendFrameworkParser()
        result = parser.parse(yaml_str)

        assert result["frontend_app"] is not None
        assert result["frontend_app"].name == "ecommerce-app"
        assert len(result["routes"]) == 3

        # Angular/React emitters take entities as dicts with 'id' and 'fields'
        entities = [
            {"id": "Order", "fields": [{"name": "total", "type": "float"}]},
            {"id": "Product", "fields": [{"name": "name", "type": "str"}]},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            emitter = AngularComponentEmitter()
            emitter.emit(entities, Path(tmpdir))

    def test_full_pipeline_react(self):
        """Test pipeline đầy đủ: YAML → React code."""
        yaml_str = """
name: react-dashboard
framework: react
ui_framework: tailwind
routes:
  - path: /
    component: Home
  - path: /products
    component: ProductList
"""
        parser = FrontendFrameworkParser()
        result = parser.parse(yaml_str)

        entities = [
            {"id": "Product", "fields": [{"name": "sku", "type": "str"}]},
            {"id": "Cart", "fields": [{"name": "items", "type": "list"}]},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            emitter = ReactComponentEmitter()
            emitter.emit(entities, Path(tmpdir))

    def test_full_pipeline_fastapi(self):
        """Test pipeline đầy đủ: YAML → FastAPI config service."""
        yaml_str = """
name: api-config
framework: react
"""
        parser = FrontendFrameworkParser()
        result = parser.parse(yaml_str)

        emitter = FastAPIFrontendEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.generate(result["frontend_app"], Path(tmpdir))
            content = "\n".join(f.content for f in files)
            assert "ConfigService" in content or "BaseModel" in content

    def test_full_pipeline_nestjs(self):
        """Test pipeline đầy đủ: YAML → NestJS config module."""
        yaml_str = """
name: nestjs-config
framework: angular
"""
        parser = FrontendFrameworkParser()
        result = parser.parse(yaml_str)

        emitter = NestJSFrontendEmitter()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = emitter.generate(result["frontend_app"], Path(tmpdir))
            content = "\n".join(f.content for f in files)
            assert "Config" in content

    def test_empty_yaml_to_valid_config(self):
        """E2E: YAML rỗng → valid empty config."""
        parser = FrontendFrameworkParser()
        result = parser.parse("")

        assert result["frontend_app"] is None
        assert result["routes"] == []
        assert result["state_store"] is None

    def test_complex_nested_routes_pipeline(self):
        """Test pipeline với nested routes phức tạp."""
        yaml_str = """
name: admin-panel
framework: angular
routes:
  - path: /admin
    component: AdminLayout
    children:
      - path: /admin/users
        component: UserManagement
      - path: /admin/settings
        component: AdminSettings
        children:
          - path: /admin/settings/general
            component: GeneralSettings
          - path: /admin/settings/security
            component: SecuritySettings
"""
        parser = FrontendFrameworkParser()
        result = parser.parse(yaml_str)

        assert len(result["routes"]) == 1
        admin_route = result["routes"][0]
        assert admin_route.path == "/admin"
        assert len(admin_route.children) == 2
        assert len(admin_route.children[1].children) == 2

    def test_parser_to_dict_roundtrip(self):
        """Test parse → to_dict → reconstruct."""
        yaml_str = """
name: roundtrip-app
framework: react
ui_framework: tailwind
layout: topnav
description: Test app
routes:
  - path: /
    component: Home
"""
        parser = FrontendFrameworkParser()
        result = parser.parse(yaml_str)
        app = result["frontend_app"]

        # Convert to dict
        app_dict = app.to_dict()
        assert app_dict["name"] == "roundtrip-app"
        assert app_dict["framework"] == "react"
        assert len(app_dict["routes"]) == 1

    def test_auto_generate_routes_from_entities(self):
        """Test auto-generate routes từ entities."""
        yaml_str = """
name: auto-routes-app
framework: angular
"""
        parser = FrontendFrameworkParser()
        result = parser.parse(yaml_str)
        app = result["frontend_app"]

        entities = [
            {"id": "Order", "fields": [{"name": "total", "type": "float"}]},
            {"id": "Product", "fields": [{"name": "sku", "type": "str"}]},
            {"id": "Customer", "fields": [{"name": "email", "type": "str"}]},
        ]
        routes = app.generate_routes(entities)
        # / + 3 entities × 2 routes = 7
        assert len(routes) == 7

    def test_multiple_frameworks_emission(self):
        """Test emit cùng config sang nhiều frameworks."""
        yaml_str = """
name: multi-framework-app
framework: react
ui_framework: tailwind
routes:
  - path: /
    component: Home
"""
        parser = FrontendFrameworkParser()
        result = parser.parse(yaml_str)

        # Emit cho React
        entities = [
            {"id": "Product", "fields": [{"name": "sku", "type": "str"}]},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            react_emitter = ReactComponentEmitter()
            react_emitter.emit(entities, Path(tmpdir))

        # Emit cho Angular
        with tempfile.TemporaryDirectory() as tmpdir:
            angular_emitter = AngularComponentEmitter()
            angular_emitter.emit(entities, Path(tmpdir))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
