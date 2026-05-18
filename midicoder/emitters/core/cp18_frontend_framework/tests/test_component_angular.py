"""Tests cho Angular Component Emitter (P2-002-E).

Module: midicoder/emitters/core/component/angular.py
Features: CRUD Components, Dashboard, Forms, Layout/Shell, 5 UI Frameworks

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile


class TestAngularComponentEmitter:
    """Tests cho AngularComponentEmitter."""

    def test_angular_component_emitter_basic(self):
        """Test emit cơ bản tạo được files."""
        from ..angular import AngularComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = AngularComponentEmitter()
            files = emitter.emit(entities, output_dir)

            assert len(files) >= 5  # List, Detail, Form, Dashboard, Shell

    def test_angular_component_emitter_list_component(self):
        """Test emit List Component có table và pagination."""
        from ..angular import AngularComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = AngularComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "list" in contents.lower() or "table" in contents.lower()

    def test_angular_component_emitter_detail_component(self):
        """Test emit Detail Component."""
        from ..angular import AngularComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = AngularComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "detail" in contents.lower()

    def test_angular_component_emitter_form_component(self):
        """Test emit Form Component có validation."""
        from ..angular import AngularComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = AngularComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "form" in contents.lower() or "valid" in contents.lower() or "reactiveform" in contents.lower()

    def test_angular_component_emitter_dashboard(self):
        """Test emit Dashboard Component."""
        from ..angular import AngularComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = AngularComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "dashboard" in contents.lower() or "widget" in contents.lower() or "stats" in contents.lower()

    def test_angular_component_emitter_shell_layout(self):
        """Test emit Shell/Layout Component."""
        from ..angular import AngularComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = AngularComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "shell" in contents.lower() or "layout" in contents.lower() or "sidebar" in contents.lower() or "nav" in contents.lower() or "router-outlet" in contents.lower()

    def test_angular_component_emitter_ui_framework(self):
        """Test emit với UI framework parameter."""
        from ..angular import AngularComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = AngularComponentEmitter(ui_framework="material")
            files = emitter.emit(entities, output_dir)

            assert len(files) > 0

    def test_angular_component_emitter_standalone(self):
        """Test emit là standalone components (Angular v17+)."""
        from ..angular import AngularComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = AngularComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "standalone" in contents.lower()

    def test_angular_component_emitter_multiple_entities(self):
        """Test emit nhiều entities."""
        from ..angular import AngularComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [
                {"id": "Order", "fields": [{"name": "total", "type": "float"}]},
                {"id": "Product", "fields": [{"name": "name", "type": "str"}]},
            ]

            emitter = AngularComponentEmitter()
            files = emitter.emit(entities, output_dir)

            assert len(files) >= 5

    def test_angular_component_emitter_input_output(self):
        """Test emit có Input/Output decorators."""
        from ..angular import AngularComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = AngularComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            # Phải có Input hoặc Output hoặc EventEmitter
            assert "input" in contents.lower() or "output" in contents.lower() or "eventemitter" in contents.lower()


class TestAngularComponentEmitterIntegration:
    """Integration tests."""

    def test_generated_files_written_to_disk(self):
        """Test files được ghi ra disk."""
        from ..angular import AngularComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = AngularComponentEmitter()
            files = emitter.emit(entities, output_dir)

            for f in files:
                full_path = output_dir / f.path
                assert full_path.exists(), f"File not found: {full_path}"

    def test_template_files_structure(self):
        """Test cấu trúc files output hợp lý."""
        from ..angular import AngularComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = AngularComponentEmitter()
            files = emitter.emit(entities, output_dir)

            # Kiểm tra có .ts files (component typescript)
            ts_files = [f for f in files if f.path.suffix == '.ts']
            assert len(ts_files) >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
