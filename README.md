![midicoder](midicoder-repo-cover.png)

# Midicoder

**Stop vibe coding. Start contract coding.**

Midicoder là một công cụ **AI coding pipeline mã nguồn mở** giúp biến ý tưởng sản phẩm thành code **một cách có cấu trúc, deterministic và reviewable**.

Thay vì để AI "đoán" code từ prompt và rewrite cả file, Midicoder vận hành theo triết lý:

> **Code được sinh ra từ contract, không phải từ vibe.**

---

# 🇻🇳 Built by Vietnamese engineers

Midicoder được xây dựng và phát triển bởi **đội ngũ kỹ sư Việt Nam**, với mục tiêu tạo ra một cách tiếp cận mới cho AI-assisted development:

- minh bạch
- deterministic
- production-ready

Chúng tôi tin rằng AI không nên thay thế engineering discipline.

AI nên **khuếch đại engineering discipline**.

---

# Vì sao Midicoder tồn tại?

Làn sóng **vibe coding** đang rất phổ biến:

- prompt
- AI viết code
- sửa
- prompt lại

Nhưng với codebase lớn, cách này nhanh chóng trở nên:

- khó kiểm soát
- khó review
- khó maintain
- khó reproduce

Midicoder đưa ra một hướng tiếp cận khác:

## Contract Coding

> Xem tài liệu chi tiết tại đây: [docs.midicoder.com](https://docs.midicoder.com)

Trước khi code được sinh ra, hệ thống sẽ tạo ra một **bộ contract DSL** mô tả:

- domain
- commands
- workflows
- API
- policy

Contract trở thành **source of truth** cho toàn bộ pipeline.

---

# Cài đặt

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://midicoder.com/releases/{version}/install.ps1 | iex"
```

### macOS / Linux

```bash
curl -o- https://midicoder.com/releases/{version}/install.sh | bash
```

Sau khi cài đặt, kiểm tra:

```bash
midicoder --version
```

Chạy ứng dụng:

```bash
midicoder
```

Midicoder sẽ khởi động **4 servers** tự động và mở browser:

| Service | Port | URL |
|---------|------|-----|
| Backend (FastAPI) | 6868 | http://localhost:6868 |
| Frontend (Angular) | 7272 | http://localhost:7272 |
| SQLite Viewer (Datasette) | 8080 | http://localhost:8080 |
| MCP Server (uvicorn) | 7878 | http://localhost:7878 |

> **MCP Server** cung cấp 14 tools cho LLM agent tự query DSL schema, validate contracts, cross-check references, và truy vấn SQLite — dùng trong contract generation pipeline.

---

# Midicoder pipeline

Midicoder hoạt động như một **AI coding pipeline** gồm nhiều stage rõ ràng:

```
master brief
      ↓
contracts (DSL)
      ↓
IR (deterministic)
      ↓
code plans
      ↓
patch plans
      ↓
apply patches
```

Điều này mang lại:

- reproducibility
- auditability
- diff rõ ràng
- dễ review

AI không bao giờ ghi file trực tiếp.

AI chỉ:

- sinh DSL
- đề xuất patch

CE sẽ thực thi patch một cách an toàn.

---

# Những nguyên tắc cốt lõi

## Contract‑first

Contract DSL là **source of truth**.

## Deterministic pipeline

Các bước compile (contracts → IR → plans) **không phụ thuộc LLM**.

## Patch‑based generation

Midicoder không rewrite file.

Nó tạo **patch nhỏ có anchor**, giúp review và rollback dễ dàng.

## Artifact‑driven

Mọi bước đều tạo artifact:

```
.midicoder/
```

Bạn có thể audit toàn bộ pipeline.

---

# Midicoder không phải là AI chat

Midicoder không phải là:

- Copilot
- Cursor
- ChatGPT coding

Midicoder là:

> **AI software engineering pipeline**

---

# Khi nào nên dùng Midicoder

Midicoder phù hợp khi:

- bạn build backend system
- bạn cần maintain codebase lớn
- bạn muốn AI nhưng vẫn giữ engineering discipline

Không phù hợp khi:

- bạn chỉ viết script nhỏ
- prototype nhanh

---

# Triết lý

```
vibe coding → fun
contract coding → ships
```

---

# Developing Workflow

## Yêu cầu hệ thống

- **Python 3.12.x** (bắt buộc — không hỗ trợ 3.11 hoặc 3.13+)
- **Node.js 18+** (cho Angular build)
- **uv** (recommended, cho quản lý virtual environment)

## Setup môi trường phát triển

```bash
# 1. Clone repository
git clone https://github.com/hemidi-jsc/midicoder-ce.git
cd midicoder-ce

# 2. Tạo virtual environment (dùng uv)
uv venv --python 3.12
source .venv/bin/activate  # Linux/macOS
# hoặc: .venv\Scripts\activate  # Windows

# 3. Cài đặt dependencies
uv pip install -e ".[dev]"

# 4. Cài đặt dependencies cho Angular frontend
cd webgui && npm install && cd ..
```

## Chạy trong chế độ phát triển

Midicoder hoạt động với 3 server song song. Trong chế độ dev, chạy mỗi server riêng biệt để tận dụng hot-reload:

### Terminal 1 — Backend (FastAPI)

```bash
# API server tự động reload khi file .py thay đổi
uvicorn midicoder.api.main:server --host 0.0.0.0 --port 6868 --reload
```

### Terminal 2 — Frontend (Angular)

```bash
cd webgui
ng serve --port 7272
# Angular dev server tự động proxy API requests đến backend:
#   /api/*  →  http://localhost:6868/api/*
#   /ws/*   →  ws://localhost:6868/ws/*
```

### Terminal 3 — SQLite Viewer (Datasette) — Optional

```bash
datasette ~/.midicoder/data --port 8080 --host 0.0.0.0 --cors
```

Mở browser tại:
- **Frontend:** http://localhost:7272
- **Backend API:** http://localhost:6868/docs (Swagger UI)
- **MCP Server:** http://localhost:7878/tools (list tools)
- **SQLite Viewer:** http://localhost:8080

> **Lưu ý:** Angular dev server (`ng serve`) proxy API requests về backend tự động. Bạn truy cập frontend là đủ, không cần mở backend tab riêng.

### Terminal 4 — MCP Server (uvicorn) — Optional

```bash
# MCP server — cung cấp 14 tools cho LLM agent (watch mode)
uvicorn midicoder.mcp.server:app --host 0.0.0.0 --port 7878 --reload
```

MCP Server expose **14 tools** trong 6 groups, dùng cho LLM self-validation trong contract generation pipeline:

| Group | Tools | Mô tả |
|-------|-------|-------|
| **MCP-B: DSL Schema** | `get_dsl_schema`, `get_dsl_section` | LLM dùng để học DSL syntax trước khi generate |
| **MCP-C: Packs** | `list_packs`, `get_pack` | Xem examples definitions/recipes của packs |
| **MCP-D: Compiler** | `compile_contracts`, `validate_capability_graph` | Trigger compile + kiểm tra capability graph |
| **MCP-E: SQLite** | `get_active_brief`, `get_clarifications`, `list_artifacts` | Truy vấn dữ liệu từ SQLite databases |
| **MCP-F: Context** | `get_project_context`, `list_symbols` | Project context + symbols đã generate |
| **MCP-G: Validation** | `validate_contract_yaml`, `cross_check_category`, `get_generated_artifact` | LLM self-validate contracts realtime |

**Test MCP endpoints:**

```bash
# Health check
curl http://localhost:7878/health

# List tất cả tools
curl http://localhost:7878/tools

# Gọi tool — lấy DSL schema
curl -X POST http://localhost:7878/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_dsl_section", "arguments": {"section": "entities"}}'
```

> Trong production (launcher), MCP server tự động khởi động ở port 7878 và không cần start thủ công.

## Cấu trúc dự án

```
midicoder-ce/
├── midicoder/                 # Python package chính
│   ├── __main__.py            # Entry point
│   ├── launcher.py            # WebGUI launcher (start 4 servers)
│   ├── spa_serve.py           # SPA static server (stdlib-only)
│   ├── api/                   # FastAPI backend
│   │   ├── main.py            # ASGI app
│   │   └── routers/           # API endpoints
│   ├── mcp/                   # MCP Server (uvicorn + Starlette, 14 tools)
│   │   ├── server.py          # ASGI app (port 7878)
│   │   └── tools/             # Tool registry
│   │       ├── dsl_schema.py  # MCP-B: get_dsl_schema, get_dsl_section
│   │       ├── packs.py       # MCP-C: list_packs, get_pack
│   │       ├── compiler.py    # MCP-D: compile_contracts, validate_capability_graph
│   │       ├── sqlite_tools.py # MCP-E: get_active_brief, get_clarifications, list_artifacts
│   │       ├── context.py     # MCP-F: get_project_context, list_symbols
│   │       └── contract_validation.py # MCP-G: validate, cross_check, get_artifact
│   ├── pipeline/              # Pipeline logic
│   ├── frontend/              # Angular dist (build artifact, trong .gitignore)
│   ├── packs/                 # Capability packs
│   └── storage/               # SQLite storage layer
├── webgui/                    # Angular SPA frontend
│   ├── src/
│   └── angular.json
├── scripts/
│   ├── build-win.ps1          # Build binary cho Windows
│   ├── build-linux.sh         # Build binary cho Linux/macOS
│   ├── install/
│   │   ├── install.sh         # Install script (Linux/macOS)
│   │   └── install.ps1        # Install script (Windows)
│   └── hooks/                 # PyInstaller hooks
├── midicoder.spec             # PyInstaller spec file
└── pyproject.toml
```

## Linting & Testing

```bash
# Lint Python code
ruff check midicoder/

# Format Python code
ruff format midicoder/

# Chạy test
pytest midicoder/tests/

# Lint + build Angular
cd webgui && ng lint && ng build --configuration=production
```

---

# Build Binary Release

Midicoder được đóng gói thành **standalone binary** bằng PyInstaller — người dùng cuối không cần cài đặt Python, Node.js, hay bất kỳ dependency nào.

## Binary bundling structure

Thành phần được bundle vào binary:

| Component | Status | Ghi chú |
|-----------|--------|---------|
| Python 3.12.x runtime | ✅ Bundled | Locked từ `.venv` |
| FastAPI + uvicorn | ✅ Bundled | Auto-discovered |
| tree_sitter (native .pyd/.so) | ✅ Bundled | UPX exclude patterns |
| Datasette (SQLite viewer) | ✅ Bundled | Templates + static assets |
| Angular SPA dist | ✅ Bundled | Build tại release time |
| Node.js | ❌ | Chỉ cần khi build Angular |

## Build trên Windows

```powershell
# Prerequisites: .venv với Python 3.12.x + Node.js
.\scripts\build-win.ps1
```

Script tự động thực hiện:
1. Build Angular (`npx ng build --configuration=production`)
2. Copy dist → `midicoder/frontend/`
3. Build PyInstaller từ `midicoder.spec`
4. Package thành `midicoder-windows-bin.zip`
5. Cleanup `midicoder/frontend/`

Output: `dist/windows/midicoder.exe` (~150-250MB)

## Build trên Linux/macOS

```bash
# Prerequisites: .venv với Python 3.12.x + Node.js
./scripts/build-linux.sh
```

Quy trình tương tự Windows. Output: `dist/linux/midicoder` + `midicoder-linux-bin.tar.gz`

## Build thủ công

```bash
# 1. Build Angular
cd webgui && npx ng build --configuration=production && cd ..

# 2. Copy dist vào package
rm -rf midicoder/frontend
mkdir -p midicoder/frontend
cp -r webgui/dist/webgui/browser/* midicoder/frontend/
touch midicoder/frontend/__init__.py

# 3. Build PyInstaller
.venv/bin/python -m PyInstaller --clean midicoder.spec

# 4. Cleanup
rm -rf midicoder/frontend
```

> **Quan trọng:** `midicoder/frontend/` là build artifact — KHÔNG commit vào git.
> File này được thêm vào `.gitignore` và build script tự động tạo/xóa khi build.

## Verify binary

```bash
# Kiểm tra version
./dist/midicoder --version

# Chạy binary — sẽ start 3 servers + mở browser
./dist/midicoder

# Kiểm tra các port đang hoạt động
curl http://localhost:6868/api/pipeline/status  # Backend
curl http://localhost:7272/ | head -5           # Frontend
curl http://localhost:8080/                     # Datasette
```

---

# Tầm nhìn

Chúng tôi tin rằng thế hệ tiếp theo của AI coding sẽ không chỉ là:

"chat với AI"

mà là:

> **AI‑native software engineering pipelines**

Midicoder là một bước đầu tiên.

---

# Open Source

Midicoder là **open source**.

Chúng tôi chào đón mọi đóng góp từ cộng đồng developer.

Đặc biệt là cộng đồng **engineer Việt Nam**.

---

# Một ý tưởng từ Việt Nam

Midicoder được tạo ra bởi một nhóm kỹ sư Việt Nam với mong muốn:

> Việt Nam không chỉ là nơi gia công phần mềm.

> Việt Nam có thể tạo ra **những ý tưởng engineering mới cho thế giới**.

Nếu bạn thấy ý tưởng này thú vị, hãy ⭐ repository.
