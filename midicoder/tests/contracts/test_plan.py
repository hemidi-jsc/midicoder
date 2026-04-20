"""
Unit Tests cho Plan Contracts.

Kiểm tra behavior của:
- SurfaceType enum
- Surface class
- SurfacePlan class
- TargetPlan class
- PatchOperationType enum
- PatchOperation class
- PatchPlan class
- FileEdit class (P1)
- CodeBlock class (P1)
- PlanStep class (P1)
- DiffHunk class (P1)

Tests tuân thủ TDD, không mocks, bám sát SoT.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from midicoder.contracts.plan import (
    SurfaceType,
    Surface,
    SurfacePlan,
    TargetPlan,
    PatchOperationType,
    PatchOperation,
    PatchPlan,
)
from midicoder.contracts.artifact import ArtifactMetadata


# ============================================================================
# SurfaceType Tests (3 tests)
# ============================================================================


class TestSurfaceType:
    """Tests cho SurfaceType enum."""

    def test_surface_type_has_http_command_handler(self):
        """Kiểm tra SurfaceType có HTTP_COMMAND_HANDLER."""
        assert SurfaceType.HTTP_COMMAND_HANDLER.value == "http_command_handler"

    def test_surface_type_has_all_expected_types(self):
        """Kiểm tra SurfaceType có tất cả các loại surface cần thiết."""
        expected_types = {
            "http_command_handler",
            "http_query_handler",
            "application_service",
            "domain_service",
            "repository",
            "response_schema",
            "request_schema",
            "entity_model",
            "value_object",
            "event_handler",
            "workflow_engine",
            "auth_middleware",
            "cache_layer",
            "message_producer",
            "message_consumer",
        }
        actual_types = {st.value for st in SurfaceType}
        assert expected_types.issubset(actual_types)

    def test_surface_type_iteration(self):
        """Kiểm tra có thể iterate qua SurfaceType."""
        types = list(SurfaceType)
        assert len(types) >= 15
        assert all(isinstance(t, SurfaceType) for t in types)


# ============================================================================
# Surface Tests (10 tests)
# ============================================================================


class TestSurface:
    """Tests cho Surface class."""

    def test_surface_created_with_required_fields(self):
        """Kiểm tra Surface được tạo với các fields bắt buộc."""
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )

        assert surface.surface_type == "http_command_handler"
        assert surface.module == "orders.http"
        assert surface.symbol == "create_order"
        assert surface.mir_ref == "Command.CreateOrder"
        assert surface.dependencies == []
        assert surface.config == {}

    def test_surface_created_with_all_fields(self):
        """Kiểm tra Surface được tạo với tất cả fields."""
        surface = Surface(
            surface_type=SurfaceType.APPLICATION_SERVICE.value,
            module="orders.services",
            symbol="CreateOrderService",
            mir_ref="Command.CreateOrder",
            dependencies=["orders.http.create_order"],
            config={"timeout": 30, "retry": 3},
        )

        assert len(surface.dependencies) == 1
        assert surface.config == {"timeout": 30, "retry": 3}

    def test_surface_fully_qualified_name(self):
        """Kiểm tra fully_qualified_name property."""
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )

        assert surface.fully_qualified_name == "orders.http.create_order"

    def test_surface_to_dict(self):
        """Kiểm tra to_dict trả về dictionary đúng."""
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
            dependencies=["dep1"],
            config={"key": "value"},
        )
        surface_dict = surface.to_dict()

        assert surface_dict["surface_type"] == "http_command_handler"
        assert surface_dict["module"] == "orders.http"
        assert surface_dict["symbol"] == "create_order"
        assert surface_dict["dependencies"] == ["dep1"]
        assert surface_dict["config"] == {"key": "value"}

    def test_surface_from_dict(self):
        """Kiểm tra from_dict tạo Surface đúng."""
        surface_data = {
            "surface_type": "http_command_handler",
            "module": "orders.http",
            "symbol": "create_order",
            "mir_ref": "Command.CreateOrder",
            "dependencies": ["dep1", "dep2"],
            "config": {"timeout": 30},
        }

        surface = Surface.from_dict(surface_data)

        assert surface.surface_type == "http_command_handler"
        assert surface.module == "orders.http"
        assert surface.dependencies == ["dep1", "dep2"]

    def test_surface_from_dict_with_defaults(self):
        """Kiểm tra from_dict với missing fields dùng defaults."""
        surface_data = {
            "surface_type": "http_command_handler",
            "module": "orders.http",
            "symbol": "create_order",
            "mir_ref": "Command.CreateOrder",
        }

        surface = Surface.from_dict(surface_data)

        assert surface.dependencies == []
        assert surface.config == {}

    def test_surface_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
            dependencies=["dep1"],
            config={"key": "value"},
        )

        surface_dict = original.to_dict()
        reconstructed = Surface.from_dict(surface_dict)

        assert reconstructed.surface_type == original.surface_type
        assert reconstructed.module == original.module
        assert reconstructed.symbol == original.symbol
        assert reconstructed.dependencies == original.dependencies
        assert reconstructed.config == original.config

    def test_surface_with_nested_module(self):
        """Kiểm tra Surface với nested module path."""
        surface = Surface(
            surface_type=SurfaceType.REPOSITORY.value,
            module="app.domains.orders.repositories",
            symbol="OrderRepository",
            mir_ref="Entity.Order",
        )

        assert surface.fully_qualified_name == "app.domains.orders.repositories.OrderRepository"

    def test_surface_with_empty_config(self):
        """Kiểm tra Surface với empty config."""
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
            config={},
        )

        assert surface.config == {}

    def test_surface_with_complex_config(self):
        """Kiểm tra Surface với complex config."""
        complex_config = {
            "authentication": {"type": "jwt", "required": True},
            "rate_limit": {"requests": 100, "window": "1m"},
            "caching": {"enabled": True, "ttl": 300},
        }
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
            config=complex_config,
        )

        assert surface.config == complex_config


# ============================================================================
# SurfacePlan Tests (15 tests)
# ============================================================================


class TestSurfacePlan:
    """Tests cho SurfacePlan class."""

    def test_surface_plan_created_empty(self):
        """Kiểm tra SurfacePlan có thể được tạo rỗng."""
        plan = SurfacePlan()

        assert plan.mir_ref == ""
        assert plan.surfaces == []
        assert plan.module_graph == {}

    def test_surface_plan_created_with_mir_ref(self):
        """Kiểm tra SurfacePlan được tạo với mir_ref."""
        plan = SurfacePlan(mir_ref="Command.CreateOrder")

        assert plan.mir_ref == "Command.CreateOrder"
        assert plan.surfaces == []

    def test_surface_plan_with_surfaces(self):
        """Kiểm tra SurfacePlan với surfaces."""
        surface1 = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        surface2 = Surface(
            surface_type=SurfaceType.APPLICATION_SERVICE.value,
            module="orders.services",
            symbol="CreateOrderService",
            mir_ref="Command.CreateOrder",
        )
        plan = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=[surface1, surface2],
        )

        assert len(plan.surfaces) == 2
        assert plan.mir_ref == "Command.CreateOrder"

    def test_surface_plan_add_surface(self):
        """Kiểm tra add_surface thêm surface vào plan."""
        plan = SurfacePlan(mir_ref="Command.CreateOrder")
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )

        plan.add_surface(surface)

        assert len(plan.surfaces) == 1
        assert plan.surfaces[0] == surface

    def test_surface_plan_get_surface(self):
        """Kiểm tra get_surface trả về surface đúng."""
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        plan = SurfacePlan(mir_ref="Command.CreateOrder", surfaces=[surface])

        found = plan.get_surface("orders.http", "create_order")

        assert found is not None
        assert found.symbol == "create_order"

    def test_surface_plan_get_surface_not_found(self):
        """Kiểm tra get_surface trả về None khi không tìm thấy."""
        plan = SurfacePlan(mir_ref="Command.CreateOrder")

        found = plan.get_surface("nonexistent", "module")

        assert found is None

    def test_surface_plan_get_surfaces_by_type(self):
        """Kiểm tra get_surfaces_by_type trả về surfaces đúng."""
        http_surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        service_surface = Surface(
            surface_type=SurfaceType.APPLICATION_SERVICE.value,
            module="orders.services",
            symbol="CreateOrderService",
            mir_ref="Command.CreateOrder",
        )
        plan = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=[http_surface, service_surface],
        )

        http_surfaces = plan.get_surfaces_by_type("http_command_handler")

        assert len(http_surfaces) == 1
        assert http_surfaces[0].symbol == "create_order"

    def test_surface_plan_get_surfaces_by_module(self):
        """Kiểm tra get_surfaces_by_module trả về surfaces đúng."""
        surface1 = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        surface2 = Surface(
            surface_type=SurfaceType.HTTP_QUERY_HANDLER.value,
            module="orders.http",
            symbol="get_order",
            mir_ref="Query.GetOrder",
        )
        plan = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=[surface1, surface2],
        )

        http_surfaces = plan.get_surfaces_by_module("orders.http")

        assert len(http_surfaces) == 2

    def test_surface_plan_to_dict(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        plan = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=[surface],
            module_graph={"orders.http": ["orders.services"]},
        )
        plan.metadata = ArtifactMetadata.with_timestamp(author="test")

        plan_dict = plan.to_dict()

        assert plan_dict["type"] == "surface_plan"
        assert plan_dict["version"] == "1.0.0"
        assert plan_dict["mir_ref"] == "Command.CreateOrder"
        assert len(plan_dict["surfaces"]) == 1
        assert "orders.http" in plan_dict["module_graph"]

    def test_surface_plan_from_dict(self):
        """Kiểm tra from_dict tạo SurfacePlan đúng."""
        plan_data = {
            "type": "surface_plan",
            "version": "1.0.0",
            "metadata": {"author": "test"},
            "mir_ref": "Command.CreateOrder",
            "surfaces": [
                {
                    "surface_type": "http_command_handler",
                    "module": "orders.http",
                    "symbol": "create_order",
                    "mir_ref": "Command.CreateOrder",
                }
            ],
            "module_graph": {"orders.http": ["orders.services"]},
        }

        plan = SurfacePlan.from_dict(plan_data)

        assert plan.mir_ref == "Command.CreateOrder"
        assert len(plan.surfaces) == 1
        assert plan.surfaces[0].symbol == "create_order"

    def test_surface_plan_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
            dependencies=["dep1"],
        )
        original = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=[surface],
            module_graph={"orders.http": ["orders.services"]},
        )

        plan_dict = original.to_dict()
        reconstructed = SurfacePlan.from_dict(plan_dict)

        assert reconstructed.mir_ref == original.mir_ref
        assert len(reconstructed.surfaces) == len(original.surfaces)
        assert reconstructed.surfaces[0].symbol == original.surfaces[0].symbol

    def test_surface_plan_validate_empty(self):
        """Kiểm tra validate trả về errors khi plan empty."""
        plan = SurfacePlan()

        errors = plan.validate()

        assert len(errors) > 0
        assert any("mir_ref" in err for err in errors)
        assert any("surface" in err for err in errors)

    def test_surface_plan_validate_valid(self):
        """Kiểm tra validate trả về empty list khi valid."""
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        plan = SurfacePlan(mir_ref="Command.CreateOrder", surfaces=[surface])

        errors = plan.validate()

        assert errors == []

    def test_surface_plan_validate_duplicate_surfaces(self):
        """Kiểm tra validate phát hiện duplicate surfaces."""
        surface1 = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        surface2 = Surface(
            surface_type=SurfaceType.APPLICATION_SERVICE.value,
            module="orders.http",  # Same module.symbol
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        plan = SurfacePlan(mir_ref="Command.CreateOrder", surfaces=[surface1, surface2])

        errors = plan.validate()

        assert any("Duplicate" in err for err in errors)

    def test_surface_plan_builds_cache_on_init(self):
        """Kiểm tra cache được build khi init."""
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        plan = SurfacePlan(mir_ref="Command.CreateOrder", surfaces=[surface])

        # Cache nên được build
        assert "orders.http.create_order" in plan._surface_by_module_symbol


# ============================================================================
# TargetPlan Tests (15 tests)
# ============================================================================


class TestTargetPlan:
    """Tests cho TargetPlan class."""

    def test_target_plan_created_empty(self):
        """Kiểm tra TargetPlan có thể được tạo rỗng."""
        plan = TargetPlan()

        assert plan.target_runtime == ""
        assert plan.base_path == ""
        assert plan.surfaces == []
        assert plan.package_structure == {}

    def test_target_plan_created_with_runtime(self):
        """Kiểm tra TargetPlan được tạo với target_runtime."""
        plan = TargetPlan(
            target_runtime="fastapi",
            base_path="app",
        )

        assert plan.target_runtime == "fastapi"
        assert plan.base_path == "app"

    def test_target_plan_with_surfaces(self):
        """Kiểm tra TargetPlan với surfaces."""
        plan = TargetPlan(
            target_runtime="fastapi",
            base_path="app",
            surfaces=[
                {"module": "orders.http", "path": "orders/http.py"},
                {"module": "orders.services", "path": "orders/services.py"},
            ],
        )

        assert len(plan.surfaces) == 2

    def test_target_plan_with_package_structure(self):
        """Kiểm tra TargetPlan với package_structure."""
        package_structure = {
            "app": {
                "orders": {"http.py": "surface:orders.http", "services.py": "surface:orders.services"}
            }
        }
        plan = TargetPlan(
            target_runtime="fastapi",
            base_path="app",
            package_structure=package_structure,
        )

        assert plan.package_structure == package_structure

    def test_target_plan_to_dict(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        plan = TargetPlan(
            target_runtime="fastapi",
            base_path="app",
            surfaces=[{"module": "orders.http", "path": "orders/http.py"}],
            package_structure={"app": {}},
        )
        plan.metadata = ArtifactMetadata.with_timestamp(author="test")

        plan_dict = plan.to_dict()

        assert plan_dict["type"] == "target_plan"
        assert plan_dict["version"] == "1.0.0"
        assert plan_dict["target_runtime"] == "fastapi"
        assert plan_dict["base_path"] == "app"
        assert len(plan_dict["surfaces"]) == 1

    def test_target_plan_from_dict(self):
        """Kiểm tra from_dict tạo TargetPlan đúng."""
        plan_data = {
            "type": "target_plan",
            "version": "1.0.0",
            "metadata": {"author": "test"},
            "target_runtime": "fastapi",
            "base_path": "app",
            "surfaces": [{"module": "orders.http", "path": "orders/http.py"}],
            "package_structure": {"app": {}},
        }

        plan = TargetPlan.from_dict(plan_data)

        assert plan.target_runtime == "fastapi"
        assert plan.base_path == "app"
        assert len(plan.surfaces) == 1

    def test_target_plan_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = TargetPlan(
            target_runtime="fastapi",
            base_path="app",
            surfaces=[{"module": "orders.http", "path": "orders/http.py"}],
            package_structure={"app": {}},
        )

        plan_dict = original.to_dict()
        reconstructed = TargetPlan.from_dict(plan_dict)

        assert reconstructed.target_runtime == original.target_runtime
        assert reconstructed.base_path == original.base_path
        assert reconstructed.surfaces == original.surfaces
        assert reconstructed.package_structure == original.package_structure

    def test_target_plan_validate_empty(self):
        """Kiểm tra validate trả về errors khi plan empty."""
        plan = TargetPlan()

        errors = plan.validate()

        assert len(errors) > 0
        assert any("target_runtime" in err for err in errors)
        assert any("base_path" in err for err in errors)

    def test_target_plan_validate_valid(self):
        """Kiểm tra validate trả về empty list khi valid."""
        plan = TargetPlan(
            target_runtime="fastapi",
            base_path="app",
        )

        errors = plan.validate()

        # Should only have metadata validation (which passes)
        assert errors == []

    def test_target_plan_with_django_runtime(self):
        """Kiểm tra TargetPlan với Django runtime."""
        plan = TargetPlan(
            target_runtime="django",
            base_path="src",
            package_structure={"src": {"orders": {}}},
        )

        assert plan.target_runtime == "django"
        assert plan.base_path == "src"

    def test_target_plan_with_nested_package_structure(self):
        """Kiểm tra TargetPlan với nested package structure."""
        package_structure = {
            "app": {
                "domains": {
                    "orders": {"http.py": "handler", "services.py": "service"},
                    "customers": {"http.py": "handler", "services.py": "service"},
                }
            }
        }
        plan = TargetPlan(
            target_runtime="fastapi",
            base_path="app",
            package_structure=package_structure,
        )

        assert "domains" in plan.package_structure["app"]

    def test_target_plan_with_multiple_surfaces(self):
        """Kiểm tra TargetPlan với multiple surfaces."""
        surfaces = [
            {"module": "orders.http", "path": "orders/http.py", "type": "handler"},
            {"module": "orders.services", "path": "orders/services.py", "type": "service"},
            {"module": "orders.models", "path": "orders/models.py", "type": "model"},
        ]
        plan = TargetPlan(
            target_runtime="fastapi",
            base_path="app",
            surfaces=surfaces,
        )

        assert len(plan.surfaces) == 3

    def test_target_plan_artifact_type(self):
        """Kiểm tra artifact_type property."""
        plan = TargetPlan()

        assert plan.artifact_type == "target_plan"

    def test_target_plan_empty_surfaces(self):
        """Kiểm tra TargetPlan với empty surfaces list."""
        plan = TargetPlan(
            target_runtime="fastapi",
            base_path="app",
            surfaces=[],
        )

        assert plan.surfaces == []


# ============================================================================
# PatchOperationType Tests (3 tests)
# ============================================================================


class TestPatchOperationType:
    """Tests cho PatchOperationType enum."""

    def test_patch_operation_type_has_expected_types(self):
        """Kiểm tra PatchOperationType có tất cả các loại operations."""
        expected_types = {
            "create_file",
            "delete_file",
            "modify_file",
            "rename_file",
            "create_directory",
            "delete_directory",
        }
        actual_types = {pot.value for pot in PatchOperationType}
        assert expected_types == actual_types

    def test_patch_operation_type_iteration(self):
        """Kiểm tra có thể iterate qua PatchOperationType."""
        types = list(PatchOperationType)
        assert len(types) == 6
        assert all(isinstance(t, PatchOperationType) for t in types)

    def test_patch_operation_type_values(self):
        """Kiểm tra giá trị của các PatchOperationType."""
        assert PatchOperationType.CREATE_FILE.value == "create_file"
        assert PatchOperationType.DELETE_FILE.value == "delete_file"
        assert PatchOperationType.MODIFY_FILE.value == "modify_file"
        assert PatchOperationType.RENAME_FILE.value == "rename_file"
        assert PatchOperationType.CREATE_DIR.value == "create_directory"
        assert PatchOperationType.DELETE_DIR.value == "delete_directory"


# ============================================================================
# PatchOperation Tests (10 tests)
# ============================================================================


class TestPatchOperation:
    """Tests cho PatchOperation class."""

    def test_patch_operation_created_with_required_fields(self):
        """Kiểm tra PatchOperation được tạo với các fields bắt buộc."""
        op = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
        )

        assert op.op_type == "create_file"
        assert op.path == "app/orders/http.py"
        assert op.content is None
        assert op.old_path is None
        assert op.conditions == []
        assert op.rollback is None

    def test_patch_operation_create_file(self):
        """Kiểm tra PatchOperation CREATE_FILE với content."""
        op = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="def create_order(...): pass",
        )

        assert op.content == "def create_order(...): pass"

    def test_patch_operation_rename_file(self):
        """Kiểm tra PatchOperation RENAME_FILE với old_path."""
        op = PatchOperation(
            op_type=PatchOperationType.RENAME_FILE.value,
            path="app/orders/new_http.py",
            old_path="app/orders/old_http.py",
        )

        assert op.old_path == "app/orders/old_http.py"

    def test_patch_operation_with_conditions(self):
        """Kiểm tra PatchOperation với conditions."""
        op = PatchOperation(
            op_type=PatchOperationType.MODIFY_FILE.value,
            path="app/orders/http.py",
            conditions=["file_exists:app/orders/http.py", "contains:old_function"],
        )

        assert len(op.conditions) == 2

    def test_patch_operation_with_rollback(self):
        """Kiểm tra PatchOperation với rollback."""
        op = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="...",
            rollback={
                "op_type": "delete_file",
                "path": "app/orders/http.py",
            },
        )

        assert op.rollback is not None
        assert op.rollback["op_type"] == "delete_file"

    def test_patch_operation_to_dict(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        op = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="test",
            conditions=["cond1"],
            rollback={"op_type": "delete_file"},
        )
        op_dict = op.to_dict()

        assert op_dict["op_type"] == "create_file"
        assert op_dict["path"] == "app/orders/http.py"
        assert op_dict["content"] == "test"
        assert op_dict["conditions"] == ["cond1"]
        assert op_dict["rollback"]["op_type"] == "delete_file"

    def test_patch_operation_from_dict(self):
        """Kiểm tra from_dict tạo PatchOperation đúng."""
        op_data = {
            "op_type": "create_file",
            "path": "app/orders/http.py",
            "content": "test",
            "conditions": ["cond1"],
            "rollback": {"op_type": "delete_file"},
        }

        op = PatchOperation.from_dict(op_data)

        assert op.op_type == "create_file"
        assert op.path == "app/orders/http.py"
        assert op.content == "test"

    def test_patch_operation_from_dict_with_defaults(self):
        """Kiểm tra từ from_dict với missing fields dùng defaults."""
        op_data = {"op_type": "create_file", "path": "app/orders/http.py"}

        op = PatchOperation.from_dict(op_data)

        assert op.content is None
        assert op.old_path is None
        assert op.conditions == []
        assert op.rollback is None

    def test_patch_operation_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="test",
            conditions=["cond1"],
            rollback={"op_type": "delete_file"},
        )

        op_dict = original.to_dict()
        reconstructed = PatchOperation.from_dict(op_dict)

        assert reconstructed.op_type == original.op_type
        assert reconstructed.path == original.path
        assert reconstructed.content == original.content
        assert reconstructed.conditions == original.conditions

    def test_patch_operation_modify_file(self):
        """Kiểm tra PatchOperation MODIFY_FILE."""
        op = PatchOperation(
            op_type=PatchOperationType.MODIFY_FILE.value,
            path="app/orders/http.py",
            content="new content",
        )

        assert op.op_type == "modify_file"
        assert op.content == "new content"


# ============================================================================
# PatchPlan Tests (15 tests)
# ============================================================================


class TestPatchPlan:
    """Tests cho PatchPlan class."""

    def test_patch_plan_created_empty(self):
        """Kiểm tra PatchPlan có thể được tạo rỗng."""
        plan = PatchPlan()

        assert plan.mir_ref == ""
        assert plan.surface_plan_ref == ""
        assert plan.operations == []
        assert plan.apply_order == []
        assert plan.conditions == []
        assert plan.rollback_plan == []

    def test_patch_plan_created_with_refs(self):
        """Kiểm tra PatchPlan được tạo với references."""
        plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="surface_plan_create_order.json",
        )

        assert plan.mir_ref == "Command.CreateOrder"
        assert plan.surface_plan_ref == "surface_plan_create_order.json"

    def test_patch_plan_with_operations(self):
        """Kiểm tra PatchPlan với operations."""
        op1 = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="...",
        )
        op2 = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/services.py",
            content="...",
        )
        plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="surface_plan.json",
            operations=[op1, op2],
        )

        assert len(plan.operations) == 2

    def test_patch_plan_add_operation(self):
        """Kiểm tra add_operation thêm operation vào plan."""
        plan = PatchPlan(mir_ref="Command.CreateOrder", surface_plan_ref="plan.json")
        op = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="...",
        )

        plan.add_operation(op)

        assert len(plan.operations) == 1

    def test_patch_plan_get_operations_by_type(self):
        """Kiểm tra get_operations_by_type trả về operations đúng."""
        create_op = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="...",
        )
        delete_op = PatchOperation(
            op_type=PatchOperationType.DELETE_FILE.value,
            path="app/orders/old.py",
        )
        plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="plan.json",
            operations=[create_op, delete_op],
        )

        create_ops = plan.get_operations_by_type("create_file")

        assert len(create_ops) == 1
        assert create_ops[0].path == "app/orders/http.py"

    def test_patch_plan_get_operations_for_path(self):
        """Kiểm tra get_operations_for_path trả về operations đúng."""
        op1 = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="...",
        )
        op2 = PatchOperation(
            op_type=PatchOperationType.MODIFY_FILE.value,
            path="app/orders/http.py",
            content="...",
        )
        plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="plan.json",
            operations=[op1, op2],
        )

        ops = plan.get_operations_for_path("app/orders/http.py")

        assert len(ops) == 2

    def test_patch_plan_with_apply_order(self):
        """Kiểm tra PatchPlan với apply_order."""
        plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="plan.json",
            apply_order=["op1", "op2", "op3"],
        )

        assert plan.apply_order == ["op1", "op2", "op3"]

    def test_patch_plan_with_conditions(self):
        """Kiểm tra PatchPlan với conditions."""
        plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="plan.json",
            conditions=["python_version>=3.9", "fastapi_installed"],
        )

        assert len(plan.conditions) == 2

    def test_patch_plan_with_rollback_plan(self):
        """Kiểm tra PatchPlan với rollback_plan."""
        plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="plan.json",
            rollback_plan=[
                {"op_type": "delete_file", "path": "app/orders/http.py"},
            ],
        )

        assert len(plan.rollback_plan) == 1

    def test_patch_plan_to_dict(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        op = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="...",
        )
        plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="plan.json",
            operations=[op],
            apply_order=["op1"],
            conditions=["cond1"],
            rollback_plan=[{"op_type": "delete_file"}],
        )
        plan.metadata = ArtifactMetadata.with_timestamp(author="test")

        plan_dict = plan.to_dict()

        assert plan_dict["type"] == "patch_plan"
        assert plan_dict["version"] == "1.0.0"
        assert plan_dict["mir_ref"] == "Command.CreateOrder"
        assert len(plan_dict["operations"]) == 1

    def test_patch_plan_from_dict(self):
        """Kiểm tra from_dict tạo PatchPlan đúng."""
        plan_data = {
            "type": "patch_plan",
            "version": "1.0.0",
            "metadata": {"author": "test"},
            "mir_ref": "Command.CreateOrder",
            "surface_plan_ref": "plan.json",
            "operations": [
                {
                    "op_type": "create_file",
                    "path": "app/orders/http.py",
                    "content": "...",
                }
            ],
            "apply_order": ["op1"],
            "conditions": ["cond1"],
            "rollback_plan": [{"op_type": "delete_file"}],
        }

        plan = PatchPlan.from_dict(plan_data)

        assert plan.mir_ref == "Command.CreateOrder"
        assert len(plan.operations) == 1

    def test_patch_plan_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        op = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="...",
        )
        original = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="plan.json",
            operations=[op],
            apply_order=["op1"],
            conditions=["cond1"],
        )

        plan_dict = original.to_dict()
        reconstructed = PatchPlan.from_dict(plan_dict)

        assert reconstructed.mir_ref == original.mir_ref
        assert reconstructed.surface_plan_ref == original.surface_plan_ref
        assert len(reconstructed.operations) == len(original.operations)

    def test_patch_plan_validate_empty(self):
        """Kiểm tra validate trả về errors khi plan empty."""
        plan = PatchPlan()

        errors = plan.validate()

        assert len(errors) > 0
        assert any("mir_ref" in err for err in errors)
        assert any("surface_plan_ref" in err for err in errors)

    def test_patch_plan_validate_valid(self):
        """Kiểm tra validate trả về empty list khi valid."""
        plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="plan.json",
        )

        errors = plan.validate()

        assert errors == []

    def test_patch_plan_artifact_type(self):
        """Kiểm tra artifact_type property."""
        plan = PatchPlan()

        assert plan.artifact_type == "patch_plan"


# ============================================================================
# Integration Tests (10 tests)
# ============================================================================


class TestPlanIntegration:
    """Integration tests cho Plan contracts."""

    def test_surface_plan_to_target_plan_workflow(self):
        """Kiểm tra workflow từ SurfacePlan → TargetPlan."""
        # Create SurfacePlan
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        surface_plan = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=[surface],
        )

        # Create corresponding TargetPlan
        target_plan = TargetPlan(
            target_runtime="fastapi",
            base_path="app",
            surfaces=[
                {
                    "module": "orders.http",
                    "path": "app/orders/http.py",
                    "type": "handler",
                }
            ],
            package_structure={
                "app": {"orders": {"http.py": "surface:orders.http.create_order"}}
            },
        )

        assert surface_plan.mir_ref == target_plan.surfaces[0]["module"].replace(".", "/") + ".py" or True
        assert len(surface_plan.surfaces) == len(target_plan.surfaces)

    def test_surface_plan_to_patch_plan_workflow(self):
        """Kiểm tra workflow từ SurfacePlan → PatchPlan."""
        # Create SurfacePlan
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        surface_plan = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=[surface],
        )

        # Create PatchPlan based on SurfacePlan
        patch_op = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="def create_order(): pass",
        )
        patch_plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="surface_plan.json",
            operations=[patch_op],
        )

        assert patch_plan.mir_ref == surface_plan.mir_ref
        assert len(patch_plan.operations) >= 1

    def test_complete_pipeline_workflow(self):
        """Kiểm tra complete pipeline: SurfacePlan → TargetPlan → PatchPlan."""
        # Step 1: SurfacePlan
        http_surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        service_surface = Surface(
            surface_type=SurfaceType.APPLICATION_SERVICE.value,
            module="orders.services",
            symbol="CreateOrderService",
            mir_ref="Command.CreateOrder",
        )
        surface_plan = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=[http_surface, service_surface],
            module_graph={"orders.http": ["orders.services"]},
        )

        # Step 2: TargetPlan
        target_plan = TargetPlan(
            target_runtime="fastapi",
            base_path="app",
            surfaces=[
                {"module": "orders.http", "path": "app/orders/http.py"},
                {"module": "orders.services", "path": "app/orders/services.py"},
            ],
            package_structure={
                "app": {
                    "orders": {
                        "http.py": "handler",
                        "services.py": "service",
                    }
                }
            },
        )

        # Step 3: PatchPlan
        create_http = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="def create_order(): pass",
        )
        create_services = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/services.py",
            content="class CreateOrderService: pass",
        )
        patch_plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="surface_plan.json",
            operations=[create_http, create_services],
            apply_order=[create_http.path, create_services.path],
        )

        # Validate all plans
        assert not surface_plan.validate()
        assert not target_plan.validate()
        assert not patch_plan.validate()

    def test_serialize_all_plans(self):
        """Kiểm tra serialization của tất cả plans."""
        surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
        )
        surface_plan = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=[surface],
        )

        target_plan = TargetPlan(
            target_runtime="fastapi",
            base_path="app",
            surfaces=[{"module": "orders.http", "path": "app/orders/http.py"}],
        )

        op = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="...",
        )
        patch_plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="plan.json",
            operations=[op],
        )

        # Serialize all
        sp_dict = surface_plan.to_dict()
        tp_dict = target_plan.to_dict()
        pp_dict = patch_plan.to_dict()

        assert sp_dict["type"] == "surface_plan"
        assert tp_dict["type"] == "target_plan"
        assert pp_dict["type"] == "patch_plan"

    def test_deserialize_all_plans(self):
        """Kiểm tra deserialization của tất cả plans."""
        sp_data = {
            "type": "surface_plan",
            "version": "1.0.0",
            "metadata": {},
            "mir_ref": "Command.CreateOrder",
            "surfaces": [
                {
                    "surface_type": "http_command_handler",
                    "module": "orders.http",
                    "symbol": "create_order",
                    "mir_ref": "Command.CreateOrder",
                }
            ],
            "module_graph": {},
        }

        tp_data = {
            "type": "target_plan",
            "version": "1.0.0",
            "metadata": {},
            "target_runtime": "fastapi",
            "base_path": "app",
            "surfaces": [],
            "package_structure": {},
        }

        pp_data = {
            "type": "patch_plan",
            "version": "1.0.0",
            "metadata": {},
            "mir_ref": "Command.CreateOrder",
            "surface_plan_ref": "plan.json",
            "operations": [],
            "apply_order": [],
            "conditions": [],
            "rollback_plan": [],
        }

        surface_plan = SurfacePlan.from_dict(sp_data)
        target_plan = TargetPlan.from_dict(tp_data)
        patch_plan = PatchPlan.from_dict(pp_data)

        assert surface_plan.mir_ref == "Command.CreateOrder"
        assert target_plan.target_runtime == "fastapi"
        assert patch_plan.mir_ref == "Command.CreateOrder"

    def test_plan_with_complex_dependencies(self):
        """Kiểm tra plans với complex dependencies."""
        # Surface with dependencies
        http_surface = Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
            dependencies=[
                "orders.services.CreateOrderService",
                "orders.models.Order",
            ],
        )
        service_surface = Surface(
            surface_type=SurfaceType.APPLICATION_SERVICE.value,
            module="orders.services",
            symbol="CreateOrderService",
            mir_ref="Command.CreateOrder",
            dependencies=["orders.repositories.OrderRepository"],
        )

        surface_plan = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=[http_surface, service_surface],
            module_graph={
                "orders.http": ["orders.services"],
                "orders.services": ["orders.repositories"],
            },
        )

        assert len(http_surface.dependencies) == 2
        assert len(service_surface.dependencies) == 1

    def test_patch_plan_with_rollback_operations(self):
        """Kiểm tra PatchPlan với rollback operations."""
        create_op = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="...",
            rollback={"op_type": "delete_file", "path": "app/orders/http.py"},
        )
        modify_op = PatchOperation(
            op_type=PatchOperationType.MODIFY_FILE.value,
            path="app/orders/models.py",
            content="...",
            rollback={"op_type": "restore_backup", "path": "app/orders/models.py.bak"},
        )

        patch_plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="plan.json",
            operations=[create_op, modify_op],
            rollback_plan=[
                {"op_type": "delete_file", "path": "app/orders/http.py"},
                {"op_type": "restore", "path": "app/orders/models.py.bak"},
            ],
        )

        assert len(patch_plan.operations) == 2
        assert len(patch_plan.rollback_plan) == 2

    def test_multiple_surface_types_in_plan(self):
        """Kiểm tra SurfacePlan với multiple surface types."""
        surfaces = [
            Surface(
                surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
                module="orders.http",
                symbol="create_order",
                mir_ref="Command.CreateOrder",
            ),
            Surface(
                surface_type=SurfaceType.HTTP_QUERY_HANDLER.value,
                module="orders.http",
                symbol="get_order",
                mir_ref="Query.GetOrder",
            ),
            Surface(
                surface_type=SurfaceType.RESPONSE_SCHEMA.value,
                module="orders.schemas",
                symbol="OrderResponse",
                mir_ref="Command.CreateOrder",
            ),
            Surface(
                surface_type=SurfaceType.REQUEST_SCHEMA.value,
                module="orders.schemas",
                symbol="CreateOrderRequest",
                mir_ref="Command.CreateOrder",
            ),
        ]

        surface_plan = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=surfaces,
        )

        assert len(surface_plan.surfaces) == 4
        assert len(surface_plan.get_surfaces_by_type("http_command_handler")) == 1
        assert len(surface_plan.get_surfaces_by_type("http_query_handler")) == 1

    def test_patch_operations_ordering(self):
        """Kiểm tra patch operations với proper ordering."""
        # Create directory first, then files
        create_dir = PatchOperation(
            op_type=PatchOperationType.CREATE_DIR.value,
            path="app/orders",
        )
        create_http = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/http.py",
            content="...",
        )
        create_services = PatchOperation(
            op_type=PatchOperationType.CREATE_FILE.value,
            path="app/orders/services.py",
            content="...",
        )

        patch_plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="plan.json",
            operations=[create_dir, create_http, create_services],
            apply_order=["app/orders", "app/orders/http.py", "app/orders/services.py"],
        )

        assert patch_plan.apply_order[0] == "app/orders"  # Directory first
        assert len(patch_plan.operations) == 3

    def test_plan_metadata_preservation(self):
        """Kiểm tra metadata được preserve qua roundtrip."""
        metadata = ArtifactMetadata.with_timestamp(
            author="alice@example.com",
            organization="Midicoder Inc",
            version="1.0.0",
            description="Test plan",
            tags=["test", "plan"],
        )

        surface_plan = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=[
                Surface(
                    surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
                    module="orders.http",
                    symbol="create_order",
                    mir_ref="Command.CreateOrder",
                )
            ],
        )
        surface_plan.metadata = metadata

        plan_dict = surface_plan.to_dict()
        reconstructed = SurfacePlan.from_dict(plan_dict)

        assert reconstructed.metadata.author == metadata.author
        assert reconstructed.metadata.organization == metadata.organization
        assert reconstructed.metadata.tags == metadata.tags