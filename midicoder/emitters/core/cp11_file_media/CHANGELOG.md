# Changelog — CP11 File Storage & Media Processing Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-05-18

### Added

- **Models**: CDNIntegration (AWS CloudFront config), PresignedURLPolicy
- **Recipes**: S3StorageRecipe, LocalStorageRecipe, MinIORecipe, ImageUploadRecipe, DocumentUploadRecipe, VideoUploadRecipe, ImageResizeRecipe, ThumbnailRecipe, ImageTranscodeRecipe, CloudFrontRecipe, PresignedURLRecipe, FullStorageRecipe
- **FastAPI Emitter**: CDN config module (CloudFront URL resolution, presigned URL helper)
- **NestJS Emitter**: CdnService (CloudFront URL resolution, signed URL support)
- **Angular Emitter**: CdnConfig/CdnUrlResult interfaces, resolveFileUrl() method in FileStorageService
- **React Emitter**: CdnConfig interface, resolveFileUrl() function in useFileStorage
- **Parser**: Parse CDN config (CloudFront) and PresignedURLPolicy from YAML/dict metadata
- **Tests**: test_cdn_models.py (32 tests), test_recipes.py (24 tests) — total 206 tests

### Changed

- Scope: AWS (S3, CloudFront) + Local only — removed GCS/Azure references
- Taxonomy: definitions_count 3→5, added `cdn_integration` and `presigned_url` capabilities
- Version bumped to 1.1.0

### Fixed

- GCS reference in providers/base.py docstring
- SyntaxWarning: escape sequences in angular.py and react.py

### Removed

- GCP/Azure references from pack documentation

---

**Capabilities Provided:** `file_upload`, `file_download`, `file_storage`, `media_transform`, `cdn_integration`, `presigned_url`

**Capabilities (Runtime):** `s3_storage`, `local_storage`, `upload_policy`, `media_transform`, `cdn_integration`, `presigned_url`

**Obligations:**

1. **UploadValidation** — All uploads must validate type, size, and malware

**Dependencies:** CP07

## [1.0.0] - 2026-05-11

### Added

- **Models**: StorageProfile, UploadPolicy, MediaTransform
- **FastAPI Emitter**: S3 config, file upload service, media transform service, storage router
- **NestJS Emitter**: S3Module, FileUploadService, MediaTransformService, FileUploadController
- **Angular Integration**: FileStorageService, FileUploadComponent
- **React Integration**: useFileStorage, FileUpload

---

**Capabilities Provided:** `file_upload`, `file_download`, `file_storage`, `media_transform`

**Capabilities (Runtime):** `s3_storage`, `local_storage`, `upload_policy`, `media_transform`

**Obligations:**

1. **UploadValidation** — All uploads must validate type, size, and malware

**Dependencies:** CP07
