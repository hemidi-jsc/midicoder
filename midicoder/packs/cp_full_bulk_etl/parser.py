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

from midicoder.packs.cp_full_bulk_etl.models import (
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


# ===========================================================================
# ETL Parser (từ CP38)
# ===========================================================================

from midicoder.packs.cp_full_bulk_etl.models import (
    ETLImportError,
    ETLImportFormat,
    ETLJob,
    ETLJobStatus,
    ETLStep,
    ExportJob,
    ETLPBulkConfig,
    ImportJob,
    LoadMode,
    TransformType,
)


@dataclass
class ETLIR:
    """Intermediate Representation cho CP38 — Import/Export/ETL.

    Gom tập tất cả cấu hình import jobs, export jobs,
    ETL pipelines, và bulk configuration từ DSL.

    Attributes:
        import_jobs: Danh sách import jobs
        export_jobs: Danh sách export jobs
        etl_jobs: Danh sách ETL pipelines
        bulk_config: Cấu hình bulk operation (optional)
    """
    import_jobs: list[ImportJob] = field(default_factory=list)
    export_jobs: list[ExportJob] = field(default_factory=list)
    etl_jobs: list[ETLJob] = field(default_factory=list)
    bulk_config: ETLPBulkConfig | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "import_jobs": [j.to_dict() for j in self.import_jobs],
            "export_jobs": [j.to_dict() for j in self.export_jobs],
            "etl_jobs": [j.to_dict() for j in self.etl_jobs],
            "bulk_config": self.bulk_config.to_dict() if self.bulk_config else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ETLIR":
        import_jobs = [ImportJob.from_dict(j) for j in data.get("import_jobs", [])]
        export_jobs = [ExportJob.from_dict(j) for j in data.get("export_jobs", [])]
        etl_jobs = [ETLJob.from_dict(j) for j in data.get("etl_jobs", [])]
        bulk_data = data.get("bulk_config")
        bulk_config = ETLPBulkConfig.from_dict(bulk_data) if bulk_data else None
        return cls(
            import_jobs=import_jobs,
            export_jobs=export_jobs,
            etl_jobs=etl_jobs,
            bulk_config=bulk_config,
        )


def parse_import_jobs(data: dict[str, Any]) -> list[ImportJob]:
    """Parse danh sách import jobs từ DSL dict."""
    raw_jobs = data.get("import_jobs", data.get("imports", []))
    jobs = []
    for j in raw_jobs:
        errors_data = j.get("errors", [])
        errors = [ETLImportError(
            row_number=e.get("row_number", 0),
            column=e.get("column", ""),
            error_message=e.get("error_message", ""),
        ) for e in errors_data]

        jobs.append(ImportJob(
            job_key=j.get("job_key", ""),
            target_entity=j.get("target_entity", ""),
            source_file=j.get("source_file"),
            format=ETLImportFormat(j.get("format", "csv")),
            status=ETLJobStatus(j.get("status", "pending")),
            total_rows=j.get("total_rows", 0),
            success_rows=j.get("success_rows", 0),
            failed_rows=j.get("failed_rows", 0),
            skipped_rows=j.get("skipped_rows", 0),
            errors=errors,
            tenant_id=j.get("tenant_id"),
        ))
    return jobs


def parse_export_jobs(data: dict[str, Any]) -> list[ExportJob]:
    """Parse danh sách export jobs từ DSL dict."""
    raw_jobs = data.get("export_jobs", data.get("exports", []))
    jobs = []
    for j in raw_jobs:
        jobs.append(ExportJob(
            job_key=j.get("job_key", ""),
            entity=j.get("entity", ""),
            format=ETLImportFormat(j.get("format", "csv")),
            filters=j.get("filters", {}),
            status=ETLJobStatus(j.get("status", "pending")),
            output_path=j.get("output_path"),
            total_rows=j.get("total_rows", 0),
            tenant_id=j.get("tenant_id"),
        ))
    return jobs


def parse_etl_pipelines(data: dict[str, Any]) -> list[ETLJob]:
    """Parse danh sách ETL pipelines từ DSL dict."""
    raw_pipelines = data.get("etl_pipelines", data.get("pipelines", []))
    jobs = []
    for p in raw_pipelines:
        steps_data = p.get("steps", [])
        steps = []
        for s in steps_data:
            step_type = s.get("step_type", "extract")
            config = s.get("config", {})
            steps.append(ETLStep(
                step_key=s.get("step_key", ""),
                step_type=step_type,
                config=config,
                order=s.get("order", len(steps)),
            ))

        jobs.append(ETLJob(
            job_key=p.get("job_key", ""),
            steps=steps,
            status=ETLJobStatus(p.get("status", "pending")),
            total_rows_processed=p.get("total_rows_processed", 0),
        ))
    return jobs


def parse_to_etl_ir(data: dict[str, Any]) -> ETLIR:
    """Parse DSL dict thành ETLIR (từ CP38)."""
    import_jobs = parse_import_jobs(data)
    export_jobs = parse_export_jobs(data)
    etl_jobs = parse_etl_pipelines(data)

    bulk_data = data.get("bulk_config", {})
    bulk_config = None
    if bulk_data:
        bulk_config = ETLPBulkConfig(
            chunk_size=bulk_data.get("chunk_size", 1000),
            max_retries=bulk_data.get("max_retries", 3),
            rollback_threshold=bulk_data.get("rollback_threshold", 0.1),
        )

    return ETLIR(
        import_jobs=import_jobs,
        export_jobs=export_jobs,
        etl_jobs=etl_jobs,
        bulk_config=bulk_config,
    )


__all__ = [
    "BulkIR",
    "parse_bulk_jobs",
    "parse_bulk_config",
    "parse_dlq_config",
    "parse_to_ir",
    # CP38 ETL exports
    "ETLIR",
    "parse_import_jobs",
    "parse_export_jobs",
    "parse_etl_pipelines",
    "parse_to_etl_ir",
]
