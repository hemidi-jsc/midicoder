# Đóng góp cho Midicoder CE

Chúng tôi hoan nghênh các đóng góp cải thiện sự mạnh mẽ, tài liệu và khả năng của Midicoder CE – miễn là tuân thủ các ranh giới bảo vệ (guardrail) đã nêu.

## 1. Trước khi bắt đầu

1. Đọc kỹ: [ARCHITECTURE](./ARCHITECTURE.md), [GOVERNANCE](./GOVERNANCE.md), [CODE_OF_CONDUCT](./CODE_OF_CONDUCT.md).
2. Kiểm tra Issue/Discussion hiện có. Nếu thay đổi lớn, mở Discussion trước khi viết mã.
3. Hiểu phạm vi: CE tập trung vào **lập kế hoạch xác định**, không mở rộng vào runtime/điều phối/hosted.

## 2. Thiết lập môi trường

```bash
# Clone repo
cd path/to/workspace
git clone https://github.com/hemidi-jsc/midicoder.git
cd midicoder

# Python environment
python -m venv .venv
. .venv/Scripts/activate  # hoặc source .venv/bin/activate
python -m pip install --upgrade pip

# Dependencies (dev)
python -m pip install -r requirements-dev.txt  # nếu chưa tồn tại, cài trực tiếp:
python -m pip install rich ruamel.yaml tree_sitter tree_sitter_languages pytest ruff pip-audit

# Chuẩn bị cấu hình LLM (dùng cho test contract)
python -m midicoder init
# -> nhập stack, base_url, model, API key (lưu trong .midicoder/secrets/secrets.json)
```

> Nếu repo chưa có `requirements-dev.txt`, liệt kê các gói ở trên trong PR của bạn hoặc cập nhật README.

## 3. Quy trình mở Issue

1. **Chọn template phù hợp**: `bug report`, `feature request`, `docs` hoặc `discussion`. Nếu đề xuất vượt phạm vi CE (runtime, SaaS), hãy chọn `discussion` để được phân loại trước.
2. **Điền thông tin bắt buộc**: phiên bản Midicoder, lệnh đã chạy, log/runs liên quan, guardrail bị ảnh hưởng, kỳ vọng và kết quả thực tế.
3. **Đính kèm artefact**: nén thư mục `.midicoder/runs/<stage>/<timestamp>` hoặc trích xuất `summary.json` để core team có thể tái hiện.
4. **SLA phản hồi**: core maintainer sẽ gắn nhãn `triaged` trong vòng **5 ngày làm việc** với issue `bug/blocker/security`; các issue tài liệu/enhancement sẽ được phản hồi trong **≤12 ngày làm việc**. Bạn sẽ nhận auto-reply yêu cầu log/repro trong 48h – hãy bổ sung để tránh bị đóng.
5. **Khi nào dùng Discussions**: các thay đổi lớn (DSL, IR, guardrail) hoặc câu hỏi chiến lược nên được mở ở Discussions `#architecture`/`#roadmap` để tránh tràn issue tracker.

Issue giúp core team đánh giá ưu tiên; đừng tự ý mở PR lớn nếu chưa có sự đồng thuận ở bước này.

## 4. Quy trình gửi Pull Request

1. **Chuẩn bị branch**: `git checkout -b feat/<topic>` (hoặc `fix/<bug-id>`); liên kết tới issue tương ứng.
2. **Thực thi thay đổi**: viết mã, cập nhật test, tài liệu và ví dụ. Bất kỳ hành vi mới nào phải được ghi rõ trong README/ARCHITECTURE nếu ảnh hưởng người dùng.
3. **Chạy kiểm thử**: hoàn thành các lệnh trong mục *Lint, type-check, test* và ghi tóm tắt kết quả trong PR.
4. **Tự rà soát guardrail**: đảm bảo bảng “Tiêu chí đánh giá PR” dưới đây đều đạt; ghi chú nếu có ngoại lệ được core team chấp thuận.
5. **Chuẩn bị artefact**: đính kèm log `ruff`, `pytest`, `pip-audit` và các file `.midicoder/runs/.../summary.json` liên quan.
6. **Mở PR**: sử dụng template được cung cấp; điền đầy đủ mục Mục tiêu, Cách thực hiện, Guardrail, Kiểm thử.
7. **Yêu cầu review**: ping maintainer phụ trách khu vực (gắn @ trong PR); core team phản hồi nhận xét trong ≤5 ngày cho hotfix/bug/security và ≤10 ngày cho PR thông thường. Dùng label `request-second-look` nếu bạn cần reviewer khác hỗ trợ.

### Tiêu chí đánh giá PR

| Hạng mục | Câu hỏi | Trạng thái mong muốn |
| --- | --- | --- |
| Guardrail kiến trúc | Có phá vỡ contract-first, deterministic, patch-based hoặc state boundary? | Không; nếu có ngoại lệ phải có approval trước |
| Test coverage & determinism | Có unit/integration test che phủ thay đổi? có minh chứng deterministic (`runs`)? | Có test tự động + artefact cần thiết |
| Tài liệu & ví dụ | README/ARCHITECTURE/guide liên quan đã cập nhật chưa? | Đã cập nhật cùng PR |
| Ảnh hưởng backward compatibility | Có thay đổi CE/API hoặc artefact? đã ghi rõ trong CHANGELOG? | Rõ ràng và có hướng dẫn nâng cấp |

### Chấp nhận / Từ chối đóng góp

| Trạng thái | Ví dụ | Hành động |
| --- | --- | --- |
| Chấp nhận | Fix lỗi anchor, cải thiện docs, thêm test deterministic, tối ưu hiệu năng index | Merge sau khi pass CI và review |
| Cần hiệu chỉnh | PR thiếu test, chưa cập nhật docs, guardrail chưa rõ | Yêu cầu cập nhật rồi review lại |
| Từ chối | Tính năng runtime/daemon, yêu cầu SaaS, thay đổi DSL trái guardrail | Đóng PR/issue, hướng dẫn đọc README + GOVERNANCE |

#### Template PR (khuyến nghị)

```
## Mục tiêu
- …

## Cách thực hiện
- …

## Guardrail đã kiểm tra
- Contract-first: / 
- Deterministic surface: / 
- Patch-based workflow: / 
- State boundary: / 

## Kiểm thử
- python -m pytest …
- python -m ruff check .
- python -m pip-audit
```

## 5. Quy trình làm việc đề xuất

1. Tạo branch: `git checkout -b feat/<topic>`.
2. Chạy các lệnh CE cần thiết trên repo thử nghiệm để tái tạo vấn đề.
3. Ghi lại artifacts liên quan: `runs/<stage>/<timestamp>`, patch-plan, v.v.
4. Sau khi hoàn thành, cập nhật tài liệu và CHANGELOG.

## 6. Những gì chúng tôi tìm kiếm

| Nhóm | Ví dụ |
| --- | --- |
| Sửa lỗi | patch engine không tìm anchor, validator báo sai dòng |
| Cải thiện tài liệu | thêm ví dụ contract, hướng dẫn apply patch |
| Kiểm thử | integration test mới cho `code gen`, regression case |
| Plugin/extension | tận dụng API plugin chính thức (nếu đã công bố) |
| Phân tích kỹ thuật | profiling, đo thời gian IR build |

## 7. Ngoài phạm vi (PR sẽ bị đóng)

- Thêm runtime/daemon/agent.
- Điều phối workflow, cron, job runner.
- Thay đổi ngữ nghĩa DSL/IR mà chưa thảo luận.
- Điều phối AI tự trị, auto-apply patch không có sự can thiệp của con người.
- Tính năng SaaS/hosted, RBAC doanh nghiệp, multi-tenant.
- Cộng tác thời gian thực, editor trực quan.

## 8. Guardrail kiến trúc

1. **Contract-first** – mọi logic mới phải bắt nguồn từ hợp đồng.
2. **Deterministic compilation** – không đưa LLM vào pipeline deterministic.
3. **Patch-based workflow** – không ghi trực tiếp vào repo làm việc; mọi thay đổi qua patch-plan.
4. **State scope** – chỉ ghi vào `.midicoder/`; không tạo thư mục ẩn khác.
5. **Planning vs Execution** – CE chỉ cung cấp `midicoder code apply` khi người vận hành chủ động chạy kèm guardrail. Không nhận PR thêm daemon/agent tự động ghi vào repo.

## 9. Lint, type-check, test

```bash
# Lint & format
python -m ruff check .
python -m ruff format --check .  # hoặc black nếu dự án áp dụng

# Unit + integration
python -m pytest tests/unit
python -m pytest tests/integration -k contract

# Kiểm tra bảo mật phụ thuộc
python -m pip-audit
```

> Một số integration test cần endpoint LLM hoạt động. `tests/README.md` mô tả cách skip tự động nếu thiếu config.

## 10. Phong cách mã nguồn (Python)

- **Type hints** đầy đủ, ưu tiên `from __future__ import annotations`.
- **Đặt tên**: module snake_case, class PascalCase, constant UPPER_SNAKE_CASE.
- **Logging**: dùng `midicoder.io.messages` hoặc logging chuẩn thay vì `print`.
- **Docstring**: mô tả "tại sao" và điều kiện biên.
- **Ví dụ**:

```python
from dataclasses import dataclass
from typing import Iterable

@dataclass(slots=True)
class PlanSummary:
    target: str
    anchors: list[str]

    def missing_anchor(self) -> bool:
        return not self.anchors

def summarize_plans(plans: Iterable[dict]) -> list[PlanSummary]:
    summaries: list[PlanSummary] = []
    for plan in plans:
        summaries.append(
            PlanSummary(
                target=plan["target"],
                anchors=[a["name"] for a in plan.get("anchors", [])],
            )
        )
    return summaries
```

## 11. Checklist PR

- Đã mở issue/discussion và nhận triage (bắt buộc với thay đổi lớn).
- Đã cập nhật/kiểm tra `requirements*.txt` hoặc hướng dẫn cài đặt nếu thêm phụ thuộc.
- Đã chạy `python -m ruff check .`, `python -m pytest ...`, `python -m pip-audit` (ghi rõ kết quả trong PR).
- Đã cập nhật tài liệu liên quan (README, ARCHITECTURE, guides) và link tới commit.
- Đã cập nhật [CHANGELOG](./CHANGELOG.md) (mục \"Unreleased\").
- Đã đính kèm artefact cần thiết (`runs/.../summary.json`, log test, ảnh chụp kết quả).
- Đã tự đánh giá theo bảng \"Tiêu chí đánh giá PR\" (mục 4) và ghi chú trạng thái.
- Đã xác nhận guardrail (contract-first, deterministic, patch-based, state boundary) và sử dụng template PR.

## 12. Liên hệ & hỗ trợ

- Thắc mắc quy trình: GitHub Discussions `#contributing`.
- Báo cáo bảo mật: contact@midicoder.com (đừng mở issue công khai).
- Hỗ trợ ứng xử: contact@midicoder.com.

Cảm ơn bạn đã giúp Midicoder CE trở nên đáng tin cậy hơn!