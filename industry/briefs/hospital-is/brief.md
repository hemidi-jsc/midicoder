# Hospital Information System (HIS) - Universal-Fully Brief

## 1. Product Context

### Product Name

MediCore HIS - Enterprise Hospital Information System

### Product Type

B2B Healthcare SaaS Platform with On-Premise Deployment Option

### Target Market

- **Primary Markets:** North America, Europe, APAC regions with established healthcare infrastructure
- **Customer Segments:**
    - Mid-size hospitals (100-500 beds)
    - Large hospital systems (500+ beds)
    - Specialty hospitals (cardiac, oncology, pediatric)
    - Multi-facility healthcare networks
- **Geographic Focus:** US, UK, Germany, Australia, Singapore, Japan

### Problem Statement

Modern hospitals face critical challenges in patient care delivery and operational efficiency:

1. **Fragmented Clinical Systems:** Hospitals operate 10+ disconnected systems (EMR, LIS, RIS, PACS, pharmacy, billing) leading to data silos, redundant entry, and critical information gaps at point of care.

2. **Clinical Workflow Inefficiencies:** Manual processes for order entry, result review, and care coordination consume 30-40% of clinician time, contributing to burnout and delayed patient care.

3. **Interoperability Barriers:** Lack of standardized data exchange between hospital systems and external providers (labs, imaging centers, specialists) impedes care coordination and increases duplicate testing.

4. **Compliance Complexity:** Hospitals must navigate HIPAA, HITECH, Joint Commission, and local regulations while maintaining audit-ready documentation for patient safety and billing compliance.

5. **Financial Pressure:** Declining reimbursement rates and rising operational costs require precise cost tracking, denial management, and revenue cycle optimization.

6. **Patient Engagement Gaps:** Limited patient portal functionality prevents patients from accessing their health information, scheduling appointments, or communicating with providers effectively.

### Solution Overview

MediCore HIS is a comprehensive hospital information system that provides:

- **Unified Clinical Platform:** Integrated EMR with point-of-care documentation, CPOE (Computerized Physician Order Entry), and clinical decision support
- **Modular Specialty Applications:** Configurable modules for ER, OR, ICU, maternity, oncology, and specialty clinics
- **Laboratory and Imaging Integration:** Native LIS and RIS interfaces with HL7/FHIR interoperability
- **Revenue Cycle Management:** End-to-end billing, claims management, and denial prevention
- **Patient Engagement Portal:** Secure patient access to health records, appointment scheduling, and provider messaging
- **Analytics and Reporting:** Clinical quality metrics, operational dashboards, and regulatory reporting
- **Interoperability Framework:** HL7 v2/v3, FHIR R4, DICOM, and proprietary interface support

### Business Model

- **Revenue Model:** SaaS subscription with tiered pricing based on bed count and modules
    - Essential: $500/bed/month (core EMR, CPOE, basic reporting)
    - Professional: $850/bed/month (+ LIS, RIS, patient portal)
    - Enterprise: $1,200/bed/month (+ revenue cycle, advanced analytics)
    - Implementation: $50K-$500K one-time based on complexity

- **Per-Transaction Fees:** Optional add-ons for e-prescribing ($0.50/prescription), quality reporting

- **Professional Services:** Implementation, training, and customization ($100-$250/hour)

- **Annual Maintenance:** 18% of license value for on-premise deployments

### Go-to-Market Strategy

- **Launch Phase (Months 1-12):** 10 design partner hospitals with 50% discount for reference case studies
- **Growth Phase (Months 13-36):** Direct sales team, channel partnerships with healthcare IT consultants
- **Expansion Phase (Months 37-60):** International expansion, value-based care modules, telehealth integration

---

## 2. Business Goals and KPIs

### Strategic Goals

1. **Market Penetration:** Achieve 3% market share in mid-size hospital segment within 5 years
2. **Clinical Excellence:** Enable hospitals to achieve Magnet status and Top Performer designations
3. **Operational Efficiency:** Reduce hospital administrative costs by 20% through automation
4. **Patient Safety:** Support hospitals in achieving zero preventable adverse events
5. **Interoperability Leadership:** Become the most interoperable HIS in the market (HL7/FHIR certified)

### Tactical KPIs

| KPI ID | KPI Name                     | Definition                                         | Baseline | Target Y1    | Target Y3    | Measurement |
| ------ | ---------------------------- | -------------------------------------------------- | -------- | ------------ | ------------ | ----------- |
| KPI01  | Hospital Customers           | Number of live hospital deployments                | 0        | 10           | 100          | Monthly     |
| KPI02  | Annual Recurring Revenue     | Contracted annual subscription revenue             | $0       | $5M          | $50M         | Monthly     |
| KPI03  | Bed Count Under Management   | Total hospital beds on platform                    | 0        | 2,000        | 20,000       | Monthly     |
| KPI04  | Clinical User Adoption       | % of licensed users active weekly                  | N/A      | 70%          | 85%          | Monthly     |
| KPI05  | Implementation Time          | Days from contract to go-live                      | N/A      | 180          | 120          | Per Project |
| KPI06  | Net Revenue Retention        | (Starting ARR + expansions - churn) / Starting ARR | N/A      | 105%         | 115%         | Quarterly   |
| KPI07  | Customer Satisfaction (CSAT) | Average post-support interaction rating            | N/A      | 4.0/5        | 4.5/5        | Monthly     |
| KPI08  | Net Promoter Score (NPS)     | Promoter % - Detractor %                           | N/A      | 30           | 50           | Quarterly   |
| KPI09  | System Uptime                | Percentage of time system available                | N/A      | 99.9%        | 99.99%       | Monthly     |
| KPI10  | Order Entry Time             | Average time to complete CPOE order                | N/A      | <60s         | <30s         | Weekly      |
| KPI11  | Query Response Time          | 95th percentile clinical query latency             | N/A      | <2s          | <1s          | Weekly      |
| KPI12  | Interface Success Rate       | % of HL7 messages successfully processed           | N/A      | 99%          | 99.9%        | Daily       |
| KPI13  | Documentation Efficiency     | Notes completed per clinician per shift            | N/A      | Baseline+10% | Baseline+25% | Monthly     |
| KPI14  | Billing Accuracy Rate        | % of claims accepted on first submission           | N/A      | 90%          | 95%          | Monthly     |
| KPI15  | Patient Portal Activation    | % of patients with active portal accounts          | N/A      | 30%          | 50%          | Quarterly   |

### Time Horizons

**Short-Term (0-12 months):**

- 10 design partner hospitals live
- Core EMR and CPOE modules stable
- HL7 v2 and FHIR R4 certification
- $5M ARR

**Mid-Term (13-36 months):**

- 50 hospital customers
- $25M ARR
- LIS and RIS modules GA
- Revenue cycle management GA

**Long-Term (37-60 months):**

- 100+ hospital customers
- $50M ARR
- International deployments
- AI-powered clinical decision support

---

## 3. User Personas and Roles

### P01: Dr. Sarah Chen - Attending Physician (Internal Medicine)

**Demographics:** Female, 45 years old, board-certified internist

**Role in System:** Primary care provider, clinical documentation

**Goals and Motivations:**

- Efficient patient care with minimal administrative burden
- Quick access to complete patient information
- Evidence-based clinical decision support
- Meaningful use compliance without extra work

**Pain Points:**

- Current EMR requires excessive clicking and scrolling
- Critical lab results get buried in inbox
- Duplicate data entry across systems
- After-hours chart review is time-consuming

**Technical Proficiency:** Intermediate - comfortable with clinical software, frustrated by poor UX

**Usage Frequency:** Daily, 6-8 hours during clinical shifts

**Key Tasks:**

- Review patient charts before visits
- Document clinical encounters
- Enter medication orders and referrals
- Review and sign lab/imaging results
- Communicate with care team

### P02: Maria Rodriguez - Registered Nurse (ICU)

**Demographics:** Female, 38 years old, 15 years ICU experience

**Role in System:** Direct patient care, nursing documentation

**Goals and Motivations:**

- Quick documentation at bedside
- Real-time alerts for critical values
- Easy medication administration recording
- Clear visibility of care plan and orders

**Pain Points:**

- Multiple logins to different systems
- Missing information during shift handoff
- Difficult to find historical trends
- Excessive alert fatigue

**Technical Proficiency:** Beginner - task-focused, prefers simple interfaces

**Usage Frequency:** Daily, 12-hour shifts with continuous use

**Key Tasks:**

- Record vital signs and assessments
- Administer medications and document
- Document nursing interventions
- Review physician orders
- Communicate with providers

### P03: Dr. James Park - Chief Medical Information Officer (CMIO)

**Demographics:** Male, 52 years old, physician administrator

**Role in System:** Clinical leader, system optimization

**Goals and Motivations:**

- Improve clinical quality and patient safety
- Optimize clinician workflow and satisfaction
- Ensure regulatory compliance
- Drive meaningful EMR adoption

**Pain Points:**

- Difficulty measuring system impact on care
- Clinician resistance to documentation requirements
- Balancing innovation with stability
- Limited analytics capabilities

**Technical Proficiency:** Advanced - understands both clinical and IT domains

**Usage Frequency:** Weekly, 10+ hours for system management

**Key Tasks:**

- Configure clinical documentation templates
- Review system analytics and reports
- Manage clinical decision support rules
- Train super users
- Liaise with IT and vendors

### P04: Jennifer Wu - Hospital Revenue Cycle Manager

**Demographics:** Female, 47 years old, RHIA certified

**Role in System:** Financial operations, billing oversight

**Goals and Motivations:**

- Maximize clean claim rate
- Reduce days in accounts receivable
- Minimize denial rates
- Accurate cost-to-charge ratios

**Pain Points:**

- Billing delays due to incomplete documentation
- Denials from coding errors
- Difficult to track denial reasons
- Manual reconciliation required

**Technical Proficiency:** Intermediate - proficient with billing systems

**Usage Frequency:** Daily, 8 hours

**Key Tasks:**

- Monitor claim submission status
- Analyze denial patterns
- Manage coding staff
- Report on financial KPIs
- Coordinate with payers

### P05: Robert Taylor - Health Information Management (HIM) Director

**Demographics:** Male, 55 years old, RHIA certified

**Role in System:** Records management, compliance

**Goals and Motivations:**

- Ensure complete and accurate health records
- Maintain HIPAA compliance
- Support data integrity for research
- Enable efficient records retrieval

**Pain Points:**

- Incomplete chart documentation
- Audit preparation is labor-intensive
- Difficult to track record retention requirements
- Privacy risk from improper access

**Technical Proficiency:** Intermediate - knowledgeable about compliance

**Usage Frequency:** Daily, 8 hours

**Key Tasks:**

- Monitor chart completion status
- Manage release of information requests
- Conduct compliance audits
- Train staff on documentation requirements
- Oversee record retention

### Role-Permission Matrix

| Role               | Patient Care | Documentation | Orders | Billing | Reporting | Configuration | Admin |
| ------------------ | ------------ | ------------- | ------ | ------- | --------- | ------------- | ----- |
| System Admin       | ✓            | ✓             | ✓      | ✓       | ✓         | ✓             | ✓     |
| CIO/CMIO           | ✓            | ✓             | ✓      | ✓       | ✓         | ✓             | ✗     |
| Physician          | ✓            | ✓             | ✓      | ✗       | ✓         | ✗             | ✗     |
| Advanced Practice  | ✓            | ✓             | ✓      | ✗       | ✓         | ✗             | ✗     |
| Nurse              | ✓            | ✓             | ✗      | ✗       | ✓         | ✗             | ✗     |
| Nurse Practitioner | ✓            | ✓             | ✓      | ✗       | ✓         | ✗             | ✗     |
| Pharmacist         | ✓            | ✓             | ✓      | ✗       | ✓         | ✗             | ✗     |
| Lab Technologist   | ✓            | ✓             | ✗      | ✗       | ✓         | ✗             | ✗     |
| Radiologist        | ✓            | ✓             | ✗      | ✗       | ✓         | ✗             | ✗     |
| Billing Specialist | ✗            | ✓             | ✗      | ✓       | ✓         | ✗             | ✗     |
| HIM Specialist     | ✗            | ✓             | ✗      | ✗       | ✓         | ✗             | ✗     |
| Patient            | ✓            | ✗             | ✗      | ✗       | ✓         | ✗             | ✗     |

---

## 4. Core User Journeys

### J01: New Patient Registration and Intake

**Primary Persona:** Front Desk Staff (external to main personas)

**Trigger Event:** Patient arrives for appointment or admission

**Preconditions:**

- Patient has appointment scheduled or requires admission
- Registration system is operational
- Patient provides required information

**Postconditions:**

- Patient record created or updated
- Insurance verified
- Patient checked in and ready for care

**Step-by-Step Flow:**

1. Patient provides identification and insurance information
2. Staff searches for existing patient record
3. If new patient: create master patient index record
4. Collect demographic information (name, DOB, address, phone)
5. Collect insurance information (primary, secondary)
6. Verify insurance eligibility electronically
7. Collect consent forms (treatment, HIPAA, financial)
8. Assign to appropriate queue (ER, clinic, admission)
9. Generate patient wristband/identification
10. Notify care team of patient arrival

**Alternative Paths:**

- **Emergency:** Skip insurance verification, provide care first
- **Existing Patient:** Update information only
- **Transfer:** Import information from referring facility

**Success Criteria:**

- Registration completes within 5 minutes
- Zero duplicate patient records
- 100% insurance verification before billing

**Metrics Tracked:**

- Registration time
- Data entry errors
- Insurance denial rate

### J02: Physician Patient Encounter (Clinic Visit)

**Primary Persona:** P01 (Dr. Sarah Chen - Attending Physician)

**Trigger Event:** Patient scheduled for office visit

**Preconditions:**

- Patient registered and checked in
- Appointment scheduled in system
- Physician has access to patient record

**Postconditions:**

- Encounter documented
- Orders entered (if applicable)
- Patient scheduled for follow-up (if needed)
- Billing triggers generated

**Step-by-Step Flow:**

1. Physician reviews scheduled patient list
2. Open patient chart and review history
3. Review pending results and messages
4. Document chief complaint and history of present illness
5. Document review of systems and physical exam
6. Enter assessment and diagnosis (ICD-10)
7. Enter treatment plan and orders:
    - Medications (e-prescribe)
    - Labs (CPOE)
    - Imaging (CPOE)
    - Referrals
8. Document patient education provided
9. Schedule follow-up appointment
10. Sign and finalize note
11. System generates billing codes (CPT)

**Alternative Paths:**

- **Telehealth:** Virtual encounter with video documentation
- **Procedure:** Include procedure-specific documentation
- **Hospital Admission:** Trigger admission workflow

**Success Criteria:**

- Note completion within 10 minutes per patient
- All orders transmitted correctly
- CPT codes match documentation

**Metrics Tracked:**

- Documentation time per patient
- Order entry errors
- Coding accuracy

### J03: Critical Lab Result Management

**Primary Persona:** P02 (Maria Rodriguez - Nurse) with notification to P01 (Physician)

**Trigger Event:** Critical lab value identified by LIS

**Preconditions:**

- Lab order placed and specimen collected
- LIS integrated with HIS
- Alert thresholds configured

**Postconditions:**

- Ordering physician notified
- Clinical action documented
- Patient monitored as needed

**Step-by-Step Flow:**

1. LIS identifies critical value (e.g., K+ = 2.5)
2. System flags result as critical
3. Alert sent to ordering physician (in-app, SMS, page)
4. Physician receives notification and reviews result
5. Physician acknowledges alert in system
6. System prompts for clinical action
7. Physician documents assessment and orders
8. Nurse notified of physician action
9. Nurse implements orders (medication, monitoring)
10. Outcome documented

**Alternative Paths:**

- **Physician unavailable:** Escalate to covering provider
- **Already treated:** Document as informational
- **Error suspected:** Trigger repeat order

**Success Criteria:**

- Alert delivered within 5 minutes of result
- Physician acknowledgment within 30 minutes
- Clinical action documented within 1 hour

**Metrics Tracked:**

- Time to notification
- Time to acknowledgment
- Time to action

### J04: Medication Order and Administration (CPOE + Barcode)

**Primary Persona:** P01 (Physician orders) → P02 (Nurse administers)

**Trigger Event:** Patient requires medication

**Preconditions:**

- Patient has active medication order
- Medication available in pharmacy inventory
- Nurse has access to medication administration record (MAR)

**Postconditions:**

- Medication administered and documented
- Patient monitored for response/adverse effects

**Step-by-Step Flow:**

1. Physician enters medication order (drug, dose, route, frequency)
2. System performs clinical decision support checks:
    - Allergy check
    - Drug-drug interaction check
    - Dose range check
    - Renal/hepatic adjustment check
3. Pharmacist reviews and approves order
4. Medication prepared and sent to unit
5. Nurse scans patient wristband barcode
6. Nurse scans medication barcode (5 Rights verification)
7. System confirms match and allows administration
8. Nurse administers medication
9. Nurse documents administration time and response
10. System updates MAR and triggers next dose

**Alternative Paths:**

- **Hold:** Provider orders hold, system suspends doses
- **Missed:** Document reason for missed dose
- **Refused:** Document patient refusal

**Success Criteria:**

- Zero medication administration errors
- 100% barcode scanning compliance
- Real-time CDS alerts

**Metrics Tracked:**

- Medication errors
- CDS alert override rate
- Barcode scan compliance

### J05: Patient Admission to Inpatient Unit

**Primary Persona:** P02 (Nurse) with P01 (Physician) orders

**Trigger Event:** Physician admission order or ER transfer

**Preconditions:**

- Bed available on appropriate unit
- Admission orders written
- Patient registered

**Postconditions:**

- Patient admitted to unit
- Admission assessment completed
- Care plan initiated

**Step-by-Step Flow:**

1. Admission order entered by physician
2. Bed management assigns bed
3. Admitting nurse receives assignment
4. Nurse performs admission assessment:
    - Vital signs
    - Physical assessment
    - Pain assessment
    - Fall risk
    - Pressure ulcer risk
5. Nurse documents allergies and code status
6. Physician documents admission diagnosis and orders:
    - Nursing level
    - Diet
    - Activity
    - Precautions
    - Labs and imaging
    - Medications
7. System generates admission documentation
8. Patient transferred to unit
9. Handoff communication completed
10. Family notified of location

**Alternative Paths:**

- **Observation:** Different billing and workflows
- **Transfer:** From another unit/facility
- **Direct OR:** Bypass unit, go to surgery

**Success Criteria:**

- Admission to rooming within 30 minutes
- All orders transmitted before bed assignment
- Zero adverse events during transfer

**Metrics Tracked:**

- Door-to-bed time
- Order transmission time
- Assessment completion time

### J06: Surgical Scheduling and OR Workflow

**Primary Persona:** Surgical Coordinator → Surgeon → OR Nurse → Anesthesia

**Trigger Event:** Surgeon requests surgical procedure

**Preconditions:**

- Patient has surgical consultation completed
- Insurance authorization obtained (if required)
- Patient pre-operative clearance obtained

**Postconditions:**

- Surgery completed and documented
- Patient recovered and discharged to appropriate location

**Step-by-Step Flow:**

1. Surgeon schedules procedure in OR management system
2. Pre-operative testing ordered and completed
3. Pre-admission testing reviewed
4. Patient notified of surgery date/time
5. Day of surgery: patient registered and checked in
6. Pre-operative holding: verification, consent, IV started
7. Patient transported to OR
8. Time out performed (WHO surgical checklist)
9. Anesthesia administered
10. Surgery performed
11. Operative note entered by surgeon
12. Patient transported to PACU
13. Recovery documented
14. Disposition determined (ward, ICU, discharge)
15. Patient transferred to next location

**Alternative Paths:**

- **Cancellations:** Pre-op or day-of cancellation
- **Add-on:** Unplanned additional procedure
- **Emergent:** Expedited scheduling

**Success Criteria:**

- On-time room start rate > 85%
- Zero wrong-site/wrong-patient events
- Complete surgical documentation

**Metrics Tracked:**

- OR utilization
- On-time starts
- Turnover time
- Cancellation rate

### J07: Patient Discharge Planning and Execution

**Primary Persona:** Case Manager with P01 (Physician)

**Trigger Event:** Patient medically ready for discharge

**Preconditions:**

- Discharge criteria met
- Discharge destination determined
- Follow-up arranged (if needed)

**Postconditions:**

- Patient safely discharged
- Discharge instructions provided
- Billing completed

**Step-by-Step Flow:**

1. Case manager identifies discharge readiness
2. Physician enters discharge orders
3. Discharge medications reconciled and ordered
4. Discharge instructions generated and reviewed
5. Patient/family education completed
6. Follow-up appointments scheduled
7. Home health/equipment ordered (if needed)
8. Discharge summary completed by physician
9. Patient financially cleared
10. Patient transported to discharge location
11. Room cleaned and made ready for new admission

**Alternative Paths:**

- **Against Medical Advice:** Different documentation and liability
- **Transfer to Facility:** Transfer documentation
- **Death:** Mortuary and documentation workflows

**Success Criteria:**

- Readmission rate < 15% at 30 days
- Discharge instructions understood by patient
- All follow-up arranged before discharge

**Metrics Tracked:**

- Length of stay
- 30-day readmission rate
- Discharge before noon rate

### J08: Clinical Documentation Improvement (CDI)

**Primary Persona:** P05 (HIM Director) with CDI Specialist

**Trigger Event:** Query generation for incomplete documentation

**Preconditions:**

- Patient encounter documented
- CDI rules configured
- Query workflow established

**Postconditions:**

- Documentation clarified
- Accurate coding enabled
- Quality metrics supported

**Step-by-Step Flow:**

1. CDI system identifies potential queries (e.g., sepsis documentation)
2. Query generated and sent to provider
3. Provider receives query in inbox
4. Provider responds to query (adds documentation or clarifies)
5. CDI specialist reviews response
6. If sufficient: close query, notify coding
7. If insufficient: follow-up or escalate
8. Coding team uses final documentation for coding
9. Quality metrics updated

**Alternative Paths:**

- **Auto-resolution:** System auto-closes with documentation
- **Escalation:** To CMO if provider unresponsive
- **Appeal:** Provider disputes query

**Success Criteria:**

- Query response time < 48 hours
- 95% query closure rate
- Improved CCMR (Clinical Modification Capture Rate)

**Metrics Tracked:**

- Query volume
- Response time
- CCDR (Clinical Clarification Documentation Rate)

### J09: Medication Reconciliation

**Primary Persona:** Pharmacist with P02 (Nurse) and P01 (Physician)

**Trigger Event:** Patient admission, transfer, or discharge

**Preconditions:**

- Patient has medication history (home meds)
- Current orders in system

**Postconditions:**

- Accurate medication list
- Discontinuities resolved
- Orders appropriate for new setting

**Step-by-Step Flow:**

1. Home medications collected (admission)
2. Pharmacist compares home meds to current orders
3. Discrepancies identified (omissions, additions, dose changes)
4. Pharmacist queries physician on discrepancies
5. Physician clarifies intent
6. Medication list updated and reconciled
7. Reconciliation documented in record
8. At discharge: compare inpatient meds to discharge meds
9. Discharge medication list provided to patient
10. Primary care provider notified of changes

**Alternative Paths:**

- **Transfer:** Compare unit to unit orders
- **Limited information:** Use pharmacy benefit data

**Success Criteria:**

- 100% reconciliation completion
- Zero medication errors from reconciliation gaps
- Accurate discharge med list

**Metrics Tracked:**

- Reconciliation completion rate
- Discrepancy rate
- Medication errors

### J10: Incident Reporting and Management

**Primary Persona:** P02 (Nurse) reporting, Risk Management investigating

**Trigger Event:** Adverse event or near miss identified

**Preconditions:**

- Incident occurs or is identified
- Staff trained on reporting requirements

**Postconditions:**

- Incident documented
- Investigation completed
- Corrective actions implemented

**Step-by-Step Flow:**

1. Staff member identifies incident
2. Patient safety addressed immediately
3. Incident report initiated in system
4. Factual information documented (what, when, where, who)
5. Report submitted (anonymous option available)
6. Risk management notified
7. Investigation assigned
8. Root cause analysis performed (if serious)
9. Corrective action plan developed
10. Actions implemented and tracked
11. Report closed when actions complete
12. Trends analyzed for system improvements

**Alternative Paths:**

- **Sentinel Event:** Expedited investigation, external reporting
- **Good Catch:** Positive reinforcement workflow
- **Repeat Event:** Escalation to quality committee

**Success Criteria:**

- Non-punitive reporting culture (high report rate)
- Timely investigation completion
- Effective corrective actions

**Metrics Tracked:**

- Reports per 1,000 patient days
- Time to investigation close
- Recurrence rate

---

## 5. Functional Requirements

### Authentication & Authorization

**FR01: Multi-Factor Authentication**

- **Description:** System shall require MFA for all clinical users
- **Priority:** Must
- **Acceptance Criteria:**
    - Given a physician logging in, when they enter credentials, then they are prompted for MFA
    - Given emergency access, when verified, then MFA can be bypassed with audit
    - Given MFA failure, when 3 attempts fail, then account locked for 15 minutes
- **Dependencies:** None
- **Test Scenarios:** Successful MFA, MFA bypass emergency, lockout after failures

**FR02: Role-Based Access Control (RBAC)**

- **Description:** System shall enforce granular permissions based on user role
- **Priority:** Must
- **Acceptance Criteria:**
    - Given a nurse, when they access billing module, then access is denied
    - Given a physician, when they access patient chart in their department, then access granted
    - Given role change, when permissions updated, then changes apply immediately
- **Dependencies:** FR01
- **Test Scenarios:** Permission enforcement, role change, departmental restrictions

**FR03: Session Management**

- **Description:** System shall manage sessions with auto-lock for patient safety
- **Priority:** Must
- **Acceptance Criteria:**
    - Given active session, when 10 minutes of inactivity, then session auto-locks
    - Given concurrent session limit, when exceeded, then oldest session terminated
    - Given user logout, when confirmed, then all tokens invalidated
- **Dependencies:** FR01
- **Test Scenarios:** Auto-lock, concurrent sessions, logout propagation

**FR04: Break-Glass Emergency Access**

- **Description:** System shall provide emergency access with enhanced auditing
- **Priority:** Must
- **Acceptance Criteria:**
    - Given emergency situation, when break-glass activated, then access granted immediately
    - Given break-glass use, when accessed, then security team notified within 5 minutes
    - Given break-glass review, when report generated, then all access logged
- **Dependencies:** FR01, FR02
- **Test Scenarios:** Emergency access, notification, audit review

### Core Clinical Operations

**FR05: Patient Master Index (PMI)**

- **Description:** System shall maintain unique patient identifier across all encounters
- **Priority:** Must
- **Acceptance Criteria:**
    - Given patient search, when potential match found, then probability score shown
    - Given duplicate detected, when merged, then all records linked
    - Given 100,000 patients, when searched, then results within 500ms
- **Dependencies:** None
- **Test Scenarios:** Patient matching, duplicate detection, merge operations

**FR06: Problem List Management**

- **Description:** System shall maintain active and resolved problem lists per patient
- **Priority:** Must
- **Acceptance Criteria:**
    - Given problem entry, when ICD-10 selected, then standardized term stored
    - Given problem resolution, when status changed, then resolution date captured
    - Given problem list, when viewed, then sorted by date/status
- **Dependencies:** FR05
- **Test Scenarios:** Problem CRUD, ICD-10 integration, list display

**FR07: Medication List Management**

- **Description:** System shall maintain comprehensive medication history per patient
- **Priority:** Must
- **Acceptance Criteria:**
    - Given medication entry, when NDC selected, then drug details auto-populated
    - Given allergy, when medication ordered, then alert displayed
    - Given medication list, when printed, then includes instructions and dates
- **Dependencies:** FR05
- **Test Scenarios:** Medication entry, allergy alerts, list printing

**FR08: Clinical Documentation (Notes)**

- **Description:** System shall support structured and free-text clinical documentation
- **Priority:** Must
- **Acceptance Criteria:**
    - Given note template, when selected, then appropriate sections displayed
    - Given note entry, when saved, then draft stored with timestamp
    - Given note signing, when authenticated, then note finalized and time-stamped
- **Dependencies:** FR01, FR05
- **Test Scenarios:** Template selection, draft save, note signing

**FR09: Computerized Physician Order Entry (CPOE)**

- **Description:** System shall support electronic order entry for medications, labs, imaging, procedures
- **Priority:** Must
- **Acceptance Criteria:**
    - Given medication order, when entered, then CDS checks performed
    - Given lab order, when placed, then transmitted to LIS
    - Given order, when cancelled, then reason required and logged
- **Dependencies:** FR05, FR08
- **Test Scenarios:** Order entry, CDS alerts, order cancellation

**FR10: Clinical Decision Support (CDS)**

- **Description:** System shall provide evidence-based clinical alerts and recommendations
- **Priority:** Must
- **Acceptance Criteria:**
    - Given drug allergy, when medication ordered, then hard stop displayed
    - Given critical lab value, when result received, then provider alerted
    - Given CDS rule, when triggered, then override requires documentation
- **Dependencies:** FR09
- **Test Scenarios:** Allergy alerts, critical values, rule overrides

### Laboratory and Imaging

**FR11: Laboratory Information System Integration**

- **Description:** System shall integrate with LIS for order entry and result receipt
- **Priority:** Must
- **Acceptance Criteria:**
    - Given lab order, when transmitted, then LIS receives within 5 seconds
    - Given lab result, when received, then posted to chart within 1 minute
    - Given critical value, when identified, then alert sent to provider
- **Dependencies:** FR09
- **Test Scenarios:** Order transmission, result posting, critical alerts

**FR12: Radiology Information System Integration**

- **Description:** System shall integrate with RIS for imaging orders and reports
- **Priority:** Must
- **Acceptance Criteria:**
    - Given imaging order, when transmitted, then RIS receives and schedules
    - Given imaging report, when received, then displayed with images
    - Given critical finding, when documented, then provider notified
- **Dependencies:** FR09
- **Test Scenarios:** Order workflow, report display, critical findings

**FR13: PACS Image Viewing**

- **Description:** System shall provide integrated DICOM image viewing
- **Priority:** Should
- **Acceptance Criteria:**
    - Given image study, when opened, then displays within 5 seconds
    - Given image manipulation, when adjusted, then changes persist per session
    - Given 100 images, when scrolled, then smooth rendering maintained
- **Dependencies:** FR12
- **Test Scenarios:** Image loading, manipulation, performance

### Revenue Cycle

**FR14: Charge Capture**

- **Description:** System shall automatically capture billable services from documentation
- **Priority:** Must
- **Acceptance Criteria:**
    - Given encounter completion, when finalized, then charges generated
    - Given CPT code, when selected, then description and fee displayed
    - Given charge, when reviewed, then can be modified with reason
- **Dependencies:** FR08
- **Test Scenarios:** Auto-charge generation, code selection, charge modification

**FR15: Claims Generation and Submission**

- **Description:** System shall generate and transmit claims to payers
- **Priority:** Must
- **Acceptance Criteria:**
    - Given claim, when scrubbed, then errors identified before submission
    - Given claim batch, when transmitted, then acknowledgment received
    - Given rejection, when received, then flagged for correction
- **Dependencies:** FR14
- **Test Scenarios:** Claim scrubbing, submission, rejection handling

**FR16: Denial Management**

- **Description:** System shall track and manage claim denials
- **Priority:** Should
- **Acceptance Criteria:**
    - Given denial, when received, then reason code captured
    - Given denial, when appealed, then tracking maintained
    - Given denial trend, when analyzed, then report generated
- **Dependencies:** FR15
- **Test Scenarios:** Denial capture, appeal tracking, trend reporting

### Reporting and Analytics

**FR17: Clinical Quality Measures**

- **Description:** System shall calculate and report clinical quality measures
- **Priority:** Must
- **Acceptance Criteria:**
    - Given measure specification, when calculated, then numerator/denominator accurate
    - Given measure report, when generated, then includes stratification
    - Given measure submission, when transmitted, then format validated
- **Dependencies:** FR08, FR09
- **Test Scenarios:** Measure calculation, reporting, submission

**FR18: Operational Dashboards**

- **Description:** System shall provide real-time operational dashboards
- **Priority:** Should
- **Acceptance Criteria:**
    - Given dashboard, when loaded, then displays within 3 seconds
    - Given KPI widget, when refreshed, then data current within 1 minute
    - Given drill-down, when clicked, then detailed view opens
- **Dependencies:** None
- **Test Scenarios:** Dashboard load, refresh, drill-down

**FR19: Regulatory Reporting**

- **Description:** System shall support required regulatory reporting
- **Priority:** Must
- **Acceptance Criteria:**
    - Given report requirement, when generated, then format validated
    - Given submission deadline, when approaching, then alert sent
    - Given submission, when transmitted, then acknowledgment stored
- **Dependencies:** FR17
- **Test Scenarios:** Report generation, deadline alerts, submission tracking

### Interoperability

**FR20: HL7 v2 Integration**

- **Description:** System shall support HL7 v2 messaging for integration
- **Priority:** Must
- **Acceptance Criteria:**
    - Given HL7 message, when received, then parsed and processed
    - Given HL7 interface, when down, then messages queued
    - Given interface error, when logged, then alert sent
- **Dependencies:** None
- **Test Scenarios:** Message parsing, queue management, error handling

**FR21: FHIR API**

- **Description:** System shall expose FHIR R4 compliant REST API
- **Priority:** Must
- **Acceptance Criteria:**
    - Given FHIR resource, when requested, then returned in correct format
    - Given FHIR search, when executed, then results match criteria
    - Given FHIR write, when validated, then data persisted
- **Dependencies:** None
- **Test Scenarios:** Resource retrieval, search, write operations

**FR22: Direct Secure Messaging**

- **Description:** System shall support Direct protocol for secure messaging
- **Priority:** Should
- **Acceptance Criteria:**
    - Given Direct message, when sent, then delivered to recipient
    - Given Direct receipt, when received, then verified and displayed
    - Given Direct failure, when retry, then exponential backoff used
- **Dependencies:** None
- **Test Scenarios:** Message sending, receiving, retry

### Patient Engagement

**FR23: Patient Portal**

- **Description:** System shall provide secure patient portal for patient access
- **Priority:** Must
- **Acceptance Criteria:**
    - Given patient login, when authenticated, then portal displayed
    - Given health record, when viewed, then appropriate content shown
    - Given message, when sent, then delivered to care team
- **Dependencies:** FR01
- **Test Scenarios:** Patient authentication, record viewing, messaging

**FR24: Appointment Scheduling**

- **Description:** System shall enable patients to self-schedule appointments
- **Priority:** Should
- **Acceptance Criteria:**
    - Given availability, when displayed, then accurate time slots shown
    - Given appointment, when booked, then confirmation sent
    - Given cancellation, when processed, then slot released
- **Dependencies:** FR23
- **Test Scenarios:** Availability display, booking, cancellation

### Additional Functional Requirements

**FR25: e-Prescribing (Surescripts)**

- **Description:** System shall transmit electronic prescriptions to pharmacies
- **Priority:** Must
- **Acceptance Criteria:**
    - Given prescription, when transmitted, then pharmacy receives within 1 minute
    - Given refills, when authorized, then pharmacy notified
    - Given EPCS, when controlled substance, then compliant with regulations
- **Dependencies:** FR09
- **Test Scenarios:** Prescription transmission, refills, EPCS

**FR26: Immunization Registry Integration**

- **Description:** System shall interface with state immunization registries
- **Priority:** Should
- **Acceptance Criteria:**
    - Given immunization, when administered, then reported to registry
    - Given registry query, when executed, then historical records returned
    - Given reconciliation, when performed, then gaps identified
- **Dependencies:** FR20
- **Test Scenarios:** Reporting, querying, reconciliation

**FR27: Public Health Reporting**

- **Description:** System shall automate public health reporting requirements
- **Priority:** Must
- **Acceptance Criteria:**
    - Given reportable condition, when diagnosed, then flagged for reporting
    - Given report, when generated, then format validated
    - Given transmission, when completed, then acknowledgment stored
- **Dependencies:** FR20
- **Test Scenarios:** Condition flagging, report generation, transmission

**FR28: Two-Way Referral Management**

- **Description:** System shall manage specialist referrals electronically
- **Priority:** Should
- **Acceptance Criteria:**
    - Given referral, when created, then specialist receives electronically
    - Given referral response, when received, then displayed in system
    - Given referral closure, when completed, then summary received
- **Dependencies:** FR22
- **Test Scenarios:** Referral creation, response, closure

**FR29: Meaningful Use / Promoting Interoperability**

- **Description:** System shall support CMS Promoting Interoperability reporting
- **Priority:** Must
- **Acceptance Criteria:**
    - Given measure, when calculated, then accurate for reporting period
    - Given attestation, when submitted, then data validated
    - Given exclusion, when requested, then process supported
- **Dependencies:** FR17, FR21
- **Test Scenarios:** Measure calculation, attestation, exclusions

**FR30: Data Export and Portability**

- **Description:** System shall support patient data export for portability
- **Priority:** Should
- **Acceptance Criteria:**
    - Given export request, when processed, then complete record provided
    - Given CCDA format, when generated, then validated against standard
    - Given patient consent, when required, then workflow supported
- **Dependencies:** FR21
- **Test Scenarios:** Export generation, CCDA validation, consent workflow

**FR31: Telehealth Integration**

- **Description:** System shall support virtual care encounters
- **Priority:** Should
- **Acceptance Criteria:**
    - Given telehealth visit, when initiated, then video connected
    - Given telehealth documentation, when completed, then stored with encounter
    - Given telehealth billing, when processed, then correct modifiers applied
- **Dependencies:** FR08
- **Test Scenarios:** Video connection, documentation, billing

**FR32: Mobile Clinician Applications**

- **Description:** System shall provide mobile apps for clinicians
- **Priority:** Should
- **Acceptance Criteria:**
    - Given mobile app, when logged in, then MFA required
    - Given patient data, when viewed, then read-only unless signed
    - Given push notification, when sent, then received within 10 seconds
- **Dependencies:** FR01
- **Test Scenarios:** Mobile authentication, data access, notifications

---

## 6. Non-Functional Requirements

### Security

**NFR01: Data Encryption at Rest**

- **Category:** Security
- **Description:** All PHI must be encrypted at rest using AES-256
- **Measurement Criteria:** Database encryption verification, storage encryption audit
- **Target Value:** 100% of data encrypted
- **Priority:** Must

**NFR02: Data Encryption in Transit**

- **Category:** Security
- **Description:** All data in transit must use TLS 1.3 or higher
- **Measurement Criteria:** SSL Labs scan, network traffic analysis
- **Target Value:** A+ SSL Labs rating, 100% TLS 1.3
- **Priority:** Must

**NFR03: Access Control**

- **Category:** Security
- **Description:** System shall implement least-privilege access with role-based controls
- **Measurement Criteria:** Access review audit, permission testing
- **Target Value:** 100% of access role-based, quarterly access reviews
- **Priority:** Must

**NFR04: Audit Logging**

- **Category:** Security
- **Description:** All access to PHI must be logged with user, timestamp, and action
- **Measurement Criteria:** Audit log completeness review
- **Target Value:** 100% of PHI access logged, immutable logs
- **Priority:** Must

**NFR05: Security Incident Response**

- **Category:** Security
- **Description:** System shall support security incident detection and response
- **Measurement Criteria:** Incident response drill, time-to-detect metrics
- **Target Value:** Detection within 1 hour, response within 4 hours
- **Priority:** Must

**NFR06: Penetration Testing**

- **Category:** Security
- **Description:** System shall undergo annual penetration testing
- **Measurement Criteria:** Penetration test report, remediation tracking
- **Target Value:** Annual testing, critical issues resolved within 30 days
- **Priority:** Must

### Performance

**NFR07: Clinical Query Performance**

- **Category:** Performance
- **Description:** Clinical queries (chart access, search) must respond within 2 seconds for 95th percentile
- **Measurement Criteria:** Performance monitoring, synthetic transactions
- **Target Value:** p95 < 2s, p99 < 5s
- **Priority:** Must

**NFR08: Order Entry Performance**

- **Category:** Performance
- **Description:** Order entry and submission must complete within 5 seconds
- **Measurement Criteria:** Transaction timing, user testing
- **Target Value:** < 5s for 95% of orders
- **Priority:** Must

**NFR09: Report Generation Performance**

- **Category:** Performance
- **Description:** Standard reports must generate within 30 seconds
- **Measurement Criteria:** Report timing, queue monitoring
- **Target Value:** < 30s for standard reports, < 5 minutes for complex
- **Priority:** Should

### Reliability

**NFR10: System Availability**

- **Category:** Reliability
- **Description:** System must maintain 99.9% uptime during business hours
- **Measurement Criteria:** Uptime monitoring, status page
- **Target Value:** 99.9% uptime (maximum 4.38 hours downtime/month)
- **Priority:** Must

**NFR11: Disaster Recovery**

- **Category:** Reliability
- **Description:** System must support disaster recovery with RTO of 4 hours and RPO of 1 hour
- **Measurement Criteria:** DR drill results, backup restoration testing
- **Target Value:** RTO < 4 hours, RPO < 1 hour, quarterly drills
- **Priority:** Must

**NFR12: Data Durability**

- **Category:** Reliability
- **Description:** Patient data must have 99.999999999% (11 nines) durability
- **Measurement Criteria:** Storage provider SLA, replication verification
- **Target Value:** Zero data loss, cross-region replication
- **Priority:** Must

### Scalability

**NFR13: Concurrent Users**

- **Category:** Scalability
- **Description:** System must support 10,000 concurrent users per large hospital deployment
- **Measurement Criteria:** Load testing, production monitoring
- **Target Value:** 10,000 concurrent users with acceptable performance
- **Priority:** Must

**NFR14: Data Volume**

- **Category:** Scalability
- **Description:** System must support 10 years of clinical data per hospital
- **Measurement Criteria:** Performance testing with historical data
- **Target Value:** No performance degradation with 10-year history
- **Priority:** Should

### Usability

**NFR15: Clinician Usability**

- **Category:** Usability
- **Description:** Clinicians must be able to complete common tasks efficiently
- **Measurement Criteria:** User testing, task completion time
- **Target Value:** 80% of users complete key tasks within expected time
- **Priority:** Should

**NFR16: Accessibility**

- **Category:** Usability
- **Description:** System must meet WCAG 2.1 AA accessibility standards
- **Measurement Criteria:** Accessibility audit, screen reader testing
- **Target Value:** WCAG 2.1 AA compliance
- **Priority:** Should

### Compliance

**NFR17: HIPAA Compliance**

- **Category:** Compliance
- **Description:** System must support HIPAA Privacy and Security Rule compliance
- **Measurement Criteria:** HIPAA security risk analysis, compliance audit
- **Target Value:** Full HIPAA compliance, annual risk analysis
- **Priority:** Must

**NFR18: HITECH Compliance**

- **Category:** Compliance
- **Description:** System must support HITECH Act requirements including breach notification
- **Measurement Criteria:** Breach notification drill, audit log review
- **Target Value:** Breach notification within 60 days as required
- **Priority:** Must

**NFR19: ONC Health IT Certification**

- **Category:** Compliance
- **Description:** System must be ONC Health IT Certified
- **Measurement Criteria:** Certification body audit, certification listing
- **Target Value:** ONC ATC certified for applicable criteria
- **Priority:** Must

---

## 7. Domain Rules and Invariants

### INV01: Patient Identity Integrity

- **Name:** Patient Identity Must Be Unique and Consistent
- **Description:** Each patient must have exactly one master patient record; duplicate records must be prevented or merged
- **Formal Statement:** `∀p1, p2 ∈ Patients, (p1.ssn == p2.ssn AND p1.dob == p2.dob) → p1.id == p2.id OR merge_required`
- **Enforcement Point:** Runtime (on patient registration)
- **Violation Handling:** Error code `DUPLICATE_PATIENT`; suggest merge workflow
- **Test Cases:** Duplicate registration attempt, merge operation, identity resolution

### INV02: Order Status State Machine

- **Name:** Medical Orders Must Follow Valid State Transitions
- **Description:** Orders must only transition through predefined valid states
- **Formal Statement:** Valid transitions: `ACTIVE → DISCONTINUED | FULFILLED → COMPLETED`; Invalid: `COMPLETED → ACTIVE`
- **Enforcement Point:** Runtime (on order status change)
- **Violation Handling:** Error code `INVALID_ORDER_TRANSITION`; reject transition
- **Test Cases:** Valid transition, invalid transition, concurrent status changes

### INV03: Medication Allergy Safety

- **Name:** Medication Orders Must Be Checked Against Known Allergies
- **Description:** Before medication administration, allergies must be checked and alerts raised for matches
- **Formal Statement:** `∀order ∈ MedicationOrders, ∀allergy ∈ Patient.Allergies, (allergy.drug_class == order.drug_class) → alert_required`
- **Enforcement Point:** Runtime (at order entry and administration)
- **Violation Handling:** Hard stop with override requiring documentation
- **Test Cases:** Allergy match, allergy override, new allergy addition

### INV04: Critical Result Acknowledgment

- **Name:** Critical Results Must Be Acknowledged by Provider
- **Description:** Critical lab/imaging results require explicit provider acknowledgment within defined time
- **Formal Statement:** `∀result ∈ CriticalResults, acknowledged(result) OR escalations_required`
- **Enforcement Point:** Runtime (with escalation after timeout)
- **Violation Handling:** Escalation to covering provider, then department head
- **Test Cases:** Timely acknowledgment, escalation trigger, covering provider workflow

### INV05: Signature Authentication

- **Name:** Clinical Entries Must Be Authenticated by Authorized Provider
- **Description:** Only properly authenticated providers can sign clinical documentation
- **Formal Statement:** `∀entry ∈ ClinicalEntries, signed(entry) → ∃user ∈ Providers, user.authenticated AND user.authorized`
- **Enforcement Point:** Runtime (at signing)
- **Violation Handling:** Error code `UNAUTHORIZED_SIGNATURE`; require authentication
- **Test Cases:** Valid signature, unauthorized attempt, session timeout

### INV06: Billing-Documentation Alignment

- **Name:** Billed Services Must Be Supported by Documentation
- **Description:** Charges for professional services must have supporting clinical documentation
- **Formal Statement:** `∀charge ∈ ProfessionalCharges, ∃documentation ∈ ClinicalNotes, documentation.supports(charge)`
- **Enforcement Point:** Runtime (at billing submission)
- **Violation Handling:** Error code `UNDOCUMENTED_CHARGE`; require documentation
- **Test Cases:** Complete documentation, missing documentation, retrospective documentation

### INV07: Access Minimum Necessary

- **Name:** PHI Access Must Follow Minimum Necessary Principle
- **Description:** Users can only access PHI necessary for their role and current patient assignments
- **Formal Statement:** `∀access ∈ PHIAccess, access.authorized → (access.user.role_permitted AND access.patient.in_assignments)`
- **Enforcement Point:** Runtime (on every PHI access)
- **Violation Handling:** Error code `ACCESS_DENIED`; log as potential violation
- **Test Cases:** Authorized access, unauthorized access, role-based restrictions

### INV08: Medication Administration 5-Rights

- **Name:** Medication Administration Must Verify 5 Rights
- **Description:** Before administration, must verify right patient, drug, dose, route, time
- **Formal Statement:** `∀admin ∈ MedicationAdministration, admin.validated → (patient ✓ ∧ drug ✓ ∧ dose ✓ ∧ route ✓ ∧ time ✓)`
- **Enforcement Point:** Runtime (at barcode scan)
- **Violation Handling:** Error code `ADMINISTRATION_ERROR`; prevent administration
- **Test Cases:** All rights match, single right mismatch, multiple mismatches

### INV09: Data Retention Compliance

- **Name:** Health Records Must Be Retained Per Regulatory Requirements
- **Description:** Patient records must be retained for minimum required period (typically 7-10 years)
- **Formal Statement:** `∀record ∈ HealthRecords, retention_period(record) >= jurisdiction.minimum_retention`
- **Enforcement Point:** Runtime (on deletion attempt), Batch (retention processing)
- **Violation Handling:** Error code `RETENTION_VIOLATION`; prevent deletion
- **Test Cases:** Early deletion attempt, retention period expiry, jurisdictional variations

### INV10: Consent Management

- **Name:** Protected Information Access Must Respect Patient Consents
- **Description:** Access to sensitive information (mental health, substance abuse, HIV) requires specific consent
- **Formal Statement:** `∀access ∈ SensitivePHIAccess, access.granted → consent.exists AND consent.active AND consent.covers(access.type)`
- **Enforcement Point:** Runtime (on sensitive data access)
- **Violation Handling:** Error code `CONSENT_REQUIRED`; require consent verification
- **Test Cases:** Consent present, consent expired, consent scope mismatch

---

## 8. Compliance and Regulatory Constraints

### CC01: HIPAA Privacy Rule

- **Regulatory Framework:** HIPAA (Health Insurance Portability and Accountability Act)
- **Reference:** 45 CFR Part 160 and 164 - Privacy Rule
- **Regulatory Overlay ID:** RX01 (Privacy & PII Protection), RX04 (Clinical Safety & Health Privacy)
- **Requirement Description:** Protect individually identifiable health information; require patient authorization for most disclosures
- **Implementation Controls:**
    - Access controls and authentication
    - Minimum necessary access enforcement
    - Patient authorization workflow
    - Breach detection and notification
- **Evidence Requirements:** HIPAA security risk analysis, access logs, authorization records
- **Audit Frequency:** Annual security risk analysis; continuous monitoring

### CC02: HIPAA Security Rule

- **Regulatory Framework:** HIPAA
- **Reference:** 45 CFR Part 164 Subpart C - Security Rule
- **Regulatory Overlay ID:** RX01, RX11 (Immutable Audit Evidence)
- **Requirement Description:** Implement administrative, physical, and technical safeguards for e-PHI
- **Implementation Controls:**
    - Access management (unique user IDs, emergency access)
    - Audit controls (activity logs)
    - Integrity controls (encryption, checksums)
    - Transmission security (TLS)
- **Evidence Requirements:** Security policies, risk analysis, audit logs, encryption certificates
- **Audit Frequency:** Annual; continuous for technical controls

### CC03: HIPAA Breach Notification

- **Regulatory Framework:** HIPAA HITECH
- **Reference:** 45 CFR Part 164.400-414 - Breach Notification Rule
- **Regulatory Overlay ID:** RX01, RX11
- **Requirement Description:** Notify affected individuals, HHS, and media of breaches affecting 500+ individuals
- **Implementation Controls:**
    - Breach detection workflow
    - Notification templates and processes
    - Breach documentation and tracking
- **Evidence Requirements:** Breach logs, notification records, HHS submissions
- **Audit Frequency:** Per incident; annual process review

### CC04: ONC Health IT Certification

- **Regulatory Framework:** ONC (Office of the National Coordinator)
- **Reference:** 45 CFR Part 170 - Health IT Certification Program
- **Regulatory Overlay ID:** RX04
- **Requirement Description:** EHR must be certified for Promoting Interoperability Programs
- **Implementation Controls:**
    - Certified EHR functionality (CDS, order management, results management)
    - FHIR-based interoperability
    - USCDI data exchange
    - Security and privacy features
- **Evidence Requirements:** ONC ATC certification listing, certification body audit reports
- **Audit Frequency:** Recertification every 3 years; continuous compliance

### CC05: Meaningful Use / Promoting Interoperability

- **Regulatory Framework:** CMS (Centers for Medicare & Medicaid Services)
- **Reference:** Promoting Interoperability Programs
- **Regulatory Overlay ID:** RX04
- **Requirement Description:** Support providers in reporting for incentive programs
- **Implementation Controls:**
    - Measure calculation and tracking
    - Exclusion workflows
    - Data submission to QHP
    - Attestation support
- **Evidence Requirements:** Measure reports, submissions, attestations
- **Audit Frequency:** Annual program year

### CC06: CLIA Laboratory Compliance

- **Regulatory Framework:** CLIA (Clinical Laboratory Improvement Amendments)
- **Reference:** 42 CFR Part 493
- **Regulatory Overlay ID:** RX04
- **Requirement Description:** Laboratory systems must support CLIA requirements for test validation, QC, and reporting
- **Implementation Controls:**
    - Test validation documentation
    - QC tracking and alerts
    - Proficiency testing management
    - Operator credentialing
- **Evidence Requirements:** Validation records, QC logs, PT results, credentials
- **Audit Frequency:** Biennial CLIA inspection; ongoing

### CC07: Stark Law and Anti-Kickback

- **Regulatory Framework:** Stark Law, Anti-Kickback Statute
- **Reference:** 42 USC 1395nn; 42 USC 1320a-7b
- **Regulatory Overlay ID:** RX11 (Immutable Audit Evidence)
- **Requirement Description:** Prevent improper financial relationships from influencing referrals
- **Implementation Controls:**
    - Referral tracking
    - Financial relationship disclosure
    - Audit trail for referrals
- **Evidence Requirements:** Referral logs, disclosure records, audit reports
- **Audit Frequency:** Annual compliance review

### CC08: State Health Information Privacy Laws

- **Regulatory Framework:** Various State Laws (e.g., CMIA in California, HIPAA additions)
- **Reference:** State-specific statutes
- **Regulatory Overlay ID:** RX01, RX12 (Data Residency & Cross-border Transfer)
- **Requirement Description:** Comply with state-specific health information privacy requirements
- **Implementation Controls:**
    - Jurisdiction-specific consent requirements
    - Data residency controls
    - Enhanced protection for sensitive data (mental health, substance abuse)
- **Evidence Requirements:** Jurisdiction configuration, consent records, data location logs
- **Audit Frequency:** Annual compliance review

### CC09: Joint Commission Standards

- **Regulatory Framework:** The Joint Commission
- **Reference:** National Patient Safety Goals, Standards for Hospitals
- **Regulatory Overlay ID:** RX04
- **Requirement Description:** Support compliance with Joint Commission accreditation standards
- **Implementation Controls:**
    - Patient identification processes
    - Medication management controls
    - Infection tracking
    - Incident reporting
- **Evidence Requirements:** Process documentation, tracking reports, survey readiness
- **Audit Frequency:** Triennial survey; ongoing monitoring

### CC10: FDA Medical Device Reporting (for certain functionalities)

- **Regulatory Framework:** FDA (Food and Drug Administration)
- **Reference:** 21 CFR Part 803 - Medical Device Reporting
- **Regulatory Overlay ID:** RX04, RX09 (Safety, Incident & Traceability)
- **Requirement Description:** Certain clinical decision support features may be regulated as medical devices
- **Implementation Controls:**
    - MDR determination documentation
    - Adverse event reporting workflow
    - Software validation (if device)
- **Evidence Requirements:** MDR determination, adverse event reports, validation documentation
- **Audit Frequency:** Ongoing; annual review of MDR determination

---

## 9. Integration Requirements

### INT01: Laboratory Information System (LIS)

- **Contract ID:** INT01
- **Integration Type:** Bi-directional HL7 v2
- **External System Name:** LIS (e.g., Sunquest, Cerner RLTS, Epic Beaker)
- **Protocol:** HL7 v2.5.1 over MLLP
- **Authentication Method:** IP allowlist + application credentials
- **Data Format:** HL7 v2 segments (ORM, ORC, OBR, OBX)
- **Rate Limits:** 1000 messages/minute
- **SLA Requirements:** 99.9% availability; < 5 second order-to-ack
- **Error Handling:**
    - Message rejection: Return ACK with error code
    - Interface down: Queue messages, alert on timeout
    - Data validation: Reject invalid orders with explanation
- **Retry Policy:** Exponential backoff (1m, 5m, 15m, 1h); max 24 hours
- **Data Mapping:**
    - Patient demographics: PID segment
    - Lab orders: ORM, OBR segments
    - Results: ORU, OBX segments
    - Critical values: Alert with OBR-25

### INT02: Radiology Information System (RIS)

- **Contract ID:** INT02
- **Integration Type:** Bi-directional HL7 v2
- **External System Name:** RIS (e.g., Centricity, RadNet, Epic Resolute)
- **Protocol:** HL7 v2.5.1 over MLLP
- **Authentication Method:** IP allowlist + application credentials
- **Data Format:** HL7 v2 segments
- **Rate Limits:** 500 messages/minute
- **SLA Requirements:** 99.9% availability; < 10 second order-to-ack
- **Error Handling:**
    - Order rejection: Return ACK with reason
    - Status updates: Process asynchronously
- **Retry Policy:** Queue with 15-minute retry interval
- **Data Mapping:**
    - Imaging orders: ORM/OBR
    - Scheduling: SIU segments
    - Reports: ORU segments with DICOM SR
    - Preliminary results: ALERT messages

### INT03: Pharmacy System / e-Prescribing (Surescripts)

- **Contract ID:** INT03
- **Integration Type:** Outbound NCPDP/HL7
- **External System Name:** Surescripts, pharmacy systems
- **Protocol:** NCPDP Telecommunications Standard over HTTPS
- **Authentication Method:** Mutual TLS + credentials
- **Data Format:** NCPDP D.0050.00
- **Rate Limits:** 100 prescriptions/minute
- **SLA Requirements:** 99.9% availability; < 30 second acknowledgment
- **Error Handling:**
    - Rejection: Return with rejection code
    - Timeout: Retry with original request
- **Retry Policy:** 3 retries over 5 minutes
- **Data Mapping:**
    - Patient: NCPDP patient fields
    - Prescription: NCPDP prescription fields
    - Refills: Refill authorization messages
    - EPCS: DEA-compliant controlled substance format

### INT04: Health Information Exchange (HIE)

- **Contract ID:** INT04
- **Integration Type:** Bi-directional FHIR/Direct
- **External System Name:** Regional HIE (e.g., CommonWell, Carequality)
- **Protocol:** FHIR R4 REST, Direct Secure Messaging
- **Authentication Method:** OAuth 2.0, X.509 certificates
- **Data Format:** FHIR resources, CCDA documents
- **Rate Limits:** 100 queries/minute
- **SLA Requirements:** 99% availability; < 30 second query response
- **Error Handling:**
    - Query failure: Return with FHIR OperationOutcome
    - Network failure: Queue and retry
- **Retry Policy:** Query: no retry; Document: retry with backoff
- **Data Mapping:**
    - Patient queries: Patient resource search
    - Document exchange: CCDA via Direct
    - Summaries: FHIR Patient + related resources

### INT05: Claims Clearinghouse

- **Contract ID:** INT05
- **Integration Type:** Outbound EDI
- **External System Name:** Clearinghouse (e.g., Change Healthcare, Availity)
- **Protocol:** SFTP + EDI X12
- **Authentication Method:** SFTP credentials
- **Data Format:** EDI 837P/837I (professional/institutional claims)
- **Rate Limits:** Batch processing, 1000 claims/batch
- **SLA Requirements:** 99% availability; same-day acknowledgment
- **Error Handling:**
    - Rejection: Process 999/277CA response
    - Formatting error: Return to billing for correction
- **Retry Policy:** Automatic retransmission for missing acknowledgments
- **Data Mapping:**
    - Claims: 837 segments
    - Acknowledgments: 999, 277CA
    - Remittance: 835 ERA/EOB

### INT06: Immunization Registry

- **Contract ID:** INT06
- **Integration Type:** Bi-directional HL7/FHIR
- **External System Name:** State Immunization Information System (IIS)
- **Protocol:** HIeR (HL7 Immunization Exchange) or FHIR Immunization
- **Authentication Method:** OAuth 2.0 or credentials
- **Data Format:** HIeR v2, FHIR Immunization resource
- **Rate Limits:** 100 transactions/minute
- **SLA Requirements:** 99% availability; < 5 second response
- **Error Handling:**
    - Duplicate detection: Process as update
    - Validation error: Return to user with correction
- **Retry Policy:** 3 retries over 10 minutes
- **Data Mapping:**
    - Immunizations: HIeR v2 / FHIR Immunization
    - Patient lookup: Demographic match
    - History retrieval: Query by patient

### INT07: Cancer Registry

- **Contract ID:** INT07
- **Integration Type:** Outbound HL7
- **External System Name:** State Cancer Registry (SEER, NPCR)
- **Protocol:** HL7 v2.5 with specific segments
- **Authentication Method:** Credentials + IP allowlist
- **Data Format:** HL7 with cancer-specific extensions
- **Rate Limits:** Batch processing
- **SLA Requirements:** Monthly reporting cycle
- **Error Handling:**
    - Validation failure: Return for correction
    - Missing data: Flag for completion
- **Retry Policy:** Manual review and resubmission
- **Data Mapping:**
    - Cancer cases: MOR message with cancer extensions
    - Patient data: PID segment
    - Clinical data: Custom cancer fields

### INT08: Public Health Reporting (CDPH, etc.)

- **Contract ID:** INT08
- **Integration Type:** Outbound HL7/FHIR
- **External System Name:** Public Health Departments
- **Protocol:** HL7 v2, FHIR, or Direct
- **Authentication Method:** Credentials
- **Data Format:** HL7, FHIR, HL7-based standards (LOINC)
- **Rate Limits:** Varies by report type
- **SLA Requirements:** Timely reporting (often 24-72 hours for reportable conditions)
- **Error Handling:**
    - Rejection: Resubmit with corrections
    - Acknowledgment: Store for compliance
- **Retry Policy:** Until acknowledgment received
- **Data Mapping:**
    - Reportable conditions: LOINC-based CDA/HL7
    - Laboratory results: LOINC + organism data
    - Vital events: State-specific formats

### INT09: Revenue Cycle / Billing System

- **Contract ID:** INT09
- **Integration Type:** Bi-directional HL7/API
- **External System Name:** Billing System (e.g., Waystar, Experian)
- **Protocol:** HL7 v2 or REST API
- **Authentication Method:** API key or OAuth
- **Data Format:** HL7 FHS, JSON
- **Rate Limits:** 500 transactions/minute
- **SLA Requirements:** Real-time or near-real-time
- **Error Handling:**
    - Billing error: Flag for manual review
    - Patient not found: Create in billing system
- **Retry Policy:** Queue with 5-minute retry
- **Data Mapping:**
    - Encounters: FHS messages
    - Charges: EVN+PID+PV1+DG1
    - Payments: Financial transaction messages

### INT10: Patient Portal / Engagement Platform

- **Contract ID:** INT10
- **Integration Type:** Bi-directional API
- **External System Name:** Patient Engagement Platform (e.g., Redox, HealtheLife)
- **Protocol:** REST API (FHIR preferred)
- **Authentication Method:** OAuth 2.0
- **Data Format:** FHIR R4, JSON
- **Rate Limits:** 1000 requests/minute
- **SLA Requirements:** 99.9% availability; < 2 second response
- **Error Handling:**
    - Authentication failure: Re-authenticate
    - Data not found: Return appropriate FHIR response
- **Retry Policy:** Client-side retry with exponential backoff
- **Data Mapping:**
    - Patient registration: Patient resource
    - Appointments: Appointment resource
    - Messages: Communication resource
    - Results: Observation resource

### INT11: Telehealth Platform

- **Contract ID:** INT11
- **Integration Type:** Bi-directional API
- **External System Name:** Telehealth Platform (e.g., Twilio, Zoom for Healthcare)
- **Protocol:** REST Webhooks + Real-time
- **Authentication Method:** OAuth 2.0, API keys
- **Data Format:** JSON, WebRTC
- **Rate Limits:** 100 sessions/minute
- **SLA Requirements:** 99.9% uptime; < 5 second connection time
- **Error Handling:**
    - Connection failure: Retry with alternative endpoint
    - Video failure: Fall back to audio-only
- **Retry Policy:** Automatic reconnection attempts
- **Data Mapping:**
    - Session initiation: Create encounter
    - Session completion: Update encounter status
    - Billing events: Generate charge codes

### INT12: Claims Adjudication (Payer Direct)

- **Contract ID:** INT12
- **Integration Type:** Bi-directional EDI/API
- **External System Name:** Payers (Medicare, Medicaid, Commercial)
- **Protocol:** EDI X12, API (varies by payer)
- **Authentication Method:** Payer-specific (credentials, certificates)
- **Data Format:** 270/271 (eligibility), 835 (remittance), API JSON
- **Rate Limits:** Payer-specific
- **SLA Requirements:** Real-time eligibility; batch remittance
- **Error Handling:**
    - Eligibility failure: Notify user
    - Remittance delay: Queue for processing
- **Retry Policy:** Per payer specifications
- **Data Mapping:**
    - Eligibility: 270/271 segments
    - Remittance: 835 segments
    - Explanation: EOB mapping

---

## 10. Data Model Expectations

### Core Entities

**Patient**

- **Description:** Master patient record
- **Primary Key:** `patient_id` (UUID)
- **Fields:**
    - `mrn` (string, required, unique per facility)
    - `first_name` (string, required)
    - `last_name` (string, required)
    - `middle_name` (string)
    - `dob` (date, required)
    - `gender` (enum: male, female, other, unknown)
    - `ssn` (string, encrypted)
    - `marital_status` (enum)
    - `race` (string)
    - `ethnicity` (enum)
    - `language` (string)
    - `email` (string)
    - `phone_primary` (string)
    - `phone_secondary` (string)
    - `address` (Address VO)
    - `emergency_contact` (Contact VO)
    - `insurance_plans` (array of Insurance VO)
    - `created_at` (datetime, required)
    - `updated_at` (datetime, required)
- **Relationships:** `encounters`, `orders`, `allergies`, `medications`
- **Indexes:** `mrn`, `dob + last_name`, `ssn_hash`
- **Retention Policy:** Permanent (per state law)

**Encounter**

- **Description:** Patient encounter (visit, admission)
- **Primary Key:** `encounter_id` (UUID)
- **Fields:**
    - `patient_id` (UUID, required)
    - `encounter_number` (string, unique per facility)
    - `type` (enum: outpatient, inpatient, emergency, observation)
    - `class` (enum: scheduled, unscheduled)
    - `status` (enum: planned, in_progress, finished, cancelled)
    - `admitted_at` (datetime)
    - `discharged_at` (datetime)
    - `admission_type` (enum: elective, emergency, transfer)
    - `discharge_disposition` (enum: home, transfer, died, AMA)
    - `attending_physician_id` (UUID)
    - `consulting_physicians` (array of UUID)
    - `location` (string)
    - `bed_id` (string)
    - `diagnoses` (array of Diagnosis VO)
    - `created_at` (datetime, required)
    - `updated_at` (datetime, required)
- **Relationships:** `patient`, `orders`, `documents`, `charges`
- **Indexes:** `patient_id`, `admitted_at`, `status`
- **Retention Policy:** 10 years minimum

**ClinicalDocument**

- **Description:** Clinical note or document
- **Primary Key:** `document_id` (UUID)
- **Fields:**
    - `encounter_id` (UUID, required)
    - `patient_id` (UUID, required)
    - `type` (enum: progress_note, consultation, discharge_summary, etc.)
    - `section_type` (string, e.g., HPI, ROS, Assessment, Plan)
    - `content` (text, required)
    - `structured_data` (JSON)
    - `status` (enum: draft, signed, amended)
    - `authored_at` (datetime)
    - `signed_at` (datetime)
    - `author_id` (UUID, required)
    - `author_type` (enum: physician, nurse, etc.)
    - `signed_by_id` (UUID)
    - `amended_document_id` (UUID)
    - `created_at` (datetime, required)
    - `updated_at` (datetime, required)
- **Relationships:** `encounter`, `patient`, `author`
- **Indexes:** `encounter_id`, `author_id`, `authored_at`
- **Retention Policy:** Permanent

**MedicationOrder**

- **Description:** Medication order
- **Primary Key:** `order_id` (UUID)
- **Fields:**
    - `encounter_id` (UUID, required)
    - `patient_id` (UUID, required)
    - `medication_id` (UUID, required)
    - `ndc` (string)
    - `drug_name` (string)
    - `dosage` (string)
    - `route` (string)
    - `frequency` (string)
    - `indication` (string)
    - `start_date` (datetime)
    - `end_date` (datetime)
    - `refills` (integer)
    - `status` (enum: active, discontinued, held, completed)
    - `discontinued_reason` (string)
    - `ordered_by_id` (UUID, required)
    - `verified_by_id` (UUID)
    - `created_at` (datetime, required)
    - `updated_at` (datetime, required)
- **Relationships:** `encounter`, `patient`, `medication`, `administered_doses`
- **Indexes:** `patient_id`, `status`, `medication_id`
- **Retention Policy:** 10 years

**Order**

- **Description:** Clinical order (lab, imaging, procedure)
- **Primary Key:** `order_id` (UUID)
- **Fields:**
    - `encounter_id` (UUID, required)
    - `patient_id` (UUID, required)
    - `type` (enum: lab, imaging, procedure, referral)
    - `code` (string, LOINC/CPT/other)
    - `display_name` (string)
    - `status` (enum: active, completed, cancelled, failed)
    - `priority` (enum: routine, urgent, stat)
    - `location` (string)
    - `ordered_by_id` (UUID, required)
    - `scheduled_at` (datetime)
    - `completed_at` (datetime)
    - `result_id` (UUID)
    - `created_at` (datetime, required)
    - `updated_at` (datetime, required)
- **Relationships:** `encounter`, `patient`, `results`
- **Indexes:** `patient_id`, `status`, `ordered_by_id`
- **Retention Policy:** 10 years

**OrderResult**

- **Description:** Order result (lab value, imaging report)
- **Primary Key:** `result_id` (UUID)
- **Fields:**
    - `order_id` (UUID, required)
    - `patient_id` (UUID, required)
    - `type` (enum: lab, imaging, pathology)
    - `status` (enum: preliminary, final, amended)
    - `value` (string)
    - `unit` (string)
    - `reference_range` (string)
    - `flag` (enum: normal, high, low, critical)
    - `interpretation` (text)
    - `report_text` (text)
    - `reported_at` (datetime)
    - `reporter_id` (UUID)
    - `reviewed_by_id` (UUID)
    - `reviewed_at` (datetime)
    - `critical_notified_at` (datetime)
    - `critical_acknowledged_at` (datetime)
    - `created_at` (datetime, required)
- **Relationships:** `order`, `patient`
- **Indexes:** `order_id`, `patient_id`, `reported_at`
- **Retention Policy:** 10 years

**Allergy**

- **Description:** Patient allergy/intolerance
- **Primary Key:** `allergy_id` (UUID)
- **Fields:**
    - `patient_id` (UUID, required)
    - `substance` (string)
    - `substance_code` (string, SNOMED)
    - `category` (enum: medication, food, environmental, other)
    - `reaction` (text)
    - `severity` (enum: mild, moderate, severe, life_threatening)
    - `status` (enum: active, inactive, resolved)
    - `documented_by_id` (UUID)
    - `documented_at` (datetime, required)
    - `created_at` (datetime, required)
- **Relationships:** `patient`
- **Indexes:** `patient_id`, `substance_code`, `status`
- **Retention Policy:** Permanent

**Provider**

- **Description:** Healthcare provider (physician, nurse, etc.)
- **Primary Key:** `provider_id` (UUID)
- **Fields:**
    - `npi` (string, unique)
    - `deanumber` (string)
    - `first_name` (string, required)
    - `last_name` (string, required)
    - `middle_name` (string)
    - `credentials` (string, e.g., MD, DO, RN)
    - `specialty` (string)
    - `license_number` (string)
    - `license_state` (string)
    - `status` (enum: active, inactive, terminated)
    - `department_id` (UUID)
    - `created_at` (datetime, required)
- **Relationships:** `orders`, `documents`, `departments`
- **Indexes:** `npi`, `last_name`, `status`
- **Retention Policy:** Permanent

**InsurancePlan**

- **Description:** Patient insurance coverage
- **Primary Key:** `insurance_id` (UUID)
- **Fields:**
    - `patient_id` (UUID, required)
    - `payer_id` (UUID)
    - `plan_name` (string)
    - `policy_number` (string)
    - `group_number` (string)
    - `member_id` (string)
    - `coverage_type` (enum: primary, secondary, tertiary)
    - `effective_date` (date)
    - `expiration_date` (date)
    - `copay` (decimal)
    - `deductible` (decimal)
    - `status` (enum: active, inactive, cancelled)
    - `created_at` (datetime, required)
- **Relationships:** `patient`, `payer`
- **Indexes:** `patient_id`, `member_id`, `status`
- **Retention Policy:** 7 years after expiration

**Charge**

- **Description:** Billable charge
- **Primary Key:** `charge_id` (UUID)
- **Fields:**
    - `encounter_id` (UUID, required)
    - `patient_id` (UUID, required)
    - `charge_type` (enum: professional, facility, pharmacy, supply)
    - `cpt_code` (string)
    - `hcpcs_code` (string)
    - `description` (string)
    - `quantity` (decimal)
    - `unit_price` (decimal)
    - `total_amount` (decimal)
    - `status` (enum: pending, billed, adjusted, written_off)
    - `claim_id` (UUID)
    - `created_at` (datetime, required)
- **Relationships:** `encounter`, `claim`
- **Indexes:** `encounter_id`, `status`, `created_at`
- **Retention Policy:** 7 years

**User**

- **Description:** System user (clinician, staff)
- **Primary Key:** `user_id` (UUID)
- **Fields:**
    - `username` (string, unique, required)
    - `email` (string)
    - `password_hash` (string, encrypted)
    - `first_name` (string, required)
    - `last_name` (string, required)
    - `provider_id` (UUID)
    - `role_id` (UUID, required)
    - `department_id` (UUID)
    - `status` (enum: active, inactive, locked)
    - `mfa_enabled` (boolean)
    - `last_login_at` (datetime)
    - `failed_login_attempts` (integer)
    - `locked_until` (datetime)
    - `created_at` (datetime, required)
    - `updated_at` (datetime, required)
- **Relationships:** `provider`, `role`, `department`
- **Indexes:** `username`, `email`, `provider_id`
- **Retention Policy:** 7 years after account closure

### Value Objects

**Address**

- **Fields:** `line1`, `line2`, `city`, `state`, `postal_code`, `country`

**Contact**

- **Fields:** `name`, `relationship`, `phone`, `email`

**Money**

- **Fields:** `amount`, `currency`

**Period**

- **Fields:** `start`, `end`

### Enum Definitions

**EncounterType:** `outpatient`, `inpatient`, `emergency`, `observation`, `ambulatory_surgery`, `behavioral_health`

**OrderStatus:** `active`, `completed`, `cancelled`, `failed`, `partially_completed`

**DocumentStatus:** `draft`, `signed`, `amended`, `final`

**AllergySeverity:** `mild`, `moderate`, `severe`, `life_threatening`

**CriticalityFlag:** `normal`, `high`, `low`, `critical`

---

## 11. Security and Access Control

### Authentication Strategy

- **Primary Mechanism:** SAML 2.0 SSO (enterprise) or username/password with MFA
- **Token Management:** JWT access tokens (15-minute TTL), refresh tokens (24-hour)
- **MFA Options:** TOTP (Google Authenticator, Authy), SMS, FIDO2/WebAuthn
- **Password Policy:**
    - Minimum 12 characters
    - Require uppercase, lowercase, number, special character
    - Password history: last 12 passwords
    - Maximum age: 90 days
    - Lockout: 5 failed attempts, 30-minute lockout

### Authorization Model

**Type:** Role-Based Access Control (RBAC) with attribute-based restrictions

**Role Hierarchy:**

1. System Administrator
2. Facility Administrator
3. Chief Medical Information Officer (CMIO)
4. Physician
5. Advanced Practice Provider (NPA/PAC)
6. Nurse
7. Pharmacist
8. Allied Health (Therapist, etc.)
9. Laboratory Staff
10. Radiology Staff
11. Billing/Coding Staff
12. HIM Staff
13. Patient Portal User

### Role-Permission Bindings

| Role           | Patient Records   | Orders               | Billing | Admin         | Reporting |
| -------------- | ----------------- | -------------------- | ------- | ------------- | --------- |
| System Admin   | Full              | Full                 | Full    | Full          | Full      |
| Facility Admin | Full              | Full                 | Full    | Partial       | Full      |
| CMIO           | Full              | Full                 | View    | Clinical Only | Full      |
| Physician      | Assigned Patients | Create/View Assigned | View    | No            | Clinical  |
| NPA            | Assigned Patients | Create/View Assigned | View    | No            | Clinical  |
| Nurse          | Assigned Patients | View/Execute         | No      | No            | Unit      |
| Pharmacist     | Meds Only         | Med Orders           | No      | No            | Pharmacy  |
| Lab Staff      | Lab Data Only     | Lab Orders           | No      | No            | Lab       |
| Billing        | Demographics      | View                 | Full    | No            | Billing   |

### Permission Definitions (20+)

| Permission               | Description                                 |
| ------------------------ | ------------------------------------------- |
| `patients:view`          | View patient demographic information        |
| `patients:full_record`   | View complete patient clinical record       |
| `patients:create`        | Create new patient record                   |
| `patients:edit`          | Edit patient information                    |
| `encounters:view`        | View encounters                             |
| `encounters:create`      | Create encounters (admission, registration) |
| `encounters:discharge`   | Process discharges                          |
| `orders:create`          | Create clinical orders                      |
| `orders:discontinue`     | Discontinue orders                          |
| `orders:view_all`        | View all orders (including other providers) |
| `documents:create`       | Create clinical documents                   |
| `documents:sign`         | Sign clinical documents                     |
| `documents:amend`        | Amend signed documents                      |
| `medications:order`      | Order medications                           |
| `medications:administer` | Document medication administration          |
| `billing:view`           | View billing information                    |
| `billing:create`         | Create charges                              |
| `billing:adjust`         | Adjust charges                              |
| `reports:view`           | View reports                                |
| `reports:export`         | Export reports                              |
| `users:manage`           | Manage user accounts                        |
| `system:configure`       | Configure system settings                   |

### Session Management

- **Timeout:** 10 minutes of inactivity for clinical users; 30 minutes for administrative
- **Auto-Lock:** Immediate screen lock on station leave (touch/keystroke detection)
- **Concurrent Sessions:** Maximum 2 concurrent sessions per user
- **Session Notification:** Alert user when new session starts

### Data Protection

- **Encryption at Rest:** AES-256 for database, file storage
- **Encryption in Transit:** TLS 1.3 for all communications
- **PII Encryption:** Field-level encryption for SSN, MRN
- **Key Management:** AWS KMS / HashiCorp Vault with automatic rotation (90 days)

### Audit Logging

**Logged Events:**

- All PHI access (view, create, update, delete)
- Authentication events (login, logout, MFA, lockout)
- Role/permission changes
- Break-glass emergency access
- Report generation and export
- Data export/portability requests
- System configuration changes

**Log Retention:** 7 years minimum; immutable storage

---

## 12. Observability and Operations

### Logging Requirements

**Log Levels:**

- ERROR: System errors, failed transactions, security events
- WARN: Potential issues, threshold breaches
- INFO: Business events, user actions
- DEBUG: Debug information (disabled in production)

**Log Format:** Structured JSON

```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "correlation_id": "abc123def456",
    "user_id": "user-123",
    "patient_id": "patient-456",
    "encounter_id": "encounter-789",
    "event": "clinical_document.viewed",
    "message": "Clinical document accessed",
    "metadata": {
        "document_id": "doc-123",
        "document_type": "progress_note"
    }
}
```

**Required Fields:**

- `timestamp` (ISO 8601 UTC)
- `level`
- `correlation_id` (trace ID)
- `user_id` (if authenticated)
- `patient_id` (if applicable)
- `event`
- `message`
- `service_name`
- `environment`

**Retention Period:** 7 years hot; 10 years warm (compressed)

### Metrics Requirements

**Application Metrics:**

1. `encounters.created.total` (counter)
2. `orders.created.total` (counter)
3. `documents.signed.total` (counter)
4. `critical_results.acknowledged` (counter)
5. `medications.administered.total` (counter)
6. `api.request.duration` (histogram)
7. `api.error.total` (counter)
8. `auth.login.success` (counter)
9. `auth.login.failure` (counter)
10. `queries.duration` (histogram)

**Infrastructure Metrics:**

- CPU utilization
- Memory usage
- Disk I/O
- Database connections
- Cache hit rate
- Queue depths

**Business Metrics:**

- Admissions per day
- Discharges per day
- Average length of stay
- Order volume
- Documentation volume

### Tracing Requirements

**Trace Sampling Rate:** 100% for errors; 5% for successful requests

**Span Requirements:**

- HTTP requests (inbound/outbound)
- Database queries
- External API calls
- Message queue operations
- Cache operations

**Correlation Strategy:** W3C Trace Context headers

### Alerting Requirements

**Critical Alerts (PagerDuty, immediate):**

1. System error rate > 1% for 5 minutes
2. Clinical availability < 99%
3. Critical result notification failure
4. HL7 interface down
5. Database connection pool exhausted
6. Security incident detected

**Warning Alerts (Slack, email):**

1. Error rate > 0.5% for 15 minutes
2. Query performance degradation
3. Queue depth exceeding threshold
4. Backup failure
5. Certificate expiration within 30 days

**Notification Channels:**

- Critical: PagerDuty (phone call), SMS
- Warning: Slack #incidents, email on-call
- Info: Daily summary email

### Dashboard Requirements

**Executive Dashboard:**

- System health status
- Key operational metrics
- Incident status
- User activity

**Clinical Operations Dashboard:**

- Admissions, discharges, transfers
- Bed availability
- OR utilization
- Emergency department metrics

**Technical Operations Dashboard:**

- Application performance
- Infrastructure health
- Integration status
- Security events

### Incident Response Procedures

**Severity Levels:**

- SEV1: Complete system outage; life-threatening; immediate response
- SEV2: Major functionality impaired; 1-hour response
- SEV3: Minor functionality affected; 4-hour response
- SEV4: Cosmetic issue; next business day

**Response Steps:**

1. Detection and triage
2. Incident declaration and team notification
3. Impact assessment
4. Containment and mitigation
5. Root cause investigation
6. Resolution and verification
7. Recovery and monitoring
8. Post-incident review (within 48 hours)

**Communication:**

- Internal: Incident bridge, Slack
- External: Status page, customer notifications

---

## 13. Acceptance Criteria

### Definition of Done (DoD)

A feature is "Done" when:

1. Code written and peer-reviewed
2. Unit tests pass (minimum 80% coverage)
3. Integration tests pass
4. Security review completed
5. HIPAA compliance verified
6. Documentation updated
7. Staging deployment verified
8. Product owner acceptance
9. No critical/high bugs open

### Minimum Viable Product (MVP) Scope

**Must Have for Launch:**

- Patient registration and master index
- Clinical documentation (progress notes)
- CPOE (medications, labs, imaging)
- Laboratory integration (HL7)
- Basic patient scheduling
- User authentication with MFA
- Audit logging
- Basic reporting

### Launch Readiness Checklist

- [ ] HIPAA security risk analysis completed
- [ ] ONC certification obtained (if applicable)
- [ ] Penetration test completed with no critical findings
- [ ] Disaster recovery drill completed
- [ ] Load testing at 2x expected peak
- [ ] HL7 interfaces tested and certified
- [ ] Monitoring and alerting configured
- [ ] Runbooks documented
- [ ] Training materials completed
- [ ] Super users trained
- [ ] Support team ready

### Performance Baselines

| Metric            | Baseline | Target |
| ----------------- | -------- | ------ |
| Chart load time   | < 5s     | < 2s   |
| Order entry       | < 10s    | < 5s   |
| Query response    | < 5s     | < 2s   |
| Report generation | < 2 min  | < 30s  |

### Security Audit Completion

- [ ] External penetration test
- [ ] Vulnerability assessment
- [ ] Access control review
- [ ] Encryption verification
- [ ] Audit log review

### Compliance Verification

- [ ] HIPAA compliance audit
- [ ] Security rule compliance
- [ ] Privacy rule compliance
- [ ] Breach notification process tested

---

## 14. Out-of-Scope

### Features Deferred to Future Phases

1. **Advanced Analytics:** Predictive modeling, population health
2. **Genomic Data Management:** Genomic sequencing results
3. **Wearable Integration:** IoT health device data
4. **Blockchain for Health Records:** Distributed ledger experiments
5. **AI-Powered Documentation:** Voice-to-chart, auto-documentation
6. **Remote Patient Monitoring:** Continuous vitals monitoring
7. **Advanced Interoperability:** Carequality, CommonWell direct participation
8. **Multi-Language Support:** Beyond English/Spanish

### Integrations Not Included (Initial Phase)

1. **Wearable Devices:** Apple Health, Fitbit
2. **Social Determinants:** Community resource connections
3. **Research Databases:** Clinical trial matching
4. **Telehealth:** Video visit platform (use third-party)

### Markets/Regions Not Supported (Initial)

1. **International:** US-focused initially (HIPAA)
2. **Canada:** Different privacy regulations
3. **Europe:** GDPR + local health regulations

### Explicitly Rejected Approaches

1. **Patient-Owned Records:** Not aligned with hospital model
2. **Blockchain Core:** Premature optimization
3. **White-Label Portal:** Use integrated patient engagement

---

## 15. Open Questions

### OQ01: Cloud vs. On-Premise Deployment

- **Question:** Should MVP support only cloud deployment or include on-premise option?
- **Impact:** High (infrastructure complexity, compliance scope)
- **Decision Deadline:** 2026-05-01
- **Proposed Options:**
    - Option A: Cloud-first, on-premise in subsequent phase (simpler MVP)
    - Option B: Both from day one (complex but market-required)
- **Decision Owner:** CTO / VP Product

### OQ02: ONC Certification Strategy

- **Question:** Pursue full ONC certification for MVP or defer?
- **Impact:** Medium (certification takes 6-12 months)
- **Decision Deadline:** 2026-04-20
- **Proposed Options:**
    - Option A: Full certification for MVP (longer time to market)
    - Option B: Target certification in Phase 2 (faster launch, limited market)
- **Decision Owner:** VP Product / Compliance Lead

### OQ03: Patient Portal: Build vs. Partner

- **Question:** Build patient portal in-house or integrate third-party?
- **Impact:** Medium (development resources vs. ongoing costs)
- **Decision Deadline:** 2026-05-15
- **Proposed Options:**
    - Option A: Build in-house (more control, more resources)
    - Option B: Partner (faster, ongoing fees)
- **Decision Owner:** VP Product

### OQ04: Data Residency Requirements

- **Question:** Support multi-region deployment for data residency?
- **Impact:** High (infrastructure complexity)
- **Decision Deadline:** 2026-05-01
- **Proposed Options:**
    - Option A: Single region (simpler)
    - Option B: Multi-region from start (complex)
- **Decision Owner:** CTO

### OQ05: Mobile App Strategy

- **Question:** Native mobile apps for clinicians in MVP?
- **Impact:** Medium (development complexity, maintenance)
- **Decision Deadline:** 2026-05-10
- **Proposed Options:**
    - Option A: Responsive web only for MVP
    - Option B: Native apps for iOS/Android
- **Decision Owner:** VP Product / CTO

---

## 16. Glossary

| Term          | Definition                                          | Context                                         | Related Terms                   |
| ------------- | --------------------------------------------------- | ----------------------------------------------- | ------------------------------- |
| HIS           | Hospital Information System                         | Primary system for hospital operations          | EMR, EHR                        |
| EMR           | Electronic Medical Record                           | Digital patient records within one organization | EHR, Clinical Documentation     |
| EHR           | Electronic Health Record                            | Interoperable digital health records            | EMR, HIE                        |
| CPOE          | Computerized Physician Order Entry                  | Electronic entry of medical orders              | Order Management                |
| LIS           | Laboratory Information System                       | System managing lab operations                  | Laboratory Integration          |
| RIS           | Radiology Information System                        | System managing radiology operations            | Imaging, PACS                   |
| PACS          | Picture Archiving and Communication System          | Medical image storage and retrieval             | Imaging, DICOM                  |
| HL7           | Health Level Seven                                  | Healthcare data exchange standard               | Interoperability, FHIR          |
| FHIR          | Fast Healthcare Interoperability Resources          | Modern healthcare data standard                 | HL7, API                        |
| DICOM         | Digital Imaging and Communications in Medicine      | Medical imaging standard                        | PACS, Imaging                   |
| NPI           | National Provider Identifier                        | US provider identifier                          | Provider, Credentialing         |
| NCPDP         | National Council for Prescription Drug Programs     | Pharmacy data standard                          | e-Prescribing                   |
| EPCS          | Electronic Prescribing of Controlled Substances     | DEA-compliant controlled substance prescribing  | e-Prescribing, DEA              |
| CCDA          | Consolidated Clinical Document Architecture         | US health document standard                     | Interoperability, HIE           |
| ICD-10        | International Classification of Diseases            | Disease coding system                           | Coding, Billing                 |
| CPT           | Current Procedural Terminology                      | Procedure coding system                         | Billing, Healthcare             |
| LOINC         | Logical Observation Identifiers Names and Codes     | Lab/test code system                            | Laboratory, Interoperability    |
| SNOMED CT     | Systematized Nomenclature of Medicine               | Clinical terminology                            | Clinical Terms                  |
| PHI           | Protected Health Information                        | Individually identifiable health information    | HIPAA, Privacy                  |
| HIPAA         | Health Insurance Portability and Accountability Act | US health privacy/security law                  | Privacy, Security               |
| HIE           | Health Information Exchange                         | Sharing health information across organizations | Interoperability                |
| MFA           | Multi-Factor Authentication                         | Authentication with multiple factors            | Security, Authentication        |
| RBAC          | Role-Based Access Control                           | Access control based on roles                   | Security, Authorization         |
| RTO           | Recovery Time Objective                             | Target recovery time after disaster             | DR, Reliability                 |
| RPO           | Recovery Point Objective                            | Target data loss tolerance after disaster       | DR, Reliability                 |
| EHR Incentive | Meaningful Use / Promoting Interoperability         | CMS EHR incentive programs                      | ONC, Reporting                  |
| ONC           | Office of the National Coordinator                  | US health IT coordination office                | Certification, Interoperability |
| CLIA          | Clinical Laboratory Improvement Amendments          | Lab regulations                                 | Laboratory, Compliance          |
| Stark Law     | Physician Self-Referral Law                         | Prohibits certain referrals                     | Compliance, Billing             |

_End of Brief_
