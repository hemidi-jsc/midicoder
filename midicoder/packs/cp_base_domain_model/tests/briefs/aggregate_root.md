# UAT Briefs — B01: aggregate_root

> Capability: `aggregate_root` | AggregateRoot DSL definition
> Coverage: Root entity + child entities (cluster), consistency levels, domain events, invariants, aggregate boundary enforcement

---

### B01-AGR-01: Order aggregate (Order root + OrderItem children, STRICT consistency)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** E-commerce system where an Order is the root entity with OrderItem children. All changes to Order and its items must be atomic (ACID). External code can only access OrderItems through the Order root.

**Input DSL:**
```yaml
aggregates:
  - id: Order
    root_entity: Order
    child_entities:
      - OrderItem
    events:
      - OrderPlaced
      - OrderCancelled
      - OrderShipped
    consistency: strict
    invariants:
      - "total_amount >= 0"
      - "len(items) > 0"
```

**Expected Output:**
- File: `app/models/order.py`
- Contains: `class Order(Base)` with `__tablename__ = "orders"`, relationship `order_items` to OrderItem, and `OrderItem` entity with foreign key to `orders.id`

---

### B01-AGR-02: BankAccount aggregate (Account root + Transaction children, STRICT)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Banking system where a BankAccount is the aggregate root. All Transactions (deposits, withdrawals) are child entities. STRICT consistency ensures no balance corruption during concurrent transfers.

**Input DSL:**
```yaml
aggregates:
  - id: BankAccount
    root_entity: BankAccount
    child_entities:
      - Transaction
    events:
      - Deposited
      - Withdrawn
      - Transferred
    consistency: strict
    invariants:
      - "balance >= 0"
      - "currency in ('USD', 'EUR', 'VND')"
```

**Expected Output:**
- File: `app/models/bank_account.py`
- Contains: `class BankAccount(Base)` with `balance` field, `transactions` relationship, and invariant `balance >= 0` enforced via CHECK constraint

---

### B01-AGR-03: Patient aggregate (Patient root + Visit/Prescription children, EVENTUAL)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Hospital management system. Patient is the root with Visit and Prescription as children. EVENTUAL consistency allows Visit and Prescription data to synchronize asynchronously across distributed microservices.

**Input DSL:**
```yaml
aggregates:
  - id: Patient
    root_entity: Patient
    child_entities:
      - Visit
      - Prescription
    events:
      - PatientAdmitted
      - VisitRecorded
      - PrescriptionIssued
    consistency: eventual
    invariants:
      - "status in ('admitted', 'outpatient', 'discharged')"
```

**Expected Output:**
- File: `app/models/patient.py`
- Contains: `class Patient(Base)` with `visits` and `prescriptions` relationships, consistency_level = `eventual` in aggregate metadata

---

### B01-AGR-04: Warehouse aggregate (Warehouse root + Inventory/Stock children, RELAXED)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Logistics warehouse system. Warehouse is root with Inventory and Stock as children. RELAXED consistency permits temporary stock count discrepancies during bulk import operations.

**Input DSL:**
```yaml
aggregates:
  - id: Warehouse
    root_entity: Warehouse
    child_entities:
      - Inventory
      - Stock
    events:
      - StockReceived
      - StockDispatched
      - InventoryRecounted
    consistency: relaxed
    invariants:
      - "quantity >= 0"
```

**Expected Output:**
- File: `app/models/warehouse.py`
- Contains: `class Warehouse(Base)` with `inventory` and `stock` relationships, consistency_level = `relaxed`

---

### B01-AGR-05: User aggregate (User root + Profile/Preferences children, STRICT)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** SaaS platform where User is the aggregate root. Profile and Preferences are child entities — any update to user profile or preferences must be atomic within the same transaction.

**Input DSL:**
```yaml
aggregates:
  - id: User
    root_entity: User
    child_entities:
      - Profile
      - Preferences
    events:
      - UserRegistered
      - ProfileUpdated
      - PreferencesChanged
    consistency: strict
    invariants:
      - "email matches email_regex"
      - "age >= 13"
```

**Expected Output:**
- File: `app/models/user.py`
- Contains: `class User(Base)` with `profile` (one-to-one) and `preferences` (one-to-one) relationships, CHECK constraint on email pattern and age

---

### B01-AGR-06: Invoice aggregate with emitted events (InvoiceCreated, InvoicePaid)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Billing system. Invoice aggregate root emits InvoiceCreated when a new invoice is generated and InvoicePaid when payment is received. Downstream services subscribe to these events for reporting.

**Input DSL:**
```yaml
aggregates:
  - id: Invoice
    root_entity: Invoice
    child_entities:
      - InvoiceLine
    events:
      - InvoiceCreated
      - InvoicePaid
      - InvoiceOverdue
    consistency: strict
    invariants:
      - "total_amount >= 0"
      - "status in ('draft', 'issued', 'paid', 'overdue')"
```

**Expected Output:**
- File: `app/models/invoice.py`
- Contains: `class Invoice(Base)` with `invoice_lines` relationship, and event publisher wiring for `InvoiceCreated`, `InvoicePaid`, `InvoiceOverdue` events

---

### B01-AGR-07: Booking aggregate with invariant (no double-booking)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Hotel reservation system. Booking aggregate enforces a no-double-booking invariant: the same room cannot have overlapping time reservations within the aggregate boundary.

**Input DSL:**
```yaml
aggregates:
  - id: Booking
    root_entity: Booking
    child_entities:
      - RoomAssignment
      - GuestInfo
    events:
      - BookingConfirmed
      - BookingCancelled
    consistency: strict
    invariants:
      - "check_in < check_out"
      - "no overlapping reservations for same room"
      - "guest_count <= room_capacity"
```

**Expected Output:**
- File: `app/models/booking.py`
- Contains: `class Booking(Base)` with `room_assignments` and `guest_info` relationships, and invariant checks for date range overlap and capacity

---

### B01-AGR-08: Cart aggregate (Cart root + CartItem children, RELAXED)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** E-commerce shopping cart. Cart root with CartItem children. RELAXED consistency allows cart items to be updated independently (e.g., real-time price adjustments) without full transaction locking.

**Input DSL:**
```yaml
aggregates:
  - id: Cart
    root_entity: Cart
    child_entities:
      - CartItem
    events:
      - ItemAdded
      - ItemRemoved
      - ItemQuantityChanged
    consistency: relaxed
    invariants:
      - "quantity > 0"
```

**Expected Output:**
- File: `app/models/cart.py`
- Contains: `class Cart(Base)` with `cart_items` relationship, consistency_level = `relaxed`, and invariant `quantity > 0` on CartItem

---

### B01-AGR-09: Project aggregate (Project root + Task/Milestone children, EVENTUAL)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Project management tool. Project root with Task and Milestone children. EVENTUAL consistency allows tasks and milestones to be updated by different team members asynchronously.

**Input DSL:**
```yaml
aggregates:
  - id: Project
    root_entity: Project
    child_entities:
      - Task
      - Milestone
    events:
      - ProjectCreated
      - TaskCompleted
      - MilestoneReached
    consistency: eventual
    invariants:
      - "start_date <= end_date"
      - "status in ('planning', 'active', 'on_hold', 'completed')"
```

**Expected Output:**
- File: `app/models/project.py`
- Contains: `class Project(Base)` with `tasks` and `milestones` relationships, EVENTUAL consistency level

---

### B01-AGR-10: Company aggregate (Company root + Department/Employee children, STRICT)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** HR management system. Company root with Department and Employee children. STRICT consistency ensures that employee-to-department assignments are always coherent — an employee must belong to an active department.

**Input DSL:**
```yaml
aggregates:
  - id: Company
    root_entity: Company
    child_entities:
      - Department
      - Employee
    events:
      - CompanyRegistered
      - EmployeeHired
      - EmployeeTransferred
      - DepartmentCreated
    consistency: strict
    invariants:
      - "employee.department_id must reference active department"
      - "company_name length between 2 and 200"
```

**Expected Output:**
- File: `app/models/company.py`
- Contains: `class Company(Base)` with `departments` and `employees` relationships, FOREIGN KEY constraint linking Employee.department_id to Department.id with ON DELETE RESTRICT

---

### B01-AGR-11: InsurancePolicy aggregate with invariants (premium > 0)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Insurance system. InsurancePolicy aggregate root enforces that premium must be positive and coverage_start must precede coverage_end.

**Input DSL:**
```yaml
aggregates:
  - id: InsurancePolicy
    root_entity: InsurancePolicy
    child_entities:
      - Coverage
      - Beneficiary
    events:
      - PolicyActivated
      - PolicyRenewed
      - PolicyCancelled
    consistency: strict
    invariants:
      - "premium > 0"
      - "coverage_start < coverage_end"
      - "policyholder_age >= 18"
```

**Expected Output:**
- File: `app/models/insurance_policy.py`
- Contains: `class InsurancePolicy(Base)` with `coverages` and `beneficiaries` relationships, CHECK constraints for `premium > 0` and `coverage_start < coverage_end`

---

### B01-AGR-12: Course aggregate (Course root + Enrollment/Lecture children, EVENTUAL)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** E-learning platform. Course root with Enrollment and Lecture children. EVENTUAL consistency allows lectures to be published and enrollments to be processed independently across services.

**Input DSL:**
```yaml
aggregates:
  - id: Course
    root_entity: Course
    child_entities:
      - Enrollment
      - Lecture
    events:
      - CoursePublished
      - StudentEnrolled
      - LecturePublished
    consistency: eventual
    invariants:
      - "max_enrollments > 0"
      - "enrollment_count <= max_enrollments"
```

**Expected Output:**
- File: `app/models/course.py`
- Contains: `class Course(Base)` with `enrollments` and `lectures` relationships, EVENTUAL consistency, and CHECK constraint on enrollment count

---

### B01-AGR-13: Ticket aggregate (Ticket root + Comment/Assignment children, STRICT)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** IT helpdesk system. Ticket root with Comment and Assignment children. STRICT consistency ensures that ticket status, assignments, and comments are always in a valid, coherent state.

**Input DSL:**
```yaml
aggregates:
  - id: Ticket
    root_entity: Ticket
    child_entities:
      - Comment
      - Assignment
    events:
      - TicketCreated
      - TicketAssigned
      - TicketResolved
    consistency: strict
    invariants:
      - "status in ('open', 'in_progress', 'resolved', 'closed')"
      - "priority in ('low', 'medium', 'high', 'critical')"
```

**Expected Output:**
- File: `app/models/ticket.py`
- Contains: `class Ticket(Base)` with `comments` and `assignments` relationships, CHECK constraints on status and priority enums

---

### B01-AGR-14: Loan aggregate with invariant (outstanding >= 0)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Lending platform. Loan aggregate root enforces that outstanding_balance must never go below zero and payment amount cannot exceed outstanding balance.

**Input DSL:**
```yaml
aggregates:
  - id: Loan
    root_entity: Loan
    child_entities:
      - PaymentSchedule
      - Disbursement
    events:
      - LoanApproved
      - LoanDisbursed
      - PaymentReceived
      - LoanClosed
    consistency: strict
    invariants:
      - "outstanding_balance >= 0"
      - "payment_amount <= outstanding_balance"
      - "interest_rate > 0"
```

**Expected Output:**
- File: `app/models/loan.py`
- Contains: `class Loan(Base)` with `payment_schedules` and `disbursements` relationships, CHECK constraints for outstanding_balance >= 0 and interest_rate > 0

---

### B01-AGR-15: Subscription aggregate with events (SubCreated, SubRenewed, SubCancelled)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** SaaS subscription billing. Subscription aggregate emits SubCreated on new signup, SubRenewed on automatic renewal, and SubCancelled when user cancels. Billing and notification services listen to these events.

**Input DSL:**
```yaml
aggregates:
  - id: Subscription
    root_entity: Subscription
    child_entities:
      - BillingCycle
      - AddOn
    events:
      - SubCreated
      - SubRenewed
      - SubCancelled
    consistency: strict
    invariants:
      - "plan in ('free', 'pro', 'enterprise')"
      - "status in ('active', 'paused', 'cancelled', 'expired')"
      - "billing_cycle_days in (7, 14, 30, 90, 365)"
```

**Expected Output:**
- File: `app/models/subscription.py`
- Contains: `class Subscription(Base)` with `billing_cycles` and `addons` relationships, event publisher wiring for SubCreated/SubRenewed/SubCancelled, and CHECK constraints on plan/status/cycle_days

---

### B01-AGR-16: Restaurant aggregate (Restaurant root + Table/Order children, RELAXED)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Restaurant POS system. Restaurant root with Table and Order children. RELAXED consistency allows tables to be updated independently while orders are being processed, supporting high-concurrency dining operations.

**Input DSL:**
```yaml
aggregates:
  - id: Restaurant
    root_entity: Restaurant
    child_entities:
      - Table
      - Order
    events:
      - TableReserved
      - OrderPlaced
      - OrderCompleted
    consistency: relaxed
    invariants:
      - "seat_count > 0"
      - "table_number > 0"
```

**Expected Output:**
- File: `app/models/restaurant.py`
- Contains: `class Restaurant(Base)` with `tables` and `orders` relationships, consistency_level = `relaxed`

---

### B01-AGR-17: Hospital aggregate (Hospital root + Ward/Bed children, EVENTUAL)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Hospital information system. Hospital root with Ward and Bed children. EVENTUAL consistency allows bed availability to sync across wards asynchronously during peak admission hours.

**Input DSL:**
```yaml
aggregates:
  - id: Hospital
    root_entity: Hospital
    child_entities:
      - Ward
      - Bed
    events:
      - PatientAdmittedToWard
      - BedOccupied
      - BedVacated
    consistency: eventual
    invariants:
      - "bed_number > 0"
      - "bed_status in ('available', 'occupied', 'maintenance', 'quarantined')"
```

**Expected Output:**
- File: `app/models/hospital.py`
- Contains: `class Hospital(Base)` with `wards` and `beds` relationships, EVENTUAL consistency, and CHECK constraint on bed_status enum

---

### B01-AGR-18: Portfolio aggregate (Portfolio root + Position children, STRICT)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Investment portfolio management. Portfolio root with Position children (individual stock/crypto holdings). STRICT consistency ensures portfolio value is always recalculated atomically with all position updates.

**Input DSL:**
```yaml
aggregates:
  - id: Portfolio
    root_entity: Portfolio
    child_entities:
      - Position
    events:
      - PositionOpened
      - PositionClosed
      - PositionAdjusted
    consistency: strict
    invariants:
      - "total_value >= 0"
      - "shares > 0"
```

**Expected Output:**
- File: `app/models/portfolio.py`
- Contains: `class Portfolio(Base)` with `positions` relationship, STRICT consistency, and CHECK constraints for total_value and shares

---

### B01-AGR-19: Repository aggregate (Repo root + Branch/Commit children, EVENTUAL)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Code repository platform. Repository root with Branch and Commit children. EVENTUAL consistency allows commits to be pushed to different branches asynchronously without blocking the main repository state.

**Input DSL:**
```yaml
aggregates:
  - id: Repository
    root_entity: Repository
    child_entities:
      - Branch
      - Commit
    events:
      - RepoCreated
      - BranchCreated
      - CommitPushed
    consistency: eventual
    invariants:
      - "visibility in ('public', 'private', 'internal')"
      - "default_branch must exist"
```

**Expected Output:**
- File: `app/models/repository.py`
- Contains: `class Repository(Base)` with `branches` and `commits` relationships, EVENTUAL consistency, and CHECK constraint on visibility enum

---

### B01-AGR-20: Minimal aggregate (single root, no children, STRICT)

**Capability:** `aggregate_root`  
**Stack:** `both`

**Use Case:** Simple configuration entity that acts as an aggregate root with no child entities. Demonstrates the minimal valid aggregate — root only, STRICT consistency, single invariant.

**Input DSL:**
```yaml
aggregates:
  - id: Config
    root_entity: Config
    child_entities: []
    events:
      - ConfigChanged
    consistency: strict
    invariants:
      - "version > 0"
```

**Expected Output:**
- File: `app/models/config.py`
- Contains: `class Config(Base)` with no child relationships, consistency_level = `strict`, and CHECK constraint `version > 0`
