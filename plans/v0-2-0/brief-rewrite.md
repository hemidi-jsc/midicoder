# Thiết kế command `midicoder brief rewrite` - v0.2.0

## 1. Mục tiêu sản phẩm

`midicoder brief rewrite` chịu trách nhiệm biến input của người dùng (brief tự do, backlog, ticket dump, notes, remediation brief) thành một **product brief chuẩn hóa**, nhất quán, ít mơ hồ và đủ giàu thông tin để `contract gen` hoạt động ổn định.

Mục tiêu của command này không phải là sinh DSL hay code, mà là tạo ra một **canonical problem statement**.

---

## 2. Vai trò trong pipeline mới

### 2.1 Vị trí

`brief rewrite` là pha đầu của toàn bộ pipeline.

### 2.2 Tác động tới các pha sau

Output của `brief rewrite` là đầu vào ưu tiên cho:

- `contract gen`
- `runtime fix` khi cần tạo remediation brief mới
- các cycle re-plan sau verification failures

### 2.3 Tư tưởng thiết kế

- LLM được phép dùng ở đây.
- Nhưng command phải constrained mạnh để tránh sáng tác quá mức.
- Command phải giữ trace giữa brief gốc và brief chuẩn hóa.

---

## 3. Product goals chi tiết

1. Làm rõ mục tiêu nghiệp vụ.
2. Tách functional requirement và non-functional requirement.
3. Chuẩn hóa thuật ngữ domain.
4. Xác định actors, entities, workflows, integrations, policies, constraints.
5. Chỉ ra các khoảng trống cần hỏi thêm.
6. Sinh remediation brief từ lỗi verification/runtime mà không làm mất brief gốc.

---

## 4. Non-goals

1. Không sinh contract DSL.
2. Không quyết định cấu trúc file/code.
3. Không suy diễn công nghệ mục tiêu quá sớm ngoài các ràng buộc người dùng nêu rõ.
4. Không tự thay đổi business intent cốt lõi của brief gốc.

---

## 5. Inputs

Command nhận một hoặc nhiều nguồn:

1. `brief.md` hoặc raw user input
2. optional context:
   - existing product brief
   - remediation brief cũ
   - project profile/index summary
   - verification failure summary
3. optional policy:
   - stack hints
   - domain glossary
   - architecture constraints

---

## 6. Outputs

### 6.1 Primary artifact

`briefs/rewritten/<timestamp>.md`

### 6.2 Companion artifacts

- `briefs/rewritten/<timestamp>.json`
- `briefs/rewritten/<timestamp>.trace.json`
- `briefs/rewritten/<timestamp>.diff.md`
- `briefs/rewritten/latest.md` (symlink/copy logical alias)

### 6.3 JSON structure đề xuất

```json
{
  "brief_version": "0.2.0",
  "source_briefs": ["brief.md"],
  "mode": "initial|remediation|merge",
  "domain_glossary": [],
  "functional_requirements": [],
  "non_functional_requirements": [],
  "actors": [],
  "entities": [],
  "workflows": [],
  "integrations": [],
  "constraints": [],
  "risks": [],
  "open_questions": []
}
```

---

## 7. Thuật toán cấp cao

### Phase 1 - Load source brief set

1. Resolve input brief files.
2. Nếu là remediation mode, load thêm verification summary và previous version artifacts.
3. Normalize encoding, whitespace, frontmatter.

### Phase 2 - Extract factual signals

1. Entity candidates
2. Actor candidates
3. Feature/module candidates
4. Business rules candidates
5. NFR candidates
6. Stack/environment constraints

### Phase 3 - LLM rewrite under schema contract

LLM được phép dùng nhưng prompt phải ép output vào schema chuẩn hóa:

- không được tự thêm feature nếu không có bằng chứng
- phải gắn confidence hoặc evidence cho các suy luận mềm
- phải liệt kê open questions rõ ràng

### Phase 4 - Deterministic post-processing

1. Deduplicate glossary terms
2. Canonicalize headings
3. Sort requirements theo nhóm
4. Validate presence của mục bắt buộc
5. Tạo diff với brief gốc

### Phase 5 - Persist artifacts

Ghi markdown + JSON + trace.

---

## 8. Remediation brief mode

### 8.1 Mục tiêu

Khi verification hoặc runtime fix phát hiện lỗi, hệ thống **không rewrite đè brief gốc**.

### 8.2 Cách làm

Tạo một brief mới loại `remediation` gồm:

- failures observed
- impacted modules/contracts
- invariants phải giữ nguyên
- corrective goals

### 8.3 Ví dụ loại lỗi

1. Implementation defect
2. Contract mismatch
3. Missing infrastructure wiring
4. Broken test assumptions

---

## 9. Determinism / model usage

- Cho phép LLM: **có**
- Deterministic hậu xử lý: **bắt buộc**
- Không có chế độ chạy hoàn toàn offline ở v0.2.0 cho command này, trừ khi user cung cấp structured brief JSON hợp lệ.

---

## 10. Failure modes

1. Brief quá mơ hồ
2. Brief mâu thuẫn nội bộ
3. LLM output thiếu section bắt buộc
4. Domain glossary bất nhất
5. Remediation brief làm thay đổi intent gốc

### Cách xử lý

- Fail với diagnostics có cấu trúc
- Không tạo artifact “success” giả
- Vẫn lưu trace để review

---

## 11. Observability

Run artifacts phải có:

- prompt
- normalized input bundle
- raw response
- processed response
- validation issues
- diff summary

---

## 12. Backward compatibility

Nếu repo cũ chỉ có `brief.md`, command vẫn dùng được.

Nếu đã có `briefs/rewritten/latest.md`, command có thể chạy incremental merge hoặc remediation mode.

---

## 13. Test strategy

1. Snapshot tests cho rewrite output shape
2. Contradiction detection tests
3. Remediation brief generation tests
4. Non-regression tests cho glossary canonicalization

---

## 14. Open questions

1. Có nên hỗ trợ interactive clarification loop trước khi rewrite không?
2. Có nên sinh machine-readable priority labels cho requirements không?
3. Có nên hỗ trợ nhiều brief inputs từ ticket system/PRD/wiki cùng lúc không?

