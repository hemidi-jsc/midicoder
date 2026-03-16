# Phụ lục A - Quyền Tác Giả & Pháp Chế CE

Tài liệu này gom toàn bộ chính sách liên quan đến quyền tác giả, nghĩa vụ pháp lý và quyền quyết định thương mại cho Midicoder CE. Phụ lục được rà soát lần cuối ngày **11/03/2026** để cộng đồng dễ tham chiếu mà không phải đọc rải rác ở README, GOVERNANCE và ROADMAP.

## A1. Phạm vi áp dụng

- Áp dụng cho mã nguồn trong `midicoder/`.
- Điều chỉnh mọi đóng góp được merge vào nhánh công khai của dự án CE.
- Trường hợp xung đột, điều khoản trong giấy phép Apache License 2.0 và các chính sách doanh nghiệp của Hemidi JSC sẽ được ưu tiên.

---

## 4. Quyền tác giả

### 4.1 Chủ sở hữu copyright gốc
- Hemidi JSC nắm quyền tác giả với toàn bộ mã/tài liệu được công bố trước ngày contributor gửi PR.
- Các asset liên quan (logo, thương hiệu Midicoder) không nằm trong giấy phép CE và phải được xin phép riêng nếu dùng cho mục đích marketing.

### 4.2 Quyền của contributor
- Contributor **giữ nguyên quyền tác giả** đối với phần đóng góp của mình.
- Khi PR được merge, contributor cấp phép lại phần đóng góp theo Apache License 2.0, không cần ký CLA riêng.
- Contributor có quyền tái sử dụng phần đóng góp của chính mình trong dự án khác, miễn là tuân thủ Apache-2.0.
- Nếu contributor muốn rút đóng góp, core team có thể từ chối khi phần đó đã gắn với release hoặc phụ thuộc vào guardrail khác; thay vào đó sẽ xem xét revert kỹ thuật nếu có lý do pháp lý chính đáng.

### 4.3 Quan hệ contributor - core team
- Đây là quan hệ cộng đồng tự nguyện, **không tạo lập quan hệ lao động** hay nghĩa vụ trả thù lao.
- Core team chịu trách nhiệm cuối cùng về kiến trúc, roadmap, bảo mật và pháp chế; contributor chấp nhận rằng quyết định merge/revert thuộc toàn quyền core team.
- Contributor có quyền được ghi nhận trong CHANGELOG hoặc phần credits của release; core team có thể gỡ attribution nếu đóng góp bị revert vì vi phạm guardrail, bảo mật hoặc pháp lý.

---

## 5. Các vấn đề pháp chế

| Chủ đề | Chính sách chuẩn | Diễn giải |
| --- | --- | --- |
| Giấy phép | Apache License 2.0 | Áp dụng cho mã lẫn tài liệu đi kèm. Không có giấy phép kép trong CE. |
| Quyền sử dụng đóng góp | Hemidi JSC có thể dùng lại trong CE và sản phẩm thương mại | Contributor không nhận chia sẻ doanh thu; attribution giữ nguyên trong CHANGELOG/release note. |
| Trách nhiệm pháp lý | Phân phối **“as-is”** | Không SLA, không bảo hành; người dùng chịu trách nhiệm khi đưa output vào sản phẩm. |
| Bảo mật dữ liệu | Người dùng tự cấu hình endpoint LLM | CE không gửi telemetry; hãy tuân thủ chính sách nội bộ của tổ chức khi đẩy dữ liệu nguồn. |

### 5.1 Điều khoản thương mại hóa
- Mọi đóng góp CE có thể được tái sử dụng trong bản thương mại, bao gồm việc đóng gói lại hoặc thêm tính năng độc quyền, miễn là vẫn tuân thủ Apache-2.0 đối với phần đã mở nguồn.
- Khi tính năng CE được tái sử dụng trong bản thương mại, core team sẽ:
  1. Ghi nhận trong CHANGELOG hoặc release note.
  2. Giữ nguyên các guardrail để tránh sai khác hành vi CE.
  3. Bổ sung tài liệu mô tả phần thương mại mở rộng nếu cần.

### 5.2 Nghĩa vụ pháp lý của dự án và contributor
- **Dự án**: chịu trách nhiệm duy trì giấy phép, thông báo bảo mật, và gỡ bỏ nội dung vi phạm DMCA hoặc quyền sở hữu trí tuệ khác khi nhận được yêu cầu hợp lệ.
- **Contributor**: cam kết rằng phần đóng góp là do chính họ sở hữu hoặc có quyền cấp phép; chịu trách nhiệm nếu sao chép nội dung vi phạm bản quyền bên thứ ba.
- Nếu phát sinh tranh chấp, dự án sẽ tạm khoá PR/commit liên quan, thông báo công khai và phối hợp tháo gỡ trong vòng 14 ngày làm việc.

---

## 6. Quyền quyết định thương mại với đề xuất từ cộng đồng

### 6.1 Nguyên tắc
- Quyết định thương mại (tích hợp vào bản thương mại, định giá, SLA, tính năng độc quyền) **thuộc toàn quyền core team và Hemidi JSC**.
- Cộng đồng có thể đề xuất tính năng, nhưng không thể yêu cầu roadmap thương mại hoặc quyền truy cập mã nguồn khép kín.

### 6.2 Quy trình đánh giá đề xuất liên quan thương mại
1. **Nộp đề xuất** qua GitHub Discussion `#roadmap` hoặc Issue `feature request`, ghi rõ tác động thương mại (nếu có).
2. **Triage (≤14 ngày)**: PM phân loại `CE`, `commercial-track`, hoặc `out-of-scope`. Kết quả được phản hồi công khai.
3. **Đánh giá sâu**: core team xem xét guardrail kỹ thuật, tác động doanh thu, chi phí vận hành và rủi ro pháp lý.
4. **Quyết định**:
   - `CE`: thêm vào ROADMAP với thời gian dự kiến.
   - `commercial-track`: mô tả lý do và cách tham gia chương trình khách hàng (beta, early access).
   - `out-of-scope`: giải thích vì sao không phù hợp (ví dụ: phá vỡ guardrail, yêu cầu hạ tầng riêng).
5. **Escalation**: nếu contributor không đồng ý, có thể mở Discussion `#governance` hoặc email `contact@midicoder.com`. Quyết định cuối cùng vẫn thuộc về core team.

### 6.3 Vùng đỏ (không đàm phán)
- Không chuyển giao quyền sở hữu thương hiệu Midicoder hoặc tên lệnh.
- Không chia sẻ kế hoạch thương mại nội bộ ngoài các kênh công khai đã công bố.
- Không chấp nhận cam kết doanh thu hoặc quyền ưu tiên tính năng đổi lấy đóng góp CE.

---

## A2. Câu hỏi nhanh

- **Tôi cần ký CLA không?** Không. Merge PR đồng nghĩa bạn chấp nhận Apache-2.0 và các điều khoản trong phụ lục này.
- **Tôi có thể dùng lại đoạn code của mình ở dự án khác?** Có, miễn tuân thủ Apache-2.0 và giữ attribution phù hợp.
- **Tôi muốn ràng buộc tính năng CE vào hợp đồng thương mại?** Vui lòng liên hệ `contact@midicoder.com`; yêu cầu đó nằm ngoài phạm vi CE.
- **Ai xử lý tranh chấp bản quyền?** Gửi email `contact@midicoder.com` với bằng chứng sở hữu; core team sẽ phản hồi trong tối đa 14 ngày làm việc.

---

_Mọi thắc mắc thêm vui lòng tham khảo_ `GOVERNANCE.md` _và_ `README.md` _hoặc liên hệ các kênh được liệt kê ở cuối hai tài liệu đó._