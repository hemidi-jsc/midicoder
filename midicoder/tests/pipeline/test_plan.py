"""
Tests cho Implementation Plan Module.

Test cases cho typed data structures trong midicoder/pipeline/plan.py:
- FileSpec tests
- ModuleSpec tests
- ImplementationPlan tests
- Serialization tests
- Hash determinism tests

TDD: Tests được viết trước implementation.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
import json
from datetime import datetime, timezone
from midicoder.pipeline.plan import FileSpec, ModuleSpec, ImplementationPlan


# ============================================================================
# FileSpec Tests
# ============================================================================

class TestFileSpec:
    """Test cases cho FileSpec dataclass."""

    def test_file_spec_creation_default_values(self):
        """Test tạo FileSpec với default values."""
        spec = FileSpec(
            path="app/models/order.py",
            file_type="model",
            template="fastapi/model.py.jinja2"
        )
        
        assert spec.path == "app/models/order.py"
        assert spec.file_type == "model"
        assert spec.template == "fastapi/model.py.jinja2"
        assert spec.context == {}
        assert spec.dependencies == []
        assert spec.metadata == {}

    def test_file_spec_creation_custom_values(self):
        """Test tạo FileSpec với custom values."""
        spec = FileSpec(
            path="app/routes/order.py",
            file_type="route",
            template="fastapi/routes.py.jinja2",
            context={"entity": {"id": "Order", "name": "Đơn hàng"}},
            dependencies=["app/models/order.py", "app/schemas/order.py"],
            metadata={"generated": True}
        )
        
        assert spec.path == "app/routes/order.py"
        assert spec.file_type == "route"
        assert spec.context["entity"]["id"] == "Order"
        assert len(spec.dependencies) == 2
        assert spec.metadata["generated"] is True

    def test_file_spec_to_dict(self):
        """Test FileSpec.to_dict() method."""
        spec = FileSpec(
            path="app/models/order.py",
            file_type="model",
            template="fastapi/model.py.jinja2",
            context={"entity": {"id": "Order"}},
            dependencies=["app/config.py"],
            metadata={"version": "1.0.0"}
        )
        
        result = spec.to_dict()
        
        assert result["path"] == "app/models/order.py"
        assert result["file_type"] == "model"
        assert result["template"] == "fastapi/model.py.jinja2"
        assert result["context"]["entity"]["id"] == "Order"
        assert "app/config.py" in result["dependencies"]
        assert result["metadata"]["version"] == "1.0.0"

    def test_file_spec_from_dict(self):
        """Test FileSpec.from_dict() method."""
        data = {
            "path": "app/services/order_service.py",
            "file_type": "service",
            "template": "fastapi/service.py.jinja2",
            "context": {"entity": {"id": "Order"}},
            "dependencies": ["app/models/order.py"],
            "metadata": {"test": True}
        }
        
        spec = FileSpec.from_dict(data)
        
        assert isinstance(spec, FileSpec)
        assert spec.path == "app/services/order_service.py"
        assert spec.file_type == "service"
        assert spec.context == {"entity": {"id": "Order"}}
        assert len(spec.dependencies) == 1
        assert spec.metadata["test"] is True

    def test_file_spec_from_dict_with_defaults(self):
        """Test FileSpec.from_dict() với missing optional fields."""
        data = {
            "path": "app/main.py",
            "file_type": "main",
            "template": "fastapi/main.py.jinja2"
        }
        
        spec = FileSpec.from_dict(data)
        
        assert spec.context == {}
        assert spec.dependencies == []
        assert spec.metadata == {}


# ============================================================================
# ModuleSpec Tests
# ============================================================================

class TestModuleSpec:
    """Test cases cho ModuleSpec dataclass."""

    def test_module_spec_creation_default_values(self):
        """Test tạo ModuleSpec với default values."""
        module = ModuleSpec(
            name="orders",
            module_type="backend"
        )
        
        assert module.name == "orders"
        assert module.module_type == "backend"
        assert module.files == []
        assert module.dependencies == []
        assert module.metadata == {}

    def test_module_spec_creation_with_files(self):
        """Test tạo ModuleSpec với files và dependencies."""
        files = [
            FileSpec(
                path="app/models/order.py",
                file_type="model",
                template="fastapi/model.py.jinja2"
            ),
            FileSpec(
                path="app/routes/order.py",
                file_type="route",
                template="fastapi/routes.py.jinja2"
            )
        ]
        
        module = ModuleSpec(
            name="orders",
            module_type="backend",
            files=files,
            dependencies=["auth", "users"],
            metadata={"priority": 1}
        )
        
        assert len(module.files) == 2
        assert "auth" in module.dependencies
        assert "users" in module.dependencies
        assert module.metadata["priority"] == 1

    def test_module_spec_to_dict(self):
        """Test ModuleSpec.to_dict() method."""
        files = [
            FileSpec(
                path="app/models/order.py",
                file_type="model",
                template="fastapi/model.py.jinja2"
            )
        ]
        
        module = ModuleSpec(
            name="orders",
            module_type="backend",
            files=files,
            dependencies=["auth"]
        )
        
        result = module.to_dict()
        
        assert result["name"] == "orders"
        assert result["module_type"] == "backend"
        assert len(result["files"]) == 1
        assert result["files"][0]["path"] == "app/models/order.py"
        assert "auth" in result["dependencies"]

    def test_module_spec_from_dict(self):
        """Test ModuleSpec.from_dict() method."""
        data = {
            "name": "users",
            "module_type": "backend",
            "files": [
                {
                    "path": "app/models/user.py",
                    "file_type": "model",
                    "template": "fastapi/model.py.jinja2"
                }
            ],
            "dependencies": ["auth"],
            "metadata": {}
        }
        
        module = ModuleSpec.from_dict(data)
        
        assert isinstance(module, ModuleSpec)
        assert module.name == "users"
        assert module.module_type == "backend"
        assert len(module.files) == 1
        assert isinstance(module.files[0], FileSpec)
        assert module.files[0].path == "app/models/user.py"
        assert "auth" in module.dependencies

    def test_module_spec_from_dict_with_defaults(self):
        """Test ModuleSpec.from_dict() với missing optional fields."""
        data = {
            "name": "core",
            "module_type": "backend"
        }
        
        module = ModuleSpec.from_dict(data)
        
        assert module.files == []
        assert module.dependencies == []
        assert module.metadata == {}


# ============================================================================
# ImplementationPlan Tests
# ============================================================================

class TestImplementationPlan:
    """Test cases cho ImplementationPlan dataclass."""

    def test_implementation_plan_creation(self):
        """Test tạo ImplementationPlan."""
        plan = ImplementationPlan()
        
        assert plan.meta == {}
        assert plan.modules == []

    def test_implementation_plan_creation_with_meta(self):
        """Test tạo ImplementationPlan với metadata."""
        plan = ImplementationPlan(
            meta={
                "version": "1.0.0",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "target": "all"
            }
        )
        
        assert plan.meta["version"] == "1.0.0"
        assert plan.meta["target"] == "all"
        assert "created_at" in plan.meta

    def test_implementation_plan_add_module(self):
        """Test ImplementationPlan.add_module() method."""
        plan = ImplementationPlan()
        
        module = ModuleSpec(
            name="orders",
            module_type="backend",
            files=[
                FileSpec(
                    path="app/models/order.py",
                    file_type="model",
                    template="fastapi/model.py.jinja2"
                )
            ]
        )
        
        plan.add_module(module)
        
        assert len(plan.modules) == 1
        assert plan.modules[0].name == "orders"

    def test_implementation_plan_to_dict(self):
        """Test ImplementationPlan.to_dict() method."""
        plan = ImplementationPlan(
            meta={"version": "1.0.0", "target": "backend"},
            modules=[
                ModuleSpec(
                    name="orders",
                    module_type="backend",
                    files=[
                        FileSpec(
                            path="app/models/order.py",
                            file_type="model",
                            template="fastapi/model.py.jinja2"
                        )
                    ]
                )
            ]
        )
        
        result = plan.to_dict()
        
        assert result["meta"]["version"] == "1.0.0"
        assert result["meta"]["target"] == "backend"
        assert len(result["modules"]) == 1
        assert result["modules"][0]["name"] == "orders"

    def test_implementation_plan_from_dict(self):
        """Test ImplementationPlan.from_dict() method."""
        data = {
            "meta": {"version": "1.0.0", "target": "all"},
            "modules": [
                {
                    "name": "orders",
                    "module_type": "backend",
                    "files": [
                        {
                            "path": "app/models/order.py",
                            "file_type": "model",
                            "template": "fastapi/model.py.jinja2"
                        }
                    ],
                    "dependencies": [],
                    "metadata": {}
                }
            ]
        }
        
        plan = ImplementationPlan.from_dict(data)
        
        assert isinstance(plan, ImplementationPlan)
        assert plan.meta["version"] == "1.0.0"
        assert len(plan.modules) == 1
        assert isinstance(plan.modules[0], ModuleSpec)
        assert plan.modules[0].name == "orders"

    def test_implementation_plan_to_json(self):
        """Test ImplementationPlan.to_json() method."""
        plan = ImplementationPlan(
            meta={"version": "1.0.0"},
            modules=[
                ModuleSpec(
                    name="orders",
                    module_type="backend",
                    files=[
                        FileSpec(
                            path="app/models/order.py",
                            file_type="model",
                            template="fastapi/model.py.jinja2"
                        )
                    ]
                )
            ]
        )
        
        json_str = plan.to_json()
        
        # Verify valid JSON
        parsed = json.loads(json_str)
        assert parsed["meta"]["version"] == "1.0.0"
        assert len(parsed["modules"]) == 1

    def test_implementation_plan_from_json(self):
        """Test ImplementationPlan.from_json() method."""
        json_str = json.dumps({
            "meta": {"version": "1.0.0"},
            "modules": [
                {
                    "name": "users",
                    "module_type": "backend",
                    "files": [
                        {
                            "path": "app/models/user.py",
                            "file_type": "model",
                            "template": "fastapi/model.py.jinja2"
                        }
                    ],
                    "dependencies": [],
                    "metadata": {}
                }
            ]
        })
        
        plan = ImplementationPlan.from_json(json_str)
        
        assert isinstance(plan, ImplementationPlan)
        assert plan.meta["version"] == "1.0.0"
        assert plan.modules[0].name == "users"

    def test_implementation_plan_compute_hash_deterministic(self):
        """Test compute_hash() trả về deterministic hash."""
        plan = ImplementationPlan(
            meta={"version": "1.0.0"},
            modules=[
                ModuleSpec(
                    name="orders",
                    module_type="backend",
                    files=[
                        FileSpec(
                            path="app/models/order.py",
                            file_type="model",
                            template="fastapi/model.py.jinja2"
                        )
                    ]
                )
            ]
        )
        
        hash1 = plan.compute_hash()
        hash2 = plan.compute_hash()
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_implementation_plan_compute_hash_different_content(self):
        """Test compute_hash() khác nhau với content khác nhau."""
        plan1 = ImplementationPlan(
            meta={"version": "1.0.0"},
            modules=[
                ModuleSpec(
                    name="orders",
                    module_type="backend",
                    files=[]
                )
            ]
        )
        
        plan2 = ImplementationPlan(
            meta={"version": "1.0.0"},
            modules=[
                ModuleSpec(
                    name="users",
                    module_type="backend",
                    files=[]
                )
            ]
        )
        
        hash1 = plan1.compute_hash()
        hash2 = plan2.compute_hash()
        
        assert hash1 != hash2

    def test_implementation_plan_get_files_by_type(self):
        """Test get_files_by_type() method."""
        plan = ImplementationPlan(
            modules=[
                ModuleSpec(
                    name="orders",
                    module_type="backend",
                    files=[
                        FileSpec(
                            path="app/models/order.py",
                            file_type="model",
                            template="fastapi/model.py.jinja2"
                        ),
                        FileSpec(
                            path="app/routes/order.py",
                            file_type="route",
                            template="fastapi/routes.py.jinja2"
                        )
                    ]
                )
            ]
        )
        
        models = plan.get_files_by_type("model")
        routes = plan.get_files_by_type("route")
        
        assert len(models) == 1
        assert models[0].path == "app/models/order.py"
        assert len(routes) == 1
        assert routes[0].path == "app/routes/order.py"

    def test_implementation_plan_get_modules_by_type(self):
        """Test get_modules_by_type() method."""
        plan = ImplementationPlan(
            modules=[
                ModuleSpec(
                    name="orders",
                    module_type="backend",
                    files=[]
                ),
                ModuleSpec(
                    name="frontend",
                    module_type="frontend",
                    files=[]
                ),
                ModuleSpec(
                    name="infra",
                    module_type="infra",
                    files=[]
                )
            ]
        )
        
        backend_modules = plan.get_modules_by_type("backend")
        frontend_modules = plan.get_modules_by_type("frontend")
        
        assert len(backend_modules) == 1
        assert backend_modules[0].name == "orders"
        assert len(frontend_modules) == 1
        assert frontend_modules[0].name == "frontend"

    def test_implementation_plan_count_files(self):
        """Test count_files() method."""
        plan = ImplementationPlan(
            modules=[
                ModuleSpec(
                    name="orders",
                    module_type="backend",
                    files=[
                        FileSpec(path="a.py", file_type="model", template="t"),
                        FileSpec(path="b.py", file_type="route", template="t"),
                    ]
                ),
                ModuleSpec(
                    name="users",
                    module_type="backend",
                    files=[
                        FileSpec(path="c.py", file_type="model", template="t"),
                    ]
                ),
                ModuleSpec(
                    name="frontend",
                    module_type="frontend",
                    files=[
                        FileSpec(path="d.ts", file_type="component", template="t"),
                    ]
                )
            ]
        )
        
        counts = plan.count_files()
        
        assert counts["backend"] == 3
        assert counts["frontend"] == 1
        assert counts["infra"] == 0


# ============================================================================
# Integration Tests (Round-trip)
# ============================================================================

class TestPlanIntegration:
    """Integration tests cho Implementation Plan."""

    def test_plan_round_trip_json(self):
        """Test full round-trip: Plan → JSON → Plan."""
        original_plan = ImplementationPlan(
            meta={
                "version": "1.0.0",
                "created_at": "2026-04-27T10:00:00Z",
                "target": "all"
            },
            modules=[
                ModuleSpec(
                    name="orders",
                    module_type="backend",
                    files=[
                        FileSpec(
                            path="app/models/order.py",
                            file_type="model",
                            template="fastapi/model.py.jinja2",
                            context={"entity": {"id": "Order"}},
                            dependencies=[],
                            metadata={}
                        ),
                        FileSpec(
                            path="app/routes/order.py",
                            file_type="route",
                            template="fastapi/routes.py.jinja2",
                            context={"entity": {"id": "Order"}},
                            dependencies=["app/models/order.py"],
                            metadata={}
                        )
                    ],
                    dependencies=["auth"],
                    metadata={"priority": 1}
                ),
                ModuleSpec(
                    name="frontend-orders",
                    module_type="frontend",
                    files=[
                        FileSpec(
                            path="src/app/orders/orders.component.ts",
                            file_type="component",
                            template="angular/component.ts.jinja2",
                            context={"entity": {"id": "Order"}},
                            dependencies=[],
                            metadata={}
                        )
                    ],
                    dependencies=[],
                    metadata={}
                )
            ]
        )
        
        # Serialize to JSON
        json_str = original_plan.to_json()
        
        # Deserialize from JSON
        restored_plan = ImplementationPlan.from_json(json_str)
        
        # Verify structure
        assert restored_plan.meta["version"] == original_plan.meta["version"]
        assert restored_plan.meta["target"] == original_plan.meta["target"]
        assert len(restored_plan.modules) == len(original_plan.modules)
        
        # Verify modules
        assert restored_plan.modules[0].name == "orders"
        assert restored_plan.modules[0].module_type == "backend"
        assert len(restored_plan.modules[0].files) == 2
        
        assert restored_plan.modules[1].name == "frontend-orders"
        assert restored_plan.modules[1].module_type == "frontend"
        assert len(restored_plan.modules[1].files) == 1

    def test_hash_consistency_after_round_trip(self):
        """Test hash consistency sau round-trip JSON."""
        original_plan = ImplementationPlan(
            meta={"version": "1.0.0"},
            modules=[
                ModuleSpec(
                    name="orders",
                    module_type="backend",
                    files=[
                        FileSpec(
                            path="app/models/order.py",
                            file_type="model",
                            template="fastapi/model.py.jinja2"
                        )
                    ]
                )
            ]
        )
        
        original_hash = original_plan.compute_hash()
        
        # Round-trip through JSON
        json_str = original_plan.to_json()
        restored_plan = ImplementationPlan.from_json(json_str)
        restored_hash = restored_plan.compute_hash()
        
        # Hashes should be identical
        assert original_hash == restored_hash

    def test_complex_plan_round_trip(self):
        """Test round-trip với plan phức tạp hơn."""
        plan = ImplementationPlan(
            meta={
                "version": "1.0.0",
                "target": "all",
                "source_mir_hash": "abc123"
            },
            modules=[
                ModuleSpec(
                    name="core",
                    module_type="backend",
                    files=[
                        FileSpec(path="app/main.py", file_type="main", template="fastapi/main.py.jinja2"),
                        FileSpec(path="app/config.py", file_type="config", template="fastapi/config.py.jinja2"),
                    ],
                    dependencies=[],
                    metadata={}
                ),
                ModuleSpec(
                    name="auth",
                    module_type="backend",
                    files=[
                        FileSpec(path="app/models/user.py", file_type="model", template="fastapi/model.py.jinja2"),
                        FileSpec(path="app/routes/auth.py", file_type="route", template="fastapi/routes.py.jinja2"),
                    ],
                    dependencies=["core"],
                    metadata={}
                ),
                ModuleSpec(
                    name="orders",
                    module_type="backend",
                    files=[
                        FileSpec(path="app/models/order.py", file_type="model", template="fastapi/model.py.jinja2"),
                    ],
                    dependencies=["auth", "core"],
                    metadata={}
                ),
                ModuleSpec(
                    name="frontend",
                    module_type="frontend",
                    files=[
                        FileSpec(path="src/app/app.module.ts", file_type="module", template="angular/module.ts.jinja2"),
                    ],
                    dependencies=[],
                    metadata={}
                ),
                ModuleSpec(
                    name="infra",
                    module_type="infra",
                    files=[
                        FileSpec(path="docker-compose.yml", file_type="docker_compose", template="infra/docker-compose.yml.jinja2"),
                    ],
                    dependencies=[],
                    metadata={}
                )
            ]
        )
        
        json_str = plan.to_json()
        restored = ImplementationPlan.from_json(json_str)
        
        assert len(restored.modules) == 5
        assert restored.meta["source_mir_hash"] == "abc123"
        
        # Verify dependency structure preserved
        backend_modules = restored.get_modules_by_type("backend")
        assert len(backend_modules) == 3
        
        # Find orders module by name (more robust than index)
        orders_module = next(m for m in backend_modules if m.name == "orders")
        assert "auth" in orders_module.dependencies
        assert "core" in orders_module.dependencies


# ============================================================================
# Edge Cases
# ============================================================================

class TestPlanEdgeCases:
    """Test edge cases cho Implementation Plan."""

    def test_empty_plan(self):
        """Test plan rỗng."""
        plan = ImplementationPlan()
        
        json_str = plan.to_json()
        restored = ImplementationPlan.from_json(json_str)
        
        assert restored.meta == {}
        assert restored.modules == []

    def test_plan_with_special_characters_in_path(self):
        """Test path có special characters."""
        spec = FileSpec(
            path="app/features/order-items/order-item.model.py",
            file_type="model",
            template="fastapi/model.py.jinja2"
        )
        
        data = spec.to_dict()
        restored = FileSpec.from_dict(data)
        
        assert restored.path == spec.path

    def test_plan_with_unicode_in_context(self):
        """Test context có unicode (tiếng Việt)."""
        spec = FileSpec(
            path="app/models/order.py",
            file_type="model",
            template="fastapi/model.py.jinja2",
            context={"entity": {"id": "Order", "name": "Đơn hàng"}}
        )
        
        json_str = json.dumps(spec.to_dict(), ensure_ascii=False)
        data = json.loads(json_str)
        restored = FileSpec.from_dict(data)
        
        assert restored.context["entity"]["name"] == "Đơn hàng"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])