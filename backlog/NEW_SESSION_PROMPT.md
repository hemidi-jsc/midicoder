# TIẾP TỤC THI CÔNG TASK TIẾP THEO TRONG D:\hemidi-labs\midicoder-ce\backlog\TODOS.md

## Epic E12: Core Compiler Packs CP01-CP30 (P0-P2)

| Task ID | Description                          | Status | Notes                        |
| ------- | ------------------------------------ | ------ | ---------------------------- |
| E12-001 | CP01: Domain Model DSL               | DONE   | `midicoder/dsl/`             |
| E12-002 | CP02: Multi-Tenant Architecture      | TODO   | Tenant-aware schemas         |
| E12-003 | CP03: Authentication & Authorization | TODO   | JWT, OAuth2, RBAC            |
| E12-004 | CP04: RBAC & Policy Engine           | TODO   | access.yaml, policy eval     |
| E12-005 | CP05: Event-Driven Architecture      | TODO   | Event schemas, message queue |
| E12-006 | CP06: API Gateway & Service Mesh     | TODO   | Gateway config               |
| E12-007 | CP07: Infrastructure as Code         | TODO   | Docker + Terraform           |
| E12-008 | CP08: Database & Data Access         | TODO   | SQLAlchemy, repository       |
| E12-009 | CP09: Caching & Performance          | TODO   | Redis, cache strategies      |
| E12-010 | CP10: Search & Indexing              | TODO   | Elasticsearch                |
| E12-011 | CP11: File Storage & Media           | TODO   | S3, image processing         |
| E12-012 | CP12: Notification & Communication   | TODO   | Email/SMS/push               |
| E12-013 | CP13: Background Job & Workflow      | TODO   | Celery/worker                |
| E12-014 | CP14: Audit Trail & Compliance       | TODO   | Audit logging                |
| E12-015 | CP15: Observability Stack            | TODO   | Prometheus/Grafana           |
| E12-016 | CP16-CP30: Remaining CPs             | TODO   | Per phase priority           |

## QUY TẮC BẮT BUỘC QUY TRÌNH Test Driven Development và 2 Skills:

- Sử dụng skill `coding` và `judge` lần lượt, `judge` để hiểu context, sau đó `coding`, sau đó lại `judge` kết quả, lặp lại tới khi đạt trạng thái tốt nhất.
- Tuân thủ tuyệt đối quy trình TDD, viết tests bám sát theo SoT không viết mock và test giả.
- Khi viết test phải nhớ rõ là viết test độc lập theo SoT, tuyệt đối không nên viết test theo code đã implemented.
- Code có thể sửa, còn tests khi đã viết và judge đầy đủ sẽ phải giữ nguyên không sửa nữa.

## QUY TẮC BẮT BUỘC: Comment Code bằng TIẾNG VIỆT

### Tuân thủ Tuyệt đối

1. **TẤT CẢ comments** trong code PHẢI viết bằng **TIẾNG VIỆT RÕ RÀNG**
2. **Docstrings** PHẢI viết bằng tiếng Việt, theo Google/NumPy style
3. **Error messages** PHẢI viết bằng tiếng Việt
4. **Variable names** vẫn giữ tiếng Anh (chuẩn coding)
5. **Function names** vẫn giữ tiếng Anh (chuẩn coding)
6. Không được chỉnh sửa hoặc tạo file mới trong các folder sau:

- `backlog` -> không được chỉnh sửa, ngoại trừ file `TODOS.md` nhằm cập nhật tiến độ
- `midicoder\brief`
- `midicoder\code`
- `midicoder\commands`
- `midicoder\config`
- `midicoder\context`
- `midicoder\contract`
- `midicoder\io`
- `midicoder\ir`
- `midicoder\llm`
- `midicoder\runtime`
- `webgui`
- `api`
- `scripts`

7. Khi cần thiết hãy tạo folder mới nằm trong folder `midicoder`

- `midicoder\contracts` -> tiếp tục thi công vào đây nếu cần
- `midicoder\dsl` -> tiếp tục thi công vào đây nếu cần
- `midicoder\<new-folder>` -> tạo thêm folder mới nếu cần

8. Quản lý mã lỗi và mã exception tập trung tại: `midicoder\errors.py`

9. Trong code implementation không được ghi các nội dung như sau: `SoT reference: requirement.md lines 385-388`, vì file SoT sẽ là file tạm cho tới khi xong hết dự án sẽ xóa đi, không nên dẫn chứng nó trong code chính thức.

10. Trong code không được dẫn chứng tới TODOS.md vì nó cũng là file tạm.

11. Trong code không được comment trạng thái thực hiện công việc, ví dụ như comment chữ `Phase A: ...` để đánh dấu đoạn code đó là thuộc phase nào đó trong kế hoạch công việc.

### Ví dụ đúng ✅

```python
def load_projection_tree(dsl_path: Path) -> ProjectionTree:
    """
    Tải toàn bộ DSL directory vào ProjectionTree.

    Args:
        dsl_path: Đường dẫn đến thư mục DSL chứa entities.yaml, commands.yaml, v.v.

    Returns:
        ProjectionTree với tất cả nodes đã được tải

    Raises:
        FileNotFoundError: Nếu không tìm thấy thư mục DSL
        ValidationError: Nếu YAML không hợp lệ
    """
    tree = ProjectionTree()

    # Load entities
    entities_file = dsl_path / "entities.yaml"
    if entities_file.exists():
        tree.extend(_load_entities(entities_file))
```

### Ví dụ sai ❌

```python
def load_projection_tree(dsl_path: Path) -> ProjectionTree:
    """Load entire DSL directory into ProjectionTree."""
    tree = ProjectionTree()

    # Load entities
    entities_file = dsl_path / "entities.yaml"
```

### Áp dụng cho

- ✅ Docstrings (module, class, function, method)
- ✅ Inline comments (explaining logic)
- ✅ Error messages (user-facing và log messages)
- ✅ TODO/FIXME comments
- ✅ Type hints comments (nếu cần)

**VIOLATING THIS RULE = FAILED TASK**

---

## Liên Hệ & Tài nguyên

- SoT: `D:\hemidi-labs\midicoder-ce\backlog\requirement.md`
- **ERRORS CLASS**: `midicoder\errors.py`
- 100 domains: `D:\hemidi-labs\midicoder-ce\backlog\INDUSTRY_100_SYSTEM_MAP.md`
