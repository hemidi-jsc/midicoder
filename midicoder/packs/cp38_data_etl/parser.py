# coding: utf-8
"""
Mô-đun parser cho CP38 — Data Import/Export/ETL.

Parse DSL dict (từ contract YAML) sang ETLIR — Intermediate Representation
cho import jobs, export jobs, ETL pipelines, và bulk configuration.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp38_data_etl.models import (
    BulkConfig,
    ETLJob,
    ETLMapping,
    ETLStep,
    ExtractConfig,
    ExtractSource,
    ExportJob,
    ImportError,
    ImportFormat,
    ImportJob,
    JobStatus,
    LoadConfig,
    LoadMode,
    TransformConfig,
    TransformType,
)


@dataclass
class ETLIR:
    """Intermediate Representation cho CP38.

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
    bulk_config: BulkConfig | None = None

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ETLIR sang dict."""
        return {
            "import_jobs": [j.to_dict() for j in self.import_jobs],
            "export_jobs": [j.to_dict() for j in self.export_jobs],
            "etl_jobs": [j.to_dict() for j in self.etl_jobs],
            "bulk_config": self.bulk_config.to_dict() if self.bulk_config else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ETLIR":
        """Tạo ETLIR từ dict."""
        import_jobs = [ImportJob.from_dict(j) for j in data.get("import_jobs", [])]
        export_jobs = [ExportJob.from_dict(j) for j in data.get("export_jobs", [])]
        etl_jobs = [ETLJob.from_dict(j) for j in data.get("etl_jobs", [])]
        bulk_data = data.get("bulk_config")
        bulk_config = BulkConfig.from_dict(bulk_data) if bulk_data else None
        return cls(
            import_jobs=import_jobs,
            export_jobs=export_jobs,
            etl_jobs=etl_jobs,
            bulk_config=bulk_config,
        )


def parse_import_jobs(data: dict[str, Any]) -> list[ImportJob]:
    """Parse danh sách import jobs từ DSL dict.

    Args:
        data: DSL dict với key 'import_jobs' hoặc 'imports'

    Returns:
        Danh sách ImportJob
    """
    raw_jobs = data.get("import_jobs", data.get("imports", []))
    jobs = []
    for j in raw_jobs:
        errors_data = j.get("errors", [])
        errors = [ImportError(
            row_number=e.get("row_number", 0),
            column=e.get("column", ""),
            error_message=e.get("error_message", ""),
        ) for e in errors_data]

        jobs.append(ImportJob(
            job_key=j.get("job_key", ""),
            target_entity=j.get("target_entity", ""),
            source_file=j.get("source_file"),
            format=ImportFormat(j.get("format", "csv")),
            status=JobStatus(j.get("status", "pending")),
            total_rows=j.get("total_rows", 0),
            success_rows=j.get("success_rows", 0),
            failed_rows=j.get("failed_rows", 0),
            skipped_rows=j.get("skipped_rows", 0),
            errors=errors,
            tenant_id=j.get("tenant_id"),
        ))
    return jobs


def parse_export_jobs(data: dict[str, Any]) -> list[ExportJob]:
    """Parse danh sách export jobs từ DSL dict.

    Args:
        data: DSL dict với key 'export_jobs' hoặc 'exports'

    Returns:
        Danh sách ExportJob
    """
    raw_jobs = data.get("export_jobs", data.get("exports", []))
    jobs = []
    for j in raw_jobs:
        jobs.append(ExportJob(
            job_key=j.get("job_key", ""),
            entity=j.get("entity", ""),
            format=ImportFormat(j.get("format", "csv")),
            filters=j.get("filters", {}),
            status=JobStatus(j.get("status", "pending")),
            output_path=j.get("output_path"),
            total_rows=j.get("total_rows", 0),
            tenant_id=j.get("tenant_id"),
        ))
    return jobs


def parse_etl_pipelines(data: dict[str, Any]) -> list[ETLJob]:
    """Parse danh sách ETL pipelines từ DSL dict.

    Args:
        data: DSL dict với key 'etl_pipelines' hoặc 'pipelines'

    Returns:
        Danh sách ETLJob
    """
    raw_pipelines = data.get("etl_pipelines", data.get("pipelines", []))
    jobs = []
    for p in raw_pipelines:
        steps_data = p.get("steps", [])
        steps = []
        for s in steps_data:
            step_type = s.get("step_type", "extract")

            # Build config dict từ step
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
            status=JobStatus(p.get("status", "pending")),
            total_rows_processed=p.get("total_rows_processed", 0),
        ))
    return jobs


def parse_to_ir(data: dict[str, Any]) -> ETLIR:
    """Parse DSL dict thành ETLIR.

    Args:
        data: DSL dict với import_jobs, export_jobs, etl_pipelines, bulk_config

    Returns:
        ETLIR gom tập tất cả parsed data
    """
    import_jobs = parse_import_jobs(data)
    export_jobs = parse_export_jobs(data)
    etl_jobs = parse_etl_pipelines(data)

    bulk_data = data.get("bulk_config", {})
    bulk_config = None
    if bulk_data:
        bulk_config = BulkConfig(
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
    "ETLIR",
    "parse_import_jobs",
    "parse_export_jobs",
    "parse_etl_pipelines",
    "parse_to_ir",
]
