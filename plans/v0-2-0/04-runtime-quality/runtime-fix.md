# Thiết kế command `midicoder runtime fix` - v0.2.0

## 1. Mục tiêu sản phẩm

`midicoder runtime fix` không còn là LLM patch generator. Trong v0.2.0, nó là **deterministic remediation orchestrator**.

Nhiệm vụ của command:

1. đọc kết quả verification failures
2. phân loại lỗi theo tầng
3. xác định lỗi thuộc implementation, contract, test-generation hay brief
4. tạo remediation brief/task set
5. tạo version mới
6. chạy lại pipeline từ pha thích hợp

---

## 2. Vì sao phải bỏ LLM ở runtime fix

Runtime fix kiểu LLM patching có nhược điểm:

1. fix cục bộ nhưng không sửa nguồn gốc pipeline
2. dễ drift business semantics
3. khó audit
4. khó hội tụ khi lỗi lặp lại

Hướng mới là:

- sửa từ upstream artifact phù hợp
- để compiler pipeline generate lại có kiểm soát

---

## 3. Input

1. verification summary mới nhất
2. workdir snapshot
3. current version artifacts
4. prior remediation attempts
5. context graph hiện tại

---

## 4. Output

1. remediation report
2. remediation classification artifact
3. remediation brief hoặc remediation task bundle
4. version mới
5. pipeline rerun summary

---

## 5. Error classification model

### Class A - implementation defect

Ví dụ:

- import lỗi
- syntax lỗi
- typecheck fail
- unit test fail do implementation
- missing wiring

### Class B - architecture/integration defect

Ví dụ:

- wrong ownership target
- bad patch target
- module boundary violation
- service graph mismatch

### Class C - contract defect

Ví dụ:

- request/response contract sai
- workflow semantics thiếu
- policy semantics sai

### Class D - brief defect

Ví dụ:

- requirement gốc mâu thuẫn
- business intent thiếu hoặc sai

---

## 6. Remediation routing

### Nếu Class A

Tạo implementation remediation task và rerun từ:

- `code build` hoặc `code gen` tùy mức ảnh hưởng

### Nếu Class B

Tạo integration remediation task và rerun từ:

- `index` hoặc `code gen`

### Nếu Class C

Tạo remediation brief + contract patch set và rerun từ:

- `contract repair` hoặc `contract gen` scoped

### Nếu Class D

Tạo remediation brief mới và rerun từ:

- `brief rewrite`

---

## 7. Thuật toán cấp cao

### Phase 1 - Load verification artifacts

1. Read verify-summary
2. Load stage logs
3. Normalize errors

### Phase 2 - Root-cause classification

1. map failure -> affected files
2. map files -> contracts/IR refs/modules/services
3. classify upstream defect layer

### Phase 3 - Build remediation artifact

Artifact có thể gồm:

- remediation brief
- remediation task set
- impacted modules list
- preserved invariants

### Phase 4 - Create new version

Không sửa trực tiếp version hiện tại theo cách opaque.

- create new version
- carry forward approved artifacts cần thiết
- attach remediation metadata

### Phase 5 - Rerun pipeline

Chạy lại từ phase tương ứng.

### Phase 6 - Compare results

1. failure reduced?
2. new regressions introduced?
3. convergence status?

---

## 8. Remediation brief format

```json
{
  "mode": "remediation",
  "source_version": "v123",
  "failure_classes": ["implementation_defect"],
  "preserve_invariants": [
    "Không đổi public API contract create_user",
    "Không đổi workflow state transitions"
  ],
  "corrective_goals": [
    "Sửa wiring DB session trong app/shared/db.py",
    "Loại bỏ circular import giữa app.users.service và app.main"
  ],
  "evidence": {
    "verify_summary": "...",
    "changed_files": []
  }
}
```

---

## 9. Không dùng LLM

Runtime fix v0.2.0 phải chạy hoàn toàn deterministic.

Nếu remediation brief cần ngôn ngữ tự nhiên đẹp hơn, có thể sinh template deterministic từ error classes. Không phụ thuộc model.

---

## 10. Hội tụ vòng lặp

Hệ thống phải track:

- iteration count
- error signature history
- failure reduction score
- repeated-failure threshold

Nếu vượt threshold mà không hội tụ:

- stop auto loop
- emit escalation report

---

## 11. Failure modes

1. classifier không đủ bằng chứng root cause
2. remediation route chọn sai phase
3. rerun tạo regressions lớn hơn
4. loop không hội tụ

### Policy

- stop with escalation artifact
- không patch trực tiếp workdir bằng heuristic mù

---

## 12. Observability

Artifacts bắt buộc:

- remediation-classification.json
- remediation-brief.md / .json
- rerun-plan.json
- convergence-report.json
- version lineage report

---

## 13. Test strategy

1. Error classification tests
2. Routing tests implementation vs contract vs brief
3. Version lineage tests
4. Auto-loop convergence tests
5. Escalation threshold tests

---

## 14. Open questions

1. Có nên cho runtime fix chạy scoped pipeline song song theo service không?
2. Có nên lưu diff giữa old/new brief trong remediation mode không?
3. Có nên có confidence score để quyết định auto-rerun hay manual review?



## 15. Quan hệ với generated tests

Vì v0.2.0 yêu cầu DSL hỗ trợ full test generation, `runtime fix` phải hiểu thêm một lớp lỗi mới:

- test_generation_defect
- insufficient_coverage

Nếu lỗi đến từ generated tests hoặc coverage < 85%, remediation route mặc định không phải patch tay testcase trong workdir, mà là quay về upstream artifact phù hợp:

- contract/test DSL
- IR test intents
- canonical backend code/test build outputs
