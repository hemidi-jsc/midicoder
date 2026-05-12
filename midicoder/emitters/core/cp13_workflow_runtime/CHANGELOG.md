# Changelog — CP13: Background Job & Workflow Generator

## [1.0.0] — 2026-05-11

### Added
- **Job Scheduling Models**: `JobDefinition`, `JobInstance`, `JobPriority`, `SchedulePolicy` với `__post_init__` validation
- **CP13 Error Codes**: MDC-CP13-001~008 (job scheduling, workflow transition, guard/effect errors)
- **pack.yml**: CP13 manifest, đồng bộ 1:1 với taxonomy.yml
- **FastAPI Stack Templates**: `workflow_service.py.jinja2`, `job_scheduler.py.jinja2`
- **NestJS Stack Templates**: `workflow.service.ts.jinja2`, `job.scheduler.ts.jinja2`
- **Angular Stack Templates**: `workflow.service.ts.jinja2`, `job-status.component.ts.jinja2`
- **React Stack Templates**: `WorkflowContext.tsx.jinja2`, `useWorkflow.ts.jinja2`, `types.ts.jinja2`
- **Tests**: 26 tests cho scheduler models (100% coverage)
- **4 stacks**: FastAPI, NestJS, Angular, React

### Existing (preserved)
- Workflow engine: `StateMachine`, `EventStore`, `TransitionResult`, `TransitionContext`
- Guards: `PermissionGuard`, `BusinessGuard`, `ComplianceGuard`, `RoleGuard`, `StateGuard`
- Effects: `EventEffect`, `CommandEffect`, `NotificationEffect`, `AuditEffect`, `CompensationEffect`
- Emitters: `WorkflowFastAPIEmitter` (1,730 lines), `WorkflowNestJSEmitter` (1,063 lines)
- Parser: `WorkflowParser`
- Models: `WorkflowDefinition`, `Transition`, `Guard`, `Effect`

### Obligations
- **Job Execution Idempotency**: Mỗi job execution có idempotency key (instance_id)
