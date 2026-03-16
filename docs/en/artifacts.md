# Artifacts Reference

Complete reference for all files and directories created by Midi Coder.

## Overview

Midi Coder creates a structured `.midicoder/` directory in your project root with all artifacts versioned and traceable.

```
project-root/
├── .midicoder/              # Midi Coder workspace
│   ├── config.json          # Configuration
│   ├── secrets.json         # API keys (gitignored)
│   ├── state.json           # Global state
│   ├── context/             # Project Context
│   ├── runs/                # Execution logs
│   └── versions/            # Version workspaces
├── src/                     # Your source code
└── ...
```

---

## Root Level

### `.midicoder/config.json`

**Created by:** `midicoder init`

**Purpose:** Main configuration file.

**Format:** JSON

**Example:**

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

**Key Fields:**

- `working_dir`: Absolute path to project root (for indexing and patching)
- `stack`: Array of target stacks (`fastapi`, `nest`, `angular`)
- `llm.high`: High-tier LLM for complex tasks (contract gen, patch strategy)
- `llm.cheap`: Cheap-tier LLM for simple tasks (stack translation)
- `cache`: LLM response caching configuration
- `snapshot_whitelist`: Optional glob patterns for selective snapshots

**See:** [Configuration Guide](config.md)

---

### `.midicoder/secrets.json`

**Created by:** `midicoder init`

**Purpose:** Store API keys and sensitive data.

**Format:** JSON

**Security:** This file is gitignored. Never commit to version control.

**Example:**

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

**Management:**

```bash
# View secrets (masked)
midicoder config secrets list

# Update secret
midicoder config secrets set llm high
```

---

### `.midicoder/state.json`

**Created by:** `midicoder init`

**Updated by:** Most commands

**Purpose:** Track global pipeline state.

**Format:** JSON

**Example:**

```json
{
  "current_version": "v0.1.0",
  "contracts_locked": false,
  "last_index": "2025-02-10T10:30:00Z"
}
```

**Key Fields:**

- `current_version`: Active version (set by `version create`)
- `contracts_locked`: Whether contracts can be modified
- `last_index`: Timestamp of last indexing

---

## Context Directory

### `.midicoder/context/`

**Created by:** `midicoder index`

**Updated by:** `midicoder index reindex`

**Purpose:** Store Project Context for LLM and code generation.

**Structure:**

```
.midicoder/context/
├── manifest.json        # Scan metadata
├── profile.json         # Stack detection, conventions
├── symbols.json         # Classes, functions, methods
├── entrypoints.json     # Application entry points
├── seams.json           # Integration boundaries
├── exemplars.json       # Code examples
└── memos/               # Design decisions (from contract repair)
    └── *.md
```

---

### `manifest.json`

**Format:** JSON

**Purpose:** Metadata about the indexing run.

**Example:**

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

**Purpose:** Detected tech stack and coding conventions.

**Example:**

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

**Purpose:** Catalog of all classes, functions, methods in codebase.

**Example:**

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

**Purpose:** Main entry points of the application.

**Example:**

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

**Purpose:** Safe integration boundaries for patching.

**Example:**

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

**Seam Types:**

- `router_group`: Route registration points
- `service_methods`: Service layer methods
- `repository_methods`: Data access methods
- `dto_models`: DTO/Schema definitions
- `dependencies`: Dependency injection providers

---

### `exemplars.json`

**Format:** JSON

**Purpose:** Example code snippets for LLM reference.

**Example:**

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

**Created by:** `midicoder contract repair run`

**Purpose:** Store design decisions and constraints from contract repair process.

**Format:** Markdown files

**Example:** `memos/rbac-guidelines.md`

```markdown
# RBAC Guidelines

From contract repair feedback FB-003:

- Always use `create_*` permission for creation commands
- Always use `read_*` permission for queries
- Admin role has all permissions by default
- Permission naming: `<verb>_<entity>` (snake_case)
```

**Usage:** These memos are included in future `contract gen` and `code gen` prompts as additional context.

---

## Runs Directory

### `.midicoder/runs/`

**Purpose:** Store execution logs for all commands.

**Structure:**

```
.midicoder/runs/
├── init/
│   └── <timestamp>/
│       └── summary.json
├── index/
│   └── <timestamp>/
│       └── summary.json
├── contract_gen/
│   └── <timestamp>/
│       ├── summary.json
│       ├── pass_01_info.yaml.json/
│       │   ├── prompt.txt
│       │   ├── response.txt
│       │   ├── processed.yaml
│       │   └── trace.json
│       └── pass_02_entities.yaml.json/
│           └── ...
├── ir_build/
├── code_build/
├── code_gen/
└── code_apply/
```

---

### Run Summary Format

**File:** `summary.json`

**Purpose:** High-level results of command execution.

**Example (contract_gen):**

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

**Purpose:** Detailed LLM interaction logs for debugging.

**Structure:**

```
pass_01_info.yaml.json/
├── prompt.txt           # Exact prompt sent to LLM
├── response.txt         # Raw LLM response
├── processed.yaml       # Cleaned YAML output
└── trace.json           # Metadata (tokens, duration, context)
```

**`trace.json` Example:**

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

**Created by:** `midicoder version create`

**Purpose:** Isolated workspace for each version/feature.

**Structure:**

```
.midicoder/versions/v0.1.0/
├── state.json           # Version metadata
├── master-brief.md      # Requirements (user-written)
├── contract-feedbacks.yml  # Contract review feedback (optional)
├── locks/               # Lock files
├── cache/               # LLM cache (ephemeral)
├── contracts/           # DSL contracts
├── irs/                 # Intermediate representation
├── plans/               # Code plans (pseudo code)
├── patches/             # Patch plans and operations
└── snapshots/           # Backups before apply
```

---

### `state.json` (Version-level)

**Purpose:** Version-specific metadata.

**Example:**

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

**Created by:** `midicoder version create` (template)

**Edited by:** User

**Purpose:** Natural language requirements that drive contract generation.

**Format:** Markdown with structured sections

**Template Sections:**

1. Overview
2. Domain & Data
3. Business Flows & Scenarios
4. Commands & Queries
5. Rules & Policy
6. Workflow / State Machine
7. API
8. Non-functional Requirements
9. Technical Constraints
10. Appendix

**See:** Template generated by `version create` for detailed structure.

---

### `contract-feedbacks.yml`

**Created by:** `midicoder contract feedback`

**Edited by:** User

**Purpose:** Contract review notes and repair instructions.

**Format:** YAML

**Example:**

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
      CreateOrder missing authorization guard.
    suggestion: |
      Add guard with permission = "create_order"
    last_error: null

notes:
  - "Follow RBAC guidelines"
  - "Use ISO 8601 for timestamps"
```

---

### `contracts/`

**Created by:** `midicoder contract gen`

**Purpose:** Structured DSL contracts (YAML).

**Structure:**

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

**See:** `technic/DSL-schema.md` for complete contract schema specification.

---

### `irs/`

**Created by:** `midicoder ir build`

**Purpose:** Normalized intermediate representation.

**Structure:**

```
irs/
├── ir.json              # Complete IR (all modules)
├── manifest.json        # Metadata, stats, unresolved refs
└── diagrams/            # Mermaid diagrams (optional)
    ├── api/
    │   ├── graphql_api_map.mmd
    │   └── http_api_map.mmd
    ├── commands/
    │   └── command_graph.mmd
    ├── entities/
    │   └── domain_model.mmd
    ├── workflows/
    │   └── subscription_lifecycle.mmd
    └── manifest.json
```

---

#### `ir.json`

**Format:** JSON

**Purpose:** Normalized, validated IR from all contracts.

**Structure:**

```json
{
  "version": "v0.1.0",
  "domain": {
    "entities": [...],
    "value_objects": [...],
    "errors": [...],
    "events": [...]
  },
  "application": {
    "commands": [...],
    "queries": [...]
  },
  "workflows": [...],
  "api": {
    "http_routes": [...],
    "graphql_schemas": [...]
  },
  "policy": {
    "roles": [...],
    "permissions": [...],
    "permission_maps": [...]
  },
  "rules": [...],
  "scenarios": [...]
}
```

**See:** `technic/IR-compiler.md` for IR schema details.

---

#### `manifest.json` (IR)

**Purpose:** IR build metadata and statistics.

**Example:**

```json
{
  "version": "v0.1.0",
  "timestamp": "2025-02-10T11:30:00Z",
  "source_contracts": [
    "contracts/domain/entities.yaml",
    "contracts/app/commands.yaml"
  ],
  "stats": {
    "entities": 5,
    "commands": 8,
    "queries": 3,
    "workflows": 2,
    "http_routes": 12,
    "errors": 6
  },
  "unresolved_refs": [],
  "warnings": []
}
```

---

### `plans/`

**Created by:** `midicoder code build`

**Purpose:** Pseudo code plans (FastAPI flavor).

**Structure:**

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

#### `index.json` (Plans)

**Purpose:** Registry of all code plans.

**Example:**

```json
{
  "version": "v0.1.0",
  "commands": ["create-user", "update-user"],
  "workflows": ["order-workflow"],
  "api": ["post-users", "get-users"]
}
```

---

#### Code Plan Format

**File:** `commands/create-user.code-plan.json`

**Purpose:** Pseudo code with folder structure and anchors.

**Example:**

```json
{
  "ir_refs": ["Command:CreateUser"],
  "folder": "app/api/users",
  "target": "fastapi",
  "files": {
    "router": {
      "path": "app/api/users/router.py",
      "sections": [
        {
          "anchor": "# midicoder:api:users:router:routes",
          "pseudo": "@router.post('/users')\nasync def create_user(data: CreateUserRequest, service: UserService = Depends(get_user_service)) -> UserResponse:\n    user = await service.create_user(data)\n    return UserResponse.from_orm(user)"
        }
      ]
    },
    "service": {
      "path": "app/api/users/service.py",
      "sections": [
        {
          "anchor": "# midicoder:api:users:service:handlers",
          "pseudo": "async def create_user(self, data: CreateUserRequest) -> User:\n    # Validate email\n    # Check duplicate\n    # Create user\n    # Save to database\n    return user"
        }
      ]
    },
    "schemas": {
      "path": "app/api/users/schemas.py",
      "sections": [
        {
          "anchor": "# midicoder:api:users:schemas:models",
          "pseudo": "class CreateUserRequest(BaseModel):\n    email: EmailStr\n    name: str\n    role: UserRole"
        }
      ]
    }
  },
  "warnings": []
}
```

---

### `patches/`

**Created by:** `midicoder code gen` and `midicoder code apply`

**Purpose:** Patch plans and applied operations.

**Structure:**

```
patches/
├── plans/               # Patch plans (from code gen)
│   ├── index.json
│   ├── commands/
│   │   └── create-user.patch-plan.json
│   └── workflows/
│       └── order-workflow.patch-plan.json
├── runtime/             # Runtime files (optional, with --runtime)
│   └── app/
│       └── api/
│           └── users/
│               ├── router.py
│               ├── service.py
│               └── schemas.py
└── <run_id>/            # Applied operations (from code apply)
    ├── ops.json
    └── *.patch
```

---

#### `index.json` (Patch Plans)

**Purpose:** Registry of all patch plans.

**Example:**

```json
{
  "version": "v0.1.0",
  "commands": ["create-user", "update-user"],
  "workflows": ["order-workflow"],
  "api": []
}
```

---

#### Patch Plan Format

**File:** `plans/commands/create-user.patch-plan.json`

**Purpose:** Executable patches with operations.

**Example:**

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
      "content": "@router.post('/users', response_model=UserResponse)\nasync def create_user(\n    data: CreateUserRequest,\n    service: UserService = Depends(get_user_service),\n) -> UserResponse:\n    user = await service.create_user(data)\n    return UserResponse.from_orm(user)"
    },
    {
      "path": "app/api/users/service.py",
      "operation": "edit",
      "anchor": "# midicoder:api:users:service:handlers",
      "mode": "after",
      "content": "async def create_user(self, data: CreateUserRequest) -> User:\n    if await self.repo.find_by_email(data.email):\n        raise ConflictError('Email already exists')\n    user = User(**data.dict())\n    await self.repo.save(user)\n    return user"
    }
  ]
}
```

**Operation Types:**

- `write`: Create new file with content
- `edit`: Modify existing file at anchor
- `delete`: Remove file

**Edit Modes:**

- `before`: Insert content before anchor
- `after`: Insert content after anchor
- `replace`: Replace content at anchor

---

#### `ops.json`

**Created by:** `midicoder code apply`

**Purpose:** Log of applied operations.

**Example:**

```json
[
  {
    "type": "edit",
    "path": "app/api/users/router.py",
    "anchor": "# midicoder:api:users:router:routes",
    "mode": "after",
    "content": "@router.post('/users')...",
    "status": "success",
    "timestamp": "2025-02-10T12:00:00Z"
  },
  {
    "type": "write",
    "path": "app/api/users/schemas.py",
    "content": "class CreateUserRequest(BaseModel):...",
    "status": "success",
    "timestamp": "2025-02-10T12:00:01Z"
  }
]
```

---

#### Unified Diffs (`.patch`)

**Purpose:** Git-style diffs of applied changes.

**Example:** `app_api_users_router.py.patch`

```diff
--- a/app/api/users/router.py
+++ b/app/api/users/router.py
@@ -15,7 +15,13 @@ router = APIRouter(prefix="/users", tags=["users"])
 
 
 # midicoder:api:users:router:routes
-# TODO: Add routes here
+@router.post('/users', response_model=UserResponse)
+async def create_user(
+    data: CreateUserRequest,
+    service: UserService = Depends(get_user_service),
+) -> UserResponse:
+    user = await service.create_user(data)
+    return UserResponse.from_orm(user)
 
 
 # End routes
```

---

### `snapshots/`

**Created by:** `midicoder code apply`

**Purpose:** Backup files before applying patches.

**Structure:**

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

**`manifest.json` Example:**

```json
{
  "run_id": "20250210_120000",
  "timestamp": "2025-02-10T12:00:00Z",
  "files": [
    "app/api/users/router.py",
    "app/api/users/service.py"
  ]
}
```

**Usage:** Restore files if patches cause issues.

---

## File Naming Conventions

### Timestamps

Format: `YYYYMMDD_HHMMSS`

Example: `20250210_120000` (Feb 10, 2025, 12:00:00)

### Slugs (for plans/patches)

Format: `kebab-case`

Examples:
- `create-user` (from Command:CreateUser)
- `order-workflow` (from Workflow:OrderWorkflow)
- `post-users` (from HttpRoute:POST /users)

### Trace Files (contract gen)

Format: `pass_<number>_<target_file>.json`

Examples:
- `pass_01_info.yaml.json`
- `pass_02_entities.yaml.json`
- `pass_03_commands.yaml.json`

---

## Gitignore Recommendations

Add to `.gitignore`:

```gitignore
# Midi Coder secrets and cache
.midicoder/secrets.json
.midicoder/versions/*/cache/

# Midi Coder runs (optional, useful for debugging)
# .midicoder/runs/

# Midi Coder snapshots (optional, temporary backups)
# .midicoder/snapshots/
```

**Recommended to commit:**

- `.midicoder/config.json` (without secrets)
- `.midicoder/versions/*/contracts/` (DSL contracts)
- `.midicoder/versions/*/master-brief.md` (requirements)
- `.midicoder/versions/*/contract-feedbacks.yml` (review notes)

**Optional to commit:**

- `.midicoder/context/` (can regenerate with `midicoder index`)
- `.midicoder/runs/` (useful for audit trail)
- `.midicoder/versions/*/irs/` (can regenerate with `ir build`)
- `.midicoder/versions/*/plans/` (can regenerate with `code build`)
- `.midicoder/versions/*/patches/` (can regenerate with `code gen`)

---

## Artifact Lifecycle

### Ephemeral (Regenerable)

These can be safely deleted and regenerated:

- `.midicoder/context/*` → Regenerate with `midicoder index`
- `.midicoder/versions/*/cache/*` → Regenerate automatically
- `.midicoder/versions/*/irs/*` → Regenerate with `midicoder ir build`
- `.midicoder/versions/*/plans/*` → Regenerate with `midicoder code build`
- `.midicoder/versions/*/patches/*` → Regenerate with `midicoder code gen`

### Persistent (Keep)

These should be preserved:

- `.midicoder/config.json` → Configuration
- `.midicoder/versions/*/master-brief.md` → Requirements (user-written)
- `.midicoder/versions/*/contracts/*` → Contracts (LLM-generated, expensive)
- `.midicoder/versions/*/contract-feedbacks.yml` → Review notes (user-written)

### Sensitive (Never Commit)

- `.midicoder/secrets.json` → API keys

### Audit Trail (Optional)

- `.midicoder/runs/*` → Execution logs (useful for debugging)
- `.midicoder/versions/*/snapshots/*` → Backups (temporary)

---

## Disk Space Management

### Typical Sizes

- `.midicoder/config.json`: ~1 KB
- `.midicoder/secrets.json`: ~1 KB
- `.midicoder/context/`: 100 KB - 5 MB (depends on project size)
- `.midicoder/runs/`: 10 KB - 100 MB (depends on run count)
- `.midicoder/versions/<version>/contracts/`: 10 KB - 500 KB
- `.midicoder/versions/<version>/irs/`: 50 KB - 2 MB
- `.midicoder/versions/<version>/plans/`: 100 KB - 5 MB
- `.midicoder/versions/<version>/patches/`: 100 KB - 10 MB
- `.midicoder/versions/<version>/snapshots/`: Varies (copy of modified files)

### Cleanup Recommendations

```bash
# Clean old runs (keep last 10)
ls -t .midicoder/runs/contract_gen/ | tail -n +11 | xargs rm -rf

# Clean snapshots after successful apply
rm -rf .midicoder/versions/*/snapshots/

# Clean cache
rm -rf .midicoder/versions/*/cache/

# Clean runtime files (if using --runtime)
rm -rf .midicoder/versions/*/patches/runtime/
```

---

## Artifact Validation

### Check Integrity

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

**Related Documentation:**

- [Pipeline Overview](pipeline.md): How artifacts flow through pipeline
- [CLI Commands](cli.md): Commands that create/modify artifacts
- [Configuration](config.md): Config file details
- [Troubleshooting](troubleshooting.md): Common artifact issues

**Technical Specs:**

- `technic/DSL-schema.md`: Contract file schemas
- `technic/IR-compiler.md`: IR JSON schema
- `technic/source-indexing.md`: Context extraction details
- `technic/codegen.md`: Plan and patch formats

---

## Summary

Midi Coder creates a comprehensive artifact tree:

### Core Configuration
- `config.json`: Main settings
- `secrets.json`: API keys (gitignored)
- `state.json`: Pipeline state

### Project Context
- `context/`: Indexed codebase structure
  - Stack detection, symbols, seams, exemplars

### Execution Logs
- `runs/`: Detailed logs per command
  - Traces for LLM interactions
  - Summaries and metadata

### Version Workspaces
- `versions/<version>/`:
  - `master-brief.md`: Requirements (user input)
  - `contracts/`: DSL YAML (LLM output)
  - `irs/`: Normalized IR JSON (deterministic)
  - `plans/`: Pseudo code (deterministic)
  - `patches/`: Real patches (LLM-assisted)
  - `snapshots/`: Backups before apply

**Key Principles:**

- Every step creates auditable artifacts
- Clear separation of concerns
- Deterministic artifacts vs LLM artifacts
- Version isolation for parallel development
- Git-friendly structure (`.gitignore` sensitive files)

**Next Steps:**

- See [Pipeline](pipeline.md) for how artifacts flow
- See [CLI Commands](cli.md) for commands that create artifacts
- See [Configuration](config.md) for config file details