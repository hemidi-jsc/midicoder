# Bắt đầu với Midi Coder

Chào mừng đến với Midi Coder! Hướng dẫn này giúp bạn bắt đầu với sinh code quyết định, dựa trên contract.

## Midi Coder là gì?

Midi Coder là một **pipeline quyết định** biến đổi yêu cầu thành code thông qua các contracts có cấu trúc:

```
Yêu cầu của bạn → DSL Contracts → IR → Code Plans → Patches → Working Code
```

**Lợi ích chính:**

- **Contract-first**: Yêu cầu dưới dạng YAML có cấu trúc (single source of truth)
- **Quyết định**: Kết quả lặp lại được, không có hành vi LLM ngẫu nhiên
- **Dựa trên patch**: Thay đổi nhỏ, dễ review (không ghi đè toàn bộ file)
- **Có thể kiểm tra**: Mọi bước tạo artifacts truy vết được
- **Đa stack**: Hỗ trợ FastAPI, NestJS, Angular từ cùng contract

---

## Yêu cầu Hệ thống

- **Python** 3.9 hoặc mới hơn
- **pip** (Python package manager)
- **virtualenv** hoặc `venv` (khuyến nghị)
- **Git** (cho version control)

**Hệ điều hành:**

- Linux (tested trên Ubuntu 20.04+)
- macOS (tested trên 11.0+)
- Windows (tested trên Windows 10+)

---

## Cài đặt

### Bước 1: Tạo Virtual Environment

```bash
# Tạo virtual environment
python -m venv .venv

# Kích hoạt (Linux/macOS)
source .venv/bin/activate

# Kích hoạt (Windows)
.venv\Scripts\activate
```

### Bước 2: Cài đặt Midi Coder

```bash
# Nâng cấp pip
pip install -U pip

# Cài đặt Midi Coder ở development mode
pip install -e .
```

### Bước 3: Xác minh Cài đặt

```bash
# Kiểm tra version
midicoder --help

# Sẽ hiển thị các commands có sẵn
```

---

## Bắt đầu Nhanh (5 Phút)

### 1. Khởi tạo Workspace

```bash
cd /path/to/your/project
midicoder init
```

Interactive wizard sẽ hỏi:

- **Working directory**: Đường dẫn đến project của bạn (mặc định: thư mục hiện tại)
- **Tech stack**: Chọn một hoặc nhiều (FastAPI, NestJS, Angular)
- **High-tier LLM**: Cho complex tasks (contract generation, patch planning)
  - Provider: Anthropic hoặc OpenAI
  - Model: vd, `claude-sonnet-4-5` hoặc `gpt-4`
  - API Key: API key của bạn
- **Cheap-tier LLM**: Cho simple tasks (stack translation)
  - Provider: Anthropic hoặc OpenAI
  - Model: vd, `claude-3-5-haiku` hoặc `gpt-3.5-turbo`
  - API Key: API key của bạn

**Kết quả:** Tạo `.midicoder/` với `config.json` và `secrets.json`

### 2. Index Dự án của bạn

```bash
midicoder index
```

Quét codebase và tạo **Project Context**:

- Phát hiện tech stack của bạn
- Tìm classes, functions, methods
- Xác định safe injection points (seams)
- Trích xuất code examples (exemplars)

**Kết quả:** Tạo `.midicoder/context/` với symbols, entrypoints, seams, etc.

**Thời gian:** Thường 10-60 giây tùy kích thước project.

### 3. Tạo Version

```bash
midicoder version create v0.1.0
```

Tạo workspace cho version này:

- Version directory: `.midicoder/versions/v0.1.0/`
- Template: `master-brief.md` (chỉnh sửa tiếp theo!)

### 4. Viết Yêu cầu

Chỉnh sửa `.midicoder/versions/v0.1.0/master-brief.md`:

```bash
vim .midicoder/versions/v0.1.0/master-brief.md
# hoặc dùng editor yêu thích
```

**Các sections trong template:**

1. **Tổng quan**: Mục tiêu, phạm vi, glossary
2. **Domain & Data**: Entities, value objects, errors
3. **Business Flows**: User journeys, scenarios
4. **Commands & Queries**: CQRS operations
5. **Rules & Policy**: Business rules, RBAC
6. **Workflow**: State machines
7. **API**: HTTP routes, GraphQL
8. **Non-functional**: Performance, security
9. **Technical Constraints**: Stack conventions

**Ví dụ (tối thiểu):**

```markdown
# Master Brief: Quản lý User

## 1. Tổng quan

CRUD user đơn giản với authentication.

## 2. Domain & Data

**Entities:**
- User: id, email, name, role, created_at

**Errors:**
- UserNotFound: Khi user ID không tồn tại
- EmailAlreadyExists: Khi email trùng

## 4. Commands & Queries

**Commands:**
- CreateUser: email, name, role → User
  - Validates email format
  - Kiểm tra trùng lặp
  - Tạo user với hashed password
  - Phát UserCreated event

**Queries:**
- GetUser: user_id → User
- ListUsers: filters → User[]

## 5. Rules & Policy

**RBAC:**
- Roles: admin, user
- Permissions:
  - create_user (chỉ admin)
  - read_user (tất cả authenticated)
  - update_user (admin hoặc chính user)
  - delete_user (chỉ admin)

## 7. API

**Routes:**
- POST /users (CreateUser) - admin
- GET /users/:id (GetUser) - authenticated
- GET /users (ListUsers) - authenticated
- PUT /users/:id (UpdateUser) - admin hoặc chính user
- DELETE /users/:id (DeleteUser) - admin
```

### 5. Sinh Contracts

```bash
midicoder contract gen
```

LLM đọc `master-brief.md` của bạn và sinh structured contracts:

- `contracts/domain/entities.yaml`
- `contracts/domain/errors.yaml`
- `contracts/app/commands.yaml`
- `contracts/app/queries.yaml`
- `contracts/policy/rbac.yaml`
- `contracts/api/http.yaml`

**Thời gian:** 1-3 phút tùy độ phức tạp.

**Nếu thất bại:** Chạy `midicoder contract gen resume` để retry chỉ các files thất bại.

### 6. Build IR (Intermediate Representation)

```bash
midicoder ir build
```

Biên dịch contracts thành IR JSON normalized:

- Validates tất cả contracts (schema, cross-refs)
- Normalizes IDs và references
- Sinh Mermaid diagrams (tùy chọn)

**Thời gian:** 5-15 giây.

**Kết quả:** `.midicoder/versions/v0.1.0/irs/ir.json`

### 7. Build Code Plans

```bash
midicoder code build
```

Sinh pseudo code plans (FastAPI flavor):

- Quyết định (không LLM)
- Tổ chức folder-level
- Dùng anchors cho injection points

**Thời gian:** 2-10 giây.

**Kết quả:** `.midicoder/versions/v0.1.0/plans/`

### 8. Sinh Patch Plans

```bash
midicoder code gen
```

Chuyển đổi pseudo code thành real patches:

- **Bước 1 (high-tier LLM)**: Quyết định ĐÂU và NHƯ THẾ NÀO patch
- **Bước 2 (cheap-tier LLM)**: Chuyển đổi sang target stack (nếu không phải FastAPI)

**Thời gian:** 1-3 phút tùy độ phức tạp.

**Kết quả:** `.midicoder/versions/v0.1.0/patches/plans/`

### 9. Xem trước Thay đổi

```bash
midicoder code apply --dry-run
```

Hiển thị những gì sẽ được thay đổi mà không thực sự modify files.

Review output để đảm bảo patches đúng.

### 10. Áp dụng Thay đổi

```bash
midicoder code apply
```

Áp dụng patches vào working directory của bạn:

- Tạo snapshots (backups)
- Áp dụng write/edit/delete operations
- Record operations trong `ops.json`
- Sinh unified diffs
- Reindex changed files

**Thời gian:** 5-20 giây.

**Kết quả:** Code của bạn đã được cập nhật! ✨

---

## Điều gì vừa xảy ra?

Hãy trace những gì Midi Coder đã làm:

1. **Init**: Thiết lập workspace, lưu config và API keys
2. **Index**: Quét codebase, trích xuất cấu trúc
3. **Version**: Tạo isolated workspace cho v0.1.0
4. **Công việc của bạn**: Viết yêu cầu trong `master-brief.md`
5. **Contract Gen**: LLM sinh structured DSL contracts
6. **IR Build**: Biên dịch contracts thành normalized IR (quyết định)
7. **Code Build**: Sinh pseudo code plans (quyết định)
8. **Code Gen**: LLM sinh real patches với locations
9. **Code Apply**: Áp dụng patches an toàn vào code

**Điểm chính:**

- LLM chỉ dùng ở bước 5 và 8
- Bước 6 và 7 là 100% quyết định
- Mọi bước tạo auditable artifacts
- Thay đổi dựa trên patch (không ghi đè file)

---

## Kiểm tra Artifacts

### Cấu hình

```bash
# Xem config
cat .midicoder/config.json

# Xem state
cat .midicoder/state.json

# Xem secrets (API keys)
cat .midicoder/secrets.json
```

### Project Context

```bash
# Xem detected stack và conventions
cat .midicoder/context/profile.json

# Xem symbols (classes, functions)
cat .midicoder/context/symbols.json

# Xem safe injection points
cat .midicoder/context/seams.json

# Xem code examples
cat .midicoder/context/exemplars.json
```

### Contracts (DSL)

```bash
# Xem entities
cat .midicoder/versions/v0.1.0/contracts/domain/entities.yaml

# Xem commands
cat .midicoder/versions/v0.1.0/contracts/app/commands.yaml

# Xem API routes
cat .midicoder/versions/v0.1.0/contracts/api/http.yaml
```

### IR (Intermediate Representation)

```bash
# Xem normalized IR
cat .midicoder/versions/v0.1.0/irs/ir.json

# Xem metadata
cat .midicoder/versions/v0.1.0/irs/manifest.json

# Xem diagrams (nếu sinh)
ls .midicoder/versions/v0.1.0/irs/diagrams/
```

### Code Plans

```bash
# Xem plan registry
cat .midicoder/versions/v0.1.0/plans/index.json

# Xem một command plan
cat .midicoder/versions/v0.1.0/plans/commands/create-user.code-plan.json
```

### Patch Plans

```bash
# Xem patch registry
cat .midicoder/versions/v0.1.0/patches/plans/index.json

# Xem một patch plan
cat .midicoder/versions/v0.1.0/patches/plans/commands/create-user.patch-plan.json
```

### Applied Operations

```bash
# Tìm latest apply run
ls -lt .midicoder/versions/v0.1.0/patches/

# Xem operations
cat .midicoder/versions/v0.1.0/patches/<run_id>/ops.json

# Xem unified diff
cat .midicoder/versions/v0.1.0/patches/<run_id>/*.patch
```

---

## Bước Tiếp theo

### Lặp lại Contracts

Nếu cần tinh chỉnh contracts:

```bash
# 1. Kiểm tra issues
midicoder contract check

# 2. Tạo feedback file
midicoder contract feedback

# 3. Chỉnh sửa feedback
vim .midicoder/versions/v0.1.0/contract-feedbacks.yml

# 4. Validate feedback
midicoder contract repair prepare

# 5. Áp dụng repairs
midicoder contract repair run

# 6. Rebuild downstream
midicoder ir build
midicoder code build
midicoder code gen
midicoder code apply --dry-run
midicoder code apply
```

### Làm việc với Nhiều Versions

```bash
# Tạo version mới
midicoder version create v0.2.0

# Chỉnh sửa master-brief.md cho v0.2.0
vim .midicoder/versions/v0.2.0/master-brief.md

# Chạy pipeline cho v0.2.0
midicoder contract gen
# ... (tiếp tục pipeline)
```

### Incremental Reindexing

Sau thay đổi code manual:

```bash
# Reindex files cụ thể
midicoder index reindex --path src/users/service.py src/auth/controller.py

# Regenerate patches với fresh context
midicoder code gen
midicoder code apply --dry-run
midicoder code apply
```

---

## Tích hợp CI/CD

Cho automation, dùng chế độ non-interactive:

```bash
# Đặt environment variables
export MIDICODER_WORKING_DIR=/app
export MIDICODER_STACK=fastapi
export MIDICODER_LLM_HIGH_PROVIDER=anthropic
export MIDICODER_LLM_HIGH_MODEL=claude-sonnet-4-5
export MIDICODER_LLM_HIGH_API_KEY=$ANTHROPIC_API_KEY
export MIDICODER_LLM_CHEAP_PROVIDER=anthropic
export MIDICODER_LLM_CHEAP_MODEL=claude-3-5-haiku
export MIDICODER_LLM_CHEAP_API_KEY=$ANTHROPIC_API_KEY

# Khởi tạo non-interactively
midicoder init --non-interactive

# Chạy pipeline
midicoder index
midicoder version create $CI_COMMIT_TAG
cp docs/requirements.md .midicoder/versions/$CI_COMMIT_TAG/master-brief.md
midicoder contract gen
midicoder ir build --skip-diagrams
midicoder code build
midicoder code gen
midicoder code apply --force
```

**Xem:** [Hướng dẫn Non-Interactive](non-interactive.md) cho thiết lập automation đầy đủ.

---

## Vấn đề Thường gặp

### `No current version set`

**Giải pháp:** Chạy `midicoder version create <version>` trước.

### `master-brief.md is missing`

**Giải pháp:** Version không được tạo đúng. Tạo lại hoặc thêm file manually.

### Contract generation thất bại

**Giải pháp:** 
1. Kiểm tra LLM API key hợp lệ
2. Review `master-brief.md` cho rõ ràng
3. Dùng `midicoder contract gen resume` để retry

### IR build thất bại

**Giải pháp:**
1. Chạy `midicoder contract check` để xem issues
2. Sửa contracts hoặc dùng `midicoder contract feedback` + `repair`
3. Retry `midicoder ir build`

### Code apply conflicts

**Giải pháp:**
1. Review với `--dry-run`
2. Manually resolve conflicts
3. Dùng `--force` chỉ khi chắc chắn (có thể gây merge issues)

**Xem:** [Troubleshooting](troubleshooting.md) cho nhiều issues và solutions hơn.

---

## Tài nguyên Học tập

### Tài liệu

- **[Deep Dive Pipeline](pipeline.md)**: Giải thích chi tiết từng bước
- **[Lệnh CLI](cli.md)**: Reference đầy đủ về commands
- **[Cấu hình](config.md)**: Cấu trúc config file và options
- **[Artifacts](artifacts.md)**: Cấu trúc file và formats
- **[Hướng dẫn Non-Interactive](non-interactive.md)**: Thiết lập automation
- **[Troubleshooting](troubleshooting.md)**: Vấn đề thường gặp
- **[FAQ](faq.md)**: Câu hỏi thường gặp

### Đặc tả Kỹ thuật

- **`technic/DSL-schema.md`**: Đặc tả DSL đầy đủ
- **`technic/IR-compiler.md`**: Thuật toán biên dịch IR
- **`technic/codegen.md`**: Chiến lược sinh code
- **`technic/source-indexing.md`**: Trích xuất Project Context
- **`technic/contract-repair.md`**: Workflow feedback & repair
- **`technic/midicoder-algorithm.md`**: Thiết kế thuật toán và roadmap tương lai

### Ví dụ Projects

Xem `midicoder/code/example/` cho:

- Ví dụ IR JSON
- Ví dụ code plans
- Ví dụ patch plans
- Ví dụ contracts

---

## Nhận Trợ giúp

### Command Help

```bash
# General help
midicoder --help

# Command-specific help
midicoder init --help
midicoder contract --help
```

### Configuration Keywords

```bash
# Liệt kê tất cả configuration options có sẵn
midicoder init --config-list
```

### Cộng đồng & Hỗ trợ

- **Issues**: Báo bugs trên GitHub
- **Discussions**: Đặt câu hỏi trong GitHub Discussions
- **Contributing**: Xem [Hướng dẫn Đóng góp](contributing.md)

---

## Best Practices

### Viết master-brief.md

1. **Cụ thể**: "User phải có valid email" không phải "User có email"
2. **Bao gồm error cases**: Lỗi gì có thể xảy ra và khi nào?
3. **Định nghĩa permissions**: Ai có thể làm gì?
4. **Mô tả workflows**: State transitions là gì?
5. **Tham chiếu code hiện có**: Đề cập files/classes nếu mở rộng hệ thống existing

### Contract Iteration

1. Luôn chạy `contract check` trước `ir build`
2. Dùng `contract feedback` + `repair` thay vì regenerate mọi thứ
3. Review contracts trước khi proceed sang code generation
4. Version control contracts cùng với code

### Code Application

1. Luôn dùng `--dry-run` trước để preview changes
2. Review diffs trước khi applying
3. Commit generated code trong commits riêng để dễ review
4. Chạy tests sau khi applying patches

### Project Organization

1. Dùng semantic versioning cho versions (`v1.0.0`, `v1.1.0`)
2. Hoặc dùng feature names (`feature-auth`, `refactor-payments`)
3. Giữ `master-brief.md` cập nhật với implemented features
4. Dùng contract feedback cho ongoing refinements

---

## Tiếp theo là gì?

Bây giờ bạn đã hoàn thành quick start:

1. **Khám phá pipeline**: Đọc [Deep Dive Pipeline](pipeline.md)
2. **Học tất cả commands**: Xem [Lệnh CLI](cli.md)
3. **Thiết lập automation**: Xem [Hướng dẫn Non-Interactive](non-interactive.md)
4. **Hiểu artifacts**: Review [Artifacts](artifacts.md)
5. **Dive vào DSL**: Học `technic/DSL-schema.md`

**Chúc bạn code vui vẻ với Midi Coder!**