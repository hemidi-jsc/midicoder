# CP42 — Approval Workflow Engine
#
# Version: 1.0.0
# Status: stable
#
# Changelog:
# - 1.0.0 (2026-05-22): Initial release
#   - Multi-level approval chain management
#   - Approval matrix based on role, department, threshold
#   - Delegation system (temporary/permanent/conditional)
#   - Automatic escalation on timeout/rejection
#   - Voting mode (unanimous/majority/first-to-approve)
#   - RBAC validation trước khi quyết định phê duyệt
#   - Audit trail ghi log mọi quyết định
#   - Escalation worker cho timeout handling
#   - Frontend approval UI (Angular, React)
#   - 4 stacks: FastAPI (7), NestJS (7), Angular (6), React (6)
