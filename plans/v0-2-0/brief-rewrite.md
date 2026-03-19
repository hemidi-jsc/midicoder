# Thiết kế command `midicoder brief rewrite` - v0.2.0

## 1. Mục tiêu tài liệu

Tài liệu này có hai phần rõ ràng:

1. **Phân tích chính xác code hiện tại** của `midicoder brief rewrite`.
2. **Đề xuất thiết kế v0.2.0** dựa trên những gì code đang làm tốt/chưa tốt.

Mục tiêu là tránh đoán mò và dùng lại đúng các quyết định/ưu nhược điểm hiện có làm nền cho redesign.

---

## 2. Hiện trạng code hiện có

## 2.1 Entry point CLI hiện tại

`midicoder brief rewrite` được triển khai tại `midicoder/commands/brief.py::rewrite()`.

Luồng hiện tại:

1. setup paths + current version
2. đọc `.midicoder/versions/<version>/master-brief.md`
3. load `llm.high`
4. tạo run dir `brief_rewrite`
5. gọi `midicoder.brief.rewriter.rewrite_master_brief(...)`
6. ghi kết quả ra:
   - `master-brief.updated.md`
   - `master-brief.analysis.md`
   - `master-brief.errors.txt` nếu có lỗi khi apply block
7. ghi run outputs vào `.midicoder/runs/brief_rewrite/...`

=> Điểm quan trọng: command hiện tại **không ghi đè** `master-brief.md`; nó tạo file `master-brief.updated.md` để user review rồi thay thế thủ công nếu muốn. Đây là một đặc điểm tốt cần giữ lại. Nó cũng luôn yêu cầu đã có `current_version` và `master-brief.md` trước khi chạy.

## 2.2 Thuật toán thật sự trong `rewrite_master_brief()`

Phần lõi nằm ở `midicoder/brief/rewriter.py::rewrite_master_brief()`.

### Bước A - Build keyword map có cache

Hàm này gọi `get_keyword_map_cached(...)` từ `midicoder.brief.analyzer`.

Ý nghĩa:

- brief hiện tại được hash bằng SHA-256
- cache keyword map lưu tại `versions/<version>/cache/brief_keywords.json`
- nếu hash brief không đổi thì tái sử dụng cache
- nếu brief đổi hoặc cache miss thì gọi LLM để trích xuất:
  - domain terms
  - entities
  - commands
  - events
  - apis
  - integrations
  - access_control
  - persistence
  - scenarios
  - synonyms
  - contract_files

=> Đây là một optimization thật trong code hiện tại, không phải ý tưởng giả định.

### Bước B - Tải context artifacts từ `.midicoder/context`

`rewrite_master_brief()` load:

- `symbols.json`
- `virtual_seams.json`
- nếu không có thì fallback sang `seams.json`
- nếu vẫn không đủ thì dùng `exemplars.json`

Luồng ưu tiên hiện tại là:

1. virtual seams
2. real seams
3. symbols + exemplars

Nói cách khác, brief rewrite hiện tại **phụ thuộc khá mạnh vào hệ thống index/context** để hiểu codebase, chứ không chỉ nhìn vào brief gốc.

### Bước C - Multi-pass LLM rewrite

Code hiện tại chạy 3 pass thật sự:

#### Pass 1 - Summarize snippets

- build prompt để tóm tắt các snippet code liên quan
- LLM trả về JSON summaries

#### Pass 2 - Aggregate module narratives

- dùng context summaries từ pass 1
- LLM gom thành các "module narratives"

#### Pass 3 - Rewrite brief

- build system prompt riêng cho rewrite
- đưa `original_content` + `module_narratives`
- LLM trả về các block search/replace
- code parse block đó và apply lên brief gốc

### Bước D - Apply search/replace blocks thay vì để model trả full file

Đây là một điểm rất đáng chú ý trong implementation hiện tại:

- model **không trả thẳng file brief hoàn chỉnh** như output chuẩn duy nhất
- model trả về các block search/replace
- code apply block lên `original_content`
- nếu block nào không match thì ghi lỗi, nhưng vẫn có thể áp các block khác

=> Đây là một thiết kế khá tốt về mặt an toàn vì giảm nguy cơ model rewrite toàn bộ file một cách mất kiểm soát.

## 2.3 Output artifacts hiện tại

Ngoài file updated brief, command đang lưu khá nhiều artifact hữu ích:

- original brief
- llm_config
- prompt pass 1/2/3
- raw response pass 1/2/3
- context summaries
- module narratives
- final llm response
- error.txt nếu fail

=> Mức observability hiện tại tương đối tốt.

---

## 3. Ưu điểm của implementation hiện tại

1. **Không ghi đè brief gốc** ngay lập tức.
2. **Có cache keyword map**, tránh lặp LLM call không cần thiết.
3. **Biết tận dụng context của repo** thông qua symbols/seams/exemplars.
4. **Multi-pass architecture** hợp lý hơn single prompt rewrite.
5. **Search/replace apply** an toàn hơn việc model trả full file rồi tin tuyệt đối.
6. **Run logs chi tiết**, dễ debug.

---

## 4. Nhược điểm của implementation hiện tại

1. Brief rewrite hiện vẫn bị buộc vào mô hình `virtual_seams`/`seams`, trong khi đây không phải mental model tự nhiên của end-user.
2. Context retrieval hiện chưa dựa trên một artifact thống nhất kiểu project graph / automatic seam map.
3. Output vẫn thiên về “improve master-brief.md” hơn là sinh ra một **canonical rewritten brief artifact** có schema ổn định.
4. Cơ chế search/replace có thể fail từng block nếu brief đã drift so với text mà model nhìn thấy.
5. Chưa có remediation mode tách bạch giữa:
   - rewritten brief chuẩn
   - remediation brief từ verification/runtime issues.

---

## 5. Thiết kế v0.2.0

## 5.1 Mục tiêu mới

`midicoder brief rewrite` ở v0.2.0 vẫn giữ tinh thần hiện tại, nhưng nâng thành pha:

- chuẩn hóa brief đầu vào
- tạo canonical rewritten brief
- hỗ trợ remediation brief
- gắn trace rõ giữa source brief và rewritten brief

## 5.2 Những gì **giữ lại** từ code hiện tại

1. Không ghi đè `master-brief.md` trực tiếp.
2. Giữ keyword cache theo hash brief.
3. Giữ multi-pass structure.
4. Giữ prompt/response/run artifacts chi tiết.
5. Giữ cơ chế apply patch-like changes thay vì blind full overwrite, nếu output mode là text patch.

## 5.3 Những gì cần thay đổi

### A. Đổi nền retrieval từ seam/virtual seam sang project context graph

Thay vì:

- `virtual_seams.json`
- `seams.json`
- exemplars fallback

v0.2.0 dùng:

- `automatic_seams.json`
- `symbols.json`
- `ownership.json`
- `module_graph.json`
- `entrypoints.json`
- `exemplars.json`

### B. Bổ sung rewritten brief schema

Ngoài Markdown, command phải sinh JSON chuẩn hóa, ví dụ:

- functional requirements
- non-functional requirements
- domain glossary
- actors
- entities
- workflows
- integrations
- constraints
- open questions

### C. Tách remediation mode

Khi downstream phát hiện lỗi contract/runtime, command phải có mode sinh `remediation brief` mới thay vì sửa đè rewritten brief cũ.

### D. Tăng tính ổn định của apply model

Tiếp tục ưu tiên patch-style application, nhưng nên hỗ trợ thêm structured edits ở mức section thay vì chỉ search/replace text thuần.

---

## 6. Thuật toán v0.2.0 đề xuất

### Phase 1 - Load canonical inputs

- source brief
- previous rewritten brief nếu có
- remediation signals nếu có
- project context graph

### Phase 2 - Keyword and concept extraction

Giữ cache-based extraction như hiện tại.

### Phase 3 - Context summarization

Giữ multi-pass tư duy hiện tại nhưng retrieval source mới là project context graph.

### Phase 4 - Rewrite planning

Model sinh ra một structured rewrite plan:

- section ops
- additions
- replacements
- open questions

### Phase 5 - Materialize outputs

- `master-brief.updated.md`
- rewritten brief JSON
- analysis artifacts
- remediation brief nếu applicable

---

## 7. Kết luận thiết kế

Đây là command **được phép dùng LLM** ở v0.2.0. Tuy nhiên redesign phải bám sát 3 đặc tính tốt đã có trong code hiện tại:

1. multi-pass context-aware rewrite
2. keyword cache
3. không ghi đè brief gốc trực tiếp

