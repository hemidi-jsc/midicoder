# UAT Briefs — B01 Temporal Entity (temporal_entity.md)

> Capability: `temporal_entity` | Definition: `TemporalEntity`
> Focus: SCD Type 2 with valid_from/valid_to time-bounded state, temporal granularity, current predicate, and range query index.

---

### B01-TE-01: EmployeeSalary (temporal tracking with MONTH granularity)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Track every salary change for an employee over their career. Query "what was this employee's salary in March 2023?" by matching temporal range.

**Input DSL:**
```yaml
TemporalEntity:
  id: EmployeeSalary
  fields:
    - name: employee_id
      type: UUID
    - name: base_salary
      type: DECIMAL
      precision: 10
      scale: 2
    - name: bonus_rate
      type: DECIMAL
      precision: 5
      scale: 2
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: MONTH
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/employee_salary.py`
- Contains: `valid_from` and `valid_to` datetime fields, `MONTH` granularity, range index on `(employee_id, valid_from, valid_to)`, and `current_predicate` filter

---

### B01-TE-02: ProductPricing (price history with DAY granularity)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** E-commerce product price changes tracked daily. Historical order prices must reflect the price at order time, not current price.

**Input DSL:**
```yaml
TemporalEntity:
  id: ProductPricing
  fields:
    - name: product_id
      type: UUID
    - name: price
      type: DECIMAL
      precision: 12
      scale: 2
    - name: currency
      type: STRING
      length: 3
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: DAY
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/product_pricing.py`
- Contains: `DAY` granularity, `price` field with DECIMAL(12,2), temporal range query support, and `valid_to IS NULL` current predicate

---

### B01-TE-03: StockPrice (temporal with SECOND granularity)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Real-time stock price tracking with second-level granularity. Each price tick creates a new temporal record for audit and compliance.

**Input DSL:**
```yaml
TemporalEntity:
  id: StockPrice
  fields:
    - name: ticker_symbol
      type: STRING
      length: 10
    - name: bid_price
      type: DECIMAL
      precision: 14
      scale: 4
    - name: ask_price
      type: DECIMAL
      precision: 14
      scale: 4
    - name: volume
      type: INTEGER
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: SECOND
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/stock_price.py`
- Contains: `SECOND` granularity, `bid_price`/`ask_price` with DECIMAL(14,4), and high-frequency temporal indexing

---

### B01-TE-04: CustomerAddress (address change history)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Track every address change for a customer over time. Shipping addresses for historical orders must use the address valid at order date.

**Input DSL:**
```yaml
TemporalEntity:
  id: CustomerAddress
  fields:
    - name: customer_id
      type: UUID
    - name: street
      type: STRING
    - name: city
      type: STRING
    - name: state
      type: STRING
      length: 50
    - name: postal_code
      type: STRING
      length: 20
    - name: country
      type: STRING
      length: 3
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: DAY
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/customer_address.py`
- Contains: address fields (street, city, state, postal_code, country), `DAY` granularity, and temporal range query on `(customer_id, valid_from, valid_to)`

---

### B01-TE-05: ExchangeRate (temporal with MINUTE granularity)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Foreign exchange rate tracking updated every minute. Transactions settled at different times need the exchange rate valid at settlement time.

**Input DSL:**
```yaml
TemporalEntity:
  id: ExchangeRate
  fields:
    - name: source_currency
      type: STRING
      length: 3
    - name: target_currency
      type: STRING
      length: 3
    - name: rate
      type: DECIMAL
      precision: 18
      scale: 6
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: MINUTE
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/exchange_rate.py`
- Contains: `MINUTE` granularity, `rate` field with DECIMAL(18,6), composite key on `(source_currency, target_currency)`, and temporal index

---

### B01-TE-06: UserRole (temporal role assignments)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Track role changes over time for audit. "Was this user an admin in June 2024?" requires temporal lookup of role assignments.

**Input DSL:**
```yaml
TemporalEntity:
  id: UserRole
  fields:
    - name: user_id
      type: UUID
    - name: role_code
      type: STRING
      length: 50
    - name: granted_by
      type: UUID
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: DAY
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/user_role.py`
- Contains: `role_code` field, `DAY` granularity, temporal query support for "role at time T", and `valid_to IS NULL` current predicate

---

### B01-TE-07: InsuranceCoverage (coverage period tracking)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Insurance coverage validity period. Claims filed at a specific date must check if the policy was active (valid_from ≤ claim_date ≤ valid_to).

**Input DSL:**
```yaml
TemporalEntity:
  id: InsuranceCoverage
  fields:
    - name: policy_number
      type: STRING
      length: 30
    - name: coverage_type
      type: STRING
      length: 50
    - name: coverage_amount
      type: DECIMAL
      precision: 14
      scale: 2
    - name: deductible
      type: DECIMAL
      precision: 10
      scale: 2
  valid_from_field: effective_date
  valid_to_field: expiration_date
  granularity: DAY
  current_predicate: "expiration_date IS NULL"
```

**Expected Output:**
- File: `app/models/insurance_coverage.py`
- Contains: custom `effective_date`/`expiration_date` fields (not default valid_from/to), custom predicate `"expiration_date IS NULL"`, and `DAY` granularity

---

### B01-TE-08: LeaseAgreement (temporal with valid_from/valid_to)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Property lease terms that change over time (rent increases, term extensions). Historical rent queries need the lease terms valid at the inquiry date.

**Input DSL:**
```yaml
TemporalEntity:
  id: LeaseAgreement
  fields:
    - name: property_id
      type: UUID
    - name: tenant_id
      type: UUID
    - name: monthly_rent
      type: DECIMAL
      precision: 12
      scale: 2
    - name: security_deposit
      type: DECIMAL
      precision: 12
      scale: 2
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: MONTH
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/lease_agreement.py`
- Contains: `monthly_rent`/`security_deposit` fields, `MONTH` granularity, temporal range query, and `valid_to IS NULL` current predicate

---

### B01-TE-09: EmployeePosition (position change history)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Track every position/title change for an employee. Org charts at any point in time require temporal position lookup.

**Input DSL:**
```yaml
TemporalEntity:
  id: EmployeePosition
  fields:
    - name: employee_id
      type: UUID
    - name: department_id
      type: UUID
    - name: position_title
      type: STRING
      length: 100
    - name: grade_level
      type: INTEGER
    - name: manager_id
      type: UUID
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: DAY
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/employee_position.py`
- Contains: `position_title`/`grade_level`/`manager_id` fields, `DAY` granularity, and temporal query on `(employee_id, valid_from, valid_to)`

---

### B01-TE-10: ContractTerms (temporal with DAY granularity)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Vendor contract terms that change on specific dates (price renegotiation, SLA updates). Compliance audit requires exact terms at contract execution date.

**Input DSL:**
```yaml
TemporalEntity:
  id: ContractTerms
  fields:
    - name: contract_id
      type: UUID
    - name: unit_price
      type: DECIMAL
      precision: 12
      scale: 2
    - name: payment_terms
      type: STRING
      length: 10
    - name: sla_level
      type: STRING
      length: 20
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: DAY
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/contract_terms.py`
- Contains: `unit_price`/`payment_terms`/`sla_level` fields, `DAY` granularity, and temporal range query support

---

### B01-TE-11: MedicalPrescription (valid period for prescriptions)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Medical prescriptions have a validity window. Pharmacies must verify the prescription is valid (within valid_from/valid_to range) before dispensing.

**Input DSL:**
```yaml
TemporalEntity:
  id: MedicalPrescription
  fields:
    - name: patient_id
      type: UUID
    - name: medication_name
      type: STRING
    - name: dosage
      type: STRING
      length: 200
    - name: frequency
      type: STRING
      length: 50
    - name: prescribing_physician_id
      type: UUID
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: DAY
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/medical_prescription.py`
- Contains: `dosage`/`frequency`/`prescribing_physician_id` fields, `DAY` granularity, and temporal validation query for prescription validity

---

### B01-TE-12: WarehouseLocation (item movement history)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Track which warehouse/bin a product is stored at over time. Inventory reconciliation needs location history for missing items investigation.

**Input DSL:**
```yaml
TemporalEntity:
  id: WarehouseLocation
  fields:
    - name: item_sku
      type: STRING
    - name: warehouse_id
      type: UUID
    - name: aisle
      type: STRING
      length: 10
    - name: rack
      type: STRING
      length: 10
    - name: bin
      type: STRING
      length: 10
    - name: quantity
      type: INTEGER
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: MINUTE
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/warehouse_location.py`
- Contains: `warehouse_id`/`aisle`/`rack`/`bin` location fields, `MINUTE` granularity, and temporal query for "where was SKU X at time T"

---

### B01-TE-13: UserPreferences (temporal preference changes)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** User preference settings (language, notification frequency, theme) tracked over time. Support "undo my last preference change" by reverting to previous temporal record.

**Input DSL:**
```yaml
TemporalEntity:
  id: UserPreferences
  fields:
    - name: user_id
      type: UUID
    - name: language_code
      type: STRING
      length: 10
    - name: notification_frequency
      type: STRING
      length: 20
    - name: theme
      type: STRING
      length: 20
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: DAY
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/user_preferences.py`
- Contains: preference fields (language, notification_frequency, theme), `DAY` granularity, and temporal rollback support

---

### B01-TE-14: ServiceLevel (SLA versioning with MONTH granularity)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Service Level Agreement terms that change quarterly. SLA compliance reports need the SLA terms valid during each measurement period.

**Input DSL:**
```yaml
TemporalEntity:
  id: ServiceLevel
  fields:
    - name: service_id
      type: UUID
    - name: sla_tier
      type: STRING
      length: 20
    - name: uptime_target
      type: DECIMAL
      precision: 5
      scale: 2
    - name: response_time_sla
      type: INTEGER
    - name: penalty_rate
      type: DECIMAL
      precision: 8
      scale: 4
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: MONTH
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/service_level.py`
- Contains: `uptime_target`/`response_time_sla`/`penalty_rate` fields, `MONTH` granularity, and temporal SLA compliance query support

---

### B01-TE-15: TaxRate (temporal with DAY granularity)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Tax rates that change on specific dates (e.g., VAT rate increase on Jan 1). Invoice tax calculation must use the rate valid on invoice date.

**Input DSL:**
```yaml
TemporalEntity:
  id: TaxRate
  fields:
    - name: jurisdiction_code
      type: STRING
      length: 20
    - name: tax_type
      type: STRING
      length: 50
    - name: rate_percent
      type: DECIMAL
      precision: 6
      scale: 4
    - name: effective_date_override
      type: DATE
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: DAY
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/tax_rate.py`
- Contains: `rate_percent` with DECIMAL(6,4), `DAY` granularity, jurisdiction-based temporal query, and `valid_to IS NULL` predicate

---

### B01-TE-16: ShippingRate (zone-based rate history)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Shipping rates by zone that change seasonally. Historical shipments must use the rate valid at shipment date for billing reconciliation.

**Input DSL:**
```yaml
TemporalEntity:
  id: ShippingRate
  fields:
    - name: zone_code
      type: STRING
      length: 10
    - name: carrier_code
      type: STRING
      length: 20
    - name: base_rate
      type: DECIMAL
      precision: 10
      scale: 2
    - name: per_kg_rate
      type: DECIMAL
      precision: 8
      scale: 2
    - name: fuel_surcharge_pct
      type: DECIMAL
      precision: 5
      scale: 2
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: DAY
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/shipping_rate.py`
- Contains: `base_rate`/`per_kg_rate`/`fuel_surcharge_pct` fields, `DAY` granularity, and temporal rate lookup by zone/carrier/time

---

### B01-TE-17: ConfigurationSetting (temporal config changes)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** System configuration settings tracked over time. Debugging production incidents requires knowing which config values were active at a given time.

**Input DSL:**
```yaml
TemporalEntity:
  id: ConfigurationSetting
  fields:
    - name: config_key
      type: STRING
    - name: config_value
      type: STRING
    - name: config_group
      type: STRING
      length: 50
    - name: changed_by
      type: UUID
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: SECOND
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/configuration_setting.py`
- Contains: `config_key`/`config_value`/`config_group` fields, `SECOND` granularity, and temporal config history query

---

### B01-TE-18: AccessPolicy (temporal permissions)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** User access permissions that are time-bounded (e.g., contractor access expires). Security audit requires "what permissions did this user have on date X?"

**Input DSL:**
```yaml
TemporalEntity:
  id: AccessPolicy
  fields:
    - name: subject_id
      type: UUID
    - name: resource_type
      type: STRING
      length: 50
    - name: resource_id
      type: UUID
    - name: permission
      type: STRING
      length: 20
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: DAY
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/access_policy.py`
- Contains: `subject_id`/`resource_type`/`resource_id`/`permission` fields, `DAY` granularity, and temporal permission query with expiry detection

---

### B01-TE-19: Minimal temporal entity (just id + temporal fields)

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Simplest possible temporal entity — a flag that tracks boolean state changes over time with no extra business fields beyond the ID and temporal columns.

**Input DSL:**
```yaml
TemporalEntity:
  id: FeatureFlag
  fields:
    - name: flag_key
      type: STRING
    - name: is_active
      type: BOOLEAN
  valid_from_field: valid_from
  valid_to_field: valid_to
  granularity: SECOND
  current_predicate: "valid_to IS NULL"
```

**Expected Output:**
- File: `app/models/feature_flag.py`
- Contains: minimal fields (`flag_key`, `is_active`), `SECOND` granularity, default `valid_from`/`valid_to` fields, and `valid_to IS NULL` predicate

---

### B01-TE-20: Complex temporal entity with multiple fields + custom predicate

**Capability:** `temporal_entity`  
**Stack:** `both`

**Use Case:** Complex multi-field temporal entity with a non-default current predicate. Tracks multi-country pricing where "current" is determined by `is_current` flag, not NULL valid_to.

**Input DSL:**
```yaml
TemporalEntity:
  id: RegionalPricing
  fields:
    - name: product_id
      type: UUID
    - name: region_code
      type: STRING
      length: 10
    - name: price
      type: DECIMAL
      precision: 14
      scale: 4
    - name: tax_included
      type: BOOLEAN
    - name: promo_discount_pct
      type: DECIMAL
      precision: 5
      scale: 2
    - name: is_current
      type: BOOLEAN
  valid_from_field: effective_start
  valid_to_field: effective_end
  granularity: DAY
  current_predicate: "is_current = true"
```

**Expected Output:**
- File: `app/models/regional_pricing.py`
- Contains: custom `effective_start`/`effective_end` fields, custom predicate `"is_current = true"`, `DAY` granularity, multiple business fields, and temporal composite index
