# Phase 0 - Tổng quan chiến lược universal testing

## 1. Mục tiêu phase

Thiết lập ngôn ngữ chung cho toàn team về việc:

- Midicoder cần được test theo command, function, artifact và state
- test suite phải tăng trưởng tới quy mô cực lớn mà vẫn maintainable
- CI/CD phải đóng vai trò gatekeeper tuyệt đối

---

## 2. KPI toàn chương trình

### 2.1 KPI chất lượng

- branch reviewable luôn đạt **100% statement + branch coverage** cho scope `midicoder/`
- tất cả command public có unit + integration coverage
- tất cả regression bug phải có replay test tương ứng
- mọi failure mode quan trọng đều có deterministic assertion

### 2.2 KPI quy mô

- >= 10k unit tests handwritten và curated
- >= 100k parametrized command tests
- >= 300k property-based executions
- >= 300k corpus/regression executions
- >= 290k integration matrix executions
- tổng >= 1,000,000 test executions trong nightly / release pipeline

---

## 3. Các loại test phải có

1. **Function unit tests**
2. **Command integration tests**
3. **Artifact contract tests**
4. **Regression replay tests**
5. **Property-based tests**
6. **Policy / governance checks**
7. **CI/CD meta-tests** cho chính quality gate

---

## 4. Tại sao không chỉ chạy pytest thường

Nếu chỉ viết unit tests thông thường, team sẽ đạt coverage trong thời gian ngắn nhưng không đạt universal tested level.

Điều cần thiết là:

- parametrize rộng theo state matrix
- lưu corpus các lỗi thật
- replay artifacts lỗi cũ
- ép mọi thay đổi code kéo theo test + docs + policy checks

---

## 5. Exit criteria của toàn plan

Plan này chỉ được coi là hoàn thành khi:

1. Jenkins pipeline enforce toàn bộ quality gates
2. PR template và docs policy được enforce tự động
3. 100% coverage là bắt buộc thay vì khuyến nghị
4. có test inventory theo command
5. có nightly matrix đủ lớn để đạt 1 triệu executions
