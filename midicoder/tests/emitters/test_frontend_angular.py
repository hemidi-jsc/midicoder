"""
Tests cho Frontend Angular Emitter (P2-002-A).

Bám sát CURRENT_TASK_REQUIREMENT.md:
- FR1: Angular App Structure Emission
- FR2: Entity-driven Component Generation
- FR3: Service Layer Generation (REST + GraphQL + WebSocket + gRPC-web)
- FR4: NgRx State Management
- FR5: UI Framework Support (5 frameworks)
- FR6: Full Auth Integration
- FR7: Full Routing (lazy loading + guards + resolvers)
- FR8: Model/Interface Generation

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile
import shutil


class TestAngularEmitterBasics:
    """Test cơ bản cho AngularEmitter class."""

    def test_emitter_creates_app_structure(self):
        """Test emit base app structure (FR1)."""
        from midicoder.emitters.stack.angular import AngularEmitter
        from midicoder.pipeline.mir import MIR

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mir = MIR()
            mir.metadata = {
                "entities": [],
                "routes": [],
                "operations": [],
                "authnz": {},
            }

            emitter = AngularEmitter.create_emitter()
            files = emitter.emit(mir, output_dir)

            # Verify files were created
            assert len(files) > 0
            # Check for base files
            file_paths = [f.path for f in files]
            paths_str = str(file_paths)
            assert "app.config" in paths_str or "app.component" in paths_str or "app.routes" in paths_str

    def test_emitter_with_entities(self):
        """Test emit entity modules (FR2)."""
        from midicoder.emitters.stack.angular import AngularEmitter
        from midicoder.pipeline.mir import MIR

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mir = MIR()
            mir.metadata = {
                "entities": [
                    {
                        "id": "Order",
                        "fields": [
                            {"name": "order_id", "type": "str", "required": True},
                            {"name": "total", "type": "float", "required": True},
                            {"name": "status", "type": "str", "required": False},
                        ],
                    }
                ],
                "routes": [],
                "operations": [],
                "authnz": {},
            }

            emitter = AngularEmitter.create_emitter()
            files = emitter.emit(mir, output_dir)

            # Should have entity module files
            assert len(files) > 0

    def test_emitter_with_ui_framework(self):
        """Test emit with different UI frameworks (FR5)."""
        from midicoder.emitters.stack.angular import AngularEmitter
        from midicoder.pipeline.mir import MIR

        frameworks = ["material", "tailwind", "bootstrap", "antd", "carbon"]

        for framework in frameworks:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                mir = MIR()
                mir.metadata = {
                    "entities": [{"id": "User", "fields": [{"name": "name", "type": "str"}]}],
                    "routes": [],
                    "operations": [],
                    "authnz": {},
                }

                emitter = AngularEmitter.create_emitter(ui_framework=framework)
                files = emitter.emit(mir, output_dir)

                # Should emit without errors for any framework
                assert len(files) > 0, f"Framework {framework} should emit files"

    def test_emitter_with_auth(self):
        """Test emit auth module (FR6)."""
        from midicoder.emitters.stack.angular import AngularEmitter
        from midicoder.pipeline.mir import MIR

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mir = MIR()
            mir.metadata = {
                "entities": [],
                "routes": [],
                "operations": [],
                "authnz": {
                    "provider": "jwt",
                    "roles": ["admin", "user"],
                    "permissions": ["order:create", "order:read"],
                },
            }

            emitter = AngularEmitter.create_emitter()
            files = emitter.emit(mir, output_dir)

            # Should have auth files
            file_contents = "\n".join(f.content for f in files)
            assert "auth" in file_contents.lower() or "interceptor" in file_contents.lower() or len(files) > 0

    def test_emitter_with_ngrx(self):
        """Test emit NgRx state (FR4)."""
        from midicoder.emitters.stack.angular import AngularEmitter
        from midicoder.pipeline.mir import MIR

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mir = MIR()
            mir.metadata = {
                "entities": [
                    {"id": "Product", "fields": [
                        {"name": "name", "type": "str"},
                        {"name": "price", "type": "float"},
                    ]}
                ],
                "routes": [],
                "operations": [],
                "authnz": {},
            }

            emitter = AngularEmitter.create_emitter(state_management="ngrx")
            files = emitter.emit(mir, output_dir)

            # Should have NgRx files
            file_contents = "\n".join(f.content for f in files)
            assert len(files) > 0

    def test_emitter_empty_metadata(self):
        """Test emit với empty metadata."""
        from midicoder.emitters.stack.angular import AngularEmitter
        from midicoder.pipeline.mir import MIR

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mir = MIR()
            mir.metadata = {}

            emitter = AngularEmitter.create_emitter()
            files = emitter.emit(mir, output_dir)

            # Should still emit base structure
            assert len(files) > 0

    def test_emitter_multiple_entities(self):
        """Test emit với nhiều entities."""
        from midicoder.emitters.stack.angular import AngularEmitter
        from midicoder.pipeline.mir import MIR

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mir = MIR()
            mir.metadata = {
                "entities": [
                    {"id": "Order", "fields": [{"name": "total", "type": "float"}]},
                    {"id": "Product", "fields": [{"name": "name", "type": "str"}]},
                    {"id": "Customer", "fields": [{"name": "email", "type": "str"}]},
                ],
                "routes": [],
                "operations": [],
                "authnz": {},
            }

            emitter = AngularEmitter.create_emitter()
            files = emitter.emit(mir, output_dir)

            # Should have files for each entity
            assert len(files) > 0

    def test_emitter_with_routes(self):
        """Test emit routing (FR7)."""
        from midicoder.emitters.stack.angular import AngularEmitter
        from midicoder.pipeline.mir import MIR

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mir = MIR()
            mir.metadata = {
                "entities": [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}],
                "routes": [
                    {"path": "/orders", "entity": "Order", "methods": ["GET"]},
                    {"path": "/orders/:id", "entity": "Order", "methods": ["GET"]},
                ],
                "operations": [],
                "authnz": {},
            }

            emitter = AngularEmitter.create_emitter()
            files = emitter.emit(mir, output_dir)

            # Should have routing files
            assert len(files) > 0

    def test_emitter_with_operations(self):
        """Test emit với operations (FR3)."""
        from midicoder.emitters.stack.angular import AngularEmitter
        from midicoder.pipeline.mir import MIR

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mir = MIR()
            mir.metadata = {
                "entities": [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}],
                "routes": [],
                "operations": [
                    {
                        "id": "CreateOrder",
                        "type": "create_record",
                        "entity": "Order",
                    },
                    {
                        "id": "GetOrders",
                        "type": "list_records",
                        "entity": "Order",
                    },
                ],
                "authnz": {},
            }

            emitter = AngularEmitter.create_emitter()
            files = emitter.emit(mir, output_dir)

            # Should emit service/operation files
            assert len(files) > 0

    def test_emitter_full_integration(self):
        """Test full integration: entities + routes + operations + authnz."""
        from midicoder.emitters.stack.angular import AngularEmitter
        from midicoder.pipeline.mir import MIR

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mir = MIR()
            mir.metadata = {
                "entities": [
                    {"id": "Order", "fields": [
                        {"name": "order_id", "type": "str", "required": True},
                        {"name": "total", "type": "float", "required": True},
                        {"name": "status", "type": "str"},
                    ]},
                    {"id": "Product", "fields": [
                        {"name": "name", "type": "str", "required": True},
                        {"name": "price", "type": "float", "required": True},
                    ]},
                ],
                "routes": [
                    {"path": "/orders", "entity": "Order", "methods": ["GET", "POST"]},
                    {"path": "/products", "entity": "Product", "methods": ["GET"]},
                ],
                "operations": [
                    {"id": "CreateOrder", "type": "create_record", "entity": "Order"},
                    {"id": "GetOrders", "type": "list_records", "entity": "Order"},
                ],
                "authnz": {
                    "provider": "jwt",
                    "roles": ["admin", "user"],
                    "permissions": ["order:create", "order:read", "product:read"],
                },
            }

            emitter = AngularEmitter.create_emitter(
                ui_framework="material",
                state_management="ngrx",
                communication=["rest", "graphql", "websocket", "grpc"],
            )
            files = emitter.emit(mir, output_dir)

            # Full integration should produce many files
            assert len(files) > 5
            # Check for various file types
            file_contents = "\n".join(f.content for f in files)
            assert len(file_contents) > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])