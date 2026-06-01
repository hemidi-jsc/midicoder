# UAT Briefs: entity_modeling

20 real-world use cases for Entity DSL definition. Each brief tests full pipeline: YAML DSL → Entity model → Code generation (FastAPI/NestJS).

---

### B01-ENT-01: Simple User entity with UUID primary key and email/name fields

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** E-commerce platform needs a basic User entity for user registration and profile management with UUID primary key for distributed system compatibility.

**Input DSL:**
```yaml
entities:
  - id: User
    description: "Registered user account"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: email
        type: string
        length: 255
        nullable: false
      - name: name
        type: string
        length: 255
        nullable: false
      - name: created_at
        type: datetime
        server_default: "NOW()"
```

**Expected Output:**
- File: `app/models/user.py`
- Contains: `class User(Base)`, `__tablename__ = "users"`, `id: Mapped[UUID]`, `Column(PGUUID(as_uuid=True), primary_key=True)`, `email: Mapped[str]`, `Column(String(255), nullable=False)`

### B01-ENT-02: Product entity with DECIMAL price and TEXT description

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** E-commerce catalogue requires Product entity with precise decimal pricing (10 digits, 2 decimal places) and unlimited-length text description for product details.

**Input DSL:**
```yaml
entities:
  - id: Product
    description: "Catalogue product"
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
        nullable: false
      - name: description
        type: text
        nullable: true
```

**Expected Output:**
- File: `app/models/product.py`
- Contains: `class Product(Base)`, `price: Mapped[Decimal]`, `Column(Numeric(10, 2))`, `description: Mapped[str | None]`, `Column(Text)`

### B01-ENT-03: Order entity with MANY_TO_MANY relationship to Product

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Order system where an order can contain multiple products and each product can appear in multiple orders, requiring a join table `order_products`.

**Input DSL:**
```yaml
entities:
  - id: Order
    description: "Customer order"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: order_date
        type: datetime
        nullable: false
      - name: total_amount
        type: decimal
        precision: 12
        scale: 2
    relationships:
      - type: many-to-many
        target: Product
        secondary: order_products
        local_field: product_ids
        back_populates: orders
  - id: Product
    description: "Catalogue product"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: name
        type: string
        length: 255
    relationships:
      - type: many-to-many
        target: Order
        secondary: order_products
        local_field: order_ids
        back_populates: order
```

**Expected Output:**
- File: `app/models/order.py`
- Contains: `class Order(Base)`, `relationship("Product", secondary="order_products"`, `back_populates="orders"`, `order_products` join table definition

### B01-ENT-04: Category entity with SELF_REFERENCING parent-child tree

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Product categorization system with hierarchical categories (Electronics → Phones → Smartphones), requiring self-referencing relationship for parent-child tree structure.

**Input DSL:**
```yaml
entities:
  - id: Category
    description: "Product category with hierarchical structure"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: name
        type: string
        length: 100
        nullable: false
      - name: parent_id
        type: uuid
        nullable: true
    relationships:
      - type: self-referencing
        local_field: parent_id
        back_populates: children
```

**Expected Output:**
- File: `app/models/category.py`
- Contains: `class Category(Base)`, `parent_id: Mapped[UUID | None]`, `ForeignKey`, `relationship("Category"`, `remote_side`, `back_populates="children"`

### B01-ENT-05: Employee entity with ONE_TO_ONE relationship to Department

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** HR system where each employee belongs to exactly one department, and the department head is stored as a one-to-one reference from Department back to Employee.

**Input DSL:**
```yaml
entities:
  - id: Employee
    description: "Company employee"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: full_name
        type: string
        length: 200
        nullable: false
      - name: department_id
        type: uuid
        nullable: false
    relationships:
      - type: one-to-one
        target: Department
        local_field: department_id
        back_populates: employees
  - id: Department
    description: "Organizational department"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: name
        type: string
        length: 100
        nullable: false
    relationships:
      - type: one-to-one
        target: Employee
        back_populates: department
```

**Expected Output:**
- File: `app/models/employee.py`
- Contains: `class Employee(Base)`, `relationship("Department", uselist=False`, `back_populates`, `department_id`, `ForeignKey`

### B01-ENT-06: Customer entity with UNIQUE constraint on email

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** CRM system requiring that no two customers can share the same email address, enforced at the database level via a unique constraint.

**Input DSL:**
```yaml
entities:
  - id: Customer
    description: "CRM customer record"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: email
        type: string
        length: 255
        nullable: false
      - name: company_name
        type: string
        length: 300
        nullable: true
    constraints:
      - type: unique
        fields:
          - email
```

**Expected Output:**
- File: `app/models/customer.py`
- Contains: `class Customer(Base)`, `UniqueConstraint("email")` or `Column(String(255), nullable=False, unique=True)`

### B01-ENT-07: Invoice entity with CHECK constraint ensuring amount >= 0

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Financial invoicing system that must prevent negative invoice amounts at the database level to ensure data integrity for accounting records.

**Input DSL:**
```yaml
entities:
  - id: Invoice
    description: "Financial invoice record"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: invoice_number
        type: string
        length: 50
        nullable: false
      - name: amount
        type: decimal
        precision: 12
        scale: 2
        nullable: false
      - name: issued_date
        type: datetime
        nullable: false
    constraints:
      - type: check
        name: check_invoice_amount_non_negative
        condition: "amount >= 0"
```

**Expected Output:**
- File: `app/models/invoice.py`
- Contains: `class Invoice(Base)`, `CheckConstraint("amount >= 0")` or `__table_args__` with check constraint

### B01-ENT-08: Transaction entity with multi-column unique index

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Banking transaction log that must prevent duplicate transaction references by enforcing uniqueness across (transaction_ref, account_id) pair.

**Input DSL:**
```yaml
entities:
  - id: Transaction
    description: "Financial transaction record"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: transaction_ref
        type: string
        length: 64
        nullable: false
      - name: account_id
        type: uuid
        nullable: false
      - name: amount
        type: decimal
        precision: 15
        scale: 2
      - name: occurred_at
        type: datetime
        nullable: false
    indexes:
      - name: uq_transaction_ref_account
        fields:
          - transaction_ref
          - account_id
        unique: true
```

**Expected Output:**
- File: `app/models/transaction.py`
- Contains: `class Transaction(Base)`, `Index("uq_transaction_ref_account", "transaction_ref", "account_id", unique=True)`

### B01-ENT-09: AuditLog entity with JSON metadata field

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** System audit trail that stores arbitrary metadata as JSON for each audit event, allowing flexible schema evolution without migration.

**Input DSL:**
```yaml
entities:
  - id: AuditLog
    description: "System audit log entry"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: action
        type: string
        length: 100
        nullable: false
      - name: actor_id
        type: uuid
        nullable: false
      - name: metadata
        type: json
        nullable: true
      - name: created_at
        type: datetime
        nullable: false
```

**Expected Output:**
- File: `app/models/audit_log.py`
- Contains: `class AuditLog(Base)`, `metadata: Mapped[Any | None]`, `Column(JSON)`

### B01-ENT-10: Config entity with ENUM status field

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Application configuration store where each config entry has a status limited to active, draft, or deprecated values, enforced at the database level.

**Input DSL:**
```yaml
entities:
  - id: Config
    description: "Application configuration entry"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: key
        type: string
        length: 128
        nullable: false
      - name: value
        type: text
        nullable: false
      - name: status
        type: enum
        enum_values:
          - active
          - draft
          - deprecated
        nullable: false
```

**Expected Output:**
- File: `app/models/config.py`
- Contains: `class Config(Base)`, `status: Mapped[`, `enum_values=["active", "draft", "deprecated"]` or `Column(Enum`

### B01-ENT-11: FileAttachment entity with LARGE_BINARY data field

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Document management system storing file attachments as binary data blobs in the database for direct retrieval without external storage.

**Input DSL:**
```yaml
entities:
  - id: FileAttachment
    description: "File attachment with binary content"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: filename
        type: string
        length: 500
        nullable: false
      - name: content_type
        type: string
        length: 100
        nullable: false
      - name: data
        type: largebinary
        nullable: true
      - name: size_bytes
        type: integer
        nullable: false
```

**Expected Output:**
- File: `app/models/file_attachment.py`
- Contains: `class FileAttachment(Base)`, `data: Mapped[bytes | None]`, `Column(LargeBinary)`

### B01-ENT-12: Tag entity with ARRAY of string values

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Content tagging system where each tag record stores an array of synonym strings for fuzzy matching and search optimization.

**Input DSL:**
```yaml
entities:
  - id: Tag
    description: "Content tag with synonym array"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: name
        type: string
        length: 50
        nullable: false
      - name: synonyms
        type: array
        nullable: true
      - name: usage_count
        type: integer
        default: 0
```

**Expected Output:**
- File: `app/models/tag.py`
- Contains: `class Tag(Base)`, `synonyms: Mapped[list[str] | None]`, `Column(ARRAY(String)`

### B01-ENT-13: Tenant entity with lifecycle hook setting defaults on insert

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Multi-tenant SaaS platform where new tenant records automatically get a subscription tier of "free" and status "pending" via before_insert lifecycle hook.

**Input DSL:**
```yaml
entities:
  - id: Tenant
    description: "SaaS tenant account"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: name
        type: string
        length: 200
        nullable: false
      - name: subscription_tier
        type: string
        length: 50
        default: "free"
      - name: status
        type: string
        length: 20
        default: "pending"
    lifecycle:
      before_insert: set_tenant_defaults
```

**Expected Output:**
- File: `app/models/tenant.py`
- Contains: `class Tenant(Base)`, `event.listen(Tenant, "before_insert", set_tenant_defaults)` or `@event.listen`

### B01-ENT-14: Address entity with POLYMORPHIC relationship

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Shipping system where addresses can belong to different entity types (User, Company, Warehouse), using polymorphic target_type and target_id fields.

**Input DSL:**
```yaml
entities:
  - id: Address
    description: "Polymorphic address record"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: street
        type: string
        length: 500
        nullable: false
      - name: city
        type: string
        length: 100
        nullable: false
      - name: postal_code
        type: string
        length: 20
        nullable: false
      - name: target_type
        type: string
        length: 50
        nullable: false
      - name: target_id
        type: uuid
        nullable: false
    relationships:
      - type: polymorphic
        polymorphic: true
        local_field: target_id
```

**Expected Output:**
- File: `app/models/address.py`
- Contains: `class Address(Base)`, `target_type: Mapped[str]`, `target_id: Mapped[UUID]`, polymorphic_identity or discriminator

### B01-ENT-15: Full e-commerce Product entity combining all features

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Complete product entity for a production e-commerce platform combining ENUM type, DECIMAL price, CHECK constraint, indexes, self-referencing category, and lifecycle hooks.

**Input DSL:**
```yaml
entities:
  - id: Product
    description: "Full-featured e-commerce product"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: sku
        type: string
        length: 50
        nullable: false
      - name: name
        type: string
        length: 300
        nullable: false
      - name: description
        type: text
      - name: price
        type: decimal
        precision: 12
        scale: 2
        nullable: false
      - name: stock_quantity
        type: integer
        default: 0
      - name: status
        type: enum
        enum_values:
          - active
          - discontinued
          - draft
        nullable: false
      - name: category_id
        type: uuid
        nullable: true
      - name: metadata
        type: json
      - name: created_at
        type: datetime
        server_default: "NOW()"
      - name: updated_at
        type: datetime
        server_default: "NOW()"
    relationships:
      - type: self-referencing
        target: Product
        local_field: parent_category_id
        back_populates: children
    constraints:
      - type: unique
        fields:
          - sku
      - type: check
        name: check_price_positive
        condition: "price > 0"
      - type: check
        name: check_stock_non_negative
        condition: "stock_quantity >= 0"
    indexes:
      - name: idx_product_sku
        fields:
          - sku
        unique: true
      - name: idx_product_status
        fields:
          - status
    lifecycle:
      before_insert: set_created_timestamp
      before_update: set_updated_timestamp
```

**Expected Output:**
- File: `app/models/product.py`
- Contains: `class Product(Base)`, `__tablename__ = "products"`, `CheckConstraint("price > 0")`, `CheckConstraint("stock_quantity >= 0")`, `Index("idx_product_sku"`, `Index("idx_product_status"`, `event.listen`, `sku`, `ForeignKey`

### B01-ENT-16: Multi-tenant entity with tenant_id field and tenant_scope

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Project management app where each project belongs to a specific tenant, with tenant_id foreign key and an index for efficient tenant-scoped queries.

**Input DSL:**
```yaml
entities:
  - id: Project
    description: "Tenant-scoped project record"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: tenant_id
        type: uuid
        nullable: false
      - name: name
        type: string
        length: 200
        nullable: false
      - name: description
        type: text
      - name: created_at
        type: datetime
        server_default: "NOW()"
    constraints:
      - type: foreign_key
        name: fk_project_tenant
        fields:
          - tenant_id
    indexes:
      - name: idx_project_tenant
        fields:
          - tenant_id
```

**Expected Output:**
- File: `app/models/project.py`
- Contains: `class Project(Base)`, `tenant_id: Mapped[UUID]`, `ForeignKey`, `Index("idx_project_tenant", "tenant_id")`

### B01-ENT-17: WarehouseInventory entity with multiple CHECK constraints

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Warehouse inventory tracking with business rules: quantity must be non-negative, reorder_level must be positive, and max_capacity must exceed reorder_level.

**Input DSL:**
```yaml
entities:
  - id: WarehouseInventory
    description: "Warehouse stock tracking record"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: product_id
        type: uuid
        nullable: false
      - name: quantity
        type: integer
        default: 0
      - name: reorder_level
        type: integer
        default: 10
      - name: max_capacity
        type: integer
        default: 1000
    constraints:
      - type: check
        name: check_quantity_non_negative
        condition: "quantity >= 0"
      - type: check
        name: check_reorder_positive
        condition: "reorder_level > 0"
      - type: check
        name: check_capacity_exceeds_reorder
        condition: "max_capacity > reorder_level"
```

**Expected Output:**
- File: `app/models/warehouse_inventory.py`
- Contains: `class WarehouseInventory(Base)`, `CheckConstraint("quantity >= 0")`, `CheckConstraint("reorder_level > 0")`, `CheckConstraint("max_capacity > reorder_level")`

### B01-ENT-18: SearchIndex entity with composite index on 3 columns

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Full-text search index entity that requires a composite index across (tenant_id, status, created_at) for efficient tenant-scoped, status-filtered chronological queries.

**Input DSL:**
```yaml
entities:
  - id: SearchIndex
    description: "Search index entry with composite index"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: tenant_id
        type: uuid
        nullable: false
      - name: entity_type
        type: string
        length: 50
        nullable: false
      - name: entity_id
        type: uuid
        nullable: false
      - name: status
        type: string
        length: 20
        nullable: false
      - name: created_at
        type: datetime
        server_default: "NOW()"
    indexes:
      - name: idx_search_tenant_status_time
        fields:
          - tenant_id
          - status
          - created_at
```

**Expected Output:**
- File: `app/models/search_index.py`
- Contains: `class SearchIndex(Base)`, `Index("idx_search_tenant_status_time", "tenant_id", "status", "created_at")`

### B01-ENT-19: Document entity with all 6 lifecycle hooks

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Document management system that requires hooks at every lifecycle stage: set defaults on insert, log creation, validate before update, notify on update, prevent deletion of locked docs, and archive on delete.

**Input DSL:**
```yaml
entities:
  - id: Document
    description: "Managed document with full lifecycle"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: title
        type: string
        length: 300
        nullable: false
      - name: content_hash
        type: string
        length: 64
        nullable: false
      - name: version
        type: integer
        default: 1
      - name: is_locked
        type: boolean
        default: false
      - name: created_at
        type: datetime
        server_default: "NOW()"
      - name: updated_at
        type: datetime
        server_default: "NOW()"
      - name: deleted_at
        type: datetime
        nullable: true
    lifecycle:
      before_insert: set_default_metadata
      after_insert: log_document_creation
      before_update: validate_document_integrity
      after_update: notify_document_change
      before_delete: check_document_lock
      after_delete: archive_document_content
```

**Expected Output:**
- File: `app/models/document.py`
- Contains: `class Document(Base)`, `event.listen(Document, "before_insert"`, `event.listen(Document, "after_insert"`, `event.listen(Document, "before_update"`, `event.listen(Document, "after_update"`, `event.listen(Document, "before_delete"`, `event.listen(Document, "after_delete"`

### B01-ENT-20: Minimal entity with only id and description

**Capability:** `entity_modeling`
**Stack:** `both`

**Use Case:** Minimal note-taking entity with just a UUID primary key and a text description field, representing the simplest possible entity definition.

**Input DSL:**
```yaml
entities:
  - id: Note
    description: "Minimal note entity"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: description
        type: text
        nullable: false
```

**Expected Output:**
- File: `app/models/note.py`
- Contains: `class Note(Base)`, `__tablename__ = "notes"`, `id: Mapped[UUID]`, `description: Mapped[str]`
