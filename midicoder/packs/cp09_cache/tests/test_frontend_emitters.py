# coding: utf-8
"""
Tests cho CP09 Angular và React frontend emitters.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from midicoder.packs.cp09_cache.angular import (
    AngularEmitter,
    emit_angular_cache,
)
from midicoder.packs.cp09_cache.react import (
    ReactEmitter,
    emit_react_cache,
)
from midicoder.packs.cp09_cache.models import (
    CacheCollection,
    CacheProfile,
    CacheBackend,
)


# ============================================================================
# Angular Emitter
# ============================================================================

class TestAngularEmitter:
    def setup_method(self):
        self.collection = CacheCollection()
        self.collection.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS, ttl=300))
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_emit_returns_files(self):
        emitter = AngularEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        assert len(files) >= 3

    def test_emit_cache_service(self):
        emitter = AngularEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        paths = [str(f.path) for f in files]
        assert any("cache.service.ts" in p for p in paths)

    def test_emit_cache_interceptor(self):
        emitter = AngularEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        paths = [str(f.path) for f in files]
        assert any("cache.interceptor.ts" in p for p in paths)

    def test_emit_cache_module(self):
        emitter = AngularEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        paths = [str(f.path) for f in files]
        assert any("cache.module.ts" in p for p in paths)

    def test_emit_content_has_tenant(self):
        emitter = AngularEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        all_content = "\n".join(f.content for f in files)
        assert "tenant" in all_content.lower() or "Tenant" in all_content

    def test_emit_files_on_disk(self):
        emitter = AngularEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        for f in files:
            assert f.path.exists(), f"File not written: {f.path}"

    def test_emit_empty_raises(self):
        empty = CacheCollection()
        emitter = AngularEmitter(stack_dir=Path("."))
        with pytest.raises(Exception):
            emitter.emit(empty, Path(self.tmpdir))

    def test_emit_multiple_backends(self):
        self.collection.add_profile(CacheProfile(id="p2", backend=CacheBackend.MEMORY))
        emitter = AngularEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        service = next(f for f in files if "cache.service.ts" in str(f.path))
        assert "Redis" in service.content or "Memory" in service.content

    def test_convenience_function(self):
        files = emit_angular_cache(
            self.collection,
            stack_dir=Path("."),
            output_dir=Path(self.tmpdir),
        )
        assert len(files) >= 3


# ============================================================================
# React Emitter
# ============================================================================

class TestReactEmitter:
    def setup_method(self):
        self.collection = CacheCollection()
        self.collection.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS, ttl=600))
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_emit_returns_files(self):
        emitter = ReactEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        assert len(files) >= 3

    def test_emit_cache_provider(self):
        emitter = ReactEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        paths = [str(f.path) for f in files]
        assert any("CacheProvider.tsx" in p for p in paths)

    def test_emit_use_cache_hook(self):
        emitter = ReactEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        paths = [str(f.path) for f in files]
        assert any("useCache.ts" in p for p in paths)

    def test_emit_cache_utils(self):
        emitter = ReactEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        paths = [str(f.path) for f in files]
        assert any("cache-utils.ts" in p for p in paths)

    def test_emit_cache_types(self):
        emitter = ReactEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        paths = [str(f.path) for f in files]
        assert any("cache.types.ts" in p for p in paths)

    def test_emit_content_has_tenant(self):
        emitter = ReactEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        all_content = "\n".join(f.content for f in files)
        assert "tenant" in all_content.lower() or "Tenant" in all_content

    def test_emit_files_on_disk(self):
        emitter = ReactEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        for f in files:
            assert f.path.exists(), f"File not written: {f.path}"

    def test_emit_empty_raises(self):
        empty = CacheCollection()
        emitter = ReactEmitter(stack_dir=Path("."))
        with pytest.raises(Exception):
            emitter.emit(empty, Path(self.tmpdir))

    def test_emit_default_ttl(self):
        emitter = ReactEmitter(stack_dir=Path("."))
        files = emitter.emit(self.collection, Path(self.tmpdir))
        provider = next(f for f in files if "CacheProvider.tsx" in str(f.path))
        assert "600" in provider.content

    def test_convenience_function(self):
        files = emit_react_cache(
            self.collection,
            stack_dir=Path("."),
            output_dir=Path(self.tmpdir),
        )
        assert len(files) >= 3
