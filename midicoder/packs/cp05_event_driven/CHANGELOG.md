# Changelog — CP05 Event-Driven Architecture Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-07

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
