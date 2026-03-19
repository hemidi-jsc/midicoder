# Coverage 100% và review gate

## 1. Nguyên tắc

Review bởi con người là tài nguyên đắt. Midicoder chỉ nên assign review khi machine gates đã pass hoàn toàn.

## 2. Chính sách

1. coverage < 100% => fail build
2. unit fail => fail build
3. integration fail => fail build
4. lint fail => fail build
5. docs policy fail => fail build
6. PR template policy fail => fail build

## 3. Hành vi mong muốn trong Jenkins

- stage `quality-gate` là gate cuối trước khi cho phép review
- khi coverage hoặc test không đạt, build phải dừng ngay
- khi mọi gate đạt, pipeline mới đánh dấu build là `review-ready`

## 4. Lý do chọn 100% thay vì 85-95%

Với Midicoder là hệ thống orchestration/transform/contract tooling, phần lớn code path đều có thể và nên được kiểm soát bằng test deterministic.

100% coverage không tự động đồng nghĩa với chất lượng cao, nhưng trong repo này nó là **điều kiện cần bắt buộc**.
