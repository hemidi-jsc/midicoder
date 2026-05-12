# Changelog — CP13 Background Job & Workflow Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-07

### Added

- **Models**: JobSpec, WorkflowDefinition, WorkerConfig
- **FastAPI Emitter**: Job scheduler, background worker, workflow service
- **NestJS Emitter**: WorkflowModule, JobScheduler, Worker
- **Angular Integration**: WorkflowService, JobStatusComponent
- **React Integration**: useWorkflow, useJobStatus

---

**Capabilities Provided:** `schedule_job`, `background_worker`, `workflow_orchestrate`

**Capabilities (Runtime):** `job_scheduler`, `background_worker`, `workflow_engine`

**Obligations:**

1. **JobRetry** — Failed jobs must retry with exponential backoff

**Dependencies:** CP05
