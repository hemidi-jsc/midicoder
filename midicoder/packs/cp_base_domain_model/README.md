# B01 — cp_base_domain_model

> **Domain Model DSL & IR Builder** — Foundation pack của Midicoder CE.

## Mục đích

B01 cung cấp toàn bộ primitive DDD (Domain-Driven Design) cho hệ thống: **Entity, Command, Query, ValueObject, Aggregate, Saga, CQRS, Event Sourcing**. Pack đóng vai trò là root của dependency graph — không phụ thuộc pack nào (`depends_on: []`), nhưng **31/51 pack còn lại** đều phụ thuộc trực tiếp vào B01.

**Luồng chính:** YAML DSL → Parser → Typed Dataclass → Emitter → Code generate (FastAPI/SQLAlchemy hoặc NestJS/TypeORM)

---

## Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────────────────┐
│                         B01  cp_base_domain_model                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  models.py (2499 dòng)                                               │
│  ├── 21 Enum  (FieldType, RelationshipType, GuardType, EffectType…)  │
│  ├── 33 Dataclass (Entity, Command, Query, VO, Aggregate, Saga…)     │
│  └── 78 symbols export qua __all__                                   │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ EntityParser │  │CommandParser │  │  VO Parser   │               │
│  │ YAML→Entity  │  │ YAML→Command │  │ YAML→VO      │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                  │                  │                       │
│         ▼                  ▼                  ▼                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │EntityEmitter │  │Cmd Emitter   │  │  VO Emitter  │               │
│  │ABC (abstract)│  │FastAPI/NestJS│  │dual-path     │               │
│  └──────┬───────┘  └──────────────┘  │Py/TS         │               │
│         │                            └──────┬───────┘               │
│    ┌────┴────┐                                  │                    │
│    ▼         ▼                                  ▼                    │
│ FastAPI    NestJS                              FastAPI/ NestJS       │
│ SQLAlchemy TypeORM                              Dataclass/ Class     │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  Recipes (11): factory functions tạo pre-configured DDD instances   │
│  Guards (11 types): AUTH, TENANT, KYC, AML, HIPAA, GDPR, PCI, FRAUD │
│  Effects (17): CRUD, TX, Event, Integration, Observability, Compliance│
│  Error Handler: Global middleware cho FastAPI/NestJS/Angular/React   │
│  45 Jinja2 templates (20 FastAPI, 21 NestJS, 2 Angular, 2 React)    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Cấu trúc file

```
cp_base_domain_model/
├── models.py                 # 2499 dòng — toàn bộ model (Entity, Command, Query, VO, Advanced)
├── __init__.py               # Re-export 98 symbols
├── pack.yml                  # Metadata: 14 definitions, 11 recipes, 4 obligations, 45 templates
│
├── entity_parser.py          # YAML DSL → Entity
├── entity_emitter.py         # Abstract base class cho Entity emitter
├── entity_fastapi.py         # SQLAlchemy model (Python)
├── entity_nestjs.py          # TypeORM entity (TypeScript)
│
├── command_parser.py         # YAML DSL → Command
├── command_fastapi.py        # FastAPI command handler emitter
├── command_nestjs.py         # NestJS command handler emitter
├── command_guards.py         # 11 guard types + compliance (KYC/AML/HIPAA/GDPR/PCI/Fraud/Safety/Claims)
├── command_effects.py        # 17 effect types (CRUD, TX, Event, Integration, Observability, Compliance)
├── command_validator.py      # Command input validation
├── command_transaction.py    # TransactionManagerSQL (SQLite-based nested TX)
│
├── query_parser.py           # Module-level functions: parse_filters, parse_pagination, v.v.
├── query_fastapi.py          # FastAPI query handler emitter
├── query_nestjs.py           # NestJS query handler emitter
├── query_guards.py           # 2 query guard types (AUTH, TENANT_SCOPE)
├── query_effects.py          # 2 query effect types (AUDIT_LOG, RECORD_METRIC)
│
├── vo_parser.py              # YAML DSL → ValueObject
├── vo_emitter.py             # Abstract VO emitter với dual-path Python/TypeScript
├── vo_fastapi.py             # Frozen dataclass (Python)
├── vo_nestjs.py              # Class + decorator (TypeScript)
├── vo_types.py               # TypeResolver: DSL type → Python/TS type mapping
├── vo_inheritance.py         # InheritanceResolver: chain resolve, merge, cycle detection
├── vo_computed.py            # ComputedFieldEvaluator: sandboxed formula + code gen
├── vo_inheritance.py         # InheritanceResolver
│
├── error_handler_models.py   # GlobalErrorHandler, ErrorMapper, Logging/Notification config
├── error_handler_fastapi.py  # FastAPI error handler emitter
│
├── recipes.py                # 11 recipe factory functions
│
└── tests/                    # 18 test files, 677 test cases
    ├── test_entity_parser.py
    ├── test_entity_models.py
    ├── test_entity_emitter.py
    ├── test_command_parser.py
    ├── test_command_effects.py
    ├── test_command_emitter.py
    ├── test_command_guards_p2.py
    ├── test_command_compliance.py
    ├── test_value_object_parser.py
    ├── test_value_object_core.py
    ├── test_value_object_fastapi.py
    ├── test_value_object_nestjs.py
    ├── test_value_objects_tenant.py
    ├── test_query_emitter.py
    ├── test_recipes.py
    ├── test_error_handler_models.py
    ├── test_pack_emitter_router.py
    └── test_pipeline_plan.py
```

---

## Models — Tóm tắt

### Nhóm Entity (7 dataclass + 5 enum)

| Class           | Mô tả                                                                                                             |
| --------------- | ----------------------------------------------------------------------------------------------------------------- |
| `Entity`        | Core domain model: `id`, `fields`, `relationships`, `constraints`, `indexes`, `lifecycle_hooks`, `render_context` |
| `EntityField`   | Field: 12 types (STRING, INTEGER, FLOAT, BOOLEAN, DATETIME, TEXT, UUID, JSON, DECIMAL, ENUM, LARGE_BINARY, ARRAY) |
| `Relationship`  | 5 types: ONE_TO_ONE, ONE_TO_MANY, MANY_TO_MANY, SELF_REFERENCING, POLYMORPHIC                                     |
| `Constraint`    | 3 types: UNIQUE, CHECK, FOREIGN_KEY                                                                               |
| `Index`         | Named, composite, unique index                                                                                    |
| `LifecycleHook` | 6 events: before/after insert, update, delete                                                                     |

**Alias backward-compatible:** `Field = EntityField`, `FieldType = EntityFieldType`

### Nhóm Command (6 dataclass + 3 enum)

| Class              | Mô tả                                                                                                                   |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `Command`          | Write operation: `input`, `fetches`, `guards`, `effects`, `errors`, `writes_to`, `transaction_required`, `tenant_scope` |
| `CommandField`     | Input field với 21 attributes (validation: pattern, min/max length/value, items)                                        |
| `CommandGuard`     | 11 guard types (AUTH, TENANT_SCOPE, KYC, AML, HIPAA, FRAUD, SAFETY, CLAIMS, v.v.)                                       |
| `CommandEffect`    | 17 effect types (CRUD, TX, Event, Integration, Observability, Compliance)                                               |
| `CommandError`     | Error code, message, http_status, retryable, compensation                                                               |
| `ValidationResult` | is_valid, errors[], warnings[]                                                                                          |

### Nhóm Query (11 dataclass + 6 enum)

| Class              | Mô tả                                                                                            |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| `Query`            | Read operation: `reads_from`, `filters`, `pagination`, `projection`, `sort`, `guards`, `effects` |
| `FilterExpression` | field, operator (13 types), value — có `to_sqlalchemy()`                                         |
| `FilterGroup`      | Nested AND/OR logic — có `to_sqlalchemy()`                                                       |
| `PaginationConfig` | OFFSET hoặc CURSOR                                                                               |
| `PHIMaskingConfig` | HIPAA PHI masking: `should_mask()`, `mask_value()`                                               |

### Nhóm ValueObject (2 dataclass + 1 enum)

| Class         | Mô tả                                                                                          |
| ------------- | ---------------------------------------------------------------------------------------------- |
| `ValueObject` | Immutable domain primitive: `id`, `fields`, `immutable`, `comparable`, `extends` (inheritance) |
| `VOField`     | 10 types (không có LARGE_BINARY, ARRAY, OBJECT — đúng khái niệm VO)                            |

### Advanced Domain Patterns (8 dataclass + 9 enum)

`DomainEvent`, `AggregateRoot`, `Projection`, `EventSourcedAggregate`, `TemporalEntity`, `PolymorphicEntity`, `Saga`, `SagaStep`

---

## Use Case thực tế — 12 Capabilities

Mỗi capability trong B01 phục vụ một trường hợp thực tế cụ thể. Dưới đây là ví dụ chi tiết cho **tất cả 12 capabilities**.

---

### 1. Entity Modeling — CRUD model cơ bản

**Khi nào dùng:** Cần tạo database model cho bất kỳ entity nào trong hệ thống (User, Product, Order, Invoice, v.v.).

**Trường hợp thực tế:** Hệ thống e-commerce cần entity `Product` với field `price` (DECIMAL), `category` (ENUM), và lifecycle hook tự động set timestamp.

```yaml
# DSL YAML — file dsl.yml
entities:
    - id: Product
      description: "Sản phẩm trong catalogue"
      fields:
          - name: id
            type: uuid
            primary_key: true
          - name: name
            type: string
            length: 255
            nullable: false
          - name: price
            type: decimal
            precision: 10
            scale: 2
          - name: category
            type: enum
            enum_values: ["electronics", "clothing", "food", "furniture"]
          - name: created_at
            type: datetime
            server_default: "NOW()"
      constraints:
          - type: check
            fields: [price]
            condition: "price >= 0"
      indexes:
          - name: idx_product_category
            fields: [category]
      lifecycle:
          before_insert: set_created_at
```

**Kết quả emit FastAPI:**

```python
# → app/models/product.py (tự động generate)
class Product(Base):
    __tablename__ = "products"
    id: Mapped[UUID] = Column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = Column(String(255), nullable=False)
    price: Mapped[Decimal] = Column(Numeric(10, 2))
    category: Mapped[ProductCategory] = Column(String(50))
    # + CheckConstraint, Index, lifecycle hook
```

**Dùng Recipe thay thế:**

```python
entity = SimpleEntityRecipe(
    name="Product",
    extra_fields=[
        Field(name="price", field_type=FieldType.DECIMAL, precision=10, scale=2),
        Field(name="category", field_type=FieldType.ENUM,
              enum_values=["electronics", "clothing", "food", "furniture"]),
    ],
    with_tenant=True,        # → auto thêm tenant_id field
    with_lifecycle_hooks=True,  # → auto thêm created_at/updated_at hooks
)
```

---

### 2. Command-Query Separation (CQRS) — Write/Read tách biệt

**Khi nào dùng:** Khi cần enforce separation of concerns — write operation có validation/guard/transaction, read operation có pagination/filter/projection.

**Trường hợp thực tế:** Command `CreateOrder` phải kiểm tra KYC (nếu user mới), có transaction, và emit event `OrderCreated`.

```python
cmd = CQRSCommandRecipe(
    name="CreateOrder",
    entity="Order",
    permission="order.create",
    input_fields=[
        CommandField(name="product_id", field_type=CommandFieldType.UUID, required=True),
        CommandField(name="quantity", field_type=CommandFieldType.INTEGER, required=True, min_value=1),
        CommandField(name="note", field_type=CommandFieldType.STRING, max_length=500),
    ],
    emits_events=["OrderCreated"],
    transaction_required=True,  # → auto thêm BEGIN/COMMIT/ROLLBACK effects
)
# Tự động thêm:
# - CommandGuard(AUTH, "order.create")
# - CommandGuard(TENANT_SCOPE, mode="tenant_isolated")
# - CommandEffect(CREATE_RECORD, "Order")
# - CommandEffect(PUBLISH_EVENT, "OrderCreated")
# - on_error="rollback"
```

**Read side — Query với filter + pagination:**

```python
query = CQRSQueryRecipe(
    name="ListOrders",
    entity="Order",
    permission="order.read",
    pagination_type=PaginationType.OFFSET,
    page_size=20,
    default_sort_field="created_at",
    default_sort_direction=SortDirection.DESC,
    include_audit_log=True,  # → auto thêm WRITE_AUDIT_LOG effect
)
# Tự động thêm:
# - QueryGuard(AUTH, "order.read")
# - QueryGuard(TENANT_SCOPE)
# - PaginationConfig(OFFSET, page_size=20)
# - SortExpression(created_at, DESC)
```

---

### 3. Value Object — Domain primitive bất biến

**Khi nào dùng:** Khi cần model dữ liệu mà equality based on value (không phải identity), ví dụ: Money, Address, MoneyRange, Email.

**Trường hợp thực tế:** Hệ thống thanh toán cần VO `Money` với computed field `tax_amount` (formula = `subtotal * tax_rate`).

```yaml
# DSL YAML
value_objects:
    - id: Money
      description: "Tiền tệ với currency"
      fields:
          - name: amount
            type: decimal
            required: true
            precision: 15
            scale: 2
          - name: currency
            type: string
            required: true
            enum_values: ["USD", "EUR", "VND"]
    - id: MoneyWithTax
      description: "Tiền có tính thuế"
      extends: Money
      fields:
          - name: tax_rate
            type: decimal
            required: true
          - name: subtotal
            type: decimal
            required: true
```

**Code generate FastAPI (Python — frozen dataclass):**

```python
@dataclass(frozen=True)
class MoneyWithTax:
    amount: Decimal
    currency: str
    tax_rate: Decimal
    subtotal: Decimal

    @property
    def tax_amount(self) -> Decimal:
        return Decimal(str(self.subtotal * self.tax_rate))
```

**Code generate NestJS (TypeScript — class):**

```typescript
export class MoneyWithTax {
    readonly amount: number;
    readonly currency: string;
    readonly taxRate: number;
    readonly subtotal: number;

    get taxAmount(): number {
        return this.subtotal * this.taxRate;
    }
}
```

**VO Inheritance — child override parent fields:**

```python
# ValueObject.extends cho phép chain inheritance
# MoneyWithTax extends Money → merge fields từ parent + override/add child fields
# Circular inheritance tự động detect → raise error
```

---

### 4. Aggregate Root — Consistency boundary

**Khi nào dùng:** Khi nhiều entity liên quan nhau cần cùng consistency boundary (ví dụ: Order ↔ OrderItems).

**Trường hợp thực tế:** Order là aggregate root, OrderItem là child. Chỉ được truy cập OrderItem qua Order, không được truy cập trực tiếp.

```python
agg = AggregateRootRecipe(
    name="Order",
    root_entity="Order",
    child_entities=["OrderItem", "OrderShipping"],
    events=["OrderPlaced", "OrderCancelled", "OrderShipped"],
    invariants=[
        "total_amount >= 0",
        "len(items) > 0",
        "status in ('pending', 'confirmed', 'shipped', 'delivered')",
    ],
    consistency=ConsistencyLevel.STRICT,  # ACID trong boundary
)
```

**Luồng thực tế:** Khi user cancel order:

1. Command `CancelOrder` → vào Aggregate `Order`
2. Guard check: order có ở trạng thái cho phép cancel không? (invariant check)
3. Effect: UPDATE Order status + UPDATE tất cả OrderItems status
4. Emit event `OrderCancelled`
5. Tất cả trong 1 transaction (STRICT consistency)

---

### 5. Domain Events — Event-driven communication

**Khi nào dùng:** Khi cần notify các phần khác của hệ thống mà không coupling trực tiếp.

**3 loại event:**

| Loại           | Ý nghĩa                   | Ví dụ                               |
| -------------- | ------------------------- | ----------------------------------- |
| `FACT`         | Đã xảy ra, không thể undo | `OrderPlaced`, `PaymentReceived`    |
| `INTENTION`    | Ý định, có thể bị hủy     | `OrderCancelled`, `PaymentRefunded` |
| `STATE_CHANGE` | Thay đổi trạng thái       | `OrderShipped`, `UserDeactivated`   |

```yaml
# DSL YAML
entities:
    - id: Order
commands:
    - id: CreateOrder
      emits:
          - OrderPlaced # FACT — đã đặt hàng, không undo được
events:
    - id: OrderPlaced
      event_type: fact
      aggregate_id: Order
      fields:
          - name: order_id
            type: uuid
          - name: total_amount
            type: decimal
    - id: OrderCancelled
      event_type: intention # ý định hủy — có thể restore
      aggregate_id: Order
    - id: OrderShipped
      event_type: state_change # trạng thái thay đổi
      aggregate_id: Order
```

---

### 6. CQRS Projection — Read model tối ưu

**Khi nào dùng:** Khi write model (Order, OrderItem) không phù hợp cho read — cần read model denormalized.

**Trường hợp thực tế:** Dashboard cần hiển thị `OrderSummary` (flatten Order + OrderItems + User info) thay vì join 3 bảng.

```python
proj = ProjectionRecipe(
    name="OrderSummary",
    source_aggregate="Order",
    source_events=["OrderPlaced", "OrderShipped"],
    fields=[
        Field(name="order_id", field_type=FieldType.UUID),
        Field(name="user_name", field_type=FieldType.STRING),
        Field(name="total", field_type=FieldType.DECIMAL),
        Field(name="status", field_type=FieldType.STRING),
        Field(name="item_count", field_type=FieldType.INTEGER),
        Field(name="shipped_at", field_type=FieldType.DATETIME),
    ],
    projection_type=ProjectionType.DENORMALIZED,
)
```

**4 loại projection:**

| Loại                | Use case                                        |
| ------------------- | ----------------------------------------------- |
| `DENORMALIZED`      | Dashboard, report — flatten data                |
| `MATERIALIZED_VIEW` | Query phức tạp, compute trước cache             |
| `SEARCH_INDEX`      | Elasticsearch/OpenSearch — full-text search     |
| `GRAPH`             | Relationship query — "who bought same products" |

---

### 7. Event Sourcing — Reconstruct state từ event log

**Khi nào dùng:** Khi cần audit trail 100% state changes, hoặc cần "time travel" (replay events để xem state ở thời điểm bất kỳ).

**Trường hợp thực tế:** Tài chính (BankAccount) — mọi giao dịch là event, state hiện tại = sum của tất cả events.

```python
agg = EventSourcedAggregateRecipe(
    name="BankAccount",
    root_entity="BankAccount",
    events=["Deposited", "Withdrawn", "TransferredOut", "TransferredIn"],
    snapshot_interval=100,  # lưu snapshot mỗi 100 events
    versioned=True,          # optimistic concurrency control
)
# eventing_strategy = SNAPSHOT
# → mỗi 100 events, snapshot lại state để tránh replay tất cả events từ đầu
```

**3 chiến lược eventing:**

| Chiến lược    | Khi nào dùng                                      |
| ------------- | ------------------------------------------------- |
| `APPEND_ONLY` | Chỉ thêm events mới, không bao giờ xóa/update     |
| `SNAPSHOT`    | Periodic snapshot + events từ snapshot (mặc định) |
| `COMPRESSION` | Compress events cũ thành snapshot tự động         |

---

### 8. Temporal Entity — Time-bounded data (SCD Type 2)

**Khi nào dùng:** Khi cần track history của dữ liệu thay đổi theo thời gian.

**Trường hợp thực tế:** Giá sản phẩm thay đổi theo thời gian — cần biết giá của sản phẩm tại bất kỳ thời điểm nào.

```python
temporal = TemporalEntityRecipe(
    name="ProductPrice",
    extra_fields=[
        Field(name="product_id", field_type=FieldType.UUID),
        Field(name="price", field_type=FieldType.DECIMAL, precision=10, scale=2),
    ],
    granularity=TemporalGranularity.DAY,  # tracking theo ngày
    valid_from_field="valid_from",
    valid_to_field="valid_to",
)
# Tự động thêm:
# - valid_from (DATETIME, nullable=False)
# - valid_to (DATETIME, nullable=True) — NULL = bản ghi hiện tại
# - current_predicate = "valid_to IS NULL"
# - Index trên (product_id, valid_from, valid_to)

# Query: "Giá của product P123 tại ngày 2025-01-15?"
# → SELECT * FROM product_prices
#   WHERE product_id = 'P123'
#   AND '2025-01-15' BETWEEN valid_from AND COALESCE(valid_to, '9999-12-31')
```

---

### 9. Polymorphic Entity — Inheritance trong database

**Khi nào dùng:** Khi có base entity + nhiều subtype với fields khác nhau.

**Trường hợp thực tế:** Payment có nhiều loại: CreditCard, BankTransfer, Crypto — mỗi loại có fields khác nhau.

```python
poly = PolymorphicEntityRecipe(
    name="Payment",
    subtypes=[
        {"name": "CreditCardPayment", "fields": [
            Field(name="card_number", field_type=FieldType.STRING, length=19),
            Field(name="expiry", field_type=FieldType.STRING, length=7),
        ]},
        {"name": "BankTransferPayment", "fields": [
            Field(name="account_number", field_type=FieldType.STRING),
            Field(name="bank_name", field_type=FieldType.STRING),
        ]},
        {"name": "CryptoPayment", "fields": [
            Field(name="wallet_address", field_type=FieldType.STRING),
            Field(name="tx_hash", field_type=FieldType.STRING),
        ]},
    ],
    polymorphism_type=PolymorphismType.SINGLE_TABLE,  # 1 bảng, discriminator column
    discriminator_field="payment_type",
)
```

**3 loại polymorphism:**

| Loại                   | Database design                 | Khi nào dùng                        |
| ---------------------- | ------------------------------- | ----------------------------------- |
| `SINGLE_TABLE` (STI)   | 1 bảng, discriminator column    | Số subtype ít, fields overlap nhiều |
| `JOINED_TABLE` (CTI)   | Mỗi subtype 1 bảng, join qua PK | Fields subtype rất khác nhau        |
| `CONCRETE_TABLE` (JTI) | Mỗi subtype 1 bảng độc lập      | Không cần query across all types    |

---

### 10. Saga — Long-running transaction

**Khi nào dùng:** Khi transaction trải dài qua nhiều aggregate/service, không thể dùng 1 DB transaction duy nhất.

**Trường hợp thực tế:** Order fulfillment — ReserveInventory → ProcessPayment → ShipOrder. Nếu bước nào fail, compensating steps tự động rollback.

```python
saga = SagaRecipe(
    name="OrderFulfillment",
    steps=[
        SagaStep(
            name="ReserveInventory",
            action="reserve_inventory",
            compensating_action="release_inventory",
            compensating_type=CompensatingActionType.UNDO,
            on_success_event="InventoryReserved",
            on_failure_event="InventoryReservationFailed",
        ),
        SagaStep(
            name="ProcessPayment",
            action="process_payment",
            compensating_action="refund_payment",
            compensating_type=CompensatingActionType.UNDO,
            on_success_event="PaymentProcessed",
            on_failure_event="PaymentFailed",
        ),
        SagaStep(
            name="ShipOrder",
            action="ship_order",
            compensating_action="recall_shipment",
            compensating_type=CompensatingActionType.NOTIFY,  # gửi notify, không undo được
            on_success_event="OrderShipped",
            on_failure_event="ShippingFailed",
        ),
    ],
    orchestration=SagaOrchestration.ORCHESTRATION,  # orchestrator trung tâm
    timeout_seconds=3600,  # 1 giờ
)
```

**3 loại compensating action:**

| Loại     | Hành vi                                     |
| -------- | ------------------------------------------- |
| `UNDO`   | Reverse operation (cancel, refund, release) |
| `NOOP`   | Không làm gì (idempotent)                   |
| `NOTIFY` | Gửi notification về failure                 |

**2 chế độ orchestration:**

| Chế độ          | Mô tả                                            |
| --------------- | ------------------------------------------------ |
| `ORCHESTRATION` | Orchestrator trung tâm điều khiển sequence       |
| `CHOREOGRAPHY`  | Mỗi event trigger step tiếp theo (decentralized) |

---

### 11. Guard & Effect — Security + Side Effects

**Khi nào dùng:** Command phải enforce security (AUTH, TENANT, KYC, AML, HIPAA) và có side effects (CRUD, Event, Email, Audit).

**11 Guard types — ví dụ thực tế:**

| Guard               | Domain               | Trường hợp dùng                                   |
| ------------------- | -------------------- | ------------------------------------------------- |
| `AUTH`              | Mọi hệ thống         | Check permission trước execute command            |
| `TENANT_SCOPE`      | Multi-tenant         | Isolate data theo tenant                          |
| `RATE_LIMIT`        | API                  | Limit 100 requests/60s                            |
| `KYC_CHECK`         | Banking (RX03)       | User đã verified identity chưa?                   |
| `AML_SCREENING`     | Banking (RX03)       | Transaction có nghi ngờ rửa tiền?                 |
| `HIPAA_ACCESS`      | Healthcare (RX04)    | User có clearance đọc bệnh án?                    |
| `GDPR_CONSENT`      | EU Compliance        | User đã consent xử lý dữ liệu?                    |
| `PCI_RESTRICT`      | Payment (PCI-DSS)    | Restrict access to cardholder data                |
| `FRAUD_DETECTION`   | Payment (DP12)       | Velocity check, amount threshold, pattern anomaly |
| `SAFETY_CHECK`      | Manufacturing (DP05) | Equipment safe? Personnel certified?              |
| `CLAIMS_VALIDATION` | Insurance (DP14)     | Policy covered? In period? Within limit?          |

**Ví dụ KYC + AML guard trong banking:**

```python
cmd = Command(
    id="TransferMoney",
    input=[...],
    guards=[
        CommandGuard(guard_type=GuardType.AUTH, permission="account.transfer"),
        CommandGuard(guard_type=GuardType.TENANT_SCOPE, mode="tenant_isolated"),
        CommandGuard(guard_type=GuardType.KYC_CHECK),           # check user đã KYC chưa
        CommandGuard(guard_type=GuardType.AML_SCREENING),       # check transaction có suspicious chưa
        CommandGuard(guard_type=GuardType.FRAUD_DETECTION,
                     limit=10, window="1h",  # max 10 transfers/hour
                     condition=10000),       # max $10,000 per transfer
    ],
    effects=[
        CommandEffect(effect_type=EffectType.UPDATE_RECORD, entity="Account"),
        CommandEffect(effect_type=EffectType.PUBLISH_EVENT, event="MoneyTransferred"),
        CommandEffect(effect_type=EffectType.WRITE_AUDIT_LOG, audit_action="transfer"),
        CommandEffect(effect_type=EffectType.RECORD_METRIC,
                      metric_name="transfer.duration", metric_value=1),
    ],
    transaction_required=True,
)

# Runtime:
guards = CommandGuards(cmd, auth_service, tenant_service, compliance_service)
await guards.check_all(data={"amount": 5000, "to_account": "ACC_123"}, user_id="U1")
# Thứ tự check: AUTH → TENANT → KYC → AML → FRAUD → HIPAA → SAFETY → CLAIMS
# (thứ tự thực phụ thuộc vào thứ tự guard trong command.guards list)
# Mỗi compliance guard → audit log (KPI-029)
```

**17 Effect types — nhóm chính:**

| Nhóm          | Effects                                          | Ví dụ                                                  |
| ------------- | ------------------------------------------------ | ------------------------------------------------------ |
| CRUD          | CREATE, UPDATE, DELETE                           | `repositories["Order"].create(data)`                   |
| Extended      | QUERY_RECORDS, UPSERT                            | `repositories["Order"].upsert(data)`                   |
| Transaction   | BEGIN, COMMIT, ROLLBACK                          | `TransactionManagerSQL` nested TX                      |
| Event         | PUBLISH_EVENT                                    | `event_bus.publish({"type": "OrderCreated", ...})`     |
| Integration   | CALL_EXTERNAL_API, SEND_EMAIL, SEND_SMS, WEBHOOK | `notification_service.send_email(...)`                 |
| Observability | WRITE_AUDIT_LOG, RECORD_METRIC                   | `audit_service.log(...)`, `MetricRegistry.record(...)` |
| Compliance    | CHECK_COMPLIANCE, MASK_PII                       | PHI masking, compliance check                          |

---

### 12. Query — Filter + Aggregation + HIPAA Masking

**Khi nào dùng:** Read operation với filter, pagination, projection, aggregation.

**Trường hợp thực tế:** Dashboard HIPAA — query patient records, auto-mask dữ liệu nhạy cảm.

```python
# Filter expression
filters = parse_filters({
    "status": {"eq": "active"},
    "created_at": {"gte": "2025-01-01"},
    "diagnosis": {"ilike": "%flu%"},
})

# FilterGroup nested AND/OR
filter_group = FilterGroup(
    operator="and",
    filters=[
        FilterExpression(field="status", operator=FilterOp.EQ, value="active"),
        FilterGroup(
            operator="or",
            filters=[
                FilterExpression(field="priority", operator=FilterOp.EQ, value="high"),
                FilterExpression(field="patient_id", operator=FilterOp.IN, value=["P1", "P2", "P3"]),
            ],
        ),
    ],
)
# → SQL: status = 'active' AND (priority = 'high' OR patient_id IN ('P1','P2','P3'))

# Aggregation Query
agg_query = AggregationQuery(
    id="CountOrdersByStatus",
    reads_from="Order",
    aggregation=AggregationConfig(
        function=AggFunction.COUNT,
        group_by=["status"],
    ),
    filters=[
        FilterExpression(field="created_at", operator=FilterOp.GTE, value="2025-01-01"),
    ],
)

# HIPAA PHI Masking
phi_config = PHIMaskingConfig(
    enabled=True,
    mask_patterns=["^ssn$", "^medicaid_id$", "^diagnosis$"],
    allowed_fields=["patient_name", "age"],  # fields được phép expose
    default_mask_value="***",
)
phi_config.should_mask("ssn")        # → True
phi_config.should_mask("patient_name")  # → False (trong allowed_fields)
phi_config.should_mask("medicaid_id")  # → True (built-in detection)
phi_config.mask_value("ssn", "123-45-6789")  # → "***"
```

**13 Filter operators:**
`eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`, `like`, `ilike`, `between`, `is_null`, `is_not_null`

---

### 13. Global Error Handler — Centralized error handling

**Khi nào dùng:** Cần centralized exception mapping → HTTP response với logging/notification.

**Trường hợp thực tế:** Production app cần map `ConnectionError` → 503, `ValueError` → 400, và notify Slack khi có error.

```python
error_config = GlobalErrorHandlerRecipe(
    name="AppErrorHandler",
    strategy=ErrorHandlingStrategy.FALLBACK,
    log_level=ErrorLevel.ERROR,
    include_stack_trace=False,  # không expose stack trace cho client
    with_logging=True,
    with_notification=True,
    common_mappers=True,  # auto thêm 6 mappers: ValueError→400, KeyError→404, v.v.
    # Logging:
    # - format: structured
    # - destination: stdout
    # - redact: password, token, ssn, credit_card, api_key
    # Notification:
    # - notify_on: ERROR level
    # - slack_webhook: ""
    # - sentry_dsn: ""
    # - rate_limit: 50/hour
)
# → Trả về dict: {
#   "handler": GlobalErrorHandler(...),
#   "mappers": [6 ErrorMapper instances],
#   "logging_config": ErrorLoggingConfig(...),
#   "notification_config": ErrorNotificationConfig(...),
# }
```

**6 mappers mặc định:**

| Exception         | HTTP Status | Error Code          | Retryable |
| ----------------- | ----------- | ------------------- | --------- |
| `ValueError`      | 400         | INVALID_INPUT       | ❌        |
| `KeyError`        | 404         | NOT_FOUND           | ❌        |
| `PermissionError` | 403         | FORBIDDEN           | ❌        |
| `TypeError`       | 500         | INTERNAL_ERROR      | ❌        |
| `ConnectionError` | 503         | SERVICE_UNAVAILABLE | ✅        |
| `TimeoutError`    | 504         | GATEWAY_TIMEOUT     | ✅        |

---

### 14. Computed Field — Formula evaluation trong VO

**Khi nào dùng:** VO có field được tính tự động từ các field khác.

**Trường hợp thực tế:** Invoice VO có `total_amount = unit_price * quantity` và `vat_amount = subtotal * 0.1`.

```python
# Runtime — evaluate formula
evaluator = ComputedFieldEvaluator()
result = evaluator.evaluate(
    formula="self.unit_price * self.quantity",
    values={"unit_price": Decimal("100"), "quantity": 5},
    depends_on=["unit_price", "quantity"],
)  # → Decimal("500")

# Code generate — Python
python_code = evaluator.generate_python_code(
    field_name="total_amount",
    field_type="decimal",
    formula="self.unit_price * self.quantity",
    depends_on=["unit_price", "quantity"],
)
# →
# @property
# def total_amount(self) -> Decimal:
#     return Decimal(str(self.unit_price * self.quantity))

# Code generate — TypeScript (self. → this., snake_case → camelCase)
ts_code = evaluator.generate_typescript_code(
    field_name="total_amount",
    field_type="decimal",
    formula="self.unit_price * self.quantity",
    depends_on=["unit_price", "quantity"],
)
# →
# get totalAmount(): number {
#     return this.unitPrice * this.quantity;
# }
```

**Sandboxed — chỉ cho phép:** `abs`, `round`, `min`, `max`, `sum`, `len`, `pow`, `int`, `float`, `str`, `bool`

---

## Cách sử dụng từ pack khác

### 1. Import models

```python
from midicoder.packs.cp_base_domain_model import (
    Entity, EntityField, FieldType,
    Command, CommandField, GuardType, EffectType,
    Query, FilterOp,
    ValueObject, VOFieldType,
)
```

### 2. Dùng Recipe để tạo entity/command/VO pre-configured

```python
from midicoder.packs.cp_base_domain_model import (
    SimpleEntityRecipe,
    CQRSCommandRecipe,
    CQRSQueryRecipe,
    ValueObjectRecipe,
    AggregateRootRecipe,
    SagaRecipe,
)

# Tạo CRUD entity với tenant + audit
entity = SimpleEntityRecipe(
    name="Invoice",
    with_tenant=True,
    with_lifecycle_hooks=True,
)

# Tạo command với guard + transaction
cmd = CQRSCommandRecipe(
    name="CreateInvoice",
    entity="Invoice",
    permission="invoice.create",
    transaction_required=True,
)

# Tạo query với pagination
query = CQRSQueryRecipe(
    name="ListInvoices",
    entity="Invoice",
    permission="invoice.read",
    pagination_type="offset",
    page_size=20,
)
```

### 3. Parse YAML DSL

```python
from midicoder.packs.cp_base_domain_model import EntityParser, CommandParser, ValueObjectParser

yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: email
        type: string
        unique: true
        length: 255
"""
parser = EntityParser()
entities = parser.parse(yaml_content)
```

### 4. Emit code

```python
from pathlib import Path
from midicoder.packs.cp_base_domain_model import FastAPIEntityEmitter, NestJSEntityEmitter

# FastAPI
emitter = FastAPIEntityEmitter(stack_dir=Path("midicoder/stacks/fastapi/cp_base_domain_model"))
code = emitter.emit(entity, all_entities)  # → SQLAlchemy model Python code

# NestJS
emitter = NestJSEntityEmitter(stack_dir=Path("midicoder/stacks/nestjs/cp_base_domain_model"))
code = emitter.emit(entity, all_entities)  # → TypeORM entity TypeScript code
```

### 5. Dùng Guard và Effect

```python
from midicoder.packs.cp_base_domain_model import CommandGuards, CommandEffects

guards = CommandGuards(command, auth_service, tenant_service, compliance_service)
await guards.check_all(user_id="u1", tenant_id="t1")

effects = CommandEffects(command, repositories, event_bus, notification_service, audit_service)
result = await effects.execute(context)
```

---

## Cách B01 được render ra output app

### Luồng pipeline

```
DSL YAML file
    │
    ▼
Parser (EntityParser/CommandParser/QueryParser/VO Parser)
    │
    ▼
Typed Dataclass (Entity/Command/Query/ValueObject)
    │
    ▼
PackEmitterRouter.dispatch(key, stack)  →  tìm emitter phù hợp
    │
    ├── FastAPI → FastAPIEntityEmitter  → Jinja2 template `entity.py.jinja2`  → SQLAlchemy model code
    │                                              `command.py.jinja2`      → Command dataclass + handler
    │                                              `query.py.jinja2`        → Query dataclass + handler
    │                                              `value_object.py.jinja2` → Frozen dataclass
    │                                              `error_handler.py.jinja2`→ Global middleware
    │
    └── NestJS  → NestJSEntityEmitter   → Jinja2 template `entity.ts.jinja2`  → TypeORM entity
                                               `command.ts.jinja2`      → Command class + handler
                                               `query.ts.jinja2`        → Query DTO + handler
                                               `value-object.ts.jinja2` → VO class
                                               `exception.filter.ts.jinja2` → Global exception filter
```

### 45 template Jinja2

| Stack       | Số file | Loại                                                                                                                                                                                                                                                                    |
| ----------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FastAPI** | 20      | `entity.py`, `command.py/handler/validator/guards/effects/errors`, `query.py/handler/validator/guards/effects/output/aggregation`, `value_object.py`, `error_handler.py`, `problem_details.py`, `validation_decorator.py`, `input_sanitizer.py`, `__init__.py`          |
| **NestJS**  | 21      | `entity.ts`, `command.ts/handler/validator/guards/effects/errors/module`, `query.ts/handler/validator/guards/effects/output/aggregation`, `value-object.ts`, `exception.filter.ts`, `problem-details.dto.ts`, `validation.pipe.ts`, `sanitization.utils.ts`, `index.ts` |
| **Angular** | 2       | `error-interceptor.service.ts`, `validation.module.ts`                                                                                                                                                                                                                  |
| **React**   | 2       | `error-boundary.tsx`, `use-validation.ts`                                                                                                                                                                                                                               |

### File contributions (trong pack.yml)

Mỗi entity/command/query/VO được declare trong DSL sẽ sinh ra:

- **Per entity:** 1 file model (FastAPI) hoặc 1 file entity (NestJS)
- **Per command:** 6 file × 2 stack = 12 files (command, handler, validator, guards, effects, errors)
- **Per query:** 7 file × 2 stack = 14 files (query, handler, validator, guards, effects, output, aggregation)
- **Per VO:** 1 file × 2 stack = 2 files
- **Infrastructure:** 15 files (one-time, không per-entity)

---

## Hạn chế đã biết

| Hạn chế                                            | Mức độ | Ghi chú                                                              |
| -------------------------------------------------- | ------ | -------------------------------------------------------------------- |
| `models.py` 2499 dòng quá lớn                      | Medium | Chưa split thành module con — scope P3                               |
| `entity_nestjs.py` dead import `IsString`          | Low    | Import nhưng không dùng trong generated code                         |
| `entity_nestjs.py` import typeorm tách rời         | Low    | 2 import statement cho cùng package                                  |
| `error-boundary.tsx.jinja2` inline style hardcoded | Low    | Fallback UI, không phải component business                           |
| `datetime.utcnow()` deprecated warning             | Low    | `command_guards.py` line 363 — nên dùng `datetime.now(datetime.UTC)` |
| `vo_computed.py` sandboxed `eval()`                | Medium | Safe nhưng không cho phép function phức tạp ngoài whitelist          |
| `vo_types.py` decimal → `number` trong TypeScript  | Low    | Mất precision, nên dùng `decimal.js`                                 |
| `get_table_name()` plural hóa đơn giản             | Low    | Chỉ append "s", không xử lý box→boxes, child→children                |

---

## Ưu điểm

| Ưu điểm                  | Chi tiết                                                                                             |
| ------------------------ | ---------------------------------------------------------------------------------------------------- |
| **Đầy đủ DDD**           | 14 definitions cover từ basic (Entity, VO) đến advanced (Saga, EventSourcing, Temporal, Polymorphic) |
| **Dual-stack**           | FastAPI (SQLAlchemy) và NestJS (TypeORM) song song, symmetric design                                 |
| **Template + fallback**  | Mỗi emitter ưu tiên Jinja2 template, fallback inline nếu template không tồn tại                      |
| **Recipe pattern**       | 11 factory functions với default hợp lý (tenant isolation, audit, strict consistency)                |
| **Compliance-ready**     | 11 guard types bao gồm KYC, AML, HIPAA, GDPR, PCI, FRAUD, SAFETY, CLAIMS + audit logging             |
| **Sandboxed formula**    | VO computed field dùng sandboxed eval, không cho `__import__`, `exec`, `open`                        |
| **VO inheritance**       | Support extends chain, circular detection, deep merge fields/methods/rules                           |
| **Dual-path VO emitter** | Python (`def method(self)`) và TypeScript (`throw new Error(...)`) tách biệt                         |
| **Test coverage cao**    | 677 test cases, ~9,500 dòng test code, bao phủ parser/emitter/guard/effect/recipe                    |
| **Tenant isolation**     | Build-in multi-tenant trong Command (tenant_scope), Query, Guard, Recipe                             |
| **HIPAA PHI masking**    | `PHIMaskingConfig` với `should_mask()` và `mask_value()`                                             |

---

## Boundary với pack khác (Overlap)

| Capability        | B01 giữ                                                 | Pack khác giữ                                    |
| ----------------- | ------------------------------------------------------- | ------------------------------------------------ |
| `event_sourcing`  | DSL definition (`EventSourcedAggregate` model) + Recipe | **C02** giữ runtime (EventStore, CQRSProjection) |
| `cqrs_projection` | DSL definition (`Projection` model) + Recipe            | **C02** giữ runtime implementation               |
| `saga`/`SagaStep` | Domain-level saga (compensating action)                 | **F20** giữ orchestration-level saga             |
| `entity_modeling` | DSL model + Recipe                                      | **BE01** giữ entity_generation (repository)      |

**Quy tắc:** B01 chỉ giữ DSL definition + Recipe. Runtime implementation thuộc pack chuyên sâu.

---

## Testing

### Chạy toàn bộ test suite

```bash
python -m pytest midicoder/packs/cp_base_domain_model/tests/ -v
```

**Target: 677/677 passed.**

### Coverage theo module

| Module                                                     | Số file test | Coverage ước tính |
| ---------------------------------------------------------- | ------------ | ----------------- |
| Entity (parser + models + emitter)                         | 3 files      | ~95%              |
| Command (parser + emitter + guards + effects + compliance) | 5 files      | ~90%              |
| ValueObject (parser + core + FastAPI + NestJS + tenant)    | 6 files      | ~90%              |
| Query (emitter + parser)                                   | 1 file       | ~85%              |
| Recipes                                                    | 1 file       | ~95%              |
| Error Handler                                              | 1 file       | ~95%              |
| Pipeline/Router                                            | 2 files      | ~85%              |

### Test đặc biệt

| File                           | Mục đích                                              |
| ------------------------------ | ----------------------------------------------------- |
| `test_command_guards_p2.py`    | 48 tests cho FRAUD, SAFETY, CLAIMS guard              |
| `test_command_compliance.py`   | 30 tests cho RX02 Financial, RX03 AML/KYC, RX04 HIPAA |
| `test_value_objects_tenant.py` | 9 tests cho tenant isolation trong VO                 |
| `test_command_effects.py`      | 35+ tests cho 17 effect types                         |
| `test_recipes.py`              | 60+ tests cho tất cả 11 recipe                        |

---

## Error Codes

B01 dùng prefix `ErrorCode.CP01_*` (defined trong `midicoder/errors.py`):

| Range                 | Purpose                                                                             |
| --------------------- | ----------------------------------------------------------------------------------- |
| `CP01_001`–`CP01_010` | Entity (NOT_FOUND, INVALID_FIELD, RELATIONSHIP, CONSTRAINT, LIFECYCLE, EMIT)        |
| `CP01_011`–`CP01_020` | ValueObject (NOT_FOUND, INVALID_FIELD_TYPE, TEMPLATE_NOT_FOUND, EMIT_FAILED, v.v.)  |
| `CP01_021`–`CP01_027` | Command (NOT_FOUND, INVALID_INPUT, GUARD_FAILED, EMIT_FAILED)                       |
| `CP01_028`–`CP01_035` | Query (NOT_FOUND, INVALID_FILTER, INVALID_PAGINATION, EMIT_FAILED)                  |
| `CP01_052`–`CP01_055` | Guard (TENANT_MISSING, TENANT_VIOLATION, USER_NOT_AUTHENTICATED, PERMISSION_DENIED) |
| `CP01_057`–`CP01_087` | Compliance Guard (KYC, AML, HIPAA, GDPR, PCI, FRAUD, SAFETY, CLAIMS)                |
| `CP01_062`–`CP01_066` | Transaction (NOT_ACTIVE, COMMIT_FAILED, ROLLBACK_FAILED)                            |
| `CP01_088`–`CP01_099` | Effect (DOUBLE_ENTRY_MISMATCH, PAYMENT_FAILED, v.v.)                                |

---

## Maintainance

### Khi thêm field type mới

1. Thêm vào `EntityFieldType` enum trong `models.py`
2. Thêm vào `_parse_field_type()` trong `entity_parser.py`
3. Thêm type mapping trong `entity_fastapi.py` (`_get_field_imports`, `_get_type_annotation`, `_get_sqlalchemy_type`)
4. Thêm type mapping trong `entity_nestjs.py` (`_get_typeScript_type`)
5. Thêm test vào `test_entity_parser.py` và `test_entity_emitter.py`

### Khi thêm guard type mới

1. Thêm vào `GuardType` enum trong `models.py`
2. Thêm method `_check_tenant_scope()` trong `command_guards.py`
3. Thêm dispatch trong `check_all()` method
4. Thêm error code vào `errors.py` (range `CP01_XXX`)
5. Thêm test vào `test_command_guards_p2.py` hoặc `test_command_compliance.py`

### Khi thêm effect type mới

1. Thêm vào `EffectType` enum trong `models.py`
2. Thêm method `_execute_{type_name}()` trong `command_effects.py`
3. Thêm dispatch trong `execute()` method
4. Thêm test vào `test_command_effects.py`

### Khi thêm recipe mới

1. Thêm function vào `recipes.py` với pattern `RecipeNameRecipe(name, ...)`
2. Export trong `__init__.py` và thêm vào `__all__`
3. Thêm vào `recipes` list trong `pack.yml`
4. Thêm test vào `test_recipes.py`
