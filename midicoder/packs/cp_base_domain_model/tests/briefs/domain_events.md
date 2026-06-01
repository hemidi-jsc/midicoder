# UAT Briefs — B01: domain_events

> Capability: `domain_events` | DomainEvent DSL definition
> Coverage: Event types (FACT, INTENTION, STATE_CHANGE), immutability, event properties, command effects with PUBLISH_EVENT, recipe integration

---

### B01-EVT-01: OrderCreated (FACT event with order_id, customer_id, total)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** E-commerce system emits an OrderCreated event when a customer places an order. This is a FACT event — it records something that already happened and cannot be undone.

**Input DSL:**
```yaml
events:
  - id: OrderCreated
    event_type: fact
    aggregate_id: Order
    fields:
      - name: order_id
        type: uuid
      - name: customer_id
        type: uuid
      - name: total
        type: decimal
        precision: 10
        scale: 2
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class OrderCreated` dataclass with `order_id: UUID`, `customer_id: UUID`, `total: Decimal`, plus `occurred_on: datetime`, `immutable = True`

---

### B01-EVT-02: PaymentInitiated (INTENTION event with amount, method)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Payment gateway initiates a payment. This is an INTENTION event — the payment may succeed or fail, so downstream consumers should treat it as a pending action rather than a completed fact.

**Input DSL:**
```yaml
events:
  - id: PaymentInitiated
    event_type: intention
    aggregate_id: Payment
    fields:
      - name: payment_id
        type: uuid
      - name: amount
        type: decimal
        precision: 12
        scale: 2
      - name: method
        type: string
        enum_values:
          - credit_card
          - bank_transfer
          - wallet
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class PaymentInitiated` dataclass with `payment_id`, `amount`, `method` fields, `event_type = "intention"`

---

### B01-EVT-03: UserStatusChanged (STATE_CHANGE event with old_status, new_status)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** User account status changes from "active" to "suspended". This is a STATE_CHANGE event — it captures the before-and-after state for audit trail and compliance reporting.

**Input DSL:**
```yaml
events:
  - id: UserStatusChanged
    event_type: state_change
    aggregate_id: User
    fields:
      - name: user_id
        type: uuid
      - name: old_status
        type: string
      - name: new_status
        type: string
      - name: changed_by
        type: uuid
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class UserStatusChanged` dataclass with `old_status`, `new_status`, `changed_by` fields, `event_type = "state_change"`

---

### B01-EVT-04: InventoryDepleted (FACT with product_id, warehouse_id)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Warehouse inventory for a specific product drops to zero. This FACT event triggers automatic reorder workflows and notifies procurement teams.

**Input DSL:**
```yaml
events:
  - id: InventoryDepleted
    event_type: fact
    aggregate_id: Inventory
    fields:
      - name: product_id
        type: uuid
      - name: warehouse_id
        type: uuid
      - name: depleted_at
        type: datetime
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class InventoryDepleted` dataclass with `product_id`, `warehouse_id`, `depleted_at` fields, immutable once emitted

---

### B01-EVT-05: OrderCancelled (INTENTION with reason, refund_amount)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Customer requests order cancellation. INTENTION event because the cancellation may be rejected if the order has already been shipped. Includes reason and refund amount for financial reconciliation.

**Input DSL:**
```yaml
events:
  - id: OrderCancelled
    event_type: intention
    aggregate_id: Order
    fields:
      - name: order_id
        type: uuid
      - name: reason
        type: string
      - name: refund_amount
        type: decimal
        precision: 10
        scale: 2
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class OrderCancelled` dataclass with `order_id`, `reason`, `refund_amount`, `event_type = "intention"`

---

### B01-EVT-06: AccountFrozen (STATE_CHANGE with reason, frozen_by)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Bank freezes a suspicious account. STATE_CHANGE event captures transition from "active" to "frozen", including the compliance officer who triggered it and the regulatory reason.

**Input DSL:**
```yaml
events:
  - id: AccountFrozen
    event_type: state_change
    aggregate_id: BankAccount
    fields:
      - name: account_id
        type: uuid
      - name: reason
        type: string
      - name: frozen_by
        type: uuid
      - name: regulatory_code
        type: string
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class AccountFrozen` dataclass with `account_id`, `reason`, `frozen_by`, `regulatory_code`, `event_type = "state_change"`

---

### B01-EVT-07: ShipmentDispatched (FACT with tracking_number, carrier)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Logistics system dispatches a shipment. FACT event with tracking number and carrier name, consumed by customer notification service to send shipping updates.

**Input DSL:**
```yaml
events:
  - id: ShipmentDispatched
    event_type: fact
    aggregate_id: Shipment
    fields:
      - name: shipment_id
        type: uuid
      - name: tracking_number
        type: string
      - name: carrier
        type: string
      - name: dispatched_at
        type: datetime
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class ShipmentDispatched` dataclass with `shipment_id`, `tracking_number`, `carrier`, `dispatched_at` fields

---

### B01-EVT-08: PrescriptionApproved (INTENTION with doctor_id, medication)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Doctor approves a patient's prescription. INTENTION event because the pharmacy may reject the medication due to stock issues or drug interactions before fulfillment.

**Input DSL:**
```yaml
events:
  - id: PrescriptionApproved
    event_type: intention
    aggregate_id: Prescription
    fields:
      - name: prescription_id
        type: uuid
      - name: doctor_id
        type: uuid
      - name: medication
        type: string
      - name: dosage
        type: string
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class PrescriptionApproved` dataclass with `prescription_id`, `doctor_id`, `medication`, `dosage`, `event_type = "intention"`

---

### B01-EVT-09: SubscriptionExpired (STATE_CHANGE with expiry_date, renewal_flag)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** SaaS subscription reaches its expiry date. STATE_CHANGE event transitions subscription from "active" to "expired". The renewal_flag indicates whether auto-renewal was attempted.

**Input DSL:**
```yaml
events:
  - id: SubscriptionExpired
    event_type: state_change
    aggregate_id: Subscription
    fields:
      - name: subscription_id
        type: uuid
      - name: expiry_date
        type: datetime
      - name: renewal_flag
        type: boolean
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class SubscriptionExpired` dataclass with `subscription_id`, `expiry_date`, `renewal_flag`, `event_type = "state_change"`

---

### B01-EVT-10: FraudAlertTriggered (FACT with user_id, transaction_id, risk_score)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Fraud detection system flags a suspicious transaction. FACT event with a risk score (0-100), triggering immediate review workflow and potential account lock.

**Input DSL:**
```yaml
events:
  - id: FraudAlertTriggered
    event_type: fact
    aggregate_id: Transaction
    fields:
      - name: user_id
        type: uuid
      - name: transaction_id
        type: uuid
      - name: risk_score
        type: float
      - name: alert_reason
        type: string
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class FraudAlertTriggered` dataclass with `user_id`, `transaction_id`, `risk_score`, `alert_reason`, immutable once emitted

---

### B01-EVT-11: BatchImportCompleted (FACT with total_records, success_count, error_count)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Bulk data import job finishes processing. FACT event summarizing total records processed, successful imports, and failed records for operations monitoring.

**Input DSL:**
```yaml
events:
  - id: BatchImportCompleted
    event_type: fact
    aggregate_id: BatchJob
    fields:
      - name: job_id
        type: uuid
      - name: total_records
        type: integer
      - name: success_count
        type: integer
      - name: error_count
        type: integer
      - name: completed_at
        type: datetime
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class BatchImportCompleted` dataclass with `job_id`, `total_records`, `success_count`, `error_count`, `completed_at`

---

### B01-EVT-12: PriceUpdated (STATE_CHANGE with old_price, new_price, effective_date)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Product price is updated in the catalog. STATE_CHANGE event captures old and new prices along with the effective date, enabling price history tracking and customer notification.

**Input DSL:**
```yaml
events:
  - id: PriceUpdated
    event_type: state_change
    aggregate_id: Product
    fields:
      - name: product_id
        type: uuid
      - name: old_price
        type: decimal
        precision: 10
        scale: 2
      - name: new_price
        type: decimal
        precision: 10
        scale: 2
      - name: effective_date
        type: datetime
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class PriceUpdated` dataclass with `product_id`, `old_price`, `new_price`, `effective_date`, `event_type = "state_change"`

---

### B01-EVT-13: ReviewSubmitted (INTENTION with rating, comment)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Customer submits a product review. INTENTION event because the review must pass moderation before being publicly visible. Rating and comment are stored for the moderation queue.

**Input DSL:**
```yaml
events:
  - id: ReviewSubmitted
    event_type: intention
    aggregate_id: Review
    fields:
      - name: review_id
        type: uuid
      - name: product_id
        type: uuid
      - name: rating
        type: integer
      - name: comment
        type: text
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class ReviewSubmitted` dataclass with `review_id`, `product_id`, `rating`, `comment`, `event_type = "intention"`

---

### B01-EVT-14: ContractSigned (FACT with parties, effective_date, value)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Legal system records a signed contract. FACT event with parties involved, contract effective date, and contract value. Consumed by billing, compliance, and document management services.

**Input DSL:**
```yaml
events:
  - id: ContractSigned
    event_type: fact
    aggregate_id: Contract
    fields:
      - name: contract_id
        type: uuid
      - name: parties
        type: json
      - name: effective_date
        type: datetime
      - name: value
        type: decimal
        precision: 15
        scale: 2
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class ContractSigned` dataclass with `contract_id`, `parties: dict`, `effective_date`, `value`, immutable

---

### B01-EVT-15: AccountDeactivated (STATE_CHANGE with deactivated_by, reason)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** User account is deactivated (by admin or user self-request). STATE_CHANGE event for audit logging and downstream service notification (e.g., revoke API keys, cancel subscriptions).

**Input DSL:**
```yaml
events:
  - id: AccountDeactivated
    event_type: state_change
    aggregate_id: User
    fields:
      - name: user_id
        type: uuid
      - name: deactivated_by
        type: uuid
      - name: reason
        type: string
      - name: deactivated_at
        type: datetime
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class AccountDeactivated` dataclass with `user_id`, `deactivated_by`, `reason`, `deactivated_at`, `event_type = "state_change"`

---

### B01-EVT-16: ClaimFiled (INTENTION with claim_type, amount, incident_date)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Insurance claim is filed by a policyholder. INTENTION event because the claim must be investigated and may be rejected. Includes claim type, requested amount, and incident date.

**Input DSL:**
```yaml
events:
  - id: ClaimFiled
    event_type: intention
    aggregate_id: InsuranceClaim
    fields:
      - name: claim_id
        type: uuid
      - name: policy_id
        type: uuid
      - name: claim_type
        type: string
      - name: amount
        type: decimal
        precision: 12
        scale: 2
      - name: incident_date
        type: datetime
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class ClaimFiled` dataclass with `claim_id`, `policy_id`, `claim_type`, `amount`, `incident_date`, `event_type = "intention"`

---

### B01-EVT-17: ComplianceViolationDetected (FACT with violation_type, severity)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Automated compliance monitoring detects a policy violation. FACT event with violation type and severity level, triggering immediate regulatory reporting and incident response.

**Input DSL:**
```yaml
events:
  - id: ComplianceViolationDetected
    event_type: fact
    aggregate_id: ComplianceAudit
    fields:
      - name: audit_id
        type: uuid
      - name: violation_type
        type: string
      - name: severity
        type: string
        enum_values:
          - low
          - medium
          - high
          - critical
      - name: detected_at
        type: datetime
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class ComplianceViolationDetected` dataclass with `audit_id`, `violation_type`, `severity` (enum), `detected_at`

---

### B01-EVT-18: ScheduleChanged (STATE_CHANGE with old_time, new_time, affected_items)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Meeting scheduler reschedules an event. STATE_CHANGE event captures the old and new time slots along with affected items (attendees, resources). Consumed by notification service to alert attendees.

**Input DSL:**
```yaml
events:
  - id: ScheduleChanged
    event_type: state_change
    aggregate_id: Schedule
    fields:
      - name: schedule_id
        type: uuid
      - name: old_time
        type: datetime
      - name: new_time
        type: datetime
      - name: affected_items
        type: json
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class ScheduleChanged` dataclass with `schedule_id`, `old_time`, `new_time`, `affected_items: dict`, `event_type = "state_change"`

---

### B01-EVT-19: NotificationSent (FACT with recipient_id, channel, template)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** Notification system sends an alert to a user. FACT event with recipient ID, delivery channel (email/SMS/push), and template used. Used for notification analytics and delivery confirmation tracking.

**Input DSL:**
```yaml
events:
  - id: NotificationSent
    event_type: fact
    aggregate_id: Notification
    fields:
      - name: notification_id
        type: uuid
      - name: recipient_id
        type: uuid
      - name: channel
        type: string
        enum_values:
          - email
          - sms
          - push
      - name: template
        type: string
```

**Expected Output:**
- File: `app/models/domain_events.py`
- Contains: `class NotificationSent` dataclass with `notification_id`, `recipient_id`, `channel` (enum), `template`

---

### B01-EVT-20: Multi-event command (Command that publishes 3 events in sequence)

**Capability:** `domain_events`  
**Stack:** `both`

**Use Case:** A single command `ProcessPayment` publishes three events in sequence: PaymentInitiated (INTENTION), PaymentProcessed (FACT), and AccountBalanceChanged (STATE_CHANGE). Demonstrates command with multiple PUBLISH_EVENT effects.

**Input DSL:**
```yaml
events:
  - id: PaymentInitiated
    event_type: intention
    aggregate_id: Payment
    fields:
      - name: payment_id
        type: uuid
      - name: amount
        type: decimal
  - id: PaymentProcessed
    event_type: fact
    aggregate_id: Payment
    fields:
      - name: payment_id
        type: uuid
      - name: amount
        type: decimal
      - name: gateway_response
        type: string
  - id: AccountBalanceChanged
    event_type: state_change
    aggregate_id: BankAccount
    fields:
      - name: account_id
        type: uuid
      - name: old_balance
        type: decimal
      - name: new_balance
        type: decimal

commands:
  - id: ProcessPayment
    effects:
      - type: publish_event
        event: PaymentInitiated
      - type: update_record
        entity: Payment
      - type: publish_event
        event: PaymentProcessed
      - type: update_record
        entity: BankAccount
      - type: publish_event
        event: AccountBalanceChanged
```

**Expected Output:**
- File: `app/commands/process_payment_effects.py`
- Contains: Three `PUBLISH_EVENT` effects wired to `PaymentInitiated`, `PaymentProcessed`, `AccountBalanceChanged`, with intermediate `UPDATE_RECORD` effects on Payment and BankAccount entities
