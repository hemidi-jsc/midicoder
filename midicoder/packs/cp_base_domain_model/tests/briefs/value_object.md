# UAT Briefs: value_object

20 real-world use cases for ValueObject DSL definition. Each brief tests: YAML DSL → VO model → Code generation (FastAPI frozen dataclass / NestJS class).

---

### B01-VO-01: Money VO with DECIMAL amount and STRING currency

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Payment system requires a Money value object that pairs a decimal amount with a three-letter ISO currency code, ensuring amounts are never used without currency context.

**Input DSL:**
```yaml
value_objects:
  - id: Money
    description: "Monetary amount with currency"
    fields:
      - name: amount
        type: decimal
        required: true
        precision: 15
        scale: 2
      - name: currency
        type: string
        required: true
        length: 3
    immutable: true
    comparable: true
```

**Expected Output:**
- File: `app/domain/value_objects/money.py`
- Contains: `@dataclass(frozen=True)`, `class Money`, `amount: Decimal`, `currency: str`, `def __eq__`, `def __hash__`

### B01-VO-02: Email VO with pattern validation

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** User registration system uses an Email value object that validates the string against RFC 5322 email pattern before accepting it as a valid email address.

**Input DSL:**
```yaml
value_objects:
  - id: Email
    description: "Validated email address"
    fields:
      - name: value
        type: string
        required: true
        min_length: 5
        max_length: 255
        pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    immutable: true
    comparable: true
```

**Expected Output:**
- File: `app/domain/value_objects/email.py`
- Contains: `@dataclass(frozen=True)`, `class Email`, `value: str`, `__post_init__`, `pattern`, `re.match`

### B01-VO-03: Address VO with nested object fields (street, city, state, zip)

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Shipping module models a postal address as an immutable value object with separate fields for street, city, state/province, and ZIP/postal code.

**Input DSL:**
```yaml
value_objects:
  - id: Address
    description: "Postal address value object"
    fields:
      - name: street
        type: string
        required: true
        max_length: 500
      - name: city
        type: string
        required: true
        max_length: 100
      - name: state
        type: string
        required: true
        max_length: 100
      - name: zip_code
        type: string
        required: true
        max_length: 20
      - name: country
        type: string
        required: true
        length: 2
    immutable: true
    comparable: true
```

**Expected Output:**
- File: `app/domain/value_objects/address.py`
- Contains: `@dataclass(frozen=True)`, `class Address`, `street: str`, `city: str`, `state: str`, `zip_code: str`, `country: str`, `to_dict`, `from_dict`

### B01-VO-04: PriceRange VO with DECIMAL min and max

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Product filter that defines a price range with minimum and maximum decimal values, validated so that min does not exceed max.

**Input DSL:**
```yaml
value_objects:
  - id: PriceRange
    description: "Price range filter with min and max bounds"
    fields:
      - name: min_price
        type: decimal
        required: true
        precision: 10
        scale: 2
      - name: max_price
        type: decimal
        required: true
        precision: 10
        scale: 2
    immutable: true
```

**Expected Output:**
- File: `app/domain/value_objects/price_range.py`
- Contains: `@dataclass(frozen=True)`, `class PriceRange`, `min_price: Decimal`, `max_price: Decimal`, `__post_init__`, `min_price <= max_price`

### B01-VO-05: Coordinate VO with FLOAT latitude and longitude

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Geolocation feature stores a geographic point as latitude/longitude pair with float precision, constrained to valid GPS coordinate ranges.

**Input DSL:**
```yaml
value_objects:
  - id: Coordinate
    description: "Geographic coordinate point"
    fields:
      - name: latitude
        type: float
        required: true
        min_value: -90.0
        max_value: 90.0
      - name: longitude
        type: float
        required: true
        min_value: -180.0
        max_value: 180.0
    immutable: true
    comparable: true
```

**Expected Output:**
- File: `app/domain/value_objects/coordinate.py`
- Contains: `@dataclass(frozen=True)`, `class Coordinate`, `latitude: float`, `longitude: float`, `__post_init__`, `-90.0 <= latitude <= 90.0`

### B01-VO-06: DateRange VO with DATETIME start and end

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Reporting module defines a date range with start and end datetime values for filtering reports, with validation that end is not before start.

**Input DSL:**
```yaml
value_objects:
  - id: DateRange
    description: "Date range for report filtering"
    fields:
      - name: start
        type: datetime
        required: true
      - name: end
        type: datetime
        required: true
    immutable: true
```

**Expected Output:**
- File: `app/domain/value_objects/date_range.py`
- Contains: `@dataclass(frozen=True)`, `class DateRange`, `start: datetime`, `end: datetime`, `__post_init__`, `end >= start`

### B01-VO-07: Percentage VO with computed display field (0-100 range)

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Discount calculation uses a Percentage value object that stores a raw float (0-100) and provides a computed display string with percent sign (e.g., "25.5%").

**Input DSL:**
```yaml
value_objects:
  - id: Percentage
    description: "Percentage value with display formatting"
    fields:
      - name: value
        type: float
        required: true
        min_value: 0.0
        max_value: 100.0
    immutable: true
```

**Expected Output:**
- File: `app/domain/value_objects/percentage.py`
- Contains: `@dataclass(frozen=True)`, `class Percentage`, `value: float`, `def display`, `"%"`, `0.0 <= value <= 100.0`

### B01-VO-08: PhoneNumber VO with regex pattern validation

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Customer contact system validates phone numbers against E.164 format (e.g., +1234567890) using regex pattern matching in the value object constructor.

**Input DSL:**
```yaml
value_objects:
  - id: PhoneNumber
    description: "E.164 formatted phone number"
    fields:
      - name: value
        type: string
        required: true
        min_length: 8
        max_length: 15
        pattern: "^\\+[1-9]\\d{6,14}$"
    immutable: true
    comparable: true
```

**Expected Output:**
- File: `app/domain/value_objects/phone_number.py`
- Contains: `@dataclass(frozen=True)`, `class PhoneNumber`, `value: str`, `__post_init__`, `re.match`, `pattern`

### B01-VO-09: LineItemPrice VO with computed total (quantity * unit_price)

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Order line item pricing uses a value object with quantity (integer) and unit_price (decimal), with a computed total property that returns quantity multiplied by unit_price.

**Input DSL:**
```yaml
value_objects:
  - id: LineItemPrice
    description: "Line item price with computed total"
    fields:
      - name: quantity
        type: integer
        required: true
        min_value: 1
      - name: unit_price
        type: decimal
        required: true
        precision: 10
        scale: 2
    immutable: true
```

**Expected Output:**
- File: `app/domain/value_objects/line_item_price.py`
- Contains: `@dataclass(frozen=True)`, `class LineItemPrice`, `quantity: int`, `unit_price: Decimal`, `def total`, `self.quantity * self.unit_price`

### B01-VO-10: BaseVO to DerivedVO inheritance (Base: id + name; Derived: adds type)

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Polymorphic naming system where a base NamedEntity VO provides id and name, and a TypedEntity VO extends it by adding a type discriminator field.

**Input DSL:**
```yaml
value_objects:
  - id: NamedEntity
    description: "Base value object with identity and name"
    fields:
      - name: id
        type: uuid
        required: true
      - name: name
        type: string
        required: true
        max_length: 200
    immutable: true
  - id: TypedEntity
    description: "Named entity with type discriminator"
    extends: NamedEntity
    fields:
      - name: entity_type
        type: string
        required: true
        max_length: 50
    immutable: true
```

**Expected Output:**
- File: `app/domain/value_objects/typed_entity.py`
- Contains: `class TypedEntity`, `id: UUID`, `name: str`, `entity_type: str`, `extends: NamedEntity` or `NamedEntity` fields inherited

### B01-VO-11: Multi-level inheritance (Base → Mid → Leaf)

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Three-level value object hierarchy: BaseVO provides id and version, MiddleVO extends with category, and LeafVO extends middle with priority level.

**Input DSL:**
```yaml
value_objects:
  - id: BaseVO
    description: "Root base value object"
    fields:
      - name: id
        type: uuid
        required: true
      - name: version
        type: integer
        required: true
        default: 1
    immutable: true
  - id: MiddleVO
    description: "Middle level with category"
    extends: BaseVO
    fields:
      - name: category
        type: string
        required: true
        max_length: 100
    immutable: true
  - id: LeafVO
    description: "Leaf level with priority"
    extends: MiddleVO
    fields:
      - name: priority
        type: integer
        required: true
        min_value: 1
        max_value: 10
    immutable: true
```

**Expected Output:**
- File: `app/domain/value_objects/leaf_vo.py`
- Contains: `class LeafVO`, `id: UUID`, `version: int`, `category: str`, `priority: int`, `extends: MiddleVO` or inherited fields from BaseVO through MiddleVO

### B01-VO-12: StatusLabel VO with ENUM field (active/pending/cancelled)

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Order status representation using a value object with an enum field limited to active, pending, and cancelled states for type-safe status management.

**Input DSL:**
```yaml
value_objects:
  - id: StatusLabel
    description: "Status label with predefined values"
    fields:
      - name: status
        type: enum
        required: true
        enum_values:
          - active
          - pending
          - cancelled
      - name: label
        type: string
        max_length: 50
    immutable: true
    comparable: true
```

**Expected Output:**
- File: `app/domain/value_objects/status_label.py`
- Contains: `@dataclass(frozen=True)`, `class StatusLabel`, `status: str` or `status: Enum`, `enum_values=["active", "pending", "cancelled"]`, `label: str`

### B01-VO-13: UserIdRef VO with ref to User entity

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Domain event payload that references a User entity by UUID, providing a typed wrapper around the entity reference for semantic clarity.

**Input DSL:**
```yaml
value_objects:
  - id: UserIdRef
    description: "Typed reference to User entity"
    fields:
      - name: user_id
        type: uuid
        required: true
    immutable: true
    comparable: true
```

**Expected Output:**
- File: `app/domain/value_objects/user_id_ref.py`
- Contains: `@dataclass(frozen=True)`, `class UserIdRef`, `user_id: UUID`, `ref: User` or entity reference to User

### B01-VO-14: ShippingAddressRef VO with ref to Address VO

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Order shipping uses a ShippingAddressRef value object that references a base Address value object, adding a shipping-specific label (e.g., "Home", "Work").

**Input DSL:**
```yaml
value_objects:
  - id: AddressVO
    description: "Base address value object"
    fields:
      - name: street
        type: string
        required: true
        max_length: 500
      - name: city
        type: string
        required: true
        max_length: 100
      - name: zip_code
        type: string
        required: true
        max_length: 20
    immutable: true
  - id: ShippingAddressRef
    description: "Shipping address reference with label"
    extends: AddressVO
    fields:
      - name: label
        type: string
        required: true
        max_length: 50
    immutable: true
```

**Expected Output:**
- File: `app/domain/value_objects/shipping_address_ref.py`
- Contains: `class ShippingAddressRef`, `street: str`, `city: str`, `zip_code: str`, `label: str`, `extends: AddressVO`

### B01-VO-15: TagList VO with ARRAY of strings

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Content tagging system uses an immutable TagList value object that holds an array of unique, lowercase tag strings for content categorization.

**Input DSL:**
```yaml
value_objects:
  - id: TagList
    description: "Immutable list of content tags"
    fields:
      - name: tags
        type: array
        required: true
    immutable: true
```

**Expected Output:**
- File: `app/domain/value_objects/tag_list.py`
- Contains: `@dataclass(frozen=True)`, `class TagList`, `tags: list[str]`, `__post_init__`

### B01-VO-16: Metadata VO with JSON field and defaults

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Flexible metadata storage as a value object with a JSON field that defaults to an empty dict, allowing arbitrary key-value pairs for extension data.

**Input DSL:**
```yaml
value_objects:
  - id: Metadata
    description: "Flexible metadata as JSON"
    fields:
      - name: key
        type: string
        required: true
        max_length: 100
      - name: data
        type: json
        default: {}
    immutable: true
```

**Expected Output:**
- File: `app/domain/value_objects/metadata.py`
- Contains: `@dataclass(frozen=True)`, `class Metadata`, `key: str`, `data: dict` or `data: Any`, `default={}`

### B01-VO-17: UUIDLabel VO with UUID + STRING label

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Audit trail identifier that pairs a UUID with a human-readable label for cross-referencing between system-generated IDs and display names.

**Input DSL:**
```yaml
value_objects:
  - id: UUIDLabel
    description: "UUID paired with human-readable label"
    fields:
      - name: uuid_value
        type: uuid
        required: true
      - name: label
        type: string
        required: true
        min_length: 1
        max_length: 200
    immutable: true
    comparable: true
```

**Expected Output:**
- File: `app/domain/value_objects/uuid_label.py`
- Contains: `@dataclass(frozen=True)`, `class UUIDLabel`, `uuid_value: UUID`, `label: str`, `def __eq__`, `def __hash__`

### B01-VO-18: ComparableMoney VO equality test (two equal VOs should be equal)

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Payment reconciliation requires that two Money value objects with the same amount and currency compare as equal, even if they are different instances.

**Input DSL:**
```yaml
value_objects:
  - id: ComparableMoney
    description: "Money with value-based equality"
    fields:
      - name: amount
        type: decimal
        required: true
        precision: 15
        scale: 2
      - name: currency
        type: string
        required: true
        length: 3
    immutable: true
    comparable: true
```

**Expected Output:**
- File: `app/domain/value_objects/comparable_money.py`
- Contains: `@dataclass(frozen=True)`, `class ComparableMoney`, `comparable: true`, `def __eq__(self, other)`, `self.amount == other.amount and self.currency == other.currency`

### B01-VO-19: StrictString VO with all field attributes (min/max length, pattern, enum)

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Code identifier value object that enforces all possible field-level validations: minimum/maximum length, regex pattern, and enum whitelist for a strict product code format.

**Input DSL:**
```yaml
value_objects:
  - id: StrictString
    description: "String with all validation attributes"
    fields:
      - name: code
        type: string
        required: true
        min_length: 3
        max_length: 10
        pattern: "^[A-Z]{2}\\d{3,8}$"
      - name: category
        type: enum
        required: true
        enum_values:
          - electronic
          - mechanical
          - software
          - service
    immutable: true
```

**Expected Output:**
- File: `app/domain/value_objects/strict_string.py`
- Contains: `@dataclass(frozen=True)`, `class StrictString`, `code: str`, `category: str`, `min_length: 3`, `max_length: 10`, `pattern`, `enum_values=["electronic", "mechanical", "software", "service"]`, `__post_init__`

### B01-VO-20: ImmutableFrozen VO test (frozen=True, mutation should fail)

**Capability:** `value_object`
**Stack:** `both`

**Use Case:** Test that a frozen value object raises an exception when attempting to mutate any field after construction, confirming immutability guarantee.

**Input DSL:**
```yaml
value_objects:
  - id: ImmutableFrozen
    description: "Frozen value object that rejects mutation"
    fields:
      - name: value
        type: string
        required: true
      - name: counter
        type: integer
        required: true
    immutable: true
```

**Expected Output:**
- File: `app/domain/value_objects/immutable_frozen.py`
- Contains: `@dataclass(frozen=True)`, `class ImmutableFrozen`, `value: str`, `counter: int`, `FrozenInstanceError` or `cannot assign to field`
