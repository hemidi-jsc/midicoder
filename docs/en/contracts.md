# Contracts and DSL

Contracts are YAML files that represent the system design. They are generated from `master-brief.md` and validated against a schema.

## Master brief

`midicoder version create <ver>` generates:

```
.midicoder/versions/<ver>/master-brief.md
```

The template covers product goals, domain entities, workflows, rules, API routes, and non-functional requirements. This brief is the input for contract generation.

## Contract generation

Command:

```bash
midicoder contract gen
```

Inputs:

- `master-brief.md`
- Project Context
- DSL schema (see `technic/DSL-schema.md`)

Outputs:

```text
.midicoder/versions/<ver>/contracts/
  meta/info.yaml
  glossary.yaml
  domain/entities.yaml
  domain/value_objects.yaml
  domain/errors.yaml
  domain/events.yaml
  app/commands.yaml
  app/queries.yaml
  rules/*.yaml
  workflows/*.yaml
  policy/rbac.yaml
  policy/permissions_map.yaml
  persistence/model.yaml
  api/http.yaml
  scenarios/*.yaml or *.feature
```

## Smart resume

`midicoder contract gen resume` scans the last run and generates only missing or failed files, saving tokens and time.

## Validation and lint

All outputs are validated by schema and cross-file checks. Errors are reported with details so you can correct the brief or contracts before moving to IR.
