"""Brief management module."""

MASTER_BRIEF_TEMPLATE = """# Master Brief: <Tên dự án / feature>

## 1. Tổng quan
- Mục tiêu sản phẩm/dịch vụ:
- Đối tượng sử dụng chính:
- Phạm vi (in-scope / out-of-scope):
- Bối cảnh hệ thống liên quan:
- Thuật ngữ chính (glossary, sẽ map sang `glossary.yaml`):
- Metadata version (owner, liên hệ, môi trường... sẽ map sang `meta/info.yaml`):

## 2. Domain & Data
- Các thực thể chính (Entities, sẽ map sang `domain/entities.yaml`):
- Value Objects quan trọng (nếu có, sẽ map sang `domain/value_objects.yaml`):
- Enum / danh mục dùng chung:
- Lỗi nghiệp vụ/kỹ thuật chính (sẽ map sang `domain/errors.yaml`):
- Yêu cầu mô hình hoá lưu trữ/persistence (nếu có, sẽ map sang `persistence/model.yaml`):

## 3. Luồng nghiệp vụ chính & Scenarios
- Luồng A: mô tả từng bước, điều kiện, actor:
- Luồng B:
- Các kịch bản end-to-end / acceptance scenarios (nếu có, sẽ map sang `scenarios/*.yaml` hoặc `.feature`):

## 4. Commands & Queries
- Command: <tên> — mục tiêu, input, output, side-effects, lỗi chính, events phát ra (map `app/commands.yaml`):
- Query: <tên> — mục tiêu đọc, input, output, entity nào được đọc (nếu có, map `app/queries.yaml`):

## 5. Rules & Policy
- Rules nghiệp vụ quan trọng (khi nào áp dụng, áp dụng cho command nào; map `rules/*.yaml`):
- Policy RBAC/ABAC: vai trò (roles) và quyền (permissions) chính (map `policy/rbac.yaml`):
- Permission map: mapping role → permission → command/API (nếu có, map `policy/permissions_map.yaml`):

## 6. Workflow / State Machine
- Entity: <tên> — các trạng thái và ý nghĩa:
- Transitions: điều kiện chuyển trạng thái, ai được phép thực hiện:
- Sự kiện domain/integration tương ứng (nếu có, map `domain/events.yaml`):
- Workflow dài giữa nhiều bounded context (nếu có, map `workflows/*.yaml`):

## 7. API
- Route: <method path> → <command/query> (sẽ map sang `api/http.yaml`):
- Quy ước auth, versioning, error response:

## 8. Phi chức năng
- Performance, security, logging, audit, observability...:

## 9. Ràng buộc kỹ thuật
- Stack hiện tại, conventions, error handling pattern:
- Ràng buộc về database, transaction, multi-tenant... (bổ sung cho `persistence/model.yaml` nếu cần):

## 10. Phụ lục
- Tài liệu tham khảo, link tới đặc tả chi tiết, diagram...:
"""

__all__ = ["MASTER_BRIEF_TEMPLATE"]
