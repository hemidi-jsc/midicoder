# Phase 4 - Engine để đạt 1 triệu test executions

## 1. Mục tiêu phase

Tạo cơ chế scale test executions lên mức 1 triệu mà không làm repo trở thành mớ hỗn độn.

---

## 2. Bốn nguồn tạo volume

### 2.1 Parametrized matrices

Sinh cases từ:

- flags
- config modes
- artifact presence
- version state
- repo topology

### 2.2 Property-based tests

Dùng để tạo volume lớn cho:

- parser
- validator
- path logic
- graph logic
- patch operations

### 2.3 Corpus replay

Lưu mọi bug thật dưới dạng replay corpus:

- input artifacts
- config
- command invoked
- expected failure hoặc expected fix

### 2.4 Nightly cross-product pipeline

Nightly job sẽ quét:

- command x fixture family x mode x python version

để đạt tổng số executions mục tiêu.

---

## 3. Kiến trúc dữ liệu test

Đề xuất:

```text
midicoder/tests/
  corpus/
    command_name/
    regressions/
    generated/
  fixtures/
    repos/
    contracts/
    ir/
    plans/
    patches/
  generators/
```

---

## 4. Quy tắc anti-chaos

1. không sinh ra 1 triệu file test python
2. volume đến từ data, không đến từ copy-paste
3. mọi generated corpus đều phải reproducible
4. seed phải cố định cho nightly chuẩn
5. failures phải lưu artifact để replay được

---

## 5. Exit criteria

- nightly pipeline đạt >= 1,000,000 executions
- failure replay reproducible
- execution time nằm trong ngân sách CI định trước
