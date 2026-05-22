# coding: utf-8
"""
Mô-đun recipes cho CP38 — Data Import/Export/ETL.

Cung cấp các recipe patterns để generate import jobs, export jobs,
ETL pipelines, và bulk operations theo common use cases.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp38_data_etl.models import (
    BulkConfig,
    ETLJob,
    ETLMapping,
    ETLStep,
    ExtractConfig,
    ExtractSource,
    ExportJob,
    ImportFormat,
    ImportJob,
    JobStatus,
    LoadConfig,
    LoadMode,
    TransformConfig,
    TransformType,
)
from midicoder.emitters.core.cp38_data_etl.parser import ETLIR


@dataclass
class RecipeOutput:
    """Kết quả của recipe.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: ETLIR kết quả
    """
    name: str
    description: str
    ir: ETLIR


def csv_import_recipe(entity: str, file_path: str) -> RecipeOutput:
    """Recipe: Import dữ liệu từ file CSV vào entity.

    Tạo import job để đọc file CSV và chèn dữ liệu vào entity
    đích. Hỗ trợ tracking số hàng thành công/thất bại.

    Args:
        entity: Tên entity đích
        file_path: Đường dẫn file CSV

    Returns:
        RecipeOutput với 1 import job (format=csv)
    """
    import_job = ImportJob(
        job_key=f"import_{entity}",
        target_entity=entity,
        source_file=file_path,
        format=ImportFormat.CSV,
        status=JobStatus.PENDING,
    )

    return RecipeOutput(
        name="csv_import",
        description=f"Import dữ liệu CSV từ {file_path} vào {entity}",
        ir=ETLIR(import_jobs=[import_job]),
    )


def json_import_recipe(entity: str, file_path: str) -> RecipeOutput:
    """Recipe: Import dữ liệu từ file JSON vào entity.

    Tạo import job để đọc file JSON (array of objects) và chèn
    dữ liệu vào entity đích.

    Args:
        entity: Tên entity đích
        file_path: Đường dẫn file JSON

    Returns:
        RecipeOutput với 1 import job (format=json)
    """
    import_job = ImportJob(
        job_key=f"import_{entity}_json",
        target_entity=entity,
        source_file=file_path,
        format=ImportFormat.JSON,
        status=JobStatus.PENDING,
    )

    return RecipeOutput(
        name="json_import",
        description=f"Import dữ liệu JSON từ {file_path} vào {entity}",
        ir=ETLIR(import_jobs=[import_job]),
    )


def data_migrate_recipe(
    source: ExtractSource,
    target: str,
    mappings: list[ETLMapping],
    source_config: dict[str, Any] | None = None,
    load_mode: LoadMode = LoadMode.UPSERT,
) -> RecipeOutput:
    """Recipe: Data migration từ source sang target với ETL mappings.

    Tạo ETL job hoàn chỉnh: extract từ source (file/database/api),
    apply các transform mappings, load vào target entity.

    Args:
        source: Nguồn dữ liệu (file/database/api)
        target: Entity đích
        mappings: Danh sách ETL mappings (source_column -> target_field với transform)
        source_config: Cấu hình thêm cho source (file_path, query, table)
        load_mode: Chế độ load (mặc định upsert)

    Returns:
        RecipeOutput với ETL job (extract + transform mappings + load)
    """
    source_config = source_config or {}

    # Bước 1: Extract
    extract_step = ETLStep(
        step_key="extract_source",
        step_type="extract",
        config=ExtractConfig(
            source=source,
            file_path=source_config.get("file_path"),
            query=source_config.get("query"),
            table=source_config.get("table"),
            delimiter=source_config.get("delimiter", ","),
        ).to_dict(),
        order=0,
    )

    # Bước 2: Transform mappings (nếu có)
    steps: list[ETLStep] = [extract_step]
    order = 1

    if mappings:
        # Gom các mappings vào 1 transform step
        transform_configs = []
        for m in mappings:
            transform_configs.append(m.to_dict())

        transform_step = ETLStep(
            step_key="transform_mappings",
            step_type="transform",
            config={
                "mappings": transform_configs,
                "step_type": "map",
                "params": {},
            },
            order=order,
        )
        order += 1
        steps.append(transform_step)

    # Bước 3: Load
    load_step = ETLStep(
        step_key="load_target",
        step_type="load",
        config=LoadConfig(
            target_entity=target,
            mode=load_mode,
            upsert_key=source_config.get("upsert_key"),
        ).to_dict(),
        order=order,
    )
    steps.append(load_step)

    etl_job = ETLJob(
        job_key=f"migrate_{source.value}_to_{target}",
        steps=steps,
        status=JobStatus.PENDING,
    )

    return RecipeOutput(
        name="data_migrate",
        description=f"Migrate dữ liệu từ {source.value} sang {target} với {len(mappings)} mappings",
        ir=ETLIR(etl_jobs=[etl_job]),
    )


def etl_pipeline_recipe(steps: list[ETLStep], job_key: str = "etl_pipeline") -> RecipeOutput:
    """Recipe: ETL pipeline từ danh sách steps có sẵn.

    Tạo ETL job từ danh sách ETLSteps được định nghĩa sẵn.
    Người dùng có thể customize từng step theo nhu cầu.

    Args:
        steps: Danh sách ETL steps (phải có ít nhất 1 extract + 1 load)
        job_key: Job key cho ETL pipeline

    Returns:
        RecipeOutput với ETL job từ các steps đã cho
    """
    etl_job = ETLJob(
        job_key=job_key,
        steps=steps,
        status=JobStatus.PENDING,
    )

    return RecipeOutput(
        name="etl_pipeline",
        description=f"ETL pipeline với {len(steps)} steps: {job_key}",
        ir=ETLIR(etl_jobs=[etl_job]),
    )


def bulk_export_recipe(
    entity: str,
    fmt: ImportFormat = ImportFormat.CSV,
    filters: dict[str, Any] | None = None,
) -> RecipeOutput:
    """Recipe: Export dữ liệu từ entity ra file (bulk operation).

    Tạo export job để trích xuất dữ liệu từ entity và ghi ra
    file với định dạng CSV hoặc JSON.

    Args:
        entity: Tên entity nguồn
        fmt: Định dạng file output (csv/json)
        filters: Bộ lọc dữ liệu (optional)

    Returns:
        RecipeOutput với 1 export job
    """
    filters = filters or {}

    export_job = ExportJob(
        job_key=f"export_{entity}",
        entity=entity,
        format=fmt,
        filters=filters,
        status=JobStatus.PENDING,
    )

    bulk_cfg = BulkConfig(
        chunk_size=1000,
        max_retries=3,
        rollback_threshold=0.1,
    )

    return RecipeOutput(
        name="bulk_export",
        description=f"Export dữ liệu từ {entity} sang format {fmt.value}",
        ir=ETLIR(export_jobs=[export_job], bulk_config=bulk_cfg),
    )


__all__ = [
    "RecipeOutput",
    "csv_import_recipe",
    "json_import_recipe",
    "data_migrate_recipe",
    "etl_pipeline_recipe",
    "bulk_export_recipe",
]
