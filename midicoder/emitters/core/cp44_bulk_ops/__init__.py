# coding: utf-8
"""
CP44 — Bulk Operations Engine.

Core pack cho hệ thống xử lý hàng loạt trên entities:
- BulkJob, BulkChunk, BulkResult, DLQEntry models
- BulkEngine cho in-memory simulation
- Parser: BulkIR + parse functions
- Recipes: basic_bulk_recipe, full_bulk_recipe
- Emitters: FastAPI, NestJS, Angular, React
"""

from midicoder.emitters.core.cp44_bulk_ops.models import (
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
from midicoder.emitters.core.cp44_bulk_ops.parser import (
    BulkIR,
    parse_bulk_config,
    parse_bulk_jobs,
    parse_dlq_config,
    parse_to_ir,
)
from midicoder.emitters.core.cp44_bulk_ops.recipes import (
    RecipeOutput,
    basic_bulk_recipe,
    full_bulk_recipe,
)

__all__ = [
    # Models
    "BulkAction",
    "BulkChunk",
    "BulkEngine",
    "BulkJob",
    "BulkResult",
    "ChunkStatus",
    "DLQEntry",
    "JobStatus",
    "RetryStrategy",
    # Parser
    "BulkIR",
    "parse_bulk_config",
    "parse_bulk_jobs",
    "parse_dlq_config",
    "parse_to_ir",
    # Recipes
    "RecipeOutput",
    "basic_bulk_recipe",
    "full_bulk_recipe",
]
