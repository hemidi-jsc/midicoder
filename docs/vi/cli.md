# Tham khảo Lệnh CLI

Tham khảo đầy đủ cho tất cả lệnh Midi Coder CLI.

## Lệnh Pipeline Cốt lõi

### `midicoder init`

Khởi tạo `.midicoder/` workspace và cấu hình.

**Cách dùng:**

```bash
# Chế độ interactive (mặc định)
midicoder init

# Chế độ non-interactive (CI/CD)
midicoder init --non-interactive

# Liệt kê tất cả configuration options
midicoder init --config-list
```

**Options:**

- `--non-interactive, -y`: Chạy ở chế độ non-interactive
- `--config-list`: Hiển thị tất cả configuration keywords và thoát
- `--env-prefix`: Environment variable prefix (mặc định: `MIDICODER_`)
- `--working-dir`: Đường dẫn working directory
- `--stack`: Danh sách tech stack cách nhau bằng dấu phẩy (vd: `fastapi,nest,angular`)
- `--llm-high-provider`: High-tier LLM provider (`anthropic` hoặc `openai`)
- `--llm-high-model`: Tên model LLM high-tier
- `--llm-high-url`: Base URL API LLM high-tier
- `--llm-high-key-env`: Environment variable chứa API key high-tier (khuyến nghị)
- `--llm-high-key`: API key high-tier (visible trong process list, dùng `--llm-high-key-env` thay thế)
- `--llm-cheap-provider`: Cheap-tier LLM provider
- `--llm-cheap-model`: Tên model LLM cheap-tier
- `--llm-cheap-url`: Base URL API LLM cheap-tier
- `--llm-cheap-key-env`: Environment variable chứa API key cheap-tier (khuyến nghị)
- `--llm-cheap-key`: API key cheap-tier (visible trong process list)

**Outputs:**

- `.midicoder/config.json`: Cấu hình chính
- `.midicoder/secrets.json`: API keys (gitignored)
- `.midicoder/state.json`: Pipeline state

**Ví dụ:**

```bash
# Interactive setup
midicoder init

# Non-interactive với environment variables
export MIDICODER_WORKING_DIR=/path/to/project
export MIDICODER_STACK=fastapi,nest
export MIDICODER_LLM_HIGH_PROVIDER=anthropic
export MIDICODER_LLM_HIGH_MODEL=claude-sonnet-4-5
export MIDICODER_LLM_HIGH_API_KEY=sk-ant-...
midicoder init --non-interactive

# Non-interactive với CLI flags
midicoder init \
  --non-interactive \
  --working-dir /path/to/project \
  --stack fastapi \
  --llm-high-provider anthropic \
  --llm-high-model claude-sonnet-4-5 \
  --llm-high-key-env ANTHROPIC_API_KEY \
  --llm-cheap-provider anthropic \
  --llm-cheap-model claude-3-5-haiku \
  --llm-cheap-key-env ANTHROPIC_API_KEY
```

**Xem thêm:** [Hướng dẫn Non-Interactive](non-interactive.md)

---

### `midicoder index`

Build Project Context bằng cách quét source code.

**Cách dùng:**

```bash
# Full index (lần đầu hoặc refresh hoàn toàn)
midicoder index

# Incremental reindex (chỉ files thay đổi)
midicoder index reindex --path src/users/controller.py src/auth/service.py
```

**Options:**

- `--path`: Danh sách đường dẫn files thay đổi (relative tới working_dir) cho incremental reindex

**Outputs:**

```
.midicoder/context/
├── manifest.json        # Scan metadata
├── profile.json         # Stack detection, conventions
├── symbols.json         # Classes, functions, methods
├── entrypoints.json     # Application entry points
├── seams.json           # Integration boundaries
└── exemplars.json       # Reference code snippets
```

**Khi nào dùng:**

- Sau `midicoder init` (lần đầu)
- Khi cấu trúc codebase thay đổi đáng kể
- Trước `midicoder contract gen` (để cung cấp context mới)
- Sau `midicoder code apply` (tự động trừ khi `--no-reindex`)

---

### `midicoder version create`

Tạo version workspace mới.

**Cách dùng:**

```bash
midicoder version create <version>
```

**Arguments:**

- `<version>`: Version identifier (vd: `0.1.0`, `feature-auth`, `v1.2.0`)

**Outputs:**

```
.midicoder/versions/<version>/
├── state.json           # Version metadata
├── master-brief.md      # Requirements template (user chỉnh sửa)
├── locks/               # Lock files
├── contracts/           # DSL contracts (từ contract gen)
├── irs/                 # IR JSON (từ ir build)
├── plans/               # Code plans (từ code build)
├── patches/             # Patch plans (từ code gen)
└── snapshots/           # Backups (từ code apply)
```

**Bước tiếp theo:**

1. Chỉnh sửa `.midicoder/versions/<version>/master-brief.md`
2. Chạy `midicoder contract gen`

---

### `midicoder contract gen`

Sinh DSL contracts từ `master-brief.md`.

**Cách dùng:**

```bash
# Sinh tất cả contracts
midicoder contract gen

# Resume từ run thất bại (smart retry)
midicoder contract gen resume
```

**Inputs:**

- `.midicoder/versions/<version>/master-brief.md` (do user viết)
- `.midicoder/context/*` (Project Context)
- DSL schema (built-in)
- LLM config (high-tier model)

**Outputs:**

```
.midicoder/versions/<version>/contracts/
├── meta/info.yaml
├── glossary.yaml
├── domain/
│   ├── entities.yaml
│   ├── value_objects.yaml
│   ├── errors.yaml
│   └── events.yaml
├── app/
│   ├── commands.yaml
│   └── queries.yaml
├── rules/*.yaml
├── workflows/*.yaml
├── policy/
│   ├── rbac.yaml
│   └── permissions_map.yaml
├── api/http.yaml
└── scenarios/*.yaml
```

**Smart Resume:**

Subcommand `resume` phân tích run mới nhất và chỉ regenerate các files thất bại hoặc thiếu:

```bash
midicoder contract gen resume
```

- Tiết kiệm đến 50% tokens
- Validates files hiện có
- Chỉ retry những gì cần thiết

**Traceability:**

Mỗi run tạo traces chi tiết trong `.midicoder/runs/contract_gen/<timestamp>/`:

- `summary.json`: Overall status
- `pass_*_*.json`: Per-file trace với prompt, response, processed YAML

**Bước tiếp theo:**

1. Review generated contracts trong `contracts/`
2. Tùy chọn chạy `midicoder contract check`
3. Chạy `midicoder ir build`

---

### `midicoder ir build`

Biên dịch contracts thành Intermediate Representation (IR).

**Cách dùng:**

```bash
# Build IR với diagrams
midicoder ir build

# Build IR không có diagrams (nhanh hơn)
midicoder ir build --skip-diagrams
```

**Options:**

- `--skip-diagrams`: Bỏ qua sinh Mermaid diagrams

**Inputs:**

- `.midicoder/versions/<version>/contracts/**/*.yaml`

**Outputs:**

```
.midicoder/versions/<version>/irs/
├── ir.json              # IR normalized đầy đủ
├── manifest.json        # Metadata, stats, unresolved refs
└── diagrams/            # (tùy chọn)
    ├── api/*.mmd
    ├── commands/*.mmd
    ├── entities/*.mmd
    └── workflows/*.mmd
```

**Quy trình (100% quyết định, không LLM):**

1. Load tất cả YAML files
2. Validate với Pydantic schema
3. Kiểm tra cross-references
4. Normalize IDs và format
5. Build IR modules
6. Sinh diagrams (tùy chọn)

**Bước tiếp theo:**

1. Review `ir.json` hoặc generated diagrams
2. Chạy `midicoder code build`

---

### `midicoder code build`

Sinh pseudo code plans từ IR.

**Cách dùng:**

```bash
midicoder code build
```

**Inputs:**

- `.midicoder/versions/<version>/irs/ir.json`
- `.midicoder/context/*` (Project Context)

**Outputs:**

```
.midicoder/versions/<version>/plans/
├── index.json           # Plan registry
├── commands/*.code-plan.json
├── workflows/*.code-plan.json
└── api/*.code-plan.json
```

**Quy trình (100% quyết định, không LLM):**

1. Load IR JSON
2. Trích xuất components (Commands, Workflows, API)
3. Map vào folder structure
4. Sinh pseudo code với anchors

**Bước tiếp theo:**

1. Review plans trong `plans/`
2. Chạy `midicoder code gen`

---

### `midicoder code gen`

Sinh patch plans từ pseudo code plans.

**Cách dùng:**

```bash
# Sinh patch plans only (mặc định)
midicoder code gen

# Sinh patch plans + runtime files
midicoder code gen --runtime
```

**Options:**

- `--runtime`: Cũng sinh runtime source files vào `.midicoder/versions/<version>/patches/runtime/`

**Inputs:**

- `.midicoder/versions/<version>/plans/`
- `.midicoder/context/*` (Project Context)
- LLM config (high-tier cho patch strategy, cheap-tier cho stack conversion)

**Outputs:**

```
.midicoder/versions/<version>/patches/
├── plans/
│   ├── index.json       # Patch plan registry
│   ├── commands/*.patch-plan.json
│   ├── workflows/*.patch-plan.json
│   └── api/*.patch-plan.json
└── runtime/             # (tùy chọn, với --runtime)
    └── generated source files
```

**Quy trình:**

1. **Bước 1 (high-tier LLM)**: Quyết định patch locations và operations
2. **Bước 2 (cheap-tier LLM hoặc skip)**: Chuyển đổi sang target stack syntax
   - Skip nếu target = FastAPI
   - Translate nếu target = NestJS/Angular

**Bước tiếp theo:**

1. Review patch plans trong `patches/plans/`
2. Tùy chọn review runtime files (nếu `--runtime`)
3. Chạy `midicoder code apply`

---

### `midicoder code apply`

Áp dụng patch plans vào working directory.

**Cách dùng:**

```bash
# Áp dụng patches (với safety checks)
midicoder code apply

# Preview không áp dụng
midicoder code apply --dry-run

# Force apply (bỏ qua conflict checks)
midicoder code apply --force

# Apply không reindexing (debug only)
midicoder code apply --no-reindex
```

**Options:**

- `--dry-run`: Preview operations không ghi files
- `--force`: Force apply khi phát hiện conflicts (có thể gây merge issues)
- `--no-reindex`: Tắt tự động reindexing sau apply (không khuyến nghị)

**Inputs:**

- `.midicoder/versions/<version>/patches/plans/`

**Outputs:**

```
.midicoder/versions/<version>/patches/<run_id>/
├── ops.json             # Applied operations log
└── *.patch              # Unified diffs

.midicoder/versions/<version>/snapshots/<run_id>/
└── backed up files
```

**Quy trình:**

1. Pre-flight checks (validate plans, check writability, detect conflicts)
2. Tạo snapshots
3. Áp dụng patches (write/edit/delete operations)
4. Verify và record operations
5. Reindex (cập nhật Project Context)

**Tính năng an toàn:**

- Snapshots trước khi modification
- Conflict detection
- Dry run mode
- Rollback capability

---

## Contract Utilities

### `midicoder contract check`

Validate contracts cho issues.

**Cách dùng:**

```bash
midicoder contract check
```

**Kiểm tra:**

- YAML syntax
- Schema compliance (Pydantic validation)
- Cross-references (Entity/Command/Workflow/etc.)
- Business logic consistency

**Output:**

- Success: Exit code 0, không có issues
- Failure: Exit code 1, danh sách issues với locations và suggestions

**Ví dụ output:**

```
[contract check] FAILED – 3 issue(s) found
- contracts/app/commands.yaml:15: Command 'CreateOrder' references unknown entity 'Order'
  Suggestion: Add 'Order' entity in domain/entities.yaml or fix reference
- contracts/domain/entities.yaml:42: Duplicate entity ID 'User' found
- contracts/api/http.yaml:8: Route '/orders' references unknown command 'ListOrders'
```

---

### `midicoder contract feedback`

Tạo/cập nhật feedback file cho contract review.

**Cách dùng:**

```bash
midicoder contract feedback
```

**Quy trình:**

1. Chạy `contract check` để lấy validation issues
2. Tạo/cập nhật `.midicoder/versions/<version>/contract-feedbacks.yml`
3. Thêm feedback items mới từ validation issues

**Output:**

```
.midicoder/versions/<version>/contract-feedbacks.yml
```

**Ví dụ feedback file:**

```yaml
meta:
  version: "0.1.0"
  author: "you@team"
  created_at: "2025-02-10T10:15:00Z"
  scope: "contracts"

items:
  - id: FB-001
    file: contracts/app/commands.yaml
    location: "commands[id=CreateOrder]"
    status: pending  # pending | in_progress | done | error
    issue: |
      CreateOrder command thiếu authorization guard.
    suggestion: |
      Thêm guard với permission = "create_order"

notes:
  - "Follow RBAC guidelines"
```

**Bước tiếp theo:**

1. Chỉnh sửa feedback file để thêm custom review notes
2. Chạy `midicoder contract repair prepare` để validate
3. Chạy `midicoder contract repair run` để áp dụng fixes

---

### `midicoder contract repair prepare`

Validate feedback file không chạy LLM.

**Cách dùng:**

```bash
midicoder contract repair prepare
```

**Kiểm tra:**

- Feedback file syntax (YAML)
- Referenced files tồn tại
- Referenced locations hợp lệ
- Không có duplicate feedback IDs

**Output:**

- Success: Feedback hợp lệ
- Failure: Danh sách validation errors

**Use case:** Dry-run validation trước expensive LLM repair operation.

---

### `midicoder contract repair run`

Áp dụng feedback items vào contracts dùng LLM.

**Cách dùng:**

```bash
midicoder contract repair run
```

**Inputs:**

- `.midicoder/versions/<version>/contract-feedbacks.yml`
- `.midicoder/versions/<version>/contracts/`
- `.midicoder/versions/<version>/master-brief.md`
- DSL schema
- LLM config (high-tier model)

**Quy trình:**

1. Load feedback file
2. Nhóm feedback items theo file
3. Xử lý files theo dependency order
4. Cho mỗi file:
   - LLM sinh patches dựa trên feedback
   - Validate patches với schema
   - Áp dụng patches vào contract file
5. Sync `master-brief.md` với changes
6. Trích xuất memos vào `.midicoder/context/memos/`
7. Cập nhật feedback status (pending → done/error)

**Outputs:**

- Updated contract files
- Updated `master-brief.md`
- Memos trong `.midicoder/context/memos/`
- Updated `contract-feedbacks.yml` với status

**Lợi ích:**

- Iterative contract refinement
- Knowledge retention (memos)
- Full audit trail

---

## Lệnh Configuration

### `midicoder config get`

Lấy giá trị configuration.

**Cách dùng:**

```bash
midicoder config get <key>
```

**Ví dụ:**

```bash
midicoder config get working_dir
midicoder config get stack
midicoder config get llm.high.model
```

---

### `midicoder config set`

Đặt giá trị configuration.

**Cách dùng:**

```bash
midicoder config set <key> <value>
```

**Ví dụ:**

```bash
midicoder config set working_dir /new/path
midicoder config set stack fastapi,nest
```

---

### `midicoder config list`

Liệt kê tất cả configuration.

**Cách dùng:**

```bash
midicoder config list
```

**Output:** JSON formatted configuration từ `.midicoder/config.json`

---

### `midicoder config validate`

Validate configuration file.

**Cách dùng:**

```bash
midicoder config validate
```

**Kiểm tra:**

- JSON syntax
- Required fields có mặt
- Valid values (stack, LLM providers, etc.)

---

### `midicoder config secrets list`

Liệt kê tất cả secret categories.

**Cách dùng:**

```bash
midicoder config secrets list
```

**Output:** Danh sách secret categories (vd: `llm`)

---

### `midicoder config secrets get`

Lấy secret value cho category và key.

**Cách dùng:**

```bash
midicoder config secrets get <category> <key>
```

**Ví dụ:**

```bash
midicoder config secrets get llm high
```

**Output:** API key (masked cho security)

---

### `midicoder config secrets set`

Đặt secret value cho category và key.

**Cách dùng:**

```bash
midicoder config secrets set <category> <key>
```

**Ví dụ:**

```bash
midicoder config secrets set llm high
# Prompts cho API key (hidden input)
```

---

### `midicoder config secrets delete`

Xóa tất cả secrets cho một category.

**Cách dùng:**

```bash
midicoder config secrets delete <category>
```

**Ví dụ:**

```bash
midicoder config secrets delete llm
```

---

### `midicoder config reset`

Reset configuration về defaults (prompts xác nhận).

**Cách dùng:**

```bash
midicoder config reset
```

**Cảnh báo:** Sẽ xóa `config.json` và `secrets.json`. Bạn cần chạy `midicoder init` lại.

---

## Lệnh Brief (Nâng cao)

### `midicoder brief analyze`

Phân tích master brief cho contract generation planning.

**Cách dùng:**

```bash
midicoder brief analyze
```

**Quy trình:**

- Dùng LLM để phân tích `master-brief.md`
- Xác định required contract files
- Trích xuất keywords và structure

**Output:** Analysis results trong `.midicoder/versions/<version>/cache/`

**Use case:** Preview contracts nào sẽ được sinh trước khi chạy `contract gen`.

---

### `midicoder brief rewrite`

Viết lại master brief dựa trên analysis.

**Cách dùng:**

```bash
midicoder brief rewrite
```

**Quy trình:**

- Phân tích `master-brief.md` hiện tại
- Tổ chức lại content để align tốt hơn với DSL schema
- Đề xuất improvements

**Cảnh báo:** Đây là tính năng thử nghiệm. Luôn backup `master-brief.md` trước khi chạy.

---

## Cheat Sheet Lệnh

### Full Pipeline (Lần đầu)

```bash
# 1. Khởi tạo workspace
midicoder init

# 2. Index project
midicoder index

# 3. Tạo version
midicoder version create v0.1.0

# 4. Chỉnh sửa master-brief.md (user action)
vim .midicoder/versions/v0.1.0/master-brief.md

# 5. Sinh contracts
midicoder contract gen

# 6. Build IR
midicoder ir build

# 7. Build code plans
midicoder code build

# 8. Sinh patch plans
midicoder code gen

# 9. Áp dụng patches
midicoder code apply --dry-run  # Preview trước
midicoder code apply            # Thực sự áp dụng
```

### Contract Iteration

```bash
# Check contracts
midicoder contract check

# Tạo feedback file
midicoder contract feedback

# Chỉnh sửa feedback (user action)
vim .midicoder/versions/v0.1.0/contract-feedbacks.yml

# Validate feedback
midicoder contract repair prepare

# Áp dụng repairs
midicoder contract repair run

# Rebuild IR và tiếp tục
midicoder ir build
midicoder code build
midicoder code gen
midicoder code apply
```

### Resume Failed Generation

```bash
# Nếu contract gen thất bại giữa chừng
midicoder contract gen resume

# Tiếp tục pipeline
midicoder ir build
midicoder code build
midicoder code gen
midicoder code apply
```

### CI/CD Automation

```bash
# Non-interactive init
export MIDICODER_WORKING_DIR=/app
export MIDICODER_STACK=fastapi
export MIDICODER_LLM_HIGH_PROVIDER=anthropic
export MIDICODER_LLM_HIGH_API_KEY=$ANTHROPIC_KEY
midicoder init --non-interactive

# Chạy full pipeline
midicoder index
midicoder version create $CI_COMMIT_TAG
# Copy master-brief từ repo
cp docs/requirements.md .midicoder/versions/$CI_COMMIT_TAG/master-brief.md
midicoder contract gen
midicoder ir build --skip-diagrams
midicoder code build
midicoder code gen
midicoder code apply --force  # Dùng cẩn thận trong CI
```

---

## Exit Codes

Tất cả commands trả về standard exit codes:

- **0**: Success
- **1**: General error (validation failed, missing files, etc.)
- **Non-zero**: Command-specific error

**Ví dụ sử dụng trong scripts:**

```bash
#!/bin/bash
set -e  # Exit on any error

midicoder contract gen || {
    echo "Contract generation failed"
    exit 1
}

midicoder ir build || {
    echo "IR build failed, check contracts"
    exit 1
}
```

---

## Workflows Thông dụng

### Phát triển Feature Mới

```bash
# 1. Bắt đầu mới
midicoder version create feature-user-auth

# 2. Viết requirements
vim .midicoder/versions/feature-user-auth/master-brief.md

# 3. Sinh và áp dụng
midicoder contract gen
midicoder ir build
midicoder code build
midicoder code gen
midicoder code apply --dry-run
midicoder code apply
```

### Tinh chỉnh Contracts

```bash
# 1. Kiểm tra issues
midicoder contract check

# 2. Tạo feedback
midicoder contract feedback

# 3. Thêm custom feedback
vim .midicoder/versions/<version>/contract-feedbacks.yml

# 4. Áp dụng repairs
midicoder contract repair prepare
midicoder contract repair run

# 5. Regenerate downstream artifacts
midicoder ir build
midicoder code build
midicoder code gen
```

### Cập nhật Code Hiện có

```bash
# 1. Reindex sau manual changes
midicoder index reindex --path src/users/service.py

# 2. Regenerate patches với fresh context
midicoder code gen

# 3. Preview và apply
midicoder code apply --dry-run
midicoder code apply
```

---

## Lệnh Debugging

### Xem Run Logs

Tất cả commands tạo run directories với detailed logs:

```bash
# Liệt kê recent runs
ls -lt .midicoder/runs/contract_gen/

# Xem summary
cat .midicoder/runs/contract_gen/<timestamp>/summary.json

# Xem LLM prompt (contract gen only)
cat .midicoder/runs/contract_gen/<timestamp>/pass_01_*.json/prompt.txt

# Xem LLM response
cat .midicoder/runs/contract_gen/<timestamp>/pass_01_*.json/response.txt
```

### Kiểm tra State

```bash
# Global state
cat .midicoder/state.json

# Version state
cat .midicoder/versions/<version>/state.json

# Configuration
cat .midicoder/config.json
```

### Validate Artifacts

```bash
# Check contracts
midicoder contract check

# Validate config
midicoder config validate

# Validate feedback (trước repair)
midicoder contract repair prepare
```

---

## Environment Variables

Midi Coder tôn trọng các environment variables này:

### Cho Non-Interactive Init

- `MIDICODER_WORKING_DIR`: Đường dẫn working directory
- `MIDICODER_STACK`: Danh sách stack cách nhau bằng dấu phẩy
- `MIDICODER_LLM_HIGH_PROVIDER`: High-tier LLM provider
- `MIDICODER_LLM_HIGH_MODEL`: High-tier LLM model
- `MIDICODER_LLM_HIGH_URL`: High-tier LLM base URL
- `MIDICODER_LLM_HIGH_API_KEY`: High-tier API key
- `MIDICODER_LLM_CHEAP_PROVIDER`: Cheap-tier LLM provider
- `MIDICODER_LLM_CHEAP_MODEL`: Cheap-tier LLM model
- `MIDICODER_LLM_CHEAP_URL`: Cheap-tier LLM base URL
- `MIDICODER_LLM_CHEAP_API_KEY`: Cheap-tier API key

### Cho Runtime

- `MIDICODER_NON_INTERACTIVE`: Đặt `true` để suppress prompts

**Xem:** [Hướng dẫn Non-Interactive](non-interactive.md) cho chi tiết đầy đủ.

---

## Nhận Trợ giúp

### In-CLI Help

```bash
# General help
midicoder --help

# Command-specific help
midicoder init --help
midicoder contract --help
midicoder code --help
```

### Configuration Keywords

```bash
# Liệt kê tất cả init configuration options
midicoder init --config-list
```

### Tài liệu

- [Tổng quan Pipeline](pipeline.md): Deep dive vào từng bước
- [Cấu hình](config.md): Cấu trúc config file và options
- [Hướng dẫn Non-Interactive](non-interactive.md): Thiết lập automation
- [Artifacts](artifacts.md): Cấu trúc file và formats
- [Troubleshooting](troubleshooting.md): Vấn đề thường gặp và giải pháp
- [FAQ](faq.md): Câu hỏi thường gặp

### Đặc tả Kỹ thuật

- `technic/DSL-schema.md`: Đặc tả DSL
- `technic/IR-compiler.md`: Chi tiết biên dịch IR
- `technic/codegen.md`: Chiến lược sinh code
- `technic/midicoder-algorithm.md`: Thiết kế thuật toán và roadmap

---

## Bước Tiếp theo

- **Lần đầu?** Bắt đầu với [Bắt đầu](getting-started.md)
- **Hiểu pipeline?** Xem [Deep Dive Pipeline](pipeline.md)
- **Thiết lập automation?** Xem [Hướng dẫn Non-Interactive](non-interactive.md)
- **Gặp vấn đề?** Truy cập [Troubleshooting](troubleshooting.md)
