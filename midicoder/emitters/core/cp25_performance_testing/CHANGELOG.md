# CP25: Performance Testing Generator — Changelog

## Version 1.0.0 (2026-05-20)

### Added
- Initial implementation của CP25 Performance Testing Generator
- Models: PerfScenarioType, PerfScenario, PerfThreshold, PerfBaseline, PerfReport, PerfSuite, PerfCollection
- PerfParser: Parse YAML/metadata → PerfCollection
- FastAPI emitter: Locust (locustfile.py, locust.conf, perf tests, baseline runner)
- NestJS emitter: Artillery (artillery.yml, baseline runner)
- Angular emitter: Lighthouse CI + Playwright (lighthouserc.js, web-vitals.spec.ts, lighthouse-ci.js)
- React emitter: Lighthouse CI + Playwright (lighthouserc.js, web-vitals.test.tsx, lighthouse-ci.js)
- Recipes: auto_generate_perf_scenarios_from_mir, generate_load_scenarios, generate_web_vitals_tests, save_baseline, compare_baseline
- BaselineManager: Lưu/load/so sánh baseline vào SQLite artifacts
- Error codes: MDC-CP25-001 đến MDC-CP25-015
- Templates jinja2 cho tất cả 4 stacks
