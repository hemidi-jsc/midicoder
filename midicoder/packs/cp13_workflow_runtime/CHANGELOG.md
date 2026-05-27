# Changelog — CP13 Background Job & Workflow Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] — 2026-05-15

### Added

- **DAG Executor Engine** (`engine/dag_executor.py`):
    - Topological sort with cycle detection (Kahn's algorithm)
    - 4 execution modes: SEQUENTIAL, PARALLEL, PARALLEL_WITH_FANIN, DYNAMIC
    - 4 failure policies: FAIL_FAST, SKIP_AND_CONTINUE, RETRY_THEN_SKIP, COMPENSATE
    - Parallel execution groups via `get_execution_plan()`
    - DAG validation (dependency check, entry/exit points)
- **Saga Orchestrator Engine** (`engine/saga_orchestrator.py`):
    - 3 compensation strategies: BACKWARD, FORWARD, MIXED
    - Action/compensation pair execution
    - Saga log for audit/debug
    - Step status tracking (7 states)
- **Queue Provider Abstraction** (`queue_provider.py`):
    - `QueueProvider` ABC with 10 async methods
    - `MemoryQueueProvider` — full in-memory implementation
    - `RedisQueueProvider`, `RabbitMQQueueProvider`, `SQSQueueProvider` — stubs
    - `QueueProviderFactory` for backend resolution
    - 5 backends: REDIS, RABBITMQ, SQS, IN_MEMORY, KAFKA
- **Job Retry with Exponential Backoff** (`scheduler.py`):
    - `RetryPolicy` with configurable base_delay, multiplier, max_delay, jitter
    - `JobRetryTracker` for per-instance retry state
    - Automatic exhaustion detection
- **Dead Letter Queue** (`scheduler.py`):
    - `DeadLetterQueue` with configurable max_size and retention
    - Message tracking, purge, full detection
- **New DSL Models** (`models.py`):
    - `JobSpec` — job specification with payload, schedule, retry_policy
    - `WorkerConfig` — worker pool size, concurrency, queue bindings
    - `TimeoutPolicy` — step/workflow/idle timeout
    - `DeadlockDetection` — deadlock detection config
- **Workflow Router Templates**:
    - FastAPI: `workflow_router.py.jinja2` — REST API for workflow CRUD
    - NestJS: `workflow.controller.ts.jinja2` — REST controller
    - React: `useJobStatus.ts.jinja2` — job status hook
- **Enhanced MIR processing** (`ir.py`):
    - `_process_workflow_to_mir()` now generates workflow_state, workflow_orchestrate, schedule_job, background_worker operations
    - Effect flows for each transition effect
    - `_store_workflows_in_metadata()` includes entity, initial_state, gateway_types, sub_workflows, compensation, human_tasks, timers
- **CP13 Error Templates** (`errors.py`):
    - Vietnamese error messages for all 8 CP13 error codes
    - Remediation suggestions per error
- **Comprehensive Test Suite** (12 test files, ~250+ tests):
    - DAG models + executor tests
    - Saga models + orchestrator tests
    - Queue provider tests (71 tests)
    - Retry/DLQ/edge case tests (40 tests)
    - Template rendering + integration tests (27 tests)
    - Original engine, guards, scheduler, models, parser, FastAPI, NestJS tests (migrated)

### Changed

- `pack.yml`: Updated definitions_count (8→14), obligations_count (4→5)
- `pack.yml`: Added capabilities: queue_abstraction, dead_letter_queue, retry_policy
- `pack.yml`: Added 3 new file contributions (workflow_router, workflow_controller, useJobStatus)
- Test files moved from `midicoder/tests/emitters/` to `cp13_workflow_runtime/tests/`
- Error code range extended: MDC-CP13-001 to MDC-CP13-011

### Fixed

- Angular template `job-status.component.ts.jinja2` — wrapped inline template in `{% raw %}` to avoid Jinja2 parsing conflict
- CP13 error codes now have Vietnamese templates (previously showed "Lỗi không xác định")
- React `useJobStatus` hook template was declared but missing — now created

---

**Capabilities Provided:** `schedule_job`, `background_worker`, `workflow_orchestrate`, `dag_execution`, `saga_orchestration`, `queue_abstraction`, `dead_letter_queue`, `retry_policy`

**Obligations:**

1. **JobRetry** — Failed jobs must retry with exponential backoff
2. **SagaCompensation** — Failed saga steps must trigger compensation chain
3. **DAGAcyclicity** — DAG must have no cycles (topological order required)
4. **NodeTimeout** — Each DAG node must have timeout to prevent hangs
5. **DeadLetterQueue** — Permanently failed jobs must move to dead letter queue

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
