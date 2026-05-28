# CP26: Documentation Generator — Changelog

## Version 1.0.0 (2026-05-20)

### Added
- Initial implementation của CP26 Documentation Generator
- Models: DocPortalType, DocPortal, DocSection, ApiDocConfig, DocCollection
- DocParser: Parse YAML/metadata → DocCollection
- FastAPI emitter: MkDocs + OpenAPI (mkdocs.yml, docs_index.md, openapi.json, nav.md)
- NestJS emitter: Swagger + Docusaurus (swagger_config.ts, docusaurus.config.js, sidebar.js, docs_index.md)
- Angular emitter: Storybook + typedoc (main.ts, preview.ts, typedoc.json, components.md)
- React emitter: Storybook + typedoc (main.ts, preview.ts, typedoc.json, components.md)
- Recipes: auto_generate_docs_from_mir, generate_api_docs, generate_component_docs, generate_project_docs
- Error codes: MDC-CP26-001 đến MDC-CP26-012
- Templates jinja2 cho tất cả 4 stacks (16 templates)
