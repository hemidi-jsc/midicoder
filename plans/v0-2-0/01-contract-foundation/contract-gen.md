# Thiết kế command `midicoder contract gen` - v0.2.0

## 1. Mục tiêu tài liệu

Tài liệu này mô tả:

1. luồng `contract gen` hiện đang chạy trong codebase
2. các ưu/nhược điểm thật sự của implementation hiện tại
3. thiết kế v0.2.0 dựa trên hiện trạng đó, không đoán mò

---

## 2. Hiện trạng code hiện có

## 2.1 Giới hạn phạm vi của đợt update này

Pha `contract gen` của v0.2.0 chỉ tập trung vào **backend systems**:

- modular monolith backend
- microservice backend
- big app backend
- platform/service APIs

Frontend support, UI contract generation, component/page DSL và frontend test synthesis **không nằm trong phạm vi patch set này**.

## 2.1 Entry point CLI

`midicoder contract gen` nằm tại `midicoder/commands/contract.py::gen()`.

Luồng hiện tại:

1. setup version/path
2. đọc `master-brief.md`
3. load config + `llm.high`
4. build `system_prompt` với stack target + master brief
5. gọi `get_contract_files_from_master_brief(...)`
6. lấy ra `required_files`
7. gọi `_generate_contract_files(...)` để generate **mỗi file một pass**

=> `contract gen` hiện có hai pha LLM rõ ràng:

- pha 1: xác định file contracts cần sinh
- pha 2: sinh nội dung từng file contract

## 2.2 Pha xác định contract files

Hàm `get_contract_files_from_master_brief(...)` ở `midicoder/brief/analyzer.py`:

- dùng cache `brief_keywords.json`
- nếu cache miss/stale thì gọi LLM để trả JSON gồm keywords + `contract_files`
- ép luôn `meta/info.yaml` và `glossary.yaml` phải có trong output

Đây là behavior thật của code hiện tại.

### Ưu điểm

1. Có cache theo hash brief.
2. Có contract file planning trước khi generate.
3. Ép include `meta/info.yaml` + `glossary.yaml`, tránh output tối thiểu quá mức.

### Nhược điểm

1. Quyết định file list vẫn phụ thuộc mạnh vào prompt/LLM.
2. Danh sách file hiện gắn với DSL hiện hữu, chưa đủ cho SaaS lớn/multi-service.
3. Các command khác (`brief analyze`, `contract check`, `contract repair run`) cũng gọi lại logic này, có thể tạo coupling lớn giữa brief-analysis và contract lifecycle.

## 2.3 Pha generate nội dung contract files

`_generate_contract_files(...)` hiện làm như sau:

1. tạo `run_dir`
2. chia `required_files` thành `batches = [[file] for file in required_files]`
   - nghĩa là **mỗi file là một pass riêng**
3. cho từng pass:
   - build context bằng `build_context_for_contract_gen(...)`
   - save trace/prompt
   - call LLM với `system_prompt` + `context_block` + `prompt`
   - strip YAML code fences
   - parse documents bằng `parse_contract_documents(...)`
   - validate parsed_files
   - ghi file ra `versions/<version>/contracts/...`

=> Đây là one-file-per-pass architecture thật sự, không phải batch theo nhóm file.

## 2.4 Observability hiện tại

Implementation hiện tại khá mạnh ở mặt trace:

- trace per pass
- prompt saved
- raw response saved
- processed response saved
- error artifacts
- generation summary
- resume support

Ngoài ra còn có `contract gen resume` để đọc run gần nhất, xác định file nào đã thành công, file nào còn fail và resume phần còn lại.

## 2.5 Ràng buộc hiện tại của system prompt

System prompt được build từ:

- version
- stack target
- master brief

Prompt context lại đến từ `build_context_for_contract_gen(...)`. Nghĩa là contract gen hiện tại không chỉ dùng brief, mà còn dùng context/index artifacts và schema tree của repo.

---

## 3. Ưu điểm của implementation hiện tại

1. **Có contract planning stage riêng**.
2. **Có cache keyword map**, giảm duplicated analysis calls.
3. **One-file-per-pass** giúp schema slicing rõ và dễ debug.
4. **Resume được**, rất hữu ích khi một số pass fail giữa chừng.
5. **Observability tốt** với trace/prompt/response đầy đủ.

---

## 4. Nhược điểm của implementation hiện tại

1. Cả file planning và file generation đều phụ thuộc LLM.
2. Danh sách DSL file hiện chưa đủ cho SaaS lớn hoặc multi-service.
3. Generation granularity là per file, nhưng chưa có phase planning “semantic batches” ở cấp bounded context/service.
4. Chưa có deterministic post-generation canonicalizer đủ mạnh ngoài parse/validate hiện có.
5. Chưa tách rõ core contracts, topology contracts, tenancy/billing contracts, reliability/ops contracts.

---

## 5. Thiết kế v0.2.0

## 5.1 Mục tiêu mới

`contract gen` vẫn là một trong rất ít command còn dùng LLM mặc định. Nhưng v0.2.0 cần nâng nó thành:

- contract compiler planner cho hệ lớn
- DSL generator có topology awareness
- source of truth đủ giàu cho `ir build` và `code build`

## 5.2 Những gì cần giữ từ hiện trạng

1. keyword cache
2. one-file-per-pass hoặc one-batch-per-scope generation
3. run traces rất chi tiết
4. resume support

## 5.3 Những gì cần thay đổi

### A. Mở rộng DSL file planning

Danh sách file mục tiêu phải vượt DSL hiện tại và bổ sung ít nhất:

- topology/services.yaml
- topology/messaging.yaml
- tenancy/tenancy.yaml
- billing/billing.yaml
- ops/observability.yaml mở rộng
- service-local integration contracts nếu multi-service

### B. Thay per-file planning bằng scoped planning

Thay vì chỉ hỏi “cần file nào?”, v0.2.0 nên plan theo scopes:

- core domain
- application/API
- policy/security
- workflow/process
- persistence/integration
- topology/tenancy/billing/ops

### C. Strengthen deterministic validation

Sau generate, không chỉ parse YAML mà còn validate:

- cross-file refs
- service ownership
- tenancy scope consistency
- async messaging topology
- reliability policy completeness

---

## 6. Thuật toán v0.2.0 đề xuất

### Phase 1 - Brief-driven contract scope planning

Giữ keyword cache + file planning, nhưng nâng output thành:

- required files
- required scopes
- service topology hints
- domain boundaries

### Phase 2 - Scoped generation

Có thể vẫn per-file ở bước materialize, nhưng planning phải per-scope.

### Phase 3 - Deterministic validation and canonicalization

Phải có validate mạnh hơn code hiện tại trước khi cho phép `ir build`.

### Phase 4 - Resume / retry

Giữ tinh thần `contract gen resume` hiện tại.

---

## 7. Kết luận thiết kế

`contract gen` là command nên tiếp tục được phép dùng LLM trong v0.2.0. Tuy nhiên redesign phải dựa trên 4 điểm thật đang có trong code:

1. file planning qua brief analyzer + cache
2. one-file-per-pass generation
3. trace rất chi tiết
4. resume support



## 8. Yêu cầu mới: DSL phải hỗ trợ full test generation

Đây là yêu cầu chốt mới của v0.2.0:

1. DSL phải đủ giàu để sinh được **full tests** cho backend.
2. Test contracts không chỉ mô tả scenario mức cao, mà phải support:
   - unit tests
   - integration tests
   - API tests
   - fixture/test data contracts
   - coverage expectations
3. `testing/tests.yaml` không còn là optional artifact yếu; nó phải trở thành source quan trọng cho `runtime test`.
4. Mỗi bounded context/service phải khai báo được tối thiểu:
   - critical paths
   - invariants
   - error cases
   - auth/policy cases
   - idempotency/retry cases nếu có
5. Bộ generated test suite phải hướng tới **coverage >= 85%** trên backend business/application layers.

### 8.1 Hệ quả lên DSL

Cần bổ sung vào DSL ít nhất các khái niệm:

- test suites theo layer
- fixtures / seed data contracts
- mock/stub integration policies
- expected coverage targets
- critical user journeys / service flows
- contract-derived assertions

### 8.2 Hệ quả lên downstream phases

- `ir build` phải compile test intents vào IR
- `code build` phải sinh canonical test skeletons hoặc canonical test plans
- `runtime test` phải dùng generated tests như một phần mặc định của verification pipeline
