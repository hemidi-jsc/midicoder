# Changelog — CP29 Multi-Language Support Generator

## [1.1.0] — 2026-05-20

### Added
- I18nKey model: dotted namespace convention (entity.*, command.*, query.*, event.*)
- LanguageProfile model: locales, default_locale, fallback_chain
- I18nBundle model: per-locale translation bundle with to_dict()
- I18nKeyset collection: sorted keys, duplicate detection, serialization
- I18nParser: auto-extract i18n keys from MIR metadata (entities, commands, queries, events)
- Recipes: auto_generate_i18n_from_mir(), generate_language_profile(), generate_i18n_bundles()
- FastAPI templates: i18n.py (babel/gettext), config, .po locale files (en, vi)
- NestJS templates: i18n module, i18n service, JSON locale files (en, vi)
- Angular templates: i18n service, XLIFF locale files (en, vi)
- React templates: i18next init, useTranslation hook, JSON locale files (en, vi)
- Error codes: MDC-CP29-001 through MDC-CP29-010
- Registry entry: CP29 → cp29_multi_language
- pack.yml manifest with file_contributions for 4 stacks
