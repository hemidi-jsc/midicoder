# I03: CI/CD Pipeline Generator (cp_infra_cicd) — Changelog

## 2.0.0 (2026-05-28)

- **Migrated from CP55 to I03**: Renamed from `cp55_cicd` to `cp_infra_cicd` (taxonomy-v2)
- **Pack ID**: `CP55` → `I03`
- **Internal ID**: `cp55_cicd` → `cp_infra_cicd`
- **Error codes**: `MDC-CP55-*` → `MDC-I03-*`
- **Template paths**: Updated from `cp55_cicd/` → `cp_infra_cicd/`
- **Pack emitters**: Updated from `cp55.cicd.*` → `cp_infra_cicd.*`
- **Dependencies**: `[CP01, CP07, CP15]` → `[B01, I01, C03]`
- Added `render_context_support: true` and `type: infra` fields

## 1.0.0 (2026-05-26)

- Initial release
- 6 data models: PipelineConfig, PipelineStage, PipelineStep, GitHubActionsWorkflow, GitLabCIPipeline, Jenkinsfile
- CIIR parser với from_dict pattern
- 4 recipes: github_actions, gitlab_ci, jenkins, full_cicd
- Infrastructure emitter với 5 Jinja2 templates
- Registry, taxonomy, DSL loader, và router integration
