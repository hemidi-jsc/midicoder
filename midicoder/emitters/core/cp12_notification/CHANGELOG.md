# Changelog — CP12 Notification & Communication Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

---

**Capabilities Provided:** `send_notification`, `email_dispatch`, `sms_dispatch`, `push_notification`

**Capabilities (Runtime):** `email`, `sms`, `push`, `template_engine`

**Obligations:**

1. **TemplateValidation** — Notification templates must have required variables
2. **FallbackChannel** — Failed dispatch must retry on fallback channel

**Dependencies:** CP05
