# Cấu hình

`midicoder init` ghi cấu hình vào `.midicoder/config.json` và secrets vào `.midicoder/secrets.json`.

## Ví dụ config

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

## Các trường quan trọng

- `working_dir`
  Đường dẫn tuyệt đối tới repo.
- `stack`
  Stack mục tiêu, ví dụ `fastapi`, `nest`, `angular`.
- `llm.high`
  Dùng cho các bước nặng như `contract gen` và quyết định patch.
- `llm.cheap`
  Dùng cho việc chuyển đổi code giữa các stack.
- `llm.*.provider`
  ID provider cho từng tier. Giá trị hỗ trợ: `anthropic`, `openai`, `openai_compatible`, `bedrock`, `azure`, `vertex_partner`.
- Các trường provider-specific
  Tùy provider, init có thể yêu cầu thêm các trường như `aws_region_name`, `azure_openai_endpoint`, `azure_openai_api_version`, `azure_openai_deployment`, `vertex_project`, `vertex_location`.
- Secrets theo provider
  Với `bedrock`, mỗi tier được cấu hình còn cần `aws_access_key_id` và `aws_secret_access_key` trong `.midicoder/secrets.json` (hoặc credential tương đương từ môi trường chạy).
- `cache`
  Bật cache tạm cho LLM.
- `snapshot_whitelist`
  Danh sách glob để giới hạn snapshot.

## Secrets

`.midicoder/secrets.json` lưu API keys và không nên commit.

```json
{
  "llm": {
    "high": { "api_key": "sk-ant-..." },
    "cheap": { "api_key": "sk-ant-..." }
  }
}
```

## Thứ tự ưu tiên trong non-interactive

1. Command-line flags
2. Environment variables
3. Default

## Hành vi ghi đè trong non-interactive init

Nếu config đã tồn tại, non-interactive init sẽ từ chối ghi đè trừ khi bật rõ ràng:

- `--rewrite-config`, hoặc
- `MIDICODER_REWRITE_CONFIG=true`

Việc ghi đè chỉ cập nhật `.midicoder/config.json` và `.midicoder/secrets.json`; các artifacts khác như runs, logs, versions, index trong `.midicoder` vẫn được giữ nguyên.

Xem thêm tại `non-interactive.md`.
