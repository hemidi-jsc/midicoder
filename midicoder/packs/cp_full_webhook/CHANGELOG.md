# CP40 — Webhook & Outbound Integration Hub
#
# Version: 1.0.0
# Status: stable
#
# Changelog:
# - 1.0.0 (2026-05-22): Initial release
#   - Webhook subscription management (CRUD)
#   - Event-driven dispatch với REST API + listener
#   - Retry policy (exponential backoff)
#   - Redis queue cho async dispatch
#   - HMAC-SHA256 signature verification
#   - Rate limiting per subscription
#   - Audit integration (CP14)
#   - Frontend dashboard (Angular, React)
#   - 4 stacks: FastAPI (7), NestJS (7), Angular (4), React (4)
#   - 163+ tests, 100% coverage
