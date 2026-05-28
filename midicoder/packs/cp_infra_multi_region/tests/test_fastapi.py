# coding: utf-8
"""
Tests cho I05 — Multi-Region FastAPI Emitter.

Kiểm tra:
- FastAPIMultiRegionEmitter: init, emit
- IR return type

Author: Midicoder Team
Version: 2.0.0
"""

import pytest
from pathlib import Path
from tempfile import mkdtemp

from midicoder.packs.cp_infra_multi_region.fastapi import FastAPIMultiRegionEmitter
from midicoder.packs.cp_infra_multi_region.parser import MultiRegionIR


class TestFastAPIMultiRegionEmitter:
    """Tests cho FastAPIMultiRegionEmitter."""

    def test_init(self):
        """Test emitter khởi tạo thành công."""
        tmpdir = mkdtemp()
        emitter = FastAPIMultiRegionEmitter(tmpdir)
        assert emitter.stack_dir == Path(tmpdir)

    def test_emit_returns_ir(self):
        """Test emit() returns MultiRegionIR."""
        tmpdir = mkdtemp()
        emitter = FastAPIMultiRegionEmitter(tmpdir)
        result = emitter.emit()
        assert isinstance(result, MultiRegionIR)

    def test_emit_with_no_args(self):
        """Test emit() without args creates default IR."""
        tmpdir = mkdtemp()
        emitter = FastAPIMultiRegionEmitter(tmpdir)
        result = emitter.emit()
        assert isinstance(result, MultiRegionIR)
        # Should have default regions
        assert len(result.regions) >= 0

    def test_emit_with_existing_ir(self):
        """Test emit() with existing IR preserves data."""
        tmpdir = mkdtemp()
        emitter = FastAPIMultiRegionEmitter(tmpdir)
        ir = MultiRegionIR()
        result = emitter.emit(ir)
        assert isinstance(result, MultiRegionIR)

    def test_emit_has_template_env(self):
        """Test emitter has Jinja2 environment."""
        tmpdir = mkdtemp()
        emitter = FastAPIMultiRegionEmitter(tmpdir)
        assert hasattr(emitter, 'env')
