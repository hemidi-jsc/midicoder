# UAT Briefs — B01: cqrs_projection

> Capability: `cqrs_projection` | Projection DSL definition
> Coverage: Projection types (DENORMALIZED, MATERIALIZED_VIEW, SEARCH_INDEX, GRAPH), event subscription, read-optimized model, ProjectionRecipe

---

### B01-CQR-01: OrderSummary projection (DENORMALIZED from OrderCreated event)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Dashboard needs a flattened OrderSummary view combining order ID, customer name, total, and status. DENORMALIZED projection subscribes to OrderCreated and avoids JOIN queries at read time.

**Input DSL:**
```yaml
projections:
  - id: OrderSummary
    projection_type: denormalized
    source_aggregate: Order
    source_events:
      - OrderCreated
    fields:
      - name: order_id
        type: uuid
      - name: customer_name
        type: string
      - name: total
        type: decimal
        precision: 10
        scale: 2
      - name: status
        type: string
      - name: created_at
        type: datetime
```

**Expected Output:**
- File: `app/models/order_summary.py`
- Contains: `class OrderSummary` with `order_id`, `customer_name`, `total`, `status`, `created_at` fields, projection_type = `denormalized`, event handler for `OrderCreated`

---

### B01-CQR-02: UserDashboard projection (MATERIALIZED_VIEW from multiple user events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** User profile dashboard aggregates data from ProfileUpdated, PreferencesChanged, and AccountDeactivated events into a single MATERIALIZED_VIEW for instant rendering without multiple database queries.

**Input DSL:**
```yaml
projections:
  - id: UserDashboard
    projection_type: materialized_view
    source_aggregate: User
    source_events:
      - ProfileUpdated
      - PreferencesChanged
      - AccountDeactivated
    fields:
      - name: user_id
        type: uuid
      - name: display_name
        type: string
      - name: avatar_url
        type: string
      - name: theme
        type: string
      - name: account_status
        type: string
```

**Expected Output:**
- File: `app/models/user_dashboard.py`
- Contains: `class UserDashboard` with MATERIALIZED_VIEW projection, event handlers for all three source events, and cached aggregate state

---

### B01-CQR-03: ProductSearchIndex (SEARCH_INDEX from ProductCreated/Updated events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** E-commerce product search uses a SEARCH_INDEX projection synced with ProductCreated and ProductUpdated events. Supports full-text search, faceting, and relevance ranking.

**Input DSL:**
```yaml
projections:
  - id: ProductSearchIndex
    projection_type: search_index
    source_aggregate: Product
    source_events:
      - ProductCreated
      - ProductUpdated
      - PriceUpdated
    fields:
      - name: product_id
        type: uuid
      - name: title
        type: string
      - name: description
        type: text
      - name: category
        type: string
      - name: price
        type: decimal
      - name: in_stock
        type: boolean
```

**Expected Output:**
- File: `app/models/product_search_index.py`
- Contains: `class ProductSearchIndex` with SEARCH_INDEX projection_type, text-analyzed `title` and `description` fields, and event sync for ProductCreated/ProductUpdated/PriceUpdated

---

### B01-CQR-04: SalesReport projection (DENORMALIZED from OrderPaid events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Finance team needs a sales report projection that accumulates order payment data. DENORMALIZED projection avoids joining orders, payments, and customers tables.

**Input DSL:**
```yaml
projections:
  - id: SalesReport
    projection_type: denormalized
    source_aggregate: Order
    source_events:
      - OrderPaid
    fields:
      - name: order_id
        type: uuid
      - name: customer_id
        type: uuid
      - name: amount
        type: decimal
        precision: 12
        scale: 2
      - name: paid_at
        type: datetime
      - name: payment_method
        type: string
```

**Expected Output:**
- File: `app/models/sales_report.py`
- Contains: `class SalesReport` with DENORMALIZED projection, event handler for OrderPaid, with all fields flattened for reporting queries

---

### B01-CQR-05: Customer360 projection (GRAPH from all customer-related events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Customer support needs a 360-degree view of each customer, connecting orders, support tickets, and payment history. GRAPH projection models the relationships between entities for traversable queries.

**Input DSL:**
```yaml
projections:
  - id: Customer360
    projection_type: graph
    source_aggregate: User
    source_events:
      - OrderCreated
      - OrderPaid
      - SupportTicketCreated
      - PaymentInitiated
      - AccountDeactivated
    fields:
      - name: customer_id
        type: uuid
      - name: total_orders
        type: integer
      - name: total_spent
        type: decimal
        precision: 12
        scale: 2
      - name: open_tickets
        type: integer
      - name: last_activity
        type: datetime
```

**Expected Output:**
- File: `app/models/customer_360.py`
- Contains: `class Customer360` with GRAPH projection_type, relationship edges to Order, SupportTicket, and Payment nodes, updated by all five source events

---

### B01-CQR-06: InventoryStatus projection (MATERIALIZED_VIEW from Inventory events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Warehouse management dashboard shows real-time inventory status. MATERIALIZED_VIEW pre-computes stock levels, reorder thresholds, and warehouse distribution for fast lookup.

**Input DSL:**
```yaml
projections:
  - id: InventoryStatus
    projection_type: materialized_view
    source_aggregate: Warehouse
    source_events:
      - StockReceived
      - StockDispatched
      - InventoryRecounted
    fields:
      - name: warehouse_id
        type: uuid
      - name: product_id
        type: uuid
      - name: current_stock
        type: integer
      - name: reorder_level
        type: integer
      - name: last_recounted
        type: datetime
```

**Expected Output:**
- File: `app/models/inventory_status.py`
- Contains: `class InventoryStatus` with MATERIALIZED_VIEW, event handlers for StockReceived/StockDispatched/InventoryRecounted, and pre-computed `current_stock`

---

### B01-CQR-07: TransactionHistory projection (DENORMALIZED from Payment events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Banking statement view. DENORMALIZED projection aggregates all payment events (deposits, withdrawals, transfers) into a flat transaction list sorted by date.

**Input DSL:**
```yaml
projections:
  - id: TransactionHistory
    projection_type: denormalized
    source_aggregate: BankAccount
    source_events:
      - Deposited
      - Withdrawn
      - Transferred
    fields:
      - name: transaction_id
        type: uuid
      - name: account_id
        type: uuid
      - name: type
        type: string
      - name: amount
        type: decimal
        precision: 12
        scale: 2
      - name: counterparty
        type: string
      - name: occurred_at
        type: datetime
```

**Expected Output:**
- File: `app/models/transaction_history.py`
- Contains: `class TransactionHistory` with DENORMALIZED projection, unified `type` field for deposit/withdraw/transfer, event handlers for all three source events

---

### B01-CQR-08: PatientTimeline projection (GRAPH from Visit/Prescription events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Medical records system shows a patient's complete health timeline. GRAPH projection links visits, prescriptions, lab results, and diagnoses into a traversable health history graph.

**Input DSL:**
```yaml
projections:
  - id: PatientTimeline
    projection_type: graph
    source_aggregate: Patient
    source_events:
      - VisitRecorded
      - PrescriptionIssued
      - LabResultAvailable
    fields:
      - name: patient_id
        type: uuid
      - name: event_type
        type: string
      - name: event_date
        type: datetime
      - name: provider_id
        type: uuid
      - name: summary
        type: text
```

**Expected Output:**
- File: `app/models/patient_timeline.py`
- Contains: `class PatientTimeline` with GRAPH projection, event nodes for visits/prescriptions/lab_results, linked by chronological edges

---

### B01-CQR-09: Leaderboard projection (MATERIALIZED_VIEW from ScoreUpdated events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Gaming platform leaderboard. MATERIALIZED_VIEW pre-sorts and caches player rankings from ScoreUpdated events, enabling O(1) top-N queries without full table scans.

**Input DSL:**
```yaml
projections:
  - id: Leaderboard
    projection_type: materialized_view
    source_aggregate: Player
    source_events:
      - ScoreUpdated
    fields:
      - name: player_id
        type: uuid
      - name: player_name
        type: string
      - name: total_score
        type: integer
      - name: rank
        type: integer
      - name: last_updated
        type: datetime
```

**Expected Output:**
- File: `app/models/leaderboard.py`
- Contains: `class Leaderboard` with MATERIALIZED_VIEW, pre-computed `rank` field, and automatic re-sort on ScoreUpdated event

---

### B01-CQR-10: AuditTrail projection (DENORMALIZED from all state change events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Compliance audit trail. DENORMALIZED projection captures every state change across the system into a unified, append-only audit log for regulatory review.

**Input DSL:**
```yaml
projections:
  - id: AuditTrail
    projection_type: denormalized
    source_aggregate: System
    source_events:
      - UserStatusChanged
      - AccountFrozen
      - AccountDeactivated
      - ScheduleChanged
      - PriceUpdated
    fields:
      - name: audit_id
        type: uuid
      - name: entity_type
        type: string
      - name: entity_id
        type: uuid
      - name: action
        type: string
      - name: performed_by
        type: uuid
      - name: performed_at
        type: datetime
```

**Expected Output:**
- File: `app/models/audit_trail.py`
- Contains: `class AuditTrail` with DENORMALIZED projection, append-only insert on each state change event, indexed by `entity_type` and `performed_at`

---

### B01-CQR-11: SearchFacets projection (SEARCH_INDEX with aggregated filters)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** E-commerce product browsing with faceted search. SEARCH_INDEX projection maintains pre-computed facet counts (price ranges, brands, categories) for instant filter UI updates.

**Input DSL:**
```yaml
projections:
  - id: SearchFacets
    projection_type: search_index
    source_aggregate: Product
    source_events:
      - ProductCreated
      - ProductUpdated
      - ProductDeleted
    fields:
      - name: category
        type: string
      - name: brand
        type: string
      - name: price_range
        type: string
      - name: availability
        type: string
      - name: facet_count
        type: integer
```

**Expected Output:**
- File: `app/models/search_facets.py`
- Contains: `class SearchFacets` with SEARCH_INDEX projection, pre-aggregated `facet_count` per category/brand/price_range combination

---

### B01-CQR-12: RevenueProjection (DENORMALIZED with SUM/AVG aggregations)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Finance dashboard showing monthly revenue. DENORMALIZED projection maintains running SUM and AVG aggregations from OrderPaid events, updated incrementally on each new payment.

**Input DSL:**
```yaml
projections:
  - id: RevenueProjection
    projection_type: denormalized
    source_aggregate: Order
    source_events:
      - OrderPaid
    fields:
      - name: month
        type: string
      - name: total_revenue
        type: decimal
        precision: 15
        scale: 2
      - name: order_count
        type: integer
      - name: avg_order_value
        type: decimal
        precision: 12
        scale: 2
```

**Expected Output:**
- File: `app/models/revenue_projection.py`
- Contains: `class RevenueProjection` with DENORMALIZED projection, incremental SUM/AVG computation on OrderPaid events, partitioned by `month`

---

### B01-CQR-13: NotificationFeed projection (MATERIALIZED_VIEW from Notification events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** In-app notification bell. MATERIALIZED_VIEW projection caches each user's notification feed sorted by recency, with read/unread status for O(1) feed retrieval.

**Input DSL:**
```yaml
projections:
  - id: NotificationFeed
    projection_type: materialized_view
    source_aggregate: Notification
    source_events:
      - NotificationSent
      - NotificationRead
    fields:
      - name: notification_id
        type: uuid
      - name: recipient_id
        type: uuid
      - name: message
        type: text
      - name: is_read
        type: boolean
      - name: created_at
        type: datetime
```

**Expected Output:**
- File: `app/models/notification_feed.py`
- Contains: `class NotificationFeed` with MATERIALIZED_VIEW, `is_read` flag updated by NotificationRead events, indexed by `recipient_id` and `created_at DESC`

---

### B01-CQR-14: ComplianceReport projection (DENORMALIZED from audit events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Regulatory compliance report. DENORMALIZED projection aggregates compliance violations, audit findings, and remediation status from multiple audit events into a single report view.

**Input DSL:**
```yaml
projections:
  - id: ComplianceReport
    projection_type: denormalized
    source_aggregate: ComplianceAudit
    source_events:
      - ComplianceViolationDetected
      - RemediationCompleted
    fields:
      - name: report_id
        type: uuid
      - name: violation_type
        type: string
      - name: severity
        type: string
      - name: status
        type: string
      - name: detected_at
        type: datetime
      - name: resolved_at
        type: datetime
```

**Expected Output:**
- File: `app/models/compliance_report.py`
- Contains: `class ComplianceReport` with DENORMALIZED projection, `resolved_at` populated by RemediationCompleted event, status transitions from "open" to "resolved"

---

### B01-CQR-15: ActivityStream projection (GRAPH from all user activity events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Social platform activity feed. GRAPH projection connects user actions (posts, likes, comments, follows) into a timeline graph for "who did what to whom" queries.

**Input DSL:**
```yaml
projections:
  - id: ActivityStream
    projection_type: graph
    source_aggregate: User
    source_events:
      - PostCreated
      - PostLiked
      - CommentAdded
      - UserFollowed
    fields:
      - name: activity_id
        type: uuid
      - name: actor_id
        type: uuid
      - name: action
        type: string
      - name: target_id
        type: uuid
      - name: occurred_at
        type: datetime
```

**Expected Output:**
- File: `app/models/activity_stream.py`
- Contains: `class ActivityStream` with GRAPH projection, actor-action-target triplets, edges linking users to their activities, updated by all four source events

---

### B01-CQR-16: StockSnapshot projection (MATERIALIZED_VIEW from PriceUpdated events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Financial trading platform. MATERIALIZED_VIEW projection captures stock price snapshots at regular intervals from PriceUpdated events, enabling chart rendering and technical analysis.

**Input DSL:**
```yaml
projections:
  - id: StockSnapshot
    projection_type: materialized_view
    source_aggregate: Stock
    source_events:
      - PriceUpdated
    fields:
      - name: symbol
        type: string
      - name: price
        type: decimal
        precision: 10
        scale: 4
      - name: volume
        type: integer
      - name: snapshot_at
        type: datetime
      - name: change_percent
        type: float
```

**Expected Output:**
- File: `app/models/stock_snapshot.py`
- Contains: `class StockSnapshot` with MATERIALIZED_VIEW, computed `change_percent` from previous price, indexed by `symbol` and `snapshot_at`

---

### B01-CQR-17: SubscriptionStatus projection (DENORMALIZED from Sub events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Billing dashboard showing current subscription status. DENORMALIZED projection consolidates SubCreated, SubRenewed, and SubCancelled events into a single-status view per subscription.

**Input DSL:**
```yaml
projections:
  - id: SubscriptionStatus
    projection_type: denormalized
    source_aggregate: Subscription
    source_events:
      - SubCreated
      - SubRenewed
      - SubCancelled
    fields:
      - name: subscription_id
        type: uuid
      - name: user_id
        type: uuid
      - name: plan
        type: string
      - name: status
        type: string
      - name: current_period_end
        type: datetime
      - name: cancelled_at
        type: datetime
```

**Expected Output:**
- File: `app/models/subscription_status.py`
- Contains: `class SubscriptionStatus` with DENORMALIZED projection, `status` updated by SubRenewed (→ active) and SubCancelled (→ cancelled, sets `cancelled_at`)

---

### B01-CQR-18: ClaimDashboard projection (MATERIALIZED_VIEW from Claim events)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Insurance adjuster dashboard. MATERIALIZED_VIEW projection pre-computes claim counts by status (open, under_review, approved, denied) and total payout amounts for management overview.

**Input DSL:**
```yaml
projections:
  - id: ClaimDashboard
    projection_type: materialized_view
    source_aggregate: InsuranceClaim
    source_events:
      - ClaimFiled
      - ClaimApproved
      - ClaimDenied
      - ClaimPaid
    fields:
      - name: policy_id
        type: uuid
      - name: total_claims
        type: integer
      - name: open_claims
        type: integer
      - name: total_payout
        type: decimal
        precision: 14
        scale: 2
      - name: last_claim_date
        type: datetime
```

**Expected Output:**
- File: `app/models/claim_dashboard.py`
- Contains: `class ClaimDashboard` with MATERIALIZED_VIEW, pre-computed `total_claims`, `open_claims`, `total_payout` counters, updated by all four claim events

---

### B01-CQR-19: Multi-source projection (subscribes to 5+ different event types)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Enterprise operations dashboard aggregates data from multiple domains: orders, inventory, shipments, payments, and support. Single projection subscribes to 5+ event types to build a unified operational view.

**Input DSL:**
```yaml
projections:
  - id: OpsDashboard
    projection_type: denormalized
    source_aggregate: System
    source_events:
      - OrderCreated
      - OrderPaid
      - InventoryDepleted
      - ShipmentDispatched
      - FraudAlertTriggered
    fields:
      - name: metric_key
        type: string
      - name: metric_value
        type: decimal
        precision: 15
        scale: 2
      - name: event_source
        type: string
      - name: recorded_at
        type: datetime
```

**Expected Output:**
- File: `app/models/ops_dashboard.py`
- Contains: `class OpsDashboard` with DENORMALIZED projection, five event handlers (OrderCreated, OrderPaid, InventoryDepleted, ShipmentDispatched, FraudAlertTriggered), `event_source` discriminator field

---

### B01-CQR-20: Full-text search index (SEARCH_INDEX with relevance scoring)

**Capability:** `cqrs_projection`  
**Stack:** `both`

**Use Case:** Knowledge base search. SEARCH_INDEX projection with TF-IDF-style relevance scoring over article content, updated whenever articles are created, modified, or deleted.

**Input DSL:**
```yaml
projections:
  - id: KnowledgeBaseSearch
    projection_type: search_index
    source_aggregate: Article
    source_events:
      - ArticlePublished
      - ArticleUpdated
      - ArticleDeleted
    fields:
      - name: article_id
        type: uuid
      - name: title
        type: string
      - name: body
        type: text
      - name: tags
        type: json
      - name: relevance_score
        type: float
      - name: published_at
        type: datetime
```

**Expected Output:**
- File: `app/models/knowledge_base_search.py`
- Contains: `class KnowledgeBaseSearch` with SEARCH_INDEX projection, text-analyzed `title` and `body` fields, computed `relevance_score`, indexed for full-text query with ranking
