# Changelog

## [1.0.0] - 2026-05-11

### Added

- **StorageProfile, UploadPolicy, MediaTransform** — 3 data models với `__post_init__` validation
- **FileStorageParser** — Parse YAML DSL → FileStorageCollection
- **StorageProvider ABC** — Provider abstraction với S3 và Local implementations
- **FastAPIFileStorageEmitter** — Sinh S3 config, FileUploadService, MediaTransformService, StorageRouter
- **NestJSFileStorageEmitter** — Sinh S3Module, FileUploadService, MediaTransformService, FileUploadController
- **AngularFileStorageEmitter** — Sinh FileStorageService, FileUploadComponent, FileStorageNgModule
- **ReactFileStorageEmitter** — Sinh FileStorageProvider, useFileStorage hook, FileUpload component
- **UploadPolicy enforcement** — Obligation: mọi file upload PHẢI qua content-type, size, extension validation
- **KPI-029: Tenant Isolation** — Tenant-aware folder prefix trên tất cả storage operations
- **10 error codes** — MDC-CP11-001 through MDC-CP11-010
