# Node Type - Midicoder DSL v1

## Tổng quan

**Node Type** là đơn vị xây dựng cơ bản nhất của Ngôn ngữ Đặc thù miền (DSL) trong Midicoder. Nó định nghĩa một danh mục các đối tượng hoặc khái niệm mà DSL có thể biểu diễn, xác thực và biên dịch thành code thực thi.

## Định nghĩa chính thức

```
Node Type = {
    "kind": string,           # Bộ định danh duy nhất (ví dụ: "Entity", "Command")
    "params": Schema,         # Schema của các tham số có kiểu
    "obligations": Rules,     # Các ràng buộc BẮT BUỘC phải thỏa
    "outputs": Artifacts      # Code/artifacts được sinh ra sau biên dịch
}
```

## Cấu trúc của Node Type

```
┌─────────────────────────────────────┐
│           NODE TYPE                 │
│  ┌─────────────────────────────┐   │
│  │  1. KIND (bắt buộc)         │   │  ← "Entity", "Command", "Query"...
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  2. PARAMS (schema)         │   │  ← Các field + kiểu + cờ bắt buộc
│  │     - id: string            │   │
│  │     - fields: list[field]   │   │
│  │     - ...                   │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  3. OBLIGATIONS (quy tắc)   │   │  ✓ Những gì PHẢI đúng
│  │     - must_have_primary_key │   │
│  │     - must_be_tenant_scoped │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  4. OUTPUTS (sinh code)     │   │  ← SQL table, Python class, ...
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## Khái niệm cốt lõi

### 1. Kind

**Kind** là bộ định danh duy nhất cho một node type. Nó tuân theo mẫu:

```
{layer}.{concept}  hoặc  {domain}.{resource}
```

Ví dụ:

- `domain.entity` - Một Entity trong domain layer
- `app.command` - Một Command trong application layer
- `infra.datasource` - Một DataSource trong infrastructure layer

### 2. Params

**Params** định nghĩa schema cho một instance của node. Mỗi tham số có:

| Field         | Mô tả                                        |
| ------------- | -------------------------------------------- |
| `name`        | Tên tham số                                  |
| `type`        | Kiểu dữ liệu (string, int, list, dict, v.v.) |
| `required`    | Có phải tham số bắt buộc không               |
| `description` | Mô tả người đọc được                         |
| `default`     | Giá trị mặc định nếu không cung cấp          |
| `constraints` | Các quy tắc xác thực bổ sung                 |

**Ví dụ: Entity Params**

```python
class EntityParams(TypedDict, total=False):
    """Tham số có kiểu cho Entity nodes."""
    id: str              # ✓ Tên entity (ví dụ: "Order")
    description: str     # ✓ Mô tả
    fields: list[dict]   # ✓ Các trường của entity
    primary_key: str     # ✓ Tên trường khóa chính
    indexes: list[dict]  # ✓ Định nghĩa indexes
    constraints: list[dict]  # ✓ Các ràng buộc nghiệp vụ
    tags: list[str]      # ✓ Tags phân loại
    tenant_scope: str    # ✓ Phạm vi đa tenant
```

### 3. Obligations

**Obligations** là các ràng buộc tại thời điểm biên dịch mà một node BẮT BUỘC phải thỏa mãn. Chúng đảm bảo:

- **Tính toàn vẹn tham chiếu**: Tất cả tham chiếu đều giải quyết được tới các node hợp lệ
- **Quy tắc nghiệp vụ**: Các bất biến đặc thù miền được thực thi
- **Bảo mật**: Kiểm soát truy cập và cách ly tenant là chính xác
- **Nhất quán**: Các phụ thuộc giữa các node là hợp lệ

**Ví dụ Obligations cho Entity:**

```yaml
obligations:
    - type: must_have_id
      message: "Entity phải có trường 'id'"

    - type: must_have_primary_key
      message: "Entity phải khai báo khóa chính"

    - type: tenant_scope_required
      message: "Entity phải khai báo tenant_scope cho ứng dụng đa tenant"

    - type: field_types_valid
      message: "Tất cả các kiểu trường phải giải quyết được"
```

### 4. Outputs

**Outputs** là các artifacts được sinh ra khi một node được biên dịch. Các outputs thường gặp bao gồm:

| Loại Output       | Ví dụ                           |
| ----------------- | ------------------------------- |
| Database Schema   | Câu lệnh SQL CREATE TABLE       |
| Code Classes      | Python/TypeScript model classes |
| API Definitions   | OpenAPI/GraphQL schemas         |
| Validation Code   | Hàm xác thực đầu vào            |
| Migration Scripts | File migration database         |

## Phân loại Node Types (7 Layers)

Midicoder tổ chức node types thành 7 tầng kiến trúc:

### Tầng 1: Foundation

Foundation nodes cung cấp khung xương cấu trúc cho tất cả các contracts.

| Node Type    | Mục đích                              |
| ------------ | ------------------------------------- |
| `Manifest`   | Metadata dự án, version, cờ strict    |
| `Metadata`   | Chú thích, tags, thuộc tính tùy chỉnh |
| `Catalog`    | Giá trị liệt kê, type catalogs        |
| `Dependency` | Phụ thuộc giữa các node               |
| `Constraint` | Quy tắc xác thực, bất biến nghiệp vụ  |

### Tầng 2: Domain

Domain nodes biểu diễn các khái niệm nghiệp vụ và mô hình dữ liệu.

| Node Type     | Mục đích                             |
| ------------- | ------------------------------------ |
| `Entity`      | Đối tượng nghiệp vụ cốt lõi có state |
| `ValueObject` | Đối tượng giá trị bất biến           |
| `Enum`        | Bộ giá trị rời rạc                   |
| `Error`       | Định nghĩa lỗi và mã lỗi             |
| `Event`       | Sự kiện miền và thông báo            |

### Tầng 3: Application

Application nodes điều phối logic nghiệp vụ và workflows.

| Node Type  | Mục đích                       |
| ---------- | ------------------------------ |
| `Command`  | Thao tác thay đổi state        |
| `Query`    | Truy xuất dữ liệu chỉ đọc      |
| `Workflow` | Quy trình nghiệp vụ nhiều bước |
| `Rule`     | Định nghĩa quy tắc nghiệp vụ   |
| `Guard`    | Kiểm tra điều kiện tiên quyết  |
| `Effect`   | Thao tác side-effect           |

### Tầng 4: Infrastructure

Infrastructure nodes định nghĩa các triển khai kỹ thuật.

| Node Type    | Mục đích                  |
| ------------ | ------------------------- |
| `Table`      | Định nghĩa bảng database  |
| `DataSource` | Cấu hình kết nối database |
| `Cache`      | Chiến lược caching        |
| `Queue`      | Định nghĩa message queue  |
| `Index`      | Chỉ số database           |

### Tầng 5: Platform

Platform nodes xử lý bảo mật, quản trị và vận hành.

| Node Type      | Mục đích                      |
| -------------- | ----------------------------- |
| `Policy`       | Chính sách ủy quyền           |
| `Role`         | Định nghĩa vai trò người dùng |
| `AccessPolicy` | Kiểm soát truy cập chi tiết   |
| `AuditLog`     | Cấu hình nhật ký kiểm toán    |
| `RateLimit`    | Quy tắc giới hạn tốc độ       |

### Tầng 6: Integration

Integration nodes định nghĩa tương tác với hệ thống bên ngoài.

| Node Type      | Mục đích                     |
| -------------- | ---------------------------- |
| `HTTPRoute`    | Định nghĩa endpoint REST API |
| `GraphQL`      | Định nghĩa schema GraphQL    |
| `Integration`  | Tích hợp hệ thống bên ngoài  |
| `Webhook`      | Cấu hình webhook             |
| `Subscription` | Xử lý đăng ký sự kiện        |

### Tầng 7: Ops

Ops nodes định nghĩa cấu hình observability và deployment.

| Node Type    | Mục đích                    |
| ------------ | --------------------------- |
| `Metric`     | Định nghĩa metric tùy chỉnh |
| `Alert`      | Quy tắc cảnh báo và ngưỡng  |
| `Log`        | Cấu hình logging            |
| `Deployment` | Quy cách deployment         |
| `Secret`     | Cấu hình quản lý bí mật     |

## Ví dụ Node Type Instance

### Entity Instance

```yaml
- kind: domain.entity
  params:
      id: Order
      description: "Đơn hàng của khách trong hệ thống thương mại điện tử"
      fields:
          - name: id
            type: uuid
            required: true
          - name: customer_id
            type: uuid
            required: true
            source: "Customer.id"
          - name: status
            type: OrderStatus
            required: true
            default: "pending"
          - name: total_amount
            type: decimal
            required: true
      primary_key: id
      indexes:
          - name: idx_customer
            fields: [customer_id]
          - name: idx_status
            fields: [status]
      constraints:
          - type: check
            expression: "total_amount >= 0"
      tenant_scope: tenant
      tags: ["core", "billing"]
```

### Command Instance

```yaml
- kind: app.command
  params:
    id: CreateOrder
    description: "Tạo đơn hàng mới cho khách hàng"
    input:
      - name: customer_id
        type: uuid
        required: true
      - name: items
        type: list[OrderItemInput]
        required: true
      - name: notes
        type: string
        required: false
    fetches:
      - "Customer:{customer_id}"
      - "Product:{item.product_id}" for item in items
    guards:
      - id: customer.exists
        params: {entity: "Customer", field: "customer_id"}
      - id: product.in_stock
        params: {entity: "Inventory"}
    effects:
      - id: db.insert
        params: {table: "orders"}
      - id: emit.event
        params: {event: "OrderCreated"}
    errors:
      - "CustomerNotFound"
      - "InsufficientStock"
      - "InvalidOrder"
    returns:
      - name: order_id
        type: uuid
      - name: total_amount
        type: decimal
    required_permissions:
      - "orders:create"
    tenant_scope: tenant
    transaction: true
```

## So sánh với các hệ thống khác

| Hệ thống      | Khái niệm tương đương | Ví dụ                     |
| ------------- | --------------------- | ------------------------- |
| **OOP**       | Class / Type          | `class Order { ... }`     |
| **Database**  | Table Definition      | `CREATE TABLE orders ...` |
| **AST**       | Node Class            | `FunctionDef`, `ClassDef` |
| **GraphQL**   | Type Definition       | `type Order { ... }`      |
| **HTML**      | Element Tag           | `<table>`, `<div>`        |
| **Terraform** | Resource Type         | `aws_s3_bucket`           |

## Tại sao Node Types quan trọng

### 1. Type Safety

Compiler biết chính xác mỗi node type có những field nào, cho phép:

- Phát hiện lỗi sớm
- Auto-complete trong IDE
- Xác thực schema

### 2. Validation

Obligations đảm bảo nodes được cấu hình đúng:

- Thiếu các field bắt buộc
- Tham chiếu không hợp lệ
- Vi phạm quy tắc nghiệp vụ

### 3. Code Generation

Mỗi node type biết phải sinh ra code gì:

- Entity → Database table + Python class + GraphQL type
- Command → Handler function + validation + kiểm tra auth

### 4. Documentation

Node types cho phép tự động sinh tài liệu:

- API references từ HTTPRoute nodes
- Data models từ Entity nodes
- Error catalogs từ Error nodes

### 5. Reusability

Node types là các patterns có thể tái sử dụng:

- Định nghĩa một lần, dùng mọi nơi
- Patterns nhất quán qua các projects
- Các packs đặc thù ngành

## Mở rộng Node Types

Node types có thể được mở rộng thông qua:

### 1. Core Packs (CP)

Node types tích hợp được duy trì bởi đội Midicoder.

### 2. Domain Packs (DP)

Node types đặc thù ngành (ví dụ: Y tế, Tài chính).

### 3. Regulatory Overlays (RX)

Mở rộng đặc thù compliance (ví dụ: HIPAA, GDPR).

## Tóm tắt

**Node Type** là:

> Một **bản vẽ** định nghĩa danh mục các đối tượng trong hệ thống, bao gồm:
>
> - **Kind**: Bộ định danh duy nhất để nhận diện
> - **Params**: Schema mô tả các thuộc tính của node
> - **Obligations**: Quy tắc đảm bảo tính đúng đắn
> - **Outputs**: Artifacts được sinh ra trong quá trình biên dịch

**Ví dụ đơn giản:**

Nếu Midicoder giống như LEGO:

- Mỗi **loại gạch** = một Node Type
- Mỗi **cấu trúc lắp ráp** = một Node instance
- **Hướng dẫn lắp ráp** = Obligations
- **Mô hình cuối cùng** = Code được sinh ra

---

## Xem thêm

- [Tổng quan DSL v1](./dsl-v1-overview.md)
- [Projection Model](./projection-model.md)
- [Obligations & Guards](./obligations-guards.md)
- [Code Generation](./code-generation.md)
