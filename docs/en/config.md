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
      "model": "claude-3-5-sonnet-20241022",
      "base_url": "https://api.anthropic.com"
    },
    "cheap": {
      "model": "claude-3-5-haiku-20241022",
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

See `non-interactive.md` for the full list of flags and variables.
