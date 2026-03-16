# Quản trị Midicoder CE

Midicoder CE áp dụng mô hình **nhóm cốt lõi kiểm soát** để đảm bảo tính xác định, sự phù hợp chiến lược và ranh giới rõ ràng giữa CE và phiên bản thương mại.

## 1. Nguyên tắc

- **Tính xác định > Phổ biến** – quyết định kiến trúc không dựa trên bỏ phiếu.
- **Guardrail bất biến** – contract-first, deterministic, patch-based, state boundary.
- **Niềm tin doanh nghiệp** – lộ trình ưu tiên khả năng kiểm chứng, audit.
- **CE phục vụ đánh giá** – không cố gắng tương đương tính năng với bản thương mại.

## 2. Vai trò & trách nhiệm

| Vai trò | Quyền | Trách nhiệm |
| --- | --- | --- |
| Nhóm cốt lõi | Quyết định kiến trúc, roadmap, release | Duy trì guardrail, cập nhật tài liệu, phản hồi báo cáo |
| Contributor | Gửi PR, issue, thảo luận | Tuân thủ guardrail, checklist PR, CODE_OF_CONDUCT |
| Cộng đồng | Feedback kỹ thuật, viết blog, tổ chức meetup | Hành xử thiện chí, báo cáo vi phạm |

Cộng đồng **không** có quyền phủ quyết roadmap, ép merge PR hay yêu cầu SLA phản hồi.

## 3. Quyền tác giả & cấp phép

- **Chủ sở hữu mã nguồn hiện hữu**: Hemidi JSC (đơn vị phát triển Midicoder) giữ quyền tác giả đối với toàn bộ mã và tài liệu CE đã công bố trước đó.
- **Đóng góp mới**: contributor vẫn giữ bản quyền phần code/tài liệu của mình nhưng đồng ý cấp phép lại theo Apache License 2.0 khi PR được merge (không có CLA riêng).
- **Quyền sử dụng thương mại**: Hemidi JSC có thể đưa đóng góp CE vào bản thương mại, giữ nguyên attribution và guardrail.
- **Ghi nhận**: thay đổi quan trọng sẽ được nêu trong [CHANGELOG](./CHANGELOG.md) hoặc ghi chú release. Core team có thể gỡ attribution nếu phát hiện vi phạm CODE_OF_CONDUCT hoặc đóng góp bị revert vì lý do bảo mật/pháp lý.

## 4. Nghĩa vụ pháp lý

| Chủ đề | Chính sách | Ghi chú |
| --- | --- | --- |
| Giấy phép | Apache License 2.0 ([LICENSE](../../LICENSE)) | Áp dụng cho mã nguồn, tài liệu, artefact được phát hành |
| Quyền sử dụng đóng góp | Cho phép Hemidi JSC dùng trong CE và sản phẩm thương mại | Contributor được ghi nhận nhưng không có quyền chia sẻ doanh thu |
| Giới hạn trách nhiệm | CE phân phối \"as-is\" không có SLA | Người dùng tự chịu trách nhiệm khi dùng output trong môi trường sản xuất |
| Bảo mật dữ liệu LLM | Người dùng phải tuân thủ chính sách nội bộ khi gửi context lên nhà cung cấp | CE chỉ đọc API key từ `.midicoder/secrets` và không thu thập telemetry |
## 5. Chu kỳ phát hành & tài liệu

| Hoạt động | Tần suất | Chủ sở hữu |
| --- | --- | --- |
| Release CE minor | ~mỗi quý (ví dụ: v0.1 Q2 2026, v0.2 Q3 2026) | Nhóm cốt lõi |
| Cập nhật README/ARCHITECTURE | Ngay khi thay đổi hành vi lệnh | Chủ sở hữu lệnh (command owner) |
| ROADMAP refresh | Sau mỗi release | PM sản phẩm |
| CHANGELOG | Với mỗi merge có ảnh hưởng user | Tác giả PR |
| Kiểm tra liên kết/tài liệu | Hàng tháng bằng `lychee`, `markdownlint` | Tech Writer |

Bất kỳ thay đổi tài liệu công khai nào cần ít nhất một thành viên core review trước khi merge.

## 6. Quy trình đề xuất

1. **Ý tưởng nhỏ (docs, bug fix)**: mở Issue hoặc PR trực tiếp, tuân thủ checklist.
2. **Thay đổi lớn (DSL, IR, giao diện lệnh)**: mở Discussion theo template (vấn đề, giải pháp đề xuất, guardrail, non-goal). Chờ xác nhận trước khi viết mã.
3. **Sửa policy/Governance**: gửi PR chỉnh tài liệu + mở Discussion `#governance`.

## 7. Đánh giá đề xuất tính năng từ cộng đồng

1. **Nộp đề xuất**: dùng template Discussions `#roadmap` hoặc Issue `feature request`, mô tả vấn đề, giá trị doanh nghiệp và guardrail liên quan.
2. **Triage bởi PM sản phẩm (≤14 ngày)**: phân loại `CE`, `Commercial-only` hoặc `Out-of-scope`. Kết quả và lý do sẽ được ghi trực tiếp trong issue/discussion.
3. **Đánh giá**: core team cân nhắc 3 tiêu chí – (a) phù hợp guardrail và chiến lược xác định, (b) tác động tới doanh thu/sản phẩm thương mại, (c) chi phí bảo trì dài hạn.
4. **Quyết định**:
   - Nếu thuộc CE và có nguồn lực: thêm vào [ROADMAP](./ROADMAP.md) hoặc backlog công khai.
   - Nếu chỉ phù hợp bản thương mại: gắn nhãn `commercial-track` và mô tả cách người dùng có thể đăng ký tham gia chương trình khách hàng.
   - Nếu bị từ chối: giải thích lý do và trỏ tới mục *Giới hạn & Phạm vi CE* trong README.
5. **Phản hồi**: cộng đồng không thể yêu cầu roadmap thương mại hay ép buộc SLA; escalations phải theo mục *Escalation & phản hồi*.

Mỗi đề xuất sau khi kết thúc sẽ có liên kết chéo tới issue/ROADMAP để bảo đảm minh bạch.

## 8. Mối liên kết với tài liệu khác

- [CODE_OF_CONDUCT](./CODE_OF_CONDUCT.md) – quy trình xử lý hành vi & kháng nghị.
- [SECURITY](./SECURITY.md) – kênh báo cáo lỗ hổng.
- [ROADMAP](./ROADMAP.md) – mục tiêu Now/Next/Later.
- [CONTRIBUTING](./CONTRIBUTING.md) – checklist gửi PR.

## 9. Escalation & phản hồi

- Khi không đồng ý với quyết định PR, hãy gắn label `request-second-look` (hoặc ghi rõ trong comment); core team sẽ chỉ định reviewer khác trên cơ sở bandwidth, mục tiêu hoàn tất vòng bổ sung trong ≤10 ngày làm việc.
- Nếu vẫn bất đồng, mở Discussion `#governance` mô tả lý do và guardrail liên quan.
- Hành vi vi phạm Code of Conduct sẽ chuyển sang quy trình tại tài liệu đó.

## 10. Minh bạch & trách nhiệm

- Tất cả quyết định lớn (từ chối tính năng, thay đổi guardrail) phải được ghi chú trong `ROADMAP` hoặc Issue công khai.
- Các release phải cập nhật [CHANGELOG](./CHANGELOG.md) và gắn tag Git tương ứng.
- Báo cáo bảo mật được xử lý theo SLA ở [SECURITY](./SECURITY.md).

## 11. CE vs Commercial

| Chủ đề | CE | Commercial |
| --- | --- | --- |
| Lập kế hoạch | Có | Có |
| Apply patch | Manual | Auto + rollback |
| Điều phối workflow | Không | Có |
| UI/IDE | CE | IDE plugin, dashboard |
| Hỗ trợ | Best-effort | SLA, tư vấn |

Các ranh giới này giúp bảo vệ năng lực thương mại đồng thời giữ CE hữu ích cho đánh giá kỹ thuật.

## 12. Kênh giao tiếp

- GitHub Discussions: `#architecture`, `#roadmap`, `#contributing`.
- Email bảo mật: contact@midicoder.com.
- Ứng xử: contact@midicoder.com.
- Escalation governance: contact@midicoder.com.

Chúng tôi coi trọng feedback kỹ thuật chất lượng cao, nhưng quyết định cuối cùng vẫn thuộc về nhóm cốt lõi để đảm bảo Midicoder CE giữ được mục tiêu dài hạn.