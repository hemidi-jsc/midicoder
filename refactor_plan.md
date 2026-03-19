# Refactor Plan: Chỉnh logic nghiệp vụ và luồng xử lý

## 1) Clarify mục tiêu sau khi align
Mục tiêu đúng theo yêu cầu đã làm rõ:

1. `Brief -> Contract` dùng LLM.
2. `Contract -> Diagram` để review nghiệp vụ.
   Diagram chỉ build ở bước Contract, không build ở IR build.
3. `Contract -> IR -> Code Plan` phải deterministic, không dùng LLM.
4. `Code Plan -> Patch Plan` hiện tại vẫn dùng model (đúng), vì nhiệm vụ không chỉ chuyển từ pseudo FastAPI sang target programming language mà còn nâng cấp pseudo thành implementation tốt hơn.
5. `Patch Plan -> Runtime Test + Fix` dùng model cho runtime-fix loop.

Ghi chú quan trọng:
- Hiện tại **chưa hỗ trợ SLM** cho code gen/runtime fix theo engine riêng.
- Refactor này tập trung vào sửa đúng lõi: **Code Plan phải là pseudo FastAPI thực thụ từ IR**.
- Cần có workstream song song: **nghiên cứu triển khai Qwen Coder Next3** cho `code gen` và `runtime fix`.

---

## 2) Hiện trạng codebase (điểm đúng/sai so với mục tiêu)

## 2.1 Điểm đã đúng
- `contract gen` đang dùng LLM: `midicoder/commands/contract.py`.
- `ir build` deterministic: `midicoder/ir/builder/builder.py`.
- Có pipeline patch/apply/runtime test/fix đầy đủ.

## 2.2 Điểm cần refactor
1. **Code Plan chưa đúng bản chất pseudo FastAPI**
- `code build` hiện sinh plan metadata + contracts (`pseudo_struct`, `integration_contract`, `required_files`) tại `midicoder/code/builder/planner.py`, `emitter.py`.
- Chưa sinh pseudo-code FastAPI theo file/section/anchor đủ rõ để code gen vừa nâng cấp implementation vừa chuyển sang target language.

2. **Boundary giữa Code Plan và Code Gen chưa clean**
- Nhiều logic business validation/retry nằm sâu trong `midicoder/code/generator/pipeline.py`.
- `code gen` vừa gánh “diễn giải plan”, vừa “nâng cấp implementation”, vừa “dịch ngôn ngữ”, khiến khó kiểm soát chất lượng input plan.

3. **Diagram sau Contract chưa tách phase rõ**
- Diagram hiện chủ yếu đi qua `ir build`.
- Thiếu bước explicit để review contract-level diagram ngay sau `contract gen`.

---

## 3) Target architecture (đã chỉnh theo đúng hiểu biết)

1. `brief/contract` (LLM)
2. `contract diagram` (deterministic từ contracts)
3. `ir build` (deterministic)
4. `code build` (deterministic): sinh **Pseudo FastAPI Code Plan chuẩn**
5. `code gen` (model-based implementation synthesizer): nâng cấp pseudo FastAPI thành implementation chất lượng hơn và chuyển sang target language để ra patch-plan
6. `code apply`
7. `runtime test`
8. `runtime fix` (model-based)

Nguyên tắc:
- `code build` không gọi model.
- `code gen` nhận input pseudo ổn định để tập trung nâng cấp implementation (typing, error handling, framework idioms) và target adaptation, nhưng không được drift business contract.

---

## 3.1 Phân tích Contract -> IR -> Code Build (chi tiết kỹ thuật)
Kết quả phân tích code hiện tại:
- IR hiện tại đủ gần để sinh pseudo FastAPI deterministic.
- Điểm nghẽn lớn nhất nằm ở lớp adapter `IR -> plan` trong `code build`, không chỉ ở schema IR.

Các vấn đề chính đã xác định:
1. Rule mapping dễ lệch key
- `midicoder/code/builder/validation.py` (`_build_rule_index`) normalize trực tiếp `applies_to`, dễ mismatch khi giá trị là typed ref kiểu `Command:update_role`.
- Hệ quả: pseudo thiếu bước rules thực tế.

2. Policy mapping chưa gắn vào item nghiệp vụ
- `_build_policy_index` đang index theo `permission_id`, nhưng lookup theo `item.raw_id`.
- Hệ quả: `policy_contract` và `security_contract` thiếu dữ liệu.

3. Error index đọc sai bucket
- `midicoder/code/builder/integration.py` (`_build_error_index`) đọc `application.errors` thay vì `domain.errors`.
- Hệ quả: pseudo thiếu ngữ nghĩa error flow.

4. Route context bị rút gọn quá mức
- Route index cho plan chưa giữ đủ `auth/description/tags` để emitter sinh pseudo controller chuẩn.

5. Code Plan chưa sinh pseudo code block
- Hiện thiên về `pseudo_struct` + metadata contracts, chưa sinh pseudo FastAPI theo file/anchor như mục tiêu.

Hướng điều chỉnh theo chặng:
- Contract -> IR:
1. Chuẩn hoá `Rule.applies_to` về typed-ref canonical khi build IR (hoặc dual-parse).
2. Bổ sung index liên kết `Permission.resource -> target item` trong IR output.
3. Parse `HttpRoute.auth` thành cấu trúc machine-readable (`required_roles`, `required_permissions`) ngoài raw string.

- IR -> Code Build:
1. Sửa rule/policy/error indexes để lookup theo cùng canonical key với `item.raw_id`.
2. Route index giữ đầy đủ field để pseudo emitter dùng trực tiếp.
3. `iter_plan_items` xuất normalized contracts đầy đủ trước khi emit pseudo.

- Code Build output:
1. Nâng `code-plan` schema với `pseudo_files[]` chứa pseudo FastAPI block thật.
2. Emitter deterministic sinh pseudo cho `controller/service/schema/model/workflow`.
3. Giữ `pseudo_struct` chỉ để backward compatibility.

---

## 4) Refactor phases

## Phase A - Chuẩn hoá schema Code Plan thành “Pseudo FastAPI thật”
Mục tiêu: chuyển Code Plan từ “plan contracts” sang “pseudo code artifacts” có thể dịch trực tiếp.

Công việc:
1. Nâng schema `*.code-plan.json`:
- thêm `pseudo_files[]` với cấu trúc:
  - `runtime_path`
  - `role` (`controller|service|schema|model|workflow|bootstrap`)
  - `imports[]`
  - `anchors {region_start, region_end}`
  - `pseudo_code` (FastAPI-style code block)
  - `io_contract_ref`, `policy_ref`, `workflow_ref`

2. Giữ backward-compat fields hiện có (`pseudo_struct`, `integration_contract`) trong 1-2 version.

3. Update writer/index:
- `midicoder/code/builder/writer.py`
- `midicoder/code/generator/index_manifest.py`
4. Bổ sung trường normalized-contracts trong plan payload (route/rule/policy/error đã resolve key).

Acceptance:
- Mỗi plan item có pseudo code block cụ thể theo file.
- `code build` chạy offline hoàn toàn.

---

## Phase B - Refactor deterministic emitter để sinh pseudo FastAPI chuẩn
Mục tiêu: `code build` thực sự biên dịch IR -> pseudo FastAPI (không LLM).

Công việc:
1. Tách emitter theo kind:
- `midicoder/code/builder/emitters/controller_fastapi.py`
- `.../service_fastapi.py`
- `.../schema_fastapi.py`
- `.../model_fastapi.py`
- `.../workflow_fastapi.py`

2. Từ IR contracts sinh pseudo đầy đủ:
- route decorators
- request/response schema skeleton
- dependency injection points
- policy/guard checkpoints
- workflow transition checkpoints

3. Chuẩn anchor naming ổn định theo `ir_ref` để code gen/apply không drift.

4. Bổ sung validator riêng cho pseudo-plan:
- syntax-level pseudo checks
- cross-ref giữa pseudo_files và required_files
- route <-> io mapping integrity
5. Sửa các adapter indexes:
- rule index canonical theo typed-ref
- policy index theo `resource -> item`
- error index đọc `domain.errors`
- route summary giữ `auth/description/tags`

Acceptance:
- `code build` output có thể đọc như “bộ pseudo FastAPI hoàn chỉnh”.
- Không còn phụ thuộc vào việc code gen tự suy luận nghiệp vụ thiếu trong plan.

---

## Phase C - Làm rõ Code Gen: implementation-upgrade + target adaptation
Mục tiêu: giữ đúng vai trò `code gen` là nâng cấp pseudo FastAPI thành implementation tốt hơn, rồi chuyển sang target language patch-plan.

Công việc:
1. Refactor `midicoder/code/generator/pipeline.py`:
- giảm business heuristics không cần thiết ở phase gen.
- lấy input trực tiếp từ `pseudo_files[]`.
- tách rõ 2 lớp xử lý:
  - `contract-preserving synthesis` (nâng cấp code nhưng giữ semantics nghiệp vụ),
  - `target adaptation` (đưa code về ngôn ngữ/framework đích).

2. Chuẩn hoá prompt/context builder:
- tập trung vào nâng cấp chất lượng implementation + mapping syntax/framework idioms.
- cấm thay đổi business contract (guard/policy/workflow semantics).

3. Cập nhật validation hậu-gen:
- vẫn giữ AST/import/cycle checks.
- báo lỗi rõ theo nhóm `implementation_regression`, `translation_error`, `contract_drift`, `syntax_error`.

Acceptance:
- Chất lượng patch ổn định hơn vì input pseudo đã rõ.
- `code gen` tạo runtime code tốt hơn pseudo baseline nhưng không đổi nghiệp vụ cốt lõi.
- `code gen` hoàn thành target adaptation đúng framework/language đích.

---

## Phase D - Contract Diagram phase rõ ràng
Mục tiêu: review nghiệp vụ trước IR.

Công việc:
1. Tạo command mới `midicoder contract diagram`.
2. Sinh `contracts/diagrams/*.mmd` trực tiếp từ YAML contract.
3. Tích hợp optional auto-run sau `contract gen`.
4. Gỡ diagram generation khỏi `IR build` (IR chỉ compile + validate + emit IR artifacts).

Acceptance:
- Có diagram contract-level ngay cả khi chưa build IR.

---

## Phase E - Hardening theo logic issues hiện có
Mục tiêu: tăng độ tin cậy trước khi mở rộng sang SLM tương lai.

Ưu tiên fix:
1. `contract check` scope + wording + tránh phụ thuộc LLM không cần thiết.
2. `contract feedback` count chính xác.
3. `contract gen` fail path trả exit code nhất quán.
4. runtime analyzer map traceback đúng category.
5. runtime fix hiển thị operation count đúng.
6. `code apply` chỉ smoke import khi có changed paths.
7. `loader` fail-fast khi operation invalid.
8. giảm side effects ở command read-only (`ensure_base_layout`).

---

## Phase F - Nghiên cứu triển khai Qwen Coder Next3
Mục tiêu: chuẩn bị lộ trình kỹ thuật để đưa Qwen Coder Next3 vào `code gen` và `runtime fix` một cách an toàn.

Công việc:
1. Nghiên cứu adapter layer cho model backend:
- chuẩn hoá interface gọi model (`system/context/prompt/limits/retry`) để thay thế dần cấu hình `llm.high/cheap`.
- đánh giá các phương án chạy Qwen Coder Next3: local server, self-hosted inference, hosted API.

2. Thiết kế config profile theo phase:
- `models.patch_planning`
- `models.runtime_fix`
- hỗ trợ chọn provider/model/timeout/token budget cho Qwen Coder Next3.

3. Benchmark chất lượng trên tập case nội bộ:
- so sánh với engine hiện tại theo các tiêu chí:
  - contract fidelity
  - patch apply success rate
  - syntax/import error rate
  - runtime-fix convergence (số vòng loop để pass runtime test)

4. Safety rails và rollout strategy:
- thêm feature flags để fallback engine cũ.
- bắt buộc lưu run artifacts để audit output từ Qwen.

Acceptance:
- Có báo cáo benchmark + quyết định Go/No-Go.
- Có prototype adapter tích hợp được vào `code gen` path mà không phá backward compatibility.

---

## 5) File tác động chính

Code build:
- `midicoder/code/builder/planner.py`
- `midicoder/code/builder/emitter.py`
- `midicoder/code/builder/models.py`
- `midicoder/code/builder/writer.py`
- `midicoder/code/builder/quality.py`

Code gen:
- `midicoder/code/generator/pipeline.py`
- `midicoder/code/generator/prompt.py`
- `midicoder/code/generator/plan_loader.py`
- `midicoder/code/generator/index_manifest.py`

Contract diagram:
- `midicoder/commands/contract.py`
- `midicoder/contract/diagram_builder.py` (new)

Hardening:
- `midicoder/runtime/fix/analyzer.py`
- `midicoder/runtime/fix/generator.py`
- `midicoder/code/applicator/pipeline.py`
- `midicoder/code/applicator/loader.py`
- `midicoder/commands/base.py`

---

## 6) Test strategy

1. Deterministic tests cho code build pseudo:
- cùng IR -> cùng pseudo files/hash.
- offline pass.

2. Contract fidelity tests:
- guards/policies/workflow trong pseudo không bị mất.

3. Translation tests cho code gen:
- pseudo FastAPI -> target patch-plan hợp lệ.
- không drift contract semantics.
4. Implementation-upgrade tests:
- với cùng pseudo input, output phải cải thiện cấu trúc code theo checklist chất lượng (typing/error handling/module boundaries).
- không thay đổi behavior business đã encode trong pseudo/rules/policies/workflow.
5. Qwen Coder Next3 evaluation tests:
- chạy benchmark set ở mode thử nghiệm.
- ghi nhận metric chất lượng/độ ổn định so với baseline hiện tại.
6. Regression tests cho logic issues ưu tiên.

---

## 7) Rollout đề xuất

1. Milestone 1: Phase A + B (sửa đúng Code Plan trước).
2. Milestone 2: Phase C (implementation-upgrade + target adaptation).
3. Milestone 3: Phase D + E (diagram + hardening).
4. Milestone 4: Phase F (Qwen Coder Next3 research + pilot integration).

---

## 8) Kết luận
Điểm mấu chốt của refactor lần này là sửa đúng vai trò **Code Plan**:
- phải là pseudo FastAPI deterministic từ IR,
- không dùng LLM,
- đủ giàu thông tin để code gen nâng cấp implementation có kiểm soát và chuyển sang target language.

`code gen` dùng model là đúng với mục tiêu hiện tại; SLM là hướng mở rộng sau, không phải điều kiện bắt buộc của đợt refactor này.
Trong roadmap mở rộng, Qwen Coder Next3 là hướng ưu tiên và đã được tách thành phase nghiên cứu/triển khai riêng.
