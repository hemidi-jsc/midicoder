# Changelog — CP27 Plugin System Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-05-20

### Added

- **Models**: `PluginStatus` (disabled, loading, enabled, error), `LifecycleEvent` (on_init, on_configure, on_ready, on_request, on_shutdown, before_*, after_*), `PolicyType` (security, versioning)
- **Models**: `PluginSlot` — định nghĩa điểm móc nối với events, priority_range, tenant_awareness
- **Models**: `PluginContract` — interface mà plugin phải implement (slots, config_schema, dependencies)
- **Models**: `PluginPolicy` — chính sách bảo mật + versioning (rule, enforced, config)
- **Models**: `PluginManifest` — metadata file cho plugin (id, name, version, slots, dependencies, signature)
- **Models**: `PluginContext` — runtime context (tenant_id, user_id, request_id, app_config, event_bus)
- **Models**: `PluginInfo`, `PluginCollection` — aggregate + serialization
- **Parser**: `PluginParser` — parse YAML/dict → PluginCollection (slots, contracts, policies)
- **Parser**: `parse_from_metadata()` — auto-generate từ MIR metadata (entities, commands, policies)
- **Recipes**: `auto_generate_plugins_from_mir()` — generate default slots/contracts/policies từ MIR
- **Recipes**: `generate_default_slots()` — lifecycle slots + before/after hooks per command
- **Recipes**: `generate_default_contracts()` — default contract từ entity list
- **Recipes**: `generate_default_policies()` — signature, version_gate, origin_whitelist
- **DSL**: 3 NodeKind mới — `plugin.slot`, `plugin.contract`, `plugin.policy` (dot notation)
- **DSL Params**: `PluginSlotParams`, `PluginContractParams`, `PluginPolicyParams`
- **Error codes**: 18 mã (MDC-CP27-001 → MDC-CP27-018)
- **FastAPI templates** (11): __init__, slots, contracts, policies, loader, registry, manager, api, middleware, example_plugin, plugin.json
- **NestJS templates** (11): plugins.module, slots, contracts, policies, plugin-loader, plugin-registry, plugin-manager, plugin.controller, plugin.middleware, example.plugin, plugin.json
- **Angular templates** (9): plugin.module, plugin-slots, plugin-contracts, plugin-loader, plugin-registry, plugin-api.service, plugin.interceptor, example.plugin, plugin.json
- **React templates** (7): plugin-slots, plugin-contracts, plugin-loader, plugin-registry, plugin-api, example.plugin, plugin.json
- **Tests**: 106 tests — models (44), parser (13), recipes (16), templates (33)

### Capabilities Provided

`plugin_slot_define`, `plugin_contract`, `plugin_policy`

### Dependencies

CP01 (Domain Model DSL & IR Builder)
