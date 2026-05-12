# Changelog

## [Unreleased]

### Changed
- Merged entity/, command/, query/, value_object/ into unified domain_model/ package
- All 28 modules now reside in single pack directory with namespaced file names
- Updated resolver.py mapping: CP01 → domain_model

### Fixed
- Removed CP23→command from resolver fallback (command is part of CP01)

## [1.0.0] - 2026-05-12

### Added
- Unified CP01 Domain Model pack with Entity, Command, Query, and Value Object modules
- Entity: EntityEmitter, FastAPIEntityEmitter, NestJSEntityEmitter, EntityParser
- Command: CommandValidator, CommandEffects, CommandGuards, TransactionManagerSQL
- Query: QueryGuards, QueryEffects, FastAPIQueryEmitter, NestJSQueryEmitter
- Value Object: ValueObjectEmitter, TypeResolver, InheritanceResolver, ComputedFieldEvaluator
