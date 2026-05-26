# Changelog — CP59 Tenant Billing & Invoicing

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-05-26

### Added
- **BillingPlan** model: kế hoạch thanh toán với tier (free/starter/professional/enterprise), pricing, features, usage limits
- **BillingCycle** model: chu kỳ thanh toán (monthly/quarterly/annual) với auto-renew
- **InvoiceConfig** model: cấu hình hóa đơn với line items, currency, state machine (draft → sent → paid | overdue → void)
- **UsageMeter** model: thiết bị đo lường sử dụng (api_calls, storage_gb, users, bandwidth_gb) với threshold alerts
- **PaymentGatewayConfig** model: cấu hình payment gateway (Stripe, PayPal, Adyen)
- **BillingIR** parser: Intermediate Representation cho toàn bộ billing config
- **FastAPI emitter**: sinh billing_models, billing_schemas, billing_service, billing_router, invoice_generator, billing_events
- **NestJS emitter**: sinh billing.entity, billing.dto, billing.service, billing.controller, invoice.service, billing.module
- **Recipes**: saas_billing, usage_based_billing, multi_tier_billing, invoice_generation
- **DSL integration**: 4 NodeKind (BILLING_PLAN, BILLING_CYCLE, USAGE_METER, INVOICE_CONFIG)
- **Loader**: `_load_tenant_billing()` function cho `tenant_billing.yaml`
- **Router**: EMITTER_REGISTRY + PARSER_REGISTRY entries cho FastAPI và NestJS
- **Taxonomy**: CP59 entry trong `industry/taxonomy.yml`

### Obligations
- **BillingAuditTrail**: Ghi audit log cho mọi billing action (CP14 integration)
- **UsageThresholdAlerting**: Cảnh báo khi usage đạt ngưỡng threshold (CP12 integration)
