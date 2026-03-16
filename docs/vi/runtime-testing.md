# Runtime Testing & Fixing

Tài liệu này mô tả chi tiết về 2 lệnh runtime testing và fixing của Midi Coder CLI:

- `midicoder runtime test` - Kiểm tra ứng dụng có khởi động được không
- `midicoder runtime fix` - Tự động sửa các lỗi runtime dựa trên logs

## Tổng Quan

Sau khi áp dụng patches với `midicoder code apply`, bạn cần kiểm tra xem code có chạy được không. Runtime testing pipeline giúp bạn:

1. **Test**: Khởi động ứng dụng và phát hiện lỗi runtime
2. **Fix**: Phân tích lỗi và sinh patches sửa lỗi tự động
3. **Apply**: Áp dụng fix patches và test lại

## Flow Sử Dụng

### Flow Thủ Công (Từng Bước)

```bash
# 1. Test ứng dụng
midicoder runtime test

# 2. Nếu test thất bại, sinh fix patches
midicoder runtime fix

# 3. Áp dụng fix patches
midicoder code apply --patches-dir patches/runtime-fix/<timestamp>

# 4. Test lại
midicoder runtime test
```

### Flow Tự Động (Auto-Fix Loop)

```bash
# Chạy vòng lặp tự động: test → fix → apply → test
midicoder runtime fix --auto-fix-loop --test-timeout 30 --test-port 8000
```

Flow tự động sẽ:
- Chạy runtime test
- Nếu thất bại, sinh fix patches
- Tự động apply patches
- Test lại
- Lặp lại cho đến khi pass hoặc đạt giới hạn vòng lặp (10 lần)

---

## `midicoder runtime test`

Khởi động ứng dụng để kiểm tra lỗi runtime.

### Cách Dùng

```bash
# Test với cấu hình mặc định
midicoder runtime test

# Tùy chỉnh timeout và port
midicoder runtime test --timeout 60 --port 8000

# Verbose output
midicoder runtime test --verbose
```

### Options

- `--timeout <int>`: Thời gian chờ startup tối đa (giây). Mặc định: `30`
- `--port <int>`: Port để khởi động ứng dụng. Mặc định: `8000`
- `--verbose`: Hiển thị output chi tiết

### Cách Hoạt Động

`runtime test` thực hiện các bước sau:

1. **Đọc Configuration**
   - Đọc `.midicoder/config.json` để lấy `working_dir`
   - Resolve `working_dir` thành absolute path

2. **Tìm Python Executable**
   - Tìm Python theo thứ tự ưu tiên:
     - Windows: `{working_dir}/venv/Scripts/python.exe`
     - Linux/Mac: `{working_dir}/venv/bin/python`
     - Windows: `{working_dir}/.venv/Scripts/python.exe`
     - Linux/Mac: `{working_dir}/.venv/bin/python`
     - Fallback: `sys.executable`

3. **Khởi Động Application**
   - Spawn process: `python -m uvicorn app.main:app --host 0.0.0.0 --port <port> --log-level debug`
   - Theo dõi stdout trong khoảng thời gian `timeout`

4. **Phát Hiện Lỗi**
   - **Success**: Nếu phát hiện `"Uvicorn running on"` hoặc `"Application startup complete"`
   - **Error**: Phát hiện traceback, import errors, syntax errors, etc.
   - **Timeout**: Hết timeout mà chưa startup và chưa có lỗi rõ ràng

5. **Ghi Logs**
   - Tạo thư mục: `.midicoder/logs/{timestamp}/`
   - Ghi các file logs (xem bên dưới)

6. **Cleanup**
   - Luôn terminate process trong `finally` block

### Phân Loại Lỗi

Runner nhận diện các loại lỗi sau:

| Error Type | Mô Tả | Ví Dụ |
|------------|-------|-------|
| `import_error` | Lỗi import module | `ImportError: No module named 'xyz'` |
| `syntax_error` | Lỗi cú pháp Python | `SyntaxError: invalid syntax` |
| `attribute_error` | Thuộc tính không tồn tại | `AttributeError: 'NoneType' has no attribute 'x'` |
| `type_error` | Lỗi kiểu dữ liệu | `TypeError: unsupported operand type(s)` |
| `name_error` | Biến không được định nghĩa | `NameError: name 'x' is not defined` |
| `value_error` | Giá trị không hợp lệ | `ValueError: invalid literal` |
| `application_error` | Lỗi application-level | Log có `ERROR:` hoặc `CRITICAL:` |
| `runtime_error` | Lỗi runtime khác | Các lỗi runtime khác |
| `timeout` | Timeout startup | Không startup trong thời gian cho phép |
| `runner_error` | Lỗi runner nội bộ | Lỗi trong test runner |

### Output Artifacts

Mỗi lần test tạo thư mục logs:

```
.midicoder/logs/{timestamp}/
├── error.log           # Lỗi đã parse (human-readable)
├── debug.log           # Toàn bộ stdout của app
├── summary.json        # Summary machine-readable
└── manifest.json       # Metadata của run log
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

Format dễ đọc cho developers:

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

- **0**: Test thành công (app startup)
- **1**: Test thất bại (có lỗi hoặc timeout)

### Ví Dụ

```bash
# Test cơ bản
$ midicoder runtime test
[runtime test] Starting application...
[runtime test] FAILED - 2 error(s) detected
[runtime test] Logs: .midicoder/logs/20250316T123045Z/

# Test với timeout dài hơn
$ midicoder runtime test --timeout 60
[runtime test] Starting application (timeout: 60s)...
[runtime test] SUCCESS - Application started
[runtime test] Logs: .midicoder/logs/20250316T123055Z/

# Test verbose
$ midicoder runtime test --verbose
[runtime test] Python: /path/to/venv/bin/python
[runtime test] Command: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
[runtime test] Stdout: INFO:     Started server process [12345]
[runtime test] Stdout: INFO:     Waiting for application startup.
...
```

### Troubleshooting

**Vấn đề**: Test luôn timeout

**Giải pháp**:
- Tăng `--timeout` (mặc định 30s có thể không đủ cho app phức tạp)
- Kiểm tra `debug.log` để xem app có in gì không
- Đảm bảo app không yêu cầu input interactive

**Vấn đề**: Không tìm thấy Python executable

**Giải pháp**:
- Tạo virtual environment: `python -m venv venv` hoặc `python -m venv .venv`
- Activate và cài dependencies: `pip install -r requirements.txt`

**Vấn đề**: Test pass nhưng app vẫn có lỗi

**Giải pháp**:
- Test chỉ kiểm tra startup, không kiểm tra business logic
- Cần thêm integration tests riêng cho business logic

---

## `midicoder runtime fix`

Phân tích runtime errors và sinh fix patches tự động.

### Cách Dùng

```bash
# Fix dựa trên log gần nhất
midicoder runtime fix

# Fix dựa trên log cụ thể
midicoder runtime fix --log-timestamp 20250316T123045Z

# Dry-run (không ghi patches)
midicoder runtime fix --dry-run

# Auto-apply patches sau khi generate
midicoder runtime fix --auto-apply

# Auto-fix loop (test → fix → apply → test)
midicoder runtime fix --auto-fix-loop --test-timeout 30 --test-port 8000
```

### Options

- `--log-timestamp <str>`: Timestamp của log cần fix (format: `YYYYMMDDTHHMMSSZ`)
- `--dry-run`: Chạy analysis và LLM nhưng không ghi patches
- `--auto-apply`: Tự động apply patches sau khi generate thành công
- `--auto-fix-loop`: Chạy vòng lặp tự động (test → fix → apply)
- `--test-timeout <int>`: Timeout cho runtime test (chỉ với `--auto-fix-loop`)
- `--test-port <int>`: Port cho runtime test (chỉ với `--auto-fix-loop`)

### Cách Hoạt Động

`runtime fix` thực hiện pipeline phức tạp gồm 12 bước:

#### 1. Chọn Log

- Nếu có `--log-timestamp`: Dùng log đó
- Nếu không: Tìm log failed gần nhất trong `.midicoder/logs/*/summary.json` với `success=false`

#### 2. Phân Tích Lỗi

Đọc và phân tích:
- `summary.json`: Lỗi đã được phân loại
- `error.log`: Chi tiết lỗi human-readable
- Enrich với `traceback_focus`: File và line numbers từ traceback
- Normalize paths về project-relative
- Trích xuất `runtime_keywords`: Import names, function names, etc.

#### 3. Chặn Lặp Vô Hạn

- Hash các lỗi chính thành signature
- Kiểm tra `.midicoder/versions/{version}/patches/runtime-fix/.attempts.json`
- Nếu cùng signature đã thử >= 3 lần: Stop và trả error hướng dẫn manual review

#### 4. Nạp Project Context

Đọc từ `.midicoder/context/`:
- `symbols.json`: Classes, functions, methods
- `profile.json`: Stack detection, conventions
- `seams.json`: Integration boundaries
- `entrypoints.json`: Application entry points

#### 5. Nạp Business Context

Đọc từ version hiện tại:
- **Contracts**: `.midicoder/versions/{version}/contracts/**/*.yml|yaml`
- **IR**: `.midicoder/versions/{version}/irs/ir.json` (fallback: `irs/ir.json`)

#### 6. Build Runtime Context

Tổng hợp context cho LLM:
- Profile summary (stack, framework, conventions)
- Relevant files (rank theo error file + traceback + symbols)
- Symbols theo từng file
- Entrypoints và seams filter theo keywords
- Contract và IR snippets focus vào domain liên quan

#### 7. Build Prompt

Tạo prompt với:
- Source code windows (có giới hạn token)
- Stack adapter rules: `fastapi` | `nest` | `angular` | `generic`
- Business guard rules
- Output schema strict (JSON với operations)

#### 8. Gọi LLM

- Sử dụng high-tier model (từ config)
- Model: Anthropic Claude hoặc OpenAI GPT-4
- Tier: `high` (không dùng cheap tier cho fix)

#### 9. Parse Response

Validate JSON response:
- Chỉ nhận `operations` với `operation_type=upsert_region`
- Bắt buộc có: `ir_ref`, `region_start`, `region_end`, `file_path`
- `merge_mode` phải thuộc: `patch` | `create` | `append`
- `region_content` phải không rỗng

#### 10. Guardrails

Kiểm tra an toàn:

**Chặn paths nguy hiểm:**
- `.midicoder/`
- `contracts/`
- `irs/`
- Absolute paths ngoài `working_dir`

**Chặn no-op patches:**
- `region_content` chỉ chứa `pass`
- `region_content` chỉ chứa `...`
- `region_content` rỗng

#### 11. Canonicalize Operations

Chuẩn hóa operations:
- Chuẩn hóa `ir_ref` ổn định theo `file_path + topic`
- Chuẩn hóa region markers theo `ir_ref` canonical
- Bóc imports top-level khỏi `region_content` sang `imports[]`
- Merge operations trùng `ir_ref` trên cùng file

#### 12. Ghi Output

Nếu không `--dry-run`:

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

### Định Dạng Output

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

`--auto-fix-loop` tự động hóa toàn bộ flow:

```bash
midicoder runtime fix --auto-fix-loop --test-timeout 30 --test-port 8000
```

**Flow:**

```
Vòng 1:
  1. runtime test (timeout: 30s, port: 8000)
  2. Nếu failed: runtime fix (analyze + LLM + generate patches)
  3. code apply (auto-apply patches)
  4. Nếu test passed: EXIT SUCCESS
  
Vòng 2:
  ... (lặp lại)

Vòng 10:
  ... (vòng cuối)
  Nếu vẫn failed: EXIT FAILURE với hướng dẫn manual review
```

**Giới hạn:**
- Tối đa 10 vòng (`AUTO_FIX_LOOP_MAX_ITERATIONS`)
- Dừng sớm nếu test pass
- Dừng sớm nếu phát hiện lặp signature (3 lần)

### Stack Adapter

`runtime fix` có stack adapter rules cho các framework:

#### FastAPI

```
- Sử dụng dependency injection với Depends()
- Router pattern với APIRouter()
- Pydantic models cho request/response
- async/await cho I/O operations
```

#### NestJS

```
- Decorator-based (@Controller, @Injectable, @Module)
- Constructor injection
- TypeScript strict types
- RxJS cho async operations
```

#### Angular

```
- Component-based với @Component
- Service với @Injectable
- RxJS Observables
- TypeScript strict mode
```

#### Generic

```
- Follow project conventions từ profile.json
- Standard patterns cho stack không nhận diện được
```

### Điều Kiện Tiên Quyết

Trước khi chạy `runtime fix`:

1. **Có version hợp lệ**
   - `.midicoder/state.json` với `current_version`
   - `.midicoder/versions/{version}/state.json`

2. **Có error logs**
   - `.midicoder/logs/{timestamp}/summary.json` với `success=false`
   - Hoặc truyền `--log-timestamp` đúng

3. **Có LLM config**
   - High-tier LLM config hợp lệ trong `.midicoder/config.json`
   - API key hợp lệ trong `.midicoder/secrets.json` hoặc environment variable

### Exit Codes

- **0**: Fix thành công (patches generated)
- **1**: Fix thất bại (xem reasons bên dưới)

### Khi Nào Command Thất Bại

`runtime fix` trả `success=false` khi:

❌ **Không có error logs**
```
No failed runtime logs found. Run 'midicoder runtime test' first.
```

❌ **Log timestamp không tồn tại**
```
Log timestamp '20250316T999999Z' not found.
```

❌ **Không parse được lỗi actionable**
```
Could not extract actionable errors from log.
```

❌ **LLM config lỗi**
```
High-tier LLM not configured. Run 'midicoder config set llm.high.model'.
```

❌ **LLM call lỗi**
```
LLM API call failed: 401 Unauthorized
```

❌ **LLM trả JSON sai format**
```
LLM response is not valid JSON or missing 'operations' field.
```

❌ **Tất cả operations bị reject**
```
All operations rejected by guardrails (unsafe paths or no-op patches).
```

❌ **Signature lỗi lặp lại >= 3 lần**
```
Same error signature attempted 3 times. Manual review required.
Check: .midicoder/versions/{version}/patches/runtime-fix/.attempts.json
```

### Ví Dụ

#### Ví Dụ 1: Fix Log Gần Nhất

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

#### Ví Dụ 2: Dry-Run

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

#### Ví Dụ 3: Auto-Apply

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

#### Ví Dụ 4: Auto-Fix Loop

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

**Vấn đề**: Fix generate patches nhưng vẫn lỗi sau apply

**Giải pháp**:
- LLM có thể hiểu sai context hoặc lỗi
- Review patches trong `patches/runtime-fix/{timestamp}/`
- Chỉnh sửa manual nếu cần
- Tăng context bằng cách improve contracts/IR

**Vấn đề**: Signature lỗi lặp lại 3 lần

**Giải pháp**:
- Xem `.attempts.json` để hiểu signature
- Manual review code để tìm root cause
- Fix manual và xóa `.attempts.json` để reset counter

**Vấn đề**: LLM timeout hoặc rate limit

**Giải pháp**:
- Đợi và retry
- Sử dụng `--log-timestamp` để target log cụ thể
- Không dùng `--auto-fix-loop` khi bị rate limit

**Vấn đề**: Operations bị reject bởi guardrails

**Giải pháp**:
- Xem output để biết lý do reject
- Thường do LLM cố ghi vào `.midicoder/` hoặc path không hợp lệ
- Retry hoặc fix manual

---

## Workflows Thực Tế

### Workflow 1: Sau Code Apply

```bash
# 1. Apply patches từ codegen
midicoder code apply

# 2. Test xem có chạy không
midicoder runtime test

# 3. Nếu failed, xem logs
cat .midicoder/logs/$(ls -t .midicoder/logs | head -1)/error.log

# 4. Sinh fix patches
midicoder runtime fix

# 5. Apply fix patches
midicoder code apply --patches-dir patches/runtime-fix/<timestamp>

# 6. Test lại
midicoder runtime test
```

### Workflow 2: Auto-Fix Loop Trong CI/CD

```bash
#!/bin/bash
set -e

# Deploy pipeline
midicoder code apply

# Auto-fix loop với timeout ngắn (CI environment)
midicoder runtime fix --auto-fix-loop --test-timeout 15 --test-port 8000

# Nếu success, continue deploy
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
# Quick iteration trong development
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

### 1. Test Ngay Sau Apply

Luôn chạy `runtime test` ngay sau `code apply` để phát hiện lỗi sớm.

### 2. Review Fix Patches

Dù `runtime fix` thông minh, nên review patches trước khi apply:

```bash
midicoder runtime fix --dry-run
# Review operations preview
midicoder runtime fix  # Generate patches
# Review patches trong patches/runtime-fix/{timestamp}/
midicoder code apply --patches-dir patches/runtime-fix/{timestamp}
```

### 3. Giới Hạn Auto-Fix Loop

Trong production/CI:
- Sử dụng timeout ngắn (15-30s)
- Không để loop quá nhiều vòng
- Monitor logs và attempts counter

### 4. Manual Review Khi Cần

Nếu auto-fix loop fail sau 3 lần:
- Có thể có root cause phức tạp
- Review code manual
- Fix và commit manual
- Reset attempts counter

### 5. Maintain Clean Logs

Định kỳ cleanup old logs:

```bash
# Giữ logs 7 ngày gần nhất
find .midicoder/logs -type d -mtime +7 -exec rm -rf {} \;
```

---

## Tích Hợp Với Pipeline

### Pipeline Đầy Đủ

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

# 3. Apply và test
midicoder code apply
midicoder runtime test

# 4. Fix nếu cần
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

## Giới Hạn Hiện Tại

### 1. Hard-coded Startup Target

`runtime test` hiện tại hard-code:
```python
python -m uvicorn app.main:app --host 0.0.0.0 --port {port}
```

**Workaround**: Đảm bảo project có `app.main:app` hoặc chỉnh sửa runner code.

### 2. Stack Adapter Chất Lượng

Stack adapter chỉ cung cấp guidelines, không guarantee đúng 100%.

**Workaround**: Review patches manual, đặc biệt cho NestJS/Angular.

### 3. Guardrails Không Thay Thế Code Review

Guardrails chặn paths nguy hiểm và no-op, nhưng không validate business logic.

**Workaround**: Luôn review patches trước khi apply trong production.

### 4. Giới Hạn Auto-Fix Loop

Tối đa 10 vòng để tránh loop vô hạn.

**Workaround**: Nếu fail sau 10 vòng, manual review là cần thiết.

### 5. Context Window Limits

LLM có giới hạn context window, có thể không đủ cho files lớn.

**Workaround**: Refactor files lớn thành modules nhỏ hơn.

---

## Advanced Topics

### Custom Test Runners

Hiện tại chỉ hỗ trợ Uvicorn/FastAPI. Để support thêm runners:

1. Extend `FastAPIRunner` trong `midicoder/runtime/test/runner.py`
2. Implement startup detection patterns
3. Register runner trong config

### Custom Stack Adapters

Để thêm stack adapter mới:

1. Thêm rules trong `midicoder/runtime/fix/prompt.py`
2. Update `get_stack_adapter_rules()`
3. Test với project stack đó

### Extending Error Classification

Để thêm error types:

1. Update patterns trong `midicoder/runtime/test/runner.py`
2. Update classification logic
3. Update documentation

---

## Tham Khảo

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
- `midicoder index reindex --path <paths>`: Reindex sau manual fixes
- `midicoder config validate`: Validate LLM config

---

## Câu Hỏi Thường Gặp

### Q: Runtime test có thay thế integration tests không?

**A**: Không. Runtime test chỉ kiểm tra app có **khởi động** được không. Bạn vẫn cần integration tests để kiểm tra business logic.

### Q: Runtime fix có thể sửa được mọi lỗi không?

**A**: Không. Runtime fix hoạt động tốt với:
- Import errors
- Syntax errors đơn giản
- Type errors rõ ràng
- Configuration errors

Không hoạt động tốt với:
- Business logic bugs phức tạp
- Race conditions
- Performance issues
- Security vulnerabilities

### Q: Tại sao auto-fix loop dừng sau 3 lần?

**A**: Để tránh lặp vô hạn với same error signature. Sau 3 lần, có thể là:
- LLM không hiểu đủ context
- Root cause nằm ở nơi khác
- Cần manual intervention

### Q: Có thể dùng runtime fix cho manual code không?

**A**: Không khuyến nghị. Runtime fix được thiết kế để fix code **generated bởi Midicoder**. Với manual code:
- Context có thể không đầy đủ
- Guardrails có thể quá strict
- Fix quality không đảm bảo

### Q: Logs có được gitignore không?

**A**: Có. `.midicoder/logs/` nên được gitignore. Chỉ commit patches nếu cần review.

---

## Bước Tiếp Theo

- **New to runtime testing?** Bắt đầu với `midicoder runtime test` trước
- **Want automation?** Thử `--auto-fix-loop` trong safe environment
- **Debugging issues?** Xem [Troubleshooting Guide](troubleshooting.md)
- **CI/CD setup?** Xem [Non-Interactive Guide](non-interactive.md)

---

## Changelog

### v1.0.0 (2025-03-16)
- ✨ Initial release của runtime testing commands
- ✨ Auto-fix loop với intelligent retry
- ✨ Stack adapters cho FastAPI/NestJS/Angular
- ✨ Guardrails cho safe code generation
- ✨ Detailed logging và tracing
