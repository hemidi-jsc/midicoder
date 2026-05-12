# Changelog - CP08 Database & Data Access Layer

## [1.0.0] - 2026-05-06
### Added
- Datasource model with engine types, pool config, read replica support
- DSL YAML parser with parse(raw: str) method
- __post_init__ validation for all models
- 10 error codes (MDC-CP08-001 to MDC-CP08-010)
- pack.yml registry integration
- Enhanced emitters: connection config, base repository, migration, seed data
- Full TDD test coverage