# UAT Briefs — Capability: recipes

> Capability ID: `recipes` | CP B01: Domain Model DSL & IR Builder  
> Total: 20 briefs covering all 11 Recipe functions

---

### B01-REC-01: SimpleEntityRecipe for User (with_tenant=True, with_lifecycle_hooks=True)

**Capability:** `recipes`  
**Stack:** `fastapi`

**Use Case:** Create a multi-tenant User entity with full audit fields (tenant_id, created_at, updated_at) and lifecycle hooks for auto-setting timestamps on insert/update.

**Input DSL:**
```yaml
recipe:
  type: SimpleEntity
  name: User
  with_tenant: true
  with_lifecycle_hooks: true
  extra_fields:
    - name: email
      type: string
      nullable: false
      unique: true
      length: 255
    - name: display_name
      type: string
      nullable: false
      length: 100
```

**Expected Output:**
- File: `src/models/user.py`
- Contains: `class User` with fields: id (UUID), tenant_id, email, display_name, created_at, updated_at; lifecycle hooks: set_created_at (before_insert), set_updated_at (before_update)

---

### B01-REC-02: SimpleEntityRecipe for Product (with extra fields: price, description)

**Capability:** `recipes`  
**Stack:** `both`

**Use Case:** E-commerce product catalog entity with price (decimal) and description (text) fields, multi-tenant enabled.

**Input DSL:**
```yaml
recipe:
  type: SimpleEntity
  name: Product
  with_tenant: true
  with_lifecycle_hooks: true
  extra_fields:
    - name: sku
      type: string
      nullable: false
      unique: true
      length: 64
    - name: price
      type: decimal
      nullable: false
      precision: 10
      scale: 2
    - name: description
      type: text
      nullable: true
```

**Expected Output:**
- File: `src/models/product.py`
- Contains: `class Product` with fields: id, tenant_id, sku, price (DECIMAL(10,2)), description (TEXT), created_at, updated_at

---

### B01-REC-03: SimpleEntityRecipe minimal (with_tenant=False, with_lifecycle_hooks=False)

**Capability:** `recipes`  
**Stack:** `both`

**Use Case:** Minimal entity without multi-tenant isolation or lifecycle hooks — suitable for lookup/reference tables.

**Input DSL:**
```yaml
recipe:
  type: SimpleEntity
  name: CountryCode
  with_tenant: false
  with_lifecycle_hooks: false
  extra_fields:
    - name: code
      type: string
      nullable: false
      unique: true
      length: 2
    - name: name
      type: string
      nullable: false
      length: 100
```

**Expected Output:**
- File: `src/models/country_code.py`
- Contains: `class CountryCode` with fields: id, code, name (no tenant_id, no created_at/updated_at, no lifecycle hooks)

---

### B01-REC-04: AggregateRootRecipe for Order (STRICT, with OrderItem child)

**Capability:** `recipes`  
**Stack:** `fastapi`

**Use Case:** Order aggregate with strict consistency — Order and OrderItem must be modified atomically within the same transaction boundary.

**Input DSL:**
```yaml
recipe:
  type: AggregateRoot
  name: Order
  root_entity: Order
  child_entities:
    - OrderItem
  events:
    - OrderPlaced
    - OrderCancelled
    - OrderShipped
  consistency: strict
  invariants:
    - total_price >= 0
    - items must not be empty
```

**Expected Output:**
- File: `src/aggregates/order.py`
- Contains: `class OrderAggregate` with root_entity=Order, child_entities=[OrderItem], consistency=STRICT, 3 events, 2 invariants

---

### B01-REC-05: AggregateRootRecipe for Patient (EVENTUAL, with Visit child)

**Capability:** `recipes`  
**Stack:** `nestjs`

**Use Case:** Healthcare patient aggregate with eventual consistency — Patient and Visit can eventually sync, allowing concurrent updates without blocking.

**Input DSL:**
```yaml
recipe:
  type: AggregateRoot
  name: Patient
  root_entity: Patient
  child_entities:
    - Visit
  events:
    - PatientRegistered
    - VisitRecorded
    - DischargeCompleted
  consistency: eventual
  invariants:
    - active_visits <= 1
```

**Expected Output:**
- File: `src/aggregates/patient.ts`
- Contains: `class PatientAggregate` with root_entity=Patient, child_entities=[Visit], consistency=EVENTUAL, 3 events

---

### B01-REC-06: TemporalEntityRecipe for ProductPrice (DAY granularity)

**Capability:** `recipes`  
**Stack:** `fastapi`

**Use Case:** Track product price changes over time with daily granularity — supports querying price at any historical date.

**Input DSL:**
```yaml
recipe:
  type: TemporalEntity
  name: ProductPrice
  granularity: day
  valid_from_field: valid_from
  valid_to_field: valid_to
  extra_fields:
    - name: product_id
      type: uuid
      nullable: false
    - name: price
      type: decimal
      nullable: false
      precision: 10
      scale: 2
    - name: currency
      type: string
      nullable: false
      length: 3
```

**Expected Output:**
- File: `src/models/product_price.py`
- Contains: TemporalEntity ProductPrice with valid_from/valid_to (DATETIME), DAY granularity, current_predicate="valid_to IS NULL"

---

### B01-REC-07: TemporalEntityRecipe for EmployeeSalary (MONTH granularity, extra fields)

**Capability:** `recipes`  
**Stack:** `both`

**Use Case:** HR system tracks employee salary changes with monthly granularity — effective date tracking for compensation history.

**Input DSL:**
```yaml
recipe:
  type: TemporalEntity
  name: EmployeeSalary
  granularity: month
  valid_from_field: effective_date
  valid_to_field: end_date
  extra_fields:
    - name: employee_id
      type: uuid
      nullable: false
    - name: base_salary
      type: decimal
      nullable: false
      precision: 12
      scale: 2
    - name: bonus_percentage
      type: float
      nullable: true
    - name: currency
      type: string
      nullable: false
      length: 3
      default: USD
```

**Expected Output:**
- File: `src/models/employee_salary.py`
- Contains: TemporalEntity with custom valid_from_field=effective_date, valid_to_field=end_date, MONTH granularity, current_predicate="end_date IS NULL"

---

### B01-REC-08: CQRSCommandRecipe for CreateOrder (auth guard, create category, transaction)

**Capability:** `recipes`  
**Stack:** `fastapi`

**Use Case:** Command to create a new order with authentication guard, tenant scope isolation, and transaction wrapping for data integrity.

**Input DSL:**
```yaml
recipe:
  type: CQRSCommand
  name: CreateOrder
  entity: Order
  permission: order.create
  category: create
  transaction_required: true
  emits_events:
    - OrderPlaced
  input_fields:
    - name: customer_id
      type: uuid
      required: true
    - name: item_count
      type: integer
      required: true
      min: 1
```

**Expected Output:**
- File: `src/commands/create_order.py`
- Contains: Command with guards=[AUTH(order.create), TENANT_SCOPE], effects=[create_record(Order), publish_event(OrderPlaced)], transaction_required=True

---

### B01-REC-09: CQRSCommandRecipe for UpdateUser (auth guard, update category, emits events)

**Capability:** `recipes`  
**Stack:** `both`

**Use Case:** Command to update user profile with authentication, tenant isolation, and event emission for audit trail.

**Input DSL:**
```yaml
recipe:
  type: CQRSCommand
  name: UpdateUser
  entity: User
  permission: user.update
  category: update
  transaction_required: true
  emits_events:
    - UserUpdated
  input_fields:
    - name: user_id
      type: uuid
      required: true
    - name: display_name
      type: string
      required: false
      length: 100
    - name: email
      type: string
      required: false
      length: 255
```

**Expected Output:**
- File: `src/commands/update_user.py`
- Contains: Command with update_record effect, publish_event(UserUpdated), AUTH guard with user.update permission

---

### B01-REC-10: CQRSCommandRecipe for DeleteProduct (delete category, no transaction)

**Capability:** `recipes`  
**Stack:** `nestjs`

**Use Case:** Soft-delete product command with auth guard but no transaction wrapping — suitable for single-entity deletion.

**Input DSL:**
```yaml
recipe:
  type: CQRSCommand
  name: DeleteProduct
  entity: Product
  permission: product.delete
  category: delete
  transaction_required: false
  emits_events:
    - ProductDeleted
  input_fields:
    - name: product_id
      type: uuid
      required: true
```

**Expected Output:**
- File: `src/commands/delete_product.ts`
- Contains: NestJS Command with delete_record effect, publish_event(ProductDeleted), transaction_required=False

---

### B01-REC-11: CQRSQueryRecipe for GetOrders (pagination, sort, audit log)

**Capability:** `recipes`  
**Stack:** `fastapi`

**Use Case:** Query to list user orders with offset pagination, default sort by creation date descending, and audit log tracking.

**Input DSL:**
```yaml
recipe:
  type: CQRSQuery
  name: GetOrders
  entity: Order
  permission: order.read
  pagination_type: offset
  page_size: 20
  default_sort_field: created_at
  default_sort_direction: desc
  include_audit_log: true
  input_fields:
    - name: status
      type: string
      required: false
    - name: min_date
      type: datetime
      required: false
```

**Expected Output:**
- File: `src/queries/get_orders.py`
- Contains: Query with OFFSET pagination (page_size=20), sort=created_at DESC, WRITE_AUDIT_LOG effect, guards=[AUTH, TENANT_SCOPE]

---

### B01-REC-12: CQRSQueryRecipe for SearchProducts (cursor pagination, no audit log)

**Capability:** `recipes`  
**Stack:** `both`

**Use Case:** Product search query with cursor-based pagination for large catalogs, no audit logging for read-only search.

**Input DSL:**
```yaml
recipe:
  type: CQRSQuery
  name: SearchProducts
  entity: Product
  permission: product.read
  pagination_type: cursor
  page_size: 50
  default_sort_field: created_at
  default_sort_direction: desc
  include_audit_log: false
  input_fields:
    - name: q
      type: string
      required: true
      description: Search query
    - name: category
      type: string
      required: false
    - name: min_price
      type: decimal
      required: false
    - name: max_price
      type: decimal
      required: false
```

**Expected Output:**
- File: `src/queries/search_products.py`
- Contains: Query with CURSOR pagination (page_size=50), no audit log effect, 4 input filter fields

---

### B01-REC-13: EventSourcedAggregateRecipe for BankAccount (snapshot every 10, versioned)

**Capability:** `recipes`  
**Stack:** `fastapi`

**Use Case:** Bank account aggregate that reconstructs state from event log with snapshots every 10 events and versioned optimistic concurrency control.

**Input DSL:**
```yaml
recipe:
  type: EventSourcedAggregate
  name: BankAccount
  root_entity: BankAccount
  events:
    - Deposited
    - Withdrawn
    - Transferred
    - AccountClosed
  snapshot_interval: 10
  versioned: true
```

**Expected Output:**
- File: `src/aggregates/bank_account.py`
- Contains: EventSourcedAggregate with snapshot_interval=10, versioned=True, eventing_strategy=SNAPSHOT, 4 events

---

### B01-REC-14: EventSourcedAggregateRecipe for Portfolio (append-only, no snapshot)

**Capability:** `recipes`  
**Stack:** `both`

**Use Case:** Financial portfolio with append-only event log, no snapshots — full history preservation for regulatory compliance.

**Input DSL:**
```yaml
recipe:
  type: EventSourcedAggregate
  name: Portfolio
  root_entity: Portfolio
  events:
    - AssetAdded
    - AssetRemoved
    - AssetRebalanced
    - PortfolioValued
  snapshot_interval: 0
  versioned: true
```

**Expected Output:**
- File: `src/aggregates/portfolio.py`
- Contains: EventSourcedAggregate with eventing_strategy=APPEND_ONLY, snapshot_interval=0, versioned=True

---

### B01-REC-15: SagaRecipe for OrderFulfillment (4 steps, orchestration, 120s timeout)

**Capability:** `recipes`  
**Stack:** `fastapi`

**Use Case:** Order fulfillment saga with centralized orchestration — reserve inventory, charge payment, allocate warehouse, and ship, with 2-minute timeout.

**Input DSL:**
```yaml
recipe:
  type: Saga
  name: OrderFulfillment
  orchestration: orchestration
  timeout_seconds: 120
  steps:
    - name: ReserveInventory
      action: reserve_inventory
      compensating_action: release_inventory
      compensating_type: undo
      on_success_event: InventoryReserved
    - name: ChargePayment
      action: charge_payment
      compensating_action: refund_payment
      compensating_type: undo
      on_success_event: PaymentCharged
    - name: AllocateWarehouse
      action: allocate_warehouse
      compensating_action: release_warehouse
      compensating_type: undo
      on_success_event: WarehouseAllocated
    - name: ShipOrder
      action: ship_order
      compensating_action: cancel_shipment
      compensating_type: undo
      on_success_event: OrderShipped
```

**Expected Output:**
- File: `src/sagas/order_fulfillment_recipe.py`
- Contains: Saga with orchestration=orchestration, timeout_seconds=120, 4 SagaStep instances all with UNDO

---

### B01-REC-16: PolymorphicEntityRecipe for Vehicle (STI, Car/Truck/Motorcycle)

**Capability:** `recipes`  
**Stack:** `both`

**Use Case:** Vehicle fleet management with single-table inheritance — base Vehicle entity with Car, Truck, and Motorcycle subtypes sharing a discriminator column.

**Input DSL:**
```yaml
recipe:
  type: PolymorphicEntity
  name: Vehicle
  polymorphism_type: single_table
  discriminator_field: vehicle_type
  base_fields:
    - name: vin
      type: string
      nullable: false
      unique: true
      length: 17
    - name: license_plate
      type: string
      nullable: false
      length: 20
    - name: year
      type: integer
      nullable: false
  subtypes:
    - name: Car
      fields:
        - name: seating_capacity
          type: integer
        - name: body_style
          type: string
          length: 50
    - name: Truck
      fields:
        - name: cargo_capacity_kg
          type: integer
        - name: bed_length
          type: string
          length: 30
    - name: Motorcycle
      fields:
        - name: engine_cc
          type: integer
        - name: has_sidecar
          type: boolean
```

**Expected Output:**
- File: `src/models/vehicle.py`
- Contains: PolymorphicEntity Vehicle with SINGLE_TABLE, discriminator=vehicle_type, 3 subtypes (Car/Truck/Motorcycle) with subtype-specific fields

---

### B01-REC-17: PolymorphicEntityRecipe for Payment (JOINED_TABLE, CreditCard/PayPal)

**Capability:** `recipes`  
**Stack:** `fastapi`

**Use Case:** Payment processing with joined-table inheritance — base Payment table shared across subtypes, with separate CreditCard and PayPal tables for type-specific fields.

**Input DSL:**
```yaml
recipe:
  type: PolymorphicEntity
  name: Payment
  polymorphism_type: joined_table
  discriminator_field: payment_type
  base_fields:
    - name: amount
      type: decimal
      nullable: false
      precision: 10
      scale: 2
    - name: currency
      type: string
      nullable: false
      length: 3
    - name: status
      type: string
      nullable: false
      length: 20
  subtypes:
    - name: CreditCard
      fields:
        - name: card_last_four
          type: string
          length: 4
        - name: card_brand
          type: string
          length: 20
    - name: PayPal
      fields:
        - name: paypal_email
          type: string
          length: 255
        - name: payer_id
          type: string
          length: 64
```

**Expected Output:**
- File: `src/models/payment.py`
- Contains: PolymorphicEntity Payment with JOINED_TABLE, 2 subtypes (CreditCard/PayPal), discriminator=payment_type

---

### B01-REC-18: ProjectionRecipe for OrderSummary (DENORMALIZED from OrderCreated)

**Capability:** `recipes`  
**Stack:** `both`

**Use Case:** CQRS read model for order summary dashboard — denormalized projection derived from OrderCreated event with flattened fields for fast read queries.

**Input DSL:**
```yaml
recipe:
  type: Projection
  name: OrderSummary
  source_aggregate: Order
  projection_type: denormalized
  source_events:
    - OrderPlaced
    - OrderShipped
    - OrderDelivered
    - OrderCancelled
  fields:
    - name: order_id
      type: uuid
      nullable: false
    - name: customer_name
      type: string
      length: 100
    - name: total_amount
      type: decimal
      precision: 10
      scale: 2
    - name: status
      type: string
      length: 30
    - name: item_count
      type: integer
    - name: shipped_at
      type: datetime
      nullable: true
```

**Expected Output:**
- File: `src/projections/order_summary.py`
- Contains: Projection with DENORMALIZED type, 4 source events, 6 flattened fields for dashboard read model

---

### B01-REC-19: ValueObjectRecipe for Money (DECIMAL amount, STRING currency)

**Capability:** `recipes`  
**Stack:** `both`

**Use Case:** Immutable Money value object with DECIMAL amount and STRING currency — equality-by-value, used as embedded value in Order/Invoice entities.

**Input DSL:**
```yaml
recipe:
  type: ValueObject
  name: Money
  fields:
    - name: amount
      type: decimal
      required: true
      precision: 12
      scale: 2
    - name: currency
      type: string
      required: true
      length: 3
```

**Expected Output:**
- File: `src/value_objects/money.py`
- Contains: ValueObject Money with 2 fields (amount DECIMAL, currency STRING), immutable, equality-by-value implementation

---

### B01-REC-20: GlobalErrorHandlerRecipe (FALLBACK strategy, ERROR level, with logging + notification)

**Capability:** `recipes`  
**Stack:** `fastapi`

**Use Case:** Production-ready global error handler with fallback strategy, ERROR-level logging, common exception mappers, structured JSON logging, and Slack notification.

**Input DSL:**
```yaml
recipe:
  type: GlobalErrorHandler
  name: AppErrorHandler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  with_logging: true
  with_notification: true
  common_mappers: true
  logging:
    format: json
    destination: file
    file_path: /var/log/app/errors.log
    redact_fields:
      - password
      - token
      - ssn
      - credit_card
  notification:
    slack_webhook: https://hooks.slack.com/services/T00/B00/xxx
    email_recipients:
      - ops@company.com
    include_sentry: true
    sentry_dsn: https://key@sentry.io/12345
    rate_limit_per_hour: 50
```

**Expected Output:**
- File: `src/error_handling/global_error_handler.py`
- Contains: GlobalErrorHandler (FALLBACK, ERROR, no stack trace), 6 common ErrorMappers (ValueError/KeyError/PermissionError/TypeError/ConnectionError/TimeoutError), ErrorLoggingConfig (JSON, file, redacted), ErrorNotificationConfig (Slack + Email + Sentry, rate-limited 50/hr)
