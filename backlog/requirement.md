# Midicoder v1.0.0 - Yêu Cầu Kiến Trúc & Kỹ Thuật

**Version:** 1.0.0 | **Last Updated:** 2026-04-21 | **Status:** Single Source of Truth

---

## 📋 Mục Lục

1. [Tổng Quan](#tổng-quan)
2. [Mục Tiêu v1.0.0](#mục-tiêu-v100)
3. [E00: Installation & Setup](#e00-installation--setup)
4. [E01: Project Structure & Version Management](#e01-project-structure--version-management)
5. [E02: Contract-First Compiler Architecture](#e02-contract-first-compiler-architecture)
6. [E03: Capability Language Specification](#e03-capability-language-specification)
7. [E04: Compiler Pipeline](#e04-compiler-pipeline)
8. [E05: MIR (Midicoder Intermediate Representation)](#e05-mir-midicoder-intermediate-representation)
9. [E06: Verifier & Obligation System](#e06-verifier--obligation-system)
10. [E07: Emitter & Scaffolder](#e07-emitter--scaffolder)
11. [E08: Blueprint System](#e08-blueprint-system)
12. [E09: Persistent Storage (SQLite + Neo4j)](#e09-persistent-storage-sqlite--neo4j)
13. [E10: Artifact Contracts](#e10-artifact-contracts)
14. [E11: DSL v1 Kernel Architecture](#e11-dsl-v1-kernel-architecture)
15. [E12: Core Compiler Packs (CP01-CP30)](#e12-core-compiler-packs-cp01-cp30)
16. [E13: Domain Packs (DP01-DP26)](#e13-domain-packs-dp01-dp26)
17. [E14: Regulatory Overlays (RX01-RX12)](#e14-regulatory-overlays-rx01-rx12)
18. [E15: Invariant Gates & Verification](#e15-invariant-gates--verification)
19. [E16: 100 Industry Blueprints](#e16-100-industry-blueprints)
20. [E17: Top 20 Priority Industries](#e17-top-20-priority-industries)
21. [E18: Target Support (Local + AWS)](#e18-target-support-local--aws)
22. [E19: Web Fullstack Generation](#e19-web-fullstack-generation)
23. [E20: CLI Commands](#e20-cli-commands)
24. [E21: MCP Server Tools](#e21-mcp-server-tools)
25. [E22: Non-Functional Requirements](#e22-non-functional-requirements)
26. [E23: Acceptance Criteria](#e23-acceptance-criteria)
27. [E99: Technical Engineering Decisions](#e99-technical-engineering-decisions)

---

## Tổng Quan

### Tuyên Ngôn

**Midicoder là một software factory.**

Nó nhận vào mô tả hệ thống ở mức **capability** và biên dịch ra phần mềm thật, có thể kiểm chứng, có thể vận hành, có thể migrate, có thể audit.

**Midicoder KHÔNG phải:**

- Một AI coding assistant
- Một bộ framework mới
- Một no-code platform
- Một marketplace capability/module
- Một tool để tăng tốc viết boilerplate

**Midicoder LÀ:**

- Một **software factory**
- Một **capability compiler**
- Một **lock-in destroyer**
- Một **replacement engine for generic business software**

### Scope v1.0.0

Midicoder v1.0.0 là một **Contract Coding Platform** với kiến trúc compiler dựa trên contracts, có thể compile ra phần mềm nền web fullstack theo các brief của 100 industries, với ưu tiên là 20 industries đầu tiên.

### Core Philosophy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     CONTRACT-FIRST COMPILER ARCHITECTURE                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Capability Graph (Source of Truth)                                    │
│   └─ Typed, schema-validated, versioned                                 │
│   └─ NOT LLM prompts, NOT free-form contracts                           │
│                                                                         │
│   Expansion Engine (Deterministic)                                      │
│   └─ Macro → Core capability expansion                                  │
│   └─ Config-driven, NOT LLM-generated                                   │
│                                                                         │
│   MIR (Implementation Truth)                                            │
│   └─ Typed IR with ops, data flows, effect flows                        │
│   └─ Transaction boundaries, auth boundaries                            │
│   └─ NOT pseudo-code text                                               │
│                                                                         │
│   Verifier (First-Class)                                                │
│   └─ Compile-time obligation checks                                     │
│   └─ Fail hard on unsatisfied obligations                               │
│                                                                         │
│   Emitter (Deterministic)                                               │
│   └─ Template-based code generation                                     │
│   └─ LLM chỉ là repair layer (optional)                                 │
│                                                                         │
│   Scaffolder (Runtime Setup)                                            │
│   └─ Local (Docker Compose)                                             │
│   └─ Cloud (AWS Terraform)                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Mục Tiêu v1.0.0

### Business Goals

1. **Hỗ trợ 100 industries web apps** với semantics chính xác, không chỉ CRUD
2. **Compile-time compliance** theo từng nhóm ngành
3. **Runtime invariants** không vỡ khi scale và khi lỗi
4. **Deterministic builds** - cùng input cho cùng output
5. **Multi-stack support** - Local (Docker) và AWS baseline

### Technical Goals

1. **100 Industry Blueprints** compile end-to-end
2. **Mỗi blueprint map rõ CP + DP + RX + Invariants**
3. **100 brief.md mẫu** bằng tiếng Anh theo chuẩn universal-fully brief
4. **Sau `contract build` không có bước bắt buộc phụ thuộc LLM**
5. **Hash determinism 100%** cho graph/mir/plan/patch-plan
6. **Fail-fast** cho các lỗi trọng yếu:
   - unresolved refs
   - missing permission
   - missing tenant filter
   - invalid role binding/policy

### Definition of Done

```
✅ 100 blueprints compile pass hoặc lỗi chuẩn hóa rõ
✅ Mỗi blueprint có invariant suite bắt buộc và pass deterministic gates
✅ Không có mandatory LLM step sau `contract build`
✅ Hash determinism 100% cho graph/mir/plan/patch-plan trên mọi blueprint
✅ Local + AWS đều có logging/metrics/secrets safety obligations
✅ Capability Graph là source of truth duy nhất (không có prompt tự do)
✅ MIR là typed IR (không phải pseudo text)
✅ Verifier check coverage obligations tại compile-time
```

---

## E00: Installation & Setup

### Method 1: Shell Script (Linux/macOS)

**Quick Install:**

```bash
# Quick install
curl -o- https://midicoder.com/install.sh | bash

# Or with wget
wget -qO- https://midicoder.com/install.sh | bash

# With options
curl -o- https://midicoder.com/install.sh | bash -s -- --version 1.0.0
curl -o- https://midicoder.com/install.sh | bash -s -- --sandbox  # Test mode
```

**What it does:**

1. Detects OS (macOS/Debian/RedHat/Arch)
2. Downloads binary from GitHub releases
3. Extracts to `~/.midicoder/bin/midicoder`
4. Adds `~/.midicoder/bin` to PATH in shell profile
5. Creates `~/.midicoder/data/` và `~/.midicoder/cache/`

**Installation Structure:**

```
~/.midicoder/
├── bin/
│   └── midicoder          # Main CLI binary
├── cache/                 # LLM response cache
├── data/                  # Global SQLite data (user preferences, stats)
└── midicoder.json        # Global configuration
```

---

### Initial Setup Flow

**Step 1: Installation**

```bash
# User runs install script
curl -o- https://midicoder.com/install.sh | bash

# Output:
# [INFO] Detected OS: Linux (x86_64)
# [INFO] Downloading Midicoder v1.0.0...
# [SUCCESS] Download complete (curl)
# [SUCCESS] Download verified (45678901 bytes)
# [INFO] Installing Midicoder...
# [SUCCESS] Binary installed.
# [INFO] Added to /home/user/.bashrc
# [SUCCESS] PATH configured.
# [INFO] Verifying installation...
# [SUCCESS] ✓ Midicoder installed successfully!
#           midicoder version 1.0.0

# ==========================================
#   Installation Complete!
# ==========================================
#
# To use midicoder:
#   1. Restart your terminal, OR run:
#      source ~/.bashrc   # for bash
#      source ~/.zshrc    # for zsh
#
#   2. Try running:
#      midicoder --version
#      midicoder --help
#      midicoder init
#
# Installation directory: /home/user/.midicoder
```

**Step 2: First Run - `midicoder init`**

```bash
# Navigate to project directory
cd /path/to/my-project

# Initialize midicoder
midicoder init
```

**What `midicoder init` does:**

1. **Creates `.midicoder/` directory structure** (xem E01)
2. **Creates global config `~/.midicoder/midicoder.json`** nếu chưa có
3. **Initializes SQLite databases** trong `.midicoder/data/`
4. **Starts Neo4j Docker container** (nếu chưa chạy)
5. **Starts WebGUI** (FastAPI + Angular)
6. **Opens browser** to http://localhost:7272

---

### Global Configuration Schema

**File:** `~/.midicoder/midicoder.json`

```json
{
  "version": "1.0.0",
  "created_at": "2026-04-21T00:00:00Z",
  "last_run": "2026-04-21T00:00:00Z",
  
  "cli": {
    "theme": "default",
    "language": "vi",
    "output_format": "human"
  },
  
  "llm": {
    "provider": "openai-compatible",
    "model": "qwen3.5-27B",
    "api_url": "http://localhost:11434/v1",
    "api_key": null,
    "max_tokens": 8192,
    "temperature": 0.3,
    "timeout_seconds": 300,
    "retry_attempts": 3,
    "cache_enabled": true
  },
  
  "mcp": {
    "host": "localhost",
    "port": 2026
  },
  
  "neo4j": {
    "host": "localhost",
    "port": 7687,
    "username": "neo4j",
    "password": "password",
    "docker_auto_start": true
  },
  
  "webgui": {
    "host": "localhost",
    "port": 6868,
    "frontend_port": 7272,
    "auto_start": true,
    "open_browser": true
  },
  
  "project": {
    "cwd": "/path/to/current/project",
    "last_opened": "2026-04-21T00:00:00Z"
  },
  
  "version": {
    "max_versions": 5
  }
}
```

**Supported LLM Providers:**

- `openai-compatible` - Custom URL với OpenAI API format (default)
- `openai` - OpenAI API
- `anthropic` - Anthropic API
- `aws-bedrock` - AWS Bedrock
- `azure` - Azure AI Foundry
- `vertex` - Google Vertex AI

**Configuration Commands:**

```bash
# View current config
midicoder config show

# Set a value
midicoder config set cli.language vi
midicoder config set llm.provider openai

# Set with value
midicoder config set llm.api-key "sk-xxx"

# Reset to default
midicoder config reset

# Reset specific key
midicoder config reset cli.theme
```

---

### WebGUI vs CLI Modes

**WebGUI Mode (Default):**

- **Architecture:**
  ```
  ┌─────────────────────────────────────────────────────┐
  │  Angular Frontend (:7272)                           │
  │  ├─ Brief Editor (Markdown)                         │
  │  ├─ Contract Viewer (Mermaid diagrams)              │
  │  ├─ Pipeline Dashboard                              │
  │  ├─ Version Management                              │
  │  └─ Settings                                        │
  └──────────────────┬──────────────────────────────────┘
                     │ REST + WebSocket
  ┌──────────────────▼──────────────────────────────────┐
  │  FastAPI Backend (:6868)                            │
  │  ├─ /api/brief (CRUD)                               │
  │  ├─ /api/contracts (gen/check)                      │
  │  ├─ /api/pipeline (execute)                         │
  │  ├─ /api/versions (manage)                          │
  │  ├─ /ws/progress (real-time updates)                │
  │  └─ CLI wrapper (executes midicoder commands)       │
  └──────────────────┬──────────────────────────────────┘
                     │ exec()
  ┌──────────────────▼──────────────────────────────────┐
  │  Midicoder CLI (underlying engine)                  │
  │  └─ All core logic implemented here                 │
  └─────────────────────────────────────────────────────┘
  ```

- **Khi nào dùng WebGUI:**
  - Desktop development
  - Visual diagram review
  - Collaborative work
  - Less technical users

**CLI Mode (Enhanced TUI):**

- **Features:**
  - UTF-8/Unicode support
  - Rich text rendering (using `rich` library)
  - Interactive menus, forms, tables
  - Progress bars
  - Syntax highlighting

- **Example TUI:**
  ```
  ┌─────────────────────────────────────────────────────────┐
  │  ════════ Midicoder v1.0.0 ════════                     │
  │  ══╤═ Brief ══║═ Contract ══║═ IR ══║═ Code ══║═ Preview═│
  └─────────────────────────────────────────────────────────┘
  
  ┌─ Select Command ───────────────────────────────────────┐
  │  ◉ brief analyze         Analyze project requirements  │
  │    brief clarify         Interactive clarification     │
  │    brief save            Save to library               │
  │    contract gen          Generate DSL contracts        │
  │    ir build              Build MIR from contracts      │
  │    code plan             Generate implementation plan  │
  │    code gen              Generate source code          │
  │    code apply            Apply patches to project      │
  │    preview               Start local preview           │
  │    feedback              Provide feedback              │
  │    version create        Create new version            │
  │    status                Show project status           │
  │    help                  Show help                     │
  │    quit                  Exit                          │
  └─────────────────────────────────────────────────────────┘
  │ ↑/↓ Navigate  Enter Select  q Quit  h Help            │
  ```

- **Khi nào dùng CLI:**
  - Remote servers (SSH)
  - Scripts/automation
  - Power users
  - Low-bandwidth environments

**Note:** WebGUI và CLI có thể chạy song song, trạng thái sync realtime qua SQLite.

---

## E01: Project Structure & Version Management

### Project Workspace Structure

```
.midicoder/
├── config/
│   └── midicoder.yml          # Project-specific config
├── data/
│   ├── context.db             # Codebase index (SQLite)
│   ├── artifacts.db           # Artifacts + activity_log (SQLite)
│   ├── provenance.db          # Lineage + decisions (SQLite)
│   └── briefs.db              # Brief library + clarifications (SQLite)
├── versions/
│   ├── v1.0.0/
│   │   ├── metadata.yml       # Version metadata
│   │   └── src/               # Final source code (git-ready)
│   │       ├── api/
│   │       ├── web/
│   │       └── ...
│   └── v1.0.1/
│       ├── metadata.yml
│       └── src/
├── runtime/                   # Docker compose, logs (preview)
└── cache/                     # LLM cache, template cache
```

**Project Config (`.midicoder/config/midicoder.yml`):**

```yaml
# Project-specific configuration
version: 1.0.0
created_at: "2026-04-21T00:00:00Z"

# Version management
version:
  max_versions: 5  # Auto-cleanup when exceeded

# Active version
active_version: "v1.0.0"

# Capabilities enabled
capabilities:
  enabled:
    - CP01  # Domain Model
    - CP02  # Multi-Tenant
    - CP03  # Auth
  domain_packs:
    - DP01  # E-commerce
  regulatory_overlays:
    - RX01  # GDPR
```

---

### Version Management

**Version Strategy:**

- **Full State:** Mỗi version chứa full state (master-brief + artifacts)
- **Self-Contained:** Mỗi version độc lập, không phụ thuộc version khác
- **Auto-Cleanup:** Khi vượt quá `max_versions` (default: 5), auto-cleanup oldest non-active

**Version Commands:**

```bash
# Create new version
midicoder version create --name v1.0.1
midicoder version create --from v1.0.0 --name v1.0.1

# Switch version
midicoder version use v1.0.1

# List versions
midicoder version list

# Delete version
midicoder version delete v1.0.0
```

**Version Metadata (`.midicoder/versions/<v>/metadata.yml`):**

```yaml
version: 1.0.1
created_at: "2026-04-21T10:00:00Z"
parent_version: "1.0.0"
status: draft  # draft, active, archived

pipeline:
  brief: frozen
  contract: generated
  ir: built
  code: applied

artifacts:
  briefs: 3
  contracts: 4
  files: 87
  lines: 12456
```

**Auto-Cleanup Behavior:**

```
1. Khi chạy `midicoder version create`:
   a. Kiểm tra số lượng versions hiện tại
   b. Nếu > max_versions:
      - Tìm oldest non-active version
      - Nếu status != archived: hỏi user confirmation
      - Xóa version đó (bao gồm folder `.midicoder/versions/<v>/`)
      - Update references trong SQLite

2. Active version KHÔNG bao giờ bị auto-cleanup
3. Archived versions có thể bị cleanup mà không cần confirm
```

---

### Brief Management

**Brief Types:**

| Type | Purpose | Status | Storage |
|------|---------|--------|---------|
| `working-brief` | Brief đang phân tích | draft | SQLite (briefs.db) |
| `master-brief` | Brief đã clarify | frozen | SQLite (briefs.db) |
| `patch-brief` | Incremental changes từ feedback | draft | SQLite (briefs.db) |
| `library-brief` | Reusable templates | frozen | SQLite + optional MD export |

**Brief Lifecycle:**

```
┌─────────────────────────────────────────────────────────────┐
│                    BRIEF LIFECYCLE                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  user-brief.md                                              │
│      ↓ (brief analyze)                                      │
│  working-brief (SQLite) + analysis                          │
│      ↓ (brief clarify - interactive loop)                   │
│  master-brief (SQLite) + clarifications                     │
│      ↓ (brief save)                                         │
│  library-brief (SQLite + optional MD)                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  FEEDBACK LOOP                       │   │
│  │                                                      │   │
│  │  feedback → patch-brief (SQLite)                    │   │
│  │      ↓ (merge)                                       │   │
│  │  master-brief (SQLite, updated)                     │   │
│  │      ↓ (auto-trigger pipeline)                      │   │
│  │  contract gen → ir build → code plan → code gen → code apply │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Clarification Q&A:**

- Lưu trong SQLite `briefs.db` table `clarifications`
- Có cột `is_memo` để đánh dấu highlighted memories
- Memos được inject vào LLM khi authoring contracts

```sql
CREATE TABLE clarifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id INTEGER REFERENCES briefs(id),
    round_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    is_memo INTEGER DEFAULT 0,  -- 1 = memo (highlighted memory)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## E02: Contract-First Compiler Architecture

### 15 Rules Kỹ Thuật Cốt Lõi

| # | Rule |
|---|------|
| 1 | Capability Graph là source of truth duy nhất |
| 2 | Core capability language phải nhỏ, đóng và có semantics chặt |
| 3 | Contract là compiled artifact, không phải authored artifact |
| 4 | MIR là implementation truth, không phải pseudo text |
| 5 | Surface planning tách khỏi semantics |
| 6 | Emitter phải deterministic trước, LLM chỉ là repair layer |
| 7 | Verification là first-class, không phải hậu kiểm trang trí |
| 8 | Portability phải là feature lõi, không phải nice-to-have |
| 9 | Midicoder phải local-first và model-agnostic ở phần lõi |
| 10 | Built-in security, ops, and reliability are non-negotiable |
| 11 | Không plugin market, không module economy |
| 12 | Midicoder phải có replacement benchmarks công khai |
| 13 | Patch engine phải tồn tại, nhưng không phải trái tim |
| 14 | Midicoder phải compile software, không compile addiction |
| 15 | Midicoder phải tự định vị như một factory, không phải tool IDE |

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INPUT LAYER                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  brief.md (natural language)                                            │ │
│  │  └─> LLM Analysis → master-brief (SQLite)                               │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CAPABILITY GRAPH LAYER                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  CapabilityGraph (midicoder/contracts/graph.py)                        │ │
│  │                                                                         │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Core Capabilities (Instruction Set)                               │ │ │
│  │  │  ├─ authorize_permission                                           │ │ │
│  │  │  ├─ enforce_tenant_scope                                           │ │ │
│  │  │  ├─ begin_transaction                                              │ │ │
│  │  │  ├─ create_record                                                  │ │ │
│  │  │  ├─ update_record                                                  │ │ │
│  │  │  ├─ delete_record                                                  │ │ │
│  │  │  ├─ query_records                                                  │ │ │
│  │  │  ├─ publish_event                                                  │ │ │
│  │  │  └─ ... (finite instruction set)                                   │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                         │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Macro Capabilities (High-Level Patterns)                         │ │ │
│  │  │  ├─ authorized_mutation → expands to core capabilities            │ │ │
│  │  │  ├─ authorized_query → expands to core capabilities               │ │ │
│  │  │  ├─ event_handler → expands to core capabilities                  │ │ │
│  │  │  └─ ... (domain-specific macros)                                  │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                         │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Capability Instances (System Capabilities)                       │ │ │
│  │  │  ├─ create_order (type: authorized_mutation)                      │ │ │
│  │  │  │   └─ params: {permission: "order.create", writes: [...]}      │ │ │
│  │  │  ├─ get_order (type: authorized_query)                            │ │ │
│  │  │  │   └─ params: {permission: "order.read", reads: [...]}         │ │ │
│  │  │  └─ ...                                                            │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                         │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Obligations (Compile-Time Requirements)                          │ │ │
│  │  │  ├─ permission_check_required (source: capability:create_order)  │ │ │
│  │  │  ├─ tenant_filter_required (source: capability:get_order)        │ │ │
│  │  │  ├─ transaction_required (source: capability:create_order)       │ │ │
│  │  │  └─ ...                                                            │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXPANSION ENGINE LAYER                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  ExpansionReport (midicoder/contracts/expansion.py)                    │ │
│  │                                                                         │ │
│  │  Input: Capability Instances (with macros)                              │ │
│  │  Process: Deterministic macro → core expansion                          │ │
│  │  Output: Expanded Core Capability Instances                             │ │
│  │                                                                         │ │
│  │  Example:                                                               │ │
│  │  ──────────                                                               │ │
│  │  Input:  create_order (authorized_mutation)                             │ │
│  │           └─ params: {permission: "order.create"}                       │ │
│  │                                                                         │ │
│  │  Expansion Steps:                                                       │ │
│  │  1. resolve_macro → authorized_mutation definition                      │ │
│  │  2. apply_default_obligations → [perm_check, tenant_filter, txn]       │ │
│  │  3. generate_core_instances:                                            │ │
│  │     ├─ auth_perm_001 (authorize_permission)                            │ │
│  │     ├─ tenant_scope_001 (enforce_tenant_scope)                          │ │
│  │     ├─ begin_txn_001 (begin_transaction)                                │ │
│  │     ├─ create_order_rec_001 (create_record)                             │ │
│  │     ├─ emit_order_created_001 (publish_event)                           │ │
│  │     └─ commit_txn_001 (commit_transaction)                              │ │
│  │                                                                         │ │
│  │  Trace: ExpansionTrace                                                  │ │
│  │  └─ source_id: create_order                                             │ │
│  │  └─ source_type: authorized_mutation                                     │ │
│  │  └─ target_ids: [auth_perm_001, tenant_scope_001, ...]                  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MIR LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  MIR (midicoder/contracts/mir.py)                                       │ │
│  │                                                                         │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Operations (Core Capability Instructions)                        │ │ │
│  │  │  ├─ {op: "authorize_permission", params: {...}, obligation_refs: [...] } │ │
│  │  │  ├─ {op: "enforce_tenant_scope", params: {...}, obligation_refs: [...] } │ │
│  │  │  ├─ {op: "begin_transaction", params: {...}}                      │ │ │
│  │  │  ├─ {op: "create_record", params: {...}, output_refs: [...]}     │ │ │
│  │  │  └─ ...                                                            │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                         │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Data Flows (Explicit Data Movement)                              │ │ │
│  │  │  ├─ {source_op: "authorize_permission", source_field: "user_id",  │ │ │
│  │  │     target_op: "create_record", target_field: "created_by"}      │ │ │
│  │  │  └─ ...                                                            │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                         │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Effect Flows (Events, Side Effects)                              │ │ │
│  │  │  ├─ {source_op: "create_record", effect_type: "event_publish",    │ │ │
│  │  │     target: "OrderCreated", payload_fields: [...]}                │ │ │
│  │  │  └─ ...                                                            │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                         │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Boundaries (Transaction, Auth, Tenant)                           │ │ │
│  │  │  ├─ {id: "txn_001", boundary_type: "transaction",                 │ │ │
│  │  │     enclosing_ops: ["create_order", "create_items"]}              │ │ │
│  │  │  └─ ...                                                            │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VERIFIER LAYER                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  ValidationReport (midicoder/contracts/validation.py)                  │ │
│  │                                                                         │ │
│  │  Compile-Time Checks:                                                   │ │
│  │  ───────────────────                                                     │ │
│  │  ✅ Syntax Validation (schema compliance)                               │ │
│  │  ✅ Reference Resolution (no unresolved refs)                           │ │
│  │  ✅ Obligation Coverage (all obligations satisfied)                     │ │
│  │  ✅ Authorization Checks (permission, tenant, transaction)              │ │
│  │  ✅ Data Flow Safety (no leaks, validated inputs)                       │ │
│  │  ✅ Compliance Rules (industry-specific invariants)                     │ │
│  │                                                                         │ │
│  │  Error Codes:                                                           │ │
│  │  ──────────                                                               │ │
│  │  ├─ SYNTAX_ERROR                                                         │ │
│  │  ├─ UNRESOLVED_REFERENCE                                                 │ │
│  │  ├─ MISSING_PERMISSION_CHECK                                             │ │
│  │  ├─ MISSING_TENANT_FILTER                                                │ │
│  │  ├─ OBLIGATION_NOT_COVERED                                               │ │
│  │  ├─ TENANT_LEAK                                                          │ │
│  │  ├─ PII_EXPOSURE                                                         │ │
│  │  └─ ... (40+ error codes)                                                │ │
│  │                                                                         │ │
│  │  Fail-Fast:                                                             │ │
│  │  ──────────                                                               │ │
│  │  If critical obligation not covered → compilation FAILS                 │ │
│  │  No code generation if validation fails                                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EMITTER LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Code Generation (Deterministic)                                        │ │
│  │                                                                         │ │
│  │  Input: Validated MIR                                                   │ │
│  │  Process: Template-based code generation (Jinja2)                       │ │
│  │  Output: Source Code Files                                              │ │
│  │                                                                         │ │
│  │  Targets:                                                               │ │
│  │  ──────                                                                   │ │
│  │  ├─ Backend (FastAPI/Python, NestJS/TypeScript)                         │ │
│  │  ├─ Frontend (Angular/TypeScript, React/TypeScript)                     │ │
│  │  ├─ Database (SQLAlchemy models, migrations)                            │ │
│  │  ├─ Infrastructure (Docker Compose, Terraform)                          │ │
│  │  ├─ Communication (gRPC, GraphQL, WebSocket)                            │ │
│  │  └─ Tests (pytest, Playwright)                                          │ │
│  │                                                                         │ │
│  │  LLM Role:                                                              │ │
│  │  ──────                                                                   │ │
│  │  Only as optional repair layer for edge cases                           │ │
│  │  NOT for core code generation                                           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SCAFFOLDER LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Runtime Setup                                                          │ │
│  │                                                                         │ │
│  │  Local Target (Docker Compose):                                         │ │
│  │  ──────────────────────────────                                          │ │
│  │  ├─ docker-compose.yml                                                   │ │
│  │  ├─ Dockerfile.api, Dockerfile.frontend                                  │ │
│  │  ├─ .env.local.example                                                   │ │
│  │  ├─ Neo4j container                                                      │ │
│  │  └─ Health checks, startup scripts                                       │ │
│  │                                                                         │ │
│  │  AWS Target (Terraform):                                                │ │
│  │  ──────────────────────                                                  │ │
│  │  ├─ terraform/main.tf                                                    │ │
│  │  ├─ terraform/modules/                                                   │ │
│  │  │  ├─ api (ECS/Elastic Beanstalk)                                      │ │
│  │  │  ├─ database (RDS/Aurora)                                            │ │
│  │  │  ├─ cache (ElastiCache)                                              │ │
│  │  │  ├─ neo4j (Aura)                                                     │ │
│  │  │  └─ ...                                                              │ │
│  │  └─ CI/CD pipelines (GitHub Actions)                                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## E03: Capability Language Specification

### Core Principles

1. **Small, Closed Instruction Set**: Core capabilities là finite set của primitive operations
2. **Typed Parameters**: Mỗi capability có params schema rõ ràng
3. **Explicit Obligations**: Mỗi capability declare obligations cần satisfy
4. **Macro Expansion**: Macros expand deterministic về core capabilities

### Core Capabilities (Instruction Set)

```python
# midicoder/contracts/graph.py - CoreCapability class

class CoreCapability:
    """
    Core Capability - Primitive Instruction.
    
    Đây là instruction set hữu hạn mà mọi macro expand về.
    """

    # Authorization & Security
    AUTHORIZE_PERMISSION = "authorize_permission"
    ENFORCE_TENANT_SCOPE = "enforce_tenant_scope"
    VALIDATE_INPUT = "validate_input"

    # Data Operations
    CREATE_RECORD = "create_record"
    UPDATE_RECORD = "update_record"
    DELETE_RECORD = "delete_record"
    QUERY_RECORDS = "query_records"
    LOAD_ENTITY = "load_entity"

    # Transaction Management
    BEGIN_TRANSACTION = "begin_transaction"
    COMMIT_TRANSACTION = "commit_transaction"
    ROLLBACK_TRANSACTION = "rollback_transaction"

    # Event & Integration
    PUBLISH_EVENT = "publish_event"
    CALL_EXTERNAL_SERVICE = "call_external_service"
    SEND_NOTIFICATION = "send_notification"

    # Audit & Observability
    WRITE_AUDIT_LOG = "write_audit_log"
    RECORD_METRIC = "record_metric"

    # ... (20-30 core capabilities total)
```

### Macro Capabilities (High-Level Patterns)

```python
# midicoder/contracts/graph.py - MacroCapability class

class MacroCapability:
    """
    Macro Capability - High-Level Pattern.
    
    Macros là "sugar", expand deterministic về core capabilities.
    """

    AUTHORIZED_MUTATION = "authorized_mutation"
    """
    Pattern: Authorization + Tenant Scope + Transaction + Mutation + Event
    
    Expands to:
    - authorize_permission
    - enforce_tenant_scope
    - begin_transaction
    - create_record/update_record/delete_record
    - publish_event
    - commit_transaction
    """

    AUTHORIZED_QUERY = "authorized_query"
    """
    Pattern: Authorization + Tenant Scope + Query
    
    Expands to:
    - authorize_permission
    - enforce_tenant_scope
    - query_records
    """

    EVENT_HANDLER = "event_handler"
    """
    Pattern: Event Subscription + Validation + Processing
    
    Expands to:
    - validate_input
    - begin_transaction
    - ... (processing logic)
    - commit_transaction
    """

    WORKFLOW_DEFINITION = "workflow_definition"
    """
    Pattern: Multi-step business process
    
    Expands to:
    - Multiple authorized_mutation/query in sequence
    - State machine for workflow progress
    - Compensation logic for failures
    """
```

### Capability DSL Format

```yaml
# DSL format for defining capabilities

capabilities:
  - name: create_order
    type: authorized_mutation
    params:
      permission: "order.create"
      tenant_scope: "tenant_isolated"
      transaction: required
      creates:
        - entity: Order
        - entity: OrderItem
      emits:
        - event: OrderCreated
    
  - name: get_order
    type: authorized_query
    params:
      permission: "order.read"
      tenant_scope: "tenant_isolated"
      reads:
        - entity: Order
        - entity: OrderItem
      pagination: true
    
  - name: update_order_status
    type: authorized_mutation
    params:
      permission: "order.update"
      tenant_scope: "tenant_isolated"
      transaction: required
      updates:
        - entity: Order
          fields:
            - status
      emits:
        - event: OrderStatusChanged
```

---

## E04: Compiler Pipeline

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MIDICODER COMPILER PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 0: INITIALIZATION (Deterministic)                                    │
│  ├─ midicoder init                                                          │
│  ├─ midicoder version create                                                │
│  ├─ midicoder index                                                         │
│  └─ Output: .midicoder/ structure, SQLite DBs, Neo4j ready                  │
│                                                                             │
│  PHASE 1: BRIEF PROCESSING (LLM-based)                                      │
│  ├─ midicoder brief analyze                                                 │
│  │   └─ Input: user brief (natural language)                                │
│  │   └─ Output: working-brief (SQLite)                                      │
│  ├─ midicoder brief clarify                                                 │
│  │   └─ Input: working-brief + user answers                                 │
│  │   └─ Output: master-brief (SQLite, frozen)                               │
│  └─ Context Injection: codebase summary, existing entities                  │
│                                                                             │
│  PHASE 2: CONTRACT GENERATION (LLM + MCP)                                   │
│  ├─ midicoder contract gen                                                  │
│  │   └─ Input: master-brief + MCP tools                                     │
│  │   └─ Process: LLM iterates with compile_contracts feedback               │
│  │   └─ Output: DSL contracts (artifacts.db)                                │
│  ├─ midicoder contract check                                                │
│  │   └─ Validate DSL against schema                                         │
│  │   └─ Auto-fix with LLM if errors                                         │
│  └─ MCP Tools: get_dsl_schema, list_core_capabilities, compile_contracts   │
│                                                                             │
│  PHASE 3: CAPABILITY GRAPH BUILD (Deterministic)                            │
│  ├─ Parse DSL → AST                                                         │
│  ├─ Validate schema compliance                                              │
│  ├─ Resolve $ref references                                                 │
│  ├─ Build CapabilityGraph object                                            │
│  └─ Output: CapabilityGraph (artifacts.db)                                  │
│                                                                             │
│  PHASE 4: EXPANSION (Deterministic)                                         │
│  ├─ Expand macros → core capabilities                                       │
│  ├─ Generate obligation instances                                           │
│  ├─ Build ExpansionReport with traces                                       │
│  └─ Output: Expanded CapabilityGraph (artifacts.db)                         │
│                                                                             │
│  PHASE 5: MIR GENERATION (Deterministic)                                    │
│  ├─ midicoder ir build                                                      │
│  ├─ Transform CapabilityGraph → MIR                                         │
│  ├─ Generate operations, data flows, effect flows                           │
│  ├─ Build symbol table                                                      │
│  └─ Output: mir.json (artifacts.db), symbol-table.json                      │
│                                                                             │
│  PHASE 6: VERIFICATION (Deterministic)                                      │
│  ├─ Syntax validation                                                       │
│  ├─ Reference resolution                                                    │
│  ├─ Obligation coverage checks                                              │
│  ├─ Authorization checks                                                    │
│  ├─ Data flow safety                                                        │
│  └─ Output: ValidationReport (artifacts.db)                                 │
│                                                                             │
│  PHASE 7: CODE PLANNING (Deterministic)                                     │
│  ├─ midicoder code plan                                                     │
│  ├─ MIR → Implementation Plan                                               │
│  ├─ Group by modules                                                        │
│  ├─ Select templates based on target stack                                  │
│  ├─ Build dependency graph                                                  │
│  └─ Output: lowering.json (artifacts.db)                                    │
│                                                                             │
│  PHASE 8: CODE GENERATION (Deterministic)                                   │
│  ├─ midicoder code gen                                                      │
│  ├─ Template rendering (Jinja2)                                             │
│  ├─ Inject context (MIR data, target stack)                                 │
│  ├─ Format code (Black, Prettier)                                           │
│  └─ Output: Source files (artifacts.db + versions/<v>/src/)                 │
│                                                                             │
│  PHASE 9: CODE APPLICATION (Deterministic)                                  │
│  ├─ midicoder code apply                                                    │
│  ├─ Copy generated files to versions/<v>/src/                               │
│  ├─ Handle conflicts (backup, merge)                                        │
│  └─ Output: Applied status (artifacts.db)                                   │
│                                                                             │
│  PHASE 10: PREVIEW (Runtime)                                                │
│  ├─ midicoder preview                                                       │
│  ├─ Generate docker-compose.yml                                             │
│  ├─ Start containers (backend, frontend, db, neo4j)                         │
│  ├─ Health checks                                                           │
│  └─ Output: Running application at localhost                                │
│                                                                             │
│  FEEDBACK LOOP (LLM-based)                                                  │
│  ├─ midicoder feedback                                                      │
│  │   └─ Input: User feedback (text)                                         │
│  │   └─ Output: patch-brief (SQLite)                                        │
│  ├─ Merge patch into master-brief                                           │
│  ├─ Auto-trigger: contract gen → ir build → code plan → code gen → apply   │
│  └─ Preview restart                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### LLM vs Deterministic Stages

| Stage | LLM? | Deterministic? | Context Injection? |
|-------|------|----------------|-------------------|
| brief analyze | ✅ | ❌ | ✅ (codebase) |
| brief clarify | ✅ | ❌ | ✅ (Q&A history) |
| contract gen | ✅ | ❌ | ✅ (MCP tools) |
| contract check | ⚠️ (auto-fix) | ✅ | ❌ |
| ir build | ❌ | ✅ | ❌ |
| code plan | ❌ | ✅ | ❌ |
| code gen | ❌ | ✅ | ❌ |
| code apply | ❌ | ✅ | ❌ |
| feedback | ✅ | ❌ | ✅ (MIR, symbols) |

**Determinism Guarantee:**

```python
# Deterministic stages: NO context injection

def ir_build(contracts_path: str) -> MIR:
    """
    Build MIR from contracts.
    
    Input: CHỈ contracts/ir.json
    Process: Parse → Normalize → Analyze → Generate MIR
    Output: mir.json
    
    ĐẢM BẢO: Cùng input → Cùng output (hash determinism)
    """
    # KHÔNG có context injection ở đây!
    # Chỉ đọc từ contracts/ir.json
    ...

def code_plan(mir_path: str) -> ImplementationPlan:
    """
    Generate implementation plan from MIR.
    
    Input: CHỈ mir.json
    Process: Lowering → Patch planning
    Output: lowering.json
    
    ĐẢM BẢO: Cùng input → Cùng output (hash determinism)
    """
    # KHÔNG có context injection ở đây!
    # Chỉ đọc từ mir.json
    ...
```

---

## E05: MIR (Midicoder Intermediate Representation)

### MIR Structure

```python
# midicoder/contracts/mir.py

class MIR:
    """
    Midicoder Intermediate Representation (MIR).
    
    MIR là typed IR đại diện cho implementation truth.
    Đây KHÔNG phải pseudo-code text, mà là structured data với:
    - Operations (core capability instructions)
    - Data Flows (explicit data movement)
    - Effect Flows (events, side effects)
    - Boundaries (transaction, auth, tenant)
    """
    
    def __init__(self):
        self.operations: list[Operation] = []
        self.data_flows: list[DataFlow] = []
        self.effect_flows: list[EffectFlow] = []
        self.boundaries: list[Boundary] = []
        self.metadata: dict = {}


class Operation:
    """
    Operation - Core Capability Instruction.
    """
    def __init__(
        self,
        op_id: str,
        op_type: str,  # authorize_permission, create_record, etc.
        params: dict,
        obligation_refs: list[str],
        input_refs: list[str] = None,
        output_refs: list[str] = None
    ):
        self.op_id = op_id
        self.op_type = op_type
        self.params = params
        self.obligation_refs = obligation_refs
        self.input_refs = input_refs or []
        self.output_refs = output_refs or []


class DataFlow:
    """
    Data Flow - Explicit data movement between operations.
    """
    def __init__(
        self,
        source_op: str,
        source_field: str,
        target_op: str,
        target_field: str,
        transformation: str = None  # Optional: uppercase, concat, etc.
    ):
        self.source_op = source_op
        self.source_field = source_field
        self.target_op = target_op
        self.target_field = target_field
        self.transformation = transformation


class EffectFlow:
    """
    Effect Flow - Events and side effects.
    """
    def __init__(
        self,
        source_op: str,
        effect_type: str,  # event_publish, log_write, metric_record
        target: str,  # Event name, log type, metric name
        payload_fields: list[str] = None
    ):
        self.source_op = source_op
        self.effect_type = effect_type
        self.target = target
        self.payload_fields = payload_fields or []


class Boundary:
    """
    Boundary - Transaction, Auth, Tenant boundaries.
    """
    def __init__(
        self,
        boundary_id: str,
        boundary_type: str,  # transaction, auth, tenant
        enclosing_ops: list[str],
        config: dict = None
    ):
        self.boundary_id = boundary_id
        self.boundary_type = boundary_type
        self.enclosing_ops = enclosing_ops
        self.config = config or {}
```

### MIR Example

```json
{
  "version": "1.0.0",
  "operations": [
    {
      "op_id": "auth_001",
      "op_type": "authorize_permission",
      "params": {
        "permission": "order.create"
      },
      "obligation_refs": ["perm_oblig_001"],
      "output_refs": ["user_context"]
    },
    {
      "op_id": "tenant_001",
      "op_type": "enforce_tenant_scope",
      "params": {
        "scope": "tenant_isolated"
      },
      "obligation_refs": ["tenant_oblig_001"],
      "input_refs": ["user_context"],
      "output_refs": ["tenant_id"]
    },
    {
      "op_id": "txn_begin_001",
      "op_type": "begin_transaction",
      "params": {},
      "output_refs": ["txn_id"]
    },
    {
      "op_id": "create_order_001",
      "op_type": "create_record",
      "params": {
        "entity": "Order",
        "fields": ["order_id", "tenant_id", "total", "status"]
      },
      "input_refs": ["tenant_id", "order_data"],
      "output_refs": ["order_entity"]
    },
    {
      "op_id": "emit_order_001",
      "op_type": "publish_event",
      "params": {
        "event": "OrderCreated"
      },
      "input_refs": ["order_entity"]
    },
    {
      "op_id": "txn_commit_001",
      "op_type": "commit_transaction",
      "params": {},
      "input_refs": ["txn_id"]
    }
  ],
  "data_flows": [
    {
      "source_op": "auth_001",
      "source_field": "user_id",
      "target_op": "create_order_001",
      "target_field": "created_by"
    },
    {
      "source_op": "tenant_001",
      "source_field": "tenant_id",
      "target_op": "create_order_001",
      "target_field": "tenant_id"
    }
  ],
  "effect_flows": [
    {
      "source_op": "create_order_001",
      "effect_type": "event_publish",
      "target": "OrderCreated",
      "payload_fields": ["order_id", "tenant_id", "total"]
    }
  ],
  "boundaries": [
    {
      "boundary_id": "txn_001",
      "boundary_type": "transaction",
      "enclosing_ops": ["create_order_001", "emit_order_001"]
    }
  ]
}
```

---

## E06: Verifier & Obligation System

### Compile-Time Checks

```python
# midicoder/contracts/validation.py

class ValidationReport:
    """
    Validation Report - Compile-time verification results.
    """
    
    def __init__(self):
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationWarning] = []
        self.info: list[ValidationInfo] = []
        self.passed: bool = True


class ValidationError:
    """
    Validation Error - Critical error, compilation fails.
    """
    def __init__(
        self,
        error_code: str,
        message: str,
        location: dict,
        suggestion: str = None
    ):
        self.error_code = error_code
        self.message = message
        self.location = location  # {file, line, column}
        self.suggestion = suggestion


class ValidationWarning:
    """
    Validation Warning - Non-critical, compilation continues.
    """
    def __init__(
        self,
        warning_code: str,
        message: str,
        location: dict
    ):
        self.warning_code = warning_code
        self.message = message
        self.location = location
```

### Error Codes

| Code | Description | Severity |
|------|-------------|----------|
| SYNTAX_ERROR | DSL không hợp lệ | Error |
| UNRESOLVED_REFERENCE | Reference không tìm thấy | Error |
| MISSING_PERMISSION_CHECK | Thiếu permission check | Error |
| MISSING_TENANT_FILTER | Thiếu tenant filter | Error |
| OBLIGATION_NOT_COVERED | Obligation chưa satisfy | Error |
| TENANT_LEAK | Tenant data có thể leak | Error |
| PII_EXPOSURE | PII data exposed | Error |
| INVALID_ROLE_BINDING | Role binding không hợp lệ | Error |
| TRANSACTION_MISMATCH | Transaction boundary mismatch | Error |
| DATA_FLOW_CYCLE | Data flow có cycle | Error |

### Obligation System

```python
# midicoder/contracts/obligations.py

class Obligation:
    """
    Obligation - Compile-time requirement.
    """
    
    def __init__(
        self,
        obligation_id: str,
        obligation_type: str,
        source: str,  # Capability instance ID
        requirement: dict,
        satisfied: bool = False
    ):
        self.obligation_id = obligation_id
        self.obligation_type = obligation_type
        self.source = source
        self.requirement = requirement
        self.satisfied = satisfied


# Example obligations

obligations = [
    Obligation(
        obligation_id="perm_oblig_001",
        obligation_type="permission_check",
        source="create_order",
        requirement={
            "permission": "order.create",
            "check_before": ["create_record"]
        }
    ),
    Obligation(
        obligation_id="tenant_oblig_001",
        obligation_type="tenant_filter",
        source="get_order",
        requirement={
            "scope": "tenant_isolated",
            "filter_on": ["tenant_id"]
        }
    ),
    Obligation(
        obligation_id="txn_oblig_001",
        obligation_type="transaction",
        source="create_order",
        requirement={
            "required": True,
            "encloses": ["create_record", "publish_event"]
        }
    )
]
```

### Verification Rules

1. **Permission Check Required:**
   - Every `authorized_mutation` must have `authorize_permission` before any data operation
   - Permission must match the operation type

2. **Tenant Filter Required:**
   - Every `authorized_query` must have `enforce_tenant_scope`
   - Query must filter by tenant_id

3. **Transaction Required:**
   - Mutations that write to multiple entities must be in transaction
   - Transaction must enclose all related operations

4. **No Unresolved References:**
   - All entity references must resolve to defined entities
   - All event references must resolve to defined events

5. **No Tenant Leaks:**
   - Queries must always filter by tenant
   - No cross-tenant data access without explicit `cross_tenant` scope

---

## E07: Emitter & Scaffolder

### Emitter (Code Generation)

**Template Engine:** Jinja2

**Template Storage:** `midicoder/stacks/<stack-name>/templates/`

**Supported Stacks:**

```
midicoder/stacks/
├── fastapi/
│   ├── templates/
│   │   ├── models/
│   │   │   └── sqlalchemy_model.jinja2
│   │   ├── schemas/
│   │   │   └── pydantic_schema.jinja2
│   │   ├── routes/
│   │   │   └── fastapi_route.jinja2
│   │   ├── services/
│   │   │   └── service.jinja2
│   │   └── ...
│   └── config.yml
├── nestjs/
│   ├── templates/
│   │   ├── entities/
│   │   ├── dto/
│   │   ├── controllers/
│   │   ├── services/
│   │   └── ...
│   └── config.yml
├── angular/
│   ├── templates/
│   │   ├── components/
│   │   ├── services/
│   │   ├── models/
│   │   └── ...
│   └── config.yml
├── react/
│   ├── templates/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── ...
│   └── config.yml
└── aws/
    ├── templates/
    │   ├── terraform/
    │   ├── ecs/
    │   └── ...
    └── config.yml
```

**Template Example (FastAPI Route):**

```jinja2
# templates/routes/fastapi_route.jinja2

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from {{ module_name }}.schemas import {{ schema_create }}, {{ schema_read }}
from {{ module_name }}.services import {{ service_name }}
from api.db.session import get_db

router = APIRouter(prefix="{{ prefix }}", tags=["{{ entity_name }}"])


@router.post("/", response_model={{ schema_read }})
async def create_{{ entity_singular }}(
    {{ entity_singular }}: {{ schema_create }},
    db: AsyncSession = Depends(get_db)
):
    """
    Tạo mới {{ entity_name.lower() }}.
    
    Args:
        {{ entity_singular }}: Dữ liệu {{ entity_name.lower() }} mới
        
    Returns:
        {{ entity_name.lower() }} vừa tạo
    """
    service = {{ service_name }}(db)
    return await service.create({{ entity_singular }}= {{ entity_singular }})


@router.get("/{id}", response_model={{ schema_read }})
async def get_{{ entity_singular }}(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy {{ entity_name.lower() }} theo ID.
    
    Args:
        id: ID của {{ entity_name.lower() }}
        
    Returns:
        {{ entity_name.lower() }} với ID tương ứng
        
    Raises:
        HTTPException: Nếu không tìm thấy {{ entity_name.lower() }}
    """
    service = {{ service_name }}(db)
    result = await service.get(id=id)
    if not result:
        raise HTTPException(status_code=404, detail="{{ entity_name }} not found")
    return result
```

**Code Generation Process:**

```python
# midicoder/code/emitter.py

class Emitter:
    """
    Emitter - Template-based code generator.
    
    Input: Validated MIR
    Process: Jinja2 template rendering
    Output: Source code files
    """
    
    def __init__(self, stack_config: dict, template_dir: Path):
        self.stack_config = stack_config
        self.template_dir = template_dir
        self.environment = self._load_jinja2_environment()
    
    def generate(self, mir: MIR) -> dict[str, str]:
        """
        Generate source code from MIR.
        
        Args:
            mir: Validated MIR
            
        Returns:
            Mapping of file paths to code content
        """
        files = {}
        
        # Generate models
        for entity in mir.entities:
            model_code = self._render_template(
                "models/sqlalchemy_model.jinja2",
                context={"entity": entity}
            )
            files[f"models/{entity.name.lower()}.py"] = model_code
        
        # Generate schemas
        for entity in mir.entities:
            schema_code = self._render_template(
                "schemas/pydantic_schema.jinja2",
                context={"entity": entity}
            )
            files[f"schemas/{entity.name.lower()}.py"] = schema_code
        
        # Generate routes
        for capability in mir.capabilities:
            route_code = self._render_template(
                "routes/fastapi_route.jinja2",
                context={"capability": capability}
            )
            files[f"routes/{capability.name.lower()}.py"] = route_code
        
        # ... more generation
        
        return files
    
    def _render_template(self, template_name: str, context: dict) -> str:
        """Render Jinja2 template with context."""
        template = self.environment.get_template(template_name)
        return template.render(**context)
```

### Scaffolder (Runtime Setup)

**Local Target (Docker Compose):**

```yaml
# .midicoder/runtime/docker-compose.yml

version: '3.8'

services:
  api:
    build:
      context: .midicoder/versions/${VERSION}/src/api
      dockerfile: Dockerfile
    ports:
      - "${API_PORT:-8000}:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app
      - NEO4J_URL=bolt://neo4j:7687
      - NEO4J_USERNAME=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
    depends_on:
      - db
      - neo4j
    volumes:
      - ./logs/api.log:/app/logs/app.log

  frontend:
    build:
      context: .midicoder/versions/${VERSION}/src/web
      dockerfile: Dockerfile
    ports:
      - "${FRONTEND_PORT:-4200}:4200"
    environment:
      - API_URL=http://localhost:8000

  db:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app
    volumes:
      - postgres_data:/var/lib/postgresql/data

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=${NEO4J_USERNAME}/${NEO4J_PASSWORD}
    volumes:
      - neo4j_data:/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  neo4j_data:
```

**AWS Target (Terraform):**

```hcl
# .midicoder/runtime/terraform/main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "api" {
  source = "./modules/api"
  
  app_name     = var.app_name
  instance_type = var.ecs_instance_type
  
  database_endpoint = module.rds.endpoint
  neo4j_endpoint    = module.neo4j.endpoint
  
  depends_on = [module.rds, module.neo4j]
}

module "rds" {
  source = "./modules/rds"
  
  engine  = "postgres"
  version = "15"
  
  instance_class = "db.t3.medium"
}

module "neo4j" {
  source = "terraform-aws-modules/neo4j/aws"
  version = "1.0.0"
  
  instance_type = "t3.medium"
}
```

---

## E08: Blueprint System

### Blueprint Structure

```
industry/blueprints/
├── ecommerce-d2c/
│   ├── blueprint.yml          # Blueprint definition
│   ├── brief.md               # Sample brief
│   ├── contracts/
│   │   ├── entities.yml
│   │   ├── commands.yml
│   │   ├── queries.yml
│   │   └── events.yml
│   └── invariants/
│       └── ecommerce_invariants.yml
├── marketplace-b2c/
│   └── ...
├── banking-core/
│   └── ...
└── ... (100 blueprints)
```

### Blueprint Definition

```yaml
# industry/blueprints/ecommerce-d2c/blueprint.yml

name: E-commerce D2C
description: Direct-to-consumer e-commerce platform
domain: Commerce

# Compiler Packs
compiler_packs:
  - CP01  # Domain Model
  - CP02  # Multi-Tenant
  - CP03  # Auth & Authorization
  - CP05  # Event-Driven
  - CP08  # Database & Data Access
  - CP11  # File Storage
  - CP12  # Notification

# Domain Packs
domain_packs:
  - DP01  # E-commerce domain

# Regulatory Overlays
regulatory_overlays:
  - RX01  # GDPR
  - RX11  # PCI-DSS (if payments)

# Invariants
invariants:
  - file: ecommerce_invariants.yml
    required: true

# Target Support
targets:
  - local/docker
  - aws/ecs

# Estimated Complexity
complexity: medium

# Estimated Generation Time
generation_time:
  brief_to_contract: 5m
  contract_to_code: 2m
  total: 7m
```

### Invariants

```yaml
# industry/blueprints/ecommerce-d2c/invariants/ecommerce_invariants.yml

name: E-commerce Invariants
description: Business rules that must always hold

invariants:
  - name: order_total_consistency
    description: Order total must equal sum of items
    check: |
      order.total == sum(order.items.price * order.items.quantity)
    
  - name: inventory_reservation
    description: Inventory must be reserved when order placed
    check: |
      exists(InventoryReservation { order_id == order.id })
    
  - name: payment_before_shipment
    description: Order cannot be shipped before payment
    check: |
      order.status == "shipped" => exists(Payment { order_id == order.id, status == "completed" })
    
  - name: tenant_isolation
    description: Orders are isolated by tenant
    check: |
      order.tenant_id == current_tenant.id
```

---

## E09: Persistent Storage (SQLite + Neo4j)

### SQLite Databases

**Location:** `.midicoder/data/`

#### 1. context.db - Codebase Index

```sql
-- Files table: Indexed source files
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    content_hash TEXT,
    language TEXT,
    size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Symbols table: Extracted symbols (functions, classes, etc.)
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER REFERENCES files(id),
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- function, class, interface, entity
    line_start INTEGER,
    line_end INTEGER,
    signature TEXT,
    description TEXT
);

-- Graphs metadata: Neo4j node references
CREATE TABLE graphs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    node_label TEXT NOT NULL,
    symbol_id INTEGER REFERENCES symbols(id),
    neo4j_node_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_symbols_name ON symbols(name);
CREATE INDEX idx_symbols_type ON symbols(type);
CREATE INDEX idx_files_language ON files(language);
```

#### 2. artifacts.db - Artifacts + Activity Log

```sql
-- Artifacts table
CREATE TABLE artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,
    type TEXT NOT NULL,  -- brief, contract, ir, plan, code
    name TEXT,
    content TEXT,  -- Full content (YAML/JSON/Code)
    content_hash TEXT,
    status TEXT,  -- draft, generated, validated, applied
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity log
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    command TEXT,
    stage TEXT,
    artifact_id INTEGER REFERENCES artifacts(id),
    input_hash TEXT,
    output_hash TEXT,
    duration_ms INTEGER,
    status TEXT,  -- success, failed, partial
    error_message TEXT,
    metadata TEXT  -- JSON blob
);

CREATE INDEX idx_artifacts_version ON artifacts(version);
CREATE INDEX idx_artifacts_type ON artifacts(type);
CREATE INDEX idx_activity_timestamp ON activity_log(timestamp);
```

#### 3. provenance.db - Lineage + Decisions

```sql
-- Lineage table: Artifact → Parent relationships
CREATE TABLE lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id INTEGER REFERENCES artifacts(id),
    parent_artifact_id INTEGER REFERENCES artifacts(id),
    transformation TEXT,  -- analyze, clarify, gen, build
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Decisions table: Decision points and rationales
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id INTEGER REFERENCES artifacts(id),
    decision_point TEXT NOT NULL,
    rationale TEXT,
    source TEXT,  -- user, llm, deterministic
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lineage_artifact ON lineage(artifact_id);
CREATE INDEX idx_lineage_parent ON lineage(parent_artifact_id);
```

#### 4. briefs.db - Brief Library + Clarifications

```sql
-- Briefs table
CREATE TABLE briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,
    type TEXT NOT NULL,  -- working, master, patch, library
    name TEXT,
    content TEXT NOT NULL,
    status TEXT,  -- draft, clarified, frozen, archived
    parent_brief_id INTEGER REFERENCES briefs(id),
    version_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clarification rounds
CREATE TABLE clarifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id INTEGER REFERENCES briefs(id),
    round_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    is_memo INTEGER DEFAULT 0,  -- 1 = memo (highlighted memory)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_briefs_version ON briefs(version);
CREATE INDEX idx_briefs_type ON briefs(type);
CREATE INDEX idx_clarifications_brief ON clarifications(brief_id);
```

### Neo4j Knowledge Graph

**Purpose:** Store codebase semantics as graph for semantic queries.

**Connection:**
- Host: `localhost`
- Port: `7687`
- Auto-start Docker container when connection fails

**Graph Schema (Hybrid: Pre-defined + AST-inferred):**

```cypher
// Pre-defined node labels
(:Entity) - [READS]-> ()
(:Entity) - [WRITTEN_BY]-> (:Command)
(:Command) - [REQUIRES_PERMISSION]-> (:Permission)
(:Command) - [EMITS]-> (:Event)

// Inferred from AST
(:Class) - [EXTENDS]-> (:Class)
(:Class) - [IMPLEMENTS]-> (:Interface)
(:Function) - [CALLS]-> (:Function)
(:Function) - [DEFINED_IN]-> (:Class)
```

**Sync Strategy:** Incremental update (only changed nodes/relationships)

---

## E10: Artifact Contracts

### Artifact Types

| Type | Storage | Format | Purpose |
|------|---------|--------|---------|
| brief | briefs.db | Markdown | Requirements |
| contract | artifacts.db | YAML/JSON | DSL definitions |
| ir | artifacts.db | JSON | MIR |
| plan | artifacts.db | JSON | Implementation plan |
| code | artifacts.db + src/ | Source | Generated code |

### Artifact Metadata

```python
# midicoder/artifacts/metadata.py

class ArtifactMetadata:
    """
    Metadata for tracking artifacts.
    """
    
    def __init__(
        self,
        artifact_id: int,
        version: str,
        type: str,
        name: str,
        content_hash: str,
        status: str,
        created_at: datetime,
        updated_at: datetime,
        parent_artifact_id: int = None,
        transformation: str = None
    ):
        self.artifact_id = artifact_id
        self.version = version
        self.type = type
        self.name = name
        self.content_hash = content_hash
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.parent_artifact_id = parent_artifact_id
        self.transformation = transformation
```

### Hash Determinism

```python
# midicoder/utils/determinism.py

import hashlib
from pathlib import Path

def compute_content_hash(content: str) -> str:
    """Tính hash SHA-256 của nội dung."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def compute_file_hash(file_path: Path) -> str:
    """Tính hash của file."""
    content = file_path.read_text(encoding='utf-8')
    return compute_content_hash(content)

def compute_dir_hash(dir_path: Path, exclude: list[str] = None) -> str:
    """Tính hash của thư mục (files sorted)."""
    exclude = exclude or ['.git', 'node_modules', '__pycache__']
    
    file_hashes = []
    
    for root, dirs, files in os.walk(dir_path):
        dirs[:] = [d for d in dirs if d not in exclude]
        
        for file in sorted(files):
            file_path = Path(root) / file
            rel_path = file_path.relative_to(dir_path)
            file_hash = compute_file_hash(file_path)
            file_hashes.append(f"{rel_path}:{file_hash}")
    
    file_hashes.sort()
    
    return compute_content_hash('\n'.join(file_hashes))

def verify_determinism(artifact_path: Path, expected_hash: str) -> bool:
    """Verify artifact hash matches expected."""
    actual_hash = compute_file_hash(artifact_path)
    return actual_hash == expected_hash
```

---

## E11: DSL v1 Kernel Architecture

*(See E03: Capability Language Specification)*

---

## E12: Core Compiler Packs (CP01-CP30)

### CP01: Domain Model DSL

- Entity definitions
- Relationships (one-to-one, one-to-many, many-to-many)
- Field types and constraints
- Lifecycle hooks

### CP02: Multi-Tenant Architecture

- Tenant isolation strategies (database, schema, row-level)
- Tenant context propagation
- Tenant-scoped queries
- Cross-tenant operations (controlled)

### CP03: Authentication & Authorization

- JWT authentication
- OAuth2 integration
- Permission-based authorization
- Role-based access control (RBAC)

### CP04: RBAC & Policy Engine

- Role definitions
- Permission bindings
- Policy evaluation (OPA-compatible)
- Access control lists (ACL)

### CP05: Event-Driven Architecture

- Event definitions
- Event publishers/subscribers
- Event schemas
- Message queue integration

### CP06: API Gateway & Service Mesh

- Gateway configuration
- Route definitions
- Rate limiting
- Circuit breakers

### CP07: Infrastructure as Code

- Docker Compose generation
- Terraform modules
- Environment configurations

### CP08: Database & Data Access

- SQLAlchemy models
- Repository pattern
- Migration scripts
- Connection pooling

### CP09: Caching & Performance

- Redis integration
- Cache strategies (write-through, read-through)
- Cache invalidation
- CDN configuration

### CP10: Search & Indexing

- Elasticsearch integration
- Index definitions
- Search queries
- Full-text search

### CP11: File Storage & Media

- S3-compatible storage
- Image processing
- File uploads/downloads
- CDN integration

### CP12: Notification & Communication

- Email templates
- SMS integration
- Push notifications
- In-app notifications

### CP13: Background Job & Workflow

- Celery/worker integration
- Job queues
- Workflow definitions
- Retry logic

### CP14: Audit Trail & Compliance

- Audit logging
- Immutable logs
- Compliance reports
- Data retention policies

### CP15: Observability Stack

- Prometheus metrics
- Grafana dashboards
- Distributed tracing
- Log aggregation

### CP16-CP30: Additional Packs

*(To be defined per phase priority)*

---

## E13: Domain Packs (DP01-DP26)

### DP01: E-commerce

- Product catalog
- Shopping cart
- Order management
- Payment processing
- Inventory management

### DP02: Marketplace B2C

- Multi-vendor support
- Commission management
- Vendor dashboards
- Split payments

### DP03: Banking Core

- Account management
- Transaction processing
- Double-entry bookkeeping
- KYC/AML compliance

### DP04-DP26: Additional Domains

*(Defined per industry blueprints)*

---

## E14: Regulatory Overlays (RX01-RX12)

### RX01: GDPR

- Data subject rights
- Right to be forgotten
- Data portability
- Consent management

### RX02: HIPAA

- Protected health information (PHI)
- Access controls
- Audit trails
- Encryption requirements

### RX03: PCI-DSS

- Card data protection
- Secure payment processing
- Network segmentation
- Regular audits

### RX04-RX12: Additional Regulations

*(Defined per industry requirements)*

---

## E15: Invariant Gates & Verification

### Invariant Types

1. **Business Invariants:**
   - Order total consistency
   - Inventory constraints
   - Payment before shipment

2. **Security Invariants:**
   - Authentication required
   - Authorization enforced
   - Input validation

3. **Data Integrity Invariants:**
   - Referential integrity
   - Unique constraints
   - Not-null constraints

### Verification Process

```
1. Parse invariants from YAML
2. Generate verification queries
3. Run queries against generated code
4. Report violations as compilation errors
5. Block code generation if critical violations
```

---

## E16: 100 Industry Blueprints

*(See industry/blueprints/ directory)*

Blueprints cover 100 industries, each with:
- Blueprint definition
- Sample brief
- DSL contracts
- Invariants

---

## E17: Top 20 Priority Industries

*(See industry/priority-top20.yml)*

Priority industries for initial release:
1. E-commerce D2C
2. Marketplace B2C
3. Banking Core
4. ...

---

## E18: Target Support (Local + AWS)

### Local (Docker Compose)

- Backend (FastAPI/NestJS)
- Frontend (Angular/React)
- Database (PostgreSQL)
- Cache (Redis)
- Graph DB (Neo4j)

### AWS (Terraform)

- API (ECS/Elastic Beanstalk)
- Database (RDS/Aurora)
- Cache (ElastiCache)
- Graph DB (Neo4j Aura)
- Storage (S3)

---

## E19: Web Fullstack Generation

### Backend

- FastAPI/Python
- NestJS/TypeScript

### Frontend

- Angular/TypeScript
- React/TypeScript

### Communication

- REST API
- GraphQL
- gRPC
- WebSocket

---

## E20: CLI Commands

### Global Flags

```
midicoder [GLOBAL-FLAGS] <COMMAND> [SUBCOMMAND] [OPTIONS] [ARGUMENTS]

GLOBAL FLAGS:
  --version          Show version
  --help, -h         Show help
  --debug            Enable debug mode
  --quiet            Suppress output
  --json             Output as JSON
  --config PATH      Custom config file
  --project PATH     Project directory
```

### Phase 0: Initialization Commands

#### `midicoder init`

```bash
midicoder init [OPTIONS]

OPTIONS:
  --force            Overwrite existing .midicoder/
  --no-index         Skip codebase indexing
  --version VERSION  Initial version (default: v1.0.0)

EXAMPLES:
  midicoder init
  midicoder init --force --version v1.0.0
```

**Output:**
- `.midicoder/` directory structure
- SQLite databases initialized
- Neo4j Docker container started
- WebGUI started

**Exit Codes:**
- 0: Success
- 1: Already initialized (without --force)

#### `midicoder version create`

```bash
midicoder version create --name v1.0.1 [--from v1.0.0] [--message "Add payments"]
```

#### `midicoder version use`

```bash
midicoder version use v1.0.1
```

#### `midicoder version list`

```bash
midicoder version list
```

#### `midicoder index`

```bash
midicoder index [OPTIONS]

OPTIONS:
  --force            Rebuild entire index
  --watch            Watch for file changes
```

### Phase 1: Brief Commands

#### `midicoder brief analyze`

```bash
midicoder brief analyze [OPTIONS] [FILE]

OPTIONS:
  --file, -f FILE     Brief file
  --domain DOMAIN     Specify domain

EXAMPLES:
  midicoder brief analyze
  midicoder brief analyze -f my-brief.md
  midicoder brief analyze <<< "Build an e-commerce platform..."
```

#### `midicoder brief clarify`

```bash
midicoder brief clarify [OPTIONS]

OPTIONS:
  --max-rounds N       Max clarification rounds (default: 10)
```

#### `midicoder brief save`

```bash
midicoder brief save --name "ecommerce-d2c" --tags "ecommerce,retail"
```

#### `midicoder brief load`

```bash
midicoder brief load ecommerce-d2c
```

#### `midicoder brief list`

```bash
midicoder brief list [--domain finance]
```

### Phase 2: Contract Commands

#### `midicoder contract gen`

```bash
midicoder contract gen [OPTIONS]

OPTIONS:
  --force            Regenerate even if exists
  --interactive      Review and edit before saving
```

#### `midicoder contract check`

```bash
midicoder contract check [OPTIONS]

OPTIONS:
  --auto-fix         Attempt to fix errors automatically
  --strict           Treat warnings as errors
```

### Phase 3: IR Commands

#### `midicoder ir build`

```bash
midicoder ir build [OPTIONS]

OPTIONS:
  --verbose          Verbose output
  --check-only       Validate without generating
```

### Phase 4: Code Commands

#### `midicoder code plan`

```bash
midicoder code plan [OPTIONS]

OPTIONS:
  --target TARGET    backend | frontend | all
  --verbose          Show plan details
```

#### `midicoder code gen`

```bash
midicoder code gen [OPTIONS]

OPTIONS:
  --target TARGET    backend | frontend | all
  --dry-run         Generate but don't save
```

#### `midicoder code apply`

```bash
midicoder code apply [OPTIONS]

OPTIONS:
  --target-dir DIR  Target directory
  --dry-run         Show what would be applied
  --backup          Create backups
  --force           Overwrite without prompt
```

### Phase 5: Preview & Feedback

#### `midicoder preview`

```bash
midicoder preview [start|stop|restart|status] [OPTIONS]

OPTIONS:
  --port PORT       Frontend port (default: 7272)
  --no-browser      Don't open browser
```

#### `midicoder feedback`

```bash
midicoder feedback [OPTIONS]

OPTIONS:
  --type TYPE       bug | enhancement | clarification
  --no-auto-apply   Don't auto-trigger pipeline
  --message MSG     Feedback message
```

### Utility Commands

#### `midicoder config`

```bash
midicoder config show
midicoder config set <key> <value>
midicoder config reset [key]
```

#### `midicoder status`

```bash
midicoder status [--json]
```

#### `midicoder help`

```bash
midicoder help [COMMAND]
```

---

## E21: MCP Server Tools

### Server Configuration

- **Transport:** SSE/HTTP
- **Host:** localhost
- **Port:** 2026
- **Start:** On-demand (when LLM stage needed)

### Tool Categories

| Category | Tools | Purpose |
|----------|-------|---------|
| DSL Schema | get_dsl_schema, get_dsl_section | Learn DSL syntax |
| Capabilities | list_core_capabilities, get_core_capability | Explore operations |
| Macros | list_macro_patterns, get_macro_pattern | See patterns |
| Compiler | compile_contracts, validate_capability_graph | Compile & validate |
| SQLite | get_active_brief, get_clarifications, list_artifacts | Query runtime state |
| Context | get_project_context, list_symbols | Access codebase |
| Templates | get_industry_template | Get industry starters |

### DSL Schema Tools

```python
# Get full DSL schema
get_dsl_schema(section: "all"|"entities"|"commands"|"queries"|"events")

# Get specific section
get_dsl_section(section: str)
```

### Capabilities Tools

```python
# List all core capabilities (name + short description)
list_core_capabilities() -> list[{name: str, description: str}]

# Get detailed capability syntax
get_core_capability(name: str) -> {
  name: str,
  description: str,
  params_schema: dict,
  obligations: list,
  example: str
}
```

### Macros Tools

```python
# List all macro patterns
list_macro_patterns() -> list[{name: str, description: str}]

# Get detailed macro expansion
get_macro_pattern(name: str) -> {
  name: str,
  description: str,
  expands_to: list[str],
  example: str
}
```

### Compiler Tools

```python
# Compile DSL contracts to CapabilityGraph
compile_contracts(contracts_path: str) -> {
  success: bool,
  errors: list[{
    line: int,
    column: int,
    file: str,
    error_code: str,
    message: str,
    suggestion: str
  }],
  graph_path: str  # If successful
}

# Validate compiled CapabilityGraph
validate_capability_graph(graph_path: str) -> {
  valid: bool,
  warnings: list[str]
}
```

### SQLite Access Tools

```python
# Get active brief
get_active_brief(version: str = None, type: "working"|"master") -> {
  brief_id: int,
  version: str,
  type: str,
  content: str,
  status: str
}

# Get clarification Q&A
get_clarifications(brief_id: int) -> list[{
  round: int,
  question: str,
  answer: str,
  is_memo: bool
}]

# Get memos only (highlighted memories)
get_memos(version: str) -> list[{
  question: str,
  answer: str
}]

# List artifacts
list_artifacts(version: str, type: str = None) -> list[{
  artifact_id: int,
  type: str,
  name: str,
  status: str,
  created_at: str
}]
```

### Context Tools

```python
# Query codebase context (hybrid: structural + semantic)
get_project_context(query: str, limit: int = 10, type: str = None) -> list[{
  name: str,
  type: str,
  signature: str,
  description: str,
  file_path: str
}]

# List symbols
list_symbols(type: str = None, limit: int = 50) -> {
  total_symbols: int,
  by_type: dict,
  symbols: list[...]
}
```

### Templates Tools

```python
# Get industry-specific DSL template
get_industry_template(industry: str) -> {
  description: str,
  dsl: {
    entities: str,
    commands: str,
    queries: str,
    events: str
  },
  obligations: list[str]
}
```

### LLM Agent Workflow with MCP

```
┌─────────────────────────────────────────────────────────────────┐
│ LLM AGENT: Contract Generation Workflow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 1. LEARN DSL                                                     │
│    → Call get_dsl_schema("all")                                  │
│    → Call get_dsl_schema("entities")                             │
│    → Call get_dsl_schema("commands")                             │
│                                                                  │
│ 2. EXPLORE CAPABILITIES                                          │
│    → Call list_core_capabilities()                               │
│    → Call get_core_capability("authorized_mutation")             │
│    → Call list_macro_patterns()                                  │
│                                                                  │
│ 3. GET CONTEXT (if exists)                                       │
│    → Call get_active_brief(type="master")                        │
│    → Call get_clarifications()                                   │
│    → Call get_memos()  ← Highlighted memories                    │
│    → Call list_symbols(type="entity")                            │
│                                                                  │
│ 4. GET TEMPLATE (optional)                                       │
│    → Call get_industry_template(industry="ecommerce")            │
│                                                                  │
│ 5. GENERATE DSL                                                  │
│    → Write contracts/entities.yml                                │
│    → Write commands/commands.yml                                 │
│    → Write contracts/queries.yml                                 │
│    → Write contracts/events.yml                                  │
│                                                                  │
│ 6. COMPILE & FIX (Iterative)                                     │
│    → Call compile_contracts(contracts_path="contracts/")         │
│    → IF errors:                                                  │
│       - READ each error message                                  │
│       - USE suggestion to fix                                    │
│       - MODIFY specific files                                    │
│       - Call compile_contracts AGAIN                             │
│    → REPEAT until success (max 10 iterations)                    │
│                                                                  │
│ 7. FINAL VALIDATION                                              │
│    → Call validate_capability_graph(graph_path="...")            │
│    → IF passed: SUCCESS!                                         │
│    → IF failed: Fix and retry                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## E22: Non-Functional Requirements

### Performance

- Brief → Contract: < 5 minutes (with LLM)
- Contract → Code: < 2 minutes (deterministic)
- Full pipeline: < 15 minutes
- LLM budget: < 50,000 tokens per initial generation

### Quality

- Generated code passes all linting rules
- No syntax errors in generated code
- Generated contracts validate against DSL schema
- 100% deterministic (same input → same output)

### Security

- All APIs authenticated and authorized
- Tenant isolation enforced
- No hardcoded secrets
- Input validation on all endpoints

### Reliability

- Error handling for all failure cases
- Retry logic for transient failures
- Idempotent operations where applicable

### Observability

- Structured logging
- Metrics for key operations
- Health checks for all services

---

## E23: Acceptance Criteria

### Must Have (v1.0.0)

- ✅ 100 industry blueprints defined
- ✅ Core compiler packs CP01-CP15 implemented
- ✅ CLI commands for full pipeline
- ✅ MCP server with all tools
- ✅ SQLite persistence
- ✅ Neo4j knowledge graph integration
- ✅ WebGUI (FastAPI + Angular)
- ✅ Docker Compose scaffolding

### Should Have

- ⚠️ AWS Terraform scaffolding
- ⚠️ Additional domain packs
- ⚠️ Regulatory overlays

### Nice to Have

- 🔮 React frontend template
- 🔮 NestJS backend template
- 🔮 Advanced caching strategies

---

## E99: Technical Engineering Decisions

### Decision 1: SQLite for Persistent Storage

**Reason:** Queryable, ACID compliance, zero-config, portable, local-first.

### Decision 2: Context Injection Only in LLM Stages

**Reason:** Preserve determinism in non-LLM stages (ir build, code plan, code gen).

### Decision 3: SQLite Primary for Briefs, MD Optional

**Reason:** Queryable across versions, lineage tracking, MCP access, optional MD export for readability.

### Decision 4: MCP Server with SSE/HTTP Transport

**Reason:** Supports local development with localhost, enables on-demand start.

### Decision 5: Two-Mode UI (WebGUI + CLI)

**Reason:** WebGUI for desktop users, CLI for remote/server users, both sync via SQLite.

### Decision 6: Determinism Guarantees

**Reason:** Same input → same output for reproducibility and debugging.

### Decision 7: Neo4j for Knowledge Graph

**Reason:** Native graph queries, semantic relationships, hybrid AST-based schema.

### Decision 8: Local Docker for Neo4j

**Reason:** No external dependency, auto-start on connect failed, consistent with local-first philosophy.

### Decision 9: Full State per Version

**Reason:** Self-contained versions, no merge complexity, easier to reason about.

### Decision 10: Auto-Cleanup with Confirmation

**Reason:** Prevent disk bloat, respect user intent with confirmation for non-archived versions.

---

**End of Requirement Document**

**Last Updated:** 2026-04-21

**Version:** 1.0.0

**Status:** Single Source of Truth (Self-Contained)