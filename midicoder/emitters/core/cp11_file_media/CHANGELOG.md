# Changelog — CP11 File Storage & Media Processing Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
