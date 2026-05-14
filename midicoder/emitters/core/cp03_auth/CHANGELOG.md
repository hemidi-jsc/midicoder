# Changelog — CP03 Authentication & Authorization Framework

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-05-14

### Added

- **Models**: SAMLAuthConfig, LDAPOAuthConfig, MTLSAuthConfig, StatefulSessionConfig (previously missing from parser)
- **Models**: RateLimitStrategyType, RateLimitConfig (rate limiting strategies)
- **Models**: MFAProviderType, TOTPAlgorithm, TOTPConfig, WebAuthnConfig, MFAPolicy (MFA support)
- **Parser**: SAML 2.0, LDAP, mTLS, Stateful Session parsing (was raising errors before)
- **Recipes**: jwt_recipe, oauth2_recipe, saml_recipe, ldap_recipe, mtls_recipe, stateful_session_recipe
- **Recipes**: mfa_totp_recipe, mfa_webauthn_recipe, multi_provider_recipe
- **Pipeline**: CP03 registered in pack_emitter_router.py (4 entries: fastapi, nestjs, angular, react)
- **Tests**: Moved from tests/emitters/ to pack's tests/ directory (11 test files, 200 tests)
- **Tests**: Extended models test (RateLimitConfig, TOTPConfig, WebAuthnConfig, MFAPolicy)
- **Tests**: Extended parser test (SAML, LDAP, mTLS, Session parsing)
- **Tests**: Recipes test (all 9 recipe functions)

### Changed

- AuthIR now includes `rate_limit` and `mfa` fields
- pack.yml updated: definitions_count 2→19, obligations_count 2→10
- taxonomy.yml updated: CP03 version 1.0.0→1.1.0, definitions_count 2→19, obligations_count 2→10
- **init**.py updated: all new models and recipes exported

### Fixed

- Template: FastAPI oauth2_provider.py.jinja2 — HTTP_000 → HTTP_502_BAD_GATEWAY (3 occurrences)
- Template: NestJS tenant_context.ts.jinja2 — removed dead import `activateFilters`
- Template: NestJS **init**.ts.jinja2 — removed references to non-existent rbac.service, permissions.module
- Template: React api-client.ts.jinja2 — aligned with emitter (axios instead of fetch API)

### Removed

- OAuth2AuthConfig validation for empty authorization_url/token_url (custom providers fill at runtime)

---

## [1.0.0] - 2026-05-07

### Added

- Separated CP03 from authnz/ (previously bundled with CP02+CP03+CP04)
- **Models**: AuthProviderType, JWTAuthConfig, OAuth2AuthConfig, SessionConfig, Permission, AuthIR
- **Parser**: AuthParser (YAML → AuthIR)
- **FastAPI Emitter**: jwt_auth.py, session.py, permissions.py
- **NestJS Emitter**: jwt-auth.guard.ts, auth.service.ts, permissions.decorator.ts, auth.module.ts
- **Angular Emitter**: auth.service.ts, auth.guard.ts, jwt.interceptor.ts, auth.module.ts
- **React Emitter**: AuthContext.tsx, useAuth.ts, ProtectedRoute.tsx, api-client.ts
- **Unit Tests**: 40 tests for models (100% coverage)
- **Integration Tests**: Parser + 4 stack emitters

---

**Capabilities Provided:** `authorize_permission`, `authenticate_user`

**Capabilities (Runtime):** `jwt_auth`, `oauth2_auth`, `saml_sso`, `ldap_auth`, `mtls_auth`,
`stateful_session`, `session_management`, `permission_authorization`, `rate_limiting`, `mfa_totp`, `mfa_webauthn`

**Obligations:**

1. **AuthRequired** — All protected endpoints must enforce authentication
2. **TokenExpiry** — Auth tokens must have configurable expiration
3. **SAMLSignatureValidation** — SAML assertions must be signature-verified before trust
4. **LDAPSecureBind** — LDAP connections must use LDAPS or StartTLS
5. **mTlsCaRequired** — mTLS provider must have CA certificate path
6. **SessionTTLPositive** — Stateful session TTL must be positive
7. **RateLimitPositive** — Rate limit max_requests and window must be positive
8. **TOTPDigitCount** — TOTP digit count must be 6 or 8
9. **WebAuthnOriginRequired** — WebAuthn must specify relying party ID, name, and origins
10. **MFAMandatoryProviders** — MFA required must have at least one provider

**Dependencies:** CP01, CP02
