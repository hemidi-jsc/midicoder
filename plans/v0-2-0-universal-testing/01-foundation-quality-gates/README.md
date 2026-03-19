# Phase 1 - Foundation và quality gates

## 1. Mục tiêu phase

Xây nền tảng bắt buộc để mọi test sau này có thể scale:

- tooling test chuẩn
- lint / format / convention checks
- docs update policy
- PR template policy
- coverage gate 100%
- Jenkins pipeline chạy đồng nhất cho PR, merge, release

---

## 2. Deliverables

1. `Jenkinsfile`
2. `pytest.ini`
3. `.coveragerc`
4. `.ruff.toml`
5. script kiểm tra docs update
6. script kiểm tra code convention
7. `.github/pull_request_template.md`

---

## 3. Quality gates bắt buộc

### Gate A - Repo policy

- PR template phải tồn tại và theo đúng format bắt buộc
- docs hoặc plan phải được update nếu code thay đổi hành vi hoặc quy trình

### Gate B - Code quality

- `ruff check` pass
- `ruff format --check` pass
- convention script pass

### Gate C - Testing

- unit tests pass
- integration tests pass
- coverage = 100%

### Gate D - Packaging

- package build / import smoke pass

---

## 4. Exit criteria

Phase này xong khi một PR mới không thể vượt qua CI nếu thiếu một trong các điều kiện trên.
