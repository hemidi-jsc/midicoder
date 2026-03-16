# Tham khảo Artifacts

Tham khảo đầy đủ cho tất cả files và directories được tạo bởi Midi Coder.

## Tổng quan

Midi Coder tạo một thư mục `.midicoder/` có cấu trúc trong project root với tất cả artifacts được version và truy vết được.

```
project-root/
├── .midicoder/              # Midi Coder workspace
│   ├── config.json          # Cấu hình
│   ├── secrets.json         # API keys (gitignored)
│   ├── state.json           # Global state
│   ├── context/             # Project Context
│   ├── runs/                # Execution logs
│   └── versions/            # Version workspaces
├── src/                     # Source code của bạn
└── ...
```

---

## Root Level

### `.midicoder/config.json`

**Được tạo bởi:** `midicoder init`

**Mục đích:** Main configuration file.

**Format:** JSON

**Ví dụ:**

```json
{
  "working_dir": "/absolute/path/to/project",
  "stack": ["fastapi", "nest"],
  "commands": [],
  "llm": {
    "high": {
      "provider": "anthropic",
      "model": "claude-sonnet-4-5",
      "base_url": "https://api.anthropic.com"
    },
    "cheap": {
      "provider": "anthropic",
      "model": "claude-3-5-haiku",
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

**Các trường chính:**

- `working_dir`: Absolute path đến project root (cho indexing và patching)
- `stack`: Mảng target stacks (`fastapi`, `nest`, `angular`)
- `llm.high`: High-tier LLM cho complex tasks (contract gen, patch strategy)
- `llm.cheap`: Cheap-tier LLM cho simple tasks (stack translation)
- `cache`: Cấu hình LLM response caching
- `snapshot_whitelist`: Optional glob patterns cho selective snapshots

**Xem:** [Hướng dẫn Cấu hình](config.md)

---

### `.midicoder/secrets.json`

**Được tạo bởi:** `midicoder init`

**Mục đích:** Lưu API keys và dữ liệu nhạy cảm.

**Format:** JSON

**Bảo mật:** File này được gitignored. Không bao giờ commit vào version control.

**Ví dụ:**

```json
{
  "llm": {
    "high": {
      "api_key": "sk-ant-..."
    },
    "cheap": {
      "api_key": "sk-ant-..."
    }
  }
}
```

**Quản lý:**

```bash
# Xem secrets (masked)
midicoder config secrets list

# Cập nhật secret
midicoder config secrets set llm high
```

---

### `.midicoder/state.json`

**Được tạo bởi:** `midicoder init`

**Được cập nhật bởi:** Hầu hết commands

**Mục đích:** Track global pipeline state.

**Format:** JSON

**Ví dụ:**

```json
{
  "current_version": "v0.1.0",
  "contracts_locked": false,
  "last_index": "2025-02-10T10:30:00Z"
}
```

**Các trường chính:**

- `current_version`: Active version (set bởi `version create`)
- `contracts_locked`: Liệu contracts có thể được modify
- `last_index`: Timestamp của indexing cuối cùng

---

## Context Directory

### `.midicoder/context/`

**Được tạo bởi:** `midicoder index`

**Được cập nhật bởi:** `midicoder index reindex`

**Mục đích:** Lưu Project Context cho LLM và code generation.

**Cấu trúc:**

```
.midicoder/context/
├── manifest.json        # Scan metadata
├── profile.json         # Stack detection, conventions
├── symbols.json         # Classes, functions, methods
├── entrypoints.json     # Application entry points
├── seams.json           # Integration boundaries
├── exemplars.json       # Code examples
└── memos/               # Design decisions (từ contract repair)
    └── *.md
```

---

### `manifest.json`

**Format:** JSON

**Mục đích:** Metadata về indexing run.

**Ví dụ:**

```json
{
  "root": "/path/to/project",
  "stack": ["fastapi"],
  "version": "0.1.0",
  "timestamp": "2025-02-10T10:30:00Z",
  "ignored_patterns": ["*.pyc", "__pycache__", "node_modules"],
  "files_scanned": 42,
  "symbols_found": 156
}
```

---

### `profile.json`

**Format:** JSON

**Mục đích:** Tech stack và coding conventions được phát hiện.

**Ví dụ:**

```json
{
  "stack": "fastapi",
  "language": "python",
  "framework_version": "0.109.0",
  "conventions": {
    "routing": "decorator-based",
    "dependency_injection": "fastapi-depends",
    "error_handling": "exception-handler",
    "folder_structure": "domain-driven",
    "naming": {
      "routes": "snake_case",
      "classes": "PascalCase",
      "functions": "snake_case"
    }
  },
  "patterns": {
    "repository_pattern": true,
    "service_layer": true,
    "dto_models": true
  }
}
```

---

### `symbols.json`

**Format:** JSON

**Mục đích:** Catalog của tất cả classes, functions, methods trong codebase.

**Ví dụ:**

```json
{
  "classes": [
    {
      "name": "UserService",
      "file": "src/users/service.py",
      "line": 15,
      "methods": ["create_user", "get_user", "delete_user"]
    }
  ],
  "functions": [
    {
      "name": "get_current_user",
      "file": "src/auth/deps.py",
      "line": 8,
      "signature": "async def get_current_user(token: str) -> User"
    }
  ]
}
```

---

### `entrypoints.json`

**Format:** JSON

**Mục đích:** Main entry points của application.

**Ví dụ:**

```json
{
  "entrypoints": [
    {
      "type": "fastapi_app",
      "file": "src/main.py",
      "line": 10,
      "variable": "app"
    },
    {
      "type": "cli",
      "file": "src/cli.py",
      "line": 5,
      "function": "main"
    }
  ]
}
```

---

### `seams.json`

**Format:** JSON

**Mục đích:** Safe integration boundaries cho patching.

**Ví dụ:**

```json
{
  "seams": [
    {
      "type": "router_group",
      "file": "src/api/users/router.py",
      "anchor": "# midicoder:api:users:router:routes",
      "line": 20,
      "description": "User routes registration point"
    },
    {
      "type": "service_methods",
      "file": "src/api/users/service.py",
      "anchor": "# midicoder:api:users:service:handlers",
      "line": 35,
      "description": "User service handlers"
    }
  ]
}
```

**Loại Seams:**

- `router_group`: Route registration points
- `service_methods`: Service layer methods
- `repository_methods`: Data access methods
- `dto_models`: DTO/Schema definitions
- `dependencies`: Dependency injection providers

---

### `exemplars.json`

**Format:** JSON

**Mục đích:** Code snippets mẫu cho LLM reference.

**Ví dụ:**

```json
{
  "exemplars": [
    {
      "type": "route_handler",
      "file": "src/api/users/router.py",
      "snippet": "@router.post('/users', response_model=UserResponse)\nasync def create_user(\n    data: CreateUserRequest,\n    service: UserService = Depends(get_user_service),\n) -> UserResponse:\n    user = await service.create_user(data)\n    return UserResponse.from_orm(user)"
    },
    {
      "type": "service_method",
      "file": "src/api/users/service.py",
      "snippet": "async def create_user(self, data: CreateUserRequest) -> User:\n    if await self.repo.find_by_email(data.email):\n        raise ConflictError('Email already exists')\n    user = User(**data.dict())\n    await self.repo.save(user)\n    return user"
    }
  ]
}
```

---

### `memos/`

**Được tạo bởi:** `midicoder contract repair run`

**Mục đích:** Lưu design decisions và constraints từ contract repair process.

**Format:** Markdown files

**Ví dụ:** `memos/rbac-guidelines.md`

```markdown
# RBAC Guidelines

Từ contract repair feedback FB-003:

- Luôn dùng permission `create_*` cho creation commands
- Luôn dùng permission `read_*` cho queries
- Admin role có tất cả permissions theo mặc định
- Đặt tên permission: `<verb>_<entity>` (snake_case)
```

**Cách dùng:** Các memos này được include trong future `contract gen` và `code gen` prompts như additional context.

---

## Runs Directory

### `.midicoder/runs/`

**Mục đích:** Lưu execution logs cho tất cả commands.

**Cấu trúc:**

```
.midicoder/runs/
├── init/
├── index/
├── contract_gen/
│   └── <timestamp>/
│       ├── summary.json
│       ├── pass_01_info.yaml.json/
│       │   ├── prompt.txt
│       │   ├── response.txt
│       │   ├── processed.yaml
│       │   └── trace.json
│       └── pass_02_entities.yaml.json/
├── ir_build/
├── code_build/
├── code_gen/
└── code_apply/
```

---

### Run Summary Format

**File:** `summary.json`

**Mục đích:** High-level results của command execution.

**Ví dụ (contract_gen):**

```json
{
  "version": "v0.1.0",
  "status": "generated",
  "task": "contract_gen",
  "created_files": [
    "contracts/meta/info.yaml",
    "contracts/domain/entities.yaml",
    "contracts/app/commands.yaml"
  ],
  "llm_config": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-5"
  },
  "target_stack": ["fastapi"],
  "total_passes": 3,
  "timestamp": "2025-02-10T11:00:00Z",
  "duration_seconds": 125.3
}
```

---

### Contract Gen Traces

**Mục đích:** Detailed LLM interaction logs cho debugging.

**Cấu trúc:**

```
pass_01_info.yaml.json/
├── prompt.txt           # Exact prompt gửi đến LLM
├── response.txt         # Raw LLM response
├── processed.yaml       # Cleaned YAML output
└── trace.json           # Metadata (tokens, duration, context)
```

**`trace.json` Ví dụ:**

```json
{
  "pass_number": 1,
  "target_file": "contracts/meta/info.yaml",
  "context_stats": {
    "master_brief_length": 1250,
    "schema_length": 450,
    "exemplars_count": 3,
    "total_context_tokens": 2100
  },
  "llm_stats": {
    "prompt_tokens": 2150,
    "completion_tokens": 380,
    "total_tokens": 2530,
    "duration_seconds": 8.5
  },
  "validation": {
    "yaml_valid": true,
    "schema_valid": true
  }
}
```

---

## Versions Directory

### `.midicoder/versions/<version>/`

**Được tạo bởi:** `midicoder version create`

**Mục đích:** Isolated workspace cho mỗi version/feature.

**Cấu trúc:**

```
.midicoder/versions/v0.1.0/
├── state.json           # Version metadata
├── master-brief.md      # Requirements (do user viết)
├── contract-feedbacks.yml  # Contract review feedback (tùy chọn)
├── locks/               # Lock files
├── cache/               # LLM cache (ephemeral)
├── contracts/           # DSL contracts
├── irs/                 # Intermediate representation
├── plans/               # Code plans (pseudo code)
├── patches/             # Patch plans và operations
└── snapshots/           # Backups trước apply
```

---

### `state.json` (Version-level)

**Mục đích:** Version-specific metadata.

**Ví dụ:**

```json
{
  "version": "v0.1.0",
  "created_at": "2025-02-10T09:00:00Z",
  "contracts_generated": true,
  "ir_built": true,
  "code_generated": true,
  "last_applied": "2025-02-10T12:00:00Z"
}
```

---

### `master-brief.md`

**Được tạo bởi:** `midicoder version create` (template)

**Được chỉnh sửa bởi:** User

**Mục đích:** Natural language requirements drive contract generation.

**Format:** Markdown với structured sections

**Template Sections:**

1. Tổng quan
2. Domain & Data
3. Business Flows & Scenarios
4. Commands & Queries
5. Rules & Policy
6. Workflow / State Machine
7. API
8. Non-functional Requirements
9. Technical Constraints
10. Phụ lục

**Xem:** Template được sinh bởi `version create` cho cấu trúc chi tiết.

---

### `contract-feedbacks.yml`

**Được tạo bởi:** `midicoder contract feedback`

**Được chỉnh sửa bởi:** User

**Mục đích:** Contract review notes và repair instructions.

**Format:** YAML

**Ví dụ:**

```yaml
meta:
  version: "v0.1.0"
  author: "dev@team"
  created_at: "2025-02-10T10:15:00Z"
  scope: "contracts"

items:
  - id: FB-001
    file: contracts/app/commands.yaml
    location: "commands[id=CreateOrder]"
    status: pending
    issue: |
      CreateOrder thiếu authorization guard.
    suggestion: |
      Thêm guard với permission = "create_order"
    last_error: null

notes:
  - "Follow RBAC guidelines"
  - "Dùng ISO 8601 cho timestamps"
```

---

### `contracts/`

**Được tạo bởi:** `midicoder contract gen`

**Mục đích:** Structured DSL contracts (YAML).

**Cấu trúc:**

```
contracts/
├── meta/
│   └── info.yaml                    # Version metadata
├── glossary.yaml                    # Domain terminology
├── domain/
│   ├── entities.yaml                # Domain entities
│   ├── value_objects.yaml           # Value objects
│   ├── errors.yaml                  # Errors
│   └── events.yaml                  # Domain events
├── app/
│   ├── commands.yaml                # CQRS commands
│   └── queries.yaml                 # CQRS queries
├── rules/
│   └── *.yaml                       # Business rules
├── workflows/
│   └── *.yaml                       # State machines
├── policy/
│   ├── rbac.yaml                    # Roles & permissions
│   └── permissions_map.yaml         # Permission assignments
├── persistence/
│   └── model.yaml                   # Database schema
├── api/
│   └── http.yaml                    # HTTP routes
└── scenarios/
    └── *.yaml                       # Test scenarios
```

**Xem:** `technic/DSL-schema.md` cho đặc tả contract schema đầy đủ.

---

### `irs/`

**Được tạo bởi:** `midicoder ir build`

**Mục đích:** Normalized intermediate representation.

**Cấu trúc:**

```
irs/
├── ir.json              # Complete IR (tất cả modules)
├── manifest.json        # Metadata, stats, unresolved refs
└── diagrams/            # Mermaid diagrams (tùy chọn)
    ├── api/
    ├── commands/
    ├── entities/
    ├── workflows/
    └── manifest.json
```

**Xem:** `technic/IR-compiler.md` cho chi tiết IR schema.

---

### `plans/`

**Được tạo bởi:** `midicoder code build`

**Mục đích:** Pseudo code plans (FastAPI flavor).

**Cấu trúc:**

```
plans/
├── index.json           # Plan registry
├── commands/
│   ├── create-user.code-plan.json
│   └── update-user.code-plan.json
├── workflows/
│   └── order-workflow.code-plan.json
└── api/
    └── post-users.code-plan.json
```

---

### `patches/`

**Được tạo bởi:** `midicoder code gen` và `midicoder code apply`

**Mục đích:** Patch plans và applied operations.

**Cấu trúc:**

```
patches/
├── plans/               # Patch plans (từ code gen)
│   ├── index.json
│   ├── commands/
│   │   └── create-user.patch-plan.json
│   └── workflows/
│       └── order-workflow.patch-plan.json
├── runtime/             # Runtime files (tùy chọn, với --runtime)
│   └── app/
└── <run_id>/            # Applied operations (từ code apply)
    ├── ops.json
    └── *.patch
```

---

### `snapshots/`

**Được tạo bởi:** `midicoder code apply`

**Mục đích:** Backup files trước khi applying patches.

**Cấu trúc:**

```
snapshots/
└── <run_id>/
    ├── app/
    │   └── api/
    │       └── users/
    │           ├── router.py
    │           └── service.py
    └── manifest.json
```

**Cách dùng:** Restore files nếu patches gây ra issues.

---

## File Naming Conventions

### Timestamps

Format: `YYYYMMDD_HHMMSS`

Ví dụ: `20250210_120000` (Feb 10, 2025, 12:00:00)

### Slugs (cho plans/patches)

Format: `kebab-case`

Ví dụ:
- `create-user` (từ Command:CreateUser)
- `order-workflow` (từ Workflow:OrderWorkflow)
- `post-users` (từ HttpRoute:POST /users)

### Trace Files (contract gen)

Format: `pass_<number>_<target_file>.json`

Ví dụ:
- `pass_01_info.yaml.json`
- `pass_02_entities.yaml.json`
- `pass_03_commands.yaml.json`

---

## Gitignore Recommendations

Thêm vào `.gitignore`:

```gitignore
# Midi Coder secrets và cache
.midicoder/secrets.json
.midicoder/versions/*/cache/

# Midi Coder runs (tùy chọn, hữu ích cho debugging)
# .midicoder/runs/

# Midi Coder snapshots (tùy chọn, temporary backups)
# .midicoder/snapshots/
```

**Khuyến nghị commit:**

- `.midicoder/config.json` (không có secrets)
- `.midicoder/versions/*/contracts/` (DSL contracts)
- `.midicoder/versions/*/master-brief.md` (requirements)
- `.midicoder/versions/*/contract-feedbacks.yml` (review notes)

**Tùy chọn commit:**

- `.midicoder/context/` (có thể regenerate với `midicoder index`)
- `.midicoder/runs/` (hữu ích cho audit trail)
- `.midicoder/versions/*/irs/` (có thể regenerate với `ir build`)
- `.midicoder/versions/*/plans/` (có thể regenerate với `code build`)
- `.midicoder/versions/*/patches/` (có thể regenerate với `code gen`)

---

## Artifact Lifecycle

### Ephemeral (Có thể Regenerate)

Những artifacts này có thể xóa an toàn và regenerate:

- `.midicoder/context/*` → Regenerate với `midicoder index`
- `.midicoder/versions/*/cache/*` → Regenerate tự động
- `.midicoder/versions/*/irs/*` → Regenerate với `midicoder ir build`
- `.midicoder/versions/*/plans/*` → Regenerate với `midicoder code build`
- `.midicoder/versions/*/patches/*` → Regenerate với `midicoder code gen`

### Persistent (Giữ lại)

Những artifacts này nên được bảo toàn:

- `.midicoder/config.json` → Cấu hình
- `.midicoder/versions/*/master-brief.md` → Requirements (do user viết)
- `.midicoder/versions/*/contracts/*` → Contracts (LLM-generated, đắt)
- `.midicoder/versions/*/contract-feedbacks.yml` → Review notes (do user viết)

### Sensitive (Không bao giờ Commit)

- `.midicoder/secrets.json` → API keys

### Audit Trail (Tùy chọn)

- `.midicoder/runs/*` → Execution logs (hữu ích cho debugging)
- `.midicoder/versions/*/snapshots/*` → Backups (temporary)

---

## Quản lý Disk Space

### Kích thước Thông thường

- `.midicoder/config.json`: ~1 KB
- `.midicoder/secrets.json`: ~1 KB
- `.midicoder/context/`: 100 KB - 5 MB (tùy project size)
- `.midicoder/runs/`: 10 KB - 100 MB (tùy run count)
- `.midicoder/versions/<version>/contracts/`: 10 KB - 500 KB
- `.midicoder/versions/<version>/irs/`: 50 KB - 2 MB
- `.midicoder/versions/<version>/plans/`: 100 KB - 5 MB
- `.midicoder/versions/<version>/patches/`: 100 KB - 10 MB
- `.midicoder/versions/<version>/snapshots/`: Varies (copy của modified files)

### Cleanup Recommendations

```bash
# Dọn old runs (giữ 10 mới nhất)
ls -t .midicoder/runs/contract_gen/ | tail -n +11 | xargs rm -rf

# Dọn snapshots sau successful apply
rm -rf .midicoder/versions/*/snapshots/

# Dọn cache
rm -rf .midicoder/versions/*/cache/

# Dọn runtime files (nếu dùng --runtime)
rm -rf .midicoder/versions/*/patches/runtime/
```

---

## Artifact Validation

### Kiểm tra Integrity

```bash
# Validate config
midicoder config validate

# Check contracts
midicoder contract check

# Validate feedback
midicoder contract repair prepare
```

### Regenerate Corrupted Files

```bash
# Regenerate context
midicoder index

# Regenerate IR
midicoder ir build

# Regenerate plans
midicoder code build

# Regenerate patches
midicoder code gen
```

---

## Cross-References

**Tài liệu liên quan:**

- [Tổng quan Pipeline](pipeline.md): Cách artifacts flow qua pipeline
- [Lệnh CLI](cli.md): Commands tạo/modify artifacts
- [Cấu hình](config.md): Chi tiết config file
- [Troubleshooting](troubleshooting.md): Vấn đề artifacts thường gặp

**Đặc tả kỹ thuật:**

- `technic/DSL-schema.md`: Contract file schemas
- `technic/IR-compiler.md`: IR JSON schema
- `technic/source-indexing.md`: Chi tiết trích xuất context
- `technic/codegen.md`: Plan và patch formats

---

## Tóm tắt

Midi Coder tạo một artifact tree toàn diện:

### Core Configuration
- `config.json`: Cài đặt chính
- `secrets.json`: API keys (gitignored)
- `state.json`: Pipeline state

### Project Context
- `context/`: Cấu trúc codebase indexed
  - Stack detection, symbols, seams, exemplars

### Execution Logs
- `runs/`: Detailed logs per command
  - Traces cho LLM interactions
  - Summaries và metadata

### Version Workspaces
- `versions/<version>/`:
  - `master-brief.md`: Requirements (user input)
  - `contracts/`: DSL YAML (LLM output)
  - `irs/`: Normalized IR JSON (quyết định)
  - `plans/`: Pseudo code (quyết định)
  - `patches/`: Real patches (hỗ trợ LLM)
  - `snapshots/`: Backups trước apply

**Nguyên tắc Chính:**

- Mọi bước tạo auditable artifacts
- Separation of concerns rõ ràng
- Deterministic artifacts vs LLM artifacts
- Version isolation cho parallel development
- Cấu trúc Git-friendly (`.gitignore` sensitive files)

**Bước Tiếp theo:**

- Xem [Pipeline](pipeline.md) cho cách artifacts flow
- Xem [Lệnh CLI](cli.md) cho commands tạo artifacts
- Xem [Cấu hình](config.md) cho chi tiết config file
