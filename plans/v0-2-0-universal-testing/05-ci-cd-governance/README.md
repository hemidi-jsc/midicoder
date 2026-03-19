# Phase 5 - CI/CD governance với Jenkins

## 1. Mục tiêu phase

Dùng Jenkins như bộ máy thực thi và enforcement cho mọi policy:

- lint
- format
- code convention
- docs update
- PR template
- unit tests
- integration tests
- coverage 100%
- review readiness

---

## 2. Mô hình pipeline

### 2.1 PR pipeline

Chạy nhanh nhưng không được bỏ qua gate nào:

1. checkout
2. setup environment
3. repo policy checks
4. lint + convention
5. unit tests
6. integration tests
7. coverage 100%
8. mark review-ready

### 2.2 Main / merge pipeline

Ngoài PR pipeline, chạy thêm:

- package build
- extended integration matrix
- archive artifacts

### 2.3 Nightly pipeline

- full corpus replay
- property-based high volume
- million-case matrix
- trend reports

---

## 3. Governance rules

1. Jenkins phải là source of truth cho trạng thái review-ready
2. bất kỳ bypass nào đều phải bị coi là incident
3. docs và template là quality assets, không phải optional assets
4. pipeline phải archive đầy đủ junit, coverage, lint, và policy reports

---

## 4. Exit criteria

- mọi build PR đều có report chuẩn hóa
- branch chỉ được coi là ready-for-review khi Jenkins pass toàn bộ gates
- nightly pipeline cung cấp trend dữ liệu coverage, failures, flaky tests, corpus growth
