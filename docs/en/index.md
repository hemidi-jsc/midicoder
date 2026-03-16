# Midi Coder Documentation

Welcome to Midi Coder - a **deterministic, contract-first code generation pipeline** that transforms requirements into production code through structured contracts.

## What is Midi Coder?

Midi Coder is an open-source CLI tool that helps you generate code from requirements while maintaining **full control, traceability, and determinism**.

### The Problem

Traditional code generation approaches face challenges:

- **Unpredictable**: LLM directly writes code with random variations
- **Unauditable**: No clear trace from requirements to code
- **Full rewrites**: Overwrites entire files, hard to review
- **Stack-locked**: Need different tools for different tech stacks

### The Midi Coder Solution

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
Working Code (Your project)
```

**Key Features:**

- **Contract-first**: DSL YAML as single source of truth
- **Deterministic**: Most steps are rule-based (no LLM randomness)
- **Patch-based**: Small, reviewable changes (not full file rewrites)
- **Auditable**: Every step creates versioned artifacts in `.midicoder/`
- **Multi-stack**: One IR → Multiple targets (FastAPI, NestJS, Angular)
- **LLM-assisted, not LLM-dependent**: LLMs only generate contracts and patch strategies

---

## Core Concepts

### 1. Contract-First Development

Instead of writing code directly, you write **requirements** which are transformed into **structured contracts** (DSL YAML):

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

These contracts are:
- **Validated**: Schema-checked before code generation
- **Versioned**: Stored in `.midicoder/versions/`
- **Auditable**: Full trace from requirement to implementation
- **Reusable**: Same contract → multiple stack implementations

### 2. Deterministic Pipeline

Most steps are **100% deterministic** (no LLM):

- **IR Build**: Contracts → IR (static validation)
- **Code Build**: IR → Pseudo code (rule-based mapping)
- **Code Apply**: Patches → Files (deterministic operations)

Only 2 steps use LLM:
- **Contract Gen**: Requirements → Contracts (LLM helps structure)
- **Code Gen**: Pseudo → Real patches (LLM decides locations)

### 3. Patch-Based Updates

Instead of rewriting entire files, Midi Coder generates **small patches**:

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

Benefits:
- Easy to review in pull requests
- Preserves your custom code
- Minimal merge conflicts
- Can rollback easily (snapshots included)

### 4. Multi-Stack Support

One set of contracts → Multiple implementations:

```
IR (stack-agnostic)
    ↓
FastAPI Pseudo Code
    ↓
├─→ FastAPI (Python)
├─→ NestJS (TypeScript)
└─→ Angular (TypeScript)
```

Currently supported:
- **FastAPI** (Python backend) - Full support
- **NestJS** (Node.js/TypeScript backend) - Via translation
- **Angular** (TypeScript frontend) - Via translation

---

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -U pip
pip install -e .
```

### 5-Minute Tutorial

```bash
# 1. Initialize workspace
cd /path/to/your/project
midicoder init

# 2. Index your codebase
midicoder index

# 3. Create version
midicoder version create v0.1.0

# 4. Write requirements (edit this file!)
vim .midicoder/versions/v0.1.0/master-brief.md

# 5. Generate contracts
midicoder contract gen

# 6. Build IR
midicoder ir build

# 7. Build code plans
midicoder code build

# 8. Generate patches
midicoder code gen

# 9. Preview changes
midicoder code apply --dry-run

# 10. Apply changes
midicoder code apply
```

**Result:** Your code is updated with new features! ✨

---

## Architecture Overview

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
│           ├── master-brief.md      # Requirements (YOU write this)
│           ├── contracts/           # DSL YAML (LLM generates)
│           ├── irs/                 # IR JSON (deterministic)
│           ├── plans/               # Pseudo code (deterministic)
│           ├── patches/             # Real patches (LLM-assisted)
│           └── snapshots/           # Backups
├── src/                     # Your source code
└── ...
```

### Pipeline Stages

| Stage | Input | Output | LLM? | Time |
|-------|-------|--------|------|------|
| **Init** | User input | config.json, secrets.json | | 1-2 min |
| **Index** | Source code | Project Context | | 10-60 sec |
| **Version** | Version ID | Version workspace | | <1 sec |
| **Contract Gen** | master-brief.md | contracts/*.yaml | High | 1-3 min |
| **IR Build** | contracts/ | ir.json | | 5-15 sec |
| **Code Build** | ir.json | plans/ | | 2-10 sec |
| **Code Gen** | plans/ | patches/ | High+Cheap | 1-3 min |
| **Code Apply** | patches/ | Working code | | 5-20 sec |

**Total Time:** ~5-10 minutes for typical feature

---

## Use Cases

### 1. New Feature Development

Write requirements → Generate contracts → Apply code

**Example:** Add user authentication system
- Write master-brief with auth requirements
- Generate contracts (entities, commands, API routes)
- Build and apply code
- Review and commit

### 2. API Evolution

Modify contracts → Regenerate code

**Example:** Add new field to User entity
- Update `contracts/domain/entities.yaml`
- Rebuild IR and regenerate patches
- Apply changes (only affected files)

### 3. Multi-Stack Development

One contract set → Multiple implementations

**Example:** Backend + Frontend from same contracts
- Write contracts once
- Generate FastAPI backend
- Generate Angular frontend
- Consistent API between stacks

### 4. Contract Refinement

Review → Feedback → Repair → Regenerate

**Example:** Add missing authorization checks
- Run `contract check`
- Create feedback with issues
- Run `contract repair` to fix
- Regenerate downstream artifacts

### 5. CI/CD Automation

Non-interactive pipeline for automation

**Example:** Auto-generate code in CI
- Use environment variables for config
- Run full pipeline non-interactively
- Generate code as part of build process

---

## Key Benefits

### For Developers

- **Clear requirements**: Structured, machine-readable contracts
- **Easy review**: Small patches instead of full file rewrites
- **Full control**: Edit contracts directly, no black box
- **Consistent style**: Generated code follows project conventions
- **Safe updates**: Snapshots and rollback support

### For Teams

- **Single source of truth**: Contracts define the system
- **Audit trail**: Full traceability from requirement to code
- **Version control**: All artifacts are versionable
- **Parallel development**: Isolated version workspaces
- **Stack flexibility**: Easy to add new target stacks

### For Projects

- **Deterministic**: Repeatable results (no random LLM behavior)
- **Scalable**: Handles large codebases efficiently
- **Maintainable**: Generated code is readable and follows patterns
- **Testable**: Generate test scenarios from contracts
- **Documentable**: Contracts serve as living documentation

---

## Design Philosophy

### Anti-AI Approach

Midi Coder follows an **"Anti-AI"** philosophy:

> "LLMs should assist humans in authoring requirements, not write code directly."

**Current State (v0.x):**
- LLM generates contracts from natural language (expensive but valuable)
- LLM decides patch strategies (contextual understanding needed)
- Most other steps are deterministic

**Future Vision (v1.x+):**
- Replace LLM with reverse engineering (extract contracts from code)
- Universal transpiler (IR → AST → Stack-specific emitters)
- AST-based understanding (Tree-sitter, not regex)
- Zero LLM dependency for common operations

See `technic/midicoder-algorithm.md` for roadmap details.

### Core Principles

1. **Contract-First**: Requirements as structured data, not comments
2. **Deterministic**: Prefer rules over randomness
3. **Patch-Based**: Small changes, easy to review
4. **Auditable**: Full trace from requirement to implementation
5. **Multi-Stack**: One IR → Multiple targets
6. **LLM-Assisted**: Use LLM for hard parts, not everything

---

## Documentation Structure

### Getting Started
- **[Getting Started](getting-started.md)**: Installation and 5-minute tutorial
- **[Non-Interactive Guide](non-interactive.md)**: Automation setup for CI/CD

### Core Documentation
- **[Pipeline Deep Dive](pipeline.md)**: Detailed explanation of each step
- **[CLI Commands](cli.md)**: Complete command reference
- **[Configuration](config.md)**: Config file structure and options
- **[Artifacts](artifacts.md)**: File structure and formats

### Working with Midi Coder
- **[Contracts](contracts.md)**: DSL contract specification
- **[IR](ir.md)**: Intermediate Representation details
- **[Code Generation](codegen.md)**: Code generation strategy
- **[Contract Repair](contract-repair.md)**: Feedback and repair workflow
- **[Project Context](project-context.md)**: Source indexing and context extraction

### Help & Support
- **[Troubleshooting](troubleshooting.md)**: Common issues and solutions
- **[FAQ](faq.md)**: Frequently asked questions
- **[Contributing](contributing.md)**: How to contribute

### Technical Specifications
- **`technic/DSL-schema.md`**: Complete DSL specification
- **`technic/IR-compiler.md`**: IR compilation algorithm
- **`technic/codegen.md`**: Code generation details
- **`technic/source-indexing.md`**: Context extraction algorithm
- **`technic/contract-repair.md`**: Repair workflow
- **`technic/midicoder-algorithm.md`**: R&D roadmap and future algorithms

---

## Community & Support

### Getting Help

- **Documentation**: Start with [Getting Started](getting-started.md)
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions in GitHub Discussions
- **Examples**: Check `midicoder/code/example/` for sample artifacts

### Contributing

Midi Coder is open source! Contributions welcome:

- Documentation improvements
- Bug reports and fixes
- New features
- Tests and examples
- Multi-stack support

See [Contributing Guide](contributing.md) for details.

---

## Quick Links

### For First-Time Users
1. [Installation](getting-started.md#installation)
2. [Quick Start Tutorial](getting-started.md#quick-start-5-minutes)
3. [Pipeline Overview](pipeline.md#pipeline-overview)

### For Developers
1. [CLI Command Reference](cli.md)
2. [Configuration Guide](config.md)
3. [Artifact Structure](artifacts.md)

### For Advanced Users
1. [Non-Interactive Mode](non-interactive.md)
2. [Contract Repair Workflow](contract-repair.md)
3. [Technical Specifications](pipeline.md#design-specs--technical-references)

---

## Next Steps

**New to Midi Coder?**
→ Start with [Getting Started](getting-started.md)

**Want to understand the pipeline?**
→ Read [Pipeline Deep Dive](pipeline.md)

**Need command reference?**
→ See [CLI Commands](cli.md)

**Setting up automation?**
→ Check [Non-Interactive Guide](non-interactive.md)

**Having issues?**
→ Visit [Troubleshooting](troubleshooting.md)

---

**Happy coding with Midi Coder!**
