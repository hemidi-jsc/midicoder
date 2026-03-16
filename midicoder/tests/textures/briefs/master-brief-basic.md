# Master Brief: Order Service

## 1. Tổng quan
- Mục tiêu sản phẩm: quản lý đơn hàng đơn giản.
- Đối tượng sử dụng: nhân viên bán hàng.
- Phạm vi: tạo và theo dõi đơn hàng.

## 2. Domain & Data
- Thực thể chính: Order.
- Value Object: None.
- Enum / danh mục: None.

## 3. Luồng nghiệp vụ chính
- Tạo đơn hàng mới.
- Xem danh sách đơn hàng.

## 4. Commands & Queries
- Command: CreateOrder — tạo đơn hàng.
- Query: ListOrders — xem danh sách.

## 5. Rules & Policy
- Rule: Order phải có mã hợp lệ.
- Policy: RBAC theo vai trò.

## 6. Workflow / State Machine
- Entity: Order.
- Trạng thái: draft → submitted.
- Transitions: submit.

## 7. API
- POST /orders → CreateOrder
- GET /orders → ListOrders

## 8. Phi chức năng
- Logging cơ bản.

## 9. Ràng buộc kỹ thuật
- Python + FastAPI.

## 10. Phụ lục
- Không có.
