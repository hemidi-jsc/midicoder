# Contracts và DSL

Contracts là các file YAML thể hiện thiết kế hệ thống. Chúng được tạo từ `master-brief.md` và luôn qua schema validation.

## Master brief

`midicoder version create <ver>` tạo:

```
.midicoder/versions/<ver>/master-brief.md
```

Template bao phủ mục tiêu sản phẩm, domain entities, workflows, rules, API routes, và phi chức năng. Đây là input cho contract generation.

## Sinh contracts

Lệnh:

```bash
midicoder contract gen
```

Input:

- `master-brief.md`
- Project Context
- DSL schema (xem `technic/DSL-schema.md`)

Output:

```text
.midicoder/versions/<ver>/contracts/
  meta/info.yaml
  glossary.yaml
  domain/entities.yaml
  domain/value_objects.yaml
  domain/errors.yaml
  domain/events.yaml
  app/commands.yaml
  app/queries.yaml
  rules/*.yaml
  workflows/*.yaml
  policy/rbac.yaml
  policy/permissions_map.yaml
  persistence/model.yaml
  api/http.yaml
  scenarios/*.yaml hoặc *.feature
```

## Smart resume

`midicoder contract gen resume` chỉ generate các file thiếu hoặc lỗi ở lần chạy trước.

## Validation và lint

Tất cả outputs đều được validate và check cross-file trước khi qua bước IR.
