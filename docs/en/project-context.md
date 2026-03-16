# Project Context

`midicoder index` builds Project Context to help the LLM and pipeline understand the repository.

## Files created

```text
.midicoder/context/
  manifest.json
  profile.json
  symbols.json
  entrypoints.json
  seams.json
  exemplars.json
```

## What they mean

- `profile.json`
  Detected stack, languages, and conventions.
- `symbols.json`
  Class and function definitions with file locations.
- `entrypoints.json`
  App entrypoints such as FastAPI app objects or Angular bootstrap.
- `seams.json`
  Safe integration points for patching.
- `exemplars.json`
  Example snippets for consistent style.
- `manifest.json`
  Metadata about the scan, root, and stack.

## Stack-aware indexing

Midi Coder prioritizes stack-specific indexers for:

- FastAPI
- NestJS
- Angular

If no stack is detected, a generic indexer is used.
