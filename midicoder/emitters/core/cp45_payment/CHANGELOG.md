# Changelog — CP45 Payment Gateway Abstraction

## 1.0.0 (2026-05-24)

### Added

- **Payment Gateway Abstraction** — Unified payment interface với strategy pattern
- **4 Payment Gateway Types**: Stripe, VNPay, MoMo
- **4 Payment Method Types**: credit_card, bank_transfer, ewallet,qr_code
- **PaymentTransaction** — Giao dịch với state machine (pending → processing → completed | failed | refunded | cancelled)
- **PaymentRefund** — Hoàn tiền với refund state machine riêng
- **PaymentMethod** — CRUD payment methods với PCI-DSS compliance (masked card data)
- **PaymentGatewayConfig** — Cấu hình gateway provider
- **PaymentEngine** — In-memory engine cho testing
- **Idempotency Protection** — Key-based deduplication
- **Webhook Handling** — Signature verification + status callbacks
- **24 Jinja2 Templates** (6 files × 4 stacks: FastAPI, NestJS, Angular, React)
- **10 Error Codes** (MDC-CP45-001 ~ MDC-CP45-010)
- **2 Recipes**: basic_payment_recipe, full_payment_recipe
- **Registry Integration** — CP45 registered trong contracts/registry.py
- **150+ Tests** — Models, parser, recipes, templates, emitters

### Dependencies

- CP01 (Domain Model)
- CP05 (Event-Driven Architecture)
- CP14 (Audit Trail & Compliance)
- CP33 (Financial Engine)
- CP40 (Webhook & Outbound Integration)
