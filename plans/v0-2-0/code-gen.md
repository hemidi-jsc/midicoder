# Thiết kế command `midicoder code gen` - v0.2.0

## 1. Mục tiêu sản phẩm

`midicoder code gen` nhận:

- canonical FastAPI code từ `code build`
- project context graph từ `index`
- code thật trong workdir

và sinh ra **patch plan** để cập nhật workdir đích hoặc target stack đích.

Trong v0.2.0, command này **không còn là nơi “sáng tác business logic”**.

---

## 2. Product goals

1. Dùng canonical code làm nguồn sự thật cho implementation semantics.
2. Ưu tiên deterministic patch planning.
3. Chỉ dùng model như fallback adapter khi deterministic translator không đủ.
4. Tách rõ same-stack integration và cross-stack translation.

---

## 3. Non-goals

1. Không generate business intent mới.
2. Không tự bịa file targets ngoài ownership/context model.
3. Không áp patch vào workdir.

---

## 4. Input

1. plan index + plan files có `canonical_files[]`
2. context graph (`automatic_seams`, symbols, ownership, imports, profile, module graph)
3. current workdir snapshot
4. target stack config

---

## 5. Output

`.midicoder/versions/<version>/patches/` gồm:

- `index.json`
- `*.patch-plan.json`
- `patch-report.json`
- optional `runtime/` preview files

---

## 6. Chế độ hoạt động

### 6.1 Mode A - same-stack deterministic

Canonical FastAPI -> workdir FastAPI/Python

Đây là mode mặc định ưu tiên.

### 6.2 Mode B - cross-stack deterministic translator

Canonical FastAPI -> target stack có adapter deterministic

Ví dụ tương lai:

- NestJS
- Django
- Flask
- gRPC service skeleton

### 6.3 Mode C - fallback model adapter

Chỉ dùng khi:

- target stack chưa có deterministic adapter đầy đủ
- repo có integration pattern quá dị biệt
- deterministic planner confidence dưới threshold

---

## 7. Thuật toán cấp cao

### Phase 1 - Load plan and context

1. Load plan manifest.
2. Resolve execution order.
3. Load workdir symbol graph snapshot.
4. Load automatic seam map + ownership graph.

### Phase 2 - For each canonical file, resolve integration target

Từ `canonical_files[]`, xác định:

- target file thật trong workdir
- target symbol/anchor
- patch mode
- import strategy
- conflict policy

### Phase 3 - Deterministic patch synthesis

Nếu same-stack hoặc có adapter deterministic:

1. Parse canonical AST
2. Parse target AST/file text
3. Match symbol ownership
4. Generate primitive patch ops
   - create_file
   - replace_symbol
   - replace_region
   - insert_import
   - append_symbol
   - update_init_export

### Phase 4 - Optional model fallback

Chỉ nếu deterministic synthesis không khả thi.
Model được phép làm:

- structural adaptation
- repo-style alignment
- cross-stack translation

Model không được phép:

- đổi business semantics
- đổi IO contract
- bỏ policy/workflow checkpoints

### Phase 5 - Validation

1. patch plan schema validity
2. target path safety
3. import consistency
4. ownership safety
5. circular dependency check
6. contract-preservation check

### Phase 6 - Persist patch plans

Write patch-plan JSON + report.

---

## 8. Primitive patch op model mới

Patch plan v0.2.0 nên ưu tiên primitive ops thay vì generic `upsert_region` duy nhất.

### Ops đề xuất

- `create_file`
- `replace_file`
- `replace_symbol`
- `replace_region`
- `insert_before_anchor`
- `insert_after_anchor`
- `append_symbol`
- `insert_import`
- `delete_symbol`
- `update_exports`

Mỗi op cần có:

- target path
- selector / anchor
- ownership expectation
- before-hash optional
- content payload
- rollback safety

---

## 9. Vì sao `code gen` vẫn cần context graph + workdir code

Dù canonical code đã rõ, integration vào repo thật vẫn cần:

1. biết file nào là owned/shared/unsafe
2. biết module nào đang tồn tại
3. biết import graph hiện tại
4. biết entrypoint wiring thực tế
5. biết style/package layout của repo

Do đó `code gen` là **context-aware integration compiler**, không chỉ translator thuần túy.

---

## 10. Determinism strategy

### Mặc định

- deterministic path resolution
- deterministic patch op synthesis
- deterministic import ordering
- deterministic conflict diagnostics

### Khi nào được dùng model

Chỉ khi:

- adapter coverage thiếu
- conflict resolution ambiguity cao
- cross-stack mapping chưa codify đủ

và phải có feature flag explicit.

---

## 11. Failure modes

1. Không resolve được safe target file
2. Shared file không có safe anchor
3. Cross-stack adapter thiếu coverage
4. Patch plan làm đổi contract semantics
5. Ownership conflict

### Policy khi fail

- emit blocked patch report
- không fallback ngầm sang LLM
- yêu cầu index/build/adapter coverage tốt hơn

---

## 12. Test strategy

1. Same-stack deterministic generation tests
2. AST-based patch op tests
3. Ownership conflict tests
4. Cross-stack translation tests
5. Contract preservation tests

---

## 13. Open questions

1. Nên normalize canonical AST trước khi translate không?
2. Nên có IR-level adapter thay vì code-level adapter cho một số stack không?
3. Shared file patching có nên yêu cầu explicit allowlist?

