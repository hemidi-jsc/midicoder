# Thiết kế command `midicoder index` - v0.2.0

## 1. Mục tiêu tài liệu

Tài liệu này phân tích đúng command `midicoder index` đang hoạt động như thế nào trong code hiện tại, sau đó mới mô tả redesign v0.2.0.

---

## 2. Hiện trạng code hiện có

## 2.1 Entry points hiện tại

`midicoder/commands/index.py` có 2 hàm public:

- `run(root)`
- `reindex(root, changed_paths=None)`

Cả hai đều:

1. resolve `working_dir` từ config
2. đảm bảo `.midicoder` base layout
3. tạo `run_dir`
4. gọi `build_context(...)`

Khác nhau ở chỗ:

- `run()` gọi `build_context(..., refresh=False)`
- `reindex()` gọi `build_context(..., refresh=True, reindex_only_changed=True, changed_paths=...)`

=> Nghĩa là product hiện tại đã có split rõ giữa full index và incremental reindex.

## 2.2 `build_context()` hiện thật sự làm gì

Hàm lõi nằm ở `midicoder/context/indexer.py::build_context()`.

Các pha chính hiện tại:

### Phase A - Scan repository

- load `.gitignore`
- tạo `ProjectScanner`
- scan toàn bộ hoặc scan selected files
- maintain `FileCache`

### Phase B - Full index hoặc incremental reindex

#### Nếu `reindex_only_changed=True`

- bắt buộc phải có existing context
- ưu tiên `changed_paths` do caller truyền vào
- nếu không có manual paths thì dùng git delta dựa trên `manifest.repo_hash`
- merge lại với context cũ

#### Nếu full index

- scan toàn bộ
- diff với previous files để biết changed/deleted

### Phase C - Detect stack và profile

- đọc stack từ config nếu có
- detect stack từ scanner
- extract project profile

### Phase D - Extract project artifacts

Hiện tại indexer extract:

- symbols
- entrypoints
- seams
- exemplars

### Phase E - Merge artifacts trong refresh/reindex

Khi refresh/reindex, code merge lại:

- symbols
- entrypoints
- seams
- exemplars

với context cũ.

### Phase F - Build manifest

- nếu incremental: `build_incremental_manifest(...)`
- nếu full: `build_index_manifest(...)`

### Phase G - Write artifacts

`write_context_artifacts(...)` ghi:

- manifest.json
- profile.json
- symbols.json
- entrypoints.json
- seams.json
- exemplars.json

Sau đó nó gọi `write_virtual_seams(...)` để sinh `virtual_seams.json`.

=> Điểm rất quan trọng: **virtual seams hiện được build sau khi đã có seams, symbols, entrypoints, exemplars**. Nó không phải artifact độc lập ngay từ đầu.

---

## 3. Seam và virtual seam hiện đang nghĩa là gì trong code

## 3.1 Real seams

`midicoder/context/extractors/seams.py` chỉ extract marker-based seams từ text:

- `midicoder:begin <group_id>`
- `midicoder:end <group_id>`

Nó pair begin/end markers và tạo seam entries với:

- kind begin/end
- file
- line
- detail
- group_id
- paired

=> Tức là **seam thật trong code hiện tại đúng nghĩa là marker-based anchors**.

## 3.2 Virtual seams

`midicoder/context/virtual_seams/pipeline.py` load và hợp nhất nhiều nguồn:

- real seams
- exemplar-derived virtual seams
- symbol-derived virtual seams
- entrypoint-derived virtual seams

Sau đó:

1. dedupe theo `(file, group_id)`
2. dedupe tiếp theo `(file, line)` với priority rules
3. merge real seams và virtual seams, real override by `group_id`

=> Nói cách khác, virtual seam hiện tại là **candidate seam suy luận từ code intelligence**, còn real seam là marker do con người/công cụ đã cắm vào file.

---

## 4. Ưu điểm của implementation hiện tại

1. Có hỗ trợ **incremental reindex** thật.
2. Đã có notion tách real anchors và inferred anchors.
3. Dễ debug vì artifacts ghi riêng từng loại.
4. Có git-delta optimization cho reindex.
5. Pipeline index khá modular: scanner/detector/extractor/virtual seam pipeline.

---

## 5. Nhược điểm của implementation hiện tại

1. Ở góc nhìn sản phẩm, seam là khái niệm gây nhiễu vì end-user không hề tạo seam.
2. Planner/generator downstream phải biết branch logic `seams` vs `virtual_seams`.
3. Output context còn thiếu một artifact hợp nhất kiểu project graph / ownership graph / automatic seam map.
4. Chưa có public artifact mô tả insertion strategies, ownership, confidence theo mô hình thống nhất.
5. `code apply` hiện gọi reindex helper theo changed paths, nhưng product contract vẫn chưa được phát biểu rõ là “chạy lại midicoder index”.

---

## 6. Thiết kế v0.2.0

## 6.1 Quyết định sản phẩm

Ở cấp sản phẩm, bỏ cách nói:

- seam
- virtual seam

Thay bằng:

- **automatic seam map**

Tuy nhiên ở cấp implementation nội bộ, v0.2.0 vẫn có thể giữ real seam marker và inferred seam pipeline như **nguồn tín hiệu** cho automatic seam map.

=> Tức là: **không nhất thiết xóa sạch implementation cũ ngay**, nhưng phải xóa nó khỏi product model public-facing.

## 6.2 Automatic seam map mới

Artifact hợp nhất cần chứa:

- file
- symbol
- span / line_start / line_end
- role
- insertion_strategy
- ownership
- confidence
- evidence

Nó sẽ được build từ:

- symbols
- entrypoints
- exemplars
- real marker seams
- inferred virtual seams legacy
- imports/module graph

## 6.3 Full index / reindex semantics mới

- `midicoder index`: full product contract
- internal engine có thể dùng incremental optimization
- sau `code apply`, system luôn phải trigger semantic equivalent của `midicoder index`

---

## 7. Kết luận thiết kế

Phân tích code hiện tại cho thấy điều bạn nêu là đúng:

- end-user không hề đặt seam
- seam/virtual seam chỉ là implementation detail nội bộ
- vì vậy docs và product model mới phải chuyển sang `automatic seam map`

Nhưng cũng cần ghi nhận đúng rằng code hiện tại **đã có một pipeline suy luận anchors tự động thật**, chỉ là tên gọi/artifact model của nó chưa hợp lý ở cấp sản phẩm.

