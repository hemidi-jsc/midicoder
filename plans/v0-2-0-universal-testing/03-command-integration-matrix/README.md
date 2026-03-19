# Phase 3 - Integration matrix theo từng command

## 1. Mục tiêu phase

Thiết kế integration tests cho toàn bộ command public của Midicoder theo matrix state/artifact.

---

## 2. Danh sách command bắt buộc

1. `midicoder init`
2. `midicoder version create`
3. `midicoder brief rewrite`
4. `midicoder contract gen`
5. `midicoder contract check`
6. `midicoder contract repair prepare`
7. `midicoder contract repair run`
8. `midicoder index`
9. `midicoder ir build`
10. `midicoder code build`
11. `midicoder code gen`
12. `midicoder code apply`
13. `midicoder runtime test`
14. `midicoder runtime fix`

---

## 3. Matrix chuẩn cho mỗi command

Mỗi command đều phải có tối thiểu các lớp integration sau:

- happy path
- missing precondition
- malformed artifact input
- partial failure path
- deterministic rerun path
- logging/report artifact path
- state transition path

---

## 4. Nguyên tắc fixture repo

- repo fixture phải nhỏ và tối giản
- mỗi fixture mô tả đúng một vấn đề
- có fixture baseline + broken + legacy + migration + conflict
- mọi fixture cần có metadata và expected outputs

---

## 5. Exit criteria

Phase này hoàn thành khi tất cả command public đều có integration matrix tối thiểu chuẩn hóa.
