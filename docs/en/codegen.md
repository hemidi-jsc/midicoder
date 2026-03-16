# Codegen and Patches

This page covers `code build`, `code gen`, and `code apply`.

## Code build

Command:

```bash
midicoder code build
```

Output:

```text
.midicoder/versions/<ver>/plans/
  index.json
  commands/*.code-plan.json
  workflows/*.code-plan.json
  api/*.code-plan.json
```

Plans are deterministic FastAPI pseudo code used for later patch planning.

## Code gen

Command:

```bash
midicoder code gen
```

Step 1 (high model): choose files, anchors, and patch operations.
Step 2 (cheap model): convert pseudo code to the target stack if needed.

Output:

```text
.midicoder/versions/<ver>/patches/
  plans/
    index.json
    commands/*.patch-plan.json
    workflows/*.patch-plan.json
```

## Patch plan structure

Each `*.patch-plan.json` includes:

- `path`
- `operation` (write, edit, delete)
- `anchor` and `mode` for edits
- `content` for the final code

## Code apply

Command:

```bash
midicoder code apply
```

Applies patch plans, creates snapshots, and records:

- `ops.json`
- unified diffs in `.patch` files

These outputs are stored under `.midicoder/runs/` and `.midicoder/versions/<ver>/patches/`.
