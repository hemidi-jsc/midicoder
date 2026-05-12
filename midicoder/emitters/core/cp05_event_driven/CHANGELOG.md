# Changelog: CP05 Event-Driven Architecture Generator

## [1.0.0] - 2026-05-06

### Added
- Models: EventDefinition, OutboxEntry
- FastAPI Emitter: event publisher, event subscriber, outbox pattern
- NestJS Emitter: events.module.ts, event-publisher.service.ts, event-subscriber.service.ts
- pack.yml: Self-declare capabilities (publish_event, subscribe_event, event_outbox)
- Error codes: MDC-EVT-001 to MDC-EVT-010
