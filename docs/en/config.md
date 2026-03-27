# Configuration

`midicoder init` writes configuration into `.midicoder/config.json` and secrets into `.midicoder/secrets.json`.

## Example config

```json
{
  "working_dir": "/absolute/path/to/project",
  "stack": ["fastapi", "nest"],
  "commands": [],
  "llm": {
    "high": {
      "provider": "anthropic",
      "model": "anthropic/claude-3-7-sonnet-latest",
      "base_url": "https://api.anthropic.com"
    },
    "cheap": {
      "provider": "anthropic",
      "model": "anthropic/claude-3-5-haiku-latest",
      "base_url": "https://api.anthropic.com"
    }
  },
  "cache": {
    "enable": true,
    "type": "ephemeral"
  },
  "snapshot_whitelist": null
}
```

## Key fields

- `working_dir`
  Absolute path to your project root. Used for indexing and patching.
- `stack`
  Target stacks. Options include `fastapi`, `nest`, `angular`.
- `llm.high`
  Used for complex steps such as `contract gen` and patch planning in `code gen`.
- `llm.cheap`
  Used for conversion between stacks in `code gen`.
- `llm.*.provider`
  Provider ID for each tier. Supported values: `anthropic`, `openai`, `openai_compatible`, `bedrock`, `azure`, `vertex_partner`.
- Provider-specific fields
  Depending on provider, init may require fields such as `aws_region_name`, `azure_openai_endpoint`, `azure_openai_api_version`, `azure_openai_deployment`, `vertex_project`, `vertex_location`.
- Provider-specific secrets
  For `bedrock`, each configured tier also requires `aws_access_key_id` and `aws_secret_access_key` in `.midicoder/secrets.json` (or equivalent external credentials available through your execution environment).
- `cache`
  Enables ephemeral caching for LLM responses.
- `snapshot_whitelist`
  Optional glob list to limit snapshots to critical files.

## Secrets

Secrets are stored in `.midicoder/secrets.json` and should not be committed.

```json
{
  "llm": {
    "high": { "api_key": "sk-ant-..." },
    "cheap": { "api_key": "sk-ant-..." }
  }
}
```

## Precedence in non-interactive init

1. Command-line flags
2. Environment variables
3. Defaults

## Rewrite behavior in non-interactive init

If config already exists, non-interactive init refuses overwrite unless explicitly enabled:

- `--rewrite-config`, or
- `MIDICODER_REWRITE_CONFIG=true`

Overwrite only updates `.midicoder/config.json` and `.midicoder/secrets.json`; existing runs, logs, versions, index, and other `.midicoder` artifacts are preserved.

See `non-interactive.md` for the full list of flags and variables.
