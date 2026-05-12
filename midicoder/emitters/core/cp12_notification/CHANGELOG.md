# Changelog

All notable changes to the CP12 Notification & Communication Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-11

### Added
- **Models**: NotificationChannel, NotificationTemplate, NotificationDispatch, NotificationProvider, DispatchResult
- **Parser**: parse_notifications, parse_channels, parse_providers
- **Template Engine**: TemplateRenderer với nested variables và filters (currency, uppercase, lowercase, format, default)
- **I18n**: I18nTemplateRegistry với BCP 47 locale fallback chain
- **Rate Limiter**: In-memory rate tracking per recipient per channel
- **Retry Policy**: Exponential backoff cho notification dispatch
- **Providers**: EmailGateway/SmsGateway/PushGateway ABC + SmtpEmailGateway + SendGrid/SES/Firebase stub
- **FastAPI Emitter**: NotificationService, API routes, Pydantic models, background tasks
- **NestJS Emitter**: NotificationModule, NotificationService, NotificationController, DTOs
- **Angular Templates**: NotificationService, NotificationToastComponent
- **React Templates**: NotificationContext, useNotification hook, TypeScript types

### Obligations
- Rate limiting BẮT BUỘC enforce trên mọi notification dispatch
- Template validation BẮT BUỘC trước khi render

### Capabilities
- send_notification
- email_dispatch
- sms_dispatch
- push_notification
