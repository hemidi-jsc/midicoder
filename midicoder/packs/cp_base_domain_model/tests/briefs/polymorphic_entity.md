# UAT Briefs — B01 Polymorphic Entity (polymorphic_entity.md)

> Capability: `polymorphic_entity` | Definition: `PolymorphicEntity`
> Focus: Subtype inheritance with discriminator column, SINGLE_TABLE/JOINED_TABLE/CONCRETE_TABLE polymorphism strategies.

---

### B01-PE-01: Vehicle (SINGLE_TABLE: Car, Truck, Motorcycle subtypes)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Fleet management system where all vehicle types share a single table with a `vehicle_type` discriminator. Each subtype adds specific fields (e.g., Car has passenger_capacity, Truck has payload_tonnage).

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Vehicle
  polymorphism_type: SINGLE_TABLE
  discriminator_field: vehicle_type
  base_fields:
    - name: vin
      type: STRING
      length: 17
    - name: manufacturer
      type: STRING
    - name: model_year
      type: INTEGER
  subtypes:
    - name: Car
      fields:
        - name: passenger_capacity
          type: INTEGER
        - name: body_style
          type: STRING
          length: 30
    - name: Truck
      fields:
        - name: payload_tonnage
          type: DECIMAL
          precision: 6
          scale: 2
        - name: bed_length
          type: DECIMAL
          precision: 5
          scale: 1
    - name: Motorcycle
      fields:
        - name: engine_cc
          type: INTEGER
        - name: has_sidecar
          type: BOOLEAN
```

**Expected Output:**
- File: `app/models/vehicle.py`
- Contains: `vehicle_type` discriminator column, `Car`/`Truck`/`Motorcycle` subtype classes, and shared base fields (vin, manufacturer, model_year)

---

### B01-PE-02: PaymentMethod (SINGLE_TABLE: CreditCard, PayPal, BankTransfer)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** E-commerce checkout supporting multiple payment methods in a single table. Discriminator `payment_type` routes processing logic to the correct handler.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: PaymentMethod
  polymorphism_type: SINGLE_TABLE
  discriminator_field: payment_type
  base_fields:
    - name: owner_name
      type: STRING
    - name: currency
      type: STRING
      length: 3
  subtypes:
    - name: CreditCard
      fields:
        - name: card_last_four
          type: STRING
          length: 4
        - name: card_brand
          type: STRING
          length: 20
        - name: expiry_date
          type: STRING
          length: 7
    - name: PayPal
      fields:
        - name: paypal_email
          type: STRING
    - name: BankTransfer
      fields:
        - name: account_number
          type: STRING
        - name: bank_code
          type: STRING
          length: 10
```

**Expected Output:**
- File: `app/models/payment_method.py`
- Contains: `payment_type` discriminator, `CreditCard`/`PayPal`/`BankTransfer` subtypes with subtype-specific fields, and shared owner_name/currency base fields

---

### B01-PE-03: Notification (SINGLE_TABLE: Email, SMS, PushNotification)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Unified notification system storing all notification types in one table. The `channel_type` discriminator selects the delivery mechanism.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Notification
  polymorphism_type: SINGLE_TABLE
  discriminator_field: channel_type
  base_fields:
    - name: recipient_id
      type: UUID
    - name: subject
      type: STRING
    - name: body
      type: TEXT
    - name: sent_at
      type: DATETIME
  subtypes:
    - name: Email
      fields:
        - name: recipient_email
          type: STRING
        - name: reply_to
          type: STRING
    - name: SMS
      fields:
        - name: phone_number
          type: STRING
          length: 20
        - name: carrier
          type: STRING
          length: 30
    - name: PushNotification
      fields:
        - name: device_token
          type: STRING
        - name: platform
          type: STRING
          length: 10
```

**Expected Output:**
- File: `app/models/notification.py`
- Contains: `channel_type` discriminator, `Email`/`SMS`/`PushNotification` subtypes, and shared notification fields (recipient_id, subject, body, sent_at)

---

### B01-PE-04: Order (JOINED_TABLE: DomesticOrder, InternationalOrder)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Order management with separate tables for domestic and international orders. Base table holds common fields; subtype tables hold customs, shipping method specifics via JOIN.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Order
  polymorphism_type: JOINED_TABLE
  discriminator_field: order_type
  base_fields:
    - name: customer_id
      type: UUID
    - name: order_date
      type: DATETIME
    - name: total_amount
      type: DECIMAL
      precision: 12
      scale: 2
  subtypes:
    - name: DomesticOrder
      fields:
        - name: shipping_method
          type: STRING
          length: 30
        - name: same_day_eligible
          type: BOOLEAN
    - name: InternationalOrder
      fields:
        - name: destination_country
          type: STRING
          length: 3
        - name: hs_code
          type: STRING
          length: 10
        - name: customs_value
          type: DECIMAL
          precision: 12
          scale: 2
```

**Expected Output:**
- File: `app/models/order.py`
- Contains: `JOINED_TABLE` strategy, `order_type` discriminator, separate tables for `DomesticOrder` and `InternationalOrder` joined to base `Order` table

---

### B01-PE-05: User (JOINED_TABLE: Customer, Vendor, Admin)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Marketplace platform where a person can be a Customer, Vendor, or Admin. Each role has a separate table with role-specific fields joined to the base user table.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: User
  polymorphism_type: JOINED_TABLE
  discriminator_field: user_type
  base_fields:
    - name: email
      type: STRING
    - name: full_name
      type: STRING
    - name: phone
      type: STRING
      length: 20
  subtypes:
    - name: Customer
      fields:
        - name: loyalty_points
          type: INTEGER
        - name: preferred_payment
          type: STRING
          length: 30
    - name: Vendor
      fields:
        - name: store_name
          type: STRING
        - name: tax_id
          type: STRING
          length: 30
        - name: commission_rate
          type: DECIMAL
          precision: 5
          scale: 2
    - name: Admin
      fields:
        - name: admin_level
          type: INTEGER
        - name: managed_regions
          type: STRING
```

**Expected Output:**
- File: `app/models/user.py`
- Contains: `JOINED_TABLE` strategy, `user_type` discriminator, separate joined tables for `Customer`/`Vendor`/`Admin` with role-specific fields

---

### B01-PE-06: Document (SINGLE_TABLE: Invoice, Receipt, Contract)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Document management system storing all document types in a single table. `document_type` discriminator differentiates Invoice, Receipt, and Contract records.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Document
  polymorphism_type: SINGLE_TABLE
  discriminator_field: document_type
  base_fields:
    - name: document_number
      type: STRING
    - name: issued_date
      type: DATE
    - name: issued_by
      type: UUID
  subtypes:
    - name: Invoice
      fields:
        - name: due_date
          type: DATE
        - name: subtotal
          type: DECIMAL
          precision: 14
          scale: 2
        - name: tax_amount
          type: DECIMAL
          precision: 14
          scale: 2
    - name: Receipt
      fields:
        - name: payment_method
          type: STRING
          length: 30
        - name: tendered_amount
          type: DECIMAL
          precision: 14
          scale: 2
    - name: Contract
      fields:
        - name: contract_type
          type: STRING
          length: 50
        - name: expiry_date
          type: DATE
        - name: counterparty_id
          type: UUID
```

**Expected Output:**
- File: `app/models/document.py`
- Contains: `document_type` discriminator, `Invoice`/`Receipt`/`Contract` subtypes with subtype-specific fields in a single table

---

### B01-PE-07: Product (JOINED_TABLE: PhysicalProduct, DigitalProduct, Service)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Product catalog with joined-table inheritance: physical products have weight/dimensions, digital products have download_url, services have duration — all sharing name/price base fields.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Product
  polymorphism_type: JOINED_TABLE
  discriminator_field: product_type
  base_fields:
    - name: sku
      type: STRING
    - name: name
      type: STRING
    - name: price
      type: DECIMAL
      precision: 12
      scale: 2
  subtypes:
    - name: PhysicalProduct
      fields:
        - name: weight_kg
          type: DECIMAL
          precision: 8
          scale: 3
        - name: dimensions_cm
          type: STRING
          length: 20
        - name: warehouse_location
          type: STRING
          length: 50
    - name: DigitalProduct
      fields:
        - name: download_url
          type: STRING
        - name: file_size_mb
          type: INTEGER
        - name: max_downloads
          type: INTEGER
    - name: Service
      fields:
        - name: duration_minutes
          type: INTEGER
        - name: provider_id
          type: UUID
        - name: booking_required
          type: BOOLEAN
```

**Expected Output:**
- File: `app/models/product.py`
- Contains: `JOINED_TABLE` strategy, `product_type` discriminator, three joined subtype tables with subtype-specific fields

---

### B01-PE-08: Appointment (SINGLE_TABLE: DoctorVisit, TherapySession, LabTest)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Healthcare scheduling where all appointment types live in one table. `appointment_type` discriminator distinguishes doctor visits, therapy sessions, and lab tests.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Appointment
  polymorphism_type: SINGLE_TABLE
  discriminator_field: appointment_type
  base_fields:
    - name: patient_id
      type: UUID
    - name: provider_id
      type: UUID
    - name: scheduled_at
      type: DATETIME
    - name: status
      type: STRING
      length: 20
  subtypes:
    - name: DoctorVisit
      fields:
        - name: specialty
          type: STRING
          length: 50
        - name: visit_reason
          type: STRING
    - name: TherapySession
      fields:
        - name: therapy_type
          type: STRING
          length: 50
        - name: session_count
          type: INTEGER
        - name: plan_id
          type: UUID
    - name: LabTest
      fields:
        - name: test_panel
          type: STRING
          length: 50
        - name: fasting_required
          type: BOOLEAN
        - name: collection_method
          type: STRING
          length: 30
```

**Expected Output:**
- File: `app/models/appointment.py`
- Contains: `appointment_type` discriminator, `DoctorVisit`/`TherapySession`/`LabTest` subtypes with subtype-specific scheduling fields

---

### B01-PE-09: Transaction (JOINED_TABLE: Debit, Credit, Transfer)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Banking transaction system with separate tables for Debit, Credit, and Transfer transactions. Base table holds amount/timestamp; subtables hold source/destination details.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Transaction
  polymorphism_type: JOINED_TABLE
  discriminator_field: transaction_type
  base_fields:
    - name: amount
      type: DECIMAL
      precision: 16
      scale: 4
    - name: currency
      type: STRING
      length: 3
    - name: timestamp
      type: DATETIME
    - name: description
      type: STRING
  subtypes:
    - name: Debit
      fields:
        - name: source_account
          type: UUID
        - name: merchant_id
          type: UUID
        - name: category
          type: STRING
          length: 30
    - name: Credit
      fields:
        - name: target_account
          type: UUID
        - name: source_reference
          type: STRING
          length: 50
    - name: Transfer
      fields:
        - name: from_account
          type: UUID
        - name: to_account
          type: UUID
        - name: transfer_method
          type: STRING
          length: 20
```

**Expected Output:**
- File: `app/models/transaction.py`
- Contains: `JOINED_TABLE` strategy, `transaction_type` discriminator, separate tables for `Debit`/`Credit`/`Transfer` with subtype-specific financial fields

---

### B01-PE-10: Content (SINGLE_TABLE: Article, Video, Podcast)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Media platform where content items (articles, videos, podcasts) share a single table with `content_type` discriminator and subtype-specific media fields.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Content
  polymorphism_type: SINGLE_TABLE
  discriminator_field: content_type
  base_fields:
    - name: title
      type: STRING
    - name: author_id
      type: UUID
    - name: published_at
      type: DATETIME
    - name: category
      type: STRING
      length: 50
  subtypes:
    - name: Article
      fields:
        - name: word_count
          type: INTEGER
        - name: reading_time_min
          type: INTEGER
    - name: Video
      fields:
        - name: duration_seconds
          type: INTEGER
        - name: video_url
          type: STRING
        - name: thumbnail_url
          type: STRING
    - name: Podcast
      fields:
        - name: episode_number
          type: INTEGER
        - name: audio_url
          type: STRING
        - name: duration_seconds
          type: INTEGER
```

**Expected Output:**
- File: `app/models/content.py`
- Contains: `content_type` discriminator, `Article`/`Video`/`Podcast` subtypes with media-specific fields (word_count, video_url, episode_number)

---

### B01-PE-11: Employee (JOINED_TABLE: FullTime, PartTime, Contractor)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** HR system with separate tables for employment types. Base holds personal info; subtables hold compensation, benefits, and contract details.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Employee
  polymorphism_type: JOINED_TABLE
  discriminator_field: employment_type
  base_fields:
    - name: first_name
      type: STRING
    - name: last_name
      type: STRING
    - name: email
      type: STRING
    - name: hire_date
      type: DATE
  subtypes:
    - name: FullTime
      fields:
        - name: annual_salary
          type: DECIMAL
          precision: 12
          scale: 2
        - name: benefits_enrolled
          type: BOOLEAN
        - name: equity_grant_id
          type: UUID
    - name: PartTime
      fields:
        - name: hourly_rate
          type: DECIMAL
          precision: 8
          scale: 2
        - name: max_hours_per_week
          type: INTEGER
    - name: Contractor
      fields:
        - name: contract_end_date
          type: DATE
        - name: billing_rate
          type: DECIMAL
          precision: 10
          scale: 2
        - name: company_name
          type: STRING
```

**Expected Output:**
- File: `app/models/employee.py`
- Contains: `JOINED_TABLE` strategy, `employment_type` discriminator, separate joined tables for `FullTime`/`PartTime`/`Contractor` with compensation fields

---

### B01-PE-12: Asset (SINGLE_TABLE: RealEstate, Stock, Bond)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Investment portfolio where all asset types share one table. `asset_type` discriminator separates real estate properties, stock holdings, and bond positions.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Asset
  polymorphism_type: SINGLE_TABLE
  discriminator_field: asset_type
  base_fields:
    - name: asset_name
      type: STRING
    - name: acquisition_date
      type: DATE
    - name: acquisition_cost
      type: DECIMAL
      precision: 16
      scale: 4
  subtypes:
    - name: RealEstate
      fields:
        - name: property_address
          type: STRING
        - name: square_footage
          type: INTEGER
        - name: property_type
          type: STRING
          length: 30
    - name: Stock
      fields:
        - name: ticker_symbol
          type: STRING
          length: 10
        - name: shares_count
          type: INTEGER
        - name: exchange
          type: STRING
          length: 10
    - name: Bond
      fields:
        - name: issuer
          type: STRING
        - name: coupon_rate
          type: DECIMAL
          precision: 6
          scale: 4
        - name: maturity_date
          type: DATE
```

**Expected Output:**
- File: `app/models/asset.py`
- Contains: `asset_type` discriminator, `RealEstate`/`Stock`/`Bond` subtypes with asset-class-specific fields in single table

---

### B01-PE-13: Claim (JOINED_TABLE: AutoClaim, HealthClaim, PropertyClaim)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Insurance claims processing with separate tables per claim type. Base holds claimant info and amount; subtables hold incident-specific details.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Claim
  polymorphism_type: JOINED_TABLE
  discriminator_field: claim_type
  base_fields:
    - name: claim_number
      type: STRING
    - name: claimant_id
      type: UUID
    - name: reported_date
      type: DATETIME
    - name: estimated_amount
      type: DECIMAL
      precision: 14
      scale: 2
  subtypes:
    - name: AutoClaim
      fields:
        - name: vehicle_vin
          type: STRING
          length: 17
        - name: accident_date
          type: DATETIME
        - name: at_fault
          type: BOOLEAN
    - name: HealthClaim
      fields:
        - name: icd10_code
          type: STRING
          length: 10
        - name: procedure_code
          type: STRING
          length: 15
        - name: provider_npi
          type: STRING
          length: 10
    - name: PropertyClaim
      fields:
        - name: property_address
          type: STRING
        - name: damage_type
          type: STRING
          length: 50
        - name: water_damage
          type: BOOLEAN
```

**Expected Output:**
- File: `app/models/claim.py`
- Contains: `JOINED_TABLE` strategy, `claim_type` discriminator, separate joined tables for `AutoClaim`/`HealthClaim`/`PropertyClaim` with incident-specific fields

---

### B01-PE-14: Device (SINGLE_TABLE: Smartphone, Tablet, Laptop)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** IT asset management tracking company-owned devices. `device_type` discriminator separates smartphones, tablets, and laptops with hardware-specific fields.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Device
  polymorphism_type: SINGLE_TABLE
  discriminator_field: device_type
  base_fields:
    - name: serial_number
      type: STRING
    - name: assigned_user_id
      type: UUID
    - name: purchase_date
      type: DATE
    - name: status
      type: STRING
      length: 20
  subtypes:
    - name: Smartphone
      fields:
        - name: imei
          type: STRING
          length: 15
        - name: carrier
          type: STRING
          length: 30
        - name: storage_gb
          type: INTEGER
    - name: Tablet
      fields:
        - name: screen_size_inches
          type: DECIMAL
          precision: 4
          scale: 1
        - name: stylus_included
          type: BOOLEAN
        - name: storage_gb
          type: INTEGER
    - name: Laptop
      fields:
        - name: cpu_model
          type: STRING
          length: 50
        - name: ram_gb
          type: INTEGER
        - name: ssd_gb
          type: INTEGER
```

**Expected Output:**
- File: `app/models/device.py`
- Contains: `device_type` discriminator, `Smartphone`/`Tablet`/`Laptop` subtypes with hardware-specific fields (IMEI, screen_size, CPU/ram specs)

---

### B01-PE-15: Booking (JOINED_TABLE: HotelBooking, FlightBooking, RentalBooking)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Travel booking platform with separate tables per booking type. Base holds traveler and date info; subtables hold accommodation/flight/rental specifics.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Booking
  polymorphism_type: JOINED_TABLE
  discriminator_field: booking_type
  base_fields:
    - name: traveler_id
      type: UUID
    - name: booking_date
      type: DATETIME
    - name: start_date
      type: DATE
    - name: end_date
      type: DATE
    - name: total_price
      type: DECIMAL
      precision: 12
      scale: 2
  subtypes:
    - name: HotelBooking
      fields:
        - name: hotel_id
          type: UUID
        - name: room_type
          type: STRING
          length: 30
        - name: breakfast_included
          type: BOOLEAN
    - name: FlightBooking
      fields:
        - name: airline_code
          type: STRING
          length: 3
        - name: flight_number
          type: STRING
          length: 10
        - name: departure_airport
          type: STRING
          length: 3
        - name: arrival_airport
          type: STRING
          length: 3
    - name: RentalBooking
      fields:
        - name: vehicle_class
          type: STRING
          length: 20
        - name: insurance_included
          type: BOOLEAN
        - name: pickup_location
          type: STRING
```

**Expected Output:**
- File: `app/models/booking.py`
- Contains: `JOINED_TABLE` strategy, `booking_type` discriminator, separate joined tables for `HotelBooking`/`FlightBooking`/`RentalBooking` with travel-specific fields

---

### B01-PE-16: Review (CONCRETE_TABLE: ProductReview, ServiceReview)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Review system with completely separate tables for product and service reviews. No shared table — each concrete table has all fields including reviewer and rating.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Review
  polymorphism_type: CONCRETE_TABLE
  discriminator_field: review_type
  base_fields:
    - name: reviewer_id
      type: UUID
    - name: rating
      type: INTEGER
    - name: comment
      type: TEXT
  subtypes:
    - name: ProductReview
      fields:
        - name: product_id
          type: UUID
        - name: verified_purchase
          type: BOOLEAN
        - name: order_id
          type: UUID
    - name: ServiceReview
      fields:
        - name: service_provider_id
          type: UUID
        - name: service_date
          type: DATE
        - name: would_recommend
          type: BOOLEAN
```

**Expected Output:**
- File: `app/models/review.py`
- Contains: `CONCRETE_TABLE` strategy (no shared base table), `review_type` discriminator, separate concrete tables each with base fields duplicated plus subtype-specific fields

---

### B01-PE-17: Alert (CONCRETE_TABLE: CriticalAlert, WarningAlert, InfoAlert)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Monitoring alert system with fully separate tables per severity. Critical alerts go to pager, warnings to email, info to dashboard — completely different schemas and routing.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Alert
  polymorphism_type: CONCRETE_TABLE
  discriminator_field: severity
  base_fields:
    - name: source_service
      type: STRING
    - name: message
      type: TEXT
    - name: triggered_at
      type: DATETIME
  subtypes:
    - name: CriticalAlert
      fields:
        - name: oncall_channel
          type: STRING
          length: 50
        - name: escalation_level
          type: INTEGER
        - name: ack_timeout_minutes
          type: INTEGER
    - name: WarningAlert
      fields:
        - name: email_recipients
          type: STRING
        - name: auto_resolve_minutes
          type: INTEGER
    - name: InfoAlert
      fields:
        - name: dashboard_panel
          type: STRING
          length: 50
        - name: retain_days
          type: INTEGER
```

**Expected Output:**
- File: `app/models/alert.py`
- Contains: `CONCRETE_TABLE` strategy, `severity` discriminator, three independent concrete tables (`CriticalAlert`/`WarningAlert`/`InfoAlert`) with no shared base table

---

### B01-PE-18: Minimal polymorphic entity (1 base, 2 subtypes, SINGLE_TABLE)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Simplest possible polymorphic entity — a base with two subtypes and minimal fields. Demonstrates the bare minimum SINGLE_TABLE inheritance setup.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Status
  polymorphism_type: SINGLE_TABLE
  discriminator_field: type
  base_fields:
    - name: label
      type: STRING
  subtypes:
    - name: ActiveStatus
      fields:
        - name: started_at
          type: DATETIME
    - name: ArchivedStatus
      fields:
        - name: archived_reason
          type: STRING
```

**Expected Output:**
- File: `app/models/status.py`
- Contains: `type` discriminator (default), single base field (`label`), two minimal subtypes (`ActiveStatus`/`ArchivedStatus`) in a single table

---

### B01-PE-19: Polymorphic with 5+ subtypes

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** File storage system supporting many file types. Single table with 5 subtypes, each with format-specific metadata fields.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: File
  polymorphism_type: SINGLE_TABLE
  discriminator_field: file_type
  base_fields:
    - name: filename
      type: STRING
    - name: uploaded_by
      type: UUID
    - name: uploaded_at
      type: DATETIME
    - name: storage_path
      type: STRING
  subtypes:
    - name: ImageFile
      fields:
        - name: width
          type: INTEGER
        - name: height
          type: INTEGER
        - name: format
          type: STRING
          length: 10
    - name: VideoFile
      fields:
        - name: duration_seconds
          type: INTEGER
        - name: codec
          type: STRING
          length: 20
        - name: resolution
          type: STRING
          length: 15
    - name: AudioFile
      fields:
        - name: duration_seconds
          type: INTEGER
        - name: sample_rate
          type: INTEGER
        - name: channels
          type: INTEGER
    - name: DocumentFile
      fields:
        - name: page_count
          type: INTEGER
        - name: author
          type: STRING
        - name: document_format
          type: STRING
          length: 10
    - name: ArchiveFile
      fields:
        - name: compression
          type: STRING
          length: 10
        - name: contained_file_count
          type: INTEGER
    - name: SpreadsheetFile
      fields:
        - name: sheet_count
          type: INTEGER
        - name: row_count
          type: INTEGER
```

**Expected Output:**
- File: `app/models/file.py`
- Contains: `file_type` discriminator, 6 subtypes (`ImageFile`/`VideoFile`/`AudioFile`/`DocumentFile`/`ArchiveFile`/`SpreadsheetFile`) with media-specific metadata fields

---

### B01-PE-20: Nested polymorphism (Vehicle → Car → ElectricCar/HybridCar)

**Capability:** `polymorphic_entity`  
**Stack:** `both`

**Use Case:** Multi-level inheritance where a subtype (Car) itself has further subtypes (ElectricCar, HybridCar). Demonstrates nested polymorphic hierarchy.

**Input DSL:**
```yaml
PolymorphicEntity:
  id: Vehicle
  polymorphism_type: SINGLE_TABLE
  discriminator_field: vehicle_type
  base_fields:
    - name: vin
      type: STRING
      length: 17
    - name: manufacturer
      type: STRING
    - name: model_year
      type: INTEGER
  subtypes:
    - name: Car
      fields:
        - name: passenger_capacity
          type: INTEGER
        - name: body_style
          type: STRING
          length: 30
        subtypes:
          - name: ElectricCar
            fields:
              - name: battery_kwh
                type: DECIMAL
                precision: 6
                scale: 1
              - name: range_km
                type: INTEGER
              - name: charging_standard
                type: STRING
                length: 20
          - name: HybridCar
            fields:
              - name: battery_kwh
                type: DECIMAL
                precision: 6
                scale: 1
              - name: fuel_tank_liters
                type: DECIMAL
                precision: 5
                scale: 1
              - name: electric_range_km
                type: INTEGER
    - name: Truck
      fields:
        - name: payload_tonnage
          type: DECIMAL
          precision: 6
          scale: 2
```

**Expected Output:**
- File: `app/models/vehicle.py`
- Contains: nested subtype hierarchy (`Vehicle` → `Car` → `ElectricCar`/`HybridCar`), nested discriminator handling, and all three levels of fields inherited through the hierarchy
