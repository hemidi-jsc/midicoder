# coding: utf-8
"""
Mô-đun recipes cho CP44 — Bulk Operations Engine.

Cung cấp các recipe patterns để generate bulk operations với
chunked processing, retry strategy, và DLQ management.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass

from midicoder.packs.cp_full_bulk_etl.models import (
    BulkAction,
    BulkJob,
    RetryStrategy,
)
from midicoder.packs.cp_full_bulk_etl.parser import BulkIR


@dataclass
class RecipeOutput:
    """Kết quả của recipe.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: BulkIR kết quả
    """
    name: str
    description: str
    ir: BulkIR


def basic_bulk_recipe() -> RecipeOutput:
    """Recipe: Bulk job đơn giản — 1 entity type, 1 action, chunk_size=100, concurrency=5.

    Tạo bulk job cập nhật hàng loạt users với cấu hình cơ bản.
    Không có config đặc biệt, phù hợp cho dev/prototyping.

    Returns:
        RecipeOutput với cấu hình bulk cơ bản
    """
    jobs = [
        BulkJob(
            job_id="bulk_basic_001",
            entity_type="user",
            action=BulkAction.BATCH_UPDATE,
            entity_ids=[f"user_{i:04d}" for i in range(1, 251)],
            chunk_size=100,
            max_concurrency=5,
            max_retries=3,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            timeout_seconds=300,
            metadata={"recipe": "basic_bulk"},
        ),
    ]

    return RecipeOutput(
        name="basic_bulk",
        description="1 job cập nhật 250 users, chunk_size=100, concurrency=5",
        ir=BulkIR(
            jobs=jobs,
            default_chunk_size=100,
            default_concurrency=5,
            default_max_retries=3,
            default_retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            default_timeout=300,
            dlq_enabled=True,
            use_events=True,
            use_audit=True,
        ),
    )


def full_bulk_recipe() -> RecipeOutput:
    """Recipe: Bulk jobs phức tạp — nhiều entity types, multi-tenant, retry, DLQ.

    Tạo 3 bulk jobs: (1) cập nhật products, (2) xóa orders cũ,
    (3) tạo invoices hàng loạt. Mỗi job có config riêng: chunk size,
    concurrency, retry strategy, tenant scope.

    Returns:
        RecipeOutput với cấu hình bulk đầy đủ
    """
    jobs = [
        BulkJob(
            job_id="bulk_full_products",
            entity_type="product",
            action=BulkAction.BATCH_UPDATE,
            entity_ids=[f"prod_{i:05d}" for i in range(1, 1001)],
            chunk_size=200,
            max_concurrency=10,
            max_retries=5,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            timeout_seconds=600,
            tenant_id="tenant_acme",
            operator_id="admin_001",
            metadata={"reason": "price_adjustment", "recipe": "full_bulk"},
        ),
        BulkJob(
            job_id="bulk_full_orders",
            entity_type="order",
            action=BulkAction.BATCH_DELETE,
            entity_ids=[f"order_{i:06d}" for i in range(1, 501)],
            chunk_size=50,
            max_concurrency=3,
            max_retries=1,
            retry_strategy=RetryStrategy.FIXED_DELAY,
            timeout_seconds=900,
            tenant_id="tenant_acme",
            operator_id="admin_002",
            metadata={"reason": "archive_old_orders", "older_than_days": 365, "recipe": "full_bulk"},
        ),
        BulkJob(
            job_id="bulk_full_invoices",
            entity_type="invoice",
            action=BulkAction.BATCH_CREATE,
            entity_ids=[f"inv_{i:05d}" for i in range(1, 301)],
            chunk_size=100,
            max_concurrency=8,
            max_retries=3,
            retry_strategy=RetryStrategy.LINEAR_BACKOFF,
            timeout_seconds=450,
            tenant_id="tenant_globex",
            operator_id="admin_003",
            metadata={"reason": "monthly_batch", "month": "2026-05", "recipe": "full_bulk"},
        ),
    ]

    return RecipeOutput(
        name="full_bulk",
        description="3 jobs (1000 products update, 500 orders delete, 300 invoices create), multi-tenant, các retry strategies khác nhau",
        ir=BulkIR(
            jobs=jobs,
            default_chunk_size=100,
            default_concurrency=10,
            default_max_retries=3,
            default_retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            default_timeout=300,
            dlq_enabled=True,
            use_events=True,
            use_audit=True,
        ),
    )


__all__ = [
    "RecipeOutput",
    "basic_bulk_recipe",
    "full_bulk_recipe",
    # CP38 ETL recipes
    "csv_import_recipe",
    "json_import_recipe",
    "data_migrate_recipe",
    "etl_pipeline_recipe",
    "bulk_export_recipe",
    "schema_registry_recipe",
]


# ===========================================================================
# ETL Recipes (từ CP38)
# ===========================================================================

from midicoder.packs.cp_full_bulk_etl.models import (
    CompatibilityMode,
    ETLImportFormat,
    ETLJob,
    ETLJobStatus,
    ETLMapping,
    ETLStep,
    ETLPBulkConfig,
    ExportJob,
    ExtractConfig,
    ExtractSource,
    ImportJob,
    LoadConfig,
    LoadMode,
    SchemaDefinition,
    SchemaEvolutionRule,
    SchemaFormat,
    SchemaRegistryConfig,
    ETLTransformConfig,
    TransformType,
)
from midicoder.packs.cp_full_bulk_etl.parser import ETLIR


def csv_import_recipe(entity: str, file_path: str) -> RecipeOutput:
    """Recipe: Import dữ liệu từ file CSV vào entity."""
    import_job = ImportJob(
        job_key=f"import_{entity}",
        target_entity=entity,
        source_file=file_path,
        format=ETLImportFormat.CSV,
        status=ETLJobStatus.PENDING,
    )

    return RecipeOutput(
        name="csv_import",
        description=f"Import dữ liệu CSV từ {file_path} vào {entity}",
        ir=ETLIR(import_jobs=[import_job]),
    )


def json_import_recipe(entity: str, file_path: str) -> RecipeOutput:
    """Recipe: Import dữ liệu từ file JSON vào entity."""
    import_job = ImportJob(
        job_key=f"import_{entity}_json",
        target_entity=entity,
        source_file=file_path,
        format=ETLImportFormat.JSON,
        status=ETLJobStatus.PENDING,
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
    """Recipe: Data migration từ source sang target với ETL mappings."""
    source_config = source_config or {}

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

    steps: list[ETLStep] = [extract_step]
    order = 1

    if mappings:
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
        status=ETLJobStatus.PENDING,
    )

    return RecipeOutput(
        name="data_migrate",
        description=f"Migrate dữ liệu từ {source.value} sang {target} với {len(mappings)} mappings",
        ir=ETLIR(etl_jobs=[etl_job]),
    )


def etl_pipeline_recipe(steps: list[ETLStep], job_key: str = "etl_pipeline") -> RecipeOutput:
    """Recipe: ETL pipeline từ danh sách steps có sẵn."""
    etl_job = ETLJob(
        job_key=job_key,
        steps=steps,
        status=ETLJobStatus.PENDING,
    )

    return RecipeOutput(
        name="etl_pipeline",
        description=f"ETL pipeline với {len(steps)} steps: {job_key}",
        ir=ETLIR(etl_jobs=[etl_job]),
    )


def bulk_export_recipe(
    entity: str,
    fmt: ETLImportFormat = ETLImportFormat.CSV,
    filters: dict[str, Any] | None = None,
) -> RecipeOutput:
    """Recipe: Export dữ liệu từ entity ra file (bulk operation)."""
    filters = filters or {}

    export_job = ExportJob(
        job_key=f"export_{entity}",
        entity=entity,
        format=fmt,
        filters=filters,
        status=ETLJobStatus.PENDING,
    )

    bulk_cfg = ETLPBulkConfig(
        chunk_size=1000,
        max_retries=3,
        rollback_threshold=0.1,
    )

    return RecipeOutput(
        name="bulk_export",
        description=f"Export dữ liệu từ {entity} sang format {fmt.value}",
        ir=ETLIR(export_jobs=[export_job], bulk_config=bulk_cfg),
    )


def schema_registry_recipe(
    registry_name: str,
    registry_url: str = "",
    schema_format: SchemaFormat = SchemaFormat.AVRO,
    compatibility: CompatibilityMode = CompatibilityMode.BACKWARD,
    auth_enabled: bool = False,
    auth_user: str = "",
    auth_password: str = "",
) -> RecipeOutput:
    """Schema registry với Avro, backward compatibility, auto-evolve rules."""
    registry = SchemaRegistryConfig(
        id=f"registry_{registry_name}",
        name=registry_name,
        url=registry_url,
        format=schema_format,
        compatibility_mode=compatibility,
        auth_enabled=auth_enabled,
        auth_basic_user=auth_user,
        auth_basic_password=auth_password,
        schema_lookup_max_size=1000,
    )

    sample_schema = SchemaDefinition(
        id=f"schema_{registry_name}_v1",
        name=f"{registry_name}_schema",
        format=schema_format,
        version="1.0.0",
        subject=f"{registry_name}-value",
        schema_content="",
        properties={"auto_register": True},
    )

    evolution_rule = SchemaEvolutionRule(
        id=f"rule_{registry_name}",
        schema_id=sample_schema.id,
        allowed_operations=["add_field", "add_enum_value"],
        auto_evolve=False,
        require_approval=True,
        notification_channels=["slack", "email"],
    )

    return RecipeOutput(
        name="schema_registry",
        description=f"Schema registry '{registry_name}' với {schema_format.value}, "
                    f"compatibility={compatibility.value}",
        ir=ETLIR(),
    )
