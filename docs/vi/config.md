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

## Các trường quan trọng

- `working_dir`
  Đường dẫn tuyệt đối tới repo.
- `stack`
  Stack mục tiêu, ví dụ `fastapi`, `nest`, `angular`.
- `llm.high`
  Dùng cho các bước nặng như `contract gen` và quyết định patch.
- `llm.cheap`
  Dùng cho việc chuyển đổi code giữa các stack.
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

Xem thêm tại `non-interactive.md`.
