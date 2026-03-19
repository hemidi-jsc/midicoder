# Thiết kế command `midicoder contract repair` - v0.2.0

## 1. Phạm vi tài liệu

Tài liệu này mô tả chính xác luồng hiện có của:

- `midicoder contract repair prepare`
- `midicoder contract repair run`

trọng tâm là `repair run`, vì đây là nơi xử lý repair thật sự trong code hiện tại.

---

## 2. Hiện trạng code hiện có

## 2.1 `contract repair prepare`

Entry point: `midicoder/commands/contract.py::repair_prepare()`.

Luồng hiện tại:

1. setup version/path
2. yêu cầu tồn tại `contract-feedbacks.yml`
3. gọi `validate_feedback(...)`
4. ghi run outputs `contract_repair_prepare`
5. in report bằng `report_repair_status(...)`

### `validate_feedback(...)` thực sự làm gì

Trong `midicoder/contract/feedback_processor.py`:

- parse YAML feedback file bằng `ruamel`
- validate schema bằng `FeedbackFile.model_validate(...)`
- kiểm tra `meta.version` có khớp current version không
- normalize từng item.file sang contracts path hợp lệ
- kiểm tra file contract tương ứng có tồn tại không

=> `prepare` hiện là một bước **schema + path validation** cho feedback file, chưa repair gì cả.

## 2.2 `contract repair run`

Entry point: `midicoder/commands/contract.py::repair_run()`.

Luồng hiện tại:

1. validate feedback file
2. lấy các `pending` hoặc `in_progress` items
3. load `llm.high`, schema tree, master brief
4. lại gọi `get_contract_files_from_master_brief(...)` để lấy available contract files
5. group feedback items theo file bằng `group_feedback_by_file(...)`
6. sắp xếp thứ tự file repair bằng `determine_file_repair_order(...)`
7. xử lý **theo file**, không theo từng feedback item riêng lẻ
8. mỗi file được xử lý bởi `process_file_feedback_items(...)`
9. collect repair results và ghi summary

=> Đây là một **file-level repair pipeline**, không phải single-item patch loop.

## 2.3 `determine_file_repair_order()` đang làm gì

Code hiện tại dùng pattern-based ordering:

- foundation-like files: error/entity/event/glossary/info/meta
- dependent-like files: command/query/http/api/rule/workflow/policy

rồi trả thứ tự:

1. foundation
2. other
3. dependent

=> Đây là heuristic phụ thuộc tên file, không phải dependency graph chuẩn.

## 2.4 `process_file_feedback_items()` hiện đang làm gì

Đây là lõi thực sự của contract repair run.

Cho mỗi file:

1. đọc contract file hiện tại
2. validate file riêng lẻ bằng `validate_single_contract_file(...)`
3. extract existing IDs trong file
4. extract available reference IDs từ dependency files
5. build context cho contract repair bằng `build_context_for_contract_repair(...)`
6. build comprehensive schema cho file type
7. nếu có `available_contract_files`, bổ sung cross refs
8. build prompt repair chi tiết
9. save debug files
10. gọi LLM với `CONTRACT_REPAIR_SYSTEM_PROMPT`
11. parse repair plan
12. apply patches ngay bằng `apply_contract_patches(...)`
13. chạy một số safety fix hardcoded cho vài file đặc biệt
14. revalidate file sau patch
15. update feedback statuses
16. trả result dict

=> Có nghĩa là `contract repair run` hiện tại **không chỉ generate đề xuất**, mà còn **apply patches ngay lập tức** vào contracts.

---

## 3. Ưu điểm của implementation hiện tại

1. **File-level repair** hợp lý hơn single-item repair vì giữ context toàn file.
2. **Có feedback file formalized**, tạo quy trình sửa có trạng thái.
3. **Có validation trước và sau patch**.
4. **Có update trạng thái feedback items**.
5. **Có debug artifacts per file**, giúp audit.

---

## 4. Nhược điểm của implementation hiện tại

1. `repair run` vẫn phụ thuộc LLM làm trung tâm.
2. Thứ tự dependency hiện mới là heuristic theo pattern, chưa phải graph-based.
3. Có safety fix cục bộ hardcoded cho vài file, cho thấy pipeline chưa đủ tổng quát.
4. Repair apply ngay vào contracts file, nên nếu prompt sai vẫn có nguy cơ patch không tối ưu.
5. Chưa tách rõ deterministic repair path với scoped regenerate path.

---

## 5. Thiết kế v0.2.0

## 5.1 Mục tiêu mới

`contract repair` v0.2.0 nên trở thành command deterministic-first, gồm 2 lớp:

- `prepare`: validation + repair planning
- `run`: deterministic repair executor, chỉ fallback sang scoped regenerate khi cần

## 5.2 Những gì cần giữ

1. feedback file contract
2. file-level grouping
3. validation trước/sau sửa
4. feedback status updates
5. debug artifacts theo file

## 5.3 Những gì cần thay đổi

### A. Tách deterministic repair và regenerate

- structural/simple semantic issues: deterministic patch
- ambiguous semantic/architecture issues: scoped regenerate

### B. Thay heuristic order bằng dependency graph

Dựa trên:

- reference graph giữa contracts
- workflow bindings
- route-command-query bindings
- policy/resource references

### C. Không để LLM apply trực tiếp là đường mặc định

Nếu vẫn có LLM fallback trong giai đoạn chuyển tiếp, nó chỉ nên tạo candidate repair plan; deterministic layer phải validate và normalize trước khi apply.

---

## 6. Thuật toán v0.2.0 đề xuất

### Phase 1 - Validate feedback

Giữ logic chuẩn hóa từ `validate_feedback()`.

### Phase 2 - Group + order by real dependency graph

Thay `determine_file_repair_order()` heuristic bằng graph.

### Phase 3 - Deterministic local repair

Ưu tiên sửa:

- canonical refs
- missing required nodes/fields có thể infer chắc chắn
- version mismatch / path mismatch
- ownership/policy/resource normalization

### Phase 4 - Scoped regenerate

Nếu deterministic repair không đủ, rerun scoped `contract gen` cho file/scope liên quan.

### Phase 5 - Revalidate + update feedback

Giữ behavior hiện tại nhưng mở rộng diagnostics.

---

## 7. Kết luận thiết kế

Redesign `contract repair run` phải bắt đầu từ việc thừa nhận đúng hiện trạng code:

1. đây là file-level repair pipeline
2. có feedback-state machine thật
3. đang gọi LLM trực tiếp để tạo và apply repair plan
4. có heuristic dependency ordering

và v0.2.0 phải đẩy command này sang deterministic-first thay vì prompt-first.

