# coding: utf-8
"""
Tests cho parser của Frontend Framework Generator (CP18).

Module: midicoder/emitters/core/component/parser.py
Features: FrontendFrameworkParser.parse(raw) -> dict

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.errors import MidicoderError, ErrorCode


class TestFrontendFrameworkParser:
    """Tests cho FrontendFrameworkParser."""

    def test_parser_basic(self):
        """Test parse YAML cơ bản."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        yaml_str = """
name: my-app
framework: angular
ui_framework: material
"""
        result = parser.parse(yaml_str)
        assert "frontend_app" in result
        app = result["frontend_app"]
        assert app.name == "my-app"

    def test_parser_empty_input(self):
        """Test parse input rỗng trả về empty dict."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        result = parser.parse("")
        assert result == {"frontend_app": None, "routes": [], "state_store": None}

    def test_parser_whitespace_only(self):
        """Test parse whitespace-only trả về empty dict."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        result = parser.parse("   \n  ")
        assert result == {"frontend_app": None, "routes": [], "state_store": None}

    def test_parser_invalid_yaml_raises(self):
        """Test parse YAML không hợp lệ throw lỗi."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        yaml_str = """
name: my-app
  invalid_indent: true
    worse_indent: [
"""
        with pytest.raises(MidicoderError) as exc_info:
            parser.parse(yaml_str)
        assert exc_info.value.code == ErrorCode.CP18_FRONTEND_PARSE_ERROR

    def test_parser_with_routes(self):
        """Test parse có routes."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        yaml_str = """
name: my-app
framework: react
routes:
  - path: /orders
    component: OrderList
  - path: /products
    component: ProductList
    is_lazy: true
"""
        result = parser.parse(yaml_str)
        routes = result["routes"]
        assert len(routes) == 2
        assert routes[0].path == "/orders"
        assert routes[1].is_lazy is True

    def test_parser_with_nested_routes(self):
        """Test parse có nested routes (children)."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        yaml_str = """
name: my-app
routes:
  - path: /admin
    component: AdminLayout
    children:
      - path: /admin/users
        component: UserManagement
      - path: /admin/settings
        component: Settings
"""
        result = parser.parse(yaml_str)
        routes = result["routes"]
        assert len(routes) == 1
        assert len(routes[0].children) == 2
        assert routes[0].children[0].path == "/admin/users"

    def test_parser_with_state_store(self):
        """Test parse có state_store config."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        yaml_str = """
name: my-app
framework: angular
state_store:
  store_type: angular_signals
  entities:
    - Order
    - Product
  selectors:
    - selectOrders
    - selectProducts
"""
        result = parser.parse(yaml_str)
        store = result["state_store"]
        assert store is not None
        assert store.entities == ["Order", "Product"]
        assert "selectOrders" in store.selectors

    def test_parser_with_layout(self):
        """Test parse có layout config."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        yaml_str = """
name: my-app
layout: topnav
ui_framework: tailwind
"""
        result = parser.parse(yaml_str)
        app = result["frontend_app"]
        assert app.layout.value == "topnav"
        assert app.ui_framework == "tailwind"

    def test_parser_with_description(self):
        """Test parse có description."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        yaml_str = """
name: my-app
description: Ứng dụng quản lý đơn hàng
framework: react
"""
        result = parser.parse(yaml_str)
        app = result["frontend_app"]
        assert app.description == "Ứng dụng quản lý đơn hàng"

    def test_parser_full_config(self):
        """Test parse cấu hình đầy đủ."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        yaml_str = """
name: ecommerce-app
framework: angular
ui_framework: material
layout: sidebar
description: App thương mại điện tử
routes:
  - path: /
    component: Dashboard
  - path: /orders
    component: OrderList
  - path: /orders/:id
    component: OrderDetail
state_store:
  store_type: angular_signals
  entities:
    - Order
    - Product
    - Customer
"""
        result = parser.parse(yaml_str)
        assert result["frontend_app"] is not None
        assert result["frontend_app"].name == "ecommerce-app"
        assert len(result["routes"]) == 3
        assert result["state_store"] is not None
        assert len(result["state_store"].entities) == 3

    def test_parser_yaml_comment_only(self):
        """Test parse YAML comment-only trả về empty."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        yaml_str = """
# Đây là comment
# Không có nội dung
"""
        result = parser.parse(yaml_str)
        assert result == {"frontend_app": None, "routes": [], "state_store": None}

    def test_parser_non_dict_yaml_raises(self):
        """Test parse YAML không phải mapping throw lỗi."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        yaml_str = "- just a list item"
        with pytest.raises(MidicoderError) as exc_info:
            parser.parse(yaml_str)
        assert exc_info.value.code == ErrorCode.CP18_FRONTEND_PARSE_ERROR

    def test_parser_react_zustand_store(self):
        """Test parse React + Zustand config."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        yaml_str = """
name: react-app
framework: react
state_store:
  store_type: zustand
  entities:
    - User
    - Cart
"""
        result = parser.parse(yaml_str)
        assert result["frontend_app"].framework.value == "react"
        assert result["state_store"].store_type.value == "zustand"

    def test_parser_invalid_route_path_raises(self):
        """Test parse route path không hợp lệ throw lỗi."""
        from midicoder.emitters.core.component.parser import FrontendFrameworkParser
        parser = FrontendFrameworkParser()
        yaml_str = """
name: my-app
routes:
  - path: invalid-path
    component: SomeComponent
"""
        with pytest.raises(MidicoderError):
            parser.parse(yaml_str)

    def test_parser_convenience_function(self):
        """Test module-level convenience function."""
        from midicoder.emitters.core.component.parser import parse_frontend_dsl
        yaml_str = """
name: test-app
framework: angular
"""
        result = parse_frontend_dsl(yaml_str)
        assert "frontend_app" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
