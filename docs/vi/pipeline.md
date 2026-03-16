# Deep Dive Pipeline

Trang này mô tả kiến trúc pipeline Midi Coder hoàn chỉnh và cách mỗi bước chuyển đổi artifacts.

## Triết lý

Midi Coder theo phương pháp **quyết định, contract-first**:

- **LLM chỉ là công cụ authoring**: LLMs sinh contracts (YAML) và quyết định patch strategies, nhưng KHÔNG BAO GIỜ viết code trực tiếp
- **Dựa trên patch, không rewrite**: Patches nhỏ, dễ review thay vì ghi đè toàn bộ file
- **Artifacts có thể kiểm tra**: Mọi bước tạo outputs có version, truy vết được trong `.midicoder/`
- **Hỗ trợ đa stack**: Một IR → Nhiều target stacks (FastAPI, NestJS, Angular)

## Tổng quan Pipeline

```
master-brief.md (user input)
    ↓
[contract gen] → contracts/*.yaml (DSL)
    ↓
[ir build] → ir.json (intermediate representation)
    ↓
[code build] → plans/*.code-plan.json (pseudo code, FastAPI)
    ↓
[code gen] → patches/*.patch-plan.json (code thực, target stack)
    ↓
[code apply] → Working directory (patched files)
```

---

## Bước 1: Init - Thiết lập Dự án

**Lệnh:** `midicoder init`

**Mục đích:** Khởi tạo Midi Coder workspace và cấu hình.

**Chế độ:**

- **Interactive**: Wizard hỏi cấu hình
- **Non-Interactive**: Dùng CLI flags hoặc environment variables (cho CI/CD)

Xem [Hướng dẫn Non-Interactive](non-interactive.md) để biết chi tiết automation.

**Outputs:**

```
.midicoder/
├── config.json          # Cấu hình chính
├── secrets.json         # API keys (gitignored)
└── state.json           # Pipeline state tracker
```

**Implementation:** `midicoder/commands/init.py`

---

## Bước 2: Index - Trích xuất Project Context

**Lệnh:** `midicoder index`

**Mục đích:** Quét source code để build **Project Context** cho các bước downstream.

**Quy trình:**

1. **Stack Detection**: Tự động phát hiện tech stack từ codebase
2. **Symbol Extraction**: Parse classes, functions, methods dùng AST/regex
3. **Entrypoint Discovery**: Tìm main entry points (FastAPI app, NestJS bootstrap, Angular main)
4. **Seam Identification**: Phát hiện integration boundaries (điểm injection an toàn)
5. **Exemplar Collection**: Trích xuất code snippets làm style references

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

**Reindexing:**

```bash
# Full reindex
midicoder index

# Incremental reindex (chỉ files thay đổi)
midicoder index reindex --path src/users/controller.py
```

**Implementation:** `midicoder/context/indexer.py`

---

## Bước 3: Version Create - Thiết lập Feature Branch

**Lệnh:** `midicoder version create <version>`

**Mục đích:** Tạo workspace độc lập cho một feature/release version.

**Outputs:**

```
.midicoder/versions/<version>/
├── state.json           # Version metadata
├── master-brief.md      # Yêu cầu người dùng viết (template)
├── contracts/           # DSL contracts
├── irs/                 # Intermediate representation
├── plans/               # Code plans
├── patches/             # Patch plans
└── snapshots/           # Backup trước khi apply
```

**master-brief.md** template theo DSL schema với các sections cho domain, commands, workflows, API, etc.

**Implementation:** `midicoder/commands/version.py`

---

## Bước 4: Contract Generation - Yêu cầu → DSL

**Lệnh:** `midicoder contract gen`

**Mục đích:** Chuyển đổi `master-brief.md` thành DSL contracts có cấu trúc dùng LLM.

**Inputs:**

1. **master-brief.md**: Yêu cầu người dùng
2. **Project Context**: Từ bước indexing
3. **DSL Schema**: Schema định nghĩa sẵn
4. **LLM Config**: Model high-tier (vd: Claude Sonnet)

**Quy trình:**

1. **Brief Analysis**: LLM phân tích master-brief để xác định contract files cần thiết
2. **Batch Generation**: Sinh contracts từng file một để chính xác schema slicing
3. **Schema Validation**: Mỗi YAML được validate với models
4. **Cross-reference Check**: Đảm bảo các references hợp lệ

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

```bash
# Resume từ run thất bại (chỉ sinh files thiếu/thất bại)
midicoder contract gen resume
```

Resume workflow:
1. Phân tích logs run mới nhất để xác định file status
2. Validate files hiện có (YAML syntax, structure, content)
3. Phân loại files:
   - **Completed**: Tái sử dụng (YAML hợp lệ, cấu trúc đúng)
   - **Failed**: Retry generation
   - 🆕 **Never attempted**: Sinh mới
4. Resume từ breakpoint (tiết kiệm đến 50% tokens)

**Use Case ví dụ:**
- Run ban đầu: 15 files, thất bại ở file 8 (YAML không hợp lệ)
- Resume: Chỉ retry 8 files còn lại (tiết kiệm ~47% tokens)

**Traceability:**

```
.midicoder/runs/contract_gen/<timestamp>/
├── summary.json
├── pass_01_*.json       # Per-pass trace
│   ├── prompt.txt
│   ├── response.txt
│   └── trace.json
└── ...
```

**Implementation:** `midicoder/commands/contract.py`

---

## Bước 5: IR Build - DSL → Intermediate Representation

**Lệnh:** `midicoder ir build [--skip-diagrams]`

**Mục đích:** Biên dịch DSL contracts thành IR JSON được normalize, validate.

**Quy trình (100% Quyết định, Không LLM):**

1. Load tất cả YAML files từ `contracts/`
2. Validate cấu trúc với Pydantic models
3. Kiểm tra ID uniqueness, valid references
4. Build symbol table cho cross-references
5. Normalize IDs và format
6. Build IR modules (Domain, Application, Workflow, API, Policy, Rules, Scenario)
7. Sinh Mermaid diagrams (tùy chọn)

**Outputs:**

```
.midicoder/versions/<version>/irs/
├── ir.json              # IR đầy đủ
├── manifest.json        # Metadata, stats
└── diagrams/            # Mermaid diagrams (tùy chọn)
    ├── api/*.mmd
    ├── commands/*.mmd
    ├── entities/*.mmd
    └── workflows/*.mmd
```

**Validation:**

- Structural: Required fields, no extra fields
- Semantic: ID uniqueness, valid references
- Cross-module: Referenced entities/commands tồn tại
- Chi tiết errors với file, location, suggestions

**Implementation:** `midicoder/ir/builder/builder.py`

---

## Bước 6: Code Build - IR → Pseudo Code Plans

**Lệnh:** `midicoder code build`

**Mục đích:** Sinh pseudo code plans quyết định (FastAPI flavor) từ IR.

**Quy trình (100% Quyết định, Không LLM):**

1. Load `ir.json` từ IR build step
2. Trích xuất components (Commands, Workflows, API Routes)
3. Map vào folder structure (FastAPI conventions)
4. Sinh pseudo code với:
   - Function signatures
   - Type hints
   - Business logic placeholders
   - Integration point markers (anchors)

**Outputs:**

```
.midicoder/versions/<version>/plans/
├── index.json           # Plan registry
├── commands/*.code-plan.json
├── workflows/*.code-plan.json
└── api/*.code-plan.json
```

**Example Code Plan:**

```json
{
  "ir_refs": ["Command:CreateUser"],
  "folder": "app/api/users",
  "target": "fastapi",
  "files": {
    "router": {
      "path": "app/api/users/router.py",
      "sections": [{
        "anchor": "# midicoder:api:users:router:routes",
        "pseudo": "@router.post('/users')\nasync def create_user(...):\n    ..."
      }]
    },
    "service": {
      "path": "app/api/users/service.py",
      "sections": [{
        "anchor": "# midicoder:api:users:service:handlers",
        "pseudo": "async def create_user(...) -> User:\n    ..."
      }]
    }
  }
}
```

**Tính năng chính:**

- **Anchors**: Comment markers (không phải line numbers) cho injection ổn định
- **Folder-level**: Nhóm các files liên quan (router, service, schemas, deps)
- **Warnings**: Báo cáo seams thiếu hoặc cấu trúc không thông thường

**Implementation:** `midicoder/code/builder/`

---

## Bước 7: Code Gen - Pseudo → Real Code

**Lệnh:** `midicoder code gen [--runtime]`

**Mục đích:** Chuyển đổi pseudo code plans thành executable code với patch locations chính xác.

**Quy trình hai bước:**

### Bước 1: Patch Strategy (High-tier LLM)

**Quyết định Ở ĐÂU và NHƯ THẾ NÀO patch:**

- Xác định target files (tạo mới hoặc sửa existing)
- Xác định patch operations (write/edit/delete)
- Tìm semantic anchors (comments, decorators, markers)
- Chọn patch modes (before/after/replace)

### Bước 2: Stack Conversion (Cheap-tier LLM hoặc Skip)

**Chuyển đổi syntax sang target stack:**

- **Target = FastAPI**: Skip conversion (pseudo đã là FastAPI)
- **Target = NestJS/Angular**: Dùng cheap LLM để translate
  - FastAPI → NestJS decorators
  - Python → TypeScript syntax
  - Giữ anchors và style

**Outputs:**

```
.midicoder/versions/<version>/patches/
├── plans/
│   ├── index.json       # Patch plan registry
│   ├── commands/*.patch-plan.json
│   ├── workflows/*.patch-plan.json
│   └── api/*.patch-plan.json
└── runtime/             # (tùy chọn, với --runtime flag)
    └── generated files
```

**Example Patch Plan:**

```json
{
  "ir_ref": "Command:CreateUser",
  "target_stack": "fastapi",
  "patches": [
    {
      "path": "app/api/users/router.py",
      "operation": "edit",
      "anchor": "# midicoder:api:users:router:routes",
      "mode": "after",
      "content": "@router.post('/users')\nasync def create_user(...):\n    ..."
    }
  ]
}
```

**Loại Operations:**

- **write**: Tạo file mới
- **edit**: Sửa file existing ở anchor
- **delete**: Xóa file

**Edit Modes:**

- **before**: Insert trước anchor
- **after**: Insert sau anchor
- **replace**: Replace content ở anchor

**Implementation:** `midicoder/code/generator/`

---

## Bước 8: Code Apply - Patches → Working Directory

**Lệnh:** `midicoder code apply [--force] [--dry-run] [--no-reindex]`

**Mục đích:** Áp dụng patch plans an toàn vào codebase thực tế.

**Tính năng an toàn:**

1. **Snapshot**: Backup files trước khi sửa
2. **Conflict Detection**: Kiểm tra concurrent changes
3. **Dry Run**: Xem trước không ghi
4. **Rollback**: Restore từ snapshot nếu cần
5. **Reindexing**: Cập nhật Project Context sau changes

**Quy trình:**

1. **Pre-flight**: Validate patch plans, check writability, detect conflicts
2. **Snapshot**: Backup files vào `.midicoder/versions/<version>/snapshots/`
3. **Apply**: Thực thi write/edit/delete operations
4. **Verify**: Basic syntax checks, record operations
5. **Reindex**: Cập nhật Project Context (trừ khi `--no-reindex`)

**Outputs:**

```
.midicoder/versions/<version>/patches/<run_id>/
├── ops.json             # Applied operations log
└── *.patch              # Unified diffs

.midicoder/versions/<version>/snapshots/<run_id>/
└── backed up files
```

**Example ops.json:**

```json
[
  {
    "type": "edit",
    "path": "app/api/users/service.py",
    "anchor": "# midicoder:api:users:service:handlers",
    "mode": "after",
    "content": "async def create_user(...):\n    ...",
    "status": "success"
  }
]
```

**Conflict Handling:**

- **Không có `--force`**: Abort với error
- **Có `--force`**: Apply anyway (có thể gây merge conflicts)

**Dry Run:**

```bash
midicoder code apply --dry-run
```

Hiển thị những gì sẽ được applied mà không thực sự modify.

**Implementation:** `midicoder/code/applicator/`

---

## Contract Feedback & Repair

### Check

**Lệnh:** `midicoder contract check`

Validates contracts cho issues (YAML syntax, schema, cross-refs).

### Feedback

**Lệnh:** `midicoder contract feedback`

Tạo/cập nhật `contract-feedbacks.yml` với validation issues và custom feedback.

**Example feedback file:**

```yaml
items:
  - id: FB-001
    file: contracts/app/commands.yaml
    location: "commands[id=CreateOrder]"
    status: pending
    issue: "Thiếu authorization guard"
    suggestion: "Thêm guard với permission = 'create_order'"
```

### Repair Prepare

**Lệnh:** `midicoder contract repair prepare`

Validates feedback file không chạy LLM (checks syntax, references).

### Repair Run

**Lệnh:** `midicoder contract repair run`

Áp dụng feedback items vào contracts dùng LLM:

1. Load feedback file
2. Nhóm theo file
3. Xử lý theo dependency order
4. Sinh và áp dụng patches
5. Sync `master-brief.md`
6. Trích xuất memos vào `.midicoder/context/memos/`
7. Cập nhật feedback status

**Implementation:** `midicoder/contract/`

---

## Tính năng Nâng cao

### Incremental Reindexing

```bash
midicoder index reindex --path src/users/controller.py
```

Cập nhật Project Context chỉ cho các files cụ thể.

### Smart Resume

```bash
midicoder contract gen resume
```

Resume generation thất bại, chỉ regenerate failed/missing files (tiết kiệm đến 50% tokens).

### Diagram Generation

```bash
midicoder ir build              # Với diagrams
midicoder ir build --skip-diagrams  # Không có diagrams
```

Sinh Mermaid diagrams (Domain Model, Command Graph, API Map, Workflows).

---

## Error Handling & Debugging

### Run Artifacts

Mọi command tạo detailed logs:

```
.midicoder/runs/<command>/<timestamp>/
├── summary.json         # Results
├── state_before.json    # State trước
├── state_after.json     # State sau
└── <command-specific artifacts>
```

### Trace Files (Contract Gen)

Comprehensive traces để debug LLM interactions:

```
.midicoder/runs/contract_gen/<timestamp>/
├── pass_01_*.json
│   ├── prompt.txt       # Prompt chính xác gửi đến LLM
│   ├── response.txt     # Raw LLM response
│   └── trace.json       # Context metadata
```

### Vấn đề Thường gặp

| Vấn đề | Giải pháp |
|--------|-----------|
| `No current version set` | Chạy `midicoder version create <ver>` |
| `master-brief.md is missing` | Tạo lại version hoặc thêm file manually |
| `IR is missing` | Chạy `midicoder ir build` |
| `plans/index.json is missing` | Chạy `midicoder code build` |
| `patches/index.json is missing` | Chạy `midicoder code gen` |
| Conflict khi apply | Dùng `--dry-run` để review, `--force` để override |

---

## Triết lý Thiết kế & Hướng Tương lai

### Trạng thái Hiện tại (v0.x)

- LLM cho contract authoring (chất lượng cao requirements capture)
- IR compilation quyết định (zero randomness)
- Code planning quyết định (chỉ FastAPI)
- LLM cho patch strategy (vẫn cần cho quyết định theo ngữ cảnh)
- LLM cho stack conversion (cheap model, chấp nhận được)

### Roadmap Tương lai (v1.x+)

**Mục tiêu:** Giảm phụ thuộc LLM (phương pháp Anti-AI)

1. **AST-based Code Understanding**: Thay regex bằng Tree-sitter
2. **Reverse Engineering**: Trích contracts TỪ code tự động
3. **Universal Transpiler**: IR → Generic AST → Stack-specific emitters
4. **Semantic Anchoring**: AST-path anchors thay vì line numbers
5. **Dependency Graph**: Smart file targeting dựa trên imports

Xem `technic/midicoder-algorithm.md` cho các thiết kế chi tiết.

---

## Đặc tả Thiết kế & Tham khảo Kỹ thuật

Tài liệu thiết kế chi tiết trong folder `technic/`:

- **`technic/DSL-schema.md`**: Đặc tả DSL đầy đủ
- **`technic/DSL-contracts.md`**: Workflow sinh contract
- **`technic/IR-compiler.md`**: Thuật toán biên dịch IR
- **`technic/source-indexing.md`**: Trích xuất Project Context
- **`technic/codegen.md`**: Chiến lược sinh code
- **`technic/contract-repair.md`**: Workflow feedback & repair
- **`technic/midicoder-algorithm.md`**: R&D roadmap

---

## Tóm tắt

Midi Coder pipeline:

1. **Init**: Thiết lập workspace
2. **Index**: Trích xuất Project Context
3. **Version**: Tạo feature workspace
4. **Contract Gen**: Yêu cầu → DSL (hỗ trợ LLM)
5. **IR Build**: DSL → IR (quyết định)
6. **Code Build**: IR → Pseudo plans (quyết định)
7. **Code Gen**: Pseudo → Real patches (hỗ trợ LLM)
8. **Code Apply**: Patches → Working code (quyết định)

**Nguyên tắc Chính:**
- LLM sinh contracts, không sinh code
- Mọi bước tạo auditable artifacts
- Dựa trên patch để dễ review
- Hỗ trợ đa stack qua IR
- Quyết định ở nơi có thể

**Bước Tiếp theo:**
- Xem [Lệnh CLI](cli.md) cho command reference
- Xem [Cấu hình](config.md) cho chi tiết setup
- Xem [Artifacts](artifacts.md) cho cấu trúc file
- Xem [Troubleshooting](troubleshooting.md) cho vấn đề thường gặp