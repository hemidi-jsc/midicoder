# Thiết kế command `midicoder runtime test` - v0.2.0

## 1. Mục tiêu sản phẩm

`midicoder runtime test` không còn chỉ là “chạy app lên xem có boot được không”. Trong v0.2.0, command này trở thành **verification pipeline thật** cho workdir sau apply.

---

## 2. Vì sao phải đổi

Startup smoke test chỉ phát hiện được một lớp lỗi hẹp:

- import errors
- syntax errors
- boot-time runtime errors

Nhưng không bắt được đầy đủ:

- lint violations
- type errors
- test regressions
- API contract mismatches
- broken behavior trong unit/integration tests

---

## 3. Product contract mới

`runtime test` => `verify pipeline`

### Verification stages mặc định

1. environment check
2. format/lint
3. static typecheck
4. unit test
5. integration/smoke test
6. optional app startup

---

## 4. Inputs

1. working_dir
2. stack profile từ index
3. verification config
4. changed paths (optional optimization)

---

## 5. Outputs

Thư mục logs / verification artifacts:

- `verify-summary.json`
- `lint.log`
- `typecheck.log`
- `unit.log`
- `integration.log`
- `smoke.log`
- `failure-classification.json`

---

## 6. Stage design

### Stage A - Environment readiness

Kiểm tra:

- python/node runtime
- virtual env / package manager
- dependency install state
- required env vars tối thiểu

### Stage B - Lint

Ví dụ Python:

- `ruff check`
- optional `ruff format --check`

### Stage C - Typecheck

Ví dụ Python:

- `mypy`
- hoặc `pyright`

### Stage D - Unit tests

Ví dụ:

- `pytest -q`

### Stage E - Integration tests

Nếu repo có marker/config tương ứng:

- API tests
- service integration tests
- DB migration smoke

### Stage F - Startup smoke

Cuối cùng mới boot app nếu phù hợp.

---

## 7. Error classification

Mọi lỗi phải được phân loại thành machine-readable categories:

- environment_error
- dependency_error
- lint_error
- type_error
- unit_test_failure
- integration_test_failure
- startup_error
- contract_drift_signal

---

## 8. Changed-path optimization

Nếu vừa `code apply`, command có thể ưu tiên:

- lint/typecheck/test impacted areas trước
- nhưng vẫn cần policy rõ về full verification vs fast verification

### Chế độ đề xuất

- `--fast`: chỉ impacted checks
- `--full`: full suite

Mặc định CI hoặc automated remediation nên dùng `--full`.

---

## 9. Không dùng LLM

Command này phải hoàn toàn deterministic.

---

## 10. Failure modes

1. tooling missing
2. test runner misconfigured
3. flaky tests
4. env secrets missing
5. startup dependency unavailable

### Policy khi fail

- phân biệt infra failure và code failure
- emit actionable diagnostics
- không tự patch code

---

## 11. Observability

Mỗi stage cần:

- command line executed
- start/end time
- exit code
- stdout/stderr logs
- normalized error summaries

---

## 12. Test strategy cho command

1. Stage orchestration tests
2. Error classification tests
3. Fast vs full mode tests
4. Missing tool diagnostics tests

---

## 13. Open questions

1. Có nên hỗ trợ multi-service verification matrix không?
2. Có nên detect test impact graph từ changed files không?
3. Có nên cho phép custom verification pipelines per stack không?

