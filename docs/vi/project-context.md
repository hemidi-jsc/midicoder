# Project Context

`midicoder index` tạo Project Context để LLM và pipeline hiểu repo hiện tại.

## Các file được tạo

```text
.midicoder/context/
  manifest.json
  profile.json
  symbols.json
  entrypoints.json
  seams.json
  exemplars.json
```

## Ý nghĩa

- `profile.json`
  Nhận diện stack, ngôn ngữ, conventions.
- `symbols.json`
  Danh sách class và function với vị trí file.
- `entrypoints.json`
  Các entrypoint của app.
- `seams.json`
  Điểm tích hợp an toàn để patch.
- `exemplars.json`
  Snippet mẫu để giữ style nhất quán.
- `manifest.json`
  Metadata của quá trình scan.

## Index theo stack

Midi Coder ưu tiên indexer theo stack:

- FastAPI
- NestJS
- Angular

Nếu không detect được stack, sẽ dùng indexer generic.
