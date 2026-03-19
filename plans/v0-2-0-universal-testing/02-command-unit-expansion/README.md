# Phase 2 - Mở rộng unit tests theo command và function domain

## 1. Mục tiêu phase

Bẻ nhỏ Midicoder thành các domain testable và đẩy mạnh unit tests cho từng command/function cluster.

---

## 2. Cách chia domain

### 2.1 Brief domain

- loader config
- brief analyzer
- keyword/cache logic
- rewrite plumbing
- run logging

### 2.2 Contract domain

- file selection
- schema slicing
- YAML parsing
- validation
- feedback normalization
- repair ordering

### 2.3 Index domain

- working dir resolution
- scanner/filtering
- context merge
- seam extraction
- reindex delta logic

### 2.4 IR domain

- schema parsing
- normalization
- cross reference validation
- diagnostics

### 2.5 Code domain

- plan building
- patch generation
- patch application
- backup/restore
- report generation

### 2.6 Runtime domain

- runtime log parsing
- fix context extraction
- remediation routing

---

## 3. Chiến lược triển khai

1. ưu tiên domain deterministic trước
2. test từng function nhỏ trước command wrapper
3. mock toàn bộ external boundary: LLM, filesystem lớn, subprocess, network
4. mọi bug fix phải thêm regression unit test trước khi merge

---

## 4. Số lượng mục tiêu

- brief: 20k executions
- contract: 150k executions
- index: 150k executions
- ir: 120k executions
- code build/gen/apply: 250k executions
- runtime: 80k executions

---

## 5. Deliverables

- test inventory theo module
- naming convention cho test cases
- fixture builders dùng lại được
- regression bank cho mọi issue đã fix
