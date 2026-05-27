"""
Unit tests cho render_context — EU-0.1.

Kiểm tra:
1. Tất cả TypedDicts trong projection.py có field render_context
2. Loader parse render_context từ YAML và attach vào ProjectionNode.params
3. Loader default render_context={} khi YAML không có field
4. Loader validate render_context phải là dict
"""

import pytest
import sys
from pathlib import Path
from typing import get_type_hints

# thêm project root vào path
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


class TestRenderContextInTypedDicts:
    """Kiểm tra render_context field tồn tại trong tất cả TypedDicts."""

    def test_entity_params_has_render_context(self):
        """EntityParams phải có field render_context."""
        from midicoder.dsl.projection import EntityParams

        hints = get_type_hints(EntityParams)
        assert "render_context" in hints, "EntityParams thiếu field render_context"

    def test_command_params_has_render_context(self):
        """CommandParams phải có field render_context."""
        from midicoder.dsl.projection import CommandParams

        hints = get_type_hints(CommandParams)
        assert "render_context" in hints, "CommandParams thiếu field render_context"

    def test_query_params_has_render_context(self):
        """QueryParams phải có field render_context."""
        from midicoder.dsl.projection import QueryParams

        hints = get_type_hints(QueryParams)
        assert "render_context" in hints, "QueryParams thiếu field render_context"

    def test_workflow_params_has_render_context(self):
        """WorkflowParams phải có field render_context."""
        from midicoder.dsl.projection import WorkflowParams

        hints = get_type_hints(WorkflowParams)
        assert "render_context" in hints, "WorkflowParams thiếu field render_context"

    def test_ui_component_params_has_render_context(self):
        """UIComponentParams phải có field render_context."""
        from midicoder.dsl.projection import UIComponentParams

        hints = get_type_hints(UIComponentParams)
        assert "render_context" in hints, "UIComponentParams thiếu field render_context"

    def test_frontend_app_params_has_render_context(self):
        """FrontendAppParams phải có field render_context."""
        from midicoder.dsl.projection import FrontendAppParams

        hints = get_type_hints(FrontendAppParams)
        assert "render_context" in hints, "FrontendAppParams thiếu field render_context"

    def test_aggregate_params_has_render_context(self):
        """AggregateParams phải có field render_context."""
        from midicoder.dsl.projection import AggregateParams

        hints = get_type_hints(AggregateParams)
        assert "render_context" in hints, "AggregateParams thiếu field render_context"

    def test_event_params_has_render_context(self):
        """EventParams phải có field render_context."""
        from midicoder.dsl.projection import EventParams

        hints = get_type_hints(EventParams)
        assert "render_context" in hints, "EventParams thiếu field render_context"

    def test_value_object_params_has_render_context(self):
        """ValueObjectParams phải có field render_context."""
        from midicoder.dsl.projection import ValueObjectParams

        hints = get_type_hints(ValueObjectParams)
        assert "render_context" in hints, "ValueObjectParams thiếu field render_context"

    def test_infrastructure_params_has_render_context(self):
        """IacResourceParams phải có field render_context."""
        from midicoder.dsl.projection import IacResourceParams

        hints = get_type_hints(IacResourceParams)
        assert "render_context" in hints, "IacResourceParams thiếu field render_context"

    def test_all_params_typed_dicts_have_render_context(self):
        """Tất cả classes kết thúc bằng 'Params' và là TypedDict phải có render_context."""
        import midicoder.dsl.projection as proj_module
        import typing

        params_classes = []
        for name in dir(proj_module):
            cls = getattr(proj_module, name)
            if (
                isinstance(cls, type)
                and name.endswith("Params")
                and issubclass(cls, dict)
            ):
                # Kiểm tra xem có phải TypedDict không
                if hasattr(cls, "__annotations__"):
                    params_classes.append((name, cls))

        missing = []
        for name, cls in params_classes:
            hints = get_type_hints(cls)
            if "render_context" not in hints:
                missing.append(name)

        assert not missing, (
            f"{len(missing)} TypedDicts thiếu render_context: {', '.join(missing[:10])}"
            + (f" ... và {len(missing) - 10} classes khác" if len(missing) > 10 else "")
        )


class TestLoaderParseRenderContext:
    """Kiểm tra loader.py parse render_context đúng cách."""

    def test_load_entity_with_render_context(self, tmp_path):
        """_load_entities() nên parse render_context từ YAML."""
        yaml_file = tmp_path / "entities.yaml"
        yaml_file.write_text(
            """entities:
  - id: Product
    description: Sản phẩm
    fields:
      - name: name
        type: string
    render_context:
      sidebar_width: 280
      show_sku_in_list: true
      grid_columns: 4
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_entities

        nodes = _load_entities(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.params.get("render_context") == {
            "sidebar_width": 280,
            "show_sku_in_list": True,
            "grid_columns": 4,
        }

    def test_load_entity_without_render_context(self, tmp_path):
        """_load_entities() nên default render_context={} khi YAML không có."""
        yaml_file = tmp_path / "entities.yaml"
        yaml_file.write_text(
            """entities:
  - id: Product
    description: Sản phẩm
    fields:
      - name: name
        type: string
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_entities

        nodes = _load_entities(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.params.get("render_context") == {}

    def test_load_command_with_render_context(self, tmp_path):
        """_load_commands() nên parse render_context từ YAML."""
        yaml_file = tmp_path / "commands.yaml"
        yaml_file.write_text(
            """commands:
  - id: CreateProduct
    description: Tạo sản phẩm mới
    input:
      - name: name
        type: string
    render_context:
      form_layout: vertical
      validation_mode: async
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_commands

        nodes = _load_commands(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.params.get("render_context") == {
            "form_layout": "vertical",
            "validation_mode": "async",
        }

    def test_load_query_with_render_context(self, tmp_path):
        """_load_queries() nên parse render_context từ YAML."""
        yaml_file = tmp_path / "queries.yaml"
        yaml_file.write_text(
            """queries:
  - id: ListProducts
    description: Lấy danh sách sản phẩm
    render_context:
      pagination_size: 25
      sortable_columns:
        - name
        - price
        - created_at
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_queries

        nodes = _load_queries(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.params.get("render_context") == {
            "pagination_size": 25,
            "sortable_columns": ["name", "price", "created_at"],
        }

    def test_load_workflow_with_render_context(self, tmp_path):
        """_load_workflows() nên parse render_context từ YAML."""
        yaml_file = tmp_path / "workflows.yaml"
        yaml_file.write_text(
            """workflows:
  - id: OrderFulfillment
    description: Quy trình xử lý đơn hàng
    render_context:
      diagram_style: horizontal
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_workflows

        nodes = _load_workflows(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.params.get("render_context") == {"diagram_style": "horizontal"}

    def test_load_event_with_render_context(self, tmp_path):
        """_load_events() nên parse render_context từ YAML."""
        yaml_file = tmp_path / "events.yaml"
        yaml_file.write_text(
            """events:
  - id: ProductCreated
    description: Sản phẩm đã được tạo
    render_context:
      notification_priority: high
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_events

        nodes = _load_events(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.params.get("render_context") == {"notification_priority": "high"}

    def test_load_entity_with_empty_render_context(self, tmp_path):
        """_load_entities() nên handle render_context: null thành {}."""
        yaml_file = tmp_path / "entities.yaml"
        yaml_file.write_text(
            """entities:
  - id: Product
    description: Sản phẩm
    fields:
      - name: name
        type: string
    render_context: null
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_entities

        nodes = _load_entities(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        # null YAML → None, nên default thành {}
        assert node.params.get("render_context") == {}

    def test_load_entity_with_invalid_render_context_raises_error(self, tmp_path):
        """_load_entities() nên raise error khi render_context không phải dict."""
        yaml_file = tmp_path / "entities.yaml"
        yaml_file.write_text(
            """entities:
  - id: Product
    description: Sản phẩm
    fields:
      - name: name
        type: string
    render_context: "invalid_string"
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_entities
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError):
            _load_entities(yaml_file)

    def test_load_enums_with_render_context(self, tmp_path):
        """_load_enums() nên parse render_context từ YAML."""
        yaml_file = tmp_path / "enums.yaml"
        yaml_file.write_text(
            """enums:
  - id: OrderStatus
    description: Trạng thái đơn hàng
    values:
      - id: pending
        label: Chờ xử lý
      - id: confirmed
        label: Đã xác nhận
    render_context:
      color_scheme: semantic
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_enums

        nodes = _load_enums(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.params.get("render_context") == {"color_scheme": "semantic"}

    def test_load_rules_with_render_context(self, tmp_path):
        """_load_rules() nên parse render_context từ YAML."""
        yaml_file = tmp_path / "rules.yaml"
        yaml_file.write_text(
            """rules:
  - id: MinOrderAmount
    description: Số tiền đơn hàng tối thiểu
    type: validation
    condition:
      field: amount
      operator: gte
      value: 100000
    render_context:
      show_error_inline: true
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_rules

        nodes = _load_rules(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.params.get("render_context") == {"show_error_inline": True}

    def test_load_http_with_render_context(self, tmp_path):
        """_load_http() nên parse render_context từ YAML."""
        yaml_file = tmp_path / "http.yaml"
        yaml_file.write_text(
            """routes:
  - id: GetProduct
    method: GET
    path: /products/{id}
    query_id: GetProductById
    render_context:
      swagger_hide_internal: false
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_http

        nodes = _load_http(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.params.get("render_context") == {"swagger_hide_internal": False}

    def test_load_policies_with_render_context(self, tmp_path):
        """_load_policies() nên parse render_context từ YAML."""
        yaml_file = tmp_path / "policies.yaml"
        yaml_file.write_text(
            """policies:
  - id: AdminOnly
    description: Chỉ admin được truy cập
    expression: user.role == 'admin'
    render_context:
      ui_hint: "Yêu cầu quyền admin"
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_policies

        nodes = _load_policies(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.params.get("render_context") == {"ui_hint": "Yêu cầu quyền admin"}

    def test_load_frontends_with_render_context(self, tmp_path):
        """_load_frontends() nên parse render_context từ YAML."""
        yaml_file = tmp_path / "frontends.yaml"
        yaml_file.write_text(
            """apps:
  - id: admin_dashboard
    framework: react
    render_context:
      sidebar_width: 280
      theme_mode: dark
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_frontends

        nodes = _load_frontends(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.params.get("render_context") == {
            "sidebar_width": 280,
            "theme_mode": "dark",
        }

    def test_load_ui_components_with_render_context(self, tmp_path):
        """_load_ui_components() nên parse render_context từ YAML."""
        yaml_file = tmp_path / "ui-components.yaml"
        yaml_file.write_text(
            """ui_components:
  - id: ProductList
    component_type: data_table
    entity_ref: Product
    render_context:
      card_style: compact
      grid_columns: 4
"""
        , encoding="utf-8")
        from midicoder.dsl.loader import _load_ui_components

        nodes = _load_ui_components(yaml_file)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.params.get("render_context") == {
            "card_style": "compact",
            "grid_columns": 4,
        }


class TestProjectionNodeRenderContext:
    """Kiểm tra ProjectionNode có thể chứa render_context trong params."""

    def test_projection_node_with_render_context(self):
        """ProjectionNode nên chấp nhận render_context trong params."""
        from midicoder.dsl.projection import ProjectionNode, NodeKind

        node = ProjectionNode(
            id="TestEntity",
            kind=NodeKind.ENTITY,
            params={
                "id": "TestEntity",
                "fields": [],
                "render_context": {"sidebar_width": 280, "custom_key": "custom_value"},
            },
        )
        assert node.params["render_context"]["sidebar_width"] == 280
        assert node.params["render_context"]["custom_key"] == "custom_value"

    def test_projection_node_without_render_context(self):
        """ProjectionNode nên hoạt động bình thường khi không có render_context."""
        from midicoder.dsl.projection import ProjectionNode, NodeKind

        node = ProjectionNode(
            id="TestEntity",
            kind=NodeKind.ENTITY,
            params={"id": "TestEntity", "fields": []},
        )
        # render_context là optional
        assert node.params.get("render_context") is None or node.params.get(
            "render_context"
        ) == {}
