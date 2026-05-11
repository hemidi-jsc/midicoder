# coding: utf-8
"""
Mô-đun File Storage & Media Processing Emitter (CP11).

Cung cấp:
- StorageProfile, UploadPolicy, MediaTransform: Data models cho file storage
- FileStorageCollection: Aggregate collection
- FileStorageParser: Parse YAML DSL → models
- FastAPIFileStorageEmitter, NestJSFileStorageEmitter: Backend emitters
- AngularFileStorageEmitter, ReactFileStorageEmitter: Frontend emitters
- StorageProvider: Provider abstraction (S3, Local)

KPI-029: Tenant Isolation - tenant_isolation=True mặc định

Author: Midicoder Team
Version: 1.0.0
"""

# Models
from midicoder.emitters.core.file_storage.models import (
    StorageBackend,
    TransformType,
    StorageProfile,
    UploadPolicy,
    MediaTransform,
    FileStorageCollection,
    _BACKEND_MAP,
    _TRANSFORM_MAP,
)

# Parser
from midicoder.emitters.core.file_storage.parser import FileStorageParser

# Backend Emitters
from midicoder.emitters.core.file_storage.fastapi import FastAPIFileStorageEmitter
from midicoder.emitters.core.file_storage.nestjs import NestJSFileStorageEmitter

# Frontend Emitters
try:
    from midicoder.emitters.core.file_storage.angular import (
        AngularFileStorageEmitter,
        emit_angular_file_storage,
    )
except ImportError:
    AngularFileStorageEmitter = None  # type: ignore
    emit_angular_file_storage = None  # type: ignore

try:
    from midicoder.emitters.core.file_storage.react import (
        ReactFileStorageEmitter,
        emit_react_file_storage,
    )
except ImportError:
    ReactFileStorageEmitter = None  # type: ignore
    emit_react_file_storage = None  # type: ignore

__all__ = [
    # Enums
    "StorageBackend",
    "TransformType",
    # Models
    "StorageProfile",
    "UploadPolicy",
    "MediaTransform",
    "FileStorageCollection",
    # Mappings
    "_BACKEND_MAP",
    "_TRANSFORM_MAP",
    # Parser
    "FileStorageParser",
    # Backend Emitters
    "FastAPIFileStorageEmitter",
    "NestJSFileStorageEmitter",
    # Frontend Emitters
    "AngularFileStorageEmitter",
    "emit_angular_file_storage",
    "ReactFileStorageEmitter",
    "emit_react_file_storage",
]
