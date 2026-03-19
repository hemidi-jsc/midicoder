# Thiết kế command `midicoder code build` - v0.2.0

## 1. Mục tiêu sản phẩm

`midicoder code build` compile IR thành **canonical FastAPI executable code**. Đây là thay đổi trọng tâm nhất của v0.2.0.

Command này không còn sinh `pseudo_struct` như artifact trung gian chính. Thay vào đó, nó sinh ra:

- canonical Python/FastAPI code blocks hợp lệ
- ownership metadata
- insertion anchors
- contract refs
- file intent

`pseudo_struct` nếu còn tồn tại chỉ để backward compatibility trong giai đoạn chuyển tiếp.

---

## 2. Vai trò trong pipeline mới

`code build` là compiler backend deterministic từ IR sang canonical code.

### Input

- IR
- project context graph từ `index`

### Output

- canonical code plan theo file
- không đụng workdir
- không generate patch cho workdir thật

---

## 3. Vì sao phải đổi

Hiện trạng metadata-heavy code plan dẫn tới:

1. `code gen` phải tự suy luận quá nhiều.
2. Boundary build/gen không sạch.
3. Business logic dễ drift khi model viết code.
4. Không thể deterministic transform sang stack khác nếu intermediate quá abstract.

---

## 4. Product contract mới

### 4.1 Input artifacts

- `.midicoder/versions/<version>/irs/ir.json`
- `.midicoder/context/profile.json`
- `.midicoder/context/automatic_seams.json`
- `.midicoder/context/symbols.json`
- `.midicoder/context/entrypoints.json`
- `.midicoder/context/ownership.json`
- `.midicoder/context/module_graph.json`

### 4.2 Output artifacts

Thư mục `.midicoder/versions/<version>/plans/` gồm:

- `index.json`
- `entities/*.code-plan.json`
- `commands/*.code-plan.json`
- `queries/*.code-plan.json`
- `workflows/*.code-plan.json`
- `bootstrap/*.code-plan.json`
- `canonical-runtime/` (optional snapshot folder, mới)

---

## 5. Schema code plan mới

```json
{
  "schema_version": "0.2.0",
  "ir_ref": "Command.create_user",
  "stack": "fastapi",
  "intent": {...},
  "canonical_files": [
    {
      "runtime_path": "app/users/schema.py",
      "role": "schema",
      "language": "python",
      "framework": "fastapi",
      "anchors": {
        "region_start": "# region Command.create_user.schema",
        "region_end": "# endregion Command.create_user.schema"
      },
      "ownership": "owned_generated",
      "merge_mode": "replace_region",
      "code": "... python code ...",
      "contract_refs": {
        "io": [...],
        "policy": [...],
        "workflow": [...],
        "errors": [...]
      },
      "safety": {
        "can_create_file": true,
        "can_patch_shared_file": false
      }
    }
  ],
  "required_tests": [],
  "meta": {...}
}
```

---

## 6. Thuật toán cấp cao

### Phase 1 - Load and normalize inputs

1. Load IR.
2. Load context graph.
3. Resolve stack/profile.
4. Build canonical symbol and ownership indexes.

### Phase 2 - Expand IR items

Chuyển IR thành các build items:

- entities
- value objects
- commands
- queries
- workflows
- projections
- bootstrap/runtime infra

### Phase 3 - Resolve canonical runtime file set

Không resolve bằng `seam/virtual seam` branch logic nữa.
Thay vào đó dùng:

- automatic seam map
- ownership graph
- file conventions
- route/service/model role mapping

### Phase 4 - Deterministic emitters

Tách emitter theo role:

1. controller_fastapi
2. service_fastapi
3. schema_fastapi
4. model_fastapi
5. repository_fastapi
6. workflow_fastapi
7. bootstrap_fastapi
8. infra_fastapi
9. tests_fastapi (optional future)

### Phase 5 - Canonical code validation

1. parse AST
2. import validity (in canonical namespace)
3. route/io contract integrity
4. workflow semantics presence
5. policy/guard checkpoints presence
6. no TODO/placeholder

### Phase 6 - Ownership + patch safety hints

Mỗi canonical file phải gắn:

- ownership class
- merge mode suggestion
- safe patch strategies
- preferred insertion targets

### Phase 7 - Persist plans

Write per-item code-plan JSON + plan index.

---

## 7. Có phải “real code” không?

Có, theo nghĩa:

- code hợp lệ Python/FastAPI
- parse được AST
- có thể materialize và chạy lint/typecheck ở mức cơ bản

Không, theo nghĩa:

- chưa chắc đúng style repo đích
- chưa chắc tối ưu cho codebase hiện hữu
- chưa chắc là production-final implementation

Do đó khái niệm chính xác là:

- **canonical executable code**

---

## 8. Vì sao vẫn chọn canonical FastAPI làm intermediate

1. Python/FastAPI dễ canonical hóa.
2. Dễ encode workflows/API/service/model/repository.
3. Dễ parse AST và transform deterministic.
4. Dễ dịch sang stack khác hơn từ metadata trừu tượng.

---

## 9. Determinism

`code build` v0.2.0 phải:

- không gọi LLM
- cùng input -> cùng output byte-for-byte (trừ timestamp metadata nếu có)
- có snapshot hash tests

---

## 10. Failure modes

1. IR thiếu semantics tối thiểu
2. Context graph không đủ để map ownership/path
3. Emitter không sinh được code hợp lệ
4. Canonical code conflict trên same file/role

### Policy khi fail

- fail sớm
- emit diagnostics
- không fallback sang LLM

---

## 11. Migration strategy

### 11.1 Phase chuyển tiếp

Có thể giữ:

- `pseudo_struct`
- `integration_contract`

nhưng deprecated.

### 11.2 Phase ổn định

Downstream phải đọc `canonical_files` trước.

---

## 12. Test strategy

1. Determinism tests
2. AST parse tests
3. Route/policy/workflow integrity tests
4. Ownership mapping tests
5. Multi-module SaaS sample tests

---

## 13. Open questions

1. Có nên emit canonical unit tests ngay từ code build không?
2. Repository layer có nên luôn explicit hay infer theo persistence needs?
3. Có nên có canonical dependency injection spec riêng không?

