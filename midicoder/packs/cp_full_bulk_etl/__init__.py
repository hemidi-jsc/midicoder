# coding: utf-8
"""
CP44 — Bulk Operations Engine (merged với CP38 Data Import/Export/ETL).

Core pack cho hệ thống xử lý hàng loạt trên entities:
- BulkJob, BulkChunk, BulkResult, DLQEntry models
- BulkEngine cho in-memory simulation
- Parser: BulkIR + parse functions
- Recipes: basic_bulk_recipe, full_bulk_recipe
- Emitters: FastAPI, NestJS, Angular, React

Từ CP38 — Data Import/Export/ETL:
- ImportJob, ExportJob, ETLJob, ETLMapping models
- ETL Parser: ETLIR + parse functions
- Recipes: csv_import_recipe, json_import_recipe, data_migrate_recipe,
  etl_pipeline_recipe, bulk_export_recipe
"""

from midicoder.packs.cp_full_bulk_etl.models import (
    BulkAction,
    BulkChunk,
    BulkEngine,
    BulkJob,
    BulkResult,
    ChunkStatus,
    DLQEntry,
    JobStatus,
    RetryStrategy,
)
from midicoder.packs.cp_full_bulk_etl.parser import (
    BulkIR,
    parse_bulk_config,
    parse_bulk_jobs,
    parse_dlq_config,
    parse_to_ir,
)
from midicoder.packs.cp_full_bulk_etl.recipes import (
    RecipeOutput,
    basic_bulk_recipe,
    full_bulk_recipe,
)

# ===========================================================================
# CP38 — Data Import/Export/ETL imports
# ===========================================================================

from midicoder.packs.cp_full_bulk_etl.models import (
    CompatibilityMode,
    ETLImportError,
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
    TransformType,
)
from midicoder.packs.cp_full_bulk_etl.parser import (
    ETLIR,
    parse_etl_pipelines,
    parse_export_jobs,
    parse_import_jobs,
    parse_to_etl_ir,
)
from midicoder.packs.cp_full_bulk_etl.recipes import (
    bulk_export_recipe,
    csv_import_recipe,
    data_migrate_recipe,
    etl_pipeline_recipe,
    json_import_recipe,
    schema_registry_recipe,
)

__all__ = [
    # Bulk Models
    "BulkAction",
    "BulkChunk",
    "BulkEngine",
    "BulkJob",
    "BulkResult",
    "ChunkStatus",
    "DLQEntry",
    "JobStatus",
    "RetryStrategy",
    # Bulk Parser
    "BulkIR",
    "parse_bulk_config",
    "parse_bulk_jobs",
    "parse_dlq_config",
    "parse_to_ir",
    # Bulk Recipes
    "RecipeOutput",
    "basic_bulk_recipe",
    "full_bulk_recipe",
    # ===========================================================================
    # CP38: Data Import/Export/ETL exports
    # ===========================================================================
    # ETL Enums
    "ETLImportFormat",
    "ETLJobStatus",
    "TransformType",
    "ExtractSource",
    "LoadMode",
    "SchemaFormat",
    "CompatibilityMode",
    # ETL Models
    "ImportJob",
    "ExportJob",
    "ETLImportError",
    "ETLMapping",
    "ExtractConfig",
    "LoadConfig",
    "ETLStep",
    "ETLJob",
    "ETLPBulkConfig",
    "SchemaDefinition",
    "SchemaRegistryConfig",
    "SchemaEvolutionRule",
    # ETL Parser
    "ETLIR",
    "parse_import_jobs",
    "parse_export_jobs",
    "parse_etl_pipelines",
    "parse_to_etl_ir",
    # ETL Recipes
    "csv_import_recipe",
    "json_import_recipe",
    "data_migrate_recipe",
    "etl_pipeline_recipe",
    "bulk_export_recipe",
    "schema_registry_recipe",
]
