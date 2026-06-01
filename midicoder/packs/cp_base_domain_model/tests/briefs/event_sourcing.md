# UAT Briefs — B01 Event Sourcing (event_sourcing.md)

> Capability: `event_sourcing` | Definition: `EventSourcedAggregate`
> Focus: Aggregates that reconstruct state from event log with snapshots, compression, versioned OCC, and replay.

---

### B01-ES-01: BankAccount with append-only event log (BalanceChanged events)

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Core banking ledger that records every deposit/withdrawal as an immutable event. State is derived by replaying the event log, never by reading a current balance column.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: BankAccount
  root_entity: BankAccount
  events:
    - Deposited
    - Withdrawn
  eventing_strategy: APPEND_ONLY
  snapshot_interval: 0
  versioned: true
```

**Expected Output:**
- File: `app/models/bank_account.py`
- Contains: `eventing_strategy` set to `APPEND_ONLY`, `snapshot_interval` equal to `0`, `version` field for OCC, and `Deposited`/`Withdrawn` event classes

---

### B01-ES-02: ShoppingCart with snapshot at every 10 events

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** E-commerce shopping cart that takes a snapshot every 10 item changes to avoid replaying hundreds of AddItem/RemoveItem events on checkout.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: ShoppingCart
  root_entity: ShoppingCart
  events:
    - ItemAdded
    - ItemRemoved
    - QuantityChanged
  eventing_strategy: SNAPSHOT
  snapshot_interval: 10
  versioned: true
```

**Expected Output:**
- File: `app/models/shopping_cart.py`
- Contains: `snapshot_interval` equal to `10`, `SNAPSHOT` strategy, and snapshot persistence method

---

### B01-ES-03: TradingPortfolio with event compression

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Financial trading portfolio that compresses thousands of trade events into periodic compressed snapshots to minimize storage while preserving full auditability.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: TradingPortfolio
  root_entity: TradingPortfolio
  events:
    - PositionOpened
    - PositionClosed
    - PositionAdjusted
    - DividendReceived
    - CorporateAction
  eventing_strategy: COMPRESSION
  snapshot_interval: 500
  versioned: true
```

**Expected Output:**
- File: `app/models/trading_portfolio.py`
- Contains: `COMPRESSION` eventing strategy, `snapshot_interval` of `500`, and event compression logic

---

### B01-ES-04: InsurancePolicy with versioned OCC (prevent concurrent edits)

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Insurance policy management where two agents must not modify the same policy simultaneously. Version-based OCC rejects stale writes.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: InsurancePolicy
  root_entity: InsurancePolicy
  events:
    - PolicyIssued
    - PolicyEndorsed
    - PolicyCancelled
    - ClaimFiled
  eventing_strategy: SNAPSHOT
  snapshot_interval: 50
  versioned: true
```

**Expected Output:**
- File: `app/models/insurance_policy.py`
- Contains: `versioned: true`, version column in event store, and `ConcurrencyError` / `StaleVersion` exception handling

---

### B01-ES-05: MedicalRecord with append-only + HIPAA compliance

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Patient medical record where every diagnosis, prescription, and procedure is an immutable event. HIPAA requires append-only, never delete or overwrite.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: MedicalRecord
  root_entity: MedicalRecord
  events:
    - DiagnosisAdded
    - PrescriptionWritten
    - ProcedurePerformed
    - LabResultRecorded
  eventing_strategy: APPEND_ONLY
  snapshot_interval: 0
  versioned: true
```

**Expected Output:**
- File: `app/models/medical_record.py`
- Contains: `APPEND_ONLY` strategy (no delete/update), immutable event records, and audit metadata (actor_id, timestamp) on each event

---

### B01-ES-06: Auction with event sourcing (BidPlaced, AuctionClosed events)

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Online auction house where every bid placement, bidder withdrawal, and auction closure is recorded as an event for dispute resolution.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: Auction
  root_entity: Auction
  events:
    - AuctionCreated
    - BidPlaced
    - BidWithdrawn
    - AuctionClosed
    - AuctionWon
  eventing_strategy: APPEND_ONLY
  snapshot_interval: 0
  versioned: true
```

**Expected Output:**
- File: `app/models/auction.py`
- Contains: `BidPlaced`, `AuctionClosed`, `AuctionWon` event classes and append-only event store integration

---

### B01-ES-07: Contract lifecycle (Drafted → Negotiated → Signed → Amended)

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Legal contract management tracking full lifecycle from draft through amendments. Each state transition is an event.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: Contract
  root_entity: Contract
  events:
    - ContractDrafted
    - ContractNegotiated
    - ContractSigned
    - ContractAmended
    - ContractTerminated
  eventing_strategy: SNAPSHOT
  snapshot_interval: 20
  versioned: true
```

**Expected Output:**
- File: `app/models/contract.py`
- Contains: lifecycle events `ContractDrafted` through `ContractTerminated`, snapshot every 20 events, and state-reconstruction from events

---

### B01-ES-08: Loan account with event replay capability

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Loan management system that can replay the entire event history to reconstruct the account state at any point in time for regulatory audits.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: LoanAccount
  root_entity: LoanAccount
  events:
    - LoanDisbursed
    - PaymentMade
    - InterestCharged
    - LateFeeApplied
    - LoanRestructured
  eventing_strategy: SNAPSHOT
  snapshot_interval: 100
  versioned: true
```

**Expected Output:**
- File: `app/models/loan_account.py`
- Contains: replay method that accepts a `replay_until` timestamp, reconstructs state by applying events in order

---

### B01-ES-09: Subscription with snapshot strategy (monthly snapshots)

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** SaaS subscription management taking monthly snapshots of subscription state (tier, usage, proration) for billing reconciliation.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: Subscription
  root_entity: Subscription
  events:
    - Subscribed
    - TierChanged
    - UsageRecorded
    - InvoiceGenerated
    - SubscriptionCancelled
  eventing_strategy: SNAPSHOT
  snapshot_interval: 30
  versioned: true
```

**Expected Output:**
- File: `app/models/subscription.py`
- Contains: `snapshot_interval` of `30` (approximate monthly), `SNAPSHOT` strategy, and `TierChanged`/`UsageRecorded` events

---

### B01-ES-10: Inventory with event compression (merge quantity changes)

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Warehouse inventory where ItemQuantityChanged events are compressed — consecutive quantity changes on the same SKU are merged into a single compressed event.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: Inventory
  root_entity: Inventory
  events:
    - ItemReceived
    - ItemShipped
    - ItemQuantityChanged
    - ItemRecalled
  eventing_strategy: COMPRESSION
  snapshot_interval: 200
  versioned: true
```

**Expected Output:**
- File: `app/models/inventory.py`
- Contains: `COMPRESSION` strategy, `snapshot_interval` of `200`, and event compression that merges consecutive `ItemQuantityChanged` events

---

### B01-ES-11: Ticket system with append-only log

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Customer support ticket system where every status change, assignment, and note is an immutable event in an append-only log.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: SupportTicket
  root_entity: SupportTicket
  events:
    - TicketCreated
    - TicketAssigned
    - TicketStatusChanged
    - NoteAdded
    - TicketClosed
  eventing_strategy: APPEND_ONLY
  snapshot_interval: 0
  versioned: true
```

**Expected Output:**
- File: `app/models/support_ticket.py`
- Contains: `APPEND_ONLY` strategy, `TicketCreated`/`TicketClosed` events, and no mutation/delete of events

---

### B01-ES-12: Reservation with OCC version check

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Hotel room reservation where version-based OCC prevents double-booking when two channels (website + phone) try to reserve the same room simultaneously.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: Reservation
  root_entity: Reservation
  events:
    - RoomReserved
    - RoomModified
    - RoomCancelled
    - RoomCheckedIn
    - RoomCheckedOut
  eventing_strategy: SNAPSHOT
  snapshot_interval: 25
  versioned: true
```

**Expected Output:**
- File: `app/models/reservation.py`
- Contains: version field, OCC version check on every command, and `ConcurrencyError` raised when version mismatch detected

---

### B01-ES-13: FinancialInstrument with snapshot every 100 events

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Financial instrument (bond, derivative) tracking with snapshot every 100 valuation events to enable fast state reconstruction for risk reporting.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: FinancialInstrument
  root_entity: FinancialInstrument
  events:
    - InstrumentCreated
    - ValuationUpdated
    - CouponPaid
    - MaturityReached
    - InstrumentTransferred
  eventing_strategy: SNAPSHOT
  snapshot_interval: 100
  versioned: true
```

**Expected Output:**
- File: `app/models/financial_instrument.py`
- Contains: `snapshot_interval` of `100`, `ValuationUpdated` event with precision decimal, and snapshot-based replay

---

### B01-ES-14: Order processing with event replay for auditing

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** E-commerce order processing where every state change (placed → confirmed → shipped → delivered) is an event. Auditors can replay events to any point.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: Order
  root_entity: Order
  events:
    - OrderPlaced
    - OrderConfirmed
    - OrderShipped
    - OrderDelivered
    - OrderReturned
  eventing_strategy: SNAPSHOT
  snapshot_interval: 50
  versioned: true
```

**Expected Output:**
- File: `app/models/order.py`
- Contains: full lifecycle events, `replay_to_date` method, and `OrderShipped`/`OrderDelivered` event types

---

### B01-ES-15: Employee lifecycle (Hired → Promoted → Transferred → Terminated)

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** HR employee lifecycle tracking every career change as an event. State at any point (e.g., "who was this person's title in Jan 2024?") is replayed.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: Employee
  root_entity: Employee
  events:
    - EmployeeHired
    - EmployeePromoted
    - EmployeeTransferred
    - EmployeeSuspended
    - EmployeeTerminated
  eventing_strategy: SNAPSHOT
  snapshot_interval: 15
  versioned: true
```

**Expected Output:**
- File: `app/models/employee.py`
- Contains: `EmployeeHired`, `EmployeePromoted`, `EmployeeTransferred`, `EmployeeTerminated` events and snapshot every 15 events

---

### B01-ES-16: CustomerProfile with snapshot + event compression

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Customer profile that tracks preference changes, address updates, and tier upgrades. Uses compression to merge frequent preference changes.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: CustomerProfile
  root_entity: CustomerProfile
  events:
    - ProfileCreated
    - AddressChanged
    - PreferencesUpdated
    - TierUpgraded
    - ContactInfoChanged
  eventing_strategy: COMPRESSION
  snapshot_interval: 50
  versioned: true
```

**Expected Output:**
- File: `app/models/customer_profile.py`
- Contains: `COMPRESSION` strategy, `snapshot_interval` of `50`, and compression of consecutive `PreferencesUpdated` events

---

### B01-ES-17: ProductCatalog with append-only + version tags

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Product catalog where every product addition, price change, and category update is an immutable event with version tags for release tracking.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: ProductCatalog
  root_entity: ProductCatalog
  events:
    - ProductAdded
    - ProductUpdated
    - PriceChanged
    - CategoryChanged
    - ProductDeprecated
  eventing_strategy: APPEND_ONLY
  snapshot_interval: 0
  versioned: true
```

**Expected Output:**
- File: `app/models/product_catalog.py`
- Contains: `APPEND_ONLY` strategy, version tag on each event, and `PriceChanged`/`CategoryChanged` event types

---

### B01-ES-18: Shipment tracking with event sourcing + replay

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Logistics shipment tracking with events for every location update, status change, and exception. Supports replay to see shipment state at any time.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: Shipment
  root_entity: Shipment
  events:
    - ShipmentCreated
    - PickedUp
    - InTransit
    - LocationUpdated
    - Delivered
    - ExceptionRaised
  eventing_strategy: SNAPSHOT
  snapshot_interval: 40
  versioned: true
```

**Expected Output:**
- File: `app/models/shipment.py`
- Contains: `LocationUpdated` event with coordinates, `replay` method for state reconstruction, and `SNAPSHOT` every 40 events

---

### B01-ES-19: Minimal event-sourced aggregate (single event type)

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Minimal aggregate with a single event type — a counter that increments. Demonstrates the simplest possible event-sourced entity.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: Counter
  root_entity: Counter
  events:
    - Counted
  eventing_strategy: APPEND_ONLY
  snapshot_interval: 0
  versioned: false
```

**Expected Output:**
- File: `app/models/counter.py`
- Contains: single `Counted` event, `versioned: false` (no OCC), `APPEND_ONLY` strategy, and `0` snapshot interval

---

### B01-ES-20: Complex aggregate with 5+ event types + snapshot + compression

**Capability:** `event_sourcing`  
**Stack:** `both`

**Use Case:** Full-featured aggregate combining many event types, periodic snapshots, and event compression — the most complex event-sourced scenario.

**Input DSL:**
```yaml
EventSourcedAggregate:
  id: EnterpriseAccount
  root_entity: EnterpriseAccount
  events:
    - AccountCreated
    - BalanceDeposited
    - BalanceWithdrawn
    - InterestApplied
    - FeeCharged
    - AccountFrozen
    - AccountUnfrozen
    - AccountClosed
  eventing_strategy: COMPRESSION
  snapshot_interval: 100
  versioned: true
```

**Expected Output:**
- File: `app/models/enterprise_account.py`
- Contains: 8 event types, `COMPRESSION` strategy, `snapshot_interval` of `100`, versioned OCC, and both snapshot and compression logic
