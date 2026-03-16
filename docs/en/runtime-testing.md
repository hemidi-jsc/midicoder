# Runtime Testing & Fixing

This document provides detailed documentation for Midi Coder CLI's runtime testing and fixing commands:

- `midicoder runtime test` - Test if the application starts up successfully
- `midicoder runtime fix` - Automatically fix runtime errors based on logs

## Overview

After applying patches with `midicoder code apply`, you need to verify that the code actually runs. The runtime testing pipeline helps you:

1. **Test**: Start the application and detect runtime errors
2. **Fix**: Analyze errors and automatically generate fix patches
3. **Apply**: Apply fix patches and test again

## Usage Flows

### Manual Flow (Step by Step)

```bash
# 1. Test the application
midicoder runtime test

# 2. If test fails, generate fix patches
midicoder runtime fix

# 3. Apply fix patches
midicoder code apply --patches-dir patches/runtime-fix/<timestamp>

# 4. Test again
midicoder runtime test
```

### Automated Flow (Auto-Fix Loop)

```bash
# Run automated loop: test → fix → apply → test
midicoder runtime fix --auto-fix-loop --test-timeout 30 --test-port 8000
```

The automated flow will:
- Run runtime test
- If failed, generate fix patches
- Automatically apply patches
- Test again
- Repeat until pass or reach loop limit (10 iterations)

---

## `midicoder runtime test`

Start the application to detect runtime errors.

### Usage

```bash
# Test with default configuration
midicoder runtime test

# Customize timeout and port
midicoder runtime test --timeout 60 --port 8000

# Verbose output
midicoder runtime test --verbose
```

### Options

- `--timeout <int>`: Maximum startup wait time (seconds). Default: `30`
- `--port <int>`: Port to start the application. Default: `8000`
- `--verbose`: Show detailed output

### How It Works

`runtime test` performs the following steps:

1. **Read Configuration**
   - Read `.midicoder/config.json` to get `working_dir`
   - Resolve `working_dir` to absolute path

2. **Find Python Executable**
   - Search for Python in priority order:
     - Windows: `{working_dir}/venv/Scripts/python.exe`
     - Linux/Mac: `{working_dir}/venv/bin/python`
     - Windows: `{working_dir}/.venv/Scripts/python.exe`
     - Linux/Mac: `{working_dir}/.venv/bin/python`
     - Fallback: `sys.executable`

3. **Start Application**
   - Spawn process: `python -m uvicorn app.main:app --host 0.0.0.0 --port <port> --log-level debug`
   - Monitor stdout within `timeout` period

4. **Detect Errors**
   - **Success**: If detect `"Uvicorn running on"` or `"Application startup complete"`
   - **Error**: Detect traceback, import errors, syntax errors, etc.
   - **Timeout**: Timeout reached without startup and no clear error

5. **Write Logs**
   - Create directory: `.midicoder/logs/{timestamp}/`
   - Write log files (see below)

6. **Cleanup**
   - Always terminate process in `finally` block

### Error Classification

The runner identifies the following error types:

| Error Type | Description | Example |
|------------|-------------|---------|
| `import_error` | Module import error | `ImportError: No module named 'xyz'` |
| `syntax_error` | Python syntax error | `SyntaxError: invalid syntax` |
| `attribute_error` | Attribute does not exist | `AttributeError: 'NoneType' has no attribute 'x'` |
| `type_error` | Data type error | `TypeError: unsupported operand type(s)` |
| `name_error` | Variable not defined | `NameError: name 'x' is not defined` |
| `value_error` | Invalid value | `ValueError: invalid literal` |
| `application_error` | Application-level error | Log contains `ERROR:` or `CRITICAL:` |
| `runtime_error` | Other runtime errors | Other runtime errors |
| `timeout` | Startup timeout | Did not startup within allowed time |
| `runner_error` | Internal runner error | Error in test runner |

### Output Artifacts

Each test run creates a logs directory:

```
.midicoder/logs/{timestamp}/
├── error.log           # Parsed errors (human-readable)
├── debug.log           # Full app stdout
├── summary.json        # Machine-readable summary
└── manifest.json       # Run log metadata
```

#### `summary.json`

```json
{
  "success": false,
  "timestamp": "20250316T123045Z",
  "errors": [
    {
      "type": "import_error",
      "message": "No module named 'fastapi_jwt'",
      "file": "app/auth/controller.py",
      "line": 5,
      "traceback": "..."
    }
  ],
  "total_errors": 1,
  "startup_time": null
}
```

#### `error.log`

Human-readable format for developers:

```
[IMPORT_ERROR] app/auth/controller.py:5
No module named 'fastapi_jwt'

Traceback:
  File "app/auth/controller.py", line 5, in <module>
    from fastapi_jwt import JWTBearer

---
```

#### `manifest.json`

```json
{
  "log_version": "1.0",
  "timestamp": "20250316T123045Z",
  "test_config": {
    "timeout": 30,
    "port": 8000,
    "working_dir": "/path/to/project"
  }
}
```

### Exit Codes

- **0**: Test successful (app startup)
- **1**: Test failed (errors or timeout)

### Examples

```bash
# Basic test
$ midicoder runtime test
[runtime test] Starting application...
[runtime test] FAILED - 2 error(s) detected
[runtime test] Logs: .midicoder/logs/20250316T123045Z/

# Test with longer timeout
$ midicoder runtime test --timeout 60
[runtime test] Starting application (timeout: 60s)...
[runtime test] SUCCESS - Application started
[runtime test] Logs: .midicoder/logs/20250316T123055Z/

# Verbose test
$ midicoder runtime test --verbose
[runtime test] Python: /path/to/venv/bin/python
[runtime test] Command: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
[runtime test] Stdout: INFO:     Started server process [12345]
[runtime test] Stdout: INFO:     Waiting for application startup.
...
```

### Troubleshooting

**Issue**: Test always times out

**Solution**:
- Increase `--timeout` (default 30s may not be enough for complex apps)
- Check `debug.log` to see if app prints anything
- Ensure app doesn't require interactive input

**Issue**: Cannot find Python executable

**Solution**:
- Create virtual environment: `python -m venv venv` or `python -m venv .venv`
- Activate and install dependencies: `pip install -r requirements.txt`

**Issue**: Test passes but app still has errors

**Solution**:
- Test only checks startup, not business logic
- Need separate integration tests for business logic

---

## `midicoder runtime fix`

Analyze runtime errors and generate fix patches automatically.

### Usage

```bash
# Fix based on latest log
midicoder runtime fix

# Fix based on specific log
midicoder runtime fix --log-timestamp 20250316T123045Z

# Dry-run (don't write patches)
midicoder runtime fix --dry-run

# Auto-apply patches after generation
midicoder runtime fix --auto-apply

# Auto-fix loop (test → fix → apply → test)
midicoder runtime fix --auto-fix-loop --test-timeout 30 --test-port 8000
```

### Options

- `--log-timestamp <str>`: Timestamp of log to fix (format: `YYYYMMDDTHHMMSSZ`)
- `--dry-run`: Run analysis and LLM but don't write patches
- `--auto-apply`: Automatically apply patches after successful generation
- `--auto-fix-loop`: Run automated loop (test → fix → apply)
- `--test-timeout <int>`: Timeout for runtime test (only with `--auto-fix-loop`)
- `--test-port <int>`: Port for runtime test (only with `--auto-fix-loop`)

### How It Works

`runtime fix` executes a complex 12-step pipeline:

#### 1. Select Log

- If `--log-timestamp` provided: Use that log
- Otherwise: Find latest failed log in `.midicoder/logs/*/summary.json` with `success=false`

#### 2. Analyze Errors

Read and analyze:
- `summary.json`: Classified errors
- `error.log`: Human-readable error details
- Enrich with `traceback_focus`: Files and line numbers from traceback
- Normalize paths to project-relative
- Extract `runtime_keywords`: Import names, function names, etc.

#### 3. Prevent Infinite Loops

- Hash main errors into signature
- Check `.midicoder/versions/{version}/patches/runtime-fix/.attempts.json`
- If same signature attempted >= 3 times: Stop and return error with manual review guidance

#### 4. Load Project Context

Read from `.midicoder/context/`:
- `symbols.json`: Classes, functions, methods
- `profile.json`: Stack detection, conventions
- `seams.json`: Integration boundaries
- `entrypoints.json`: Application entry points

#### 5. Load Business Context

Read from current version:
- **Contracts**: `.midicoder/versions/{version}/contracts/**/*.yml|yaml`
- **IR**: `.midicoder/versions/{version}/irs/ir.json` (fallback: `irs/ir.json`)

#### 6. Build Runtime Context

Aggregate context for LLM:
- Profile summary (stack, framework, conventions)
- Relevant files (ranked by error file + traceback + symbols)
- Symbols per file
- Entrypoints and seams filtered by keywords
- Contract and IR snippets focused on relevant domain

#### 7. Build Prompt

Create prompt with:
- Source code windows (with token limits)
- Stack adapter rules: `fastapi` | `nest` | `angular` | `generic`
- Business guard rules
- Strict output schema (JSON with operations)

#### 8. Call LLM

- Use high-tier model (from config)
- Model: Anthropic Claude or OpenAI GPT-4
- Tier: `high` (don't use cheap tier for fix)

#### 9. Parse Response

Validate JSON response:
- Only accept `operations` with `operation_type=upsert_region`
- Required fields: `ir_ref`, `region_start`, `region_end`, `file_path`
- `merge_mode` must be: `patch` | `create` | `append`
- `region_content` must not be empty

#### 10. Guardrails

Safety checks:

**Block dangerous paths:**
- `.midicoder/`
- `contracts/`
- `irs/`
- Absolute paths outside `working_dir`

**Block no-op patches:**
- `region_content` only contains `pass`
- `region_content` only contains `...`
- `region_content` is empty

#### 11. Canonicalize Operations

Normalize operations:
- Canonicalize `ir_ref` stable by `file_path + topic`
- Canonicalize region markers by canonical `ir_ref`
- Extract top-level imports from `region_content` to `imports[]`
- Merge operations with duplicate `ir_ref` on same file

#### 12. Write Output

If not `--dry-run`:

**Patch plans:**
```
.midicoder/versions/{version}/patches/runtime-fix/{timestamp}/
├── {file_path_as_dots}.patch-plan.json
├── {file_path_as_dots}.patch-plan.json
└── index.json
```

**Trace context:**
```
.midicoder/runs/runtime_fix/{timestamp}/
└── context_trace.json
```

**Attempt counter:**
```
.midicoder/versions/{version}/patches/runtime-fix/.attempts.json
```

### Output Format

#### Patch Plan

`app.auth.controller.patch-plan.json`:

```json
{
  "schema_version": "3.0.0",
  "file_path": "app/auth/controller.py",
  "operations": [
    {
      "operation_type": "upsert_region",
      "ir_ref": "app.auth.controller:jwt_setup",
      "region_start": "# region:app.auth.controller:jwt_setup",
      "region_end": "# endregion:app.auth.controller:jwt_setup",
      "region_content": "jwt_manager = JWTManager(secret_key=settings.JWT_SECRET)\napp.include_router(auth_router)",
      "merge_mode": "patch",
      "imports": [
        "from app.config import settings",
        "from fastapi_jwt_auth import JWTManager"
      ]
    }
  ]
}
```

#### Index

`index.json`:

```json
{
  "schema_version": "3.0.0",
  "generated_at": "2025-03-16T12:35:00Z",
  "runtime_enabled": false,
  "patch_plan_targets": [
    "app/auth/controller.py",
    "app/main.py"
  ],
  "generated_patch_plans": [
    "app.auth.controller.patch-plan.json",
    "app.main.patch-plan.json"
  ]
}
```

### Auto-Fix Loop

`--auto-fix-loop` automates the entire flow:

```bash
midicoder runtime fix --auto-fix-loop --test-timeout 30 --test-port 8000
```

**Flow:**

```
Iteration 1:
  1. runtime test (timeout: 30s, port: 8000)
  2. If failed: runtime fix (analyze + LLM + generate patches)
  3. code apply (auto-apply patches)
  4. If test passed: EXIT SUCCESS
  
Iteration 2:
  ... (repeat)

Iteration 10:
  ... (last iteration)
  If still failed: EXIT FAILURE with manual review guidance
```

**Limits:**
- Maximum 10 iterations (`AUTO_FIX_LOOP_MAX_ITERATIONS`)
- Early exit if test passes
- Early exit if detect signature loop (3 times)

### Stack Adapter

`runtime fix` has stack adapter rules for frameworks:

#### FastAPI

```
- Use dependency injection with Depends()
- Router pattern with APIRouter()
- Pydantic models for request/response
- async/await for I/O operations
```

#### NestJS

```
- Decorator-based (@Controller, @Injectable, @Module)
- Constructor injection
- TypeScript strict types
- RxJS for async operations
```

#### Angular

```
- Component-based with @Component
- Service with @Injectable
- RxJS Observables
- TypeScript strict mode
```

#### Generic

```
- Follow project conventions from profile.json
- Standard patterns for unrecognized stacks
```

### Prerequisites

Before running `runtime fix`:

1. **Valid version**
   - `.midicoder/state.json` with `current_version`
   - `.midicoder/versions/{version}/state.json`

2. **Error logs**
   - `.midicoder/logs/{timestamp}/summary.json` with `success=false`
   - Or provide correct `--log-timestamp`

3. **LLM config**
   - Valid high-tier LLM config in `.midicoder/config.json`
   - Valid API key in `.midicoder/secrets.json` or environment variable

### Exit Codes

- **0**: Fix successful (patches generated)
- **1**: Fix failed (see reasons below)

### When Command Fails

`runtime fix` returns `success=false` when:

❌ **No error logs**
```
No failed runtime logs found. Run 'midicoder runtime test' first.
```

❌ **Log timestamp not found**
```
Log timestamp '20250316T999999Z' not found.
```

❌ **Cannot parse actionable errors**
```
Could not extract actionable errors from log.
```

❌ **LLM config error**
```
High-tier LLM not configured. Run 'midicoder config set llm.high.model'.
```

❌ **LLM call error**
```
LLM API call failed: 401 Unauthorized
```

❌ **LLM returns invalid JSON**
```
LLM response is not valid JSON or missing 'operations' field.
```

❌ **All operations rejected**
```
All operations rejected by guardrails (unsafe paths or no-op patches).
```

❌ **Error signature repeated >= 3 times**
```
Same error signature attempted 3 times. Manual review required.
Check: .midicoder/versions/{version}/patches/runtime-fix/.attempts.json
```

### Examples

#### Example 1: Fix Latest Log

```bash
$ midicoder runtime fix
[runtime fix] Analyzing latest failed log: 20250316T123045Z
[runtime fix] Error type: import_error (No module named 'fastapi_jwt_auth')
[runtime fix] Building context...
[runtime fix] Calling LLM (high-tier)...
[runtime fix] Generated 2 operations
[runtime fix] Writing patches to: patches/runtime-fix/20250316T124000Z/
[runtime fix] SUCCESS

# Apply patches
$ midicoder code apply --patches-dir patches/runtime-fix/20250316T124000Z
```

#### Example 2: Dry-Run

```bash
$ midicoder runtime fix --dry-run
[runtime fix] Analyzing latest failed log: 20250316T123045Z
[runtime fix] Error type: import_error
[runtime fix] Building context...
[runtime fix] Calling LLM...
[runtime fix] Generated 2 operations (dry-run, not writing)
[runtime fix] 
Operations preview:
  - app/auth/controller.py: upsert_region (jwt_setup)
  - requirements.txt: upsert_region (fastapi_jwt_deps)
```

#### Example 3: Auto-Apply

```bash
$ midicoder runtime fix --auto-apply
[runtime fix] Analyzing latest failed log: 20250316T123045Z
[runtime fix] Generated 2 operations
[runtime fix] Writing patches...
[runtime fix] Auto-applying patches...
[code apply] Applying 2 patch plans...
[code apply] SUCCESS
[runtime fix] Patches applied to working directory
```

#### Example 4: Auto-Fix Loop

```bash
$ midicoder runtime fix --auto-fix-loop --test-timeout 30 --test-port 8000
[auto-fix] Iteration 1/10
[runtime test] Starting application...
[runtime test] FAILED - 1 error(s)
[runtime fix] Generating fix patches...
[runtime fix] SUCCESS - 2 operations
[code apply] Applying patches...
[code apply] SUCCESS

[auto-fix] Iteration 2/10
[runtime test] Starting application...
[runtime test] SUCCESS
[auto-fix] Application started successfully!
```

### Troubleshooting

**Issue**: Fix generates patches but still errors after apply

**Solution**:
- LLM may misunderstand context or errors
- Review patches in `patches/runtime-fix/{timestamp}/`
- Edit manually if needed
- Improve context by enhancing contracts/IR

**Issue**: Error signature repeated 3 times

**Solution**:
- Check `.attempts.json` to understand signature
- Manual review code to find root cause
- Fix manually and delete `.attempts.json` to reset counter

**Issue**: LLM timeout or rate limit

**Solution**:
- Wait and retry
- Use `--log-timestamp` to target specific log
- Don't use `--auto-fix-loop` when rate limited

**Issue**: Operations rejected by guardrails

**Solution**:
- Check output for rejection reason
- Usually LLM trying to write to `.midicoder/` or invalid path
- Retry or fix manually

---

## Real-World Workflows

### Workflow 1: After Code Apply

```bash
# 1. Apply patches from codegen
midicoder code apply

# 2. Test if it runs
midicoder runtime test

# 3. If failed, view logs
cat .midicoder/logs/$(ls -t .midicoder/logs | head -1)/error.log

# 4. Generate fix patches
midicoder runtime fix

# 5. Apply fix patches
midicoder code apply --patches-dir patches/runtime-fix/<timestamp>

# 6. Test again
midicoder runtime test
```

### Workflow 2: Auto-Fix Loop in CI/CD

```bash
#!/bin/bash
set -e

# Deploy pipeline
midicoder code apply

# Auto-fix loop with short timeout (CI environment)
midicoder runtime fix --auto-fix-loop --test-timeout 15 --test-port 8000

# If success, continue deploy
if [ $? -eq 0 ]; then
  echo "Runtime tests passed"
  docker build -t myapp:latest .
else
  echo "Runtime tests failed after auto-fix"
  exit 1
fi
```

### Workflow 3: Development Loop

```bash
# Quick iteration in development
while true; do
  clear
  echo "=== Testing application ==="
  midicoder runtime test --timeout 20
  
  if [ $? -eq 0 ]; then
    echo "✓ Tests passed!"
    break
  fi
  
  echo ""
  echo "=== Attempting auto-fix ==="
  midicoder runtime fix --auto-apply
  
  read -p "Review fixes and press Enter to test again..."
done
```

---

## Best Practices

### 1. Test Immediately After Apply

Always run `runtime test` right after `code apply` to catch errors early.

### 2. Review Fix Patches

Although `runtime fix` is intelligent, review patches before applying:

```bash
midicoder runtime fix --dry-run
# Review operations preview
midicoder runtime fix  # Generate patches
# Review patches in patches/runtime-fix/{timestamp}/
midicoder code apply --patches-dir patches/runtime-fix/{timestamp}
```

### 3. Limit Auto-Fix Loop

In production/CI:
- Use short timeout (15-30s)
- Don't let loop run too many iterations
- Monitor logs and attempts counter

### 4. Manual Review When Needed

If auto-fix loop fails after 3 times:
- May have complex root cause
- Review code manually
- Fix and commit manually
- Reset attempts counter

### 5. Maintain Clean Logs

Periodically cleanup old logs:

```bash
# Keep last 7 days of logs
find .midicoder/logs -type d -mtime +7 -exec rm -rf {} \;
```

---

## Pipeline Integration

### Full Pipeline

```bash
# 1. Setup
midicoder init
midicoder index
midicoder version create v0.1.0

# 2. Contract generation
vim .midicoder/versions/v0.1.0/master-brief.md
midicoder contract gen
midicoder ir build
midicoder code build
midicoder code gen

# 3. Apply and test
midicoder code apply
midicoder runtime test

# 4. Fix if needed
if [ $? -ne 0 ]; then
  midicoder runtime fix --auto-fix-loop
fi

# 5. Verify
midicoder runtime test
```

### CI/CD Integration

```yaml
# .github/workflows/midicoder.yml
name: Midicoder Pipeline

on: [push]

jobs:
  generate-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Midicoder
        run: pip install midicoder-cli
      
      - name: Initialize
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          midicoder init --non-interactive \
            --working-dir . \
            --stack fastapi \
            --llm-high-provider anthropic \
            --llm-high-model claude-sonnet-4-5 \
            --llm-high-key-env ANTHROPIC_API_KEY
      
      - name: Index project
        run: midicoder index
      
      - name: Generate code
        run: |
          midicoder version create ${{ github.sha }}
          cp docs/requirements.md .midicoder/versions/${{ github.sha }}/master-brief.md
          midicoder contract gen
          midicoder ir build --skip-diagrams
          midicoder code build
          midicoder code gen
      
      - name: Apply and test
        run: |
          midicoder code apply --force
          midicoder runtime fix --auto-fix-loop --test-timeout 30
      
      - name: Upload logs
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: runtime-logs
          path: .midicoder/logs/
```

---

## Current Limitations

### 1. Hard-coded Startup Target

`runtime test` currently hard-codes:
```python
python -m uvicorn app.main:app --host 0.0.0.0 --port {port}
```

**Workaround**: Ensure project has `app.main:app` or modify runner code.

### 2. Stack Adapter Quality

Stack adapter only provides guidelines, doesn't guarantee 100% correctness.

**Workaround**: Review patches manually, especially for NestJS/Angular.

### 3. Guardrails Don't Replace Code Review

Guardrails block dangerous paths and no-ops, but don't validate business logic.

**Workaround**: Always review patches before applying in production.

### 4. Auto-Fix Loop Limit

Maximum 10 iterations to avoid infinite loops.

**Workaround**: If fails after 10 iterations, manual review is necessary.

### 5. Context Window Limits

LLM has context window limits, may not be enough for large files.

**Workaround**: Refactor large files into smaller modules.

---

## Advanced Topics

### Custom Test Runners

Currently only supports Uvicorn/FastAPI. To support more runners:

1. Extend `FastAPIRunner` in `midicoder/runtime/test/runner.py`
2. Implement startup detection patterns
3. Register runner in config

### Custom Stack Adapters

To add new stack adapter:

1. Add rules in `midicoder/runtime/fix/prompt.py`
2. Update `get_stack_adapter_rules()`
3. Test with that stack project

### Extending Error Classification

To add error types:

1. Update patterns in `midicoder/runtime/test/runner.py`
2. Update classification logic
3. Update documentation

---

## Reference

### File Locations

```
.midicoder/
├── logs/                          # Runtime test logs
│   └── {timestamp}/
│       ├── error.log
│       ├── debug.log
│       ├── summary.json
│       └── manifest.json
│
├── versions/{version}/
│   └── patches/
│       └── runtime-fix/           # Runtime fix patches
│           ├── .attempts.json      # Loop counter
│           └── {timestamp}/
│               ├── index.json
│               └── *.patch-plan.json
│
└── runs/
    └── runtime_fix/{timestamp}/   # Fix run traces
        └── context_trace.json
```

### Command Matrix

| Command | Purpose | LLM | Writes Files | Auto-Apply |
|---------|---------|-----|--------------|------------|
| `runtime test` | Test app startup | No | Yes (logs) | N/A |
| `runtime fix` | Generate fix patches | Yes (high) | Yes (patches) | Optional |
| `runtime fix --dry-run` | Preview fixes | Yes | No | No |
| `runtime fix --auto-apply` | Generate + apply | Yes | Yes | Yes |
| `runtime fix --auto-fix-loop` | Full auto flow | Yes | Yes | Yes |

### Related Commands

- `midicoder code apply --patches-dir <dir>`: Apply fix patches
- `midicoder index reindex --path <paths>`: Reindex after manual fixes
- `midicoder config validate`: Validate LLM config

---

## Frequently Asked Questions

### Q: Does runtime test replace integration tests?

**A**: No. Runtime test only checks if the app **starts up**. You still need integration tests to verify business logic.

### Q: Can runtime fix fix all errors?

**A**: No. Runtime fix works well with:
- Import errors
- Simple syntax errors
- Clear type errors
- Configuration errors

Does not work well with:
- Complex business logic bugs
- Race conditions
- Performance issues
- Security vulnerabilities

### Q: Why does auto-fix loop stop after 3 times?

**A**: To avoid infinite loops with same error signature. After 3 times, it may be:
- LLM doesn't understand enough context
- Root cause is elsewhere
- Manual intervention needed

### Q: Can I use runtime fix for manual code?

**A**: Not recommended. Runtime fix is designed to fix code **generated by Midicoder**. With manual code:
- Context may not be sufficient
- Guardrails may be too strict
- Fix quality not guaranteed

### Q: Are logs gitignored?

**A**: Yes. `.midicoder/logs/` should be gitignored. Only commit patches if review needed.

---

## Next Steps

- **New to runtime testing?** Start with `midicoder runtime test` first
- **Want automation?** Try `--auto-fix-loop` in safe environment
- **Debugging issues?** See [Troubleshooting Guide](troubleshooting.md)
- **CI/CD setup?** See [Non-Interactive Guide](non-interactive.md)

---

## Changelog

### v1.0.0 (2025-03-16)
- ✨ Initial release of runtime testing commands
- ✨ Auto-fix loop with intelligent retry
- ✨ Stack adapters for FastAPI/NestJS/Angular
- ✨ Guardrails for safe code generation
- ✨ Detailed logging and tracing
