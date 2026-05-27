# coding: utf-8
"""
Tests cho CP28 — Multi-Region NestJS Emitter.

Kiểm tra:
- NestJSMultiRegionEmitter: init, emit
- IR return type

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
from tempfile import mkdtemp

from midicoder.emitters.core.cp28_multi_region.nestjs import NestJSMultiRegionEmitter
from midicoder.emitters.core.cp28_multi_region.parser import MultiRegionIR


class TestNestJSMultiRegionEmitter:
    """Tests cho NestJSMultiRegionEmitter."""

    def test_init(self):
        """Test emitter khởi tạo thành công."""
        tmpdir = mkdtemp()
        emitter = NestJSMultiRegionEmitter(tmpdir)
        assert emitter.stack_dir == Path(tmpdir)

    def test_emit_returns_ir(self):
        """Test emit() returns MultiRegionIR."""
        tmpdir = mkdtemp()
        emitter = NestJSMultiRegionEmitter(tmpdir)
        result = emitter.emit()
        assert isinstance(result, MultiRegionIR)

    def test_emit_with_no_args(self):
        """Test emit() without args creates default IR."""
        tmpdir = mkdtemp()
        emitter = NestJSMultiRegionEmitter(tmpdir)
        result = emitter.emit()
        assert isinstance(result, MultiRegionIR)

    def test_emit_with_existing_ir(self):
        """Test emit() with existing IR preserves data."""
        tmpdir = mkdtemp()
        emitter = NestJSMultiRegionEmitter(tmpdir)
        ir = MultiRegionIR()
        result = emitter.emit(ir)
        assert isinstance(result, MultiRegionIR)

    def test_emit_has_template_env(self):
        """Test emitter has Jinja2 environment."""
        tmpdir = mkdtemp()
        emitter = NestJSMultiRegionEmitter(tmpdir)
        assert hasattr(emitter, 'env')
