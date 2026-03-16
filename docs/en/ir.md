# IR Compiler

`midicoder ir build` compiles DSL contracts into deterministic IR JSON with strict validation. No LLMs are used in this step.

## Inputs

```
.midicoder/versions/<ver>/contracts/
```

## Outputs

```
.midicoder/versions/<ver>/ir/
  ir.json
  manifest.json
```

## What happens during IR build

1. Load all contract files.
2. Validate schema and structure.
3. Lint within each file.
4. Cross-reference entities, commands, workflows, and permissions.
5. Normalize and canonicalize IDs and references.
6. Emit `ir.json` and `manifest.json`.

If validation fails, the command exits with detailed errors.
