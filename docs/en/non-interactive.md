# Non-Interactive Init

`midicoder init` supports non-interactive setup for CI/CD or automation.

## Show available options

```bash
midicoder init --config-list
```

## Environment variables

```bash
export MIDICODER_WORKING_DIR=/path/to/project
export MIDICODER_STACK=fastapi,nest
export MIDICODER_LLM_HIGH_PROVIDER=anthropic
export MIDICODER_LLM_HIGH_MODEL=claude-sonnet-4-5
export MIDICODER_LLM_HIGH_URL=https://api.anthropic.com
export MIDICODER_LLM_HIGH_API_KEY=sk-ant-...
export MIDICODER_LLM_CHEAP_PROVIDER=anthropic
export MIDICODER_LLM_CHEAP_MODEL=claude-3-5-haiku
export MIDICODER_LLM_CHEAP_URL=https://api.anthropic.com
export MIDICODER_LLM_CHEAP_API_KEY=sk-ant-...

midicoder init --non-interactive
```

## Command-line flags

```bash
midicoder init \
  --non-interactive \
  --working-dir /path/to/project \
  --stack fastapi,nest \
  --llm-high-provider anthropic \
  --llm-high-model claude-sonnet-4-5 \
  --llm-high-url https://api.anthropic.com \
  --llm-high-key-env ANTHROPIC_API_KEY \
  --llm-cheap-provider anthropic \
  --llm-cheap-model claude-3-5-haiku \
  --llm-cheap-url https://api.anthropic.com \
  --llm-cheap-key-env ANTHROPIC_API_KEY
```

## Precedence

1. Command-line flags
2. Environment variables
3. Defaults

## Security note

Do not pass real API keys via `--llm-*-key`. Use `--llm-*-key-env` instead.
