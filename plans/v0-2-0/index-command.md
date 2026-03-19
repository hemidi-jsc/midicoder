# Thiết kế command `midicoder index` - v0.2.0

## 1. Mục tiêu sản phẩm

`midicoder index` xây dựng **project context graph** cho workdir hiện tại. Trong v0.2.0, command này không còn được diễn giải bằng khái niệm `seams` và `virtual seams` ở cấp sản phẩm, mà bằng một artifact thống nhất:

- **automatic seam map**

Ngoài ra command còn phải sinh:

- symbol graph
- file graph
- import graph
- entrypoint map
- project profile
- ownership candidates
- code exemplars
- manifest phục vụ incremental reindex

---

## 2. Vì sao phải redesign command này

Kiến trúc hiện tại lấy:

- seam thật từ marker `midicoder:begin/end`
- virtual seam từ symbols/exemplars/entrypoints

Điều này đúng về mặt implementation nhưng sai ở product model vì end-user không hề tạo seam. Do đó v0.2.0 đổi mô hình mental sang automatic seam map duy nhất.

---

## 3. Product contract mới

### 3.1 Inputs

- workdir hiện tại
- .gitignore / ignore rules
- config stack hints
- previous context manifest (nếu reindex)
- optional changed paths

### 3.2 Outputs

Context folder chuẩn hóa:

- `manifest.json`
- `profile.json`
- `files.json` (mới)
- `symbols.json`
- `entrypoints.json`
- `automatic_seams.json` (mới, public artifact chính)
- `ownership.json` (mới)
- `imports.json` (mới)
- `exemplars.json`
- `service_graph.json` (mới)
- `module_graph.json` (mới)
- `index_report.json` (mới)

Legacy compatibility 1-2 version:

- `seams.json` -> generated alias from automatic seam map
- `virtual_seams.json` -> generated alias from automatic seam map

---

## 4. Automatic seam map là gì

Một automatic seam là một candidate insertion/update boundary gồm:

```json
{
  "file": "app/users/service.py",
  "kind": "service_slot",
  "symbol": "CreateUserService",
  "line_start": 40,
  "line_end": 96,
  "insertion_strategy": "replace_symbol",
  "ownership": "owned",
  "confidence": 0.93,
  "evidence": ["symbol_ast", "naming_convention", "import_graph"]
}
```

Nó có thể trỏ tới:

- whole file
- class
- function
- router block
- import block
- init file
- module append zone
- config section
- test file slot

---

## 5. Thuật toán tổng thể

### Phase 1 - Scan filesystem

1. Resolve working_dir.
2. Load ignore rules.
3. Scan files có index support.
4. Compute hashes.
5. Support full index và incremental index.

### Phase 2 - Build file and symbol graph

1. Parse AST / syntax trees theo language.
2. Extract symbols.
3. Extract imports.
4. Extract entrypoints.
5. Detect framework stack.

### Phase 3 - Build structural candidates

Tạo candidates từ:

- files
- classes
- functions
- routers/controllers
- services/repositories/models
- module init files
- bootstrap entrypoints

### Phase 4 - Ownership inference

Mỗi candidate được gán ownership:

- `owned_generated`
- `owned_user`
- `shared`
- `foreign`
- `unsafe`

Nguồn suy luận:

- existing Midicoder metadata
- import centrality
- naming conventions
- path roles
- prior apply manifests
- git blame/history (optional future)

### Phase 5 - Automatic seam synthesis

Unify tất cả signals thành automatic seam map.

### Phase 6 - Graph building

Sinh:

- module graph
- service graph
- entrypoint graph
- ownership graph

### Phase 7 - Persist artifacts

Write JSON artifacts + manifest.

---

## 6. Full index vs incremental reindex

### Full index

- scan toàn bộ workdir
- rebuild toàn bộ graphs
- baseline cho generation

### Incremental reindex

- nhận changed paths hoặc git delta
- chỉ parse phần thay đổi
- merge vào context hiện có
- nhưng output contract ở cấp sản phẩm vẫn là “đã chạy `midicoder index`”

### Chốt sản phẩm

Sau `code apply`, hệ thống phải trigger **`midicoder index`**. Nội bộ có thể tối ưu thành incremental, nhưng user-facing semantics vẫn là chạy lại index đầy đủ.

---

## 7. Dữ liệu cần cho downstream

### Cho `ir build`

- stack/profile summary

### Cho `code build`

- ownership candidates
- automatic seam map
- module/service graph
- symbol graph
- entrypoints

### Cho `code gen`

- target file confidence
- symbol insertion boundaries
- patch safety hints
- shared file warnings

### Cho `runtime fix`

- relevant file mapping
- import graph
- service ownership

---

## 8. Backward compatibility với seam cũ

### 8.1 Legacy marker support

Nếu file có `midicoder:begin/end`, parser vẫn ghi nhận chúng như strong evidence trong automatic seam map.

### 8.2 Artifact compatibility

Trong 1-2 version đầu:

- có thể vẫn emit `seams.json`
- có thể vẫn emit `virtual_seams.json`

Nhưng generator/planner mới sẽ đọc từ `automatic_seams.json` trước.

---

## 9. Failure modes

1. Repo quá lớn, parse chậm
2. AST parse lỗi
3. Stack detection mơ hồ
4. Ownership inference confidence thấp
5. Incremental state bị hỏng

### Policy khi fail

- degrade gracefully theo file-level candidate
- không fabricate ownership high-confidence khi không có bằng chứng
- emit warnings có cấu trúc

---

## 10. Test strategy

1. Full index determinism tests
2. Incremental reindex equivalence tests
3. Automatic seam synthesis tests
4. Ownership inference tests
5. Large repo performance tests
6. Legacy marker compatibility tests

---

## 11. Open questions

1. Có nên thêm `tests/` và `infra/` vào index model ngay ở v0.2.0 không?
2. Có nên parse Docker/K8s/Terraform để build topology graph không?
3. Ownership inference có cần git blame ở v0.2.x không?

