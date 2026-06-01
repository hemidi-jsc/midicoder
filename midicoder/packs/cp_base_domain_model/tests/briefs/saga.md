# UAT Briefs — Capability: saga

> Capability ID: `saga` | CP B01: Domain Model DSL & IR Builder  
> Total: 20 briefs covering Saga and SagaStep DSL definitions

---

### B01-SAG-01: Order fulfillment saga (CreateOrder → ReserveInventory → ProcessPayment → ShipOrder)

**Capability:** `saga`  
**Stack:** `both`

**Use Case:** E-commerce platform processes a complete order by reserving inventory, charging payment, and shipping, with full rollback on any failure.

**Input DSL:**
```yaml
saga:
  id: OrderFulfillment
  orchestration: orchestration
  timeout_seconds: 120
  steps:
    - name: CreateOrder
      action: create_order
      compensating_action: cancel_order
      compensating_type: undo
      on_success_event: OrderCreated
    - name: ReserveInventory
      action: reserve_inventory
      compensating_action: release_inventory
      compensating_type: undo
      on_success_event: InventoryReserved
    - name: ProcessPayment
      action: charge_payment
      compensating_action: refund_payment
      compensating_type: undo
      on_success_event: PaymentProcessed
    - name: ShipOrder
      action: ship_order
      compensating_action: cancel_shipment
      compensating_type: undo
      on_success_event: OrderShipped
```

**Expected Output:**
- File: `src/sagas/order_fulfillment.py`
- Contains: `class OrderFulfillmentSaga` with 4 SagaStep instances and UNDO compensation on each

---

### B01-SAG-02: User registration saga (CreateUser → SendWelcomeEmail → SetupAccount → NotifyAdmin)

**Capability:** `saga`  
**Stack:** `fastapi`

**Use Case:** SaaS platform registers a new user, sends welcome email, sets up default account, and notifies admin, using choreography-style event triggers.

**Input DSL:**
```yaml
saga:
  id: UserRegistration
  orchestration: choreography
  timeout_seconds: 60
  steps:
    - name: CreateUser
      action: create_user
      compensating_action: delete_user
      compensating_type: undo
      on_success_event: UserCreated
      on_failure_event: UserCreationFailed
    - name: SendWelcomeEmail
      action: send_welcome_email
      compensating_action: noop
      compensating_type: noop
      on_success_event: WelcomeEmailSent
    - name: SetupAccount
      action: setup_default_account
      compensating_action: delete_account
      compensating_type: undo
      on_success_event: AccountSetupComplete
    - name: NotifyAdmin
      action: notify_admin
      compensating_action: noop
      compensating_type: notify
      on_success_event: AdminNotified
```

**Expected Output:**
- File: `src/sagas/user_registration.py`
- Contains: choreography orchestration with mixed compensation types (undo, noop, notify)

---

### B01-SAG-03: Payment processing saga (ValidatePayment → ReserveFunds → Transfer → Confirm)

**Capability:** `saga`  
**Stack:** `both`

**Use Case:** Banking application validates payment details, reserves funds, executes transfer, and confirms, with strict financial compensating actions.

**Input DSL:**
```yaml
saga:
  id: PaymentProcessing
  orchestration: orchestration
  timeout_seconds: 90
  steps:
    - name: ValidatePayment
      action: validate_payment_details
      compensating_action: noop
      compensating_type: noop
      on_success_event: PaymentValidated
    - name: ReserveFunds
      action: reserve_funds
      compensating_action: release_funds
      compensating_type: undo
      on_success_event: FundsReserved
    - name: Transfer
      action: execute_transfer
      compensating_action: reverse_transfer
      compensating_type: undo
      on_success_event: TransferCompleted
    - name: Confirm
      action: confirm_payment
      compensating_action: revert_confirmation
      compensating_type: undo
      on_success_event: PaymentConfirmed
```

**Expected Output:**
- File: `src/sagas/payment_processing.py`
- Contains: Saga with 4 steps, first step has NOOP compensation (validation is irreversible)

---

### B01-SAG-04: Insurance claim saga (FileClaim → AssignAdjuster → AssessDamage → Approve → Pay)

**Capability:** `saga`  
**Stack:** `fastapi`

**Use Case:** Insurance system processes a claim through filing, adjuster assignment, damage assessment, approval, and payment disbursement.

**Input DSL:**
```yaml
saga:
  id: InsuranceClaim
  orchestration: orchestration
  timeout_seconds: 3600
  steps:
    - name: FileClaim
      action: file_claim
      compensating_action: withdraw_claim
      compensating_type: undo
      on_success_event: ClaimFiled
    - name: AssignAdjuster
      action: assign_adjuster
      compensating_action: unassign_adjuster
      compensating_type: undo
      on_success_event: AdjusterAssigned
    - name: AssessDamage
      action: assess_damage
      compensating_action: withdraw_assessment
      compensating_type: undo
      on_success_event: DamageAssessed
    - name: Approve
      action: approve_claim
      compensating_action: reject_claim
      compensating_type: undo
      on_success_event: ClaimApproved
    - name: Pay
      action: disburse_payment
      compensating_action: recall_payment
      compensating_type: undo
      on_success_event: ClaimPaid
```

**Expected Output:**
- File: `src/sagas/insurance_claim.py`
- Contains: 5-step saga with 1-hour timeout for long-running insurance processing

---

### B01-SAG-05: Employee onboarding saga (CreateProfile → AssignWorkspace → SetupEmail → ProvisionAccess)

**Capability:** `saga`  
**Stack:** `nestjs`

**Use Case:** HR system creates a new employee profile, assigns a workspace, sets up corporate email, and provisions system access.

**Input DSL:**
```yaml
saga:
  id: EmployeeOnboarding
  orchestration: orchestration
  timeout_seconds: 300
  steps:
    - name: CreateProfile
      action: create_employee_profile
      compensating_action: delete_profile
      compensating_type: undo
      on_success_event: ProfileCreated
    - name: AssignWorkspace
      action: assign_workspace
      compensating_action: release_workspace
      compensating_type: undo
      on_success_event: WorkspaceAssigned
    - name: SetupEmail
      action: create_email_account
      compensating_action: disable_email_account
      compensating_type: undo
      on_success_event: EmailSetup
    - name: ProvisionAccess
      action: provision_system_access
      compensating_action: revoke_access
      compensating_type: undo
      on_success_event: AccessProvisioned
```

**Expected Output:**
- File: `src/sagas/employee_onboarding.ts`
- Contains: NestJS saga service with 4 steps, 300-second timeout

---

### B01-SAG-06: Hotel booking saga (CheckAvailability → ReserveRoom → ChargeDeposit → ConfirmBooking)

**Capability:** `saga`  
**Stack:** `both`

**Use Case:** Hotel booking system checks room availability, reserves the room, charges a deposit, and confirms the booking.

**Input DSL:**
```yaml
saga:
  id: HotelBooking
  orchestration: orchestration
  timeout_seconds: 120
  steps:
    - name: CheckAvailability
      action: check_room_availability
      compensating_action: noop
      compensating_type: noop
      on_success_event: RoomAvailable
    - name: ReserveRoom
      action: reserve_room
      compensating_action: release_room
      compensating_type: undo
      on_success_event: RoomReserved
    - name: ChargeDeposit
      action: charge_deposit
      compensating_action: refund_deposit
      compensating_type: undo
      on_success_event: DepositCharged
    - name: ConfirmBooking
      action: confirm_booking
      compensating_action: cancel_booking
      compensating_type: undo
      on_success_event: BookingConfirmed
```

**Expected Output:**
- File: `src/sagas/hotel_booking.py`
- Contains: Saga with availability check as NOOP step and 3 compensating undo steps

---

### B01-SAG-07: Purchase order saga (CreatePO → VendorApproval → Ship → Receive → Invoice)

**Capability:** `saga`  
**Stack:** `fastapi`

**Use Case:** Procurement system creates a purchase order, gets vendor approval, tracks shipment, confirms receipt, and processes the invoice.

**Input DSL:**
```yaml
saga:
  id: PurchaseOrder
  orchestration: orchestration
  timeout_seconds: 7200
  steps:
    - name: CreatePO
      action: create_purchase_order
      compensating_action: cancel_purchase_order
      compensating_type: undo
      on_success_event: PurchaseOrderCreated
    - name: VendorApproval
      action: request_vendor_approval
      compensating_action: retract_approval_request
      compensating_type: undo
      on_success_event: VendorApproved
    - name: Ship
      action: request_shipment
      compensating_action: cancel_shipment
      compensating_type: undo
      on_success_event: GoodsShipped
    - name: Receive
      action: confirm_receipt
      compensating_action: reject_receipt
      compensating_type: undo
      on_success_event: GoodsReceived
    - name: Invoice
      action: process_invoice
      compensating_action: void_invoice
      compensating_type: undo
      on_success_event: InvoiceProcessed
```

**Expected Output:**
- File: `src/sagas/purchase_order.py`
- Contains: 5-step saga with 2-hour timeout for vendor-dependent procurement flow

---

### B01-SAG-08: Loan approval saga (VerifyIdentity → CreditCheck → Approve → Disburse → Notify)

**Capability:** `saga`  
**Stack:** `both`

**Use Case:** Lending platform verifies borrower identity, runs credit check, approves loan, disburses funds, and sends confirmation notification.

**Input DSL:**
```yaml
saga:
  id: LoanApproval
  orchestration: orchestration
  timeout_seconds: 1800
  steps:
    - name: VerifyIdentity
      action: verify_borrower_identity
      compensating_action: noop
      compensating_type: noop
      on_success_event: IdentityVerified
    - name: CreditCheck
      action: run_credit_check
      compensating_action: noop
      compensating_type: noop
      on_success_event: CreditChecked
    - name: Approve
      action: approve_loan
      compensating_action: revoke_approval
      compensating_type: undo
      on_success_event: LoanApproved
    - name: Disburse
      action: disburse_funds
      compensating_action: recall_funds
      compensating_type: undo
      on_success_event: FundsDisbursed
    - name: Notify
      action: send_loan_confirmation
      compensating_action: noop
      compensating_type: notify
      on_success_event: BorrowerNotified
```

**Expected Output:**
- File: `src/sagas/loan_approval.py`
- Contains: Saga with mixed compensation — NOOP for verification steps, UNDO for financial steps, NOTIFY for final notification

---

### B01-SAG-09: Flight booking saga (SearchFlights → SelectFlight → Pay → IssueTicket → SendConfirmation)

**Capability:** `saga`  
**Stack:** `nestjs`

**Use Case:** Travel agency searches available flights, selects a flight, processes payment, issues the ticket, and sends booking confirmation.

**Input DSL:**
```yaml
saga:
  id: FlightBooking
  orchestration: orchestration
  timeout_seconds: 180
  steps:
    - name: SearchFlights
      action: search_available_flights
      compensating_action: noop
      compensating_type: noop
      on_success_event: FlightsSearched
    - name: SelectFlight
      action: select_and_reserve_flight
      compensating_action: cancel_reservation
      compensating_type: undo
      on_success_event: FlightReserved
    - name: Pay
      action: process_flight_payment
      compensating_action: refund_flight_payment
      compensating_type: undo
      on_success_event: FlightPaid
    - name: IssueTicket
      action: issue_e_ticket
      compensating_action: void_ticket
      compensating_type: undo
      on_success_event: TicketIssued
    - name: SendConfirmation
      action: send_booking_confirmation
      compensating_action: noop
      compensating_type: notify
      on_success_event: ConfirmationSent
```

**Expected Output:**
- File: `src/sagas/flight_booking.ts`
- Contains: 5-step NestJS saga with NOOP for search and NOTIFY for confirmation

---

### B01-SAG-10: Return/refund saga (CreateReturn → InspectItem → Refund → UpdateInventory → Notify)

**Capability:** `saga`  
**Stack:** `fastapi`

**Use Case:** E-commerce return process creates a return request, inspects returned item, issues refund, updates inventory, and notifies the customer.

**Input DSL:**
```yaml
saga:
  id: ReturnRefund
  orchestration: orchestration
  timeout_seconds: 600
  steps:
    - name: CreateReturn
      action: create_return_request
      compensating_action: cancel_return_request
      compensating_type: undo
      on_success_event: ReturnRequested
    - name: InspectItem
      action: inspect_returned_item
      compensating_action: noop
      compensating_type: noop
      on_success_event: ItemInspected
    - name: Refund
      action: issue_refund
      compensating_action: reverse_refund
      compensating_type: undo
      on_success_event: RefundIssued
    - name: UpdateInventory
      action: update_inventory_count
      compensating_action: revert_inventory_count
      compensating_type: undo
      on_success_event: InventoryUpdated
    - name: Notify
      action: send_return_notification
      compensating_action: noop
      compensating_type: notify
      on_success_event: CustomerNotified
```

**Expected Output:**
- File: `src/sagas/return_refund.py`
- Contains: 5-step saga with mixed compensation types for e-commerce returns

---

### B01-SAG-11: Minimal saga (2 steps with UNDO compensation)

**Capability:** `saga`  
**Stack:** `both`

**Use Case:** Simple two-step saga to validate the minimal viable saga — create a record and send a notification, with full undo capability.

**Input DSL:**
```yaml
saga:
  id: MinimalSaga
  orchestration: orchestration
  timeout_seconds: 30
  steps:
    - name: CreateRecord
      action: create_record
      compensating_action: delete_record
      compensating_type: undo
      on_success_event: RecordCreated
    - name: SendNotification
      action: send_notification
      compensating_action: retract_notification
      compensating_type: undo
      on_success_event: NotificationSent
```

**Expected Output:**
- File: `src/sagas/minimal_saga.py`
- Contains: Saga with exactly 2 steps, both UNDO compensation, 30-second timeout

---

### B01-SAG-12: Saga with NOOP compensation (irreversible first step)

**Capability:** `saga`  
**Stack:** `fastapi`

**Use Case:** Saga where the first step is a read-only validation that cannot be undone (NOOP), followed by compensable operations.

**Input DSL:**
```yaml
saga:
  id: IrreversibleStartSaga
  orchestration: orchestration
  timeout_seconds: 60
  steps:
    - name: ValidateInput
      action: validate_business_input
      compensating_action: noop
      compensating_type: noop
      on_success_event: InputValidated
    - name: ProcessData
      action: process_business_data
      compensating_action: revert_processing
      compensating_type: undo
      on_success_event: DataProcessed
    - name: SaveResult
      action: save_result
      compensating_action: delete_result
      compensating_type: undo
      on_success_event: ResultSaved
```

**Expected Output:**
- File: `src/sagas/irreversible_start_saga.py`
- Contains: First step compensating_type=NOOP, subsequent steps with UNDO

---

### B01-SAG-13: Saga with NOTIFY compensation (alert on failure)

**Capability:** `saga`  
**Stack:** `both`

**Use Case:** Saga where failure triggers notification alerts instead of automatic rollback — used for audit-critical operations.

**Input DSL:**
```yaml
saga:
  id: AuditCriticalSaga
  orchestration: orchestration
  timeout_seconds: 120
  steps:
    - name: ValidateAudit
      action: validate_audit_requirement
      compensating_action: send_audit_alert
      compensating_type: notify
      on_success_event: AuditValidated
      on_failure_event: AuditValidationFailed
    - name: ExecuteOperation
      action: execute_critical_operation
      compensating_action: send_failure_alert
      compensating_type: notify
      on_success_event: OperationExecuted
      on_failure_event: OperationFailed
    - name: RecordAuditTrail
      action: record_audit_trail
      compensating_action: send_compliance_alert
      compensating_type: notify
      on_success_event: AuditRecorded
```

**Expected Output:**
- File: `src/sagas/audit_critical_saga.py`
- Contains: All steps with compensating_type=NOTIFY and on_failure_event definitions

---

### B01-SAG-14: Saga with 10-step orchestration

**Capability:** `saga`  
**Stack:** `fastapi`

**Use Case:** Enterprise procurement workflow with 10 discrete steps covering the full lifecycle from requisition to payment.

**Input DSL:**
```yaml
saga:
  id: EnterpriseProcurement
  orchestration: orchestration
  timeout_seconds: 86400
  steps:
    - name: CreateRequisition
      action: create_requisition
      compensating_action: cancel_requisition
      compensating_type: undo
      on_success_event: RequisitionCreated
    - name: BudgetCheck
      action: verify_budget
      compensating_action: noop
      compensating_type: noop
      on_success_event: BudgetVerified
    - name: ManagerApproval
      action: request_manager_approval
      compensating_action: retract_approval
      compensating_type: undo
      on_success_event: ManagerApproved
    - name: FinanceApproval
      action: request_finance_approval
      compensating_action: retract_finance_approval
      compensating_type: undo
      on_success_event: FinanceApproved
    - name: CreatePO
      action: generate_purchase_order
      compensating_action: cancel_purchase_order
      compensating_type: undo
      on_success_event: PurchaseOrderGenerated
    - name: VendorNotification
      action: notify_vendor
      compensating_action: retract_notification
      compensating_type: undo
      on_success_event: VendorNotified
    - name: ReceiveGoods
      action: confirm_goods_receipt
      compensating_action: reject_goods
      compensating_type: undo
      on_success_event: GoodsReceived
    - name: QualityInspection
      action: perform_quality_inspection
      compensating_action: flag_failed_inspection
      compensating_type: notify
      on_success_event: QualityPassed
    - name: ProcessInvoice
      action: process_vendor_invoice
      compensating_action: void_invoice
      compensating_type: undo
      on_success_event: InvoiceProcessed
    - name: ExecutePayment
      action: execute_vendor_payment
      compensating_action: reverse_payment
      compensating_type: undo
      on_success_event: PaymentExecuted
```

**Expected Output:**
- File: `src/sagas/enterprise_procurement.py`
- Contains: 10-step saga with 24-hour timeout, mixed NOOP/UNDO/NOTIFY compensation

---

### B01-SAG-15: Saga with custom timeout (300 seconds)

**Capability:** `saga`  
**Stack:** `nestjs`

**Use Case:** Medium-complexity saga with explicit 300-second (5-minute) timeout for batch data migration.

**Input DSL:**
```yaml
saga:
  id: BatchDataMigration
  orchestration: orchestration
  timeout_seconds: 300
  steps:
    - name: ValidateSchema
      action: validate_target_schema
      compensating_action: noop
      compensating_type: noop
      on_success_event: SchemaValidated
    - name: ExtractData
      action: extract_source_data
      compensating_action: cleanup_extracted_data
      compensating_type: undo
      on_success_event: DataExtracted
    - name: TransformData
      action: transform_data_format
      compensating_action: revert_transformation
      compensating_type: undo
      on_success_event: DataTransformed
    - name: LoadData
      action: load_to_target
      compensating_action: rollback_load
      compensating_type: undo
      on_success_event: DataLoaded
    - name: VerifyMigration
      action: verify_data_integrity
      compensating_action: send_migration_alert
      compensating_type: notify
      on_success_event: MigrationVerified
```

**Expected Output:**
- File: `src/sagas/batch_data_migration.ts`
- Contains: Saga with timeout_seconds=300, NestJS service class

---

### B01-SAG-16: Choreography vs Orchestration comparison

**Capability:** `saga`  
**Stack:** `both`

**Use Case:** Two sagas performing similar steps but with different orchestration patterns — one choreography (decentralized) and one orchestration (centralized).

**Input DSL:**
```yaml
sagas:
  - id: DecentralizedOrder
    orchestration: choreography
    timeout_seconds: 120
    steps:
      - name: CreateOrder
        action: create_order
        compensating_action: cancel_order
        compensating_type: undo
        on_success_event: OrderCreated
      - name: ReserveInventory
        action: reserve_inventory
        compensating_action: release_inventory
        compensating_type: undo
        on_success_event: InventoryReserved
      - name: ProcessPayment
        action: charge_payment
        compensating_action: refund_payment
        compensating_type: undo
        on_success_event: PaymentProcessed
  - id: CentralizedOrder
    orchestration: orchestration
    timeout_seconds: 120
    steps:
      - name: CreateOrder
        action: create_order
        compensating_action: cancel_order
        compensating_type: undo
        on_success_event: OrderCreated
      - name: ReserveInventory
        action: reserve_inventory
        compensating_action: release_inventory
        compensating_type: undo
        on_success_event: InventoryReserved
      - name: ProcessPayment
        action: charge_payment
        compensating_action: refund_payment
        compensating_type: undo
        on_success_event: PaymentProcessed
```

**Expected Output:**
- File: `src/sagas/order_choreography.py`
- Contains: `DecentralizedOrder` with orchestration=choreography and `CentralizedOrder` with orchestration=orchestration

---

### B01-SAG-17: Saga with conditional steps (if-else branching)

**Capability:** `saga`  
**Stack:** `fastapi`

**Use Case:** Order saga that branches based on payment method — credit card path has fraud detection, bank transfer has AML screening.

**Input DSL:**
```yaml
saga:
  id: ConditionalPaymentSaga
  orchestration: orchestration
  timeout_seconds: 180
  steps:
    - name: CreateOrder
      action: create_order
      compensating_action: cancel_order
      compensating_type: undo
      on_success_event: OrderCreated
    - name: CheckPaymentMethod
      action: determine_payment_method
      compensating_action: noop
      compensating_type: noop
      on_success_event: PaymentMethodDetermined
      condition:
        if: payment_method == "credit_card"
        then:
          - name: FraudDetection
            action: run_fraud_detection
            compensating_action: noop
            compensating_type: noop
            on_success_event: FraudCheckPassed
        else:
          - name: AMLScreening
            action: run_aml_screening
            compensating_action: noop
            compensating_type: noop
            on_success_event: AMLCheckPassed
    - name: ProcessPayment
      action: execute_payment
      compensating_action: reverse_payment
      compensating_type: undo
      on_success_event: PaymentExecuted
    - name: ConfirmOrder
      action: confirm_order
      compensating_action: cancel_order
      compensating_type: undo
      on_success_event: OrderConfirmed
```

**Expected Output:**
- File: `src/sagas/conditional_payment_saga.py`
- Contains: Saga with condition block branching on payment_method field

---

### B01-SAG-18: Cross-tenant saga (steps across tenant boundaries)

**Capability:** `saga`  
**Stack:** `fastapi`

**Use Case:** B2B marketplace saga that operates across tenant boundaries — seller's inventory, platform escrow, and buyer's account.

**Input DSL:**
```yaml
saga:
  id: CrossTenantMarketplace
  orchestration: orchestration
  timeout_seconds: 600
  steps:
    - name: ReserveSellerInventory
      action: reserve_seller_inventory
      compensating_action: release_seller_inventory
      compensating_type: undo
      on_success_event: SellerInventoryReserved
      tenant: seller_tenant
    - name: HoldBuyerFunds
      action: hold_buyer_funds
      compensating_action: release_buyer_funds
      compensating_type: undo
      on_success_event: BuyerFundsHeld
      tenant: buyer_tenant
    - name: EscrowTransfer
      action: transfer_to_escrow
      compensating_action: reverse_escrow
      compensating_type: undo
      on_success_event: FundsEscrowed
      tenant: platform_tenant
    - name: NotifySellerToShip
      action: notify_seller_ship
      compensating_action: cancel_shipment_request
      compensating_type: undo
      on_success_event: SellerNotified
      tenant: seller_tenant
    - name: ConfirmDelivery
      action: confirm_delivery
      compensating_action: trigger_dispute
      compensating_type: notify
      on_success_event: DeliveryConfirmed
      tenant: buyer_tenant
    - name: ReleaseEscrow
      action: release_escrow_to_seller
      compensating_action: reverse_escrow_release
      compensating_type: undo
      on_success_event: EscrowReleased
      tenant: platform_tenant
```

**Expected Output:**
- File: `src/sagas/cross_tenant_marketplace.py`
- Contains: Saga with tenant field on each step, spanning seller_tenant, buyer_tenant, platform_tenant

---

### B01-SAG-19: Retry saga (step fails, retries, then succeeds)

**Capability:** `saga`  
**Stack:** `both`

**Use Case:** Saga with explicit retry policy on the external API step — retries up to 3 times with exponential backoff before compensating.

**Input DSL:**
```yaml
saga:
  id: ResilientExternalSync
  orchestration: orchestration
  timeout_seconds: 300
  retry_policy: "3x, exponential"
  steps:
    - name: PreparePayload
      action: prepare_sync_payload
      compensating_action: cleanup_payload
      compensating_type: undo
      on_success_event: PayloadPrepared
    - name: CallExternalAPI
      action: sync_to_external_system
      compensating_action: noop
      compensating_type: noop
      on_success_event: SyncCompleted
      retry_on: ["ConnectionError", "TimeoutError"]
      max_retries: 3
      backoff_ms: 1000
    - name: VerifySync
      action: verify_sync_status
      compensating_action: send_sync_failure_alert
      compensating_type: notify
      on_success_event: SyncVerified
```

**Expected Output:**
- File: `src/sagas/resilient_external_sync.py`
- Contains: Saga with retry_policy, max_retries=3, backoff_ms=1000 on CallExternalAPI step

---

### B01-SAG-20: Saga with parallel sub-steps

**Capability:** `saga`  
**Stack:** `fastapi`

**Use Case:** Deployment saga where multiple independent steps (build, test, security scan) run in parallel before sequential deploy.

**Input DSL:**
```yaml
saga:
  id: ParallelDeployment
  orchestration: orchestration
  timeout_seconds: 600
  steps:
    - name: CheckoutCode
      action: checkout_codebase
      compensating_action: cleanup_checkout
      compensating_type: undo
      on_success_event: CodeCheckedOut
    - name: ParallelCI
      parallel:
        - name: BuildApp
          action: build_application
          compensating_action: noop
          compensating_type: noop
          on_success_event: BuildCompleted
        - name: RunTests
          action: run_test_suite
          compensating_action: noop
          compensating_type: noop
          on_success_event: TestsPassed
        - name: SecurityScan
          action: run_security_scan
          compensating_action: noop
          compensating_type: noop
          on_success_event: SecurityScanPassed
    - name: DeployToStaging
      action: deploy_to_staging
      compensating_action: rollback_staging
      compensating_type: undo
      on_success_event: StagingDeployed
    - name: DeployToProduction
      action: deploy_to_production
      compensating_action: rollback_production
      compensating_type: undo
      on_success_event: ProductionDeployed
```

**Expected Output:**
- File: `src/sagas/parallel_deployment.py`
- Contains: Saga with parallel block containing 3 concurrent sub-steps (BuildApp, RunTests, SecurityScan)
