# Changelog — CP36 Tenant Onboarding & Subscription

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-05-21

### Added

- **Enum**: `SubscriptionPlan` (free, starter, professional, enterprise) — các bậc gói subscription
- **Enum**: `RegistrationStatus` (pending, verified, rejected, cancelled) — trạng thái đăng ký
- **Enum**: `SubscriptionStatus` (trial, active, past_due, cancelled, expired) — trạng thái subscription
- **Enum**: `BillingCycle` (monthly, yearly) — chu kỳ thanh toán
- **Dataclass**: `TenantRegistration` — entity đăng ký tenant mới (email, company_name, plan, trial_days, status, verification_token, tenant_id)
- **Dataclass**: `TenantSubscription` — entity quản lý subscription (tenant_id, plan, billing_cycle, status, price, currency, payment_method_id)
- **Dataclass**: `PlanConfig` — cấu hình giá cho từng plan (monthly_price, yearly_price, features, limits)
- **Dataclass**: `OnboardingIR` — Intermediate Representation cho CP36
- **Parser**: `OnboardingParser` + `parse_onboarding_dsl()` — parse DSL dict → OnboardingIR
- **Recipes module** (`recipes.py`):
  - `self_service_saas_recipe()` — self-service SaaS: email verify auto, trial 14 ngày, self-serve
  - `enterprise_b2b_recipe()` — enterprise B2B: admin approve required, no trial, sales-led
- **FastAPI Emitter**: 10 templates (registration_model, subscription_model, schemas, services, routers, events, __init__)
- **NestJS Emitter**: 9 templates (entities, DTOs, module, services, controllers)
- **React Emitter**: 4 templates (RegistrationForm, SubscriptionPanel, TrialBanner, useOnboarding hook)
- **Angular Emitter**: 4 templates (registration-form, subscription-panel, trial-banner components + onboarding service)
- **Tests**: Full pack-local test suite (`tests/`) — 95 tests covering models (49), parser (10), recipes (25), emitters (11)
- **Error codes**: MDC-CP36-001 to MDC-CP36-022 (22 error codes)
- **pack.yml**: Full pack declaration with capabilities, definitions, obligations, file_contributions

### Changed

- **taxonomy.yml**: Updated CP36 status from `planned` to `stable`, version 1.0.0 → 1.1.0
- **TODOS.md**: Marked CP36 as DONE

### Fixed

- **CRITICAL**: Error code convention — sử dụng `EM.raise_error(ErrorCode.CP36_XXX)` thay vì bare `raise`
- **HIGH**: Vietnamese diacritics — tất cả docstrings/comments sử dụng tiếng Việt có dấu đầy đủ

---

**Capabilities Provided:** `tenant_register`, `tenant_verify`, `trial_manage`, `subscription_manage`

**Capabilities (Runtime):** `registration_service`, `subscription_service`, `onboarding_events`, `verification_flow`

**Obligations:**

1. **RegistrationVerification** — Mọi đăng ký tenant phải được xác minh trước khi cấp quyền truy cập
2. **TrialExpiration** — Trial period phải có ngày hết hạn rõ ràng và không thể vô hạn

**Dependencies:** CP02 (Multi-Tenant), CP03 (Auth), CP12 (Notification), CP33 (Financial)
