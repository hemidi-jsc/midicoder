# Codegen và Patches

Trang này mô tả `code build`, `code gen`, và `code apply`.

## Code build

Lệnh:

```bash
midicoder code build
```

Output:

```text
.midicoder/versions/<ver>/plans/
  index.json
  commands/*.code-plan.json
  workflows/*.code-plan.json
  api/*.code-plan.json
```

Plans là pseudo code FastAPI deterministic để dùng cho patch planning.

## Code gen

Lệnh:

```bash
midicoder code gen
```

Step 1 (model high): chọn file, anchor, operation.
Step 2 (model cheap): convert pseudo sang stack đích nếu cần.

Output:

```text
.midicoder/versions/<ver>/patches/
  plans/
    index.json
    commands/*.patch-plan.json
    workflows/*.patch-plan.json
```

## Cấu trúc patch plan

Mỗi `*.patch-plan.json` bao gồm:

- `path`
- `operation` (write, edit, delete)
- `anchor` và `mode` cho edit
- `content` là code cuối

## Code apply

Lệnh:

```bash
midicoder code apply
```

Apply patch, tạo snapshot, và ghi:

- `ops.json`
- unified diff `.patch`

Các file nằm trong `.midicoder/runs/` và `.midicoder/versions/<ver>/patches/`.
