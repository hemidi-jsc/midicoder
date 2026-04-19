# Node Type - Midicoder DSL v1

## Overview

A **Node Type** is the fundamental building block of Midicoder's Domain-Specific Language (DSL). It defines a category of objects or concepts that the DSL can represent, validate, and compile into executable code.

## Formal Definition

```
Node Type = {
    "kind": string,           # Unique identifier (e.g., "Entity", "Command")
    "params": Schema,         # Typed parameters schema
    "obligations": Rules,     # Constraints that MUST be satisfied
    "outputs": Artifacts      # Generated code/artifacts after compilation
}
```

## Anatomy of a Node Type

```
┌─────────────────────────────────────┐
│           NODE TYPE                 │
│  ┌─────────────────────────────┐   │
│  │  1. KIND (required)         │   │  ← "Entity", "Command", "Query"...
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  2. PARAMS (schema)         │   │  ← Fields + types + required flags
│  │     - id: string            │   │
│  │     - fields: list[field]   │   │
│  │     - ...                   │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  3. OBLIGATIONS (rules)     │   │  ✓ What MUST be true
│  │     - must_have_primary_key │   │
│  │     - must_be_tenant_scoped │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  4. OUTPUTS (code gen)      │   │  ← SQL table, Python class, ...
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## Core Concepts

### 1. Kind

The **kind** is the unique identifier for a node type. It follows the pattern:

```
{layer}.{concept}  or  {domain}.{resource}
```

Examples:

- `domain.entity` - An Entity in the domain layer
- `app.command` - A Command in the application layer
- `infra.datasource` - A DataSource in the infrastructure layer

### 2. Params

The **params** define the schema for a node instance. Each parameter has:

| Field         | Description                               |
| ------------- | ----------------------------------------- |
| `name`        | Parameter name                            |
| `type`        | Data type (string, int, list, dict, etc.) |
| `required`    | Whether the parameter is mandatory        |
| `description` | Human-readable description                |
| `default`     | Default value if not provided             |
| `constraints` | Additional validation rules               |

**Example: Entity Params**

```python
class EntityParams(TypedDict, total=False):
    """Typed parameters for Entity nodes."""
    id: str              # ✓ Entity name (e.g., "Order")
    description: str     # ✓ Description
    fields: list[dict]   # ✓ Entity fields
    primary_key: str     # ✓ Primary key field name
    indexes: list[dict]  # ✓ Index definitions
    constraints: list[dict]  # ✓ Business constraints
    tags: list[str]      # ✓ Categorization tags
    tenant_scope: str    # ✓ Multi-tenancy scope
```

### 3. Obligations

**Obligations** are compile-time constraints that a node MUST satisfy. They ensure:

- **Referential integrity**: All references resolve to valid nodes
- **Business rules**: Domain-specific invariants are enforced
- **Security**: Access control and tenant isolation are correct
- **Consistency**: Cross-node dependencies are valid

**Example Obligations for Entity:**

```yaml
obligations:
    - type: must_have_id
      message: "Entity must have an 'id' field"

    - type: must_have_primary_key
      message: "Entity must specify a primary key"

    - type: tenant_scope_required
      message: "Entity must declare tenant_scope for multi-tenant apps"

    - type: field_types_valid
      message: "All field types must be resolvable"
```

### 4. Outputs

**Outputs** are the artifacts generated when a node is compiled. Common outputs include:

| Output Type       | Example                         |
| ----------------- | ------------------------------- |
| Database Schema   | SQL CREATE TABLE statements     |
| Code Classes      | Python/TypeScript model classes |
| API Definitions   | OpenAPI/GraphQL schemas         |
| Validation Code   | Input validation functions      |
| Migration Scripts | Database migration files        |

## Node Type Categories (7 Layers)

Midicoder organizes node types into 7 architectural layers:

### Layer 1: Foundation

Foundation nodes provide the structural backbone for all contracts.

| Node Type    | Purpose                                 |
| ------------ | --------------------------------------- |
| `Manifest`   | Project metadata, version, strict flags |
| `Metadata`   | Annotations, tags, custom properties    |
| `Catalog`    | Enumerated values, type catalogs        |
| `Dependency` | Inter-node dependencies                 |
| `Constraint` | Validation rules, business invariants   |

### Layer 2: Domain

Domain nodes represent business concepts and data models.

| Node Type     | Purpose                          |
| ------------- | -------------------------------- |
| `Entity`      | Core business objects with state |
| `ValueObject` | Immutable value carriers         |
| `Enum`        | Discrete value sets              |
| `Error`       | Error definitions and codes      |
| `Event`       | Domain events and notifications  |

### Layer 3: Application

Application nodes orchestrate business logic and workflows.

| Node Type  | Purpose                       |
| ---------- | ----------------------------- |
| `Command`  | State-changing operations     |
| `Query`    | Read-only data retrieval      |
| `Workflow` | Multi-step business processes |
| `Rule`     | Business rule definitions     |
| `Guard`    | Precondition checks           |
| `Effect`   | Side-effect operations        |

### Layer 4: Infrastructure

Infrastructure nodes define technical implementations.

| Node Type    | Purpose                       |
| ------------ | ----------------------------- |
| `Table`      | Database table definitions    |
| `DataSource` | Database connection configs   |
| `Cache`      | Caching strategies            |
| `Queue`      | Message queue definitions     |
| `Index`      | Database index specifications |

### Layer 5: Platform

Platform nodes handle security, governance, and operations.

| Node Type      | Purpose                     |
| -------------- | --------------------------- |
| `Policy`       | Authorization policies      |
| `Role`         | User role definitions       |
| `AccessPolicy` | Fine-grained access control |
| `AuditLog`     | Audit trail configurations  |
| `RateLimit`    | Rate limiting rules         |

### Layer 6: Integration

Integration nodes define external system interactions.

| Node Type      | Purpose                       |
| -------------- | ----------------------------- |
| `HTTPRoute`    | REST API endpoint definitions |
| `GraphQL`      | GraphQL schema definitions    |
| `Integration`  | External system integrations  |
| `Webhook`      | Webhook configurations        |
| `Subscription` | Event subscription handlers   |

### Layer 7: Ops

Ops nodes define observability and deployment configurations.

| Node Type    | Purpose                       |
| ------------ | ----------------------------- |
| `Metric`     | Custom metric definitions     |
| `Alert`      | Alerting rules and thresholds |
| `Log`        | Logging configurations        |
| `Deployment` | Deployment specifications     |
| `Secret`     | Secret management configs     |

## Node Type Instance Example

### Entity Instance

```yaml
- kind: domain.entity
  params:
      id: Order
      description: "Customer order in the e-commerce system"
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
    description: "Create a new order for a customer"
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

## Comparison with Other Systems

| System        | Equivalent Concept | Example                   |
| ------------- | ------------------ | ------------------------- |
| **OOP**       | Class / Type       | `class Order { ... }`     |
| **Database**  | Table Definition   | `CREATE TABLE orders ...` |
| **AST**       | Node Class         | `FunctionDef`, `ClassDef` |
| **GraphQL**   | Type Definition    | `type Order { ... }`      |
| **HTML**      | Element Tag        | `<table>`, `<div>`        |
| **Terraform** | Resource Type      | `aws_s3_bucket`           |

## Why Node Types Matter

### 1. Type Safety

The compiler knows exactly what fields each node type has, enabling:

- Early error detection
- IDE autocomplete
- Schema validation

### 2. Validation

Obligations ensure nodes are correctly configured:

- Missing required fields
- Invalid references
- Business rule violations

### 3. Code Generation

Each node type knows what code to generate:

- Entity → Database table + Python class + GraphQL type
- Command → Handler function + validation + auth checks

### 4. Documentation

Node types enable auto-generated documentation:

- API references from HTTPRoute nodes
- Data models from Entity nodes
- Error catalogs from Error nodes

### 5. Reusability

Node types are reusable patterns:

- Define once, use everywhere
- Consistent patterns across projects
- Industry-specific packs

## Node Type Extensibility

Node types can be extended through:

### 1. Core Packs (CP)

Built-in node types maintained by the Midicoder team.

### 2. Domain Packs (DP)

Industry-specific node types (e.g., Healthcare, Finance).

### 3. Regulatory Overlays (RX)

Compliance-specific extensions (e.g., HIPAA, GDPR).

## Summary

A **Node Type** is:

> A **blueprint** that defines a category of objects in a system, including:
>
> - **Kind**: Unique identifier for recognition
> - **Params**: Schema describing node attributes
> - **Obligations**: Rules ensuring correctness
> - **Outputs**: Artifacts generated during compilation

**Simple Analogy:**

If Midicoder is like LEGO:

- Each **brick type** = a Node Type
- Each **assembled structure** = a Node instance
- **Assembly instructions** = Obligations
- **Final model** = Generated code

---

## See Also

- [DSL v1 Overview](./dsl-v1-overview.md)
- [Projection Model](./projection-model.md)
- [Obligations & Guards](./obligations-guards.md)
- [Code Generation](./code-generation.md)
