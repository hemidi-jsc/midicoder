# Universal-Fully Brief Schema v1.0.0

## Overview

This schema defines the mandatory structure and depth requirements for all `brief.md` files in the Midicoder CE Brief Template Library. Each brief serves as an **input texture** for end-to-end testing of the Midicoder contract-graph compiler pipeline.

---

## Mandatory Sections

Every `brief.md` must contain exactly these 16 sections in order:

### 1. Product Context

**Purpose:** Define what the product is, who it serves, and why it exists.

**Required Content:**

- Product Name
- Product Type (e.g., B2B SaaS, D2C E-commerce, B2C Marketplace)
- Target Market (geographic regions, customer segments)
- Problem Statement (1-3 paragraphs describing the core problem)
- Solution Overview (1-2 paragraphs describing the proposed solution)
- Business Model (revenue model, pricing strategy, monetization approach)
- Go-to-Market Strategy (launch approach, channel strategy)

**Validation Rules:**

- No TBD, placeholder, or generic marketing language
- Must be specific to the industry domain
- Minimum 500 words

---

### 2. Business Goals and KPIs

**Purpose:** Define measurable success criteria.

**Required Content:**

- Strategic Goals (3-5 high-level objectives)
- Tactical KPIs (10-15 measurable metrics with baseline and target values)
- Time Horizons (short-term, mid-term, long-term milestones)
- Success Definition (what "done" means for each goal)

**KPI Categories Required:**

- User Growth (MAU, DAU, conversion rates)
- Revenue (ARR, MRR, LTV, CAC)
- Engagement (session duration, retention, activation)
- Operational (CSAT, NPS, support ticket volume)
- Technical (uptime, latency, error rates)

**Validation Rules:**

- Each KPI must have: name, definition, baseline, target, measurement frequency
- Minimum 10 KPIs with specific numeric targets
- No vague targets like "increase engagement"

---

### 3. User Personas and Roles

**Purpose:** Define who interacts with the system and their characteristics.

**Required Content:**

- At least 3 distinct personas with full profiles
- Each persona must include:
    - Persona ID (e.g., P01, P02)
    - Name and Demographics
    - Role in the System
    - Goals and Motivations
    - Pain Points
    - Technical Proficiency
    - Usage Frequency
    - Key Tasks
- Role-Permission Matrix (who can do what)
- Access Level Definitions

**Validation Rules:**

- Minimum 3 personas required
- Each persona must be distinct (no overlapping primary goals)
- Must include at least 1 admin/operator persona
- Must include at least 1 end-user persona
- Must include at least 1 stakeholder/manager persona

---

### 4. Core User Journeys

**Purpose:** Define end-to-end user flows from trigger to outcome.

**Required Content:**

- At least 10 user journeys with full specifications
- Each journey must include:
    - Journey ID (e.g., J01, J02)
    - Journey Name
    - Primary Persona(s)
    - Trigger Event
    - Preconditions (what must be true before journey starts)
    - Postconditions (what is guaranteed after journey completes)
    - Step-by-Step Flow (numbered steps with actions and decisions)
    - Alternative Paths (error cases, edge cases)
    - Success Criteria
    - Metrics Tracked

**Validation Rules:**

- Minimum 10 journeys required
- Each journey must have explicit pre/post conditions
- Journeys must cover: onboarding, core value delivery, support, exit/churn
- Must include at least 3 administrative journeys
- Must include at least 3 user-facing core journeys
- Must include at least 2 error/recovery journeys

---

### 5. Functional Requirements

**Purpose:** Define what the system must do.

**Required Content:**

- At least 30 functional requirements with full specifications
- Each requirement must include:
    - Requirement ID (e.g., FR01, FR02)
    - Title
    - Description
    - Priority (Must/Should/Could)
    - Acceptance Criteria (Given-When-Then format)
    - Dependencies (other requirements, external systems)
    - Test Scenarios (minimum 2 per requirement)

**Categories Required:**

- Authentication & Authorization
- Core Domain Operations
- Search & Discovery
- Reporting & Analytics
- Notifications & Communications
- Configuration & Administration
- Integrations & External APIs
- Data Management (import/export/archive)

**Validation Rules:**

- Minimum 30 requirements required
- Each requirement must be testable/measurable
- No vague requirements like "user-friendly interface"
- Must include CRUD operations for all core entities
- Must include at least 5 reporting/analytics requirements

---

### 6. Non-Functional Requirements

**Purpose:** Define quality attributes and constraints.

**Required Content:**

- At least 15 non-functional requirements with full specifications
- Each NFR must include:
    - NFR ID (e.g., NFR01, NFR02)
    - Category (Security, Performance, Reliability, Scalability, etc.)
    - Description
    - Measurement Criteria (how to verify)
    - Target Value (specific numeric threshold)
    - Priority

**Categories Required:**

- Security (encryption, access control, audit)
- Performance (response times, throughput)
- Reliability (availability, fault tolerance)
- Scalability (user growth, data volume)
- Usability (learnability, efficiency)
- Maintainability (code quality, documentation)
- Observability (logging, monitoring, tracing)
- Compliance (industry-specific regulations)

**Validation Rules:**

- Minimum 15 NFRs required
- Each NFR must have numeric targets where applicable
- Must include at least 5 security-related NFRs
- Must include at least 3 performance NFRs with SLA targets
- Must include at least 2 reliability NFRs with uptime targets

---

### 7. Domain Rules and Invariants

**Purpose:** Define business logic constraints that must never be violated.

**Required Content:**

- At least 10 domain invariants with full specifications
- Each invariant must include:
    - Invariant ID (e.g., INV01, INV02)
    - Name
    - Description
    - Formal Statement (logical expression if applicable)
    - Enforcement Point (compile-time, runtime, both)
    - Violation Handling (error code, user message)
    - Test Cases (scenarios that would violate)

**Categories Required:**

- Data Integrity Rules
- Business Logic Constraints
- State Transition Rules
- Temporal Constraints
- Quantity/Threshold Rules
- Relationship Constraints

**Validation Rules:**

- Minimum 10 invariants required
- Each invariant must be enforceable at compile-time or runtime
- Must include at least 3 data integrity invariants
- Must include at least 3 state transition invariants
- Must include at least 2 business logic invariants specific to domain

---

### 8. Compliance and Regulatory Constraints

**Purpose:** Define legal and regulatory requirements.

**Required Content:**

- At least 8 compliance constraints with full specifications
- Each constraint must include:
    - Constraint ID (e.g., CC01, CC02)
    - Regulatory Framework (e.g., GDPR, HIPAA, PCI-DSS)
    - Reference (specific regulation/article/section)
    - Regulatory Overlay ID (RX01-RX12 mapping)
    - Requirement Description
    - Implementation Controls
    - Evidence Requirements
    - Audit Frequency

**Validation Rules:**

- Minimum 8 compliance constraints required
- Each must map to specific RX overlay
- Must include at least 1 privacy/PII constraint (RX01)
- Must include at least 1 audit trail constraint (RX11)
- Industry-specific regulations must be included (e.g., HIPAA for healthcare, PCI-DSS for payments)

---

### 9. Integration Requirements

**Purpose:** Define external system connections and data exchanges.

**Required Content:**

- At least 10 integration contracts with full specifications
- Each contract must include:
    - Contract ID (e.g., INT01, INT02)
    - Integration Type (Inbound API, Outbound API, Event, Webhook, Batch)
    - External System Name
    - Protocol (REST, GraphQL, gRPC, WebSocket, etc.)
    - Authentication Method
    - Data Format (JSON, XML, etc.)
    - Rate Limits
    - SLA Requirements
    - Error Handling
    - Retry Policy
    - Data Mapping (field-level)

**Categories Required:**

- Payment Processors
- Email/SMS Providers
- Identity Providers (SSO)
- CRM/ERP Systems
- Analytics Platforms
- Third-party APIs
- Internal Legacy Systems

**Validation Rules:**

- Minimum 10 integration contracts required
- Each must specify protocol, auth, and data format
- Must include at least 2 inbound integrations
- Must include at least 2 outbound integrations
- Must include at least 2 event-based integrations

---

### 10. Data Model Expectations

**Purpose:** Define core entities, relationships, and data characteristics.

**Required Content:**

- Core Entity List (15-25 entities minimum)
- For each entity:
    - Entity Name
    - Description
    - Primary Key
    - Fields (name, type, required, constraints)
    - Relationships (references to other entities)
    - Indexes
    - Retention Policy
- Aggregate/Value Objects
- Enum Definitions
- Data Volume Estimates
- Growth Projections

**Validation Rules:**

- Minimum 15 core entities required
- Each entity must have clearly defined fields and relationships
- Must include user/account entities
- Must include audit/history entities
- Must include configuration/entities for tenant isolation

---

### 11. Security and Access Control

**Purpose:** Define security architecture and access policies.

**Required Content:**

- Authentication Strategy (JWT, OAuth2, SAML, etc.)
- Authorization Model (RBAC, ABAC, ReBAC)
- Role Definitions (minimum 5 roles)
- Permission Definitions (minimum 20 permissions)
- Role-Permission Bindings
- Session Management (timeout, refresh, invalidation)
- Password Policy (complexity, rotation, history)
- API Security (rate limiting, input validation, CORS)
- Data Protection (encryption at rest, in transit)
- Secret Management
- Audit Logging Requirements

**Validation Rules:**

- Must specify authentication mechanism
- Must include at least 5 distinct roles
- Must include at least 20 permissions
- Must define role-permission bindings
- Must include session management strategy
- Must include data protection requirements

---

### 12. Observability and Operations

**Purpose:** Define monitoring, logging, and operational requirements.

**Required Content:**

- Logging Requirements:
    - Log Levels
    - Log Format (structured JSON)
    - Required Fields (timestamp, correlation_id, user_id, etc.)
    - Retention Period
    - Aggregation Requirements
- Metrics Requirements:
    - Application Metrics (custom counters, gauges, histograms)
    - Infrastructure Metrics (CPU, memory, disk, network)
    - Business Metrics (conversion, revenue, user activity)
- Tracing Requirements:
    - Trace Sampling Rate
    - Span Requirements
    - Correlation Strategy
- Alerting Requirements:
    - Critical Alerts
    - Warning Alerts
    - Notification Channels
    - Escalation Policy
- Dashboard Requirements
- Incident Response Procedures

**Validation Rules:**

- Must specify logging format and required fields
- Must include at least 5 application metrics
- Must include at least 5 alerting rules
- Must specify correlation strategy for tracing
- Must include incident response procedures

---

### 13. Acceptance Criteria

**Purpose:** Define when the system is considered complete and ready.

**Required Content:**

- Definition of Done (DoD)
- Minimum Viable Product (MVP) Scope
- Launch Readiness Checklist
- Performance Baselines
- Security Audit Completion
- Compliance Verification
- User Acceptance Test (UAT) Sign-off
- Documentation Completion
- Training Completion
- Support Readiness

**Validation Rules:**

- Must include clear DoD
- Must include MVP scope definition
- Must include security/compliance sign-off requirements
- Must include at least 10 launch readiness items

---

### 14. Out-of-Scope

**Purpose:** Define what is explicitly not included.

**Required Content:**

- Features Deferred to Future Phases
- Integrations Not Included
- Markets/Regions Not Supported
- User Segments Not Targeted
- Third-party Services Not Used
- Explicitly Rejected Approaches

**Validation Rules:**

- Must include at least 5 out-of-scope items
- Must be specific (not "other features")
- Must distinguish between "future phases" vs "never"

---

### 15. Open Questions

**Purpose:** Document unresolved decisions and required clarifications.

**Required Content:**

- Question ID
- Question Description
- Impact Assessment (low/medium/high)
- Decision Deadline
- Dependencies on Answer
- Proposed Options (if applicable)
- Decision Owner

**Validation Rules:**

- This section may be empty if all questions resolved
- If questions exist, must include impact assessment
- Must not contain critical blockers without decision owner

---

### 16. Glossary

**Purpose:** Define domain-specific terminology.

**Required Content:**

- Term
- Definition
- Context/Usage Notes
- Related Terms
- Source (if external standard)

**Validation Rules:**

- Must include at least 20 domain-specific terms
- Each term must have clear, non-circular definition
- Must include all acronyms used in the brief

---

## Depth Gate Requirements

A brief passes the depth gate only if ALL criteria are met:

| Metric                      | Minimum Required |
| --------------------------- | ---------------- |
| User Personas               | 3                |
| User Journeys               | 10               |
| Functional Requirements     | 30               |
| Non-Functional Requirements | 15               |
| Domain Invariants           | 10               |
| Compliance Constraints      | 8                |
| Integration Contracts       | 10               |
| Failure Scenarios           | 10               |
| Core Entities               | 15               |
| Roles                       | 5                |
| Permissions                 | 20               |
| Total Word Count            | 5,000            |

---

## Prohibited Patterns

The following patterns cause automatic depth gate failure:

1. **Placeholder Text:**
    - "TBD", "to be defined", "to be determined"
    - "later", "future phase", "MVP+"
    - "etc.", "and so on", "similar features"
    - "[description here]", "<fill in>", "{}"

2. **Vague Requirements:**
    - "User-friendly interface"
    - "Fast performance"
    - "Secure system"
    - "Scalable architecture"
    - (Without numeric targets or specific criteria)

3. **Generic Statements:**
    - "Industry standard security"
    - "Best practices"
    - "As needed"
    - "When appropriate"

4. **Copy-Paste Indicators:**
    - References to different industry domains
    - Inconsistent terminology
    - Mismatched personas and journeys

---

## File Location Convention

All brief templates must be stored at:

```
industry/briefs/<industry-id>/brief.md
```

Where `<industry-id>` is the standardized industry identifier from `INDUSTRY_100_SYSTEM_MAP.md`.

Example:

```
industry/briefs/ecommerce-d2c/brief.md
industry/briefs/marketplace-b2c/brief.md
industry/briefs/hospital-is/brief.md
```

---

## Validation Process

1. **Structure Check:** Verify all 16 sections present
2. **Depth Gate:** Count all required items against minimums
3. **Pattern Scan:** Check for prohibited patterns
4. **Cross-Reference:** Verify consistency (personas referenced in journeys, entities referenced in requirements)
5. **Domain Validation:** Verify domain-specific accuracy

---

## Version History

| Version | Date       | Changes         |
| ------- | ---------- | --------------- |
| 1.0.0   | 2026-04-14 | Initial release |
