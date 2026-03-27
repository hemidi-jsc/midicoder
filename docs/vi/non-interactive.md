# Init Non-Interactive

`midicoder init` hỗ trợ non-interactive để dùng trong CI/CD hoặc automation scripts.

## Xem danh sách tùy chọn

```bash
midicoder init --config-list
```

## Provider được hỗ trợ

Mỗi tier (`high` và `cheap`) hỗ trợ các provider:

- `anthropic`
- `openai`
- `openai_compatible`
- `bedrock`
- `azure`
- `vertex_partner`

## Flags chung

- `--non-interactive`, `-y`
- `--config-list`
- `--env-prefix` (mặc định `MIDICODER_`)
- `--rewrite-config`
- `--working-dir`
- `--stack`

## Flags theo provider

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

Ví dụ với provider `anthropic`:

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

Các biến thường dùng:

- `MIDICODER_WORKING_DIR`
- `MIDICODER_STACK`
- `MIDICODER_LLM_HIGH_PROVIDER`
- `MIDICODER_LLM_CHEAP_PROVIDER`
- Theo từng provider sẽ có nhóm biến tương ứng với các flags ở trên

## Ví dụ command-line flags

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

Ví dụ với provider `azure`:

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

## Thứ tự ưu tiên

1. Command-line flags
2. Environment variables
3. Default

## Chính sách ghi đè config

Nếu `.midicoder/config.json` đã tồn tại, non-interactive sẽ fail-fast trừ khi cho phép ghi đè rõ ràng:

```bash
# Cách 1: dùng flag
midicoder init --non-interactive --rewrite-config

# Cách 2: dùng env var theo prefix mặc định
export MIDICODER_REWRITE_CONFIG=true
midicoder init --non-interactive
```

Nếu dùng `--env-prefix` tùy chỉnh, env var ghi đè cũng đổi theo prefix đó (ví dụ `MC_REWRITE_CONFIG=true` khi `--env-prefix MC_`).

Khi ghi đè, chỉ `config.json` và `secrets.json` được cập nhật; các dữ liệu khác như runs/logs/versions/index vẫn giữ nguyên.

## Lưu ý bảo mật

- Tránh truyền API key trực tiếp qua `--llm-*-key`; ưu tiên dùng `--llm-*-key-env`.
- API key có thể để trống lúc `init` (ví dụ khi dùng credential ngoài), nhưng các lệnh gọi LLM sau đó có thể lỗi nếu thiếu credential phù hợp.
