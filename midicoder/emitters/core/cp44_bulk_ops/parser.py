# coding: utf-8
"""
Mô-đun parser cho CP44 — Bulk Operations Engine.

Parse DSL dict (từ contract YAML) sang BulkIR — Intermediate Representation
cho các bulk job configurations, chunk settings, retry strategy,
và DLQ management.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp44_bulk_ops.models import (
    BulkAction,
    BulkJob,
    ChunkStatus,
    JobStatus,
    RetryStrategy,
)


@dataclass
class BulkIR:
    """Intermediate Representation cho CP44.

    Gom tập tất cả cấu hình bulk operations từ DSL, bao gồm
    các bulk job, chunk config, retry strategy, và DLQ config.

    Attributes:
        jobs: Danh sách bulk job configurations
        default_chunk_size: Chunk size mặc định
        default_concurrency: Concurrency mặc định
        default_max_retries: Số lần retry tối đa mặc định
        default_retry_strategy: Chiến lược retry mặc định
        default_timeout: Timeout mặc định (giây)
        dlq_enabled: Có bật DLQ không
        use_events: Có sử dụng event-driven không
        use_audit: Có ghi audit trail không
    """
    jobs: list[BulkJob] = field(default_factory=list)
    default_chunk_size: int = 100
    default_concurrency: int = 10
    default_max_retries: int = 3
    default_retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    default_timeout: int = 300
    dlq_enabled: bool = True
    use_events: bool = True
    use_audit: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Chuyển BulkIR sang dict."""
        return {
            "jobs": [j.to_dict() for j in self.jobs],
            "default_chunk_size": self.default_chunk_size,
            "default_concurrency": self.default_concurrency,
            "default_max_retries": self.default_max_retries,
            "default_retry_strategy": self.default_retry_strategy.value,
            "default_timeout": self.default_timeout,
            "dlq_enabled": self.dlq_enabled,
            "use_events": self.use_events,
            "use_audit": self.use_audit,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BulkIR":
        """Tạo BulkIR từ dict."""
        jobs = [BulkJob.from_dict(j) for j in data.get("jobs", [])]
        return cls(
            jobs=jobs,
            default_chunk_size=data.get("default_chunk_size", 100),
            default_concurrency=data.get("default_concurrency", 10),
            default_max_retries=data.get("default_max_retries", 3),
            default_retry_strategy=RetryStrategy(data.get("default_retry_strategy", "exponential_backoff")),
            default_timeout=data.get("default_timeout", 300),
            dlq_enabled=data.get("dlq_enabled", True),
            use_events=data.get("use_events", True),
            use_audit=data.get("use_audit", True),
        )


def parse_bulk_jobs(data: dict[str, Any]) -> list[BulkJob]:
    """Parse danh sách bulk jobs từ DSL dict.

    Args:
        data: DSL dict với key 'bulk_jobs' hoặc 'jobs'

    Returns:
        Danh sách BulkJob
    """
    raw = data.get("bulk_jobs", data.get("jobs", []))
    jobs = []
    for job_data in raw:
        jobs.append(BulkJob(
            job_id=job_data.get("job_id", job_data.get("id", "")),
            entity_type=job_data.get("entity_type", job_data.get("type", "")),
            action=BulkAction(job_data.get("action", "batch_update")),
            entity_ids=job_data.get("entity_ids", job_data.get("ids", [])),
            chunk_size=job_data.get("chunk_size", 100),
            max_concurrency=job_data.get("max_concurrency", 10),
            max_retries=job_data.get("max_retries", 3),
            retry_strategy=RetryStrategy(job_data.get("retry_strategy", "exponential_backoff")),
            timeout_seconds=job_data.get("timeout_seconds", job_data.get("timeout", 300)),
            tenant_id=job_data.get("tenant_id", ""),
            operator_id=job_data.get("operator_id", ""),
            metadata=job_data.get("metadata", {}),
        ))
    return jobs


def parse_bulk_config(data: dict[str, Any]) -> dict[str, Any]:
    """Parse cấu hình bulk operations từ DSL dict.

    Args:
        data: DSL dict với các config keys

    Returns:
        Dict chứa default_chunk_size, default_concurrency,
        default_max_retries, default_retry_strategy, default_timeout
    """
    return {
        "default_chunk_size": data.get("default_chunk_size", data.get("chunk_size", 100)),
        "default_concurrency": data.get("default_concurrency", data.get("concurrency", 10)),
        "default_max_retries": data.get("default_max_retries", data.get("max_retries", 3)),
        "default_retry_strategy": data.get("default_retry_strategy", data.get("retry_strategy", "exponential_backoff")),
        "default_timeout": data.get("default_timeout", data.get("timeout", 300)),
    }


def parse_dlq_config(data: dict[str, Any]) -> dict[str, Any]:
    """Parse cấu hình DLQ từ DSL dict.

    Args:
        data: DSL dict với key 'dlq' hoặc 'dead_letter_queue'

    Returns:
        Dict chứa dlq_enabled
    """
    dlq_raw = data.get("dlq", data.get("dead_letter_queue", {}))
    if isinstance(dlq_raw, bool):
        return {"dlq_enabled": dlq_raw}
    return {
        "dlq_enabled": dlq_raw.get("enabled", True),
    }


def parse_to_ir(data: dict[str, Any]) -> BulkIR:
    """Parse DSL dict thành BulkIR.

    Args:
        data: DSL dict với jobs, config, dlq, use_events, use_audit

    Returns:
        BulkIR gom tập tất cả parsed data
    """
    jobs = parse_bulk_jobs(data)
    config = parse_bulk_config(data)
    dlq = parse_dlq_config(data)

    return BulkIR(
        jobs=jobs,
        default_chunk_size=config["default_chunk_size"],
        default_concurrency=config["default_concurrency"],
        default_max_retries=config["default_max_retries"],
        default_retry_strategy=RetryStrategy(config["default_retry_strategy"]),
        default_timeout=config["default_timeout"],
        dlq_enabled=dlq["dlq_enabled"],
        use_events=data.get("use_events", True),
        use_audit=data.get("use_audit", True),
    )


__all__ = [
    "BulkIR",
    "parse_bulk_jobs",
    "parse_bulk_config",
    "parse_dlq_config",
    "parse_to_ir",
]
