# MidiCoder v0.2.0 - Thiết kế tổng thể big update

## 1. Mục tiêu của bản v0.2.0

Bản v0.2.0 là một đợt nâng cấp kiến trúc lớn với các mục tiêu sau:

1. Giảm LLM xuống mức tối thiểu, lý tưởng chỉ còn ở `contract gen`.
2. Chuyển `code build` từ sinh metadata/pseudo-struct sang sinh **canonical FastAPI executable code**.
3. Chuyển `code gen` thành pha **integration + adaptation + patch planning**, ưu tiên deterministic.
4. Chuyển `code apply` thành **file operation executor thuần túy**, không còn quyết định nội dung nghiệp vụ.
5. Thay `runtime test` từ startup smoke test sang **verification pipeline thật** gồm lint, typecheck, unit test, smoke test.
6. Thay `runtime fix` từ LLM patching sang **deterministic remediation orchestration**, tạo remediation brief/version mới và chạy lại pipeline ở pha phù hợp.
7. Loại bỏ khái niệm người dùng phải biết hoặc đặt seam. Hệ thống chỉ còn khái niệm **automatic seam map** được Midicoder tự động suy luận từ codebase.
8. Mở rộng DSL/IR để đủ sức mô hình hóa SaaS lớn, modular monolith, và microservice multi-service.
9. Đợt v0.2.0 chỉ tập trung **backend, microservice, big-app backend**; chưa đưa frontend support vào phạm vi chính thức.
10. DSL mới phải hỗ trợ **full test generation** để dùng cho `runtime test`, với mục tiêu coverage tối thiểu **85%** ở generated test suite.

---

## 2. Nguyên tắc kiến trúc mới

### 2.1 Contract-first nhưng không LLM-first

- `brief rewrite` và `contract gen` vẫn có thể dùng LLM vì đây là pha chuyển ngôn ngữ tự nhiên thành DSL có cấu trúc.
- Từ `contract check` trở đi, mọi pha cần ưu tiên deterministic compiler pipeline.

### 2.2 Canonical backend IR ở mức code

Thay vì dùng `pseudo_struct` làm intermediate chính, v0.2.0 định nghĩa một tầng mới:

- **Canonical FastAPI Code**
  - là Python code hợp lệ
  - phản ánh logic nghiệp vụ đã được compile từ IR
  - có anchors, ownership, contract refs, semantic markers
  - chưa nhất thiết là production-grade code cuối cùng cho workdir thật

Canonical FastAPI Code là "mã trung gian có thể chạy được" để các stack generator downstream có thể dịch hoặc merge một cách deterministic.

### 2.3 Không còn “real seam” vs “virtual seam” như khái niệm sản phẩm

Ở góc nhìn end-user:

- người dùng **không biết** seam là gì
- người dùng **không cần tạo** seam
- Midicoder phải tự suy luận vị trí chèn/sửa code

Do đó v0.2.0 thay thế:

- `seams`
- `virtual_seams`

bằng một khái niệm duy nhất ở cấp sản phẩm:

- **automatic seam map**

Automatic seam map là output của lệnh `midicoder index`, được xây dựng tự động từ:

- symbols
- imports
- file/module structure
- entrypoints
- framework conventions
- ownership inference
- code exemplars
- AST boundaries
- comment markers cũ (nếu tồn tại)

Nếu repo có marker cũ `midicoder:begin/end`, chúng chỉ là **một nguồn tín hiệu** của automatic seam map, không còn là khái niệm public-facing.

### 2.4 `code apply` phải luôn reindex bằng `midicoder index`

Ngay sau khi apply patch thành công, Midicoder **phải tự chạy lại lệnh `midicoder index`** trên workdir hiện tại.

Lý do:

1. Context artifacts phải đồng bộ với codebase sau apply.
2. Automatic seam map, symbol graph, file ownership, entrypoints có thể đã thay đổi.
3. Pha kế tiếp (`code gen`, `runtime test`, `runtime fix`) phải nhìn thấy trạng thái repo mới nhất.
4. Cơ chế “reindex changed files only” là optimization nội bộ, nhưng contract hệ thống ở cấp command phải được phát biểu là: **`code apply` luôn trigger `midicoder index`**.

### 2.5 Verification-first remediation

- `runtime test` không còn chỉ là boot app.
- `runtime fix` không còn tự sinh patch bằng LLM.
- Thay vào đó, hệ thống:
  - chạy verification pipeline thật
  - phân loại lỗi
  - quyết định lỗi implementation hay contract/brief
  - tạo remediation brief hoặc remediation task set
  - tạo version mới
  - chạy lại pipeline từ pha thích hợp

---

## 3. Luồng pipeline mới đề xuất

### 3.1 Luồng chuẩn

1. `midicoder brief rewrite`
2. `midicoder contract gen`
3. `midicoder contract repair`
4. `midicoder index`
5. `midicoder ir build`
6. `midicoder contract check`
7. `midicoder code build`
8. `midicoder code gen`
9. `midicoder code apply`
10. `midicoder index` (auto-run bắt buộc ngay sau apply)
11. `midicoder runtime test`
12. `midicoder runtime fix`

### 3.2 Nguyên tắc phân vai

- `brief rewrite`: làm rõ product intent thành brief kỹ thuật hóa.
- `contract gen`: sinh DSL contract chuẩn.
- `contract repair`: sửa contract bằng rule-based diagnostics.
- `index`: tạo automatic seam map + project graph + symbol graph.
- `ir build`: compile contracts sang IR giàu ngữ nghĩa.
- `code build`: compile IR sang canonical FastAPI executable code cho **backend**.
- `code gen`: generate patch plan vào workdir/target backend stack từ canonical code + context.
- `code apply`: execute patch plan và reindex.
- `runtime test`: verify chất lượng code thật + generated tests + coverage.
- `runtime fix`: tạo remediation cycle không cần LLM.

---

## 4. Automatic seam map thay thế seam/virtual seam

### 4.1 Vấn đề của mô hình hiện tại

Mô hình hiện tại tách:

- seam thật: từ marker `midicoder:begin/end`
- virtual seam: suy luận từ symbols, exemplars, entrypoints

Nhược điểm:

1. Lộ chi tiết implementation nội bộ ra mô hình mental của sản phẩm.
2. Khiến code build/code gen bị phụ thuộc vào khái niệm người dùng không quan tâm.
3. Làm planner phải branch logic `real seam` vs `virtual seam`.
4. Tạo cảm giác hệ thống chỉ hoạt động tốt nếu repo đã “chuẩn bị sẵn anchor”.

### 4.2 Mô hình mới

Automatic seam map là một danh sách **insertion/update candidates** với confidence score, ví dụ:

- file path
- AST span
- symbol owner
- role (`controller`, `service`, `model`, `bootstrap`, `config`, `test`)
- insertion strategy (`replace_symbol`, `replace_region`, `append_to_module`, `create_file`, `insert_import`, ...)
- ownership class (`owned`, `shared`, `foreign`, `generated`)
- confidence
- evidence list

### 4.3 Nguồn tín hiệu

Automatic seam map được suy luận từ nhiều tầng:

1. AST symbol extraction
2. import graph
3. routing conventions
4. framework entrypoints
5. project profile + stack detector
6. file naming conventions
7. exemplar snippets
8. comment markers legacy
9. git history / changed path history (optional về sau)
10. previous Midicoder generation metadata

### 4.4 Product contract mới

Ở tài liệu và CLI help, Midicoder không còn dùng thuật ngữ seam như input contract của user.

Nếu cần giữ backward compatibility cho artifact cũ:

- `seams.json` và `virtual_seams.json` có thể vẫn tồn tại 1-2 version
- nhưng được coi là legacy implementation detail
- docs mới chỉ mô tả `automatic seam map`

---

## 5. Hướng mở rộng DSL và IR cho SaaS lớn / microservice

### 5.1 Vấn đề hiện tại

DSL hiện tại thiên về một service/backend tương đối đơn khối. Để hỗ trợ SaaS lớn hoặc microservice, cần các lớp mô hình mới.

### 5.2 Cần bổ sung ở cấp DSL

1. **System topology**
   - bounded contexts
   - services
   - public/internal APIs
   - async topics/queues
   - external systems

2. **Tenancy & billing**
   - tenant model
   - tenant isolation mode
   - subscription plans
   - quotas / entitlements
   - billing events

3. **Identity & access at scale**
   - organizations / teams / workspaces
   - role binding scope
   - policy inheritance
   - machine-to-machine credentials

4. **Storage topology**
   - per-service database
   - read replicas
   - caches
   - object storage
   - event store

5. **Inter-service contracts**
   - sync API contracts
   - async event contracts
   - workflow choreography/orchestration
   - saga compensation contracts

6. **Operational contracts**
   - observability
   - retry/dead-letter policies
   - rate limit
   - idempotency
   - migration policy

7. **Frontend and admin surface (optional future)**
   - admin modules
   - user portals
   - BFF/API gateway contracts

### 5.3 Cần bổ sung ở cấp IR

IR v0.2.0 nên có thêm:

- service graph
- deployment boundary
- ownership graph
- integration contracts normalized
- policy graph theo scope
- workflow graph liên service
- storage access graph
- canonical refs cho tenancy/billing/quotas

---

## 6. Các tài liệu thiết kế command-level

Bộ tài liệu được chia thành các subfolder theo thứ tự release patch trong nhánh `v0.2.0`:

### 6.1 `01-contract-foundation/`

1. `01-contract-foundation/brief-rewrite.md`
2. `01-contract-foundation/contract-gen.md`
3. `01-contract-foundation/contract-check.md`
4. `01-contract-foundation/contract-repair.md`

### 6.2 `02-index-context/`

5. `02-index-context/index-command.md`

### 6.3 `03-backend-codegen/`

6. `03-backend-codegen/code-build.md`
7. `03-backend-codegen/code-gen.md`
8. `03-backend-codegen/code-apply.md`

### 6.4 `04-runtime-quality/`

9. `04-runtime-quality/runtime-test.md`
10. `04-runtime-quality/runtime-fix.md`

> Ghi chú: file hiện tại là overview tổng thể; roadmap này cố ý tập trung backend/microservice/backend-at-scale, không bao gồm frontend support trong patch set v0.2.0.

---

## 7. Quy ước tài liệu thiết kế v0.2.0

Mỗi tài liệu command-level phải mô tả ở cấp super-detail:

1. Product goal
2. Non-goals
3. Inputs
4. Outputs
5. Artifacts
6. Data model
7. Algorithm phases
8. Deterministic vs optional model usage
9. Failure modes
10. Recovery rules
11. Idempotency
12. Observability / run artifacts
13. Backward compatibility
14. Migration strategy
15. Test strategy
16. Open questions

---

## 8. Quyết định sản phẩm chốt cho v0.2.0

1. `code build` sinh canonical FastAPI executable code.
2. `code gen` ưu tiên deterministic; LLM chỉ là fallback architecture-level, không phải đường mặc định.
3. `code apply` luôn trigger `midicoder index` ngay sau apply thành công.
4. `runtime test` là verification pipeline thật, không chỉ startup.
5. `runtime fix` không dùng LLM; thay bằng remediation loop tạo version mới.
6. `seams`/`virtual seams` bị hạ cấp thành implementation detail legacy; public model mới là automatic seam map.
7. DSL/IR phải mở rộng để phục vụ SaaS lớn và multi-service.

