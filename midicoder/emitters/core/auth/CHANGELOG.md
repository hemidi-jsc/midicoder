# Changelog: CP03 Authentication & Authorization Framework

## [1.0.0] - 2026-05-07

### Added
- Tách CP03 riêng từ authnz/ (trước đó gộp chung CP02+CP03+CP04)
- Models: AuthProviderType, JWTAuthConfig, OAuth2AuthConfig, SessionConfig, Permission, AuthIR
- Parser: AuthParser (YAML → AuthIR)
- FastAPI Emitter: jwt_auth.py, session.py, permissions.py
- NestJS Emitter: jwt-auth.guard.ts, auth.service.ts, permissions.decorator.ts, auth.module.ts
- Angular Emitter: auth.service.ts, auth.guard.ts, jwt.interceptor.ts, auth.module.ts
- React Emitter: AuthContext.tsx, useAuth.ts, ProtectedRoute.tsx, api-client.ts
- pack.yml: Self-declare capabilities (authorize_permission, authenticate_user)
- Unit tests: 40 tests cho models (100% coverage)
- Integration tests: Parser + 4 stack emitters