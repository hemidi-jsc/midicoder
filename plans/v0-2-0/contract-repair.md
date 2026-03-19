# Thiết kế command `midicoder contract repair` - v0.2.0

## 1. Mục tiêu sản phẩm

`midicoder contract repair` sửa bộ contracts đã có mà **không quay lại sinh lại tất cả** trừ khi bắt buộc. Đây là command responsible cho việc:

- phát hiện contract defects
- phân loại mức độ lỗi
- đề xuất/cập nhật fixes theo rule-based pipeline
- tạo remediation artifacts rõ ràng

---

## 2. Vai trò trong pipeline mới

Nó là cầu nối giữa:

- `contract gen`
- `ir build`
- `runtime fix` khi lỗi được xác định là contract-level

---

## 3. Nguyên tắc

1. Deterministic-first.
2. Patch cục bộ trước khi regenerate diện rộng.
3. Giữ nguyên IDs, refs, public contracts nếu có thể.
4. Không thay intent business nếu chưa có remediation brief hợp lệ.

---

## 4. Input

1. current contracts
2. validation reports từ contract check / ir build / runtime fix classifier
3. optional remediation brief
4. optional previous successful contracts snapshot

---

## 5. Output

### 5.1 Primary outputs

- repaired contract files
- repair report
- repair plan artifact

### 5.2 Secondary outputs

- diagnostics grouped by severity
- exact locations changed
- follow-up required actions

---

## 6. Phân loại lỗi contract

### Lớp A - structural

- schema invalid
- missing required field
- duplicated id
- illegal enum/reference

### Lớp B - semantic linkage

- route -> command/query mismatch
- policy resource mismatch
- workflow transition mismatch
- integration op mismatch

### Lớp C - architecture

- service ownership conflict
- tenancy scope conflict
- cross-service event inconsistency

### Lớp D - brief mismatch

- contract không phản ánh remediation brief mới
- contract drift so với business intent đã approved

---

## 7. Thuật toán cấp cao

### Phase 1 - Diagnostics aggregation

Gom lỗi từ:

- contract validators
- ir build validators
- verification classifier

### Phase 2 - Repair strategy selection

Nếu lỗi thuộc:

- structural/simple semantic => deterministic patch
- architecture-level but localizable => targeted regeneration batch
- brief mismatch => yêu cầu remediation brief và regenerate batch liên quan

### Phase 3 - Deterministic patching

Ví dụ:

- canonicalize refs
- fill normalized auth fields
- restore missing route binding if uniquely inferable
- patch service ownership

### Phase 4 - Local regenerate (optional)

Chỉ regenerate module liên quan, ví dụ:

- api/http.yaml
- policy/access.yaml
- workflow/workflows.yaml

### Phase 5 - Revalidate all

Phải chạy lại toàn bộ contract validation và ref integrity.

---

## 8. Remediation integration

Nếu lỗi đến từ verification/runtime và được classifier gắn nhãn `contract_defect`, command này phải:

1. load remediation brief
2. xác định impacted contract areas
3. update cục bộ
4. emit repair report

---

## 9. Determinism / LLM usage

- Default v0.2.0: không dùng LLM cho repair path chuẩn.
- Nếu cần regenerate từ remediation brief, có thể reuse `contract gen` batch-mode với scope nhỏ.

---

## 10. Failure modes

1. Không xác định được unique fix
2. Repair xung đột public IDs
3. Một lỗi kéo theo thay đổi diện rộng vượt threshold
4. Remediation brief không đủ rõ

### Policy khi fail

- Không patch bừa
- Emit repair-blocked artifact
- Yêu cầu escalation lên brief rewrite hoặc contract gen scoped rerun

---

## 11. Run artifacts

- repair-diagnostics.json
- repair-plan.json
- changed-contracts.json
- validation-after-repair.json

---

## 12. Test strategy

1. Structural fix tests
2. Cross-reference repair tests
3. Topology repair tests
4. Tenancy scope repair tests
5. Contract drift containment tests

---

## 13. Open questions

1. Threshold nào buộc repair chuyển thành scoped regenerate?
2. Có nên hỗ trợ “repair preview” không ghi file?
3. Có nên giữ patch-style contract ops artifact không?

