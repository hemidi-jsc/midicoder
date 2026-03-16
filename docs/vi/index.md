# Tài liệu Midi Coder Midi Coder

Chào mừng đến với Midi Coder - một **pipeline sinh code deterministic (quyết định), dựa trên contract** giúp biến đổi yêu cầu thành code production thông qua các contract có cấu trúc.

## Midi Coder là gì?

Midi Coder là công cụ CLI mã nguồn mở giúp bạn sinh code từ yêu cầu trong khi vẫn duy trì **toàn quyền kiểm soát, khả năng truy vết và tính deterministic**.

### Vấn đề

Các phương pháp sinh code truyền thống gặp nhiều thách thức:

- ❌ **Không predictable**: LLM viết code trực tiếp với nhiều biến thể ngẫu nhiên
- ❌ **Không auditable**: Không có dấu vết rõ ràng từ yêu cầu đến code
- ❌ **Full rewrites**: Ghi đè toàn bộ file, khó review
- ❌ **Stack-locked**: Cần công cụ khác nhau cho từng tech stack

### Giải pháp Midi Coder

```
Requirements (master-brief.md)
    ↓ [LLM-assisted]
DSL Contracts (YAML)
    ↓ [Deterministic]
Intermediate Representation (IR JSON)
    ↓ [Deterministic]
Code Plans (Pseudo code)
    ↓ [LLM-assisted]
Patch Plans (Real code)
    ↓ [Deterministic]
Working Code (Dự án của bạn)
```

**Tính năng chính:**

- ✅ **Contract-first**: DSL YAML là single source of truth
- ✅ **Deterministic**: Hầu hết các bước dựa trên rules (không có LLM randomness)
- ✅ **Patch-based**: Thay đổi nhỏ, dễ review (không ghi đè toàn bộ file)
- ✅ **Auditable**: Mọi bước tạo versioned artifacts trong `.midicoder/`
- ✅ **Multi-stack**: Một IR → Nhiều targets (FastAPI, NestJS, Angular)
- ✅ **LLM-assisted, không LLM-dependent**: LLMs chỉ sinh contracts và patch strategies

---

## Khái niệm cốt lõi

### 1. Contract-First Development

Thay vì viết code trực tiếp, bạn viết **requirements** được chuyển đổi thành **structured contracts** (DSL YAML):

```yaml
# contracts/app/commands.yaml
commands:
  - id: CreateUser
    input:
      email: string
      name: string
      role: UserRole
    output:
      type: User
    errors:
      - EmailAlreadyExists
      - InvalidEmailFormat
    guards:
      - type: permission
        permission: create_user
```

Các contracts này:
- **Validated**: Schema-checked trước khi sinh code
- **Versioned**: Lưu trong `.midicoder/versions/`
- **Auditable**: Full trace từ requirement đến implementation
- **Reusable**: Cùng contract → nhiều stack implementations

### 2. Deterministic Pipeline

Hầu hết các bước **100% deterministic** (không LLM):

- ✅ **IR Build**: Contracts → IR (static validation)
- ✅ **Code Build**: IR → Pseudo code (rule-based mapping)
- ✅ **Code Apply**: Patches → Files (deterministic operations)

Chỉ 2 bước dùng LLM:
- ⚠️ **Contract Gen**: Requirements → Contracts (LLM giúp structure)
- ⚠️ **Code Gen**: Pseudo → Real patches (LLM quyết định locations)

### 3. Patch-Based Updates

Thay vì rewrite toàn bộ files, Midi Coder sinh **small patches**:

```diff
--- a/app/users/service.py
+++ b/app/users/service.py
@@ -15,7 +15,12 @@ class UserService:
 
     # midicoder:service:handlers
-    # TODO: Add handlers
+    async def create_user(self, data: CreateUserRequest) -> User:
+        if await self.repo.find_by_email(data.email):
+            raise EmailAlreadyExists()
+        user = User(**data.dict())
+        await self.repo.save(user)
+        return user
```

Lợi ích:
- Dễ review trong pull requests
- Preserves custom code của bạn
- Minimal merge conflicts
- Có thể rollback dễ dàng (có snapshots)

### 4. Multi-Stack Support

Một bộ contracts → Nhiều implementations:

```
IR (stack-agnostic)
    ↓
FastAPI Pseudo Code
    ↓
├─→ FastAPI (Python)
├─→ NestJS (TypeScript)
└─→ Angular (TypeScript)
```

Hiện đang hỗ trợ:
- **FastAPI** (Python backend) - Full support
- **NestJS** (Node.js/TypeScript backend) - Via translation
- **Angular** (TypeScript frontend) - Via translation

---

## Bắt đầu nhanh

### Cài đặt

```bash
# Tạo virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Cài đặt
pip install -U pip
pip install -e .
```

### Tutorial 5 phút

```bash
# 1. Khởi tạo workspace
cd /path/to/your/project
midicoder init

# 2. Index codebase của bạn
midicoder index

# 3. Tạo version
midicoder version create v0.1.0

# 4. Viết requirements (chỉnh sửa file này!)
vim .midicoder/versions/v0.1.0/master-brief.md

# 5. Sinh contracts
midicoder contract gen

# 6. Build IR
midicoder ir build

# 7. Build code plans
midicoder code build

# 8. Sinh patches
midicoder code gen

# 9. Xem trước changes
midicoder code apply --dry-run

# 10. Apply changes
midicoder code apply
```

**Kết quả:** Code của bạn đã được cập nhật với features mới! ✨

---

## Tổng quan Kiến trúc

### Directory Structure

```
your-project/
├── .midicoder/              # Midi Coder workspace
│   ├── config.json          # Configuration
│   ├── secrets.json         # API keys (gitignored)
│   ├── state.json           # Pipeline state
│   ├── context/             # Project Context (indexed codebase)
│   ├── runs/                # Execution logs
│   └── versions/
│       └── v0.1.0/
│           ├── master-brief.md      # Requirements (BẠN viết)
│           ├── contracts/           # DSL YAML (LLM sinh)
│           ├── irs/                 # IR JSON (deterministic)
│           ├── plans/               # Pseudo code (deterministic)
│           ├── patches/             # Real patches (LLM-assisted)
│           └── snapshots/           # Backups
├── src/                     # Source code của bạn
└── ...
```

### Pipeline Stages

| Stage | Input | Output | LLM? | Thời gian |
|-------|-------|--------|------|-----------|
| **Init** | User input | config.json, secrets.json | ❌ | 1-2 phút |
| **Index** | Source code | Project Context | ❌ | 10-60 giây |
| **Version** | Version ID | Version workspace | ❌ | <1 giây |
| **Contract Gen** | master-brief.md | contracts/*.yaml | ✅ High | 1-3 phút |
| **IR Build** | contracts/ | ir.json | ❌ | 5-15 giây |
| **Code Build** | ir.json | plans/ | ❌ | 2-10 giây |
| **Code Gen** | plans/ | patches/ | ✅ High+Cheap | 1-3 phút |
| **Code Apply** | patches/ | Working code | ❌ | 5-20 giây |

**Total Time:** ~5-10 phút cho typical feature

---

## Use Cases

### 1. New Feature Development

Viết requirements → Sinh contracts → Apply code

**Ví dụ:** Thêm user authentication system
- Viết master-brief với auth requirements
- Sinh contracts (entities, commands, API routes)
- Build và apply code
- Review và commit

### 2. API Evolution

Modify contracts → Regenerate code

**Ví dụ:** Thêm field mới vào User entity
- Update `contracts/domain/entities.yaml`
- Rebuild IR và regenerate patches
- Apply changes (chỉ affected files)

### 3. Multi-Stack Development

Một contract set → Nhiều implementations

**Ví dụ:** Backend + Frontend từ cùng contracts
- Viết contracts một lần
- Sinh FastAPI backend
- Sinh Angular frontend
- Consistent API giữa các stacks

### 4. Contract Refinement

Review → Feedback → Repair → Regenerate

**Ví dụ:** Thêm missing authorization checks
- Run `contract check`
- Tạo feedback với issues
- Run `contract repair` để fix
- Regenerate downstream artifacts

### 5. CI/CD Automation

Non-interactive pipeline cho automation

**Ví dụ:** Auto-generate code trong CI
- Dùng environment variables cho config
- Run full pipeline non-interactively
- Generate code như một phần của build process

---

## Lợi ích Chính

### Cho Developers

- ✅ **Clear requirements**: Structured, machine-readable contracts
- ✅ **Easy review**: Small patches thay vì full file rewrites
- ✅ **Full control**: Edit contracts trực tiếp, không có black box
- ✅ **Consistent style**: Generated code follows project conventions
- ✅ **Safe updates**: Snapshots và rollback support

### Cho Teams

- ✅ **Single source of truth**: Contracts define hệ thống
- ✅ **Audit trail**: Full traceability từ requirement đến code
- ✅ **Version control**: Tất cả artifacts có thể version
- ✅ **Parallel development**: Isolated version workspaces
- ✅ **Stack flexibility**: Dễ add target stacks mới

### Cho Projects

- ✅ **Deterministic**: Repeatable results (không có random LLM behavior)
- ✅ **Scalable**: Xử lý large codebases hiệu quả
- ✅ **Maintainable**: Generated code dễ đọc và follows patterns
- ✅ **Testable**: Generate test scenarios từ contracts
- ✅ **Documentable**: Contracts serve as living documentation

---

## Triết lý Thiết kế

### Anti-AI Approach

Midi Coder theo triết lý **"Anti-AI"**:

> "LLMs nên hỗ trợ humans trong authoring requirements, không viết code trực tiếp."

**Current State (v0.x):**
- LLM generates contracts từ natural language (expensive nhưng valuable)
- LLM decides patch strategies (cần contextual understanding)
- Hầu hết các bước khác là deterministic

**Future Vision (v1.x+):**
- Replace LLM bằng reverse engineering (extract contracts từ code)
- Universal transpiler (IR → AST → Stack-specific emitters)
- AST-based understanding (Tree-sitter, không regex)
- Zero LLM dependency cho common operations

Xem `technic/midicoder-algorithm.md` cho roadmap details.

### Core Principles

1. **Contract-First**: Requirements như structured data, không phải comments
2. **Deterministic**: Prefer rules hơn randomness
3. **Patch-Based**: Small changes, dễ review
4. **Auditable**: Full trace từ requirement đến implementation
5. **Multi-Stack**: Một IR → Nhiều targets
6. **LLM-Assisted**: Dùng LLM cho hard parts, không phải everything

---

## Cấu trúc Tài liệu

### Getting Started
- **[Bắt đầu](getting-started.md)**: Installation và tutorial 5 phút
- **[Hướng dẫn Non-Interactive](non-interactive.md)**: Automation setup cho CI/CD

### Core Documentation
- **[Deep Dive Pipeline](pipeline.md)**: Giải thích chi tiết từng bước
- **[CLI Commands](cli.md)**: Complete command reference
- **[Configuration](config.md)**: Config file structure và options
- **[Artifacts](artifacts.md)**: File structure và formats

### Working với Midi Coder
- **[Contracts](contracts.md)**: DSL contract specification
- **[IR](ir.md)**: Intermediate Representation details
- **[Code Generation](codegen.md)**: Code generation strategy
- **[Contract Repair](contract-repair.md)**: Feedback và repair workflow
- **[Project Context](project-context.md)**: Source indexing và context extraction

### Help & Support
- **[Troubleshooting](troubleshooting.md)**: Common issues và solutions
- **[FAQ](faq.md)**: Câu hỏi thường gặp
- **[Contributing](contributing.md)**: Cách đóng góp

### Technical Specifications
- **`technic/DSL-schema.md`**: Complete DSL specification
- **`technic/IR-compiler.md`**: IR compilation algorithm
- **`technic/codegen.md`**: Code generation details
- **`technic/source-indexing.md`**: Context extraction algorithm
- **`technic/contract-repair.md`**: Repair workflow
- **`technic/midicoder-algorithm.md`**: R&D roadmap và future algorithms

---

## Community & Support

### Getting Help

- **Documentation**: Bắt đầu với [Getting Started](getting-started.md)
- **Issues**: Report bugs trên GitHub Issues
- **Discussions**: Đặt câu hỏi trong GitHub Discussions
- **Examples**: Xem `midicoder/code/example/` cho sample artifacts

### Contributing

Midi Coder là open source! Contributions welcome:

- 📝 Documentation improvements
- 🐛 Bug reports và fixes
- ✨ New features
- 🧪 Tests và examples
- 🌐 Multi-stack support

Xem [Contributing Guide](contributing.md) cho details.

---

## Quick Links

### Cho người dùng lần đầu
1. [Installation](getting-started.md#cài-đặt)
2. [Quick Start Tutorial](getting-started.md#tutorial-5-phút)
3. [Pipeline Overview](pipeline.md#tổng-quan-pipeline)

### Cho Developers
1. [CLI Command Reference](cli.md)
2. [Configuration Guide](config.md)
3. [Artifact Structure](artifacts.md)

### Cho Advanced Users
1. [Non-Interactive Mode](non-interactive.md)
2. [Contract Repair Workflow](contract-repair.md)
3. [Technical Specifications](pipeline.md#đặc-tả-thiết-kế--tham-khảo-kỹ-thuật)

---

## Bước tiếp theo

**Mới với Midi Coder?**
→ Bắt đầu với [Getting Started](getting-started.md)

**Muốn hiểu pipeline?**
→ Đọc [Deep Dive Pipeline](pipeline.md)

**Cần command reference?**
→ Xem [CLI Commands](cli.md)

**Setting up automation?**
→ Check [Non-Interactive Guide](non-interactive.md)

**Gặp issues?**
→ Visit [Troubleshooting](troubleshooting.md)

---

**Chúc bạn code vui vẻ với Midi Coder!** 🚀
