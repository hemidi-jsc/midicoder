# Changelog — CP12 Notification & Communication Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] — 2026-05-17

### Added

- **Models**: WebhookConfig, WebhookDelivery, WebhookAuthType (webhook channel)
- **Models**: DeliveryStatus, DeliveryAttempt, DeliveryTracking (end-to-end delivery tracking)
- **Models**: ABTestVariant, ABTestConfig (A/B testing cho notifications)
- **Models**: ChatPlatform, ChatIntegrationConfig (Slack, Teams, Discord, Webex)
- **Providers**: TwilioSmsGateway — SMS qua Twilio API (full implement, không stub)
- **Providers**: WebhookGatewayImpl — HTTP webhook với auth (Bearer/HMAC/Basic) và retry
- **Providers**: FirebasePushGateway — FCM v1 API (cải thiện từ stub → full)
- **Providers**: WebhookGateway ABC interface
- **Recipes**: SMTPEmailRecipe, SendGridEmailRecipe, SESEmailRecipe
- **Recipes**: TwilioSMSRecipe (có templates: welcome, verification, password_reset)
- **Recipes**: FCMRecipe, WebhookRecipe, DeliveryTrackingRecipe
- **Recipes**: ABTestRecipe (simple_email_test, three_way_test factories)
- **Stacks**: FastAPI templates — webhook_service.py, delivery_tracker.py
- **Stacks**: NestJS templates — webhook.service.ts, delivery-tracker.service.ts
- **Stacks**: React types — DeliveryTracking, WebhookConfig, WebhookDeliveryResult

### Changed

- **WebhookConfig.**post_init****: Thay `EM.raise_error()` bằng `ValueError` (standalone)
- **Pack version**: 1.0.0 → 2.0.0 (breaking: removed FastAPI/NestJS emitter classes)
- **definitions_count**: 8 → 15
- **obligations_count**: 4 → 6
- **capabilities_provided**: Thêm `webhook_dispatch`, `delivery_tracking`, `ab_testing`
- **file_contributions**: 9 → 15 files (thêm webhook + delivery tracker cho backend)

### Removed

- **FastAPINotificationEmitter**: Dead code — pack.yml dùng raw Jinja2, không cần structured emitter
- **NestJSNotificationEmitter**: Dead code — pack.yml dùng raw Jinja2, không cần structured emitter

### Fixed

- **WebhookConfig.**post_init****: Fix crash — EM/ErrorCode không được import
- **WebhookDelivery.delivery_id**: Fix `uuid4` → `uuid.uuid4`
- **Test organization**: Move tests từ `tests/emitters/` vào `cp12_notification/tests/`

### Capabilities Provided

`send_notification`, `email_dispatch`, `sms_dispatch`, `push_notification`,
`webhook_dispatch`, `delivery_tracking`, `ab_testing`

### Obligations

1. **TemplateValidation** — Notification templates must have required variables
2. **FallbackChannel** — Failed dispatch must retry on fallback channel
3. **WebhookReliability** — Webhook deliveries must retry with backoff on failure
4. **ChatSecurity** — Chat bot tokens must be stored securely
5. **DeliveryTracking** — All dispatches must have tracking records
6. **ABTestIntegrity** — A/B test variants must sum to 100% weight

### Dependencies

CP05 (Event-Driven Architecture)

---

## [1.0.0] - 2026-05-11

### Added

- **Models**: NotificationChannel, NotificationTemplate, NotificationDispatch, NotificationProvider, DispatchResult
- **Parser**: parse_notifications, parse_channels, parse_providers
- **Template Engine**: TemplateRenderer with nested variables and filters (currency, uppercase, lowercase, format, default)
- **I18n**: I18nTemplateRegistry with BCP 47 locale fallback chain
- **Rate Limiter**: In-memory rate tracking per recipient per channel
- **Retry Policy**: Exponential backoff for notification dispatch
- **Providers**: EmailGateway/SmsGateway/PushGateway ABC + SmtpEmailGateway + SendGrid/SES/Firebase stub
- **FastAPI Emitter**: NotificationService, API routes, Pydantic models, background tasks
- **NestJS Emitter**: NotificationModule, NotificationService, NotificationController, DTOs
- **Angular Integration**: NotificationService, NotificationToastComponent
- **React Integration**: useNotification, NotificationContext
