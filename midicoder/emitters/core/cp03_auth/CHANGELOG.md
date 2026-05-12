# Changelog — CP03 Authentication & Authorization Framework

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

**Capabilities (Runtime):** `jwt_auth`, `oauth2_auth`, `session_management`, `permission_authorization`

**Obligations:**

1. **AuthRequired** — All protected endpoints must enforce authentication
2. **TokenExpiry** — Auth tokens must have configurable expiration

**Dependencies:** CP01, CP02
