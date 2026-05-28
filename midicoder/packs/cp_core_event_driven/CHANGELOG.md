# Changelog — C02 Event-Driven Architecture (Core Pack)

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-05-28

### Changed

- **Pack rename**: CP05 → C02 (taxonomy-v2 migration)
- **Internal ID**: `cp05_event_driven` → `cp_core_event_driven`
- **Category**: `architecture` → `core`
- **Type**: added `type: core`
- **Dependencies**: `CP01` → `B01`
- **All imports**: updated from `midicoder.packs.cp05_event_driven` → `midicoder.packs.cp_core_event_driven`
- **Template paths**: updated from `cp05_event_driven/` → `cp_core_event_driven/`
- **Stack directories**: renamed `cp05_event_driven/` → `cp_core_event_driven/` (fastapi, nestjs)
- **Render context**: added `render_context_support: true`
- **Old IDs**: added `old_ids: [CP05]` for backward compatibility

### Added

- **Models**: EventTopic, EventSubscription, EventEnvelope, OutboxConfig
- **FastAPI Emitter**: Event publisher, subscriber, outbox pattern implementation
- **NestJS Emitter**: Event publisher, subscriber, outbox pattern implementation
- **Angular Integration**: EventService, EventSubscriber
- **React Integration**: useEvent, EventListener

---

**Capabilities Provided:** `publish_event`, `subscribe_event`, `event_outbox`

**Capabilities (Runtime):** `event_publisher`, `event_subscriber`, `outbox_pattern`

**Obligations:**

1. **EventOrdering** — Events from same aggregate must maintain causal order

**Dependencies:** CP01
