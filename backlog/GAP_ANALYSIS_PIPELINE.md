# Gap Analysis: pipeline-plan.md vs requirement.md

**Created:** 2026-04-21
**Purpose:** Identify gaps between original pipeline-plan architecture and current requirement.md (SoT)
**Goal:** Ensure requirement.md is self-contained and complete

---

## Executive Summary

| Category            | Status     | Priority | Notes                                                        |
| ------------------- | ---------- | -------- | ------------------------------------------------------------ |
| CLI Commands        | ❌ Missing | P0       | 14 commands defined in pipeline-plan, missing in requirement |
| Directory Structure | ⚠️ Partial | P1       | .midicoder/ structure exists but incomplete                  |
| SQLite Schemas      | ❌ Missing | P0       | 4 database schemas not defined                               |
| Brief.md Scope      | ❌ Missing | P0       | Critical: working-brief vs master-brief vs patches           |
| Version Management  | ❌ Missing | P1       | version create/use commands not defined                      |
| LLM Budget          | ⚠️ Partial | P2       | Budget analysis exists but not integrated                    |
| Artifacts Tracking  | ⚠️ Partial | P1       | Some artifacts defined, lineage tracking missing             |

---

## Gap 1: CLI Commands (P0 - CRITICAL)

### Current State in requirement.md

- Section E20: CLI Commands only defines 2 commands (`brief analyze`, `brief rewrite`)
- Missing 12+ critical commands

### Required Commands from pipeline-plan

#### Phase 0: Initialization Commands

| Command                    | Pipeline-Plan Status | Requirement.md Status | Priority |
| -------------------------- | -------------------- | --------------------- | -------- |
| `midicoder init`           | ✅ Detailed spec     | ❌ Missing            | P0       |
| `midicoder version create` | ✅ Detailed spec     | ❌ Missing            | P1       |
| `midicoder version use`    | ✅ Detailed spec     | ❌ Missing            | P1       |
| `midicoder index`          | ✅ Detailed spec     | ❌ Missing            | P0       |

#### Phase 1: Brief Commands

| Command                   | Pipeline-Plan Status | Requirement.md Status | Priority |
| ------------------------- | -------------------- | --------------------- | -------- |
| `midicoder brief analyze` | ✅ Detailed spec     | ⚠️ Partial (E20-001)  | P0       |
| `midicoder brief clarify` | ✅ Detailed spec     | ❌ Missing            | P0       |
| `midicoder brief save`    | ✅ Detailed spec     | ❌ Missing            | P1       |
| `midicoder brief load`    | ✅ Detailed spec     | ❌ Missing            | P1       |
| `midicoder brief list`    | ✅ Detailed spec     | ❌ Missing            | P2       |

#### Phase 2: Contract Commands

| Command                    | Pipeline-Plan Status | Requirement.md Status | Priority |
| -------------------------- | -------------------- | --------------------- | -------- |
| `midicoder contract gen`   | ✅ Detailed spec     | ⚠️ Partial (E20-005)  | P0       |
| `midicoder contract check` | ✅ Detailed spec     | ❌ Missing            | P0       |

#### Phase 3: IR Commands

| Command              | Pipeline-Plan Status | Requirement.md Status | Priority |
| -------------------- | -------------------- | --------------------- | -------- |
| `midicoder ir build` | ✅ Detailed spec     | ❌ Missing            | P0       |

#### Phase 4: Code Commands

| Command                | Pipeline-Plan Status | Requirement.md Status | Priority |
| ---------------------- | -------------------- | --------------------- | -------- |
| `midicoder code plan`  | ✅ Detailed spec     | ❌ Missing            | P0       |
| `midicoder code gen`   | ✅ Detailed spec     | ❌ Missing            | P0       |
| `midicoder code apply` | ✅ Detailed spec     | ❌ Missing            | P0       |

#### Phase 5: Preview & Feedback Commands

| Command              | Pipeline-Plan Status | Requirement.md Status | Priority |
| -------------------- | -------------------- | --------------------- | -------- |
| `midicoder preview`  | ✅ Detailed spec     | ❌ Missing            | P1       |
| `midicoder feedback` | ✅ Detailed spec     | ❌ Missing            | P0       |

### Recommended Action

**Add Section E20:** Comprehensive CLI Commands with:

- Command signatures
- Input/output artifacts
- Exit codes
- LLM usage indicators
- Example usage

---

## Gap 2: SQLite Database Schemas (P0 - CRITICAL)

### Current State in requirement.md

- No SQLite schema definitions
- No persistent storage strategy for runtime state

### Required Schemas from pipeline-plan

#### 1. context.db - Codebase Index

```sql
-- Files table: Indexed source files
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE,
    content_hash TEXT,
    language TEXT,
    size_bytes INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Symbols table: Extracted symbols (functions, classes, etc.)
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id),
    name TEXT,
    type TEXT,  -- function, class, interface, etc.
    line_start INTEGER,
    line_end INTEGER,
    signature TEXT,
    description TEXT
);

-- Embeddings table: Semantic search vectors
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id),
    chunk_index INTEGER,
    embedding_vector VECTOR(384),
    content_preview TEXT,
    UNIQUE(file_id, chunk_index)
);

CREATE INDEX idx_symbols_name ON symbols(name);
CREATE INDEX idx_symbols_type ON symbols(type);
CREATE INDEX idx_files_language ON files(language);
```

#### 2. artifacts.db - Generated Artifacts Tracking

```sql
CREATE TABLE artifacts (
    id INTEGER PRIMARY KEY,
    version TEXT,
    type TEXT,  -- brief, contract, ir, code
    name TEXT,
    path TEXT,
    created_at TIMESTAMP,
    status TEXT  -- draft, generated, validated, applied
);

CREATE INDEX idx_artifacts_version ON artifacts(version);
CREATE INDEX idx_artifacts_type ON artifacts(type);
```

#### 3. provenance.db - Lineage Tracking

```sql
-- Lineage table: Artifact → Parent artifact relationships
CREATE TABLE lineage (
    id INTEGER PRIMARY KEY,
    artifact_id INTEGER REFERENCES artifacts(id),
    parent_artifact_id INTEGER REFERENCES artifacts(id),
    transformation TEXT,  -- analyze, clarify, gen, build, etc.
    created_at TIMESTAMP
);

-- Decisions table: Decision points and rationales
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    artifact_id INTEGER REFERENCES artifacts(id),
    decision_point TEXT,
    rationale TEXT,
    source TEXT  -- user, llm, deterministic
);
```

#### 4. index.db - Brief Library

```sql
CREATE TABLE briefs (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    path TEXT,
    version TEXT,
    domain TEXT,
    tags TEXT[],  -- JSON array
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

CREATE INDEX idx_briefs_domain ON briefs(domain);
CREATE INDEX idx_briefs_version ON briefs(version);
```

### Recommended Action

**Add Section E09:** Persistent Storage with:

- Database schema definitions
- Migration strategies
- Index update mechanisms (hybrid: structural + semantic)

---

## Gap 3: Brief.md Scope Definition (P0 - CRITICAL)

### Current State in requirement.md

- brief.md mentioned but scope unclear
- No distinction between working-brief, master-brief, patch-briefs

### Required Clarification from pipeline-plan

#### Brief Types

| Type                  | Purpose                     | When Created          | Mutability                          |
| --------------------- | --------------------------- | --------------------- | ----------------------------------- |
| `working-brief.md`    | Brief đang được phân tích   | After `brief analyze` | Mutable (updated during clarify)    |
| `master-brief.md`     | Brief đã clarify hoàn chỉnh | After `brief clarify` | Immutable (frozen for contract gen) |
| `patch-briefs/*.md`   | Incremental changes         | After `feedback`      | Immutable (applied to master)       |
| `briefs/library/*.md` | Reusable brief templates    | After `brief save`    | Read-only                           |

#### Brief Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    BRIEF LIFECYCLE                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  user-brief.md                                              │
│      ↓ (brief analyze)                                      │
│  working-brief.md + analysis.json                           │
│      ↓ (brief clarify - interactive loop)                   │
│  master-brief.md + clarifications/* + clarification-log.json│
│      ↓ (brief save)                                         │
│  briefs/library/<name>.md                                   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  FEEDBACK LOOP                       │   │
│  │                                                      │   │
│  │  feedback → patch-briefs/patch-*.md                 │   │
│  │      ↓ (merge)                                       │   │
│  │  master-brief.md (updated)                          │   │
│  │      ↓ (auto-trigger pipeline)                      │   │
│  │  contract gen → ... → code apply                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Critical Question Answered

**Q:** brief.md user nhập vào cho mỗi version là gì?

**A:**

- **Initial version (v1.0.0):** Full functional requirements từ đầu
- **Subsequent versions (v1.0.1+):** Có 2 options:
    1. **Option A (Recommended):** Full state (master-brief.md từ version trước + patch-briefs)
    2. **Option B:** Incremental changes only (patch-brief chỉ chứa changes mới)

**Recommendation:** Option A - master-brief.md luôn chứa FULL STATE để:

- Avoid ambiguity about current state
- Make each version self-contained
- Simplify contract generation (no need to merge history)

### Recommended Action

**Add Section E01:** Brief Management với:

- Brief types và lifecycle
- Clarification loop process
- Patch merging strategy
- Brief library for reuse

---

## Gap 4: Directory Structure (P1)

### Current State in requirement.md

- `.midicoder/` mentioned but structure not fully defined
- Missing runtime/ and cache/ directories

### Required Structure from pipeline-plan

```
.midicoder/
├── config/
│   ├── midicoder.yml          # Global configuration
│   ├── llm.yml                # LLM configuration (Qwen-3.5-27B)
│   └── capabilities.yml       # Enabled capability packs
├── versions/
│   ├── v1.0.0/
│   │   ├── metadata.yml       # Version metadata
│   │   ├── briefs/
│   │   │   ├── master-brief.md
│   │   │   ├── working-brief.md
│   │   │   ├── clarifications/
│   │   │   │   ├── q1.md
│   │   │   │   ├── a1.md
│   │   │   │   └── ...
│   │   │   └── patch-briefs/
│   │   │       ├── patch-001.md
│   │   │       └── ...
│   │   ├── contracts/
│   │   │   ├── ir.json        # Generated DSL contract
│   │   │   ├── manifest.json  # Contract manifest
│   │   │   └── schemas/
│   │   │       ├── entity_v0.yml
│   │   │       ├── command_v0.yml
│   │   │       └── ...
│   │   ├── ir/
│   │   │   ├── mir.json       # Midicoder IR (MIR)
│   │   │   ├── symbol-table.json
│   │   │   └── diagnostics/
│   │   │       ├── errors.json
│   │   │       └── warnings.json
│   │   ├── plan/
│   │   │   ├── lowering.json  # Implementation plan
│   │   │   ├── patches/
│   │   │   │   ├── file1.patch-plan.json
│   │   │   │   └── ...
│   │   │   └── index.json
│   │   ├── code/
│   │   │   ├── generated/     # Generated source code
│   │   │   ├── applied/       # Applied code status
│   │   │   └── report.json    # Generation report
│   │   └── index/
│   │       ├── context.db     # SQLite context index
│   │       ├── artifacts.db   # SQLite artifact index
│   │       └── provenance.db  # SQLite provenance tracking
│   └── v1.0.1/                # Next version (when created)
├── runtime/
│   ├── docker-compose.yml     # Local preview setup
│   ├── .env                   # Environment variables
│   └── logs/
└── cache/
    ├── llm/                   # LLM response cache
    └── templates/             # Template cache
```

### Recommended Action

**Add Section E01:** Project Structure with:

- Complete `.midicoder/` tree
- Directory purposes
- File formats and schemas

---

## Gap 5: Version Management (P1)

### Current State in requirement.md

- Version mentioned but no versioning strategy
- No commands for version management

### Required from pipeline-plan

#### Version Commands

```bash
# Create new version from scratch
midicoder version create --name v1.0.1

# Create new version from existing
midicoder version create --from v1.0.0 --name v1.0.1

# Set active version
midicoder version use v1.0.1

# List versions
midicoder version list
```

#### Version Metadata

```yaml
# .midicoder/versions/v1.0.1/metadata.yml
version: 1.0.1
created_at: "2025-01-23T10:00:00Z"
parent_version: 1.0.0
status: draft # or: active, archived

briefs:
    master: null # Will be set after brief save
    count: 0

contracts:
    generated: false
    validated: false

ir:
    built: false
    version: null

code:
    planned: false
    generated: false
    applied: false
```

### Recommended Action

**Add Section E01:** Version Management với:

- Version lifecycle
- Branching/merging strategies
- Version metadata schema

---

## Gap 6: LLM Budget Integration (P2)

### Current State in requirement.md

- LLM mentioned for contract generation
- No budget tracking or optimization

### Required from pipeline-plan

#### LLM Budget per Version

```
Initial Generation:
- brief analyze: 2,000 tokens
- brief clarify: 15,000 tokens (3 rounds × 5,000)
- contract gen: 15,000 tokens
- contract check: 3,000 tokens (3 errors × 1,000)
Total: ~35,000 tokens

Per Feedback Loop:
- feedback: 3,000 tokens
- contract gen (incremental): 5,000 tokens
- contract check: 1,000 tokens
Total: ~9,000 tokens/loop
```

#### Optimization Strategies

1. **LLM Caching**: Cache LLM responses for identical inputs
2. **Incremental Generation**: Only regenerate changed contracts
3. **Token Budget**: Set max tokens per request (8,192 for Qwen-3.5-27B)
4. **Temperature**: Low temperature (0.3) for deterministic output
5. **Batch Processing**: Batch multiple clarifications in one request

### Recommended Action

**Add Section E20:** LLM Budget Management với:

- Budget tracking per command
- Caching strategies
- Cost optimization techniques

---

## Gap 7: Initial Installation & Setup (P0 - CRITICAL)

### Current State in requirement.md
- NO section about how users install midicoder
- No installation flow documentation

### Required from scripts/install/

#### Installation Methods

**Method 1: Shell Script (Linux/macOS)**
```bash
curl -o- https://midicoder.com/install.sh | bash
# or
wget -qO- https://midicoder.com/install.sh | bash
```

**Method 2: PowerShell (Windows)**
```powershell
iwr https://midicoder.com/install.ps1 | iex
```

**Method 3: pip (Developer Mode)**
```bash
pip install midicoder-ce
```

**Method 4: Docker**
```bash
docker pull hemidi-jsc/midicoder:latest
```

#### Installation Structure

```
~/.midicoder/
├── bin/
│   └── midicoder          # Main CLI binary
├── cache/                 # LLM response cache
├── logs/                  # Runtime logs (SQLite, not JSON)
├── midicoder.json        # Global configuration
└── versions/             # Per-project version workspaces
```

#### Initial Setup Flow

```
┌─────────────────────────────────────────────────────────────┐
│                INITIAL SETUP FLOW                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. User runs install script                                │
│     ├─ Downloads binary from GitHub releases                │
│     ├─ Extracts to ~/.midicoder/bin/                        │
│     └─ Adds to PATH                                         │
│                                                              │
│  2. First run: midicoder init                               │
│     ├─ Creates .midicoder/ in project directory             │
│     ├─ Generates global config ~/.midicoder/midicoder.json  │
│     ├─ Sets up SQLite databases (context.db, artifacts.db)  │
│     └─ Detects existing codebase (if any)                   │
│                                                              │
│  3. Optional: Start WebGUI                                  │
│     ├─ midicoder webgui start                               │
│     ├─ Starts FastAPI backend on :6868                      │
│     └─ Starts Angular frontend on :7272                     │
│                                                              │
│  4. Optional: CLI mode                                      │
│     └─ Direct CLI interaction with enhanced TUI             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Global Config Schema (~/.midicoder/midicoder.json)

```json
{
  "version": "1.0.0",
  "created_at": "2026-04-21T00:00:00Z",
  "cli": {
    "mode": "webgui",  // or "cli"
    "theme": "default",
    "language": "vi",
    "output_format": "human"  // or "json" for scripting
  },
  "llm": {
    "provider": "ollama",  // or "openai", "anthropic", "aws-bedrock"
    "model": "qwen2.5:72b",
    "api_url": "http://localhost:11434",
    "api_key": null,
    "max_tokens": 8192,
    "temperature": 0.3
  },
  "project": {
    "cwd": "/path/to/current/project",
    "last_opened": "2026-04-21T00:00:00Z"
  },
  "webgui": {
    "host": "localhost",
    "port": 6868,
    "auto_start": true
  },
  "capabilities": {
    "enabled": ["CP01", "CP02", "CP03", "CP07"],
    "domain_packs": ["DP01"]
  }
}
```

### Recommended Action
**Add Section E00: Installation & Setup** với:
- Installation methods (shell, powershell, pip, docker)
- Initial setup flow
- Global config schema
- WebGUI vs CLI modes

---

## Gap 8: Technical Engineering Decisions (P0 - CRITICAL)

### Decision 1: SQLite vs JSON Logs

**Pipeline-plan approach:** Store logs as JSON files in `.midicoder/logs/`

**Problem:** 
- JSON logs are not queryable
- Cannot correlate events across time
- Hard to implement lineage tracking

**Recommended approach:** Use SQLite for ALL persistent data

```sql
-- Activity log table (replaces JSON logs)
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    command TEXT,  -- e.g., "brief analyze"
    stage TEXT,    -- e.g., "llm_call", "validation", "generation"
    artifact_id INTEGER REFERENCES artifacts(id),
    input_hash TEXT,    -- Hash of inputs (for determinism verification)
    output_hash TEXT,   -- Hash of outputs
    duration_ms INTEGER,
    status TEXT,        -- success, failed, partial
    error_message TEXT,
    metadata TEXT       -- JSON: additional context
);

CREATE INDEX idx_activity_timestamp ON activity_log(timestamp);
CREATE INDEX idx_activity_command ON activity_log(command);
CREATE INDEX idx_activity_stage ON activity_log(stage);
```

**Benefits:**
- Queryable with SQL
- Correlate with artifacts via artifact_id
- Track performance (duration_ms)
- Verify determinism via input/output hashes

---

### Decision 2: Context Injection in Deterministic Stages

**Concern:** Midicoder has 2 types of stages:
1. **LLM Authoring Stages** (non-deterministic): brief analyze, brief clarify, contract gen, feedback
2. **Deterministic Stages**: ir build, code plan, code gen, code apply

**Question:** Where and how to inject context from SQLite index?

**Answer: Context injection ONLY in LLM stages**

#### Context Injection Points

| Stage | Context Type | Purpose | Source |
|-------|-------------|---------|--------|
| `brief analyze` | Project context | Understand existing codebase | context.db (symbols, files) |
| `brief clarify` | Previous Q&A | Maintain conversation history | clarifications/ in SQLite |
| `contract gen` | Capability templates | Generate correct DSL | DSL schema + capability graph |
| `feedback` | Current state | Understand what to change | mir.json + symbol table |

#### Deterministic Stages: NO Context Injection

| Stage | Why NO Context | Determinism Guarantee |
|-------|----------------|----------------------|
| `ir build` | Parse DSL → MIR | Same DSL → Same MIR |
| `code plan` | MIR → Plan | Same MIR → Same Plan |
| `code gen` | Plan → Code | Same Plan → Same Code |
| `code apply` | Apply patches | Same patches → Same result |

**Algorithm Design Principle:**
```
LLM Stage:
  Input: User input + Context from SQLite
  Process: LLM generation
  Output: DSL/Master-brief (stored in SQLite)
  
Deterministic Stage:
  Input: Previous stage output ONLY (from SQLite)
  Process: Algorithmic transformation
  Output: Next stage artifact (stored in SQLite)
  Note: NO additional context injection
```

---

### Decision 3: Brief Storage in SQLite vs MD Files

**Pipeline-plan approach:** Store briefs as MD files in `.midicoder/versions/<v>/briefs/`

**Problem:**
- Cannot query briefs across versions
- Cannot track brief evolution
- MCP server cannot access brief content easily

**Recommended approach:** Store ALL briefs in SQLite

```sql
-- Briefs table (replaces master-brief.md, working-brief.md)
CREATE TABLE briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,  -- e.g., "v1.0.0"
    type TEXT NOT NULL,     -- working, master, patch, library
    name TEXT,              -- Library brief name (NULL for working/master)
    content TEXT,           -- Full brief content (Markdown)
    status TEXT,            -- draft, clarified, frozen, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parent_brief_id INTEGER REFERENCES briefs(id),  -- For patch briefs
    version_order INTEGER   -- For patch ordering
);

CREATE INDEX idx_briefs_version ON briefs(version);
CREATE INDEX idx_briefs_type ON briefs(type);

-- Clarification rounds
CREATE TABLE clarifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id INTEGER REFERENCES briefs(id),
    round_number INTEGER,
    question TEXT,
    answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**File sync strategy:**
- SQLite is PRIMARY source of truth
- MD files are OPTIONAL snapshots for readability
- On `brief save`, export to `briefs/library/<name>.md`
- On `brief load`, import from MD to SQLite

---

### Decision 4: MCP Server Tools for SQLite Access

**Current plan:** MCP server only has DSL schema tools

**Recommended expansion:** Add SQLite access tools

```python
# MCP Server Tools

# DSL Tools (existing)
@tool
def get_dsl_schema(section: str) -> dict: ...

@tool
def list_core_capabilities() -> list[dict]: ...

@tool
def list_macro_patterns() -> list[dict]: ...

# NEW: SQLite Access Tools

@tool
def get_active_brief(version: str = None) -> dict:
    """Get current working/master brief from SQLite"""
    # SELECT * FROM briefs WHERE version=? AND type IN ('working', 'master')
    pass

@tool
def get_previous_briefs(version: str, limit: int = 5) -> list[dict]:
    """Get previous briefs for context"""
    # SELECT * FROM briefs WHERE version=? ORDER BY created_at DESC
    pass

@tool
def get_clarifications(brief_id: int) -> list[dict]:
    """Get clarification Q&A for a brief"""
    # SELECT * FROM clarifications WHERE brief_id=?
    pass

@tool
def get_project_context(query: str) -> list[dict]:
    """Query codebase context from SQLite index"""
    # Hybrid search: structural + semantic
    # SELECT * FROM symbols WHERE ... OR embedding_distance < threshold
    pass

@tool
def get_capability_graph() -> dict:
    """Get core capability graph for reference"""
    # Load from pre-built capability graph
    pass
```

**LLM Contract Generation Flow with MCP:**
```
1. LLM receives user brief text
2. LLM calls get_active_brief() → Get current master-brief
3. LLM calls get_previous_briefs() → Understand evolution
4. LLM calls get_clarifications() → See Q&A decisions
5. LLM calls get_project_context() → Understand existing codebase
6. LLM calls list_core_capabilities() → Know available capabilities
7. LLM generates DSL contracts based on all context
8. LLM saves new brief to SQLite via midicoder CLI
```

---

### Decision 5: Two-Mode UI Strategy

**Mode 1: WebGUI (Default)**
- Full-featured Angular + FastAPI application
- Runs on localhost:7272 (frontend) + :6868 (backend)
- Rich UI with forms, charts, diagrams
- Real-time updates via WebSocket
- Target: Desktop users who want visual interface

**Mode 2: Enhanced CLI (TUI - Terminal User Interface)**
- Pure CLI with enhanced TUI components
- UTF-8/Unicode support
- Rich text rendering
- Interactive menus, forms, tables
- Target: Remote servers, scripts, power users

#### Enhanced CLI UI Components

```python
# CLI TUI Components

# Rich banner with Unicode
┌─────────────────────────────────────────────────────────┐
│  ════════ Midicoder v1.0.0 ════════                     │
│  ══╤═ Brief ══║═ Contract ══║═ IR ══║═ Code ══║═ Preview═│
└─────────────────────────────────────────────────────────┘

# Interactive menu
┌─ Select Command ───────────────────────────────────────┐
│  ◉ brief analyze      Analyze project requirements     │
│    brief clarify      Interactive clarification        │
│    brief save         Save to library                  │
│    contract gen       Generate DSL contracts           │
│    ir build           Build MIR from contracts         │
│    code plan          Generate implementation plan     │
│    code gen           Generate source code             │
│    code apply         Apply patches to project         │
│    preview            Start local preview              │
│    feedback           Provide feedback                 │
│    version create     Create new version               │
│    status             Show project status              │
│    help               Show help                        │
│    quit               Exit                             │
└─────────────────────────────────────────────────────────┘
│ ↑/↓ Navigate  Enter Select  q Quit  h Help            │

# Progress bar with Unicode
Generating contracts... ████████████░░░░░░░░░░ 60%

# Status table
┌─────────┬──────────┬─────────┬────────────────┐
│ Stage   │ Status   │ Time    │ Details        │
├─────────┼──────────┼─────────┼────────────────┤
│ brief   │ ✓ Done   │ 2m 34s  │ 12 clarifications
│ contract│ ✓ Done   │ 1m 12s  │ 34 schemas generated
│ ir      │ ✓ Done   │ 0m 45s  │ 127 symbols indexed
│ code    │ ◐ In Progress │ 45% │ Generating...
└─────────┴──────────┴─────────┴────────────────┘

# Syntax highlighting
┌─ contracts/entities/product_v0.yml ────────────────────┐
│ name: Product                                           │
│ fields:                                                 │
│   - name: sku                                           │
│     type: string                                        │
│     constraints:                                        │
│       - unique                                          │
│       - not_null                                        │
└─────────────────────────────────────────────────────────┘
```

#### UTF-8/Unicode Support

```python
# Ensure UTF-8 terminal output
import os
import sys

# Force UTF-8 encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')  # Windows: Switch to UTF-8

# Use rich library for TUI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn

console = Console(
    force_terminal=True,
    force_jupyter=False,
    width=120
)
```

### Recommended Action
**Add Section E99: Technical Engineering Decisions** với:
- SQLite vs JSON logs decision
- Context injection algorithm
- Brief storage strategy
- MCP server tools design
- Two-mode UI strategy (WebGUI + Enhanced CLI)

---

## Gap 9: Artifacts & Lineage Tracking (P1)

### Current State in requirement.md

- Artifacts defined (CapabilityGraph, MIR, etc.)
- No lineage tracking or provenance

### Required from pipeline-plan

#### Artifact Lineage

```
user-brief.md
    ↓ (analyze)
working-brief.md → analysis.json
    ↓ (clarify × N rounds)
master-brief.md → clarifications/* → clarification-log.json
    ↓ (contract gen)
contracts/ir.json → manifest.json → schemas/*
    ↓ (contract check)
contracts/validation-report.json
    ↓ (ir build)
ir/mir.json → symbol-table.json → diagnostics/*
    ↓ (code plan)
plan/lowering.json → patches/* → index.json
    ↓ (code gen)
code/generated/* → report.json
    ↓ (code apply)
target-project/* → applied/status.json
```

#### Provenance Query Examples

```sql
-- Find all artifacts derived from a brief
SELECT * FROM lineage
WHERE ancestor_id = (SELECT id FROM artifacts WHERE name = 'master-brief.md');

-- Find decision rationale for an artifact
SELECT d.rationale, d.source
FROM decisions d
JOIN artifacts a ON d.artifact_id = a.id
WHERE a.name = 'ir/mir.json';
```

### Recommended Action

**Add Section E05:** Artifact Lineage với:

- Provenance tracking mechanisms
- Decision recording
- Audit trail queries

---

## Code Implementation Alignment Check

### Review Code Already Implemented

| Component         | Implemented | Matches Pipeline-Plan? | Notes                                    |
| ----------------- | ----------- | ---------------------- | ---------------------------------------- |
| CLI Structure     | ⚠️ Partial  | ⚠️ Partial             | Only `brief analyze/rewrite` implemented |
| Brief Commands    | ⚠️ Partial  | ⚠️ Partial             | Missing clarify, save, load, list        |
| Contract Commands | ❌ Missing  | ❌ Missing             | No contract gen/check                    |
| IR Building       | ✅ Yes      | ✅ Yes                 | IR builder exists                        |
| DSL Catalogs      | ✅ Yes      | ✅ Yes                 | 34+ catalogs implemented                 |
| Validation        | ✅ Yes      | ✅ Yes                 | 34+ constraints implemented              |

### Critical Alignment Issues

1. **CLI Commands**: Need to implement 12+ missing commands
2. **SQLite Persistence**: Need to implement 4 database schemas
3. **Version Management**: Need to implement version create/use
4. **Brief Lifecycle**: Need to implement working-brief → master-brief flow

---

## Recommended Sections to Add to requirement.md

### Priority P0 (Must Have)

1. **Section E20: CLI Commands** (Complete rewrite)
    - All 14 commands with signatures
    - Input/output artifacts
    - Exit codes
    - Examples

2. **Section E09: Persistent Storage** (New)
    - SQLite schema definitions
    - Index building strategies
    - Provenance tracking

3. **Section E01: Brief Management** (Expand)
    - Brief types (working, master, patch, library)
    - Clarification loop
    - Brief lifecycle

### Priority P1 (Should Have)

4. **Section E01: Project Structure** (Expand)
    - Complete `.midicoder/` tree
    - Version workspace structure

5. **Section E01: Version Management** (New)
    - Version lifecycle
    - Version commands
    - Version metadata

### Priority P2 (Nice to Have)

6. **Section E20: LLM Budget Management** (New)
    - Budget tracking
    - Optimization strategies

---

## Conclusion

### Summary

| Gap                 | Impact   | Effort | Priority |
| ------------------- | -------- | ------ | -------- |
| CLI Commands        | High     | Medium | P0       |
| SQLite Schemas      | High     | Medium | P0       |
| Brief Scope         | Critical | Low    | P0       |
| Directory Structure | Medium   | Low    | P1       |
| Version Management  | Medium   | Medium | P1       |
| LLM Budget          | Low      | Low    | P2       |
| Lineage Tracking    | Medium   | Medium | P1       |

### Recommendation

**Requirement.md cần bổ sung 6 sections mới để trở thành self-complete SoT:**

1. Rewrite E20: CLI Commands (P0)
2. New E09: Persistent Storage (P0)
3. Expand E01: Brief Management (P0)
4. Expand E01: Project Structure (P1)
5. New E01: Version Management (P1)
6. New E20: LLM Budget (P2)

**Estimated Effort:** 2-3 days of documentation work

**Benefit:** requirement.md sẽ trở thành single source of truth cho toàn bộ Midicoder architecture, không cần reference thêm pipeline-plan.md nữa.

---

**Next Steps:**

1. [ ] Approve gap analysis
2. [ ] Prioritize sections to add
3. [ ] Implement sections in requirement.md
4. [ ] Review code implementation alignment
5. [ ] Cut-over to requirement.md only (delete pipeline-plan.md reference)
