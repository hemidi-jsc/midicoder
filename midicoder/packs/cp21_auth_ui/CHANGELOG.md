# Changelog

## [1.0.0] - 2026-05-19

### Added
- CP21 Authentication UI Generator
- 6 auth pages: Login, Register, ForgotPassword, ResetPassword, MFA Verify, OAuth Callback
- 2 route guards: RoleGuard, PermissionGuard (tách biệt khỏi CP03 AuthGuard)
- Session timeout modal + monitor service/hook
- Support 5 UI frameworks: Material, Tailwind, Bootstrap, AntD, Carbon
- Emit cho cả Angular và React
- Error codes MDC-CP21-001~005

### Models
- AuthPageType enum (6 pages)
- UIFrameworkType enum (5 frameworks)
- SessionMonitorConfig
- AuthPageConfig
- AuthUIConfig (main config)

### Emitters
- AngularAuthUIEmitter: 12 files (6 pages + 2 guards + session modal + session service + routes + module + index)
- ReactAuthUIEmitter: 11 files (6 pages + 2 route wrappers + session modal + session hook + routes + index)
