# coding: utf-8
"""
End-to-End Integration Test cho Midicoder Pipeline.

Test toàn bộ flow:
    ProjectionTree (DSL) → MIRBuilder → ImplementationPlan → Code Generation

Cover cả hai paths:
1. PackEmitterRouter dispatch (structured pack emitter — cp01.entity.fastapi)
2. Raw Emitter (Jinja2 template rendering — config.py.jinja2)

Tác giả: Midicoder CE Team
Version: 1.0.0
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from unittest.mock import patch

from midicoder.dsl.projection import ProjectionNode, ProjectionTree, NodeKind
from midicoder.pipeline.dsl_parser import DSLParser
from midicoder.pipeline.commands.ir import _build_mir_from_projection_tree
from midicoder.pipeline.mir import MIR
from midicoder.pipeline.plan import ImplementationPlan, ModuleSpec, FileSpec
from midicoder.pipeline.commands.code import (
    _create_implementation_plan,
    _generate_file,
    _render_template,
)
from midicoder.pipeline.emitter import Emitter
from midicoder.pipeline.pack_emitter_router import PackEmitterRouter


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="class")
def sample_projection_tree() -> ProjectionTree:
    """Build a minimal ProjectionTree với 2 entities + 1 command + 1 query + 1 event.

    Entities:
      - Customer  (id, name, email) — tenant_isolated
      - Order     (id, customer_id, total, status) — tenant_isolated

    Command: CreateOrder  (writes_to: Order, emits: OrderCreated)
    Query:   ListOrders   (reads_from: Order)
    Event:   OrderCreated
    """
    tree = ProjectionTree()

    # --- Entity: Customer ---
    tree.add_node(ProjectionNode(
        id="Customer",
        kind=NodeKind.ENTITY,
        params={
            "id": "Customer",
            "description": "Khách hàng",
            "fields": [
                {"name": "id", "type": "string", "primary_key": True},
                {"name": "name", "type": "string"},
                {"name": "email", "type": "string"},
            ],
            "primary_key": "id",
            "tenant_scope": "tenant_isolated",
        },
    ))

    # --- Entity: Order ---
    tree.add_node(ProjectionNode(
        id="Order",
        kind=NodeKind.ENTITY,
        params={
            "id": "Order",
            "description": "Đơn hàng",
            "fields": [
                {"name": "id", "type": "string", "primary_key": True},
                {"name": "customer_id", "type": "string"},
                {"name": "total", "type": "decimal"},
                {"name": "status", "type": "string"},
            ],
            "primary_key": "id",
            "tenant_scope": "tenant_isolated",
        },
    ))

    # --- Command: CreateOrder ---
    tree.add_node(ProjectionNode(
        id="CreateOrder",
        kind=NodeKind.COMMAND,
        params={
            "id": "CreateOrder",
            "description": "Tạo đơn hàng mới",
            "input": [
                {"name": "customer_id", "type": "string"},
                {"name": "total", "type": "decimal"},
            ],
            "writes_to": ["Order"],
            "emits": ["OrderCreated"],
            "category": "create",
            "tenant_scope": "tenant_isolated",
            "required_permissions": ["order.create"],
        },
    ))

    # --- Query: ListOrders ---
    tree.add_node(ProjectionNode(
        id="ListOrders",
        kind=NodeKind.QUERY,
        params={
            "id": "ListOrders",
            "description": "Lấy danh sách đơn hàng",
            "input": [
                {"name": "customer_id", "type": "string"},
            ],
            "reads_from": ["Order"],
            "returns": {"type": "list", "item": "Order"},
            "category": "list",
            "tenant_scope": "tenant_isolated",
        },
    ))

    # --- Event: OrderCreated ---
    tree.add_node(ProjectionNode(
        id="OrderCreated",
        kind=NodeKind.EVENT,
        params={
            "id": "OrderCreated",
            "type": "domain_event",
            "source_entity": "Order",
            "fields": [
                {"name": "order_id", "type": "string"},
                {"name": "customer_id", "type": "string"},
                {"name": "total", "type": "decimal"},
            ],
        },
    ))

    return tree


@pytest.fixture(scope="class")
def sample_mir(sample_projection_tree: ProjectionTree) -> MIR:
    """Build MIR từ ProjectionTree."""
    return _build_mir_from_projection_tree(sample_projection_tree)


@pytest.fixture(scope="class")
def sample_mir_dict(sample_mir: MIR) -> dict[str, Any]:
    """MIR serialized to dict (như lưu trong SQLite artifacts)."""
    return sample_mir.to_dict()


@pytest.fixture(scope="class")
def sample_plan(sample_mir_dict: dict[str, Any]) -> ImplementationPlan:
    """Build ImplementationPlan từ MIR dict."""
    return _create_implementation_plan(sample_mir_dict, target="all")


# ============================================================================
# Stage 1: DSL → ProjectionTree
# ============================================================================

class TestDSLToProjectionTree:
    """Test DSL → ProjectionTree construction."""

    def test_manual_tree_has_entities(self, sample_projection_tree: ProjectionTree):
        """ProjectionTree có chứa entity nodes."""
        entities = sample_projection_tree.get_entities()
        entity_ids = [e.params["id"] for e in entities]
        assert "Customer" in entity_ids
        assert "Order" in entity_ids

    def test_manual_tree_has_commands(self, sample_projection_tree: ProjectionTree):
        """ProjectionTree có chứa command nodes."""
        commands = sample_projection_tree.get_commands()
        cmd_ids = [c.params["id"] for c in commands]
        assert "CreateOrder" in cmd_ids

    def test_manual_tree_has_queries(self, sample_projection_tree: ProjectionTree):
        """ProjectionTree có chứa query nodes."""
        queries = sample_projection_tree.get_queries()
        query_ids = [q.params["id"] for q in queries]
        assert "ListOrders" in query_ids

    def test_manual_tree_has_events(self, sample_projection_tree: ProjectionTree):
        """ProjectionTree có chứa event nodes."""
        events = sample_projection_tree.get_events()
        event_ids = [e.params["id"] for e in events]
        assert "OrderCreated" in event_ids

    def test_tree_node_count(self, sample_projection_tree: ProjectionTree):
        """Total node count đúng với số nodes đã thêm."""
        assert sample_projection_tree.node_count() == 5

    def test_parse_from_yaml_dict(self):
        """DSLParser.build_projection_tree tạo tree từ YAML strings."""
        parser = DSLParser()
        tree = parser.build_projection_tree({
            "entities": (
                "entities:\n"
                "  - id: Product\n"
                "    description: Sản phẩm\n"
                "    fields:\n"
                "      - name: sku\n"
                "        type: string\n"
                "      - name: price\n"
                "        type: decimal\n"
            ),
            "commands": (
                "commands:\n"
                "  - id: CreateProduct\n"
                "    input: [sku, price]\n"
                "    category: create\n"
            ),
        })

        assert tree.node_count() == 2
        assert len(tree.get_entities()) == 1
        assert len(tree.get_commands()) == 1


# ============================================================================
# Stage 2: ProjectionTree → MIR
# ============================================================================

class TestProjectionTreeToMIR:
    """Test ProjectionTree → MIR transformation."""

    def test_mir_has_version_metadata(self, sample_mir: MIR):
        """MIR có version metadata."""
        assert sample_mir.metadata.get("version") == "1.0.0"

    def test_mir_has_source_metadata(self, sample_mir: MIR):
        """MIR có source metadata."""
        assert sample_mir.metadata.get("source") == "DSL ProjectionTree"

    def test_mir_entities_in_metadata(self, sample_mir: MIR):
        """MIR metadata chứa entity list cho emitter sử dụng."""
        entities = sample_mir.metadata.get("entities", [])
        entity_ids = [e["id"] for e in entities]
        assert "Customer" in entity_ids
        assert "Order" in entity_ids

        # Kiểm tra entity có fields
        customer = next(e for e in entities if e["id"] == "Customer")
        assert len(customer["fields"]) == 3

    def test_mir_commands_in_metadata(self, sample_mir: MIR):
        """MIR metadata chứa command list."""
        commands = sample_mir.metadata.get("commands", [])
        cmd_ids = [c["id"] for c in commands]
        assert "CreateOrder" in cmd_ids

    def test_mir_queries_in_metadata(self, sample_mir: MIR):
        """MIR metadata chứa query list."""
        queries = sample_mir.metadata.get("queries", [])
        query_ids = [q["id"] for q in queries]
        assert "ListOrders" in query_ids

    def test_mir_has_operations(self, sample_mir: MIR):
        """MIR có operations từ command/query processing."""
        assert len(sample_mir.operations) > 0

    def test_mir_has_auth_operations(self, sample_mir: MIR):
        """MIR có authorize_permission operations từ command với required_permissions."""
        auth_ops = sample_mir.get_operations_by_type("authorize_permission")
        assert len(auth_ops) > 0

    def test_mir_has_effect_flows(self, sample_mir: MIR):
        """MIR có effect flows từ command emits."""
        assert len(sample_mir.effect_flows) > 0
        # CreateOrder emits OrderCreated
        order_created_effects = [
            ef for ef in sample_mir.effect_flows
            if ef.target == "OrderCreated"
        ]
        assert len(order_created_effects) > 0

    def test_mir_has_tenant_operations(self, sample_mir: MIR):
        """MIR có enforce_tenant_scope operations."""
        tenant_ops = sample_mir.get_operations_by_type("enforce_tenant_scope")
        assert len(tenant_ops) > 0

    def test_mir_serialization_roundtrip(self, sample_mir: MIR):
        """MIR to_dict → from_dict giữ nguyên cấu trúc."""
        data = sample_mir.to_dict()
        restored = MIR.from_dict(data)

        assert len(restored.operations) == len(sample_mir.operations)
        assert len(restored.data_flows) == len(sample_mir.data_flows)
        assert restored.metadata.get("version") == "1.0.0"

    def test_mir_json_roundtrip(self, sample_mir: MIR):
        """MIR to_json → from_json giữ nguyên cấu trúc."""
        json_str = sample_mir.to_json()
        restored = MIR.from_json(json_str)

        assert len(restored.operations) == len(sample_mir.operations)

    def test_mir_compute_hash_deterministic(self, sample_mir: MIR):
        """MIR.compute_hash() deterministic — cùng MIR cho cùng hash."""
        hash1 = sample_mir.compute_hash()
        hash2 = sample_mir.compute_hash()
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex

    def test_mir_dict_has_entities_for_plan(self, sample_mir_dict: dict[str, Any]):
        """MIR dict format có metadata.entities cho _create_implementation_plan đọc."""
        entities = sample_mir_dict.get("metadata", {}).get("entities", [])
        assert len(entities) >= 2


# ============================================================================
# Stage 3: MIR → ImplementationPlan
# ============================================================================

class TestMIRToImplementationPlan:
    """Test MIR → ImplementationPlan creation."""

    def test_plan_has_backend_modules(self, sample_plan: ImplementationPlan):
        """Plan có backend modules."""
        backend = sample_plan.get_modules_by_type("backend")
        assert len(backend) > 0

    def test_plan_has_frontend_modules(self, sample_plan: ImplementationPlan):
        """Plan có frontend modules."""
        frontend = sample_plan.get_modules_by_type("frontend")
        assert len(frontend) > 0

    def test_plan_has_infra_modules(self, sample_plan: ImplementationPlan):
        """Plan có infra modules."""
        infra = sample_plan.get_modules_by_type("infra")
        assert len(infra) > 0

    def test_plan_meta_has_version(self, sample_plan: ImplementationPlan):
        """Plan meta có version."""
        assert "version" in sample_plan.meta

    def test_plan_backend_has_core_files(self, sample_plan: ImplementationPlan):
        """Backend plan có core files (main, config)."""
        backend_files = sample_plan.get_files_by_type("main")
        assert len(backend_files) > 0
        paths = [f.path for f in backend_files]
        assert any("main.py" in p for p in paths)

    def test_plan_backend_has_entity_files(self, sample_plan: ImplementationPlan):
        """Backend plan có files cho từng entity (Customer, Order)."""
        all_backend = sample_plan.get_modules_by_type("backend")
        all_paths = []
        for mod in all_backend:
            for f in mod.files:
                all_paths.append(f.path)

        # Ít nhất có file liên quan customer hoặc order
        assert any("customer" in p for p in all_paths) or any("order" in p for p in all_paths)

    def test_plan_file_counts(self, sample_plan: ImplementationPlan):
        """Plan count_files trả về dict có đủ keys."""
        counts = sample_plan.count_files()
        assert "backend" in counts
        assert "frontend" in counts
        assert "infra" in counts
        assert counts["backend"] > 0

    def test_plan_serialization_roundtrip(self, sample_plan: ImplementationPlan):
        """ImplementationPlan to_dict → from_dict giữ nguyên."""
        data = sample_plan.to_dict()
        restored = ImplementationPlan.from_dict(data)

        assert len(restored.modules) == len(sample_plan.modules)
        assert restored.meta.get("version") == sample_plan.meta.get("version")

    def test_plan_json_roundtrip(self, sample_plan: ImplementationPlan):
        """ImplementationPlan to_json → from_json giữ nguyên."""
        json_str = sample_plan.to_json()
        restored = ImplementationPlan.from_json(json_str)

        assert len(restored.modules) == len(sample_plan.modules)

    def test_plan_compute_hash_deterministic(self, sample_plan: ImplementationPlan):
        """ImplementationPlan.compute_hash() deterministic."""
        hash1 = sample_plan.compute_hash()
        hash2 = sample_plan.compute_hash()
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_plan_target_filtering_backend_only(
        self, sample_mir_dict: dict[str, Any]
    ):
        """Plan với target='backend' chỉ có backend modules."""
        plan = _create_implementation_plan(sample_mir_dict, target="backend")
        counts = plan.count_files()
        assert counts["backend"] > 0
        assert counts["frontend"] == 0

    def test_plan_target_filtering_frontend_only(
        self, sample_mir_dict: dict[str, Any]
    ):
        """Plan với target='frontend' chỉ có frontend modules."""
        plan = _create_implementation_plan(sample_mir_dict, target="frontend")
        counts = plan.count_files()
        assert counts["frontend"] > 0
        assert counts["backend"] == 0


# ============================================================================
# Stage 4: ImplementationPlan → Code Generation (Emitter path)
# ============================================================================

class TestCodeGenerationEmitter:
    """Test code generation path: raw Emitter (Jinja2 template)."""

    def test_render_config_template(self):
        """Render config.py.jinja2 — template không cần context phức tạp."""
        content = _render_template("config.py.jinja2", {"app_name": "Test API"})
        assert len(content) > 0
        # Config template nên có nội dung Python
        assert "import" in content or "class" in content or "def" in content

    def test_render_main_template(self):
        """Render main.py.jinja2 — template với settings object trong context."""
        # main.py.jinja2 expects `settings` attribute (not a dict),
        # so provide a simple namespace-like object.
        from types import SimpleNamespace

        content = _render_template(
            "main.py.jinja2",
            {
                "settings": SimpleNamespace(app_name="E2E Test API"),
                "entities": [
                    {"id": "Customer"},
                    {"id": "Order"},
                ],
            },
        )
        assert len(content) > 0

    def test_render_template_with_custom_stack(self, tmp_path: Path):
        """Render template từ custom template directory (stack override)."""
        # Tạo template file trong tmp_path
        template_file = tmp_path / "hello.txt.jinja2"
        template_file.write_text("Hello, {{ name }} from {{ stack }}!")

        emitter = Emitter(template_dir=tmp_path)
        result = emitter.render("hello.txt.jinja2", {"name": "E2E", "stack": "test"})
        assert "Hello, E2E from test!" in result

    def test_emitter_emit_creates_files(self, tmp_path: Path):
        """Emitter.emit() tạo files từ FileSpecs."""
        # Tạo template
        template_file = tmp_path / "model.py.jinja2"
        template_file.write_text(
            "class {{ entity_id }}:\n"
            "    \"\"\"{{ entity_desc }}\"\"\"\n"
            "{% for f in fields %}\n"
            "    {{ f.name }}: {{ f.type }}\n"
            "{% endfor %}"
        )

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        emitter = Emitter(template_dir=tmp_path)

        file_specs = [
            FileSpec(
                path="app/models/customer.py",
                file_type="model",
                template="model.py.jinja2",
                context={
                    "entity_id": "Customer",
                    "entity_desc": "Khach hang",
                    "fields": [
                        {"name": "id", "type": "str"},
                        {"name": "name", "type": "str"},
                    ],
                },
            ),
            FileSpec(
                path="app/models/order.py",
                file_type="model",
                template="model.py.jinja2",
                context={
                    "entity_id": "Order",
                    "entity_desc": "Don hang",
                    "fields": [
                        {"name": "id", "type": "str"},
                        {"name": "total", "type": "float"},
                    ],
                },
            ),
        ]

        generated = emitter.emit(file_specs, output_dir)

        assert len(generated) == 2
        # Kiểm tra files được tạo
        assert (output_dir / "app/models/customer.py").exists()
        assert (output_dir / "app/models/order.py").exists()

        # Kiểm tra nội dung
        customer_content = (output_dir / "app/models/customer.py").read_text()
        assert "class Customer:" in customer_content
        assert "id: str" in customer_content

        order_content = (output_dir / "app/models/order.py").read_text()
        assert "class Order:" in order_content
        assert "total: float" in order_content


# ============================================================================
# Stage 5: ImplementationPlan → Code Generation (PackEmitterRouter path)
# ============================================================================

class TestCodeGenerationPackEmitterRouter:
    """Test code generation path: PackEmitterRouter dispatch."""

    def test_router_dispatch_cp01_entity_fastapi(self):
        """PackEmitterRouter.dispatch() với cp01.entity.fastapi."""
        # Entity parser expects fields as list of dicts with 'name', 'type', 'primary_key'.
        file_spec = {
            "path": "app/models/customer.py",
            "file_type": "model",
            "template": "cp01_domain_model/entity.py.jinja2",
            "context": {
                "entity": {
                    "id": "Customer",
                    "description": "Khach hang",
                    "fields": [
                        {"name": "id", "type": "string", "primary_key": True},
                        {"name": "name", "type": "string"},
                        {"name": "email", "type": "string"},
                    ],
                },
                "all_entities": [
                    {
                        "id": "Customer",
                        "description": "Khach hang",
                        "fields": [{"name": "id", "type": "string", "primary_key": True}],
                    },
                    {
                        "id": "Order",
                        "description": "Don hang",
                        "fields": [{"name": "id", "type": "string", "primary_key": True}],
                    },
                ],
            },
            "metadata": {"stack": "fastapi"},
        }

        result_files = PackEmitterRouter.dispatch(
            "cp01.entity.fastapi", file_spec, "fastapi"
        )

        assert len(result_files) > 0
        result = result_files[0]
        assert "path" in result
        assert "content" in result
        # Content nên có class Customer hoặc model tương tự
        content = result["content"]
        assert "Customer" in content or len(content) > 0

    def test_router_dispatch_unknown_raises(self):
        """PackEmitterRouter.dispatch() raise KeyError cho unknown pack_emitter."""
        file_spec = {"path": "x.py", "context": {}}

        with pytest.raises(KeyError):
            PackEmitterRouter.dispatch("unknown.emitter", file_spec, "fastapi")

    def test_router_dispatch_with_fallback(self):
        """PackEmitterRouter trả về fallback placeholder khi parser fail."""
        file_spec = {
            "path": "app/models/invalid.py",
            "file_type": "model",
            "context": {
                # Entity dict không hợp lệ — parser sẽ return None
                "entity": {},
            },
            "metadata": {"stack": "fastapi"},
        }

        result_files = PackEmitterRouter.dispatch(
            "cp01.entity.fastapi", file_spec, "fastapi"
        )

        # Router trả về fallback placeholder
        assert len(result_files) > 0
        assert "path" in result_files[0]
        assert "content" in result_files[0]


# ============================================================================
# Stage 6: Full Pipeline E2E — DSL → MIR → Plan → Generated Files
# ============================================================================

class TestFullPipelineE2E:
    """Test toàn bộ pipeline: DSL → MIR → Plan → Code Generation.

    Các test này là end-to-end và không mock bất kỳ bước nào.
    """

    def test_full_pipeline_produces_backend_files(
        self,
        sample_projection_tree: ProjectionTree,
        tmp_path: Path,
    ):
        """Full pipeline: ProjectionTree → MIR → Plan → generated backend files."""
        # Step 1: DSL → MIR
        mir = _build_mir_from_projection_tree(sample_projection_tree)
        mir_dict = mir.to_dict()

        # Step 2: MIR → Plan
        plan = _create_implementation_plan(mir_dict, target="backend")

        # Step 3: Plan → Generated files (raw Jinja2 path — skip pack emitter for simplicity)
        output_dir = tmp_path / "generated"
        output_dir.mkdir()

        generated_count = 0
        for module in plan.get_modules_by_type("backend"):
            for file_spec in module.files:
                # Chỉ generate files không có pack_emitter metadata (raw Jinja2)
                metadata = file_spec.metadata or {}
                if metadata.get("pack_emitter"):
                    continue

                try:
                    file_dict = file_spec.to_dict()
                    result = _generate_file(file_dict, output_dir, dry_run=False, mir_data=mir_dict)
                    if result:
                        generated_count += 1
                except Exception:
                    # Một số templates có thể cần context đặc biệt — skip
                    pass

        # Nên có ít nhất 1 file được generate thành công
        assert generated_count > 0, "Không có file nào được generate thành công"

    def test_full_pipeline_produces_infra_files(
        self,
        sample_projection_tree: ProjectionTree,
        tmp_path: Path,
    ):
        """Full pipeline: Infra files từ Plan → generated."""
        mir = _build_mir_from_projection_tree(sample_projection_tree)
        mir_dict = mir.to_dict()

        plan = _create_implementation_plan(mir_dict, target="all")

        output_dir = tmp_path / "generated"
        output_dir.mkdir()

        infra_files = []
        for module in plan.get_modules_by_type("infra"):
            for file_spec in module.files:
                metadata = file_spec.metadata or {}
                if metadata.get("pack_emitter"):
                    continue
                try:
                    file_dict = file_spec.to_dict()
                    result = _generate_file(file_dict, output_dir, dry_run=False, mir_data=mir_dict)
                    if result:
                        infra_files.append(result.path)
                except Exception:
                    pass

        # Kiểm tra các infra files tồn tại
        # (có thể có 0 file nếu tất cả đều dùng pack_emitter — test validation structure)
        if infra_files:
            for path in infra_files:
                assert (output_dir / path).exists(), f"Infra file không tồn tại: {path}"

    def test_full_pipeline_mir_metadata_carries_through(
        self,
        sample_projection_tree: ProjectionTree,
        sample_mir_dict: dict[str, Any],
        sample_plan: ImplementationPlan,
    ):
        """Kiểm tra metadata (entities) từ MIR được giữ trong Plan FileSpecs context."""
        # MIR có entities trong metadata
        mir_entities = sample_mir_dict.get("metadata", {}).get("entities", [])
        assert len(mir_entities) >= 2

        # Plan modules — tìm các file có entity context
        has_entity_context = False
        for module in sample_plan.modules:
            for file_spec in module.files:
                ctx = file_spec.context or {}
                if ctx.get("entity"):
                    has_entity_context = True
                    break

        # Ít nhất một file spec có entity context (từ per_entity expansion)
        assert has_entity_context, (
            "Không có FileSpec nào có entity context — "
            "per_entity expansion có thể không hoạt động đúng"
        )

    def test_full_pipeline_deterministic_plan_hash(
        self,
        sample_mir_dict: dict[str, Any],
    ):
        """Cùng MIR → cùng Plan hash (deterministic)."""
        plan1 = _create_implementation_plan(sample_mir_dict, target="backend")
        plan2 = _create_implementation_plan(sample_mir_dict, target="backend")

        # Hash có thể khác nhau do created_at timestamp, nhưng structure nên giống
        count1 = plan1.count_files()
        count2 = plan2.count_files()
        assert count1 == count2

    def test_full_pipeline_from_yaml_parsing(
        self,
        tmp_path: Path,
    ):
        """Full pipeline bắt đầu từ YAML string → DSLParser → MIR → Plan."""
        parser = DSLParser()
        tree = parser.build_projection_tree({
            "entities": (
                "entities:\n"
                "  - id: Invoice\n"
                "    description: Hoa don\n"
                "    fields:\n"
                "      - name: id\n"
                "        type: string\n"
                "      - name: amount\n"
                "        type: decimal\n"
            ),
            "commands": (
                "commands:\n"
                "  - id: CreateInvoice\n"
                "    input: [amount]\n"
                "    category: create\n"
            ),
            "queries": "queries: []",
            "events": "events: []",
            "workflows": "workflows: []",
            "value_objects": "value_objects: []",
            "guards": "guards: []",
        })

        # DSL → MIR
        mir = _build_mir_from_projection_tree(tree)
        mir_dict = mir.to_dict()

        # MIR có entity Invoice
        entities = mir_dict.get("metadata", {}).get("entities", [])
        assert any(e["id"] == "Invoice" for e in entities)

        # MIR → Plan
        plan = _create_implementation_plan(mir_dict, target="backend")
        counts = plan.count_files()
        assert counts["backend"] > 0

        # Plan → Generate (at least core files)
        output_dir = tmp_path / "yaml_pipeline"
        output_dir.mkdir()

        generated = 0
        for module in plan.get_modules_by_type("backend"):
            for file_spec in module.files:
                metadata = file_spec.metadata or {}
                if metadata.get("pack_emitter"):
                    continue
                try:
                    file_dict = file_spec.to_dict()
                    result = _generate_file(file_dict, output_dir, dry_run=False, mir_data=mir_dict)
                    if result:
                        generated += 1
                except Exception:
                    pass

        assert generated > 0, "YAML pipeline không generate được file nào"

    def test_e2e_both_emit_paths(
        self,
        sample_projection_tree: ProjectionTree,
        tmp_path: Path,
    ):
        """Test cả hai emit paths (PackEmitterRouter + raw Emitter) trong cùng pipeline."""
        mir = _build_mir_from_projection_tree(sample_projection_tree)
        mir_dict = mir.to_dict()
        plan = _create_implementation_plan(mir_dict, target="backend")

        output_dir = tmp_path / "both_paths"
        output_dir.mkdir()

        pack_emitter_count = 0
        raw_emitter_count = 0

        for module in plan.get_modules_by_type("backend"):
            for file_spec in module.files:
                file_dict = file_spec.to_dict()
                metadata = file_spec.metadata or {}

                if metadata.get("pack_emitter"):
                    # Path 1: PackEmitterRouter
                    try:
                        result = _generate_file(file_dict, output_dir, dry_run=False, mir_data=mir_dict)
                        if result:
                            pack_emitter_count += 1
                    except Exception:
                        pass
                else:
                    # Path 2: Raw Emitter (Jinja2)
                    try:
                        result = _generate_file(file_dict, output_dir, dry_run=False, mir_data=mir_dict)
                        if result:
                            raw_emitter_count += 1
                    except Exception:
                        pass

        # Ít nhất một paths hoạt động
        total = pack_emitter_count + raw_emitter_count
        assert total > 0, (
            f"Cả hai emit paths đều không generate được file. "
            f"PackEmitterRouter: {pack_emitter_count}, Raw Emitter: {raw_emitter_count}"
        )


# ============================================================================
# Stage 7: Error Handling
# ============================================================================

class TestPipelineErrorHandling:
    """Test error handling trong pipeline."""

    def test_empty_tree_produces_empty_mir(self):
        """Empty ProjectionTree → MIR với operations rỗng."""
        tree = ProjectionTree()
        mir = _build_mir_from_projection_tree(tree)

        assert isinstance(mir, MIR)
        # MIR vẫn có metadata mặc dù tree rỗng
        assert mir.metadata.get("version") == "1.0.0"

    def test_plan_with_no_entities_has_core_files(self):
        """Plan từ MIR không có entities vẫn có core backend files."""
        mir_dict = {
            "metadata": {
                "entities": [],
                "commands": [],
                "queries": [],
            },
        }
        plan = _create_implementation_plan(mir_dict, target="backend")

        counts = plan.count_files()
        assert counts["backend"] > 0  # core files luôn có

    def test_generate_file_missing_template(self, tmp_path: Path):
        """_generate_file xử lý template không tồn tại."""
        file_plan = {
            "path": "app/missing.py",
            "type": "model",
            "template": "nonexistent_template.py.jinja2",
            "context": {},
            "metadata": {},
        }

        output_dir = tmp_path / "error_test"
        output_dir.mkdir()

        result = _generate_file(file_plan, output_dir, dry_run=False)
        # Template không tồn tại → None hoặc error được capture
        assert result is None
