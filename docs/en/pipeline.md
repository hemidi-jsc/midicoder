# Pipeline Deep Dive

This page describes the complete Midi Coder pipeline architecture and how each step transforms artifacts.

## Philosophy

Midi Coder follows a **deterministic, contract-first** approach:

- **LLM as authoring tool only**: LLMs generate contracts (YAML) and decide patch strategies, but NEVER write code directly
- **Patch-based, not rewrite**: Small, reviewable patches instead of full file rewrites
- **Auditable artifacts**: Every step creates versioned, traceable outputs in `.midicoder/`
- **Multi-stack support**: One IR → Multiple target stacks (FastAPI, NestJS, Angular)

## Pipeline Overview

```
master-brief.md (user input)
    ↓
[contract gen] → contracts/*.yaml (DSL)
    ↓
[ir build] → ir.json (intermediate representation)
    ↓
[code build] → plans/*.code-plan.json (pseudo code, FastAPI)
    ↓
[code gen] → patches/*.patch-plan.json (real code, target stack)
    ↓
[code apply] → Working directory (patched files)
```

---

## Step 1: Init - Project Setup

**Command:** `midicoder init`

**Purpose:** Initialize Midi Coder workspace and configuration.

**Modes:**

- **Interactive**: Wizard prompts for configuration
- **Non-Interactive**: Use CLI flags or environment variables (for CI/CD)

See [Non-Interactive Guide](non-interactive.md) for automation details.

**Outputs:**

```
.midicoder/
├── config.json          # Main configuration
├── secrets.json         # API keys (gitignored)
└── state.json           # Pipeline state tracker
```

**Implementation:** `midicoder/commands/init.py`

---

## Step 2: Index - Project Context Extraction

**Command:** `midicoder index`

**Purpose:** Scan source code to build **Project Context** for downstream steps.

**Process:**

1. **Stack Detection**: Auto-detect tech stack from codebase
2. **Symbol Extraction**: Parse classes, functions, methods using AST/regex
3. **Entrypoint Discovery**: Find main entry points (FastAPI app, NestJS bootstrap, Angular main)
4. **Seam Identification**: Detect integration boundaries (safe injection points)
5. **Exemplar Collection**: Extract code snippets as style references

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

# Incremental reindex (changed files only)
midicoder index reindex --path src/users/controller.py
```

**Implementation:** `midicoder/context/indexer.py`

---

## Step 3: Version Create - Feature Branch Setup

**Command:** `midicoder version create <version>`

**Purpose:** Create isolated workspace for a feature/release version.

**Outputs:**

```
.midicoder/versions/<version>/
├── state.json           # Version metadata
├── master-brief.md      # User-written requirements (template)
├── contracts/           # DSL contracts
├── irs/                 # Intermediate representation
├── plans/               # Code plans
├── patches/             # Patch plans
└── snapshots/           # Backup before apply
```

**master-brief.md** template follows DSL schema with sections for domain, commands, workflows, API, etc.

**Implementation:** `midicoder/commands/version.py`

---

## Step 4: Contract Generation - Requirements → DSL

**Command:** `midicoder contract gen`

**Purpose:** Transform `master-brief.md` into structured DSL contracts using LLM.

**Inputs:**

1. **master-brief.md**: User requirements
2. **Project Context**: From indexing step
3. **DSL Schema**: Pre-defined schema
4. **LLM Config**: High-tier model (e.g., Claude Sonnet)

**Process:**

1. **Brief Analysis**: LLM determines required contract files
2. **Batch Generation**: Generate one file at a time for precision
3. **Schema Validation**: Each YAML validated against models
4. **Cross-reference Check**: Ensure references are valid

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
# Resume from failed run (only missing/failed files)
midicoder contract gen resume
```

- Analyzes latest run logs
- Validates existing files
- Regenerates only failed/missing files
- Saves up to 50% tokens

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

## Step 5: IR Build - DSL → Intermediate Representation

**Command:** `midicoder ir build [--skip-diagrams]`

**Purpose:** Compile DSL contracts into normalized, validated IR JSON.

**Process (100% Deterministic, No LLM):**

1. Load all YAML files from `contracts/`
2. Validate structure against Pydantic models
3. Check ID uniqueness, valid references
4. Build symbol table for cross-references
5. Normalize IDs and format
6. Build IR modules (Domain, Application, Workflow, API, Policy, Rules, Scenario)
7. Generate Mermaid diagrams (optional)

**Outputs:**

```
.midicoder/versions/<version>/irs/
├── ir.json              # Complete IR
├── manifest.json        # Metadata, stats
└── diagrams/            # Mermaid diagrams (optional)
    ├── api/*.mmd
    ├── commands/*.mmd
    ├── entities/*.mmd
    └── workflows/*.mmd
```

**Validation:**

- Structural: Required fields, no extra fields
- Semantic: ID uniqueness, valid references
- Cross-module: Referenced entities/commands exist
- Detailed errors with file, location, suggestions

**Implementation:** `midicoder/ir/builder/builder.py`

---

## Step 6: Code Build - IR → Pseudo Code Plans

**Command:** `midicoder code build`

**Purpose:** Generate deterministic pseudo code plans (FastAPI flavor) from IR.

**Process (100% Deterministic, No LLM):**

1. Load `ir.json` from IR build step
2. Extract components (Commands, Workflows, API Routes)
3. Map to folder structure (FastAPI conventions)
4. Generate pseudo code with:
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

**Key Features:**

- **Anchors**: Comment markers (not line numbers) for stable injection
- **Folder-level**: Group related files (router, service, schemas, deps)
- **Warnings**: Report missing seams or unconventional structures

**Implementation:** `midicoder/code/builder/`

---

## Step 7: Code Gen - Pseudo → Real Code

**Command:** `midicoder code gen [--runtime]`

**Purpose:** Transform pseudo code plans into executable code with precise patch locations.

**Two-Step Process:**

### Step 1: Patch Strategy (High-tier LLM)

**Decides WHERE and HOW to patch:**

- Identify target files (create new or modify existing)
- Determine patch operations (write/edit/delete)
- Find semantic anchors (comments, decorators, markers)
- Choose patch modes (before/after/replace)

### Step 2: Stack Conversion (Cheap-tier LLM or Skip)

**Converts syntax to target stack:**

- **Target = FastAPI**: Skip conversion (pseudo is already FastAPI)
- **Target = NestJS/Angular**: Use cheap LLM to translate
  - FastAPI → NestJS decorators
  - Python → TypeScript syntax
  - Maintain anchors and style

**Outputs:**

```
.midicoder/versions/<version>/patches/
├── plans/
│   ├── index.json       # Patch plan registry
│   ├── commands/*.patch-plan.json
│   ├── workflows/*.patch-plan.json
│   └── api/*.patch-plan.json
└── runtime/             # (optional, with --runtime flag)
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

**Operation Types:**

- **write**: Create new file
- **edit**: Modify existing file at anchor
- **delete**: Remove file

**Edit Modes:**

- **before**: Insert before anchor
- **after**: Insert after anchor
- **replace**: Replace content at anchor

**Implementation:** `midicoder/code/generator/`

---

## Step 8: Code Apply - Patches → Working Directory

**Command:** `midicoder code apply [--force] [--dry-run] [--no-reindex]`

**Purpose:** Safely apply patch plans to actual codebase.

**Safety Features:**

1. **Snapshot**: Backup files before modification
2. **Conflict Detection**: Check for concurrent changes
3. **Dry Run**: Preview without writing
4. **Rollback**: Restore from snapshot if needed
5. **Reindexing**: Update Project Context after changes

**Process:**

1. **Pre-flight**: Validate patch plans, check writability, detect conflicts
2. **Snapshot**: Backup files to `.midicoder/versions/<version>/snapshots/`
3. **Apply**: Execute write/edit/delete operations
4. **Verify**: Basic syntax checks, record operations
5. **Reindex**: Update Project Context (unless `--no-reindex`)

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

- **Without `--force`**: Abort with error
- **With `--force`**: Apply anyway (may cause merge conflicts)

**Dry Run:**

```bash
midicoder code apply --dry-run
```

Shows what would be applied without actual modifications.

**Implementation:** `midicoder/code/applicator/`

---

## Contract Feedback & Repair

### Check

**Command:** `midicoder contract check`

Validates contracts for issues (YAML syntax, schema, cross-refs).

### Feedback

**Command:** `midicoder contract feedback`

Creates/updates `contract-feedbacks.yml` with validation issues and custom feedback.

**Example feedback file:**

```yaml
items:
  - id: FB-001
    file: contracts/app/commands.yaml
    location: "commands[id=CreateOrder]"
    status: pending
    issue: "Missing authorization guard"
    suggestion: "Add guard with permission = 'create_order'"
```

### Repair Prepare

**Command:** `midicoder contract repair prepare`

Validates feedback file without running LLM (checks syntax, references).

### Repair Run

**Command:** `midicoder contract repair run`

Applies feedback items to contracts using LLM:

1. Load feedback file
2. Group by file
3. Process in dependency order
4. Generate and apply patches
5. Sync `master-brief.md`
6. Extract memos to `.midicoder/context/memos/`
7. Update feedback status

**Implementation:** `midicoder/contract/`

---

## Advanced Features

### Incremental Reindexing

```bash
midicoder index reindex --path src/users/controller.py
```

Updates Project Context for specific files only.

### Smart Resume

```bash
midicoder contract gen resume
```

Resumes failed generation, regenerates only failed/missing files (saves up to 50% tokens).

### Diagram Generation

```bash
midicoder ir build              # With diagrams
midicoder ir build --skip-diagrams  # Without diagrams
```

Generates Mermaid diagrams (Domain Model, Command Graph, API Map, Workflows).

---

## Error Handling & Debugging

### Run Artifacts

Every command creates detailed logs:

```
.midicoder/runs/<command>/<timestamp>/
├── summary.json         # Results
├── state_before.json    # State before
├── state_after.json     # State after
└── <command-specific artifacts>
```

### Trace Files (Contract Gen)

Comprehensive traces for debugging LLM interactions:

```
.midicoder/runs/contract_gen/<timestamp>/
├── pass_01_*.json
│   ├── prompt.txt       # Exact prompt sent
│   ├── response.txt     # Raw LLM response
│   └── trace.json       # Context metadata
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `No current version set` | Run `midicoder version create <ver>` |
| `master-brief.md is missing` | Recreate version or add file manually |
| `IR is missing` | Run `midicoder ir build` |
| `plans/index.json is missing` | Run `midicoder code build` |
| `patches/index.json is missing` | Run `midicoder code gen` |
| Conflict during apply | Use `--dry-run` to review, `--force` to override |

---

## Design Philosophy & Future Direction

### Current State (v0.x)

- LLM for contract authoring (high-quality requirements capture)
- Deterministic IR compilation (zero randomness)
- Deterministic code planning (FastAPI only)
- LLM for patch strategy (still needed for contextual decisions)
- LLM for stack conversion (cheap model, acceptable)

### Future Roadmap (v1.x+)

**Goal:** Reduce LLM dependency (Anti-AI approach)

1. **AST-based Code Understanding**: Replace regex with Tree-sitter
2. **Reverse Engineering**: Extract contracts FROM code automatically
3. **Universal Transpiler**: IR → Generic AST → Stack-specific emitters
4. **Semantic Anchoring**: AST-path anchors instead of line numbers
5. **Dependency Graph**: Smart file targeting based on imports

See `technic/midicoder-algorithm.md` for detailed designs.

---

## Design Specs & Technical References

Detailed design documents in `technic/` folder:

- **`technic/DSL-schema.md`**: Complete DSL specification
- **`technic/DSL-contracts.md`**: Contract generation workflow
- **`technic/IR-compiler.md`**: IR compilation algorithm
- **`technic/source-indexing.md`**: Project Context extraction
- **`technic/codegen.md`**: Code generation strategy
- **`technic/contract-repair.md`**: Feedback & repair workflow
- **`technic/midicoder-algorithm.md`**: R&D roadmap

---

## Summary

Midi Coder pipeline:

1. **Init**: Setup workspace
2. **Index**: Extract Project Context
3. **Version**: Create feature workspace
4. **Contract Gen**: Requirements → DSL (LLM-assisted)
5. **IR Build**: DSL → IR (deterministic)
6. **Code Build**: IR → Pseudo plans (deterministic)
7. **Code Gen**: Pseudo → Real patches (LLM-assisted)
8. **Code Apply**: Patches → Working code (deterministic)

**Key Principles:**
- LLM generates contracts, not code
- Every step creates auditable artifacts
- Patch-based for easy review
- Multi-stack support via IR
- Deterministic where possible

**Next Steps:**
- See [CLI Commands](cli.md) for command reference
- See [Configuration](config.md) for setup details
- See [Artifacts](artifacts.md) for file structure
- See [Troubleshooting](troubleshooting.md) for common issues
