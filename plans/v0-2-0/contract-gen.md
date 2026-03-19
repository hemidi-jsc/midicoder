# Thiết kế command `midicoder contract gen` - v0.2.0

## 1. Mục tiêu sản phẩm

`midicoder contract gen` chuyển product brief chuẩn hóa thành một bộ **DSL contracts đầy đủ, kiểm tra được, và đủ giàu ngữ nghĩa** để compiler IR hoạt động cho hệ thống lớn.

Đây là pha cuối cùng cho phép dùng LLM theo mặc định trong pipeline mới.

---

## 2. Mục tiêu chiến lược của v0.2.0

1. Sinh contracts có thể phục vụ SaaS lớn, modular monolith, microservice nhiều service.
2. Tách rõ business contracts khỏi implementation details.
3. Đảm bảo contracts đủ giàu để `ir build` và `code build` deterministic.
4. Không đẩy trách nhiệm “suy luận nghiệp vụ” xuống `code gen`.

---

## 3. Non-goals

1. Không sinh code.
2. Không suy luận patch location.
3. Không quyết định file structure của workdir.
4. Không “chữa cháy” thay cho contract repair.

---

## 4. Input

1. rewritten brief
2. optional remediation brief
3. optional previous contracts để merge/repair-aware generation
4. optional index/profile summary nếu repo đã tồn tại

---

## 5. Output

### 5.1 Primary outputs

Bộ contracts dưới `.midicoder/versions/<version>/contracts/` hoặc thư mục contract source tương đương:

- domain/entities.yaml
- domain/value_objects.yaml
- domain/events.yaml
- app/commands.yaml
- app/queries.yaml
- app/projections.yaml
- workflow/workflows.yaml
- api/http.yaml
- policy/access.yaml
- integrations/integrations.yaml
- topology/services.yaml (mới)
- topology/messaging.yaml (mới)
- tenancy/tenancy.yaml (mới)
- billing/billing.yaml (mới)
- observability/observability.yaml (mới)

### 5.2 Companion outputs

- generation trace
- prompt/response artifacts
- validation report
- unresolved questions report

---

## 6. DSL v0.2.0 - mở rộng bắt buộc

### 6.1 Topology layer

Thêm DSL cho:

- bounded contexts
- services
- public APIs
- internal APIs
- event topics
- message queues
- scheduled jobs

### 6.2 Tenancy layer

Thêm DSL cho:

- tenant entity / tenant scope
- workspace/org/team scopes
- quota rules
- subscription plan bindings

### 6.3 Billing layer

- billable events
- meter definitions
- subscription state flows
- payment provider integration contracts

### 6.4 Reliability / ops layer

- retries
- dead letter policy
- idempotency policies
- audit requirements
- observability contracts

---

## 7. Thuật toán cấp cao

### Phase 1 - Brief decomposition

Từ rewritten brief, hệ thống tách:

- domain terms
- workflows
- API surfaces
- policy/security rules
- data/storage requirements
- service boundaries

### Phase 2 - Generation planning

Chia contracts thành batches theo domain:

1. domain core
2. application layer
3. workflow
4. policy
5. integration
6. topology/ops

### Phase 3 - LLM generation per batch

LLM được dùng để sinh YAML theo schema mục tiêu.

Prompt phải có:

- canonical glossary
- mandatory schema constraints
- naming rules
- no-placeholder rule
- contract completeness checklist

### Phase 4 - Deterministic validation

Validate:

1. schema validity
2. cross-file references
3. policy references
4. workflow references
5. route-command/query bindings
6. topology-service consistency
7. tenancy scope consistency
8. async integration consistency

### Phase 5 - Repair-first retry

Nếu validation fail:

- ưu tiên deterministic correction nhỏ
- chỉ gọi lại generation cho batch lỗi
- không regenerate toàn bộ nếu không cần

### Phase 6 - Persist + canonicalize

- sort keys/records ổn định
- normalize ids
- write files + reports

---

## 8. Đảm bảo đủ giàu cho compiler downstream

Contract gen phải sinh ra đủ thông tin để `code build` deterministic mà không phải đoán:

1. request/response schemas rõ
2. business rules canonical refs
3. required roles/permissions machine-readable
4. workflow transitions đầy đủ
5. integration operation schemas
6. tenancy and quota semantics
7. service ownership and deployment hints

---

## 9. Determinism / LLM usage

- LLM: có, nhưng chỉ trong generation step
- Validation: deterministic
- Canonicalization: deterministic
- Repair loops: deterministic-first, LLM-second

---

## 10. Failure modes

1. Contracts thiếu references bắt buộc
2. Route trỏ sai command/query
3. Policy resource không canonical
4. Workflow không đóng state graph
5. Multi-service topology mâu thuẫn
6. Tenant scopes không nhất quán

---

## 11. Observability

Mỗi batch generation phải có:

- input context snapshot
- prompt
- raw response
- parsed files
- validation errors
- retry reason

---

## 12. Migration strategy

### 12.1 Hỗ trợ DSL cũ

- Cho phép đọc contracts cũ
- Nếu thiếu modules mới, compiler gắn defaults và warning

### 12.2 Khuyến nghị nâng cấp

Cung cấp lệnh migration DSL riêng ở v0.2.x sau này.

---

## 13. Test strategy

1. Golden tests cho DSL schema
2. Cross-ref tests
3. SaaS topology tests
4. Multi-service messaging tests
5. Tenancy/billing consistency tests

---

## 14. Open questions

1. Có nên tách GraphQL/API gateway DSL riêng ở v0.2.0 không?
2. Có nên hỗ trợ frontend contracts ngay từ đầu không?
3. Service topology nên bắt buộc hay optional?

