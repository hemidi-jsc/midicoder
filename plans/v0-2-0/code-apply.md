# Thiết kế command `midicoder code apply` - v0.2.0

## 1. Mục tiêu sản phẩm

`midicoder code apply` là command thực thi patch plan lên workdir thật.

Ở v0.2.0, command này phải là **executor thuần túy**, không chịu trách nhiệm:

- suy luận business logic
- sáng tác patch
- tự chọn lại target path

Nó chỉ:

1. load patch plan
2. validate patch ops
3. apply tuần tự
4. ghi file
5. rollback nếu lỗi
6. **tự chạy lại `midicoder index` sau apply thành công**

---

## 2. Product contract chốt

### 2.1 Reindex bắt buộc

Ngay sau apply thành công, Midicoder **phải trigger `midicoder index`**.

Không chỉ là internal reindex helper, mà là product guarantee chính thức.

### 2.2 Tại sao không chỉ incremental helper

Vì downstream semantics cần nói rõ:

- context của repo sau apply đã được đồng bộ lại
- automatic seam map mới đã được rebuild
- symbol graph mới đã có hiệu lực

Nội bộ có thể optimize bằng changed-path indexing, nhưng command contract là “run index”.

---

## 3. Inputs

1. `patches/index.json`
2. patch-plan files
3. working_dir
4. apply flags
5. current context manifest (optional for safety)

---

## 4. Outputs

1. updated workdir files
2. backups
3. apply report
4. post-apply index artifacts mới
5. apply + reindex summary

---

## 5. Primitive operation support

`code apply` phải hỗ trợ primitive ops từ `code gen`:

- create_file
- replace_file
- replace_symbol
- replace_region
- insert_before_anchor
- insert_after_anchor
- append_symbol
- insert_import
- delete_symbol
- update_exports

### Legacy support

- `upsert_region` được support trong giai đoạn chuyển tiếp

---

## 6. Thuật toán cấp cao

### Phase 1 - Load and validate apply queue

1. Load patch index.
2. Expand queue theo execution order.
3. Validate schema của mỗi op.
4. Group ops theo file.

### Phase 2 - Preflight safety checks

1. target file exists/creatable
2. ownership compatible
3. anchor exists nếu op yêu cầu
4. before-hash check nếu có
5. shared-file policy check

### Phase 3 - Backup

Tạo backup per file trước khi ghi.

### Phase 4 - Apply ops per file

- parse file nếu cần AST-aware op
- apply ops theo thứ tự đã khai báo
- validate syntax nếu language adapter có hỗ trợ

### Phase 5 - Commit file writes

- write atomic nếu có thể
- track changed paths

### Phase 6 - Post-apply verification nhẹ

1. syntax parse
2. import cycle smoke (optional fast path)
3. changed file summary

### Phase 7 - Trigger reindex bắt buộc

Gọi lại `midicoder index`.

- Same command semantics
- Có thể truyền changed paths để optimizer dùng internally
- Nhưng run artifact phải ghi rõ “index rerun completed/failed”

### Phase 8 - Emit reports

- apply report
- reindex report
- final status

---

## 7. Nếu reindex fail thì sao?

### Chính sách v0.2.0

Apply được coi là **chưa hoàn tất đầy đủ** nếu reindex fail.

Status có thể là:

- `applied_and_indexed`
- `applied_but_reindex_failed`
- `failed_and_rolled_back`

Mặc định CLI phải coi `applied_but_reindex_failed` là warning-level nghiêm trọng hoặc exit non-zero tùy policy cấu hình.

---

## 8. Idempotency

`code apply` phải gần-idempotent nếu patch plan không đổi và file targets không đổi.

Cụ thể:

- apply lần hai không được duplicate imports/symbols
- ops phải có no-op detection

---

## 9. Failure modes

1. Patch queue invalid
2. Anchor missing
3. Ownership violation
4. Syntax broken sau apply
5. Reindex fail

---

## 10. Observability

Báo cáo cần có:

- changed files
- noop files
- failed files
- backups
- post-apply syntax issues
- reindex start/end/result

---

## 11. Test strategy

1. Primitive op executor tests
2. Rollback tests
3. No-op idempotency tests
4. Apply + reindex integration tests
5. Legacy `upsert_region` compatibility tests

---

## 12. Open questions

1. Có nên hard-fail khi reindex fail không?
2. Có nên cho phép `--no-index` chỉ trong debug mode không?
3. Có nên hỗ trợ apply transaction theo batch file groups không?

