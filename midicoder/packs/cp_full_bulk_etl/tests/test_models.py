# coding: utf-8
"""
Kiểm tra mô-đun models cho CP44 — Bulk Operations Engine.

Bao gồm các tests cho:
- Error codes: MDC-CP44-001 đến MDC-CP44-010
- Enums: BulkAction (4), JobStatus (6), ChunkStatus (4), RetryStrategy (3)
- BulkJob: tạo, validate, auto timestamp, default values, to_dict/from_dict roundtrip
- BulkChunk: tạo, validate, to_dict/from_dict roundtrip, nested results
- BulkResult: tạo, success/failed, auto timestamp, to_dict/from_dict
- DLQEntry: tạo, validate, auto timestamp, replay flow, to_dict/from_dict
- BulkEngine: create_job, process_job (chia chunks), cancel_job, retry_record,
  get_progress, get_dlq_entries, replay_dlq

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Test Error Codes CP44
# ===========================================================================


class TestCP44ErrorCodes:
    """Kiểm tra các mã lỗi CP44 đã được định nghĩa đúng."""

    def test_bulk_job_not_found_code(self):
        """Kiểm tra mã lỗi job không tồn tại."""
        assert ErrorCode.MDC-F28_BULK_JOB_NOT_FOUND == "MDC-CP44-001"

    def test_bulk_job_already_running_code(self):
        """Kiểm tra mã lỗi job đã chạy."""
        assert ErrorCode.MDC-F28_BULK_JOB_ALREADY_RUNNING == "MDC-CP44-002"

    def test_bulk_invalid_action_code(self):
        """Kiểm tra mã lỗi action không hợp lệ."""
        assert ErrorCode.MDC-F28_BULK_INVALID_ACTION == "MDC-CP44-003"

    def test_bulk_chunk_size_invalid_code(self):
        """Kiểm tra mã lỗi chunk size không hợp lệ."""
        assert ErrorCode.MDC-F28_BULK_CHUNK_SIZE_INVALID == "MDC-CP44-004"

    def test_bulk_concurrency_invalid_code(self):
        """Kiểm tra mã lỗi concurrency không hợp lệ."""
        assert ErrorCode.MDC-F28_BULK_CONCURRENCY_INVALID == "MDC-CP44-005"

    def test_bulk_retry_exhausted_code(self):
        """Kiểm tra mã lỗi hết số lần retry."""
        assert ErrorCode.MDC-F28_BULK_RETRY_EXHAUSTED == "MDC-CP44-006"

    def test_bulk_dlq_full_code(self):
        """Kiểm tra mã lỗi DLQ đầy."""
        assert ErrorCode.MDC-F28_BULK_DLQ_FULL == "MDC-CP44-007"

    def test_bulk_job_timeout_code(self):
        """Kiểm tra mã lỗi job hết giờ."""
        assert ErrorCode.MDC-F28_BULK_JOB_TIMEOUT == "MDC-CP44-008"

    def test_bulk_cross_tenant_access_code(self):
        """Kiểm tra mã lỗi truy cập cross-tenant."""
        assert ErrorCode.MDC-F28_BULK_CROSS_TENANT_ACCESS == "MDC-CP44-009"

    def test_bulk_cancel_failed_code(self):
        """Kiểm tra mã lỗi hủy job thất bại."""
        assert ErrorCode.MDC-F28_BULK_CANCEL_FAILED == "MDC-CP44-010"


# ===========================================================================
# Test BulkAction Enum
# ===========================================================================


class TestBulkAction:
    """Kiểm tra các giá trị và số lượng member của enum BulkAction."""

    def test_action_batch_create_value(self):
        """Kiểm tra giá trị BATCH_CREATE."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction
        assert BulkAction.BATCH_CREATE.value == "batch_create"

    def test_action_batch_update_value(self):
        """Kiểm tra giá trị BATCH_UPDATE."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction
        assert BulkAction.BATCH_UPDATE.value == "batch_update"

    def test_action_batch_delete_value(self):
        """Kiểm tra giá trị BATCH_DELETE."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction
        assert BulkAction.BATCH_DELETE.value == "batch_delete"

    def test_action_batch_read_value(self):
        """Kiểm tra giá trị BATCH_READ."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction
        assert BulkAction.BATCH_READ.value == "batch_read"

    def test_action_members_count(self):
        """Kiểm tra số lượng member của BulkAction là 4."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction
        assert len(BulkAction) == 4


# ===========================================================================
# Test JobStatus Enum
# ===========================================================================


class TestJobStatus:
    """Kiểm tra các giá trị và số lượng member của enum JobStatus."""

    def test_status_pending_value(self):
        """Kiểm tra giá trị PENDING."""
        from midicoder.packs.cp_full_bulk_etl.models import JobStatus
        assert JobStatus.PENDING.value == "pending"

    def test_status_running_value(self):
        """Kiểm tra giá trị RUNNING."""
        from midicoder.packs.cp_full_bulk_etl.models import JobStatus
        assert JobStatus.RUNNING.value == "running"

    def test_status_completed_value(self):
        """Kiểm tra giá trị COMPLETED."""
        from midicoder.packs.cp_full_bulk_etl.models import JobStatus
        assert JobStatus.COMPLETED.value == "completed"

    def test_status_failed_value(self):
        """Kiểm tra giá trị FAILED."""
        from midicoder.packs.cp_full_bulk_etl.models import JobStatus
        assert JobStatus.FAILED.value == "failed"

    def test_status_cancelled_value(self):
        """Kiểm tra giá trị CANCELLED."""
        from midicoder.packs.cp_full_bulk_etl.models import JobStatus
        assert JobStatus.CANCELLED.value == "cancelled"

    def test_status_timeout_value(self):
        """Kiểm tra giá trị TIMEOUT."""
        from midicoder.packs.cp_full_bulk_etl.models import JobStatus
        assert JobStatus.TIMEOUT.value == "timeout"

    def test_status_members_count(self):
        """Kiểm tra số lượng member của JobStatus là 6."""
        from midicoder.packs.cp_full_bulk_etl.models import JobStatus
        assert len(JobStatus) == 6


# ===========================================================================
# Test ChunkStatus Enum
# ===========================================================================


class TestChunkStatus:
    """Kiểm tra các giá trị và số lượng member của enum ChunkStatus."""

    def test_status_pending_value(self):
        """Kiểm tra giá trị PENDING."""
        from midicoder.packs.cp_full_bulk_etl.models import ChunkStatus
        assert ChunkStatus.PENDING.value == "pending"

    def test_status_processing_value(self):
        """Kiểm tra giá trị PROCESSING."""
        from midicoder.packs.cp_full_bulk_etl.models import ChunkStatus
        assert ChunkStatus.PROCESSING.value == "processing"

    def test_status_completed_value(self):
        """Kiểm tra giá trị COMPLETED."""
        from midicoder.packs.cp_full_bulk_etl.models import ChunkStatus
        assert ChunkStatus.COMPLETED.value == "completed"

    def test_status_failed_value(self):
        """Kiểm tra giá trị FAILED."""
        from midicoder.packs.cp_full_bulk_etl.models import ChunkStatus
        assert ChunkStatus.FAILED.value == "failed"

    def test_status_members_count(self):
        """Kiểm tra số lượng member của ChunkStatus là 4."""
        from midicoder.packs.cp_full_bulk_etl.models import ChunkStatus
        assert len(ChunkStatus) == 4


# ===========================================================================
# Test RetryStrategy Enum
# ===========================================================================


class TestRetryStrategy:
    """Kiểm tra các giá trị và số lượng member của enum RetryStrategy."""

    def test_strategy_exponential_backoff_value(self):
        """Kiểm tra giá trị EXPONENTIAL_BACKOFF."""
        from midicoder.packs.cp_full_bulk_etl.models import RetryStrategy
        assert RetryStrategy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"

    def test_strategy_fixed_delay_value(self):
        """Kiểm tra giá trị FIXED_DELAY."""
        from midicoder.packs.cp_full_bulk_etl.models import RetryStrategy
        assert RetryStrategy.FIXED_DELAY.value == "fixed_delay"

    def test_strategy_linear_backoff_value(self):
        """Kiểm tra giá trị LINEAR_BACKOFF."""
        from midicoder.packs.cp_full_bulk_etl.models import RetryStrategy
        assert RetryStrategy.LINEAR_BACKOFF.value == "linear_backoff"

    def test_strategy_members_count(self):
        """Kiểm tra số lượng member của RetryStrategy là 3."""
        from midicoder.packs.cp_full_bulk_etl.models import RetryStrategy
        assert len(RetryStrategy) == 3


# ===========================================================================
# Test BulkJob
# ===========================================================================


class TestBulkJob:
    """Kiểm tra dataclass BulkJob — tạo, validate, serialize, default values."""

    def test_create_valid_job_with_all_fields(self):
        """Kiểm tra tạo job hợp lệ với đầy đủ thông tin."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkJob,
            JobStatus,
            RetryStrategy,
        )
        job = BulkJob(
            job_id="job_001",
            entity_type="user",
            action=BulkAction.BATCH_UPDATE,
            entity_ids=["u1", "u2", "u3"],
            chunk_size=50,
            max_concurrency=5,
            max_retries=5,
            retry_strategy=RetryStrategy.FIXED_DELAY,
            timeout_seconds=600,
            tenant_id="tenant_01",
            operator_id="op_001",
            metadata={"source": "api"},
        )
        assert job.job_id == "job_001"
        assert job.entity_type == "user"
        assert job.action == BulkAction.BATCH_UPDATE
        assert job.status == JobStatus.PENDING
        assert job.chunk_size == 50
        assert job.max_concurrency == 5
        assert job.max_retries == 5
        assert job.retry_strategy == RetryStrategy.FIXED_DELAY
        assert job.timeout_seconds == 600
        assert job.total_records == 3
        assert job.processed == 0
        assert job.succeeded == 0
        assert job.failed == 0
        assert job.skipped == 0
        assert job.tenant_id == "tenant_01"
        assert job.operator_id == "op_001"
        assert job.metadata == {"source": "api"}

    def test_create_job_minimal_fields(self):
        """Kiểm tra tạo job với chỉ các fields bắt buộc."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkJob,
            JobStatus,
            RetryStrategy,
        )
        job = BulkJob(
            job_id="job_min",
            entity_type="product",
            action=BulkAction.BATCH_READ,
        )
        assert job.job_id == "job_min"
        assert job.entity_ids == []
        assert job.total_records == 0

    def test_create_job_empty_id_raises_error(self):
        """Kiểm tra tạo job với job_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkJob
        with pytest.raises(MidicoderError):
            BulkJob(
                job_id="",
                entity_type="user",
                action=BulkAction.BATCH_UPDATE,
            )

    def test_create_job_whitespace_id_raises_error(self):
        """Kiểm tra tạo job với job_id chỉ khoảng trắng sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkJob
        with pytest.raises(MidicoderError):
            BulkJob(
                job_id="   ",
                entity_type="user",
                action=BulkAction.BATCH_UPDATE,
            )

    def test_create_job_invalid_chunk_size_raises_error(self):
        """Kiểm tra tạo job với chunk_size <= 0 sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkJob
        with pytest.raises(MidicoderError):
            BulkJob(
                job_id="job_bad_chunk",
                entity_type="user",
                action=BulkAction.BATCH_UPDATE,
                chunk_size=0,
            )

    def test_create_job_negative_chunk_size_raises_error(self):
        """Kiểm tra tạo job với chunk_size âm sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkJob
        with pytest.raises(MidicoderError):
            BulkJob(
                job_id="job_neg_chunk",
                entity_type="user",
                action=BulkAction.BATCH_UPDATE,
                chunk_size=-1,
            )

    def test_create_job_invalid_concurrency_raises_error(self):
        """Kiểm tra tạo job với max_concurrency <= 0 sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkJob
        with pytest.raises(MidicoderError):
            BulkJob(
                job_id="job_bad_conc",
                entity_type="user",
                action=BulkAction.BATCH_UPDATE,
                max_concurrency=0,
            )

    def test_create_job_negative_concurrency_raises_error(self):
        """Kiểm tra tạo job với max_concurrency âm sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkJob
        with pytest.raises(MidicoderError):
            BulkJob(
                job_id="job_neg_conc",
                entity_type="user",
                action=BulkAction.BATCH_UPDATE,
                max_concurrency=-5,
            )

    def test_auto_timestamps_on_create(self):
        """Kiểm tra tự động tạo timestamps khi không cung cấp."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkJob
        job = BulkJob(
            job_id="job_ts",
            entity_type="item",
            action=BulkAction.BATCH_CREATE,
        )
        assert job.created_at is not None
        assert job.updated_at is not None
        assert job.created_at.tzinfo is not None
        assert job.updated_at.tzinfo is not None

    def test_custom_timestamps_preserved(self):
        """Kiểm tra timestamps tùy chỉnh không bị ghi đè (branch coverage)."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkJob
        now = datetime.now(timezone.utc)
        job = BulkJob(
            job_id="job_custom_ts",
            entity_type="item",
            action=BulkAction.BATCH_CREATE,
            created_at=now,
            updated_at=now,
        )
        assert job.created_at == now
        assert job.updated_at == now

    def test_total_records_property(self):
        """Kiểm tra total_records = len(entity_ids)."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkJob
        job = BulkJob(
            job_id="job_total",
            entity_type="order",
            action=BulkAction.BATCH_UPDATE,
            entity_ids=["o1", "o2", "o3", "o4", "o5"],
        )
        assert job.total_records == 5

    def test_total_records_empty_list(self):
        """Kiểm tra total_records = 0 khi entity_ids rỗng."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkJob
        job = BulkJob(
            job_id="job_empty",
            entity_type="user",
            action=BulkAction.BATCH_READ,
            entity_ids=[],
        )
        assert job.total_records == 0

    def test_default_values(self):
        """Kiểm tra các giá trị mặc định của BulkJob."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkJob,
            JobStatus,
            RetryStrategy,
        )
        job = BulkJob(
            job_id="job_def",
            entity_type="item",
            action=BulkAction.BATCH_READ,
        )
        assert job.chunk_size == 100
        assert job.max_concurrency == 10
        assert job.max_retries == 3
        assert job.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert job.timeout_seconds == 300
        assert job.status == JobStatus.PENDING
        assert job.processed == 0
        assert job.succeeded == 0
        assert job.failed == 0
        assert job.skipped == 0
        assert job.tenant_id == ""
        assert job.operator_id == ""
        assert job.metadata == {}
        assert job.completed_at is None

    def test_to_dict(self):
        """Kiểm tra chuyển BulkJob sang dict — serialize enums và datetime."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkJob
        job = BulkJob(
            job_id="job_dict",
            entity_type="order",
            action=BulkAction.BATCH_DELETE,
            entity_ids=["o1", "o2"],
            tenant_id="t1",
            operator_id="op1",
        )
        d = job.to_dict()
        assert d["job_id"] == "job_dict"
        assert d["entity_type"] == "order"
        assert d["action"] == "batch_delete"
        assert d["status"] == "pending"
        assert d["retry_strategy"] == "exponential_backoff"
        assert d["entity_ids"] == ["o1", "o2"]
        assert d["total_records"] == 2
        assert d["tenant_id"] == "t1"
        assert d["operator_id"] == "op1"
        assert d["created_at"] is not None
        assert d["updated_at"] is not None
        assert d["completed_at"] is None

    def test_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize BulkJob giữ nguyên tất cả fields."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkJob,
            JobStatus,
            RetryStrategy,
        )
        job = BulkJob(
            job_id="job_rt",
            entity_type="invoice",
            action=BulkAction.BATCH_UPDATE,
            entity_ids=["inv1", "inv2", "inv3"],
            chunk_size=50,
            max_concurrency=5,
            max_retries=5,
            retry_strategy=RetryStrategy.LINEAR_BACKOFF,
            timeout_seconds=600,
            tenant_id="tenant_rt",
            operator_id="op_rt",
            metadata={"priority": "high", "batch": True},
        )
        d = job.to_dict()
        restored = BulkJob.from_dict(d)
        assert restored.job_id == "job_rt"
        assert restored.entity_type == "invoice"
        assert restored.action == BulkAction.BATCH_UPDATE
        assert restored.chunk_size == 50
        assert restored.max_concurrency == 5
        assert restored.max_retries == 5
        assert restored.retry_strategy == RetryStrategy.LINEAR_BACKOFF
        assert restored.timeout_seconds == 600
        assert restored.tenant_id == "tenant_rt"
        assert restored.operator_id == "op_rt"
        assert restored.metadata == {"priority": "high", "batch": True}

    def test_from_dict_minimal(self):
        """Kiểm tra from_dict với chỉ keys tối thiểu vẫn tạo được job hợp lệ."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkJob,
            JobStatus,
            RetryStrategy,
        )
        data = {
            "job_id": "job_min_dict",
            "entity_type": "user",
            "action": "batch_read",
        }
        job = BulkJob.from_dict(data)
        assert job.job_id == "job_min_dict"
        assert job.entity_type == "user"
        assert job.action == BulkAction.BATCH_READ
        assert job.entity_ids == []
        assert job.chunk_size == 100
        assert job.max_concurrency == 10

    def test_from_dict_with_status(self):
        """Kiểm tra from_dict parse đúng status từ string."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkJob, JobStatus
        data = {
            "job_id": "job_status",
            "entity_type": "item",
            "action": "batch_update",
            "status": "completed",
        }
        job = BulkJob.from_dict(data)
        assert job.status == JobStatus.COMPLETED

    def test_all_action_types(self):
        """Kiểm tra job có thể tạo với tất cả 4 loại action."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkJob
        for action in BulkAction:
            job = BulkJob(
                job_id=f"job_{action.value}",
                entity_type="test",
                action=action,
            )
            assert job.action == action


# ===========================================================================
# Test BulkChunk
# ===========================================================================


class TestBulkChunk:
    """Kiểm tra dataclass BulkChunk — tạo, validate, serialize, nested results."""

    def test_create_valid_chunk_with_all_fields(self):
        """Kiểm tra tạo chunk hợp lệ với đầy đủ thông tin."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkChunk, ChunkStatus
        chunk = BulkChunk(
            chunk_id="chunk_001",
            job_id="job_001",
            chunk_number=1,
            entity_ids=["e1", "e2", "e3"],
        )
        assert chunk.chunk_id == "chunk_001"
        assert chunk.job_id == "job_001"
        assert chunk.chunk_number == 1
        assert chunk.status == ChunkStatus.PENDING
        assert chunk.succeeded == 0
        assert chunk.failed == 0
        assert chunk.skipped == 0
        assert chunk.results == []

    def test_create_chunk_minimal(self):
        """Kiểm tra tạo chunk với fields tối thiểu."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkChunk
        chunk = BulkChunk(
            chunk_id="chunk_min",
            job_id="job_min",
            chunk_number=1,
        )
        assert chunk.entity_ids == []

    def test_create_chunk_empty_id_raises_error(self):
        """Kiểm tra tạo chunk với chunk_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkChunk
        with pytest.raises(MidicoderError):
            BulkChunk(
                chunk_id="",
                job_id="job_001",
                chunk_number=1,
            )

    def test_create_chunk_whitespace_id_raises_error(self):
        """Kiểm tra tạo chunk với chunk_id chỉ khoảng trắng sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkChunk
        with pytest.raises(MidicoderError):
            BulkChunk(
                chunk_id="   ",
                job_id="job_001",
                chunk_number=1,
            )

    def test_chunk_to_dict(self):
        """Kiểm tra chuyển BulkChunk sang dict."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkChunk
        chunk = BulkChunk(
            chunk_id="chunk_dict",
            job_id="job_dict",
            chunk_number=2,
            entity_ids=["a", "b"],
        )
        d = chunk.to_dict()
        assert d["chunk_id"] == "chunk_dict"
        assert d["job_id"] == "job_dict"
        assert d["chunk_number"] == 2
        assert d["status"] == "pending"
        assert d["entity_ids"] == ["a", "b"]
        assert d["results"] == []
        assert d["started_at"] is None
        assert d["completed_at"] is None

    def test_chunk_to_dict_with_results(self):
        """Kiểm tra to_dict serialize nested results đúng cách."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkChunk, BulkResult
        chunk = BulkChunk(
            chunk_id="chunk_res",
            job_id="job_res",
            chunk_number=1,
            entity_ids=["e1", "e2"],
        )
        chunk.results.append(BulkResult(entity_id="e1", success=True))
        chunk.results.append(BulkResult(entity_id="e2", success=False, error="fail"))
        chunk.succeeded = 1
        chunk.failed = 1

        d = chunk.to_dict()
        assert len(d["results"]) == 2
        assert d["results"][0]["entity_id"] == "e1"
        assert d["results"][0]["success"] is True
        assert d["results"][1]["success"] is False
        assert d["results"][1]["error"] == "fail"
        assert d["succeeded"] == 1
        assert d["failed"] == 1

    def test_chunk_from_dict(self):
        """Kiểm tra tạo BulkChunk từ dict."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkChunk,
            ChunkStatus,
        )
        data = {
            "chunk_id": "chunk_fc",
            "job_id": "job_fc",
            "chunk_number": 3,
            "entity_ids": ["x", "y", "z"],
            "status": "processing",
        }
        chunk = BulkChunk.from_dict(data)
        assert chunk.chunk_id == "chunk_fc"
        assert chunk.chunk_number == 3
        assert chunk.status == ChunkStatus.PROCESSING
        assert len(chunk.entity_ids) == 3

    def test_chunk_default_values(self):
        """Kiểm tra các giá trị mặc định của BulkChunk."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkChunk, ChunkStatus
        chunk = BulkChunk(
            chunk_id="chunk_def",
            job_id="job_def",
            chunk_number=1,
        )
        assert chunk.status == ChunkStatus.PENDING
        assert chunk.succeeded == 0
        assert chunk.failed == 0
        assert chunk.skipped == 0
        assert chunk.results == []
        assert chunk.started_at is None
        assert chunk.completed_at is None


# ===========================================================================
# Test BulkResult
# ===========================================================================


class TestBulkResult:
    """Kiểm tra dataclass BulkResult — tạo, success/failed, auto timestamp."""

    def test_create_success_result(self):
        """Kiểm tra tạo result thành công."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkResult
        result = BulkResult(entity_id="e1", success=True)
        assert result.entity_id == "e1"
        assert result.success is True
        assert result.error is None
        assert result.retry_count == 0

    def test_create_failed_result(self):
        """Kiểm tra tạo result thất bại với error message."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkResult
        result = BulkResult(
            entity_id="e2",
            success=False,
            error="Validation failed",
            retry_count=2,
        )
        assert result.success is False
        assert result.error == "Validation failed"
        assert result.retry_count == 2

    def test_auto_processed_at(self):
        """Kiểm tra tự động đặt processed_at khi không cung cấp."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkResult
        result = BulkResult(entity_id="e_ts")
        assert result.processed_at is not None
        assert result.processed_at.tzinfo is not None

    def test_custom_processed_at(self):
        """Kiểm tra processed_at tùy chỉnh không bị ghi đè."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkResult
        now = datetime.now(timezone.utc)
        result = BulkResult(entity_id="e_custom", processed_at=now)
        assert result.processed_at == now

    def test_result_to_dict(self):
        """Kiểm tra chuyển BulkResult sang dict."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkResult
        result = BulkResult(
            entity_id="e1",
            success=True,
            retry_count=1,
            metadata={"rows_affected": 1},
        )
        d = result.to_dict()
        assert d["entity_id"] == "e1"
        assert d["success"] is True
        assert d["retry_count"] == 1
        assert d["metadata"] == {"rows_affected": 1}
        assert d["processed_at"] is not None

    def test_result_to_dict_failed(self):
        """Kiểm tra to_dict với result thất bại."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkResult
        result = BulkResult(
            entity_id="e_fail",
            success=False,
            error="Connection timeout",
            retry_count=3,
        )
        d = result.to_dict()
        assert d["success"] is False
        assert d["error"] == "Connection timeout"
        assert d["retry_count"] == 3

    def test_result_from_dict(self):
        """Kiểm tra tạo BulkResult từ dict."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkResult
        data = {
            "entity_id": "e_fc",
            "success": False,
            "error": "Timeout",
            "retry_count": 2,
            "metadata": {"attempt": 3},
        }
        result = BulkResult.from_dict(data)
        assert result.entity_id == "e_fc"
        assert result.success is False
        assert result.error == "Timeout"
        assert result.retry_count == 2
        assert result.metadata == {"attempt": 3}

    def test_result_from_dict_minimal(self):
        """Kiểm tra from_dict với chỉ entity_id vẫn tạo được result hợp lệ."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkResult
        data = {"entity_id": "e_min"}
        result = BulkResult.from_dict(data)
        assert result.entity_id == "e_min"
        assert result.success is True
        assert result.error is None
        assert result.retry_count == 0

    def test_result_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize BulkResult giữ nguyên."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkResult
        result = BulkResult(
            entity_id="e_rt",
            success=True,
            retry_count=0,
            metadata={"key": "value"},
        )
        d = result.to_dict()
        restored = BulkResult.from_dict(d)
        assert restored.entity_id == "e_rt"
        assert restored.success is True
        assert restored.retry_count == 0
        assert restored.metadata == {"key": "value"}

    def test_result_default_values(self):
        """Kiểm tra các giá trị mặc định của BulkResult."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkResult
        result = BulkResult(entity_id="e_def")
        assert result.success is True
        assert result.error is None
        assert result.retry_count == 0
        assert result.metadata == {}


# ===========================================================================
# Test DLQEntry
# ===========================================================================


class TestDLQEntry:
    """Kiểm tra dataclass DLQEntry — tạo, validate, replay flow, serialize."""

    def test_create_valid_dlq_entry(self):
        """Kiểm tra tạo DLQ entry hợp lệ với đầy đủ thông tin."""
        from midicoder.packs.cp_full_bulk_etl.models import DLQEntry
        entry = DLQEntry(
            entry_id="dlq_001",
            job_id="job_001",
            entity_id="e1",
            entity_type="user",
            error="Connection timeout",
            error_type="TimeoutError",
            retry_count=3,
            original_data={"name": "test"},
        )
        assert entry.entry_id == "dlq_001"
        assert entry.job_id == "job_001"
        assert entry.entity_id == "e1"
        assert entry.entity_type == "user"
        assert entry.retry_count == 3
        assert entry.replayed is False
        assert entry.replayed_at is None

    def test_create_dlq_entry_minimal(self):
        """Kiểm tra tạo DLQ entry với fields tối thiểu."""
        from midicoder.packs.cp_full_bulk_etl.models import DLQEntry
        entry = DLQEntry(
            entry_id="dlq_min",
            job_id="job_min",
            entity_id="e_min",
        )
        assert entry.entity_type == ""
        assert entry.error == ""
        assert entry.error_type == ""
        assert entry.original_data == {}

    def test_create_dlq_empty_entry_id_raises_error(self):
        """Kiểm tra tạo DLQ entry với entry_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import DLQEntry
        with pytest.raises(MidicoderError):
            DLQEntry(
                entry_id="",
                job_id="job_001",
                entity_id="e1",
            )

    def test_create_dlq_whitespace_entry_id_raises_error(self):
        """Kiểm tra tạo DLQ entry với entry_id chỉ khoảng trắng sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import DLQEntry
        with pytest.raises(MidicoderError):
            DLQEntry(
                entry_id="   ",
                job_id="job_001",
                entity_id="e1",
            )

    def test_auto_failed_at(self):
        """Kiểm tra tự động đặt failed_at khi không cung cấp."""
        from midicoder.packs.cp_full_bulk_etl.models import DLQEntry
        entry = DLQEntry(
            entry_id="dlq_ts",
            job_id="job_ts",
            entity_id="e_ts",
        )
        assert entry.failed_at is not None
        assert entry.failed_at.tzinfo is not None

    def test_custom_failed_at_preserved(self):
        """Kiểm tra failed_at tùy chỉnh không bị ghi đè."""
        from midicoder.packs.cp_full_bulk_etl.models import DLQEntry
        now = datetime.now(timezone.utc)
        entry = DLQEntry(
            entry_id="dlq_custom_ts",
            job_id="job_ts",
            entity_id="e_ts",
            failed_at=now,
        )
        assert entry.failed_at == now

    def test_dlq_to_dict(self):
        """Kiểm tra chuyển DLQEntry sang dict."""
        from midicoder.packs.cp_full_bulk_etl.models import DLQEntry
        entry = DLQEntry(
            entry_id="dlq_dict",
            job_id="job_dict",
            entity_id="e_dict",
            entity_type="order",
            error="Max retries exceeded",
            error_type="RetryExhausted",
            retry_count=5,
            original_data={"order_id": "o1"},
        )
        d = entry.to_dict()
        assert d["entry_id"] == "dlq_dict"
        assert d["job_id"] == "job_dict"
        assert d["entity_id"] == "e_dict"
        assert d["entity_type"] == "order"
        assert d["error"] == "Max retries exceeded"
        assert d["error_type"] == "RetryExhausted"
        assert d["retry_count"] == 5
        assert d["original_data"] == {"order_id": "o1"}
        assert d["replayed"] is False
        assert d["replayed_at"] is None

    def test_dlq_from_dict(self):
        """Kiểm tra tạo DLQEntry từ dict."""
        from midicoder.packs.cp_full_bulk_etl.models import DLQEntry
        data = {
            "entry_id": "dlq_fc",
            "job_id": "job_fc",
            "entity_id": "e_fc",
            "entity_type": "invoice",
            "error": "Failed",
            "error_type": "Error",
            "retry_count": 3,
            "original_data": {"key": "val"},
            "replayed": True,
        }
        entry = DLQEntry.from_dict(data)
        assert entry.entry_id == "dlq_fc"
        assert entry.entity_type == "invoice"
        assert entry.retry_count == 3
        assert entry.replayed is True

    def test_dlq_from_dict_minimal(self):
        """Kiểm tra from_dict với chỉ keys tối thiểu vẫn tạo được entry hợp lệ."""
        from midicoder.packs.cp_full_bulk_etl.models import DLQEntry
        data = {
            "entry_id": "dlq_min_fc",
            "job_id": "job_min",
            "entity_id": "e_min",
        }
        entry = DLQEntry.from_dict(data)
        assert entry.entry_id == "dlq_min_fc"
        assert entry.entity_type == ""
        assert entry.error == ""
        assert entry.replayed is False

    def test_dlq_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize DLQEntry giữ nguyên."""
        from midicoder.packs.cp_full_bulk_etl.models import DLQEntry
        entry = DLQEntry(
            entry_id="dlq_rt",
            job_id="job_rt",
            entity_id="e_rt",
            entity_type="product",
            error="Test error",
            retry_count=2,
            original_data={"sku": "ABC"},
        )
        d = entry.to_dict()
        restored = DLQEntry.from_dict(d)
        assert restored.entry_id == "dlq_rt"
        assert restored.job_id == "job_rt"
        assert restored.entity_id == "e_rt"
        assert restored.entity_type == "product"
        assert restored.error == "Test error"
        assert restored.retry_count == 2
        assert restored.original_data == {"sku": "ABC"}
        assert restored.replayed is False

    def test_dlq_default_values(self):
        """Kiểm tra các giá trị mặc định của DLQEntry."""
        from midicoder.packs.cp_full_bulk_etl.models import DLQEntry
        entry = DLQEntry(
            entry_id="dlq_def",
            job_id="job_def",
            entity_id="e_def",
        )
        assert entry.entity_type == ""
        assert entry.error == ""
        assert entry.error_type == ""
        assert entry.retry_count == 0
        assert entry.original_data == {}
        assert entry.replayed is False
        assert entry.replayed_at is None

    def test_replay_flow(self):
        """Kiểm tra replay: set replayed=True và replayed_at tự động."""
        from midicoder.packs.cp_full_bulk_etl.models import DLQEntry
        entry = DLQEntry(
            entry_id="dlq_replay",
            job_id="job_rep",
            entity_id="e_rep",
        )
        assert entry.replayed is False
        assert entry.replayed_at is None

        # Simulate replay
        entry.replayed = True
        entry.replayed_at = datetime.now(timezone.utc)
        assert entry.replayed is True
        assert entry.replayed_at is not None
        assert entry.replayed_at.tzinfo is not None


# ===========================================================================
# Test BulkEngine
# ===========================================================================


class TestBulkEngine:
    """Kiểm tra class BulkEngine — CRUD job, process, cancel, retry, DLQ."""

    def test_create_engine(self):
        """Kiểm tra tạo BulkEngine mới."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkEngine
        engine = BulkEngine()
        assert engine is not None
        assert engine.jobs == {}
        assert engine.chunks == {}
        assert engine.dlq == []

    def test_create_job_success(self):
        """Kiểm tra tạo job thành công qua engine."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkEngine,
            JobStatus,
        )
        engine = BulkEngine()
        job = engine.create_job(
            job_id="job_engine",
            entity_type="user",
            action=BulkAction.BATCH_UPDATE,
            entity_ids=["u1", "u2", "u3"],
            chunk_size=100,
        )
        assert job.job_id == "job_engine"
        assert job.status == JobStatus.PENDING
        assert job.total_records == 3
        assert "job_engine" in engine.jobs

    def test_create_job_with_all_options(self):
        """Kiểm tra tạo job với tất cả options tùy chỉnh."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkEngine,
            RetryStrategy,
        )
        engine = BulkEngine()
        job = engine.create_job(
            job_id="job_opts",
            entity_type="order",
            action=BulkAction.BATCH_DELETE,
            entity_ids=["o1"],
            chunk_size=50,
            max_concurrency=5,
            max_retries=5,
            retry_strategy=RetryStrategy.LINEAR_BACKOFF,
            timeout_seconds=600,
            tenant_id="t1",
            operator_id="op1",
            metadata={"key": "value"},
        )
        assert job.chunk_size == 50
        assert job.max_concurrency == 5
        assert job.max_retries == 5
        assert job.retry_strategy == RetryStrategy.LINEAR_BACKOFF
        assert job.timeout_seconds == 600
        assert job.tenant_id == "t1"
        assert job.operator_id == "op1"
        assert job.metadata == {"key": "value"}

    def test_create_duplicate_job_raises_error(self):
        """Kiểm tra tạo job trùng job_id sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkEngine
        engine = BulkEngine()
        engine.create_job("job_dup", "user", BulkAction.BATCH_UPDATE, ["u1"])
        with pytest.raises(MidicoderError):
            engine.create_job("job_dup", "user", BulkAction.BATCH_UPDATE, ["u2"])

    def test_process_job_creates_correct_chunks(self):
        """Kiểm tra process_job chia entity_ids thành chunks đúng số lượng."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkEngine,
            JobStatus,
        )
        engine = BulkEngine()
        # 250 records với chunk_size=100 -> 3 chunks
        ids = [f"e{i}" for i in range(250)]
        engine.create_job("job_chunks", "item", BulkAction.BATCH_UPDATE, ids, chunk_size=100)
        engine.process_job("job_chunks")

        job = engine.jobs["job_chunks"]
        assert job.status == JobStatus.COMPLETED
        assert job.processed == 250
        assert job.succeeded == 250
        assert job.failed == 0
        # Verify chunks were created
        chunk_ids = [c for c in engine.chunks if c.startswith("job_chunks")]
        assert len(chunk_ids) == 3

    def test_process_job_single_chunk(self):
        """Kiểm tra process_job với số record <= chunk_size tạo 1 chunk."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkEngine,
            JobStatus,
        )
        engine = BulkEngine()
        ids = [f"e{i}" for i in range(50)]
        engine.create_job("job_single", "item", BulkAction.BATCH_UPDATE, ids, chunk_size=100)
        engine.process_job("job_single")

        job = engine.jobs["job_single"]
        assert job.status == JobStatus.COMPLETED
        assert job.processed == 50
        assert job.succeeded == 50
        chunk_ids = [c for c in engine.chunks if c.startswith("job_single")]
        assert len(chunk_ids) == 1

    def test_process_job_empty_entity_ids(self):
        """Kiểm tra process_job với 0 entity_ids không tạo chunk."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkEngine,
            JobStatus,
        )
        engine = BulkEngine()
        engine.create_job("job_empty", "item", BulkAction.BATCH_READ, entity_ids=[])
        engine.process_job("job_empty")

        job = engine.jobs["job_empty"]
        assert job.status == JobStatus.COMPLETED
        assert job.processed == 0
        assert job.succeeded == 0
        chunk_ids = [c for c in engine.chunks if c.startswith("job_empty")]
        assert len(chunk_ids) == 0

    def test_process_nonexistent_job_raises_error(self):
        """Kiểm tra process_job với job_id không tồn tại sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkEngine
        engine = BulkEngine()
        with pytest.raises(MidicoderError):
            engine.process_job("nonexistent")

    def test_process_already_running_job_returns_early(self):
        """Kiểm tra process_job với job đang RUNNING trả về early (branch coverage)."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkEngine,
            JobStatus,
        )
        engine = BulkEngine()
        engine.create_job("job_running", "user", BulkAction.BATCH_UPDATE, ["u1"])
        # Manual set status to RUNNING
        engine.jobs["job_running"].status = JobStatus.RUNNING
        # Process again — should return early without changing state
        result = engine.process_job("job_running")
        assert result.status == JobStatus.RUNNING
        assert result.processed == 0  # Không processed vì return early

    def test_process_job_all_failed_returns_failed_status(self):
        """Kiểm tra job status FAILED khi tất cả records thất bại (monkeypatch _process_chunk)."""
        import unittest.mock
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkChunk,
            BulkEngine,
            BulkResult,
            ChunkStatus,
            JobStatus,
        )
        engine = BulkEngine()
        engine.create_job("job_all_fail", "item", BulkAction.BATCH_UPDATE, ["i1", "i2"], chunk_size=100)

        # Monkeypatch _process_chunk để simulation tất cả failed
        def failed_chunk_process(chunk: BulkChunk) -> BulkChunk:
            chunk.status = ChunkStatus.COMPLETED
            for entity_id in chunk.entity_ids:
                chunk.results.append(BulkResult(entity_id=entity_id, success=False, error="simulated failure"))
                chunk.failed += 1
            return chunk

        with unittest.mock.patch.object(engine, "_process_chunk", side_effect=failed_chunk_process):
            engine.process_job("job_all_fail")

        job = engine.jobs["job_all_fail"]
        assert job.status == JobStatus.FAILED
        assert job.failed == 2
        assert job.succeeded == 0

    def test_get_progress_before_processing(self):
        """Kiểm tra get_progress trả về đúng trạng thái trước khi xử lý."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkEngine
        engine = BulkEngine()
        engine.create_job("job_prog", "user", BulkAction.BATCH_UPDATE, ["u1", "u2"])
        progress = engine.get_progress("job_prog")

        assert progress["job_id"] == "job_prog"
        assert progress["status"] == "pending"
        assert progress["total"] == 2
        assert progress["processed"] == 0
        assert progress["succeeded"] == 0
        assert progress["failed"] == 0
        assert progress["percentage"] == 0

    def test_get_progress_after_processing(self):
        """Kiểm tra get_progress trả về đúng tiến độ sau khi xử lý."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkEngine
        engine = BulkEngine()
        engine.create_job("job_prog2", "user", BulkAction.BATCH_UPDATE, ["u1", "u2", "u3"])
        engine.process_job("job_prog2")
        progress = engine.get_progress("job_prog2")

        assert progress["status"] == "completed"
        assert progress["total"] == 3
        assert progress["processed"] == 3
        assert progress["succeeded"] == 3
        assert progress["failed"] == 0
        assert progress["percentage"] == 100.0

    def test_get_progress_empty_job(self):
        """Kiểm tra get_progress với job có 0 entity_ids không bị chia cho 0."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkEngine
        engine = BulkEngine()
        engine.create_job("job_zero", "item", BulkAction.BATCH_READ, entity_ids=[])
        progress = engine.get_progress("job_zero")
        assert progress["total"] == 0
        assert progress["percentage"] == 0

    def test_get_progress_nonexistent_job_raises_error(self):
        """Kiểm tra get_progress với job không tồn tại sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkEngine
        engine = BulkEngine()
        with pytest.raises(MidicoderError):
            engine.get_progress("nonexistent")

    def test_cancel_job(self):
        """Kiểm tra hủy job thành công chuyển status thành CANCELLED."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkEngine,
            JobStatus,
        )
        engine = BulkEngine()
        engine.create_job("job_cancel", "user", BulkAction.BATCH_DELETE, ["u1"])
        engine.cancel_job("job_cancel")
        job = engine.jobs["job_cancel"]

        assert job.status == JobStatus.CANCELLED
        assert job.completed_at is not None

    def test_cancel_nonexistent_job_raises_error(self):
        """Kiểm tra hủy job không tồn tại sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkEngine
        engine = BulkEngine()
        with pytest.raises(MidicoderError):
            engine.cancel_job("nonexistent")

    def test_retry_record_within_max_retries(self):
        """Kiểm tra retry record chưa hết retries trả về BulkResult success."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkEngine,
            BulkResult,
        )
        engine = BulkEngine()
        engine.create_job("job_retry", "user", BulkAction.BATCH_UPDATE, ["u1"], max_retries=3)
        result = engine.retry_record("job_retry", "u1", current_retry=1)

        assert isinstance(result, BulkResult)
        assert result.success is True
        assert result.retry_count == 2

    def test_retry_record_exhausted_returns_dlq(self):
        """Kiểm tra retry record hết retries trả về DLQEntry."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkEngine,
            DLQEntry,
        )
        engine = BulkEngine()
        engine.create_job("job_dlq", "user", BulkAction.BATCH_UPDATE, ["u1"], max_retries=3)
        result = engine.retry_record("job_dlq", "u1", current_retry=3)

        assert isinstance(result, DLQEntry)
        assert result.job_id == "job_dlq"
        assert result.entity_id == "u1"
        assert result.retry_count == 3
        # Entry should be added to DLQ
        assert len(engine.dlq) == 1

    def test_retry_record_nonexistent_job_raises_error(self):
        """Kiểm tra retry record với job không tồn tại sẽ ném lỗi."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkEngine
        engine = BulkEngine()
        with pytest.raises(MidicoderError):
            engine.retry_record("nonexistent", "u1")

    def test_get_dlq_entries_all(self):
        """Kiểm tra lấy tất cả DLQ entries không filter."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkEngine
        engine = BulkEngine()
        dlq = engine.get_dlq_entries()
        assert isinstance(dlq, list)
        assert len(dlq) == 0

    def test_get_dlq_entries_filtered_by_job_id(self):
        """Kiểm tra lọc DLQ entries theo job_id."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkEngine,
        )
        engine = BulkEngine()
        engine.create_job("job_a", "user", BulkAction.BATCH_UPDATE, ["u1"], max_retries=1)
        engine.create_job("job_b", "user", BulkAction.BATCH_UPDATE, ["u2"], max_retries=1)

        # Add entries to DLQ
        engine.retry_record("job_a", "u1", current_retry=1)
        engine.retry_record("job_b", "u2", current_retry=1)

        # Filter by job_a
        dlq_a = engine.get_dlq_entries(job_id="job_a")
        assert len(dlq_a) == 1
        assert dlq_a[0].job_id == "job_a"

        # Filter by job_b
        dlq_b = engine.get_dlq_entries(job_id="job_b")
        assert len(dlq_b) == 1
        assert dlq_b[0].job_id == "job_b"

        # All entries
        dlq_all = engine.get_dlq_entries()
        assert len(dlq_all) == 2

    def test_replay_dlq_success(self):
        """Kiểm tra replay DLQ entry thành công."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkEngine,
        )
        engine = BulkEngine()
        engine.create_job("job_replay", "user", BulkAction.BATCH_UPDATE, ["u1"], max_retries=1)
        engine.retry_record("job_replay", "u1", current_retry=1)

        entry = engine.dlq[0]
        assert entry.replayed is False

        result = engine.replay_dlq(entry.entry_id)
        assert result is True
        assert entry.replayed is True
        assert entry.replayed_at is not None

    def test_replay_dlq_nonexistent_entry(self):
        """Kiểm tra replay DLQ entry không tồn tại trả về False."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkEngine
        engine = BulkEngine()
        result = engine.replay_dlq("nonexistent")
        assert result is False

    def test_replay_dlq_wrong_id_in_nonempty_dlq(self):
        """Kiểm tra replay DLQ với ID sai khi DLQ có entries (hit branch 755→754)."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkEngine,
        )
        engine = BulkEngine()
        engine.create_job("job_rep_dlq", "user", BulkAction.BATCH_UPDATE, ["u1"], max_retries=1)
        engine.retry_record("job_rep_dlq", "u1", current_retry=1)

        # DLQ có 1 entry, thử replay với ID sai → iterate qua loop rồi return False
        result = engine.replay_dlq("wrong_id")
        assert result is False
        # Entry gốc không bị ảnh hưởng
        assert len(engine.dlq) == 1
        assert engine.dlq[0].replayed is False

    def test_process_job_sets_completed_at(self):
        """Kiểm tra process_job tự động set completed_at khi hoàn thành."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkEngine
        engine = BulkEngine()
        engine.create_job("job_complete_ts", "item", BulkAction.BATCH_UPDATE, ["i1"])
        engine.process_job("job_complete_ts")

        job = engine.jobs["job_complete_ts"]
        assert job.completed_at is not None
        assert job.updated_at == job.completed_at

    def test_chunk_numbering_is_sequential(self):
        """Kiểm tra chunk được đánh số thứ tự đúng."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkEngine
        engine = BulkEngine()
        ids = [f"e{i}" for i in range(250)]
        engine.create_job("job_seq", "item", BulkAction.BATCH_UPDATE, ids, chunk_size=100)
        engine.process_job("job_seq")

        chunk_ids = [c for c in engine.chunks if c.startswith("job_seq")]
        chunks = [engine.chunks[cid] for cid in chunk_ids]
        chunk_numbers = [c.chunk_number for c in chunks]
        assert chunk_numbers == [1, 2, 3]

    def test_job_has_completed_at_after_process(self):
        """Kiểm tra job có completed_at sau khi process xong."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkEngine
        engine = BulkEngine()
        engine.create_job("job_ca", "item", BulkAction.BATCH_CREATE, ["x"])
        job_before = engine.jobs["job_ca"]
        assert job_before.completed_at is None

        engine.process_job("job_ca")
        job_after = engine.jobs["job_ca"]
        assert job_after.completed_at is not None

    def test_create_job_default_metadata(self):
        """Kiểm tra metadata mặc định là dict rỗng khi không cung cấp."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkEngine
        engine = BulkEngine()
        job = engine.create_job(
            job_id="job_meta",
            entity_type="user",
            action=BulkAction.BATCH_READ,
            entity_ids=["u1"],
        )
        assert job.metadata == {}


# ===========================================================================
# Test Integration — Chunk và Result liên kết
# ===========================================================================


class TestIntegration:
    """Kiểm tra integration giữa BulkJob, BulkChunk, và BulkResult."""

    def test_job_chunks_results_flow(self):
        """Kiểm tra flow đầy đủ: job -> chunks -> results."""
        from midicoder.packs.cp_full_bulk_etl.models import (
            BulkAction,
            BulkChunk,
            BulkEngine,
            BulkResult,
            ChunkStatus,
            JobStatus,
        )
        engine = BulkEngine()
        ids = [f"e{i}" for i in range(150)]  # 150 records, chunk_size=100 -> 2 chunks
        engine.create_job(
            job_id="job_flow",
            entity_type="item",
            action=BulkAction.BATCH_UPDATE,
            entity_ids=ids,
            chunk_size=100,
        )
        engine.process_job("job_flow")

        job = engine.jobs["job_flow"]
        assert job.status == JobStatus.COMPLETED
        assert job.processed == 150
        assert job.succeeded == 150

        # Kiểm tra chunks
        chunk_ids = [c for c in engine.chunks if c.startswith("job_flow")]
        assert len(chunk_ids) == 2

        chunks = [engine.chunks[cid] for cid in chunk_ids]
        for chunk in chunks:
            assert isinstance(chunk, BulkChunk)
            assert chunk.status == ChunkStatus.COMPLETED
            assert chunk.started_at is not None
            assert chunk.completed_at is not None
            for result in chunk.results:
                assert isinstance(result, BulkResult)
                assert result.success is True

    def test_chunk_entity_distribution(self):
        """Kiểm tra entities được phân phối đều vào các chunks."""
        from midicoder.packs.cp_full_bulk_etl.models import BulkAction, BulkEngine
        engine = BulkEngine()
        ids = [f"e{i}" for i in range(250)]
        engine.create_job("job_dist", "item", BulkAction.BATCH_UPDATE, ids, chunk_size=100)
        engine.process_job("job_dist")

        chunk_ids = [c for c in engine.chunks if c.startswith("job_dist")]
        chunks = sorted([engine.chunks[cid] for cid in chunk_ids], key=lambda c: c.chunk_number)

        # Chunk 1: 100 entities (0-99)
        assert len(chunks[0].entity_ids) == 100
        # Chunk 2: 100 entities (100-199)
        assert len(chunks[1].entity_ids) == 100
        # Chunk 3: 50 entities (200-249)
        assert len(chunks[2].entity_ids) == 50
