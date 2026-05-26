# CP55: CI/CD Pipeline Generator — Changelog

## 1.0.0 (2026-05-26)

- Initial release
- 6 data models: PipelineConfig, PipelineStage, PipelineStep, GitHubActionsWorkflow, GitLabCIPipeline, Jenkinsfile
- CIIR parser với from_dict pattern
- 4 recipes: github_actions, gitlab_ci, jenkins, full_cicd
- Infrastructure emitter với 5 Jinja2 templates
- Registry, taxonomy, DSL loader, và router integration
