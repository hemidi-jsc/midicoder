# CLI Commands Reference

Complete reference for all Midi Coder CLI commands.

## Core Pipeline Commands

### `midicoder init`

Initialize `.midicoder/` workspace and configuration.

**Usage:**

```bash
# Interactive mode (default)
midicoder init

# Non-interactive mode (CI/CD)
midicoder init --non-interactive

# List all configuration options
midicoder init --config-list
```

**Options:**

- `--non-interactive, -y`: Run in non-interactive mode
- `--config-list`: Show all available configuration keywords and exit
- `--env-prefix`: Environment variable prefix (default: `MIDICODER_`)
- `--rewrite-config`: Allow overwrite of existing `.midicoder/config.json` in non-interactive mode (or set `MIDICODER_REWRITE_CONFIG=true`)
- `--working-dir`: Working directory path
- `--stack`: Comma-separated tech stack(s) (e.g., `fastapi,nest,angular`)
- Provider `openai_compatible`:
  - `--llm-high-provider`: High-tier provider (`anthropic`, `openai`, `openai_compatible`, `bedrock`, `azure`, `vertex_partner`)
  - `--llm-cheap-provider`: Cheap-tier LLM provider
  - `--llm-high-model`, `--llm-high-url`, `--llm-high-key`, `--llm-high-key-env`
  - `--llm-cheap-model`, `--llm-cheap-url`, `--llm-cheap-key`, `--llm-cheap-key-env`
- Provider `anthropic`:
  - `--llm-high-anthropic-model`, `--llm-high-anthropic-key`, `--llm-high-anthropic-key-env`
  - `--llm-cheap-anthropic-model`, `--llm-cheap-anthropic-key`, `--llm-cheap-anthropic-key-env`
- Provider `openai`:
  - `--llm-high-openai-model`, `--llm-high-openai-key`, `--llm-high-openai-key-env`
  - `--llm-cheap-openai-model`, `--llm-cheap-openai-key`, `--llm-cheap-openai-key-env`
- Provider `bedrock`:
  - `--llm-high-bedrock-model`, `--llm-high-aws-region-name`, `--llm-high-aws-access-key-id`, `--llm-high-aws-access-key-id-env`, `--llm-high-aws-secret-access-key`, `--llm-high-aws-secret-access-key-env`
  - `--llm-cheap-bedrock-model`, `--llm-cheap-aws-region-name`, `--llm-cheap-aws-access-key-id`, `--llm-cheap-aws-access-key-id-env`, `--llm-cheap-aws-secret-access-key`, `--llm-cheap-aws-secret-access-key-env`
- Provider `azure`:
  - `--llm-high-azure-model`, `--llm-high-azure-key`, `--llm-high-azure-key-env`, `--llm-high-azure-openai-endpoint`, `--llm-high-azure-openai-api-version`, `--llm-high-azure-openai-deployment`
  - `--llm-cheap-azure-model`, `--llm-cheap-azure-key`, `--llm-cheap-azure-key-env`, `--llm-cheap-azure-openai-endpoint`, `--llm-cheap-azure-openai-api-version`, `--llm-cheap-azure-openai-deployment`
- Provider `vertex_partner`:
  - `--llm-high-vertex-model`, `--llm-high-vertex-key`, `--llm-high-vertex-key-env`, `--llm-high-vertex-project`, `--llm-high-vertex-location`
  - `--llm-cheap-vertex-model`, `--llm-cheap-vertex-key`, `--llm-cheap-vertex-key-env`, `--llm-cheap-vertex-project`, `--llm-cheap-vertex-location`

**Outputs:**

- `.midicoder/config.json`: Main configuration
- `.midicoder/secrets.json`: API keys (gitignored)
- `.midicoder/state.json`: Pipeline state

**Behavior notes:**

- Interactive mode asks for confirmation before overwriting an existing config.
- Non-interactive mode fails fast if config already exists unless overwrite is explicitly allowed (`--rewrite-config` or `MIDICODER_REWRITE_CONFIG=true`).
- When using a custom `--env-prefix`, rewrite env name follows that prefix (for example `MC_REWRITE_CONFIG=true` for `--env-prefix MC_`).
- Overwrite updates only `config.json` and `secrets.json`; existing runs/logs/versions/index are kept.
- API keys are optional at init time (some providers can use external credentials such as IAM), but missing keys can still fail later when calling LLM APIs.

**Examples:**

```bash
# Interactive setup
midicoder init

# Non-interactive with environment variables
export MIDICODER_WORKING_DIR=/path/to/project
export MIDICODER_STACK=fastapi,nest
export MIDICODER_LLM_HIGH_PROVIDER=anthropic
export MIDICODER_LLM_HIGH_ANTHROPIC_MODEL=anthropic/claude-3-7-sonnet-latest
export MIDICODER_LLM_HIGH_ANTHROPIC_API_KEY=sk-ant-...
export MIDICODER_LLM_CHEAP_PROVIDER=anthropic
export MIDICODER_LLM_CHEAP_ANTHROPIC_MODEL=anthropic/claude-3-5-haiku-latest
export MIDICODER_LLM_CHEAP_ANTHROPIC_API_KEY=sk-ant-...
midicoder init --non-interactive

# Non-interactive with CLI flags
midicoder init \
  --non-interactive \
  --working-dir /path/to/project \
  --stack fastapi \
  --llm-high-provider anthropic \
  --llm-high-anthropic-model anthropic/claude-3-7-sonnet-latest \
  --llm-high-anthropic-key-env ANTHROPIC_API_KEY \
  --llm-cheap-provider anthropic \
  --llm-cheap-anthropic-model anthropic/claude-3-5-haiku-latest \
  --llm-cheap-anthropic-key-env ANTHROPIC_API_KEY

# Overwrite existing config in non-interactive mode
midicoder init --non-interactive --rewrite-config
```

**See also:** [Non-Interactive Guide](non-interactive.md)

---

### `midicoder index`

Build Project Context by scanning source code.

**Usage:**

```bash
# Full index (first time or complete refresh)
midicoder index

# Incremental reindex (changed files only)
midicoder index reindex --path src/users/controller.py src/auth/service.py
```

**Options:**

- `--path`: List of changed file paths (relative to working_dir) for incremental reindex

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

**When to use:**

- After `midicoder init` (first time)
- When codebase structure changes significantly
- Before `midicoder contract gen` (to provide fresh context)
- After `midicoder code apply` (automatic unless `--no-reindex`)

---

### `midicoder version create`

Create a new version workspace.

**Usage:**

```bash
midicoder version create <version>
```

**Arguments:**

- `<version>`: Version identifier (e.g., `0.1.0`, `feature-auth`, `v1.2.0`)

**Outputs:**

```
.midicoder/versions/<version>/
├── state.json           # Version metadata
├── master-brief.md      # Requirements template (user edits this)
├── locks/               # Lock files
├── contracts/           # DSL contracts (from contract gen)
├── irs/                 # IR JSON (from ir build)
├── plans/               # Code plans (from code build)
├── patches/             # Patch plans (from code gen)
└── snapshots/           # Backups (from code apply)
```

**Next steps:**

1. Edit `.midicoder/versions/<version>/master-brief.md`
2. Run `midicoder contract gen`

---

### `midicoder contract gen`

Generate DSL contracts from `master-brief.md`.

**Usage:**

```bash
# Generate all contracts
midicoder contract gen

# Resume from failed run (smart retry)
midicoder contract gen resume
```

**Inputs:**

- `.midicoder/versions/<version>/master-brief.md` (user-written)
- `.midicoder/context/*` (Project Context)
- DSL schema (built-in)
- LLM config (high-tier model)

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

The `resume` subcommand analyzes the latest run and only regenerates failed or missing files:

```bash
midicoder contract gen resume
```

- Saves up to 50% tokens
- Validates existing files
- Retries only what's needed

**Traceability:**

Each run creates detailed traces in `.midicoder/runs/contract_gen/<timestamp>/`:

- `summary.json`: Overall status
- `pass_*_*.json`: Per-file trace with prompt, response, processed YAML

**Next steps:**

1. Review generated contracts in `contracts/`
2. Optionally run `midicoder contract check`
3. Run `midicoder ir build`

---

### `midicoder ir build`

Compile contracts into Intermediate Representation (IR).

**Usage:**

```bash
# Build IR with diagrams
midicoder ir build

# Build IR without diagrams (faster)
midicoder ir build --skip-diagrams
```

**Options:**

- `--skip-diagrams`: Skip Mermaid diagram generation

**Inputs:**

- `.midicoder/versions/<version>/contracts/**/*.yaml`

**Outputs:**

```
.midicoder/versions/<version>/irs/
├── ir.json              # Complete normalized IR
├── manifest.json        # Metadata, stats, unresolved refs
└── diagrams/            # (optional)
    ├── api/*.mmd
    ├── commands/*.mmd
    ├── entities/*.mmd
    └── workflows/*.mmd
```

**Process (100% deterministic, no LLM):**

1. Load all YAML files
2. Validate against Pydantic schema
3. Check cross-references
4. Normalize IDs and format
5. Build IR modules
6. Generate diagrams (optional)

**Next steps:**

1. Review `ir.json` or generated diagrams
2. Run `midicoder code build`

---

### `midicoder code build`

Generate pseudo code plans from IR.

**Usage:**

```bash
midicoder code build
```

**Inputs:**

- `.midicoder/versions/<version>/irs/ir.json`
- `.midicoder/context/*` (Project Context)

**Outputs:**

```
.midicoder/versions/<version>/plans/
├── index.json           # Plan registry
├── commands/*.code-plan.json
├── workflows/*.code-plan.json
└── api/*.code-plan.json
```

**Process (100% deterministic, no LLM):**

1. Load IR JSON
2. Extract components (Commands, Workflows, API)
3. Map to folder structure
4. Generate pseudo code with anchors

**Next steps:**

1. Review plans in `plans/`
2. Run `midicoder code gen`

---

### `midicoder code gen`

Generate patch plans from pseudo code plans.

**Usage:**

```bash
# Generate patch plans only (default)
midicoder code gen

# Generate patch plans + runtime files
midicoder code gen --runtime
```

**Options:**

- `--runtime`: Also generate runtime source files into `.midicoder/versions/<version>/patches/runtime/`

**Inputs:**

- `.midicoder/versions/<version>/plans/`
- `.midicoder/context/*` (Project Context)
- LLM config (high-tier for patch strategy, cheap-tier for stack conversion)

**Outputs:**

```
.midicoder/versions/<version>/patches/
├── plans/
│   ├── index.json       # Patch plan registry
│   ├── commands/*.patch-plan.json
│   ├── workflows/*.patch-plan.json
│   └── api/*.patch-plan.json
└── runtime/             # (optional, with --runtime)
    └── generated source files
```

**Process:**

1. **Step 1 (high-tier LLM)**: Decide patch locations and operations
2. **Step 2 (cheap-tier LLM or skip)**: Convert to target stack syntax
   - Skip if target = FastAPI
   - Translate if target = NestJS/Angular

**Next steps:**

1. Review patch plans in `patches/plans/`
2. Optionally review runtime files (if `--runtime`)
3. Run `midicoder code apply`

---

### `midicoder code apply`

Apply patch plans to working directory.

**Usage:**

```bash
# Apply patches (with safety checks)
midicoder code apply

# Preview without applying
midicoder code apply --dry-run

# Force apply (skip conflict checks)
midicoder code apply --force

# Apply without reindexing (debug only)
midicoder code apply --no-reindex
```

**Options:**

- `--dry-run`: Preview operations without writing files
- `--force`: Force apply when conflicts detected (may cause merge issues)
- `--no-reindex`: Disable automatic reindexing after apply (not recommended)

**Inputs:**

- `.midicoder/versions/<version>/patches/plans/`

**Outputs:**

```
.midicoder/versions/<version>/patches/<run_id>/
├── ops.json             # Applied operations log
└── *.patch              # Unified diffs

.midicoder/versions/<version>/snapshots/<run_id>/
└── backed up files
```

**Process:**

1. Pre-flight checks (validate plans, check writability, detect conflicts)
2. Create snapshots
3. Apply patches (write/edit/delete operations)
4. Verify and record operations
5. Reindex (update Project Context)

**Safety features:**

- Snapshots before modification
- Conflict detection
- Dry run mode
- Rollback capability

---

## Contract Utilities

### `midicoder contract check`

Validate contracts for issues.

**Usage:**

```bash
midicoder contract check
```

**Checks:**

- YAML syntax
- Schema compliance (Pydantic validation)
- Cross-references (Entity/Command/Workflow/etc.)
- Business logic consistency

**Output:**

- Success: Exit code 0, no issues found
- Failure: Exit code 1, list of issues with locations and suggestions

**Example output:**

```
[contract check] FAILED – 3 issue(s) found
- contracts/app/commands.yaml:15: Command 'CreateOrder' references unknown entity 'Order'
  Suggestion: Add 'Order' entity in domain/entities.yaml or fix reference
- contracts/domain/entities.yaml:42: Duplicate entity ID 'User' found
- contracts/api/http.yaml:8: Route '/orders' references unknown command 'ListOrders'
```

---

### `midicoder contract feedback`

Create/update feedback file for contract review.

**Usage:**

```bash
midicoder contract feedback
```

**Process:**

1. Run `contract check` to get validation issues
2. Create/update `.midicoder/versions/<version>/contract-feedbacks.yml`
3. Add new feedback items from validation issues

**Output:**

```
.midicoder/versions/<version>/contract-feedbacks.yml
```

**Example feedback file:**

```yaml
meta:
  version: "0.1.0"
  author: "you@team"
  created_at: "2025-02-10T10:15:00Z"
  scope: "contracts"

items:
  - id: FB-001
    file: contracts/app/commands.yaml
    location: "commands[id=CreateOrder]"
    status: pending  # pending | in_progress | done | error
    issue: |
      CreateOrder command missing authorization guard.
    suggestion: |
      Add guard with permission = "create_order"

notes:
  - "Follow RBAC guidelines"
```

**Next steps:**

1. Edit feedback file to add custom review notes
2. Run `midicoder contract repair prepare` to validate
3. Run `midicoder contract repair run` to apply fixes

---

### `midicoder contract repair prepare`

Validate feedback file without running LLM.

**Usage:**

```bash
midicoder contract repair prepare
```

**Checks:**

- Feedback file syntax (YAML)
- Referenced files exist
- Referenced locations valid
- No duplicate feedback IDs

**Output:**

- Success: Feedback is valid
- Failure: List of validation errors

**Use case:** Dry-run validation before expensive LLM repair operation.

---

### `midicoder contract repair run`

Apply feedback items to contracts using LLM.

**Usage:**

```bash
midicoder contract repair run
```

**Inputs:**

- `.midicoder/versions/<version>/contract-feedbacks.yml`
- `.midicoder/versions/<version>/contracts/`
- `.midicoder/versions/<version>/master-brief.md`
- DSL schema
- LLM config (high-tier model)

**Process:**

1. Load feedback file
2. Group feedback items by file
3. Process files in dependency order
4. For each file:
   - LLM generates patches based on feedback
   - Validate patches against schema
   - Apply patches to contract file
5. Sync `master-brief.md` with changes
6. Extract memos to `.midicoder/context/memos/`
7. Update feedback status (pending → done/error)

**Outputs:**

- Updated contract files
- Updated `master-brief.md`
- Memos in `.midicoder/context/memos/`
- Updated `contract-feedbacks.yml` with status

**Benefits:**

- Iterative contract refinement
- Knowledge retention (memos)
- Full audit trail

---

## Configuration Commands

### `midicoder config get`

Get a configuration value.

**Usage:**

```bash
midicoder config get <key>
```

**Example:**

```bash
midicoder config get working_dir
midicoder config get stack
midicoder config get llm.high.model
```

---

### `midicoder config set`

Set a configuration value.

**Usage:**

```bash
midicoder config set <key> <value>
```

**Example:**

```bash
midicoder config set working_dir /new/path
midicoder config set stack fastapi,nest
```

---

### `midicoder config list`

List all configuration.

**Usage:**

```bash
midicoder config list
```

**Output:** JSON formatted configuration from `.midicoder/config.json`

---

### `midicoder config validate`

Validate configuration file.

**Usage:**

```bash
midicoder config validate
```

**Checks:**

- JSON syntax
- Required fields present
- Valid values (stack, LLM providers, etc.)

---

### `midicoder config secrets list`

List all secret categories.

**Usage:**

```bash
midicoder config secrets list
```

**Output:** List of secret categories (e.g., `llm`)

---

### `midicoder config secrets get`

Get secret value for a category and key.

**Usage:**

```bash
midicoder config secrets get <category> <key>
```

**Example:**

```bash
midicoder config secrets get llm high
```

**Output:** API key (masked for security)

---

### `midicoder config secrets set`

Set secret value for a category and key.

**Usage:**

```bash
midicoder config secrets set <category> <key>
```

**Example:**

```bash
midicoder config secrets set llm high
# Prompts for API key (hidden input)
```

---

### `midicoder config secrets delete`

Delete all secrets for a category.

**Usage:**

```bash
midicoder config secrets delete <category>
```

**Example:**

```bash
midicoder config secrets delete llm
```

---

### `midicoder config reset`

Reset configuration to defaults (prompts for confirmation).

**Usage:**

```bash
midicoder config reset
```

**Warning:** This will delete `config.json` and `secrets.json`. You'll need to run `midicoder init` again.

---

## Brief Commands (Advanced)

### `midicoder brief analyze`

Analyze master brief for contract generation planning.

**Usage:**

```bash
midicoder brief analyze
```

**Process:**

- Uses LLM to analyze `master-brief.md`
- Identifies required contract files
- Extracts keywords and structure

**Output:** Analysis results in `.midicoder/versions/<version>/cache/`

**Use case:** Preview what contracts will be generated before running `contract gen`.

---

### `midicoder brief rewrite`

Rewrite master brief based on analysis.

**Usage:**

```bash
midicoder brief rewrite
```

**Process:**

- Analyzes current `master-brief.md`
- Reorganizes content to better align with DSL schema
- Suggests improvements

**Warning:** This is experimental. Always backup `master-brief.md` before running.

---

## Command Cheat Sheet

### Full Pipeline (First Time)

```bash
# 1. Initialize workspace
midicoder init

# 2. Index project
midicoder index

# 3. Create version
midicoder version create v0.1.0

# 4. Edit master-brief.md (user action)
vim .midicoder/versions/v0.1.0/master-brief.md

# 5. Generate contracts
midicoder contract gen

# 6. Build IR
midicoder ir build

# 7. Build code plans
midicoder code build

# 8. Generate patch plans
midicoder code gen

# 9. Apply patches
midicoder code apply --dry-run  # Preview first
midicoder code apply            # Actually apply
```

### Contract Iteration

```bash
# Check contracts
midicoder contract check

# Create feedback file
midicoder contract feedback

# Edit feedback (user action)
vim .midicoder/versions/v0.1.0/contract-feedbacks.yml

# Validate feedback
midicoder contract repair prepare

# Apply repairs
midicoder contract repair run

# Rebuild IR and continue
midicoder ir build
midicoder code build
midicoder code gen
midicoder code apply
```

### Resume Failed Generation

```bash
# If contract gen failed partway
midicoder contract gen resume

# Continue pipeline
midicoder ir build
midicoder code build
midicoder code gen
midicoder code apply
```

### CI/CD Automation

```bash
# Non-interactive init
export MIDICODER_WORKING_DIR=/app
export MIDICODER_STACK=fastapi
export MIDICODER_LLM_HIGH_PROVIDER=anthropic
export MIDICODER_LLM_HIGH_API_KEY=$ANTHROPIC_KEY
midicoder init --non-interactive

# Run full pipeline
midicoder index
midicoder version create $CI_COMMIT_TAG
# Copy master-brief from repo
cp docs/requirements.md .midicoder/versions/$CI_COMMIT_TAG/master-brief.md
midicoder contract gen
midicoder ir build --skip-diagrams
midicoder code build
midicoder code gen
midicoder code apply --force  # Use with caution in CI
```

---

## Exit Codes

All commands return standard exit codes:

- **0**: Success
- **1**: General error (validation failed, missing files, etc.)
- **Non-zero**: Command-specific error

**Example usage in scripts:**

```bash
#!/bin/bash
set -e  # Exit on any error

midicoder contract gen || {
    echo "Contract generation failed"
    exit 1
}

midicoder ir build || {
    echo "IR build failed, check contracts"
    exit 1
}
```

---

## Common Workflows

### New Feature Development

```bash
# 1. Start fresh
midicoder version create feature-user-auth

# 2. Write requirements
vim .midicoder/versions/feature-user-auth/master-brief.md

# 3. Generate and apply
midicoder contract gen
midicoder ir build
midicoder code build
midicoder code gen
midicoder code apply --dry-run
midicoder code apply
```

### Refining Contracts

```bash
# 1. Check for issues
midicoder contract check

# 2. Create feedback
midicoder contract feedback

# 3. Add custom feedback
vim .midicoder/versions/<version>/contract-feedbacks.yml

# 4. Apply repairs
midicoder contract repair prepare
midicoder contract repair run

# 5. Regenerate downstream artifacts
midicoder ir build
midicoder code build
midicoder code gen
```

### Updating Existing Code

```bash
# 1. Reindex after manual changes
midicoder index reindex --path src/users/service.py

# 2. Regenerate patches with fresh context
midicoder code gen

# 3. Preview and apply
midicoder code apply --dry-run
midicoder code apply
```

---

## Debugging Commands

### View Run Logs

All commands create run directories with detailed logs:

```bash
# List recent runs
ls -lt .midicoder/runs/contract_gen/

# View summary
cat .midicoder/runs/contract_gen/<timestamp>/summary.json

# View LLM prompt (contract gen only)
cat .midicoder/runs/contract_gen/<timestamp>/pass_01_*.json/prompt.txt

# View LLM response
cat .midicoder/runs/contract_gen/<timestamp>/pass_01_*.json/response.txt
```

### Check State

```bash
# Global state
cat .midicoder/state.json

# Version state
cat .midicoder/versions/<version>/state.json

# Configuration
cat .midicoder/config.json
```

### Validate Artifacts

```bash
# Check contracts
midicoder contract check

# Validate config
midicoder config validate

# Validate feedback (before repair)
midicoder contract repair prepare
```

---

## Environment Variables

Midi Coder respects these environment variables:

### For Non-Interactive Init

- `MIDICODER_WORKING_DIR`: Working directory path
- `MIDICODER_STACK`: Comma-separated stack list
- `MIDICODER_LLM_HIGH_PROVIDER`: High-tier LLM provider
- `MIDICODER_LLM_CHEAP_PROVIDER`: Cheap-tier LLM provider
- `MIDICODER_LLM_HIGH_MODEL`, `MIDICODER_LLM_HIGH_URL`, `MIDICODER_LLM_HIGH_API_KEY`: For provider `openai_compatible` (high tier)
- `MIDICODER_LLM_CHEAP_MODEL`, `MIDICODER_LLM_CHEAP_URL`, `MIDICODER_LLM_CHEAP_API_KEY`: For provider `openai_compatible` (cheap tier)
- `MIDICODER_LLM_HIGH_ANTHROPIC_MODEL`, `MIDICODER_LLM_HIGH_ANTHROPIC_API_KEY`: For provider `anthropic` (high tier)
- `MIDICODER_LLM_CHEAP_ANTHROPIC_MODEL`, `MIDICODER_LLM_CHEAP_ANTHROPIC_API_KEY`: For provider `anthropic` (cheap tier)
- `MIDICODER_LLM_HIGH_OPENAI_MODEL`, `MIDICODER_LLM_HIGH_OPENAI_API_KEY`: For provider `openai` (high tier)
- `MIDICODER_LLM_CHEAP_OPENAI_MODEL`, `MIDICODER_LLM_CHEAP_OPENAI_API_KEY`: For provider `openai` (cheap tier)
- `MIDICODER_LLM_HIGH_BEDROCK_MODEL`, `MIDICODER_LLM_HIGH_AWS_REGION_NAME`, `MIDICODER_LLM_HIGH_AWS_ACCESS_KEY_ID`, `MIDICODER_LLM_HIGH_AWS_SECRET_ACCESS_KEY`: For provider `bedrock` (high tier)
- `MIDICODER_LLM_CHEAP_BEDROCK_MODEL`, `MIDICODER_LLM_CHEAP_AWS_REGION_NAME`, `MIDICODER_LLM_CHEAP_AWS_ACCESS_KEY_ID`, `MIDICODER_LLM_CHEAP_AWS_SECRET_ACCESS_KEY`: For provider `bedrock` (cheap tier)
- `MIDICODER_LLM_HIGH_AZURE_MODEL`, `MIDICODER_LLM_HIGH_AZURE_API_KEY`, `MIDICODER_LLM_HIGH_AZURE_OPENAI_ENDPOINT`, `MIDICODER_LLM_HIGH_AZURE_OPENAI_API_VERSION`, `MIDICODER_LLM_HIGH_AZURE_OPENAI_DEPLOYMENT`: For provider `azure` (high tier)
- `MIDICODER_LLM_CHEAP_AZURE_MODEL`, `MIDICODER_LLM_CHEAP_AZURE_API_KEY`, `MIDICODER_LLM_CHEAP_AZURE_OPENAI_ENDPOINT`, `MIDICODER_LLM_CHEAP_AZURE_OPENAI_API_VERSION`, `MIDICODER_LLM_CHEAP_AZURE_OPENAI_DEPLOYMENT`: For provider `azure` (cheap tier)
- `MIDICODER_LLM_HIGH_VERTEX_MODEL`, `MIDICODER_LLM_HIGH_VERTEX_API_KEY`, `MIDICODER_LLM_HIGH_VERTEX_PROJECT`, `MIDICODER_LLM_HIGH_VERTEX_LOCATION`: For provider `vertex_partner` (high tier)
- `MIDICODER_LLM_CHEAP_VERTEX_MODEL`, `MIDICODER_LLM_CHEAP_VERTEX_API_KEY`, `MIDICODER_LLM_CHEAP_VERTEX_PROJECT`, `MIDICODER_LLM_CHEAP_VERTEX_LOCATION`: For provider `vertex_partner` (cheap tier)

### For Runtime

- `MIDICODER_NON_INTERACTIVE`: Set to `true` to suppress prompts

**See:** [Non-Interactive Guide](non-interactive.md) for complete details.

---

## Getting Help

### In-CLI Help

```bash
# General help
midicoder --help

# Command-specific help
midicoder init --help
midicoder contract --help
midicoder code --help
```

### Configuration Keywords

```bash
# List all init configuration options
midicoder init --config-list
```

### Documentation

- [Pipeline Overview](pipeline.md): Deep dive into each step
- [Configuration](config.md): Config file structure and options
- [Non-Interactive Guide](non-interactive.md): Automation setup
- [Artifacts](artifacts.md): File structure and formats
- [Troubleshooting](troubleshooting.md): Common issues and solutions
- [FAQ](faq.md): Frequently asked questions

### Technical Specs

- `technic/DSL-schema.md`: DSL specification
- `technic/IR-compiler.md`: IR compilation details
- `technic/codegen.md`: Code generation strategy
- `technic/midicoder-algorithm.md`: Algorithm designs and roadmap

---

## Next Steps

- **First time?** Start with [Getting Started](getting-started.md)
- **Understanding the pipeline?** See [Pipeline Deep Dive](pipeline.md)
- **Setting up automation?** Check [Non-Interactive Guide](non-interactive.md)
- **Having issues?** Visit [Troubleshooting](troubleshooting.md)
