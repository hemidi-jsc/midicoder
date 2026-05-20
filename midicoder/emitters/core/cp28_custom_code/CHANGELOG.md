# Changelog — CP28 Custom Code Injection Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-05-20

### Added

- **Models**: `HookEvent` (on_before_emit, on_after_emit, on_template_render, on_file_write), `HookAction` (inject, modify, skip)
- **Models**: `CustomCodeBlock` — block code tùy chỉnh với target, position, stack filter, language
- **Models**: `Hook` — compile-time hook với event, action, condition, code
- **Models**: `PatchRule` — regex-based patch rule với target_pattern, replacement, enabled, stack filter
- **Models**: `CustomCodeCollection` — aggregate + serialization (to_dict/from_dict)
- **Parser**: `CustomCodeParser` — parse YAML/dict → CustomCodeCollection
- **Parser**: `parse_from_metadata()` — parse từ MIR metadata dict
- **Recipes**: `auto_generate_custom_code_from_mir()` — generate default blocks/hooks/patches từ MIR
- **Recipes**: `generate_default_blocks()` — 1 block extension cho mỗi entity/command
- **Recipes**: `generate_default_hooks()` — logging, tenant_check, skip_test_files
- **Recipes**: `generate_default_patch_rules()` — type hints, import order
- **Error codes**: 12 mã (MDC-CP28-001 → MDC-CP28-012)
- **FastAPI templates** (6): __init__, inject, blocks, hooks, patches, registry
- **NestJS templates** (5): injector, blocks, hooks, patches, registry
- **Angular templates** (5): injector, blocks, hooks, patches, registry
- **React templates** (5): injector, blocks, hooks, patches, registry
- **Tests**: 99 tests — models (35), parser (20), recipes (25), templates (19)

### Capabilities Provided

`custom_code_inject`, `hook_define`, `patch_apply`

### Dependencies

CP01 (Domain Model DSL & IR Builder)
