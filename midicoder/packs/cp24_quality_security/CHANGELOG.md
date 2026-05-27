# Changelog — CP24 Quality & Security Scanner Generator

## 1.0.0 (2026-05-20)

- Initial release
- Models: QualityProfile, SecurityScanRule, SecurityScanConfig, QualityGateConfig, QualityViolation, QualityReport, QualityCollection
- Parser: QualityProfileParser (YAML/dict → QualityCollection)
- Recipes: auto_generate_quality_collection, generate_default_profiles, generate_strict_profiles, generate_security_config
- Emitters: FastAPI, NestJS, Angular, React (4 stacks)
- Templates: 21 Jinja2 templates across 4 stacks
- Pipeline integration: Registered in EMITTER_REGISTRY (structured emitter)
- Error codes: MDC-CP24-001 to MDC-CP24-010
- Registry: CP24 → cp24_quality_security
