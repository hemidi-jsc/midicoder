# IR Compiler

`midicoder ir build` compile DSL contracts thành IR JSON deterministic, không dùng LLM.

## Input

```
.midicoder/versions/<ver>/contracts/
```

## Output

```
.midicoder/versions/<ver>/ir/
  ir.json
  manifest.json
```

## Các bước chính

1. Load toàn bộ contract.
2. Schema validation.
3. Lint trong từng file.
4. Cross-reference giữa các domain.
5. Normalize ID và references.
6. Ghi `ir.json` và `manifest.json`.

Nếu có lỗi, lệnh sẽ dừng và trả chi tiết.
