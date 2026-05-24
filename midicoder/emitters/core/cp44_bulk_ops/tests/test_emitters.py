# coding: utf-8
"""
Test emitters cho CP44 — Bulk Operations Engine.

Test 4 emitter classes:
- FastAPIBulkOpsEmitter
- NestJSBulkOpsEmitter
- AngularBulkOpsEmitter
- ReactBulkOpsEmitter
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from midicoder.emitters.core.cp44_bulk_ops.parser import BulkIR
from midicoder.errors import MidicoderError


class TestFastAPIBulkOpsEmitter:
    """Test FastAPIBulkOpsEmitter."""

    def test_emit_returns_files(self, tmp_path):
        """Emitter trả về danh sách files."""
        from midicoder.emitters.core.cp44_bulk_ops.fastapi import FastAPIBulkOpsEmitter, GeneratedFile

        # Tạo template dir và mock templates
        template_dir = tmp_path / "cp44_bulk_ops"
        template_dir.mkdir()
        for name in [
            "bulk_models.py.jinja2",
            "bulk_schemas.py.jinja2",
            "bulk_service.py.jinja2",
            "bulk_router.py.jinja2",
            "bulk_worker.py.jinja2",
            "bulk_dlq_worker.py.jinja2",
            "bulk_sse.py.jinja2",
        ]:
            (template_dir / name).write_text("{{ job_count }}")

        emitter = FastAPIBulkOpsEmitter(template_dir)
        ir = BulkIR(default_chunk_size=50, default_concurrency=5)
        files = emitter.emit(ir, tmp_path)

        assert isinstance(files, list)
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_template_count(self, tmp_path):
        """Emitter render đúng số templates tồn tại."""
        from midicoder.emitters.core.cp44_bulk_ops.fastapi import FastAPIBulkOpsEmitter

        template_dir = tmp_path / "cp44_bulk_ops"
        template_dir.mkdir()
        (template_dir / "bulk_models.py.jinja2").write_text("test")
        (template_dir / "bulk_schemas.py.jinja2").write_text("test")

        emitter = FastAPIBulkOpsEmitter(template_dir)
        ir = BulkIR()
        files = emitter.emit(ir, tmp_path)

        assert len(files) == 2

    def test_invalid_dir_raises_error(self):
        """Template dir không tồn tại raise error."""
        from midicoder.emitters.core.cp44_bulk_ops.fastapi import FastAPIBulkOpsEmitter

        with pytest.raises(MidicoderError):
            FastAPIBulkOpsEmitter("/nonexistent/path")


class TestNestJSBulkOpsEmitter:
    """Test NestJSBulkOpsEmitter."""

    def test_emit_returns_files(self, tmp_path):
        """Emitter trả về danh sách files."""
        from midicoder.emitters.core.cp44_bulk_ops.nestjs import NestJSBulkOpsEmitter

        template_dir = tmp_path / "cp44_bulk_ops"
        template_dir.mkdir()
        for name in [
            "bulk.entity.ts.jinja2",
            "bulk.dto.ts.jinja2",
            "bulk.service.ts.jinja2",
            "bulk.controller.ts.jinja2",
            "bulk.module.ts.jinja2",
            "bulk.scheduler.ts.jinja2",
            "bulk.gateway.ts.jinja2",
        ]:
            (template_dir / name).write_text("{{ job_count }}")

        emitter = NestJSBulkOpsEmitter(template_dir)
        ir = BulkIR()
        files = emitter.emit(ir)

        assert isinstance(files, list)
        assert all(isinstance(f, dict) for f in files)
        assert all("path" in f and "content" in f for f in files)

    def test_invalid_dir_raises_error(self):
        from midicoder.emitters.core.cp44_bulk_ops.nestjs import NestJSBulkOpsEmitter

        with pytest.raises(MidicoderError):
            NestJSBulkOpsEmitter("/nonexistent/path")


class TestAngularBulkOpsEmitter:
    """Test AngularBulkOpsEmitter."""

    def test_emit_returns_files(self, tmp_path):
        """Emitter trả về danh sách files."""
        from midicoder.emitters.core.cp44_bulk_ops.angular import AngularBulkOpsEmitter

        template_dir = tmp_path / "cp44_bulk_ops"
        template_dir.mkdir()
        for name in [
            "bulk-dashboard.component.ts.jinja2",
            "bulk-jobs.component.ts.jinja2",
            "bulk-job-details.component.ts.jinja2",
            "bulk.service.ts.jinja2",
            "bulk.store.ts.jinja2",
            "bulk-types.ts.jinja2",
        ]:
            (template_dir / name).write_text("{{ job_count }}")

        emitter = AngularBulkOpsEmitter(template_dir)
        ir = BulkIR()
        files = emitter.emit(ir)

        assert isinstance(files, list)
        assert all(isinstance(f, dict) for f in files)

    def test_emit_template_count(self, tmp_path):
        """Emitter render đúng số templates tồn tại."""
        from midicoder.emitters.core.cp44_bulk_ops.angular import AngularBulkOpsEmitter

        template_dir = tmp_path / "cp44_bulk_ops"
        template_dir.mkdir()
        (template_dir / "bulk-types.ts.jinja2").write_text("test")

        emitter = AngularBulkOpsEmitter(template_dir)
        ir = BulkIR()
        files = emitter.emit(ir)

        assert len(files) == 1

    def test_invalid_dir_raises_error(self):
        from midicoder.emitters.core.cp44_bulk_ops.angular import AngularBulkOpsEmitter

        with pytest.raises(MidicoderError):
            AngularBulkOpsEmitter("/nonexistent/path")


class TestReactBulkOpsEmitter:
    """Test ReactBulkOpsEmitter."""

    def test_emit_returns_files(self, tmp_path):
        """Emitter trả về danh sách files."""
        from midicoder.emitters.core.cp44_bulk_ops.react import ReactBulkOpsEmitter

        template_dir = tmp_path / "cp44_bulk_ops"
        template_dir.mkdir()
        for name in [
            "BulkDashboard.tsx.jinja2",
            "BulkJobs.tsx.jinja2",
            "BulkJobDetails.tsx.jinja2",
            "BulkProgress.tsx.jinja2",
            "useBulkOps.ts.jinja2",
        ]:
            (template_dir / name).write_text("{{ job_count }}")

        emitter = ReactBulkOpsEmitter(template_dir)
        ir = BulkIR()
        files = emitter.emit(ir)

        assert isinstance(files, list)
        assert all(isinstance(f, dict) for f in files)

    def test_emit_with_context(self, tmp_path):
        """Emitter render với context và IR data."""
        from midicoder.emitters.core.cp44_bulk_ops.react import ReactBulkOpsEmitter

        template_dir = tmp_path / "cp44_bulk_ops"
        template_dir.mkdir()
        (template_dir / "BulkDashboard.tsx.jinja2").write_text(
            "chunk={{ default_chunk_size }}, conc={{ default_concurrency }}"
        )

        emitter = ReactBulkOpsEmitter(template_dir)
        ir = BulkIR(default_chunk_size=200, default_concurrency=15)
        files = emitter.emit(ir)

        assert len(files) == 1
        assert "chunk=200" in files[0]["content"]
        assert "conc=15" in files[0]["content"]

    def test_invalid_dir_raises_error(self):
        from midicoder.emitters.core.cp44_bulk_ops.react import ReactBulkOpsEmitter

        with pytest.raises(MidicoderError):
            ReactBulkOpsEmitter("/nonexistent/path")


class TestEmitterIntegration:
    """Test integration giữa IR và emitters."""

    def test_ir_data_flows_through_emitter(self, tmp_path):
        """IR data được truyền qua emitter context."""
        from midicoder.emitters.core.cp44_bulk_ops.fastapi import FastAPIBulkOpsEmitter
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkAction, BulkJob

        template_dir = tmp_path / "cp44_bulk_ops"
        template_dir.mkdir()
        (template_dir / "bulk_models.py.jinja2").write_text(
            "jobs={{ job_count }}, chunk={{ default_chunk_size }}, dlq={{ dlq_enabled }}"
        )

        job = BulkJob(
            job_id="test_001",
            entity_type="user",
            action=BulkAction.BATCH_UPDATE,
            entity_ids=["u1", "u2"],
        )
        ir = BulkIR(jobs=[job], default_chunk_size=75, dlq_enabled=False)

        emitter = FastAPIBulkOpsEmitter(template_dir)
        files = emitter.emit(ir, tmp_path)

        assert "jobs=1" in files[0].content
        assert "chunk=75" in files[0].content
        assert "dlq=False" in files[0].content
