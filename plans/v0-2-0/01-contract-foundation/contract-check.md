# Thiết kế command `midicoder contract check` - v0.2.0

## 1. Mục tiêu tài liệu

Tài liệu này bổ sung phần đã thiếu ở bản trước: phân tích chính xác `midicoder contract check` hiện đang làm gì trong code, rồi mới đề xuất redesign.

---

## 2. Hiện trạng code hiện có

Entry point: `midicoder/commands/contract.py::check()`.

Luồng hiện tại:

1. setup version/path
2. xác định `contracts_root`
3. nếu có `master-brief.md` thì **thử** gọi lại `get_contract_files_from_master_brief(...)`
   - mục đích: lấy danh sách `expected_files`
4. nếu không analyze được brief thì fallback sang “check all existing yaml files”
5. lọc `expected_files` chỉ giữ file tồn tại
6. gọi `check_contract(contracts_root)`
7. ghi run outputs
8. nếu có issues thì in tối đa 5 issue và exit 1

## 2.1 Điểm quan trọng dễ hiểu sai

Mặc dù command cố gắng xác định `expected_files` từ brief, nhưng phần validation thực sự lại gọi:

- `check_contract(contracts_root)`

Hàm này validate toàn bộ contract tree từ `contracts_root`, không chỉ danh sách `expected_files` đã tính ở trên.

=> Nói cách khác:

- `expected_files` hiện chủ yếu để báo cáo `checked_files`
- còn validation thật sự là ở scope toàn bộ contracts root

Đây là chi tiết rất quan trọng để tránh mô tả sai command.

## 2.2 `check_contract()` hiện đang làm gì

Trong `midicoder/contract/contract_validator.py`, `check_contract(detail_path)`:

1. validate một loạt file core và optional theo layout contract hiện tại
2. load từng file bằng loader tương ứng
3. chạy nhiều validator cross-file/cross-ref
4. accumulate `ContractIssue`

Danh sách file hiện được hardcode theo DSL hiện hành, ví dụ:

- meta/info.yaml
- glossary.yaml
- domain/entities.yaml
- domain/value_objects.yaml
- domain/enums.yaml
- domain/errors.yaml
- domain/events.yaml
- app/commands.yaml
- app/queries.yaml
- api/http.yaml
- workflows/workflows.yaml
- scenarios/scenarios.yaml
- policy/rbac.yaml
- api/graphql.yaml
- persistence/model.yaml
- integrations/integrations.yaml
- meta/profiles.yaml
- meta/secrets.yaml
- policy/security.yaml
- policy/reliability.yaml
- ops/observability.yaml
- testing/tests.yaml

=> `contract check` hiện là validator **layout-aware và DSL-aware** khá sâu, không chỉ là lint YAML đơn thuần.

---

## 3. Ưu điểm của implementation hiện tại

1. Có validator tập trung `check_contract()` khá rõ ràng.
2. Check được nhiều lớp cross-ref, không chỉ schema.
3. CLI output gọn, có run artifacts.
4. Có fallback nếu brief analysis fail.

---

## 4. Nhược điểm của implementation hiện tại

1. `contract check` vẫn thử gọi LLM-based brief analysis để lấy `expected_files`, dù phần validation thật không cần phụ thuộc hoàn toàn vào LLM.
2. Danh sách DSL file còn gắn với schema hiện hành, chưa đủ cho big update SaaS/multi-service.
3. `checked_files` reporting hiện có thể gây hiểu nhầm vì khác với validation scope thực tế.
4. Chưa phân nhóm diagnostics rõ thành structural/semantic/architecture/brief-drift.

---

## 5. Thiết kế v0.2.0

## 5.1 Mục tiêu mới

`contract check` phải là command **deterministic hoàn toàn**.

Nó không nên cần LLM để xác định phạm vi check mặc định.

## 5.2 Scope model mới

Command nên hỗ trợ các mode:

- `full`: validate toàn bộ contracts root
- `changed-only`: validate impacted files + dependents
- `scope <name>`: validate một DSL scope cụ thể

### Rule mặc định

- default = `full`
- không gọi brief analyzer trong đường mặc định

## 5.3 Diagnostics model mới

Mỗi issue cần có class:

- structural
- semantic_linkage
- architecture
- brief_drift
- migration_warning

## 5.4 Tích hợp với repair pipeline

Output của `contract check` phải là input chuẩn cho:

- `contract feedback`
- `contract repair`
- `runtime fix` classifier khi xác định contract-level defects

---

## 6. Kết luận thiết kế

`contract check` hiện tại không phải command “đơn giản check các file từ brief”. Nó là validator tree-wide khá sâu. Thiết kế v0.2.0 phải giữ ưu điểm đó, nhưng loại bỏ dependency không cần thiết vào LLM trong đường mặc định và làm rõ semantics full-check của command.

