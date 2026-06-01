# UAT Briefs: command_query_separation

20 real-world use cases for Command and Query DSL definitions. Each brief tests full pipeline: YAML DSL → Model → Code generation (FastAPI/NestJS).

---

### B01-CQS-01: CreateOrder command with AUTH guard and CREATE_RECORD effect

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** E-commerce order creation that requires authenticated user with "order.create" permission and persists a new order record to the database.

**Input DSL:**
```yaml
commands:
  - id: CreateOrder
    description: "Create a new customer order"
    category: create
    input:
      - name: customer_id
        type: uuid
        required: true
      - name: product_id
        type: uuid
        required: true
      - name: quantity
        type: integer
        required: true
        min_value: 1
      - name: shipping_address
        type: string
        required: true
    returns:
      - name: order_id
        type: uuid
      - name: status
        type: string
    guards:
      - guard_type: auth
        permission: "order.create"
    effects:
      - effect_type: create_record
        entity: Order
    writes_to:
      - Order
```

**Expected Output:**
- File: `app/commands/create_order/command.py`
- Contains: `class CreateOrderCommand`, `customer_id: UUID`, `product_id: UUID`, `quantity: int`, `guard_type: auth`, `permission: "order.create"`, `effect_type: create_record`

### B01-CQS-02: UpdateUser command with TENANT_SCOPE guard (tenant_isolated)

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** User profile update in a multi-tenant SaaS app where users can only modify their own data within their tenant's scope, enforced by tenant_isolated guard.

**Input DSL:**
```yaml
commands:
  - id: UpdateUser
    description: "Update user profile within tenant scope"
    category: update
    input:
      - name: user_id
        type: uuid
        required: true
      - name: display_name
        type: string
        required: true
        max_length: 200
      - name: avatar_url
        type: string
        max_length: 1000
    guards:
      - guard_type: tenant_scope
        mode: tenant_isolated
    effects:
      - effect_type: update_record
        entity: User
    writes_to:
      - User
    tenant_scope: tenant_isolated
```

**Expected Output:**
- File: `app/commands/update_user/command.py`
- Contains: `class UpdateUserCommand`, `guard_type: tenant_scope`, `mode: tenant_isolated`, `effect_type: update_record`, `tenant_scope: tenant_isolated`

### B01-CQS-03: DeleteProduct command with AUTH guard and transaction rollback on error

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Product deletion that requires admin authorization and must roll back all changes if the deletion fails, including related inventory and order line items.

**Input DSL:**
```yaml
commands:
  - id: DeleteProduct
    description: "Delete product with admin authorization and rollback safety"
    category: delete
    input:
      - name: product_id
        type: uuid
        required: true
    guards:
      - guard_type: auth
        permission: "product.delete"
    effects:
      - effect_type: delete_record
        entity: Product
    errors:
      - code: PRODUCT_HAS_ACTIVE_ORDERS
        message: "Cannot delete product with active orders"
        http_status: 409
      - code: PRODUCT_NOT_FOUND
        message: "Product not found"
        http_status: 404
    writes_to:
      - Product
    transaction: true
    on_error: rollback
```

**Expected Output:**
- File: `app/commands/delete_product/command.py`
- Contains: `class DeleteProductCommand`, `guard_type: auth`, `permission: "product.delete"`, `effect_type: delete_record`, `transaction_required: true`, `on_error: rollback`, `PRODUCT_HAS_ACTIVE_ORDERS`

### B01-CQS-04: GetOrders query with OFFSET pagination and sort by created_at DESC

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Retrieve a paginated list of orders sorted by creation date (newest first) with page-based (offset) pagination of 20 items per page.

**Input DSL:**
```yaml
queries:
  - id: GetOrders
    description: "List orders with pagination and sorting"
    reads_from: Order
    input:
      - name: page
        type: integer
        default: 1
      - name: page_size
        type: integer
        default: 20
    pagination:
      type: offset
      page_size: 20
      page: 1
    sort:
      - field: created_at
        direction: desc
    guards:
      - guard_type: auth
        permission: "order.read"
      - guard_type: tenant_scope
        mode: tenant_isolated
```

**Expected Output:**
- File: `app/queries/get_orders/handler.py`
- Contains: `class GetOrdersHandler`, `pagination type: offset`, `page_size: 20`, `sort: created_at`, `direction: desc`, `tenant_isolated`

### B01-CQS-05: SearchProducts query with LIKE filter and CURSOR pagination

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Product search endpoint that filters by name pattern (case-insensitive LIKE) and uses cursor-based pagination for infinite scroll UI.

**Input DSL:**
```yaml
queries:
  - id: SearchProducts
    description: "Search products by name with cursor pagination"
    reads_from: Product
    input:
      - name: search_term
        type: string
        required: true
    filters:
      - field: name
        operator: ilike
        value: "%search_term%"
    pagination:
      type: cursor
      limit: 25
    guards:
      - guard_type: auth
        permission: "product.read"
```

**Expected Output:**
- File: `app/queries/search_products/handler.py`
- Contains: `class SearchProductsHandler`, `filter: name`, `operator: ilike`, `pagination type: cursor`, `limit: 25`

### B01-CQS-06: GetStats aggregation query with COUNT and SUM grouped by status

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Dashboard statistics that count orders and sum revenue grouped by order status (pending, shipped, delivered) for the admin dashboard.

**Input DSL:**
```yaml
queries:
  - id: GetOrderStats
    description: "Aggregated order statistics by status"
    reads_from: Order
    aggregation:
      functions:
        - function: count
        - function: sum
          field: total_amount
      group_by:
        - status
    guards:
      - guard_type: auth
        permission: "order.stats"
    effects:
      - effect_type: record_metric
        metric_name: order_stats_query_duration
```

**Expected Output:**
- File: `app/queries/get_order_stats/handler.py`
- Contains: `class GetOrderStatsHandler`, `aggregation: count`, `aggregation: sum`, `group_by: status`, `record_metric`, `metric_name: order_stats_query_duration`

### B01-CQS-07: TransferMoney command with AML_SCREENING guard and double-entry validation

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Bank money transfer that must pass AML (Anti-Money Laundering) screening before execution, with double-entry bookkeeping via separate debit and credit effects in a transaction.

**Input DSL:**
```yaml
commands:
  - id: TransferMoney
    description: "Transfer money between accounts with AML screening"
    category: custom
    input:
      - name: from_account
        type: uuid
        required: true
      - name: to_account
        type: uuid
        required: true
      - name: amount
        type: decimal
        required: true
        min_value: 0.01
    guards:
      - guard_type: auth
        permission: "account.transfer"
      - guard_type: aml_screening
    effects:
      - effect_type: begin_transaction
      - effect_type: update_record
        entity: Account
      - effect_type: create_record
        entity: Transaction
      - effect_type: commit_transaction
    errors:
      - code: INSUFFICIENT_FUNDS
        message: "Insufficient funds in source account"
        http_status: 422
      - code: AML_BLOCKED
        message: "Transfer blocked by AML screening"
        http_status: 403
    writes_to:
      - Account
      - Transaction
    transaction: true
    on_error: rollback
```

**Expected Output:**
- File: `app/commands/transfer_money/command.py`
- Contains: `class TransferMoneyCommand`, `guard_type: aml_screening`, `effect_type: begin_transaction`, `effect_type: commit_transaction`, `INSUFFICIENT_FUNDS`, `AML_BLOCKED`, `transaction_required: true`

### B01-CQS-08: GetPatients query with HIPAA_ACCESS guard and PHI masking

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Healthcare system query that requires HIPAA clearance and automatically masks PHI (Protected Health Information) fields like SSN and medical record numbers for unauthorized roles.

**Input DSL:**
```yaml
queries:
  - id: GetPatients
    description: "List patients with HIPAA access control and PHI masking"
    reads_from: Patient
    input:
      - name: department
        type: string
    filters:
      - field: department
        operator: eq
        value: "department"
    pagination:
      type: offset
      page_size: 15
    projection:
      include:
        - patient_id
        - full_name
        - date_of_birth
        - status
      exclude:
        - ssn
        - medical_record_number
    guards:
      - guard_type: auth
        permission: "patient.read"
      - guard_type: tenant_scope
        mode: tenant_isolated
    effects:
      - effect_type: write_audit_log
        audit_action: patient_list_access
```

**Expected Output:**
- File: `app/queries/get_patients/handler.py`
- Contains: `class GetPatientsHandler`, `guard_type: auth`, `permission: "patient.read"`, `projection include`, `projection exclude`, `write_audit_log`, `patient_list_access`

### B01-CQS-09: CreateFraudReport command with FRAUD_DETECTION guard

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Financial fraud reporting system that triggers fraud detection analysis (velocity check, amount threshold, pattern anomaly) before persisting the fraud report record.

**Input DSL:**
```yaml
commands:
  - id: CreateFraudReport
    description: "Create fraud report with automated fraud detection"
    category: create
    input:
      - name: account_id
        type: uuid
        required: true
      - name: transaction_id
        type: uuid
        required: true
      - name: fraud_type
        type: enum
        required: true
        enum_values:
          - unauthorized_charge
          - identity_theft
          - account_takeover
          - synthetic_identity
      - name: amount
        type: decimal
        required: true
      - name: description
        type: string
        max_length: 2000
    guards:
      - guard_type: auth
        permission: "fraud.create"
      - guard_type: fraud_detection
        limit: 10
        window: 1h
    effects:
      - effect_type: create_record
        entity: FraudReport
      - effect_type: publish_event
        event: FraudReportCreated
    writes_to:
      - FraudReport
```

**Expected Output:**
- File: `app/commands/create_fraud_report/command.py`
- Contains: `class CreateFraudReportCommand`, `guard_type: fraud_detection`, `limit: 10`, `window: 1h`, `effect_type: create_record`, `effect_type: publish_event`, `FraudReportCreated`

### B01-CQS-10: BulkImport command with BEGIN/CREATE/COMMIT transaction effects

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** CSV-based bulk import of product data that wraps all individual creates in a single transaction (BEGIN → multiple CREATE_RECORD → COMMIT) for atomicity.

**Input DSL:**
```yaml
commands:
  - id: BulkImportProducts
    description: "Bulk import products from CSV with transaction safety"
    category: create
    input:
      - name: items
        type: array
        required: true
    guards:
      - guard_type: auth
        permission: "product.bulk_import"
      - guard_type: rate_limit
        limit: 5
        window: 1h
    effects:
      - effect_type: begin_transaction
      - effect_type: create_record
        entity: Product
      - effect_type: commit_transaction
    errors:
      - code: BULK_IMPORT_LIMIT_EXCEEDED
        message: "Maximum bulk import limit reached"
        http_status: 429
        retryable: true
      - code: INVALID_CSV_DATA
        message: "CSV data contains invalid records"
        http_status: 400
    writes_to:
      - Product
    transaction: true
    on_error: rollback
```

**Expected Output:**
- File: `app/commands/bulk_import_products/command.py`
- Contains: `class BulkImportProductsCommand`, `guard_type: rate_limit`, `effect_type: begin_transaction`, `effect_type: create_record`, `effect_type: commit_transaction`, `BULK_IMPORT_LIMIT_EXCEEDED`, `transaction_required: true`

### B01-CQS-11: GetFilteredItems query with BETWEEN filter and projection include

**Capability:** `command_query_separation`
**Stack:`both`

**Use Case:** Warehouse inventory query that filters items within a price range (BETWEEN) and only returns specific fields (projection include) for the product listing page.

**Input DSL:**
```yaml
queries:
  - id: GetFilteredItems
    description: "Filter inventory items by price range with field projection"
    reads_from: Product
    input:
      - name: min_price
        type: decimal
        required: true
      - name: max_price
        type: decimal
        required: true
    filters:
      - field: price
        operator: between
        value: ["min_price", "max_price"]
    pagination:
      type: offset
      page_size: 50
    projection:
      include:
        - id
        - name
        - price
        - stock_quantity
    sort:
      - field: price
        direction: asc
    guards:
      - guard_type: auth
        permission: "product.read"
```

**Expected Output:**
- File: `app/queries/get_filtered_items/handler.py`
- Contains: `class GetFilteredItemsHandler`, `filter: price`, `operator: between`, `projection include: id, name, price, stock_quantity`, `sort: price`, `direction: asc`

### B01-CQS-12: NotifyUser command with SEND_EMAIL and SEND_SMS effects

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** User notification system that sends both email and SMS notifications when an order status changes, using template-based messaging.

**Input DSL:**
```yaml
commands:
  - id: NotifyUser
    description: "Send email and SMS notification to user"
    category: custom
    input:
      - name: user_id
        type: uuid
        required: true
      - name: notification_type
        type: string
        required: true
        enum_values:
          - order_confirmation
          - shipping_update
          - delivery_notification
      - name: message
        type: string
        required: true
    guards:
      - guard_type: auth
        permission: "notification.send"
    effects:
      - effect_type: send_email
        email_template: notification_email
      - effect_type: send_sms
        sms_template: notification_sms
    writes_to: []
```

**Expected Output:**
- File: `app/commands/notify_user/command.py`
- Contains: `class NotifyUserCommand`, `effect_type: send_email`, `email_template: notification_email`, `effect_type: send_sms`, `sms_template: notification_sms`

### B01-CQS-13: GetDashboard query with RECORD_METRIC effect

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Admin dashboard query that records query duration as a metric for monitoring and alerting purposes on slow dashboard loads.

**Input DSL:**
```yaml
queries:
  - id: GetDashboard
    description: "Admin dashboard with metric recording"
    reads_from: DashboardData
    aggregation:
      functions:
        - function: count
          field: id
        - function: sum
          field: revenue
      group_by:
        - date
    sort:
      - field: date
        direction: desc
    pagination:
      type: offset
      page_size: 30
    guards:
      - guard_type: auth
        permission: "dashboard.read"
    effects:
      - effect_type: record_metric
        metric_name: dashboard_query_duration
      - effect_type: write_audit_log
        audit_action: dashboard_access
```

**Expected Output:**
- File: `app/queries/get_dashboard/handler.py`
- Contains: `class GetDashboardHandler`, `record_metric`, `metric_name: dashboard_query_duration`, `write_audit_log`, `dashboard_access`

### B01-CQS-14: GetGlobalTenants query with cross_tenant guard

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Super-admin query that lists all tenants across the platform, requiring cross_tenant scope to bypass the default tenant isolation.

**Input DSL:**
```yaml
queries:
  - id: GetGlobalTenants
    description: "List all tenants across the platform (super-admin only)"
    reads_from: Tenant
    pagination:
      type: offset
      page_size: 100
    sort:
      - field: created_at
        direction: desc
    projection:
      include:
        - id
        - name
        - subscription_tier
        - tenant_count
        - created_at
    guards:
      - guard_type: auth
        permission: "admin.tenants.read"
      - guard_type: tenant_scope
        mode: cross_tenant
```

**Expected Output:**
- File: `app/queries/get_global_tenants/handler.py`
- Contains: `class GetGlobalTenantsHandler`, `permission: "admin.tenants.read"`, `mode: cross_tenant`, `projection include: id, name, subscription_tier`

### B01-CQS-15: PlaceBid command with AUTH + TENANT_SCOPE + RATE_LIMIT guards

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Auction bidding system with three-layer guard: authentication for bid permission, tenant isolation for auction scope, and rate limiting to prevent bid flooding.

**Input DSL:**
```yaml
commands:
  - id: PlaceBid
    description: "Place a bid with multi-layer security guards"
    category: create
    input:
      - name: auction_id
        type: uuid
        required: true
      - name: bid_amount
        type: decimal
        required: true
        min_value: 0.01
      - name: bidder_id
        type: uuid
        required: true
    guards:
      - guard_type: auth
        permission: "auction.bid"
      - guard_type: tenant_scope
        mode: tenant_isolated
      - guard_type: rate_limit
        limit: 20
        window: 1m
    effects:
      - effect_type: create_record
        entity: Bid
      - effect_type: publish_event
        event: BidPlaced
    errors:
      - code: BID_BELOW_MINIMUM
        message: "Bid amount is below minimum"
        http_status: 422
      - code: AUCTION_CLOSED
        message: "Auction has already closed"
        http_status: 410
    writes_to:
      - Bid
    transaction: true
```

**Expected Output:**
- File: `app/commands/place_bid/command.py`
- Contains: `class PlaceBidCommand`, `guard_type: auth`, `guard_type: tenant_scope`, `guard_type: rate_limit`, `limit: 20`, `window: 1m`, `effect_type: publish_event`, `BidPlaced`

### B01-CQS-16: GetOrdersByFilter query with multiple AND/OR filters via FilterGroup

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Order search with complex filter logic: (status is 'pending' OR status is 'processing') AND (created_at > '2026-01-01') for an advanced order management UI.

**Input DSL:**
```yaml
queries:
  - id: GetOrdersByFilter
    description: "Complex filter with AND/OR nested logic"
    reads_from: Order
    filters:
      - operator: and
        filters:
          - operator: or
            filters:
              - field: status
                operator: eq
                value: pending
              - field: status
                operator: eq
                value: processing
          - field: created_at
            operator: gte
            value: "2026-01-01T00:00:00Z"
    pagination:
      type: offset
      page_size: 20
    sort:
      - field: created_at
        direction: desc
    guards:
      - guard_type: auth
        permission: "order.read"
      - guard_type: tenant_scope
        mode: tenant_isolated
```

**Expected Output:**
- File: `app/queries/get_orders_by_filter/handler.py`
- Contains: `class GetOrdersByFilterHandler`, `filter_group: and`, `filter_group: or`, `field: status`, `operator: eq`, `field: created_at`, `operator: gte`

### B01-CQS-17: ApproveLoan command with conditional effect based on amount

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Loan approval system where large loans (amount > 10000) trigger an additional COMPLIANCE_CHECK effect for regulatory review before approval.

**Input DSL:**
```yaml
commands:
  - id: ApproveLoan
    description: "Approve loan with conditional compliance check for large amounts"
    category: update
    input:
      - name: loan_id
        type: uuid
        required: true
      - name: approval_status
        type: enum
        required: true
        enum_values:
          - approved
          - rejected
          - pending_review
      - name: amount
        type: decimal
        required: true
    guards:
      - guard_type: auth
        permission: "loan.approve"
      - guard_type: kyc_check
    effects:
      - effect_type: update_record
        entity: Loan
      - effect_type: check_compliance
        condition: "amount > 10000"
      - effect_type: write_audit_log
        audit_action: loan_approval
    writes_to:
      - Loan
    transaction: true
```

**Expected Output:**
- File: `app/commands/approve_loan/command.py`
- Contains: `class ApproveLoanCommand`, `guard_type: kyc_check`, `effect_type: check_compliance`, `condition: "amount > 10000"`, `write_audit_log`, `loan_approval`

### B01-CQS-18: UpsertProduct command with UPSERT_RECORD effect

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Product catalog synchronization that upserts (insert or update) product records from an external supplier feed, creating new products or updating existing ones by SKU.

**Input DSL:**
```yaml
commands:
  - id: UpsertProduct
    description: "Upsert product from supplier catalog sync"
    category: custom
    input:
      - name: sku
        type: string
        required: true
        min_length: 3
        max_length: 50
      - name: name
        type: string
        required: true
      - name: price
        type: decimal
        required: true
      - name: supplier_id
        type: uuid
        required: true
    guards:
      - guard_type: auth
        permission: "product.sync"
    effects:
      - effect_type: upsert_record
        entity: Product
      - effect_type: publish_event
        event: ProductSynced
    writes_to:
      - Product
```

**Expected Output:**
- File: `app/commands/upsert_product/command.py`
- Contains: `class UpsertProductCommand`, `effect_type: upsert_record`, `entity: Product`, `effect_type: publish_event`, `ProductSynced`

### B01-CQS-19: GetIncompleteOrders query with IS_NULL and IS_NOT_NULL filters

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Find orders where the shipping address is missing (IS_NULL) but the payment confirmation exists (IS_NOT_NULL), for order fulfillment triage.

**Input DSL:**
```yaml
queries:
  - id: GetIncompleteOrders
    description: "Find orders with missing shipping info but confirmed payment"
    reads_from: Order
    filters:
      - field: shipping_address
        operator: is_null
      - field: payment_confirmation
        operator: is_not_null
    pagination:
      type: offset
      page_size: 50
    sort:
      - field: created_at
        direction: asc
    guards:
      - guard_type: auth
        permission: "order.read"
      - guard_type: tenant_scope
        mode: tenant_isolated
    effects:
      - effect_type: write_audit_log
        audit_action: incomplete_order_query
```

**Expected Output:**
- File: `app/queries/get_incomplete_orders/handler.py`
- Contains: `class GetIncompleteOrdersHandler`, `field: shipping_address`, `operator: is_null`, `field: payment_confirmation`, `operator: is_not_null`, `write_audit_log`

### B01-CQS-20: WebhookDispatch command with CALL_EXTERNAL_API and WEBHOOK effects

**Capability:** `command_query_separation`
**Stack:** `both`

**Use Case:** Outbound webhook system that calls an external API endpoint and dispatches a webhook payload when an order is delivered, with retry on failure.

**Input DSL:**
```yaml
commands:
  - id: WebhookDispatch
    description: "Dispatch webhook notification to external system"
    category: custom
    input:
      - name: webhook_url
        type: string
        required: true
      - name: event_type
        type: string
        required: true
      - name: payload
        type: json
        required: true
    guards:
      - guard_type: auth
        permission: "webhook.dispatch"
      - guard_type: rate_limit
        limit: 100
        window: 1m
    effects:
      - effect_type: call_external_api
      - effect_type: webhook
    errors:
      - code: WEBHOOK_DELIVERY_FAILED
        message: "Failed to deliver webhook to external endpoint"
        http_status: 502
        retryable: true
    writes_to: []
```

**Expected Output:**
- File: `app/commands/webhook_dispatch/command.py`
- Contains: `class WebhookDispatchCommand`, `effect_type: call_external_api`, `effect_type: webhook`, `guard_type: rate_limit`, `WEBHOOK_DELIVERY_FAILED`, `retryable: true`
