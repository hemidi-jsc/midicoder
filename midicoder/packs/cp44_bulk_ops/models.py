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
                ErrorCode.CP44_BULK_JOB_NOT_FOUND,
                reason="job_id bắt buộc và không được để trống",
            )

        if self.chunk_size < 1:
            raise EM.raise_error(
                ErrorCode.CP44_BULK_CHUNK_SIZE_INVALID,
                reason=f"chunk_size phải lớn hơn 0, nhận được: {self.chunk_size}",
            )

        if self.max_concurrency < 1:
            raise EM.raise_error(
                ErrorCode.CP44_BULK_CONCURRENCY_INVALID,
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
                ErrorCode.CP44_BULK_JOB_NOT_FOUND,
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
                ErrorCode.CP44_BULK_DLQ_FULL,
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
                ErrorCode.CP44_BULK_JOB_ALREADY_RUNNING,
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
                ErrorCode.CP44_BULK_JOB_NOT_FOUND,
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
                ErrorCode.CP44_BULK_JOB_NOT_FOUND,
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
                ErrorCode.CP44_BULK_JOB_NOT_FOUND,
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
                ErrorCode.CP44_BULK_JOB_NOT_FOUND,
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
