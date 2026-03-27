# Non-Interactive Init

`midicoder init` supports non-interactive setup for CI/CD or automation.

## Show available options

```bash
midicoder init --config-list
```

## Supported providers

Each tier (`high` and `cheap`) supports:

- `anthropic`
- `openai`
- `openai_compatible`
- `bedrock`
- `azure`
- `vertex_partner`

## Common flags

- `--non-interactive`, `-y`
- `--config-list`
- `--env-prefix` (default `MIDICODER_`)
- `--rewrite-config`
- `--working-dir`
- `--stack`

## Provider-specific flags

- Provider `openai_compatible`:
  - `--llm-high-provider`, `--llm-cheap-provider`
  - `--llm-high-model`, `--llm-high-url`, `--llm-high-key`, `--llm-high-key-env`
  - `--llm-cheap-model`, `--llm-cheap-url`, `--llm-cheap-key`, `--llm-cheap-key-env`
- Provider `anthropic`:
  - `--llm-high-anthropic-model`, `--llm-high-anthropic-key`, `--llm-high-anthropic-key-env`
  - `--llm-cheap-anthropic-model`, `--llm-cheap-anthropic-key`, `--llm-cheap-anthropic-key-env`
- Provider `openai`:
  - `--llm-high-openai-model`, `--llm-high-openai-key`, `--llm-high-openai-key-env`
  - `--llm-cheap-openai-model`, `--llm-cheap-openai-key`, `--llm-cheap-openai-key-env`
- Provider `bedrock`:
  - `--llm-high-bedrock-model`, `--llm-high-aws-region-name`, `--llm-high-aws-access-key-id`, `--llm-high-aws-access-key-id-env`, `--llm-high-aws-secret-access-key`, `--llm-high-aws-secret-access-key-env`
  - `--llm-cheap-bedrock-model`, `--llm-cheap-aws-region-name`, `--llm-cheap-aws-access-key-id`, `--llm-cheap-aws-access-key-id-env`, `--llm-cheap-aws-secret-access-key`, `--llm-cheap-aws-secret-access-key-env`
- Provider `azure`:
  - `--llm-high-azure-model`, `--llm-high-azure-key`, `--llm-high-azure-key-env`, `--llm-high-azure-openai-endpoint`, `--llm-high-azure-openai-api-version`, `--llm-high-azure-openai-deployment`
  - `--llm-cheap-azure-model`, `--llm-cheap-azure-key`, `--llm-cheap-azure-key-env`, `--llm-cheap-azure-openai-endpoint`, `--llm-cheap-azure-openai-api-version`, `--llm-cheap-azure-openai-deployment`
- Provider `vertex_partner`:
  - `--llm-high-vertex-model`, `--llm-high-vertex-key`, `--llm-high-vertex-key-env`, `--llm-high-vertex-project`, `--llm-high-vertex-location`
  - `--llm-cheap-vertex-model`, `--llm-cheap-vertex-key`, `--llm-cheap-vertex-key-env`, `--llm-cheap-vertex-project`, `--llm-cheap-vertex-location`

## Environment variables

Example with provider `anthropic`:

```bash
export MIDICODER_WORKING_DIR=/path/to/project
export MIDICODER_STACK=fastapi,nest
export MIDICODER_LLM_HIGH_PROVIDER=anthropic
export MIDICODER_LLM_HIGH_ANTHROPIC_MODEL=anthropic/claude-3-7-sonnet-latest
export MIDICODER_LLM_HIGH_ANTHROPIC_API_KEY=sk-ant-...
export MIDICODER_LLM_CHEAP_PROVIDER=anthropic
export MIDICODER_LLM_CHEAP_ANTHROPIC_MODEL=anthropic/claude-3-5-haiku-latest
export MIDICODER_LLM_CHEAP_ANTHROPIC_API_KEY=sk-ant-...

midicoder init --non-interactive
```

Commonly used variables:

- `MIDICODER_WORKING_DIR`
- `MIDICODER_STACK`
- `MIDICODER_LLM_HIGH_PROVIDER`
- `MIDICODER_LLM_CHEAP_PROVIDER`
- Each provider has its own variable group matching the flags above

## Command-line flag examples

```bash
midicoder init \
  --non-interactive \
  --working-dir /path/to/project \
  --stack fastapi \
  --llm-high-provider anthropic \
  --llm-high-anthropic-model anthropic/claude-3-7-sonnet-latest \
  --llm-high-anthropic-key-env ANTHROPIC_API_KEY \
  --llm-cheap-provider anthropic \
  --llm-cheap-anthropic-model anthropic/claude-3-5-haiku-latest \
  --llm-cheap-anthropic-key-env ANTHROPIC_API_KEY
```

Example with provider `azure`:

```bash
midicoder init \
  --non-interactive \
  --working-dir /path/to/project \
  --stack fastapi \
  --llm-high-provider azure \
  --llm-high-azure-model azure/gpt-4o \
  --llm-high-azure-openai-endpoint https://my-resource.openai.azure.com \
  --llm-high-azure-openai-api-version 2024-10-21 \
  --llm-high-azure-openai-deployment gpt-4o-prod \
  --llm-high-azure-key-env AZURE_OPENAI_API_KEY \
  --llm-cheap-provider azure \
  --llm-cheap-azure-model azure/gpt-4o-mini \
  --llm-cheap-azure-openai-endpoint https://my-resource.openai.azure.com \
  --llm-cheap-azure-openai-api-version 2024-10-21 \
  --llm-cheap-azure-openai-deployment gpt-4o-mini-dev \
  --llm-cheap-azure-key-env AZURE_OPENAI_API_KEY
```

## Precedence

1. Command-line flags
2. Environment variables
3. Defaults

## Rewrite config policy

If `.midicoder/config.json` already exists, non-interactive init refuses overwrite unless you explicitly allow it:

```bash
# Option 1: flag
midicoder init --non-interactive --rewrite-config

# Option 2: env var with default prefix
export MIDICODER_REWRITE_CONFIG=true
midicoder init --non-interactive
```

If you use a custom `--env-prefix`, the rewrite env var follows that prefix (for example `MC_REWRITE_CONFIG=true` when `--env-prefix MC_`).

When overwrite is enabled, only `config.json` and `secrets.json` are updated; other data such as runs/logs/versions/index is preserved.

## Security note

- Avoid passing real API keys directly via `--llm-*-key`; prefer `--llm-*-key-env`.
- API keys can be omitted at init time (for example when external credentials are used), but later LLM commands may fail if required credentials are missing.
