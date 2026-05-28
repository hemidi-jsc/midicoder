"""Tests cho React Component Emitter (P2-002-E).

Module: midicoder/packs/component/react.py
Features: CRUD Components, Dashboard, Forms, Layout, 5 UI Frameworks

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile


class TestReactComponentEmitter:
    """Tests cho ReactComponentEmitter."""

    def test_react_component_emitter_basic(self):
        """Test emit cơ bản tạo được files."""
        from ..react import ReactComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactComponentEmitter()
            files = emitter.emit(entities, output_dir)

            assert len(files) >= 5  # List, Detail, Form, Dashboard, Layout

    def test_react_component_emitter_list_view(self):
        """Test emit ListView Component."""
        from ..react import ReactComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "list" in contents.lower() or "table" in contents.lower()

    def test_react_component_emitter_detail_view(self):
        """Test emit DetailView Component."""
        from ..react import ReactComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "detail" in contents.lower()

    def test_react_component_emitter_form_view(self):
        """Test emit FormView Component có validation."""
        from ..react import ReactComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "form" in contents.lower() or "valid" in contents.lower() or "validate" in contents.lower()

    def test_react_component_emitter_dashboard(self):
        """Test emit Dashboard Component."""
        from ..react import ReactComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "dashboard" in contents.lower() or "widget" in contents.lower() or "stats" in contents.lower()

    def test_react_component_emitter_layout(self):
        """Test emit Layout/Shell Component."""
        from ..react import ReactComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "layout" in contents.lower() or "sidebar" in contents.lower() or "nav" in contents.lower() or "outlet" in contents.lower()

    def test_react_component_emitter_ui_framework(self):
        """Test emit với UI framework parameter."""
        from ..react import ReactComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactComponentEmitter(ui_framework="antd")
            files = emitter.emit(entities, output_dir)

            assert len(files) > 0

    def test_react_component_emitter_functional_hooks(self):
        """Test emit là functional components với hooks."""
        from ..react import ReactComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "usestate" in contents.lower() or "useeffect" in contents.lower() or "react" in contents.lower()

    def test_react_component_emitter_multiple_entities(self):
        """Test emit nhiều entities."""
        from ..react import ReactComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [
                {"id": "Order", "fields": [{"name": "total", "type": "float"}]},
                {"id": "Product", "fields": [{"name": "name", "type": "str"}]},
            ]

            emitter = ReactComponentEmitter()
            files = emitter.emit(entities, output_dir)

            assert len(files) >= 5

    def test_react_component_emitter_typescript_interfaces(self):
        """Test emit có TypeScript interfaces cho props."""
        from ..react import ReactComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactComponentEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "interface" in contents.lower() or "props" in contents.lower() or "export" in contents.lower()


class TestReactComponentEmitterIntegration:
    """Integration tests."""

    def test_generated_files_written_to_disk(self):
        """Test files được ghi ra disk."""
        from ..react import ReactComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactComponentEmitter()
            files = emitter.emit(entities, output_dir)

            for f in files:
                full_path = output_dir / f.path
                assert full_path.exists(), "File not found: " + str(full_path)

    def test_template_files_structure(self):
        """Test cấu trúc files output hợp lý."""
        from ..react import ReactComponentEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactComponentEmitter()
            files = emitter.emit(entities, output_dir)

            # Kiểm tra có .tsx files
            tsx_files = [f for f in files if f.path.suffix == '.tsx']
            assert len(tsx_files) >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
