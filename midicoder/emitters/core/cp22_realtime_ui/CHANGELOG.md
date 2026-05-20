# Changelog — CP22 Real-time UI Generator

## [1.0.0] - 2026-05-20

### Added

- Realtime channel orchestration (WebSocket + SSE fallback)
- 5 widget types: PresenceIndicator, LiveFeed, LiveCounter, LiveCursor, NotificationToast
- React emitter: `RealtimeComponentEmitter` với hooks + components
- Angular emitter: `AngularRealtimeEmitter` với services + components + mixin
- ChannelSpec parser: parse CP05 events → channel subscriptions
- Tenant isolation trong tất cả realtime channels
- `PerWidgetFile` support trong `file_contributions_loader.py`
- Full test suite: 87 tests, 95% coverage
- Template Rules V1 (standalone) + V2 (structure only) compliant

### UI Framework Support

| Framework   | React     | Angular          |
| ----------- | --------- | ---------------- |
| Material    | ✅        | ✅ (angular-material) |
| Tailwind    | ✅        | ✅               |
| Bootstrap   | ✅        | ✅ (ng-bootstrap) |
| AntD        | ✅        | ✅ (primeng)     |
| Carbon      | ✅        | ✅ (clarity)     |
