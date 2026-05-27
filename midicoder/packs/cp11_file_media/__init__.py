# coding: utf-8
"""
Mô-đun File Storage & Media Processing Emitter (CP11).

Cung cấp:
- StorageProfile, UploadPolicy, MediaTransform: Data models cho file storage
- CDNIntegration: Cấu hình CDN (AWS CloudFront)
- PresignedURLPolicy: Policy cho presigned URLs
- FileStorageCollection: Aggregate collection
- FileStorageParser: Parse YAML DSL → models
- FastAPIFileStorageEmitter, NestJSFileStorageEmitter: Backend emitters
- AngularFileStorageEmitter, ReactFileStorageEmitter: Frontend emitters
- StorageProvider: Provider abstraction (S3, Local)
- Recipes: Pattern macro (S3StorageRecipe, LocalStorageRecipe, MinIORecipe, ImageUploadRecipe, DocumentUploadRecipe, VideoUploadRecipe, ImageResizeRecipe, ThumbnailRecipe, ImageTranscodeRecipe, CloudFrontRecipe, PresignedURLRecipe, FullStorageRecipe)

KPI-029: Tenant Isolation - tenant_isolation=True mặc định
Scope: AWS (S3, CloudFront) + Local (filesystem)

Author: Midicoder Team
Version: 1.1.0
"""

# Models
from midicoder.packs.cp11_file_media.models import (
    StorageBackend,
    TransformType,
    StorageProfile,
    UploadPolicy,
    MediaTransform,
    CDNIntegration,
    PresignedURLPolicy,
    FileStorageCollection,
    _BACKEND_MAP,
    _TRANSFORM_MAP,
)

# Parser
from midicoder.packs.cp11_file_media.parser import FileStorageParser

# Recipes
from midicoder.packs.cp11_file_media.recipes import (
    S3StorageRecipe,
    LocalStorageRecipe,
    MinIORecipe,
    ImageUploadRecipe,
    DocumentUploadRecipe,
    VideoUploadRecipe,
    ImageResizeRecipe,
    ThumbnailRecipe,
    ImageTranscodeRecipe,
    CloudFrontRecipe,
    PresignedURLRecipe,
    FullStorageRecipe,
)

# Backend Emitters
from midicoder.packs.cp11_file_media.fastapi import FastAPIFileStorageEmitter
from midicoder.packs.cp11_file_media.nestjs import NestJSFileStorageEmitter

# Frontend Emitters
try:
    from midicoder.packs.cp11_file_media.angular import (
        AngularFileStorageEmitter,
        emit_angular_file_storage,
    )
except ImportError:
    AngularFileStorageEmitter = None  # type: ignore
    emit_angular_file_storage = None  # type: ignore

try:
    from midicoder.packs.cp11_file_media.react import (
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
    "CDNIntegration",
    "PresignedURLPolicy",
    "FileStorageCollection",
    # Mappings
    "_BACKEND_MAP",
    "_TRANSFORM_MAP",
    # Parser
    "FileStorageParser",
    # Recipes
    "S3StorageRecipe",
    "LocalStorageRecipe",
    "MinIORecipe",
    "ImageUploadRecipe",
    "DocumentUploadRecipe",
    "VideoUploadRecipe",
    "ImageResizeRecipe",
    "ThumbnailRecipe",
    "ImageTranscodeRecipe",
    "CloudFrontRecipe",
    "PresignedURLRecipe",
    "FullStorageRecipe",
    # Backend Emitters
    "FastAPIFileStorageEmitter",
    "NestJSFileStorageEmitter",
    # Frontend Emitters
    "AngularFileStorageEmitter",
    "emit_angular_file_storage",
    "ReactFileStorageEmitter",
    "emit_react_file_storage",
]
