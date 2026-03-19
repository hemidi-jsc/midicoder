# Universal testing plan cho Midicoder - v0.2.0

## 1. Mục tiêu tối thượng

Midicoder phải đạt **universal tested level** cho chính sản phẩm Midicoder, không phải cho code do Midicoder generate ra.

Điều đó có nghĩa là:

1. test cho mọi command public trong pipeline
2. test cho mọi function deterministic quan trọng
3. test cho mọi validator, parser, transformer, orchestrator
4. test cho mọi state transition và artifact contract
5. **100% code coverage luôn luôn** trên nhánh reviewable
6. nếu chưa đạt quality gate thì **không assign người review code**

---

## 2. Định nghĩa “1 triệu tests”

"1 triệu tests" ở đây là **1 triệu lượt thực thi test cases** cho chính Midicoder.

Không nhất thiết là 1 triệu file `test_*.py`. Thay vào đó, số lượng này đến từ:

- unit tests viết tay
- parametrized tests theo matrix
- property-based tests
- corpus replay tests
- regression fixtures
- integration matrices theo command + state + artifact shape

---

## 3. Nguyên tắc tổ chức

### 3.1 Trục chính là command pipeline

Toàn bộ chiến lược test phải đi theo command pipeline của Midicoder:

1. `brief rewrite`
2. `contract gen`
3. `contract check`
4. `contract repair`
5. `index`
6. `ir build`
7. `code build`
8. `code gen`
9. `code apply`
10. `runtime test`
11. `runtime fix`

### 3.2 Test Midicoder itself

Các test này phải xác nhận:

- command hoạt động đúng
- artifacts được ghi đúng
- run logs đúng
- rollback và failure modes đúng
- deterministic behavior giữ nguyên
- LLM boundaries được mock/fake đúng

### 3.3 Coverage không được thương lượng

- Coverage gate mặc định là **100%**.
- Bất kỳ PR nào làm giảm coverage hoặc thiếu test mới cho phần code thay đổi phải fail CI.
- Chỉ khi mọi quality gate pass mới chuyển sang bước review bởi con người.

---

## 4. Cấu trúc phase

Bộ kế hoạch này được chia thành các phase:

1. `00-overview/`
2. `01-foundation-quality-gates/`
3. `02-command-unit-expansion/`
4. `03-command-integration-matrix/`
5. `04-million-case-engine/`
6. `05-ci-cd-governance/`

Mỗi phase đều phải có deliverables rõ ràng, owner rõ ràng, và quality gate rõ ràng.
