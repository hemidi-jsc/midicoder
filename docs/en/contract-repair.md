# Contract Feedback and Repair

Midi Coder supports a feedback-driven loop to improve contracts without rewriting them manually.

## Create feedback file

```bash
midicoder contract feedback
```

This creates `.midicoder/versions/<ver>/contract-feedbacks.yml` with a structured template.

## Prepare (validate only)

```bash
midicoder contract repair prepare
```

Validates the feedback file and references without calling LLM.

## Run repair

```bash
midicoder contract repair run
```

What it does:

- Applies fixes to contract YAML files.
- Updates `master-brief.md` to stay consistent.
- Extracts short memos into `.midicoder/context/memos/`.
- Updates feedback item status.

## Feedback template fields

- `id`
- `file`
- `location`
- `status`
- `issue`
- `suggestion`
- `last_error`
