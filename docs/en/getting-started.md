# Getting Started with Midi Coder

Welcome to Midi Coder! This guide will help you get started with contract-first, deterministic code generation.

## What is Midi Coder?

Midi Coder is a **deterministic pipeline** that transforms requirements into code through structured contracts:

```
Your Requirements → DSL Contracts → IR → Code Plans → Patches → Working Code
```

**Key Benefits:**

- **Contract-first**: Requirements as structured YAML (single source of truth)
- **Deterministic**: Repeatable results, no random LLM behavior
- **Patch-based**: Small, reviewable changes (not full file rewrites)
- **Auditable**: Every step creates traceable artifacts
- **Multi-stack**: Support FastAPI, NestJS, Angular from single contract

---

## System Requirements

- **Python** 3.9 or newer
- **pip** (Python package manager)
- **virtualenv** or `venv` (recommended)
- **Git** (for version control)

**Operating Systems:**

- Linux (tested on Ubuntu 20.04+)
- macOS (tested on 11.0+)
- Windows (tested on Windows 10+)

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/hemidi-jsc/midicoder.git
cd midicoder
```

### Step 1: Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### Step 2: Install Midi Coder

```bash
# Upgrade pip
pip install -U pip

# Install Midi Coder in development mode
pip install -e .
```

### Step 3: Verify Installation

```bash
# Check version
midicoder --help

# Should show available commands
```

---

## Quick Start (5 Minutes)

### 1. Initialize Workspace

```bash
cd /path/to/your/project
midicoder init
```

The interactive wizard will ask:

- **Working directory**: Path to your project (default: current directory)
- **Tech stack**: Choose one or more (FastAPI, NestJS, Angular)
- **High-tier LLM**: For complex tasks (contract generation, patch planning)
  - Provider: Anthropic or OpenAI
  - Model: e.g., `claude-sonnet-4-5` or `gpt-4`
  - API Key: Your API key
- **Cheap-tier LLM**: For simple tasks (stack translation)
  - Provider: Anthropic or OpenAI
  - Model: e.g., `claude-3-5-haiku` or `gpt-3.5-turbo`
  - API Key: Your API key

**Result:** Creates `.midicoder/` with `config.json` and `secrets.json`

### 2. Index Your Project

```bash
midicoder index
```

This scans your codebase and creates **Project Context**:

- Detects your tech stack
- Finds classes, functions, methods
- Identifies safe injection points (seams)
- Extracts code examples (exemplars)

**Result:** Creates `.midicoder/context/` with symbols, entrypoints, seams, etc.

**Time:** Usually 10-60 seconds depending on project size.

### 3. Create Version

```bash
midicoder version create v0.1.0
```

Creates workspace for this version:

- Version directory: `.midicoder/versions/v0.1.0/`
- Template: `master-brief.md` (edit this next!)

### 4. Write Requirements

Edit `.midicoder/versions/v0.1.0/master-brief.md`:

```bash
vim .midicoder/versions/v0.1.0/master-brief.md
# or use your favorite editor
```

**Template sections:**

1. **Overview**: Goals, scope, glossary
2. **Domain & Data**: Entities, value objects, errors
3. **Business Flows**: User journeys, scenarios
4. **Commands & Queries**: CQRS operations
5. **Rules & Policy**: Business rules, RBAC
6. **Workflow**: State machines
7. **API**: HTTP routes, GraphQL
8. **Non-functional**: Performance, security
9. **Technical Constraints**: Stack conventions

**Example (minimal):**

```markdown
# Master Brief: User Management

## 1. Overview

Simple user CRUD with authentication.

## 2. Domain & Data

**Entities:**
- User: id, email, name, role, created_at

**Errors:**
- UserNotFound: When user ID doesn't exist
- EmailAlreadyExists: When email is duplicate

## 4. Commands & Queries

**Commands:**
- CreateUser: email, name, role → User
  - Validates email format
  - Checks for duplicates
  - Creates user with hashed password
  - Emits UserCreated event

**Queries:**
- GetUser: user_id → User
- ListUsers: filters → User[]

## 5. Rules & Policy

**RBAC:**
- Roles: admin, user
- Permissions:
  - create_user (admin only)
  - read_user (all authenticated)
  - update_user (admin or self)
  - delete_user (admin only)

## 7. API

**Routes:**
- POST /users (CreateUser) - admin
- GET /users/:id (GetUser) - authenticated
- GET /users (ListUsers) - authenticated
- PUT /users/:id (UpdateUser) - admin or self
- DELETE /users/:id (DeleteUser) - admin
```

### 5. Generate Contracts

```bash
midicoder contract gen
```

LLM reads your `master-brief.md` and generates structured contracts:

- `contracts/domain/entities.yaml`
- `contracts/domain/errors.yaml`
- `contracts/app/commands.yaml`
- `contracts/app/queries.yaml`
- `contracts/policy/rbac.yaml`
- `contracts/api/http.yaml`

**Time:** 1-3 minutes depending on complexity.

**If it fails:** Run `midicoder contract gen resume` to retry only failed files.

### 6. Build IR (Intermediate Representation)

```bash
midicoder ir build
```

Compiles contracts into normalized IR JSON:

- Validates all contracts (schema, cross-refs)
- Normalizes IDs and references
- Generates Mermaid diagrams (optional)

**Time:** 5-15 seconds.

**Result:** `.midicoder/versions/v0.1.0/irs/ir.json`

### 7. Build Code Plans

```bash
midicoder code build
```

Generates pseudo code plans (FastAPI flavor):

- Deterministic (no LLM)
- Folder-level organization
- Uses anchors for injection points

**Time:** 2-10 seconds.

**Result:** `.midicoder/versions/v0.1.0/plans/`

### 8. Generate Patch Plans

```bash
midicoder code gen
```

Transforms pseudo code into real patches:

- **Step 1 (high-tier LLM)**: Decides WHERE and HOW to patch
- **Step 2 (cheap-tier LLM)**: Converts to target stack (if not FastAPI)

**Time:** 1-3 minutes depending on complexity.

**Result:** `.midicoder/versions/v0.1.0/patches/plans/`

### 9. Preview Changes

```bash
midicoder code apply --dry-run
```

Shows what would be changed without actually modifying files.

Review the output to ensure patches are correct.

### 10. Apply Changes

```bash
midicoder code apply
```

Applies patches to your working directory:

- Creates snapshots (backups)
- Applies write/edit/delete operations
- Records operations in `ops.json`
- Generates unified diffs
- Reindexes changed files

**Time:** 5-20 seconds.

**Result:** Your code is updated! ✨

---

## What Just Happened?

Let's trace what Midi Coder did:

1. **Init**: Setup workspace, saved config and API keys
2. **Index**: Scanned your codebase, extracted structure
3. **Version**: Created isolated workspace for v0.1.0
4. **Your work**: Wrote requirements in `master-brief.md`
5. **Contract Gen**: LLM generated structured DSL contracts
6. **IR Build**: Compiled contracts into normalized IR (deterministic)
7. **Code Build**: Generated pseudo code plans (deterministic)
8. **Code Gen**: LLM generated real patches with locations
9. **Code Apply**: Applied patches safely to your code

**Key Points:**

- LLM only used in steps 5 and 8
- Steps 6 and 7 are 100% deterministic
- Every step creates auditable artifacts
- Changes are patch-based (not file rewrites)

---

## Inspecting Artifacts

### Configuration

```bash
# View config
cat .midicoder/config.json

# View state
cat .midicoder/state.json

# View secrets (API keys)
cat .midicoder/secrets.json
```

### Project Context

```bash
# View detected stack and conventions
cat .midicoder/context/profile.json

# View symbols (classes, functions)
cat .midicoder/context/symbols.json

# View safe injection points
cat .midicoder/context/seams.json

# View code examples
cat .midicoder/context/exemplars.json
```

### Contracts (DSL)

```bash
# View entities
cat .midicoder/versions/v0.1.0/contracts/domain/entities.yaml

# View commands
cat .midicoder/versions/v0.1.0/contracts/app/commands.yaml

# View API routes
cat .midicoder/versions/v0.1.0/contracts/api/http.yaml
```

### IR (Intermediate Representation)

```bash
# View normalized IR
cat .midicoder/versions/v0.1.0/irs/ir.json

# View metadata
cat .midicoder/versions/v0.1.0/irs/manifest.json

# View diagrams (if generated)
ls .midicoder/versions/v0.1.0/irs/diagrams/
```

### Code Plans

```bash
# View plan registry
cat .midicoder/versions/v0.1.0/plans/index.json

# View a command plan
cat .midicoder/versions/v0.1.0/plans/commands/create-user.code-plan.json
```

### Patch Plans

```bash
# View patch registry
cat .midicoder/versions/v0.1.0/patches/plans/index.json

# View a patch plan
cat .midicoder/versions/v0.1.0/patches/plans/commands/create-user.patch-plan.json
```

### Applied Operations

```bash
# Find latest apply run
ls -lt .midicoder/versions/v0.1.0/patches/

# View operations
cat .midicoder/versions/v0.1.0/patches/<run_id>/ops.json

# View unified diff
cat .midicoder/versions/v0.1.0/patches/<run_id>/*.patch
```

---

## Next Steps

### Iterating on Contracts

If you need to refine contracts:

```bash
# 1. Check for issues
midicoder contract check

# 2. Create feedback file
midicoder contract feedback

# 3. Edit feedback
vim .midicoder/versions/v0.1.0/contract-feedbacks.yml

# 4. Validate feedback
midicoder contract repair prepare

# 5. Apply repairs
midicoder contract repair run

# 6. Rebuild downstream
midicoder ir build
midicoder code build
midicoder code gen
midicoder code apply --dry-run
midicoder code apply
```

### Working with Multiple Versions

```bash
# Create new version
midicoder version create v0.2.0

# Edit master-brief.md for v0.2.0
vim .midicoder/versions/v0.2.0/master-brief.md

# Run pipeline for v0.2.0
midicoder contract gen
# ... (continue pipeline)
```

### Incremental Reindexing

After manual code changes:

```bash
# Reindex specific files
midicoder index reindex --path src/users/service.py src/auth/controller.py

# Regenerate patches with fresh context
midicoder code gen
midicoder code apply --dry-run
midicoder code apply
```

---

## CI/CD Integration

For automation, use non-interactive mode:

```bash
# Set environment variables
export MIDICODER_WORKING_DIR=/app
export MIDICODER_STACK=fastapi
export MIDICODER_LLM_HIGH_PROVIDER=anthropic
export MIDICODER_LLM_HIGH_MODEL=claude-sonnet-4-5
export MIDICODER_LLM_HIGH_API_KEY=$ANTHROPIC_API_KEY
export MIDICODER_LLM_CHEAP_PROVIDER=anthropic
export MIDICODER_LLM_CHEAP_MODEL=claude-3-5-haiku
export MIDICODER_LLM_CHEAP_API_KEY=$ANTHROPIC_API_KEY

# Initialize non-interactively
midicoder init --non-interactive

# Run pipeline
midicoder index
midicoder version create $CI_COMMIT_TAG
cp docs/requirements.md .midicoder/versions/$CI_COMMIT_TAG/master-brief.md
midicoder contract gen
midicoder ir build --skip-diagrams
midicoder code build
midicoder code gen
midicoder code apply --force
```

**See:** [Non-Interactive Guide](non-interactive.md) for complete automation setup.

---

## Common Issues

### `No current version set`

**Solution:** Run `midicoder version create <version>` first.

### `master-brief.md is missing`

**Solution:** The version wasn't created properly. Recreate or add file manually.

### Contract generation fails

**Solution:** 
1. Check LLM API key is valid
2. Review `master-brief.md` for clarity
3. Use `midicoder contract gen resume` to retry

### IR build fails

**Solution:**
1. Run `midicoder contract check` to see issues
2. Fix contracts or use `midicoder contract feedback` + `repair`
3. Retry `midicoder ir build`

### Code apply conflicts

**Solution:**
1. Review with `--dry-run`
2. Manually resolve conflicts
3. Use `--force` only if you're sure (may cause merge issues)

**See:** [Troubleshooting](troubleshooting.md) for more issues and solutions.

---

## Learning Resources

### Documentation

- **[Pipeline Deep Dive](pipeline.md)**: Detailed explanation of each step
- **[CLI Commands](cli.md)**: Complete command reference
- **[Configuration](config.md)**: Config file structure and options
- **[Artifacts](artifacts.md)**: File structure and formats
- **[Non-Interactive Guide](non-interactive.md)**: Automation setup
- **[Troubleshooting](troubleshooting.md)**: Common issues
- **[FAQ](faq.md)**: Frequently asked questions

### Technical Specifications

- **`technic/DSL-schema.md`**: Complete DSL specification
- **`technic/IR-compiler.md`**: IR compilation algorithm
- **`technic/codegen.md`**: Code generation strategy
- **`technic/source-indexing.md`**: Project Context extraction
- **`technic/contract-repair.md`**: Feedback & repair workflow
- **`technic/midicoder-algorithm.md`**: Algorithm designs and future roadmap

### Example Projects

Check `midicoder/code/example/` for:

- Example IR JSON
- Example code plans
- Example patch plans
- Example contracts

---

## Getting Help

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
# List all available configuration options
midicoder init --config-list
```

### Community & Support

- **Issues**: Report bugs on GitHub
- **Discussions**: Ask questions in GitHub Discussions
- **Contributing**: See [Contributing Guide](contributing.md)

---

## Best Practices

### Writing master-brief.md

1. **Be specific**: "User must have valid email" not "User has email"
2. **Include error cases**: What errors can occur and when?
3. **Define permissions**: Who can do what?
4. **Describe workflows**: What are the state transitions?
5. **Reference existing code**: Mention files/classes if extending existing system

### Contract Iteration

1. Always run `contract check` before `ir build`
2. Use `contract feedback` + `repair` instead of regenerating everything
3. Review contracts before proceeding to code generation
4. Version control contracts alongside code

### Code Application

1. Always use `--dry-run` first to preview changes
2. Review diffs before applying
3. Commit generated code in separate commits for easy review
4. Run tests after applying patches

### Project Organization

1. Use semantic versioning for versions (`v1.0.0`, `v1.1.0`)
2. Or use feature names (`feature-auth`, `refactor-payments`)
3. Keep `master-brief.md` updated with implemented features
4. Use contract feedback for ongoing refinements

---

## What's Next?

Now that you've completed the quick start:

1. **Explore the pipeline**: Read [Pipeline Deep Dive](pipeline.md)
2. **Learn all commands**: Check [CLI Commands](cli.md)
3. **Setup automation**: See [Non-Interactive Guide](non-interactive.md)
4. **Understand artifacts**: Review [Artifacts](artifacts.md)
5. **Dive into DSL**: Study `technic/DSL-schema.md`

**Happy coding with Midi Coder!**
