# Hoàn thiện WebGUI Brief Editor — Task list đầy đủ

## Bối cảnh

Session trước đã fix 3 bug persistence (commits `33b6aa9` + `1a696fd`). Còn nhiều vấn đề UX và chức năng chưa hoàn thiện.

**File chính:**
- Backend: `api/app/routers/brief.py`, `api/app/routers/clarification.py`, `api/app/routers/pipeline.py`
- Frontend: `webgui/src/app/pages/brief-editor/brief-editor.component.ts` (inline template)
- Storage: `midicoder/storage/sqlite.py` (BriefsManager, ArtifactsManager)
- Pipeline: `webgui/src/app/core/pipeline.store.ts`

**Quy tắc:**
1. Status chỉ 4 giá trị: `draft → clarified → frozen → archived`
2. Dùng `_get_project_db_path()` cho explicit DB paths (KHÔNG dùng relative)
3. Metadata SQLite là JSON string → phải `json.loads()`
4. 1 version = 1 brief
5. Không keep backward compatibility

---

## TASK 1: Fix status brief không update sau analyze

**Vấn đề:** `/brief/analyze` không gọi `update_status()` — status luôn là `draft` dù đã phân tích thành công với confidence 0.95.

**Yêu cầu:**
- Trong `api/app/routers/brief.py` endpoint `/analyze`: sau khi lưu artifact, update status:
  - Nếu `confidence >= 0.8` VÀ không có ambiguities → `mgr.update_status(brief_id, "clarified")`
  - Nếu có ambiguities hoặc `confidence < 0.8` → giữ `draft`
  - Log lineage cho mỗi lần chuyển status
- Reload page → status badge phải hiển thị đúng từ SQLite

**Code hiện tại (brief.py line ~145):** `_upsert_brief()` chỉ update content, không đổi status.

---

## TASK 2: Fix pipeline sidebar step "Brief" không chuyển sang ✓

**Vấn đề:** `GET /pipeline/status` dùng `_get_pipeline_progress_from_sqlite()` để detect artifact. Function này check:
```python
if aid.startswith("brief_"):
    progress["brief"] = {"status": status}
```

Nhưng analysis artifact ID là `analysis-brief-f6c7eb86` — starts with `analysis-` không phải `brief_`. → Pipeline step "Brief" luôn `pending`.

**Fix:** Trong `api/app/routers/pipeline.py` function `_get_pipeline_progress_from_sqlite()`:
```python
elif aid.startswith("analysis-brief"):
    progress["brief"] = {"status": "generated"}  # triggers "complete" in frontend
```

---

## TASK 3: Implement Clarification WebGUI (full feature)

**Backend đã có:**
- `POST /clarification/start` — start session, LLM generate câu hỏi đầu tiên
- `POST /clarification/answers` — submit answer, LLM generate câu hỏi tiếp theo
- `GET /clarification/status/{session_id}` — check status

**Bug cần fix trước:** `api/app/routers/clarification.py` dùng `BriefsManager()` và `ArtifactsManager()` KHÔNG truyền `db_path` → sai DB file. Fix giống brief.py:
```python
def _get_project_db_path(db_name: str) -> Path:
    from app.config import get_project_cwd
    project_cwd = Path(get_project_cwd())
    return project_cwd / ".midicoder" / "data" / db_name

# Replace tất cả BriefsManager() → BriefsManager(db_path=_get_project_db_path("briefs.db"))
# Replace tất cả ArtifactsManager() → ArtifactsManager(db_path=_get_project_db_path("artifacts.db"))
```

**Frontend cần tạo:** Component clarification UI trong brief-editor (inline modal hoặc section mở rộng):

1. **Trigger:** Nút "Làm rõ yêu cầu →" hiện khi `analysisResult.status === 'needs_clarification'`
2. **Flow:**
   - Click nút → gọi `POST /clarification/start` → nhận câu hỏi đầu tiên
   - Hiển thị câu hỏi + text input để user trả lời
   - User submit → gọi `POST /clarification/answers` → nhận câu hỏi tiếp theo
   - Lặp cho đến khi LLM nói done → tự động chuyển brief sang `clarified` (status = clarified, type = master)
3. **UI layout:**
   - Timeline của Q&A đã hoàn thành (tương tự clarification history nhưng là active session)
   - Input box cho câu trả lời hiện tại
   - Round counter (e.g., "Round 3/10")
   - Loading spinner khi chờ LLM

**API Service methods cần thêm trong `api.service.ts`:**
```typescript
startClarification(version: string): Promise<ApiResponse<{clarification_id, questions}>>
submitAnswers(session_id: string, answers: Array<{question_id, values, notes}>): Promise<ApiResponse<{status, questions}>>
getClarificationStatus(session_id: string): Promise<ApiResponse<{status}>>
```

---

## TASK 4: Hiển thị full raw analysis content

**Vấn đề hiện tại:** Template chỉ hiển thị summary, domain/type/scale, confidence, và resource counts. Không hiện chi tiết **entities, commands, queries, events, ui_components** từ artifact content.

**Yêu cầu:** Thêm collapsible sections trong "📊 Kết quả phân tích":

1. **📋 Entities** — list table: name, type, description
2. **⚡ Commands** — list table: name, target, description
3. **🔍 Queries** — list table: name, entity, filter
4. **🔔 Events** — list table: name, source, description
5. **🎨 UI Components** — list table: name, type, description

**Data source:** Artifact content JSON đã được lưu đầy đủ. Backend `/brief/get` hiện tại chỉ trả về `intent`, `ambiguities`, `summary`. Cần expand để trả về toàn bộ `entities`, `commands`, `queries`, `events`, `ui_components` từ artifact content.

**Fix backend `/brief/get`:**
```python
analysis_data = {
    "status": ...,
    "analysis": {
        "intent": intent,
        "ambiguities": content.get("ambiguities", []),
        "summary": content.get("summary", ""),
        "entities": content.get("entities", []),       # ADD
        "commands": content.get("commands", []),       # ADD
        "queries": content.get("queries", []),         # ADD
        "events": content.get("events", []),           # ADD
        "ui_components": content.get("ui_components", []),  # ADD
    },
    "metadata": normalized_metadata,
}
```

**Frontend template:** Thêm collapsible accordion sections dưới "Resources extracted":
```html
@for (entity of analysisResult?.analysis?.entities; track entity.name) {
  <div class="entity-card">...</div>
}
```

---

## TASK 5: Lịch sử thay đổi (lineage) hiển thị chi tiết thay vì chỉ mốc thời gian

**Vấn đề hiện tại:** Lineage chỉ hiển thị `created_at`, `change_type`, `change_description`. Không hiện nội dung thay đổi thực tế.

**Yêu cầu:** Mỗi entry trong lineage timeline hiển thị:
1. **Timestamp** — định dạng đẹp (e.g., "2 giờ trước" thay vì ISO datetime)
2. **Change type badge** — created, content_update, status_change, frozen
3. **Change description** — chi tiết mô tả
4. **Diff preview** (nếu là content_update) — hiện diff ngắn: dòng bị xóa/dòng thêm mới
5. **Collapsible detail** — click để xem full content trước/sau

**Để làm được diff preview:** Cần lưu content hash + content snapshot trong `brief_lineage` table. Hiện tại table chỉ có:
```sql
CREATE TABLE brief_lineage (
    id INTEGER PRIMARY KEY,
    brief_id TEXT,
    parent_brief_id TEXT,
    version TEXT,
    change_type TEXT,
    change_description TEXT,
    created_at TIMESTAMP
)
```

**2 lựa chọn:**
- **Option A (nhanh):** Thêm column `old_content_hash`, `new_content_hash` vào lineage table. Diff preview chỉ hiện hash thay đổi (không show full diff).
- **Option B (đầy đủ):** Thêm `old_content`, `new_content` TEXT vào lineage. Lưu snapshot content tại thời điểm change.

→ **Chọn Option A** (nhanh, nhẹ). Hiển thị: "Content đã thay đổi: `3a3df2...` → `1db98f...`"

**Fix trong `brief.py` function `_log_lineage()`:** Thêm parameter `old_hash`, `new_hash`.

---

## TASK 6: Freeze button + flow

**Hiện tại:** Button "🔒 Đóng (Freeze)" đã có trong template, backend `/brief/freeze` đã có.

**Kiểm tra:**
- Freeze chỉ enabled khi `status === 'clarified'` ✓
- Sau freeze, textarea disabled, buttons disabled ✓
- Freeze log vào lineage ✓

**Cần fix:** Sau khi freeze, pipeline step "Brief" phải chuyển sang ✓. → Tương tự Task 2, nhưng check status từ briefs table.

---

## Thứ tự thực hiện

1. **Task 1** — Fix status update (backend, 5 phút)
2. **Task 2** — Fix pipeline detection (backend, 5 phút)
3. **Task 6** — Test freeze flow (test, 3 phút)
4. **Task 5** — Lineage detail (backend + frontend, 15 phút)
5. **Task 4** — Raw analysis content display (backend + frontend, 20 phút)
6. **Task 3** — Clarification WebGUI (backend fix + frontend new component, 40 phút)

Mỗi task phải commit riêng với message mô tả rõ ràng.

---

## Test E2E (sau khi hoàn tất)

1. Mở brief editor → viết content → click "Phân tích"
2. Verify: status chuyển `draft` → `clarified` (nếu confidence ≥ 0.8)
3. Verify: pipeline sidebar step "Brief" chuyển ✓
4. Reload page → verify: status + analysis restore từ SQLite
5. Click "📊 Kết quả phân tích" → mở collapsible → xem entities, commands, queries
6. Nếu confidence < 0.8 → click "Làm rõ yêu cầu" → clarification flow hoạt động
7. Click "📋 Lịch sử" → xem lineage với hash preview
8. Click "🔒 Đóng (Freeze)" → brief frozen, textarea disabled
