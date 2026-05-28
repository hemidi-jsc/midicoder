# coding: utf-8
"""
Mô-đun models cho CP44 — Bulk Operations Engine.

Định nghĩa các dataclass biểu diễn:
- BulkAction: Loại thao tác bulk (batch_create, batch_update, batch_delete, batch_read)
- JobStatus: Trạng thái job (pending, running, completed, failed, cancelled, timeout)
- ChunkStatus: Trạng thái chunk (pending, processing, completed, failed)
- RetryStrategy: Chiến lược retry (exponential_backoff, fixed_delay, linear_backoff)
- BulkJob: Công việc bulk với cấu hình chunk, concurrency, retry
- BulkChunk: Chunk dữ liệu trong job
- BulkResult: Kết quả xử lý từng entity
- DLQEntry: Bản ghi trong Dead Letter Queue
- BulkEngine: Engine xử lý bulk operations (in-memory simulation)

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP44).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class BulkAction(str, Enum):
    """Loại thao tác bulk.

    - BATCH_CREATE: Tạo hàng loạt record mới
    - BATCH_UPDATE: Cập nhật hàng loạt record tồn tại
    - BATCH_DELETE: Xóa hàng loạt record
    - BATCH_READ: Đọc hàng loạt record
    """
    BATCH_CREATE = "batch_create"
    BATCH_UPDATE = "batch_update"
    BATCH_DELETE = "batch_delete"
    BATCH_READ = "batch_read"


class JobStatus(str, Enum):
    """Trạng thái của bulk job.

    - PENDING: Đợi xử lý
    - RUNNING: Đang xử lý
    - COMPLETED: Hoàn thành thành công
    - FAILED: Thất bại
    - CANCELLED: Đã bị hủy
    - TIMEOUT: Hết thời gian chờ
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ChunkStatus(str, Enum):
    """Trạng thái của chunk.

    - PENDING: Đợi xử lý
    - PROCESSING: Đang xử lý
    - COMPLETED: Hoàn thành
    - FAILED: Thất bại
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RetryStrategy(str, Enum):
    """Chiến lược retry cho record thất bại.

    - EXPONENTIAL_BACKOFF: Khoảng thời gian retry tăng theo hàm mũ
    - FIXED_DELAY: Khoảng thời gian retry cố định
    - LINEAR_BACKOFF: Khoảng thời gian retry tăng tuyến tính
    """
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"


# ===========================================================================
# BulkJob
# ===========================================================================


@dataclass
class BulkJob:
    """Công việc bulk operations.

    Đại diện cho một công việc xử lý hàng loạt trên entities, bao gồm
    loại thao tác, danh sách entity IDs, và cấu hình xử lý (chunk size,
    concurrency, retry, timeout).

    Attributes:
        job_id: ID duy nhất của job
        entity_type: Loại entity được xử lý (ví dụ: 'user', 'product')
        action: Loại thao tác bulk
        entity_ids: Danh sách ID của các entity cần xử lý
        status: Trạng thái hiện tại của job
        chunk_size: Số record trong mỗi chunk (mặc định: 100)
        max_concurrency: Số chunk tối đa xử lý song song (mặc định: 10)
        max_retries: Số lần retry tối đa cho từng record (mặc định: 3)
        retry_strategy: Chiến lược retry (mặc định: exponential_backoff)
        timeout_seconds: Thời gian chờ tối đa của job (mặc định: 300)
        total_records: Tổng số record cần xử lý
        processed: Số record đã xử lý
        succeeded: Số record thành công
        failed: Số record thất bại
        skipped: Số record bị bỏ qua
        tenant_id: ID tenant (cho multi-tenant)
        operator_id: ID người tạo job
        metadata: Dữ liệu bổ sung
        created_at: Thời điểm tạo job
        updated_at: Thời điểm cập nhật cuối
        completed_at: Thời điểm hoàn thành
    """
    job_id: str
    entity_type: str
    action: BulkAction
    entity_ids: list[str] = field(default_factory=list)
    status: JobStatus = JobStatus.PENDING
    chunk_size: int = 100
    max_concurrency: int = 10
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    timeout_seconds: int = 300
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    tenant_id: str = ""
    operator_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate job sau khi khởi tạo."""
        if not self.job_id or not self.job_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_BULK_JOB_NOT_FOUND,
                reason="job_id bắt buộc và không được để trống",
            )

        if self.chunk_size < 1:
            raise EM.raise_error(
                ErrorCode.MDC-F28_BULK_CHUNK_SIZE_INVALID,
                reason=f"chunk_size phải lớn hơn 0, nhận được: {self.chunk_size}",
            )

        if self.max_concurrency < 1:
            raise EM.raise_error(
                ErrorCode.MDC-F28_BULK_CONCURRENCY_INVALID,
                reason=f"max_concurrency phải lớn hơn 0, nhận được: {self.max_concurrency}",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @property
    def total_records(self) -> int:
        """Tổng số record cần xử lý."""
        return len(self.entity_ids)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển BulkJob sang dict."""
        return {
            "job_id": self.job_id,
            "entity_type": self.entity_type,
            "action": self.action.value,
            "entity_ids": self.entity_ids,
            "status": self.status.value,
            "chunk_size": self.chunk_size,
            "max_concurrency": self.max_concurrency,
            "max_retries": self.max_retries,
            "retry_strategy": self.retry_strategy.value,
            "timeout_seconds": self.timeout_seconds,
            "total_records": self.total_records,
            "processed": self.processed,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped": self.skipped,
            "tenant_id": self.tenant_id,
            "operator_id": self.operator_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BulkJob":
        """Tạo BulkJob từ dict."""
        return cls(
            job_id=data["job_id"],
            entity_type=data["entity_type"],
            action=BulkAction(data["action"]),
            entity_ids=data.get("entity_ids", []),
            status=JobStatus(data.get("status", "pending")),
            chunk_size=data.get("chunk_size", 100),
            max_concurrency=data.get("max_concurrency", 10),
            max_retries=data.get("max_retries", 3),
            retry_strategy=RetryStrategy(data.get("retry_strategy", "exponential_backoff")),
            timeout_seconds=data.get("timeout_seconds", 300),
            tenant_id=data.get("tenant_id", ""),
            operator_id=data.get("operator_id", ""),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# BulkChunk
# ===========================================================================


@dataclass
class BulkChunk:
    """Chunk dữ liệu trong bulk job.

    Đại diện cho một nhóm entities được xử lý cùng nhau trong
    bulk job. Mỗi chunk chứa một subset của entity IDs.

    Attributes:
        chunk_id: ID duy nhất của chunk
        job_id: ID của job chứa chunk này
        chunk_number: Số thứ tự của chunk (bắt đầu từ 1)
        entity_ids: Danh sách entity IDs trong chunk
        status: Trạng thái hiện tại
        succeeded: Số record thành công trong chunk
        failed: Số record thất bại trong chunk
        skipped: Số record bị bỏ qua trong chunk
        results: Danh sách kết quả chi tiết
        started_at: Thời điểm bắt đầu xử lý
        completed_at: Thời điểm hoàn thành
    """
    chunk_id: str
    job_id: str
    chunk_number: int
    entity_ids: list[str] = field(default_factory=list)
    status: ChunkStatus = ChunkStatus.PENDING
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    results: list[BulkResult] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate chunk sau khi khởi tạo."""
        if not self.chunk_id or not self.chunk_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_BULK_JOB_NOT_FOUND,
                reason="chunk_id bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển BulkChunk sang dict."""
        return {
            "chunk_id": self.chunk_id,
            "job_id": self.job_id,
            "chunk_number": self.chunk_number,
            "entity_ids": self.entity_ids,
            "status": self.status.value,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped": self.skipped,
            "results": [r.to_dict() for r in self.results],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BulkChunk":
        """Tạo BulkChunk từ dict."""
        return cls(
            chunk_id=data["chunk_id"],
            job_id=data["job_id"],
            chunk_number=data["chunk_number"],
            entity_ids=data.get("entity_ids", []),
            status=ChunkStatus(data.get("status", "pending")),
        )


# ===========================================================================
# BulkResult
# ===========================================================================


@dataclass
class BulkResult:
    """Kết quả xử lý từng entity.

    Attributes:
        entity_id: ID của entity được xử lý
        success: Thành công hay không
        error: Thông báo lỗi (nếu thất bại)
        retry_count: Số lần đã retry
        metadata: Dữ liệu bổ sung
        processed_at: Thời điểm xử lý
    """
    entity_id: str
    success: bool = True
    error: str | None = None
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    processed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate result sau khi khởi tạo."""
        if self.processed_at is None:
            self.processed_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển BulkResult sang dict."""
        return {
            "entity_id": self.entity_id,
            "success": self.success,
            "error": self.error,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BulkResult":
        """Tạo BulkResult từ dict."""
        return cls(
            entity_id=data["entity_id"],
            success=data.get("success", True),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# DLQEntry
# ===========================================================================


@dataclass
class DLQEntry:
    """Bản ghi trong Dead Letter Queue.

    Chứa thông tin về entity thất bại sau khi đã hết số lần retry,
    để có thể replay sau này.

    Attributes:
        entry_id: ID duy nhất của entry
        job_id: ID của job gốc
        entity_id: ID của entity thất bại
        entity_type: Loại entity
        error: Thông báo lỗi
        error_type: Loại lỗi
        retry_count: Số lần đã retry trước khi vào DLQ
        original_data: Dữ liệu gốc của entity
        failed_at: Thời điểm thất bại
        replayed: Đã được replay chưa
        replayed_at: Thời điểm replay
    """
    entry_id: str
    job_id: str
    entity_id: str
    entity_type: str = ""
    error: str = ""
    error_type: str = ""
    retry_count: int = 0
    original_data: dict[str, Any] = field(default_factory=dict)
    failed_at: datetime | None = None
    replayed: bool = False
    replayed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate DLQ entry sau khi khởi tạo."""
        if not self.entry_id or not self.entry_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_BULK_DLQ_FULL,
                reason="entry_id bắt buộc và không được để trống",
            )

        if self.failed_at is None:
            self.failed_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DLQEntry sang dict."""
        return {
            "entry_id": self.entry_id,
            "job_id": self.job_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "error": self.error,
            "error_type": self.error_type,
            "retry_count": self.retry_count,
            "original_data": self.original_data,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "replayed": self.replayed,
            "replayed_at": self.replayed_at.isoformat() if self.replayed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DLQEntry":
        """Tạo DLQEntry từ dict."""
        return cls(
            entry_id=data["entry_id"],
            job_id=data["job_id"],
            entity_id=data["entity_id"],
            entity_type=data.get("entity_type", ""),
            error=data.get("error", ""),
            error_type=data.get("error_type", ""),
            retry_count=data.get("retry_count", 0),
            original_data=data.get("original_data", {}),
            replayed=data.get("replayed", False),
        )


# ===========================================================================
# BulkEngine
# ===========================================================================


class BulkEngine:
    """Engine xử lý bulk operations (in-memory simulation).

    Quản lý vòng đời của bulk jobs: tạo job, chia chunks, xử lý
    parallel với asyncio, retry cho record thất bại, và DLQ management.

    Đây là in-memory simulation để testing và demonstration.
    Trong thực tế, engine sẽ tích hợp với database và message queue.

    Attributes:
        jobs: Từ điển chứa tất cả jobs (job_id -> BulkJob)
        chunks: Từ điển chứa tất cả chunks (chunk_id -> BulkChunk)
        dlq: Danh sách các entry trong Dead Letter Queue
    """

    def __init__(self) -> None:
        """Khởi tạo BulkEngine."""
        self.jobs: dict[str, BulkJob] = {}
        self.chunks: dict[str, BulkChunk] = {}
        self.dlq: list[DLQEntry] = []

    def create_job(
        self,
        job_id: str,
        entity_type: str,
        action: BulkAction,
        entity_ids: list[str],
        chunk_size: int = 100,
        max_concurrency: int = 10,
        max_retries: int = 3,
        retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        timeout_seconds: int = 300,
        tenant_id: str = "",
        operator_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> BulkJob:
        """Tạo bulk job mới.

        Args:
            job_id: ID duy nhất của job
            entity_type: Loại entity
            action: Loại thao tác
            entity_ids: Danh sách entity IDs
            chunk_size: Số record mỗi chunk
            max_concurrency: Số chunk xử lý song song
            max_retries: Số lần retry tối đa
            retry_strategy: Chiến lược retry
            timeout_seconds: Thời gian chờ tối đa
            tenant_id: ID tenant
            operator_id: ID người tạo
            metadata: Dữ liệu bổ sung

        Returns:
            BulkJob đã tạo

        Raises:
            MidicoderError: Nếu job_id đã tồn tại
        """
        if job_id in self.jobs:
            raise EM.raise_error(
                ErrorCode.MDC-F28_BULK_JOB_ALREADY_RUNNING,
                reason=f"Job '{job_id}' đã tồn tại",
            )

        job = BulkJob(
            job_id=job_id,
            entity_type=entity_type,
            action=action,
            entity_ids=entity_ids,
            chunk_size=chunk_size,
            max_concurrency=max_concurrency,
            max_retries=max_retries,
            retry_strategy=retry_strategy,
            timeout_seconds=timeout_seconds,
            tenant_id=tenant_id,
            operator_id=operator_id,
            metadata=metadata or {},
        )

        self.jobs[job_id] = job
        return job

    def get_progress(self, job_id: str) -> dict[str, Any]:
        """Lấy tiến độ xử lý của job.

        Args:
            job_id: ID của job

        Returns:
            Dict chứa thông tin tiến độ

        Raises:
            MidicoderError: Nếu job không tồn tại
        """
        if job_id not in self.jobs:
            raise EM.raise_error(
                ErrorCode.MDC-F28_BULK_JOB_NOT_FOUND,
                reason=f"Job '{job_id}' không tồn tại",
            )

        job = self.jobs[job_id]
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "total": job.total_records,
            "processed": job.processed,
            "succeeded": job.succeeded,
            "failed": job.failed,
            "skipped": job.skipped,
            "percentage": (job.processed / job.total_records * 100) if job.total_records > 0 else 0,
        }

    def process_job(self, job_id: str) -> BulkJob:
        """Xử lý bulk job (simulation).

        Chia entity_ids thành các chunks và xử lý tuần tự.
        Trong thực tế, sẽ dùng asyncio để xử lý parallel.

        Args:
            job_id: ID của job cần xử lý

        Returns:
            BulkJob đã xử lý

        Raises:
            MidicoderError: Nếu job không tồn tại
        """
        if job_id not in self.jobs:
            raise EM.raise_error(
                ErrorCode.MDC-F28_BULK_JOB_NOT_FOUND,
                reason=f"Job '{job_id}' không tồn tại",
            )

        job = self.jobs[job_id]
        if job.status == JobStatus.RUNNING:
            return job

        job.status = JobStatus.RUNNING
        job.updated_at = datetime.now(timezone.utc)

        # Chia thành các chunks
        chunks = self._create_chunks(job)

        # Xử lý từng chunk (simulation - trong thực tế dùng asyncio.gather)
        for chunk in chunks:
            self._process_chunk(chunk)

        # Cập nhật trạng thái job
        job.processed = job.total_records
        job.succeeded = sum(c.succeeded for c in chunks)
        job.failed = sum(c.failed for c in chunks)
        job.skipped = sum(c.skipped for c in chunks)

        if job.failed > 0 and job.succeeded == 0:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.COMPLETED

        job.completed_at = datetime.now(timezone.utc)
        job.updated_at = job.completed_at

        return job

    def _create_chunks(self, job: BulkJob) -> list[BulkChunk]:
        """Chia entity_ids thành các chunks.

        Args:
            job: BulkJob cần chia chunks

        Returns:
            Danh sách BulkChunk
        """
        chunks = []
        total = len(job.entity_ids)
        num_chunks = math.ceil(total / job.chunk_size) if total > 0 else 0

        for i in range(num_chunks):
            start = i * job.chunk_size
            end = min(start + job.chunk_size, total)
            chunk_ids = job.entity_ids[start:end]

            chunk = BulkChunk(
                chunk_id=f"{job.job_id}_chunk_{i + 1}",
                job_id=job.job_id,
                chunk_number=i + 1,
                entity_ids=chunk_ids,
            )

            self.chunks[chunk.chunk_id] = chunk
            chunks.append(chunk)

        return chunks

    def _process_chunk(self, chunk: BulkChunk) -> BulkChunk:
        """Xử lý một chunk (simulation).

        Args:
            chunk: BulkChunk cần xử lý

        Returns:
            BulkChunk đã xử lý
        """
        chunk.status = ChunkStatus.PROCESSING
        chunk.started_at = datetime.now(timezone.utc)

        for entity_id in chunk.entity_ids:
            result = BulkResult(
                entity_id=entity_id,
                success=True,
            )
            chunk.results.append(result)
            chunk.succeeded += 1

        chunk.status = ChunkStatus.COMPLETED
        chunk.completed_at = datetime.now(timezone.utc)

        return chunk

    def cancel_job(self, job_id: str) -> BulkJob:
        """Hủy bulk job đang chạy.

        Args:
            job_id: ID của job cần hủy

        Returns:
            BulkJob đã hủy

        Raises:
            MidicoderError: Nếu job không tồn tại
        """
        if job_id not in self.jobs:
            raise EM.raise_error(
                ErrorCode.MDC-F28_BULK_JOB_NOT_FOUND,
                reason=f"Job '{job_id}' không tồn tại",
            )

        job = self.jobs[job_id]
        job.status = JobStatus.CANCELLED
        job.updated_at = datetime.now(timezone.utc)
        job.completed_at = job.updated_at

        return job

    def retry_record(
        self,
        job_id: str,
        entity_id: str,
        current_retry: int = 0,
    ) -> BulkResult | DLQEntry:
        """Retry xử lý record thất bại.

        Args:
            job_id: ID của job
            entity_id: ID của entity cần retry
            current_retry: Số lần retry hiện tại

        Returns:
            BulkResult nếu thành công, DLQEntry nếu hết retry

        Raises:
            MidicoderError: Nếu job không tồn tại
        """
        if job_id not in self.jobs:
            raise EM.raise_error(
                ErrorCode.MDC-F28_BULK_JOB_NOT_FOUND,
                reason=f"Job '{job_id}' không tồn tại",
            )

        job = self.jobs[job_id]

        # Simulation: retry luôn thành công
        if current_retry < job.max_retries:
            return BulkResult(
                entity_id=entity_id,
                success=True,
                retry_count=current_retry + 1,
            )
        else:
            # Hết retry → gửi vào DLQ
            entry = DLQEntry(
                entry_id=f"dlq_{uuid.uuid4().hex[:8]}",
                job_id=job_id,
                entity_id=entity_id,
                entity_type=job.entity_type,
                error="Max retries exceeded",
                retry_count=current_retry,
            )
            self.dlq.append(entry)
            return entry

    def get_dlq_entries(self, job_id: str | None = None) -> list[DLQEntry]:
        """Lấy danh sách entries trong DLQ.

        Args:
            job_id: Filter theo job ID (optional)

        Returns:
            Danh sách DLQEntry
        """
        if job_id:
            return [e for e in self.dlq if e.job_id == job_id]
        return list(self.dlq)

    def replay_dlq(self, entry_id: str) -> bool:
        """Replay entry từ DLQ.

        Args:
            entry_id: ID của DLQ entry

        Returns:
            True nếu thành công
        """
        for entry in self.dlq:
            if entry.entry_id == entry_id:
                entry.replayed = True
                entry.replayed_at = datetime.now(timezone.utc)
                return True
        return False


__all__ = [
    # Enums
    "BulkAction",
    "JobStatus",
    "ChunkStatus",
    "RetryStrategy",
    # Dataclasses
    "BulkJob",
    "BulkChunk",
    "BulkResult",
    "DLQEntry",
    # Engine
    "BulkEngine",
]


# ===========================================================================
# ETL / Import / Export models (từ CP38)
# ===========================================================================

from datetime import timezone as dt_timezone


class ETLImportFormat(str, Enum):
    """Định dạng file import (từ CP38).

    - CSV: File CSV với delimiter
    - JSON: File JSON (array of objects)
    """
    CSV = "csv"
    JSON = "json"


class ETLJobStatus(str, Enum):
    """Trạng thái của import/export/ETL job (từ CP38).

    - PENDING: Đang chờ chạy
    - RUNNING: Đang chạy
    - COMPLETED: Đã hoàn thành
    - FAILED: Đã thất bại
    - CANCELLED: Đã bị hủy
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransformType(str, Enum):
    """Loại transform trong ETL mapping (từ CP38).

    - MAP: Ánh xạ giá trị
    - FILTER: Lọc dữ liệu theo điều kiện
    - AGGREGATE: Tổng hợp dữ liệu (sum, count, avg)
    - CONVERT: Chuyển đổi kiểu dữ liệu
    - RENAME: Đổi tên cột/field
    """
    MAP = "map"
    FILTER = "filter"
    AGGREGATE = "aggregate"
    CONVERT = "convert"
    RENAME = "rename"


class ExtractSource(str, Enum):
    """Nguồn dữ liệu cho extract step (từ CP38).

    - FILE: File trên hệ thống
    - DATABASE: CSDL (SQL query)
    - API: REST API endpoint
    """
    FILE = "file"
    DATABASE = "database"
    API = "api"


class LoadMode(str, Enum):
    """Chế độ load dữ liệu vào target (từ CP38).

    - INSERT: Chỉ chèn mới
    - UPDATE: Chỉ cập nhật bản ghi có sẵn
    - UPSERT: Chèn mới hoặc cập nhật nếu đã tồn tại
    - DELETE: Xóa bản ghi theo key
    """
    INSERT = "insert"
    UPDATE = "update"
    UPSERT = "upsert"
    DELETE = "delete"


class SchemaFormat(str, Enum):
    """Định dạng schema được hỗ trợ (từ CP38).

    - AVRO: Apache Avro schema
    - PROTOBUF: Google Protocol Buffers
    - JSON_SCHEMA: JSON Schema (Draft 7+)
    - SQL: SQL DDL (CREATE TABLE)
    """
    AVRO = "avro"
    PROTOBUF = "protobuf"
    JSON_SCHEMA = "json_schema"
    SQL = "sql"


class CompatibilityMode(str, Enum):
    """Chế độ kiểm tra tương thích khi evolve schema (từ CP38).

    - BACKWARD: Schema mới có thể đọc dữ liệu từ schema cũ
    - FORWARD: Schema cũ có thể đọc dữ liệu từ schema mới
    - BACKWARD_FORWARD: Cả backward và forward tương thích
    - FULL: Full tương thích (cả hai chiều)
    - NONE: Không kiểm tra tương thích
    """
    BACKWARD = "backward"
    FORWARD = "forward"
    BACKWARD_FORWARD = "backward_forward"
    FULL = "full"
    NONE = "none"


@dataclass
class ETLImportError:
    """Lỗi gặp phải trong quá trình import một hàng (từ CP38).

    Attributes:
        row_number: Số thứ tự hàng (1-indexed)
        column: Tên cột/giá trị gặp lỗi
        error_message: Mô tả chi tiết lỗi
    """
    row_number: int
    column: str = ""
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_number": self.row_number,
            "column": self.column,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ETLImportError":
        return cls(
            row_number=data.get("row_number", 0),
            column=data.get("column", ""),
            error_message=data.get("error_message", ""),
        )


@dataclass
class ImportJob:
    """Job import dữ liệu từ file vào entity (từ CP38).

    Attributes:
        job_key: Identifier duy nhất cho job
        target_entity: Entity đích nhận dữ liệu import
        source_file: Đường dẫn file nguồn (optional)
        format: Định dạng file (csv/json)
        status: Trạng thái hiện tại của job
        total_rows: Tổng số hàng trong file
        success_rows: Số hàng import thành công
        failed_rows: Số hàng import thất bại
        skipped_rows: Số hàng bị bỏ qua
        errors: Danh sách lỗi chi tiết theo từng hàng
        tenant_id: Tenant ID cho multi-tenant scope
        started_at: Thời điểm bắt đầu chạy job
        completed_at: Thời điểm hoàn thành job
        created_at: Thời điểm tạo job
    """
    job_key: str
    target_entity: str
    source_file: str | None = None
    format: ETLImportFormat = ETLImportFormat.CSV
    status: ETLJobStatus = ETLJobStatus.PENDING
    total_rows: int = 0
    success_rows: int = 0
    failed_rows: int = 0
    skipped_rows: int = 0
    errors: list[ETLImportError] = field(default_factory=list)
    tenant_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.job_key or not self.job_key.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_DUPLICATE_JOB_KEY,
                job_key=self.job_key,
                reason="Job key không được để trống",
            )
        if not self.target_entity or not self.target_entity.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_TARGET_ENTITY_NOT_FOUND,
                reason="Target entity không được để trống",
            )
        if self.total_rows < self.success_rows + self.failed_rows + self.skipped_rows:
            raise EM.raise_error(
                ErrorCode.MDC-F28_INVALID_COLUMN_MAPPING,
                detail=f"total_rows ({self.total_rows}) < sum of sub-rows",
                reason="Tổng số hàng phải >= sum của các hàng con",
            )
        if self.created_at is None:
            self.created_at = datetime.now(dt_timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_key": self.job_key,
            "target_entity": self.target_entity,
            "source_file": self.source_file,
            "format": self.format.value,
            "status": self.status.value,
            "total_rows": self.total_rows,
            "success_rows": self.success_rows,
            "failed_rows": self.failed_rows,
            "skipped_rows": self.skipped_rows,
            "errors": [e.to_dict() for e in self.errors],
            "tenant_id": self.tenant_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImportJob":
        errors_data = data.get("errors", [])
        errors = [ETLImportError.from_dict(e) for e in errors_data]
        return cls(
            job_key=data.get("job_key", ""),
            target_entity=data.get("target_entity", ""),
            source_file=data.get("source_file"),
            format=ETLImportFormat(data.get("format", "csv")),
            status=ETLJobStatus(data.get("status", "pending")),
            total_rows=data.get("total_rows", 0),
            success_rows=data.get("success_rows", 0),
            failed_rows=data.get("failed_rows", 0),
            skipped_rows=data.get("skipped_rows", 0),
            errors=errors,
            tenant_id=data.get("tenant_id"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


@dataclass
class ExportJob:
    """Job export dữ liệu từ entity ra file (từ CP38).

    Attributes:
        job_key: Identifier duy nhất cho job
        entity: Entity nguồn cần export
        format: Định dạng file output (csv/json)
        filters: Bộ lọc dữ liệu (dict key-value)
        status: Trạng thái hiện tại của job
        output_path: Đường dẫn file output
        total_rows: Tổng số hàng đã export
        tenant_id: Tenant ID cho multi-tenant scope
        created_at: Thời điểm tạo job
    """
    job_key: str
    entity: str
    format: ETLImportFormat = ETLImportFormat.CSV
    filters: dict[str, Any] = field(default_factory=dict)
    status: ETLJobStatus = ETLJobStatus.PENDING
    output_path: str | None = None
    total_rows: int = 0
    tenant_id: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.job_key or not self.job_key.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_DUPLICATE_JOB_KEY,
                job_key=self.job_key,
                reason="Job key không được để trống",
            )
        if self.created_at is None:
            self.created_at = datetime.now(dt_timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_key": self.job_key,
            "entity": self.entity,
            "format": self.format.value,
            "filters": self.filters,
            "status": self.status.value,
            "output_path": self.output_path,
            "total_rows": self.total_rows,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExportJob":
        return cls(
            job_key=data.get("job_key", ""),
            entity=data.get("entity", ""),
            format=ETLImportFormat(data.get("format", "csv")),
            filters=data.get("filters", {}),
            status=ETLJobStatus(data.get("status", "pending")),
            output_path=data.get("output_path"),
            total_rows=data.get("total_rows", 0),
            tenant_id=data.get("tenant_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


@dataclass
class ETLMapping:
    """Ánh xạ cột source sang field target với transform (từ CP38).

    Attributes:
        mapping_key: Identifier duy nhất cho mapping này
        source_column: Tên cột trong dữ liệu nguồn
        target_field: Tên field trong entity đích
        transform: Loại transform (map/filter/aggregate/convert/rename)
        params: Tham số chi tiết cho transform
    """
    mapping_key: str
    source_column: str
    target_field: str
    transform: TransformType | None = None
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.mapping_key or not self.mapping_key.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_INVALID_COLUMN_MAPPING,
                detail="mapping_key",
                reason="Mapping key không được để trống",
            )
        if not self.source_column or not self.source_column.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_INVALID_COLUMN_MAPPING,
                detail="source_column",
                reason="Source column không được để trống",
            )
        if not self.target_field or not self.target_field.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_INVALID_COLUMN_MAPPING,
                detail="target_field",
                reason="Target field không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "mapping_key": self.mapping_key,
            "source_column": self.source_column,
            "target_field": self.target_field,
            "transform": self.transform.value if self.transform else None,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ETLMapping":
        transform_value = data.get("transform")
        transform = TransformType(transform_value) if transform_value else None
        return cls(
            mapping_key=data.get("mapping_key", ""),
            source_column=data.get("source_column", ""),
            target_field=data.get("target_field", ""),
            transform=transform,
            params=data.get("params", {}),
        )


@dataclass
class ExtractConfig:
    """Cấu hình extract dữ liệu từ source (từ CP38).

    Attributes:
        source: Nguồn dữ liệu (file/database/api)
        file_path: Đường dẫn file (khi source=file)
        query: SQL query (khi source=database)
        table: Tên bảng (khi source=database)
        delimiter: Ký tự phân cách (khi source=file, format=csv)
    """
    source: ExtractSource
    file_path: str | None = None
    query: str | None = None
    table: str | None = None
    delimiter: str = ","

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source.value,
            "file_path": self.file_path,
            "query": self.query,
            "table": self.table,
            "delimiter": self.delimiter,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtractConfig":
        return cls(
            source=ExtractSource(data.get("source", "file")),
            file_path=data.get("file_path"),
            query=data.get("query"),
            table=data.get("table"),
            delimiter=data.get("delimiter", ","),
        )


@dataclass
class ETLTransformConfig:
    """Cấu hình transform step trong ETL (từ CP38).

    Attributes:
        step_type: Loại transform
        params: Tham số chi tiết cho transform
    """
    step_type: TransformType
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_type": self.step_type.value,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ETLTransformConfig":
        return cls(
            step_type=TransformType(data.get("step_type", "map")),
            params=data.get("params", {}),
        )


@dataclass
class LoadConfig:
    """Cấu hình load dữ liệu vào target entity (từ CP38).

    Attributes:
        target_entity: Entity đích nhận dữ liệu
        mode: Chế độ load (insert/update/upsert/delete)
        upsert_key: Field dùng để xác định bản ghi khi upsert
    """
    target_entity: str
    mode: LoadMode = LoadMode.INSERT
    upsert_key: str | None = None

    def __post_init__(self) -> None:
        if not self.target_entity or not self.target_entity.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_TARGET_ENTITY_NOT_FOUND,
                reason="Target entity không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_entity": self.target_entity,
            "mode": self.mode.value,
            "upsert_key": self.upsert_key,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LoadConfig":
        return cls(
            target_entity=data.get("target_entity", ""),
            mode=LoadMode(data.get("mode", "insert")),
            upsert_key=data.get("upsert_key"),
        )


@dataclass
class ETLStep:
    """Một bước trong ETL pipeline (từ CP38).

    Attributes:
        step_key: Identifier duy nhất cho step
        step_type: Loại step (extract/transform/load hoặc TransformType)
        config: Cấu hình chi tiết cho step
        order: Thứ tự thực thi (0 = đầu tiên)
    """
    step_key: str
    step_type: str  # "extract", "load", hoặc TransformType
    config: dict[str, Any] = field(default_factory=dict)
    order: int = 0

    def __post_init__(self) -> None:
        if not self.step_key or not self.step_key.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_INVALID_ETL_STEP_TYPE,
                step_type=self.step_type,
                reason="Step key không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_key": self.step_key,
            "step_type": self.step_type,
            "config": self.config,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ETLStep":
        return cls(
            step_key=data.get("step_key", ""),
            step_type=data.get("step_type", "extract"),
            config=data.get("config", {}),
            order=data.get("order", 0),
        )


@dataclass
class ETLJob:
    """Job ETL hoàn chỉnh với nhiều steps (từ CP38).

    Attributes:
        job_key: Identifier duy nhất cho job
        steps: Danh sách ETL steps theo thứ tự
        status: Trạng thái hiện tại của job
        total_rows_processed: Tổng số hàng đã xử lý
        created_at: Thời điểm tạo job
    """
    job_key: str
    steps: list[ETLStep] = field(default_factory=list)
    status: ETLJobStatus = ETLJobStatus.PENDING
    total_rows_processed: int = 0
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.job_key or not self.job_key.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_DUPLICATE_JOB_KEY,
                job_key=self.job_key,
                reason="Job key không được để trống",
            )
        has_extract = any(s.step_type == "extract" for s in self.steps)
        if not has_extract:
            raise EM.raise_error(
                ErrorCode.MDC-F28_ETL_MISSING_EXTRACT_STEP,
                reason="ETL pipeline phải có ít nhất 1 extract step",
            )
        has_load = any(s.step_type == "load" for s in self.steps)
        if not has_load:
            raise EM.raise_error(
                ErrorCode.MDC-F28_ETL_MISSING_LOAD_STEP,
                reason="ETL pipeline phải có ít nhất 1 load step",
            )
        if self.created_at is None:
            self.created_at = datetime.now(dt_timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_key": self.job_key,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status.value,
            "total_rows_processed": self.total_rows_processed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ETLJob":
        steps_data = data.get("steps", [])
        steps = [ETLStep.from_dict(s) for s in steps_data]
        return cls(
            job_key=data.get("job_key", ""),
            steps=steps,
            status=ETLJobStatus(data.get("status", "pending")),
            total_rows_processed=data.get("total_rows_processed", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


@dataclass
class ETLPBulkConfig:
    """Cấu hình cho bulk operation — import/export với số lượng lớn (từ CP38).

    Attributes:
        chunk_size: Số bản ghi xử lý mỗi lần (mặc định 1000)
        max_retries: Số lần thử lại tối đa khi lỗi (mặc định 3)
        rollback_threshold: Tỷ lệ lỗi cho phép trước khi rollback (mặc định 0.1)
    """
    chunk_size: int = 1000
    max_retries: int = 3
    rollback_threshold: float = 0.1

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise EM.raise_error(
                ErrorCode.MDC-F28_INVALID_BULK_CHUNK_SIZE,
                reason=f"Chunk size phải lớn hơn 0, nhận được: {self.chunk_size}",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_size": self.chunk_size,
            "max_retries": self.max_retries,
            "rollback_threshold": self.rollback_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ETLPBulkConfig":
        return cls(
            chunk_size=data.get("chunk_size", 1000),
            max_retries=data.get("max_retries", 3),
            rollback_threshold=data.get("rollback_threshold", 0.1),
        )


@dataclass
class SchemaDefinition:
    """Schema definition với versioning (từ CP38).

    Attributes:
        id: Identifier duy nhất cho schema
        name: Tên mô tả của schema
        format: Định dạng schema (avro/protobuf/json_schema/sql)
        version: Phiên bản semver của schema (mặc định "1.0.0")
        subject: Subject name trong schema registry (mặc định "")
        schema_content: Nội dung raw của schema (JSON/AVDL/Proto/DDL)
        properties: Các property mở rộng (mặc định {})
    """
    id: str
    name: str
    format: SchemaFormat
    version: str = "1.0.0"
    subject: str = ""
    schema_content: str = ""
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_SCHEMA_NOT_FOUND,
                schema_id=self.id,
                reason="Schema ID không được để trống",
            )
        if not self.name or not self.name.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_INVALID_SCHEMA_FORMAT,
                format=self.format.value,
                reason="Schema name không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "format": self.format.value,
            "version": self.version,
            "subject": self.subject,
            "schema_content": self.schema_content,
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchemaDefinition":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            format=SchemaFormat(data.get("format", "avro")),
            version=data.get("version", "1.0.0"),
            subject=data.get("subject", ""),
            schema_content=data.get("schema_content", ""),
            properties=data.get("properties", {}),
        )


@dataclass
class SchemaRegistryConfig:
    """Cấu hình schema registry (từ CP38).

    Attributes:
        id: Identifier duy nhất cho registry config
        name: Tên mô tả của registry
        url: URL endpoint của schema registry (mặc định "")
        format: Định dạng schema mặc định (mặc định AVRO)
        compatibility_mode: Chế độ kiểm tra tương thích (mặc định BACKWARD)
        auth_enabled: Bật/tắt xác thực (mặc định False)
        auth_basic_user: Username cho basic auth (mặc định "")
        auth_basic_password: Password cho basic auth (mặc định "")
        schema_lookup_max_size: Kích thước tối đa cache lookup (mặc định 1000)
    """
    id: str
    name: str
    url: str = ""
    format: SchemaFormat = SchemaFormat.AVRO
    compatibility_mode: CompatibilityMode = CompatibilityMode.BACKWARD
    auth_enabled: bool = False
    auth_basic_user: str = ""
    auth_basic_password: str = ""
    schema_lookup_max_size: int = 1000

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_DUPLICATE_SCHEMA_ID,
                schema_id=self.id,
                reason="Registry ID không được để trống",
            )
        if not self.name or not self.name.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_INVALID_SCHEMA_FORMAT,
                format=self.format.value,
                reason="Registry name không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "format": self.format.value,
            "compatibility_mode": self.compatibility_mode.value,
            "auth_enabled": self.auth_enabled,
            "auth_basic_user": self.auth_basic_user,
            "auth_basic_password": self.auth_basic_password,
            "schema_lookup_max_size": self.schema_lookup_max_size,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchemaRegistryConfig":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            url=data.get("url", ""),
            format=SchemaFormat(data.get("format", "avro")),
            compatibility_mode=CompatibilityMode(data.get("compatibility_mode", "backward")),
            auth_enabled=data.get("auth_enabled", False),
            auth_basic_user=data.get("auth_basic_user", ""),
            auth_basic_password=data.get("auth_basic_password", ""),
            schema_lookup_max_size=data.get("schema_lookup_max_size", 1000),
        )


@dataclass
class SchemaEvolutionRule:
    """Quy tắc evolution cho schema (từ CP38).

    Attributes:
        id: Identifier duy nhất cho rule
        schema_id: Schema ID mà rule áp dụng cho
        allowed_operations: Danh sách phép biến đổi được phép (mặc định [])
        auto_evolve: Tự động apply evolution (mặc định False)
        require_approval: Yêu cầu phê duyệt trước khi evolve (mặc định True)
        notification_channels: Các kênh thông báo khi evolve (mặc định [])
    """
    id: str
    schema_id: str
    allowed_operations: list[str] = field(default_factory=list)
    auto_evolve: bool = False
    require_approval: bool = True
    notification_channels: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_DUPLICATE_SCHEMA_ID,
                schema_id=self.id,
                reason="Evolution rule ID không được để trống",
            )
        if not self.schema_id or not self.schema_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F28_SCHEMA_NOT_FOUND,
                schema_id=self.schema_id,
                reason="Schema ID không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "schema_id": self.schema_id,
            "allowed_operations": self.allowed_operations,
            "auto_evolve": self.auto_evolve,
            "require_approval": self.require_approval,
            "notification_channels": self.notification_channels,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchemaEvolutionRule":
        return cls(
            id=data.get("id", ""),
            schema_id=data.get("schema_id", ""),
            allowed_operations=data.get("allowed_operations", []),
            auto_evolve=data.get("auto_evolve", False),
            require_approval=data.get("require_approval", True),
            notification_channels=data.get("notification_channels", []),
        )
