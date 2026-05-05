"""Tests cho React Client Emitter (P2-002-D).

Module: midicoder/emitters/core/client/react.py
Features: RTK Query hooks, Pagination, Filtering, Caching, Error handling

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile


class TestReactClientEmitter:
    """Tests cho ReactClientEmitter."""

    def test_react_client_emitter_basic(self):
        """Test emit cơ bản."""
        from midicoder.emitters.core.client.react import ReactClientEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactClientEmitter()
            files = emitter.emit(entities, output_dir)

            assert len(files) > 0

    def test_react_client_emitter_pagination(self):
        """Test emit với pagination."""
        from midicoder.emitters.core.client.react import ReactClientEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Product", "fields": [{"name": "name", "type": "str"}]}]

            emitter = ReactClientEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "page" in contents.lower() or "limit" in contents.lower() or "paginated" in contents.lower()

    def test_react_client_emitter_filtering(self):
        """Test emit với filtering."""
        from midicoder.emitters.core.client.react import ReactClientEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "status", "type": "str"}]}]

            emitter = ReactClientEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "filter" in contents.lower()

    def test_react_client_emitter_caching(self):
        """Test emit với caching (RTK Query providesTags/invalidatesTags)."""
        from midicoder.emitters.core.client.react import ReactClientEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "User", "fields": [{"name": "email", "type": "str"}]}]

            emitter = ReactClientEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "providestags" in contents.lower() or "invalidatestags" in contents.lower() or "cache" in contents.lower() or "tag" in contents.lower()

    def test_react_client_emitter_error_handling(self):
        """Test emit với error handling."""
        from midicoder.emitters.core.client.react import ReactClientEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactClientEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "error" in contents.lower()

    def test_react_client_emitter_rtk_query(self):
        """Test emit có RTK Query hooks."""
        from midicoder.emitters.core.client.react import ReactClientEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactClientEmitter()
            files = emitter.emit(entities, output_dir)

            contents = "\n".join(f.content for f in files)
            assert "useget" in contents.lower() or "usecreate" in contents.lower() or "injectapi" in contents.lower()

    def test_react_client_emitter_multiple_entities(self):
        """Test emit nhiều entities."""
        from midicoder.emitters.core.client.react import ReactClientEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [
                {"id": "Order", "fields": [{"name": "total", "type": "float"}]},
                {"id": "Product", "fields": [{"name": "name", "type": "str"}]},
            ]

            emitter = ReactClientEmitter()
            files = emitter.emit(entities, output_dir)

            assert len(files) > 0


class TestReactClientEmitterIntegration:
    """Integration tests."""

    def test_generated_files_written_to_disk(self):
        """Test files được ghi ra disk."""
        from midicoder.emitters.core.client.react import ReactClientEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            entities = [{"id": "Order", "fields": [{"name": "total", "type": "float"}]}]

            emitter = ReactClientEmitter()
            files = emitter.emit(entities, output_dir)

            for f in files:
                full_path = output_dir / f.path
                assert full_path.exists(), f"File not found: {full_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])