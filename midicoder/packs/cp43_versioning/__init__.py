# coding: utf-8
"""
CP43: Versioning & History Generator.

Cung cấp:
- models: VersionConfig, HistoryRecord, SoftDeleteMixin, OperationType, VersioningCollection
- parser: VersioningParser
- fastapi: FastAPIVersioningEmitter
- nestjs: NestJSVersioningEmitter
- angular: AngularVersioningEmitter
- react: ReactVersioningEmitter
- recipes: build_versioning_ir, full_versioning_recipe, minimal_versioning_recipe, soft_delete_only_recipe
"""

from midicoder.packs.cp43_versioning.models import (
    HistoryRecord,
    OperationType,
    SoftDeleteMixin,
    VersionConfig,
    VersioningCollection,
)
from midicoder.packs.cp43_versioning.parser import VersioningParser
from midicoder.packs.cp43_versioning.fastapi import FastAPIVersioningEmitter
from midicoder.packs.cp43_versioning.nestjs import NestJSVersioningEmitter
from midicoder.packs.cp43_versioning.angular import AngularVersioningEmitter
from midicoder.packs.cp43_versioning.react import ReactVersioningEmitter
from midicoder.packs.cp43_versioning.recipes import (
    build_versioning_ir,
    full_versioning_recipe,
    minimal_versioning_recipe,
    soft_delete_only_recipe,
    create_history_record,
)

__all__ = [
    "AngularVersioningEmitter",
    "FastAPIVersioningEmitter",
    "full_versioning_recipe",
    "build_versioning_ir",
    "HistoryRecord",
    "minimal_versioning_recipe",
    "NestJSVersioningEmitter",
    "OperationType",
    "ReactVersioningEmitter",
    "SoftDeleteMixin",
    "soft_delete_only_recipe",
    "create_history_record",
    "VersionConfig",
    "VersioningCollection",
    "VersioningParser",
]
