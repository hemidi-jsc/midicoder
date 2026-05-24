# coding: utf-8
"""
Kiểm tra mô-đun models cho CP44 — Bulk Operations Engine.

Bao gồm các tests cho:
- Error codes: MDC-CP44-001 đến MDC-CP44-010
- Enums: BulkAction, JobStatus, ChunkStatus, RetryStrategy
- BulkJob: tạo, validate, to_dict/from_dict
- BulkChunk: tạo, validate, to_dict/from_dict
- BulkResult: tạo, validate, to_dict/from_dict
- DLQEntry: tạo, validate, to_dict/from_dict
- BulkEngine: create_job, process_job, process_chunk, retry_record, get_progress
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Test Error Codes CP44
# ===========================================================================


class TestCP44ErrorCodes:
    """Kiểm tra các mã lỗi CP44 đã được định nghĩa đúng."""

    def test_bulk_job_not_found_code(self):
        assert ErrorCode.CP44_BULK_JOB_NOT_FOUND == "MDC-CP44-001"

    def test_bulk_job_already_running_code(self):
        assert ErrorCode.CP44_BULK_JOB_ALREADY_RUNNING == "MDC-CP44-002"

    def test_bulk_invalid_action_code(self):
        assert ErrorCode.CP44_BULK_INVALID_ACTION == "MDC-CP44-003"

    def test_bulk_chunk_size_invalid_code(self):
        assert ErrorCode.CP44_BULK_CHUNK_SIZE_INVALID == "MDC-CP44-004"

    def test_bulk_concurrency_invalid_code(self):
        assert ErrorCode.CP44_BULK_CONCURRENCY_INVALID == "MDC-CP44-005"

    def test_bulk_retry_exhausted_code(self):
        assert ErrorCode.CP44_BULK_RETRY_EXHAUSTED == "MDC-CP44-006"

    def test_bulk_dlq_full_code(self):
        assert ErrorCode.CP44_BULK_DLQ_FULL == "MDC-CP44-007"

    def test_bulk_job_timeout_code(self):
        assert ErrorCode.CP44_BULK_JOB_TIMEOUT == "MDC-CP44-008"

    def test_bulk_cross_tenant_access_code(self):
        assert ErrorCode.CP44_BULK_CROSS_TENANT_ACCESS == "MDC-CP44-009"

    def test_bulk_cancel_failed_code(self):
        assert ErrorCode.CP44_BULK_CANCEL_FAILED == "MDC-CP44-010"


# ===========================================================================
# Test BulkAction Enum
# ===========================================================================


class TestBulkAction:
    """Kiểm tra các giá trị của enum BulkAction."""

    def test_action_batch_create(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkAction
        assert BulkAction.BATCH_CREATE.value == "batch_create"

    def test_action_batch_update(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkAction
        assert BulkAction.BATCH_UPDATE.value == "batch_update"

    def test_action_batch_delete(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkAction
        assert BulkAction.BATCH_DELETE.value == "batch_delete"

    def test_action_batch_read(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkAction
        assert BulkAction.BATCH_READ.value == "batch_read"


# ===========================================================================
# Test JobStatus Enum
# ===========================================================================


class TestJobStatus:
    """Kiểm tra các giá trị của enum JobStatus."""

    def test_status_pending(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import JobStatus
        assert JobStatus.PENDING.value == "pending"

    def test_status_running(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import JobStatus
        assert JobStatus.RUNNING.value == "running"

    def test_status_completed(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import JobStatus
        assert JobStatus.COMPLETED.value == "completed"

    def test_status_failed(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import JobStatus
        assert JobStatus.FAILED.value == "failed"

    def test_status_cancelled(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import JobStatus
        assert JobStatus.CANCELLED.value == "cancelled"

    def test_status_timeout(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import JobStatus
        assert JobStatus.TIMEOUT.value == "timeout"


# ===========================================================================
# Test ChunkStatus Enum
# ===========================================================================


class TestChunkStatus:
    """Kiểm tra các giá trị của enum ChunkStatus."""

    def test_status_pending(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import ChunkStatus
        assert ChunkStatus.PENDING.value == "pending"

    def test_status_processing(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import ChunkStatus
        assert ChunkStatus.PROCESSING.value == "processing"

    def test_status_completed(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import ChunkStatus
        assert ChunkStatus.COMPLETED.value == "completed"

    def test_status_failed(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import ChunkStatus
        assert ChunkStatus.FAILED.value == "failed"


# ===========================================================================
# Test RetryStrategy Enum
# ===========================================================================


class TestRetryStrategy:
    """Kiểm tra các giá trị của enum RetryStrategy."""

    def test_strategy_exponential(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import RetryStrategy
        assert RetryStrategy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"

    def test_strategy_fixed(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import RetryStrategy
        assert RetryStrategy.FIXED_DELAY.value == "fixed_delay"

    def test_strategy_linear(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import RetryStrategy
        assert RetryStrategy.LINEAR_BACKOFF.value == "linear_backoff"


# ===========================================================================
# Test BulkJob
# ===========================================================================


class TestBulkJob:
    """Kiểm tra dataclass BulkJob."""

    def test_create_valid_job(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkJob, BulkAction, JobStatus
        job = BulkJob(
            job_id="job_001",
            entity_type="user",
            action=BulkAction.BATCH_UPDATE,
            entity_ids=["u1", "u2", "u3"],
            chunk_size=100,
            max_concurrency=10,
        )
        assert job.job_id == "job_001"
        assert job.entity_type == "user"
        assert job.action == BulkAction.BATCH_UPDATE
        assert job.status == JobStatus.PENDING
        assert job.chunk_size == 100
        assert job.max_concurrency == 10
        assert job.total_records == 3
        assert job.processed == 0
        assert job.succeeded == 0
        assert job.failed == 0
        assert job.skipped == 0

    def test_job_empty_id_raises_error(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkJob, BulkAction
        with pytest.raises(MidicoderError):
            BulkJob(
                job_id="",
                entity_type="user",
                action=BulkAction.BATCH_UPDATE,
                entity_ids=["u1"],
            )

    def test_job_invalid_chunk_size_raises_error(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkJob, BulkAction
        with pytest.raises(MidicoderError):
            BulkJob(
                job_id="job_001",
                entity_type="user",
                action=BulkAction.BATCH_UPDATE,
                entity_ids=["u1"],
                chunk_size=0,
            )

    def test_job_invalid_concurrency_raises_error(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkJob, BulkAction
        with pytest.raises(MidicoderError):
            BulkJob(
                job_id="job_001",
                entity_type="user",
                action=BulkAction.BATCH_UPDATE,
                entity_ids=["u1"],
                max_concurrency=0,
            )

    def test_job_default_values(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkJob, BulkAction
        job = BulkJob(
            job_id="job_001",
            entity_type="product",
            action=BulkAction.BATCH_READ,
            entity_ids=[],
        )
        assert job.chunk_size == 100
        assert job.max_concurrency == 10
        assert job.max_retries == 3
        assert job.timeout_seconds == 300

    def test_job_to_dict(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkJob, BulkAction
        job = BulkJob(
            job_id="job_001",
            entity_type="order",
            action=BulkAction.BATCH_DELETE,
            entity_ids=["o1", "o2"],
        )
        d = job.to_dict()
        assert d["job_id"] == "job_001"
        assert d["entity_type"] == "order"
        assert d["action"] == "batch_delete"
        assert d["total_records"] == 2

    def test_job_from_dict(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkJob, BulkAction
        data = {
            "job_id": "job_002",
            "entity_type": "invoice",
            "action": "batch_update",
            "entity_ids": ["inv1", "inv2", "inv3"],
            "chunk_size": 50,
            "max_concurrency": 5,
        }
        job = BulkJob.from_dict(data)
        assert job.job_id == "job_002"
        assert job.action == BulkAction.BATCH_UPDATE
        assert job.chunk_size == 50
        assert job.max_concurrency == 5


# ===========================================================================
# Test BulkChunk
# ===========================================================================


class TestBulkChunk:
    """Kiểm tra dataclass BulkChunk."""

    def test_create_valid_chunk(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkChunk, ChunkStatus
        chunk = BulkChunk(
            chunk_id="chunk_001",
            job_id="job_001",
            chunk_number=1,
            entity_ids=["e1", "e2"],
        )
        assert chunk.chunk_id == "chunk_001"
        assert chunk.job_id == "job_001"
        assert chunk.chunk_number == 1
        assert chunk.status == ChunkStatus.PENDING
        assert chunk.succeeded == 0
        assert chunk.failed == 0

    def test_chunk_empty_id_raises_error(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkChunk
        with pytest.raises(MidicoderError):
            BulkChunk(
                chunk_id="",
                job_id="job_001",
                chunk_number=1,
                entity_ids=[],
            )

    def test_chunk_to_dict(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkChunk
        chunk = BulkChunk(
            chunk_id="chunk_001",
            job_id="job_001",
            chunk_number=2,
            entity_ids=["e1"],
        )
        d = chunk.to_dict()
        assert d["chunk_id"] == "chunk_001"
        assert d["chunk_number"] == 2

    def test_chunk_from_dict(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkChunk
        data = {
            "chunk_id": "chunk_002",
            "job_id": "job_001",
            "chunk_number": 3,
            "entity_ids": ["a", "b"],
        }
        chunk = BulkChunk.from_dict(data)
        assert chunk.chunk_number == 3
        assert len(chunk.entity_ids) == 2


# ===========================================================================
# Test BulkResult
# ===========================================================================


class TestBulkResult:
    """Kiểm tra dataclass BulkResult."""

    def test_create_success_result(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkResult
        result = BulkResult(
            entity_id="e1",
            success=True,
        )
        assert result.success is True
        assert result.error is None

    def test_create_failed_result(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkResult
        result = BulkResult(
            entity_id="e2",
            success=False,
            error="Validation failed",
        )
        assert result.success is False
        assert result.error == "Validation failed"

    def test_result_to_dict(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkResult
        result = BulkResult(
            entity_id="e1",
            success=True,
            metadata={"rows_affected": 1},
        )
        d = result.to_dict()
        assert d["entity_id"] == "e1"
        assert d["success"] is True

    def test_result_from_dict(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkResult
        data = {
            "entity_id": "e3",
            "success": False,
            "error": "Timeout",
            "retry_count": 2,
        }
        result = BulkResult.from_dict(data)
        assert result.success is False
        assert result.retry_count == 2


# ===========================================================================
# Test DLQEntry
# ===========================================================================


class TestDLQEntry:
    """Kiểm tra dataclass DLQEntry."""

    def test_create_valid_dlq_entry(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import DLQEntry
        entry = DLQEntry(
            entry_id="dlq_001",
            job_id="job_001",
            entity_id="e1",
            error="Connection timeout",
            retry_count=3,
        )
        assert entry.entry_id == "dlq_001"
        assert entry.job_id == "job_001"
        assert entry.entity_id == "e1"
        assert entry.retry_count == 3

    def test_dlq_empty_entry_id_raises_error(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import DLQEntry
        with pytest.raises(MidicoderError):
            DLQEntry(
                entry_id="",
                job_id="job_001",
                entity_id="e1",
                error="error",
            )

    def test_dlq_to_dict(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import DLQEntry
        entry = DLQEntry(
            entry_id="dlq_001",
            job_id="job_001",
            entity_id="e1",
            error="Test error",
        )
        d = entry.to_dict()
        assert d["entry_id"] == "dlq_001"

    def test_dlq_from_dict(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import DLQEntry
        data = {
            "entry_id": "dlq_002",
            "job_id": "job_002",
            "entity_id": "e5",
            "error": "Failed",
            "retry_count": 1,
        }
        entry = DLQEntry.from_dict(data)
        assert entry.retry_count == 1


# ===========================================================================
# Test BulkEngine
# ===========================================================================


class TestBulkEngine:
    """Kiểm tra class BulkEngine."""

    def test_create_engine(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkEngine
        engine = BulkEngine()
        assert engine is not None

    def test_create_job(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkEngine, BulkAction, JobStatus
        engine = BulkEngine()
        job = engine.create_job(
            job_id="job_test",
            entity_type="user",
            action=BulkAction.BATCH_UPDATE,
            entity_ids=["u1", "u2", "u3"],
            chunk_size=100,
        )
        assert job.job_id == "job_test"
        assert job.status == JobStatus.PENDING
        assert job.total_records == 3

    def test_create_duplicate_job_raises_error(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkEngine, BulkAction
        engine = BulkEngine()
        engine.create_job("job_dup", "user", BulkAction.BATCH_UPDATE, ["u1"])
        with pytest.raises(MidicoderError):
            engine.create_job("job_dup", "user", BulkAction.BATCH_UPDATE, ["u2"])

    def test_get_progress(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkEngine, BulkAction
        engine = BulkEngine()
        engine.create_job("job_prog", "user", BulkAction.BATCH_UPDATE, ["u1", "u2"])
        progress = engine.get_progress("job_prog")
        assert progress["total"] == 2
        assert progress["processed"] == 0
        assert progress["succeeded"] == 0
        assert progress["failed"] == 0

    def test_get_progress_unknown_job_raises_error(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkEngine
        engine = BulkEngine()
        with pytest.raises(MidicoderError):
            engine.get_progress("nonexistent")

    def test_process_job_creates_chunks(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkEngine, BulkAction, JobStatus
        engine = BulkEngine()
        ids = [f"e{i}" for i in range(250)]  # 250 records → 3 chunks với chunk_size=100
        engine.create_job("job_chunks", "item", BulkAction.BATCH_UPDATE, ids, chunk_size=100)
        engine.process_job("job_chunks")
        job = engine.jobs["job_chunks"]
        assert job.status == JobStatus.COMPLETED
        assert job.processed == 250
        assert job.succeeded == 250

    def test_cancel_job(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkEngine, BulkAction, JobStatus
        engine = BulkEngine()
        engine.create_job("job_cancel", "user", BulkAction.BATCH_DELETE, ["u1"])
        engine.cancel_job("job_cancel")
        job = engine.jobs["job_cancel"]
        assert job.status == JobStatus.CANCELLED

    def test_get_dlq_entries(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkEngine
        engine = BulkEngine()
        dlq = engine.get_dlq_entries()
        assert isinstance(dlq, list)

    def test_replay_dlq_empty(self):
        from midicoder.emitters.core.cp44_bulk_ops.models import BulkEngine
        engine = BulkEngine()
        result = engine.replay_dlq("nonexistent")
        assert result is False
