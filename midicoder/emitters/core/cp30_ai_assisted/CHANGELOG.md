# Changelog

## 1.0.0 (2026-05-20)

### Added

- **AI Review Policy Engine** (`ai_review`)
  - `ReviewPolicy` dataclass: id, name, severity, category, enabled, prompt_template_ref
  - `ReviewResult` dataclass: finding_id, policy_id, severity, message, line_range, suggestion
  - `ReviewSeverity` enum: error, warning, info
  - `ReviewCategory` enum: security, performance, style, correctness
  - Policy registry với lookup theo ID và category

- **AI Suggestion Engine** (`ai_suggest`)
  - `SuggestionContext` dataclass: file_path, language, code_snippet, cursor_position, intent
  - `SuggestionResult` dataclass: id, type, content, confidence, explanation
  - `SuggestionType` enum: completion, refactor, fix, explain

- **Prompt Template Management** (`prompt_template`)
  - `PromptTemplate` dataclass: id, name, category, content, variables, version, metadata
  - `PromptCategory` enum: code_review, code_suggestion, code_generation, documentation, testing, custom
  - Template registry với CRUD và variable substitution

- **Configuration System**
  - `AIAssistantConfig` dataclass: enabled, default_model, max_tokens, temperature, timeout
  - Config-driven — không hardcode LLM provider/API key

- **Parser & Recipes**
  - `AIAssistantParser`: parse YAML/dict/metadata thành AIAssistantCollection
  - `auto_generate_ai_assistant_from_mir()`: sinh default policies, templates, config
  - 6 default review policies (security, performance, style, correctness)
  - 8 default prompt templates (review, suggestion, doc, test)

- **Stack Templates (4 stacks)**
  - FastAPI: 7 templates (Python)
  - NestJS: 5 templates (TypeScript)
  - Angular: 6 templates (TypeScript)
  - React: 6 templates (TypeScript/TSX)
