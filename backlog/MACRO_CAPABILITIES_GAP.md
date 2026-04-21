# Macro Capabilities GAP Analysis

# Midicoder CE v1.0.0

**Version:** 1.0.0  
**Created:** 2026-04-20  
**Purpose:** Liệt kê đầy đủ các macro capabilities còn thiếu để cover 100 industries

---

## Tóm Tắt

| Layer                          | Current | Required    | GAP         | Status    |
| ------------------------------ | ------- | ----------- | ----------- | --------- |
| Base Macros                    | 50      | 50          | 0           | ✅ 100%   |
| Domain Macros (Layer 2)        | 53      | ~80         | ~27         | 🔄 66%    |
| Industry Macros (Layer 3)      | 0       | 50-100      | 50-100      | ❌ 0%     |
| **Total**                      | **103** | **180-230** | **77-127**  | 🔄 57%    |

**Update 2026-04-20:** Layer 2 Phase 1-3 complete with 53 macros covering 12 industries. 8 industries remaining (~27 macros).

---

## LAYER 2: Domain Macros cho 20 Priority Industries (Cần Thêm 50)

### Ecommerce D2C (4 macros)

| Macro ID              | Name                | Description                                    | Expands To                                                                                                                                  | Obligations                                                       |
| --------------------- | ------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `apply_promotion`     | Apply Promotion     | Áp dụng promotion/discount vào cart            | `validate_input`, `load_entity`, `update_record`, `publish_event`                                                                           | `audit_log_required`                                              |
| `process_refund`      | Process Refund      | Xử lý refund cho order                         | `authorize_permission`, `load_entity`, `begin_transaction`, `update_record`, `call_external_service`, `publish_event`, `commit_transaction` | `transaction_required`, `audit_log_required`, `pci_dss_compliant` |
| `manage_subscription` | Manage Subscription | Quản lý subscription (activate, pause, cancel) | `authorize_permission`, `state_machine_transition`, `send_notification`                                                                     | `audit_log_required`                                              |
| `recommend_products`  | Recommend Products  | Generate product recommendations               | `query_records`, `call_external_service`, `record_metric`                                                                                   | `tenant_filter_required`                                          |

### Marketplace B2C (5 macros)

| Macro ID              | Name                | Description                       | Expands To                                                                  | Obligations                                   |
| --------------------- | ------------------- | --------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------- |
| `onboard_seller`      | Onboard Seller      | Seller onboarding với KYC         | `validate_input`, `call_external_service`, `create_record`, `publish_event` | `kyc_verified`, `audit_log_required`          |
| `hold_escrow_payment` | Hold Escrow Payment | Giữ tiền trong escrow             | `begin_transaction`, `create_record`, `update_record`, `commit_transaction` | `double_entry_balanced`, `audit_log_required` |
| `split_payment`       | Split Payment       | Chia payment giữa seller/platform | `call_external_service`, `create_record`, `publish_event`                   | `double_entry_balanced`, `pci_dss_compliant`  |
| `resolve_dispute`     | Resolve Dispute     | Giải quyết dispute buyer-seller   | `approval_workflow`, `update_record`, `send_notification`                   | `audit_log_required`                          |
| `rate_review`         | Rate and Review     | Đánh giá và review                | `authorize_permission`, `create_record`, `publish_event`                    | `audit_log_required`                          |

### Marketplace B2B (4 macros)

| Macro ID              | Name                   | Description                    | Expands To                                                                        | Obligations              |
| --------------------- | ---------------------- | ------------------------------ | --------------------------------------------------------------------------------- | ------------------------ |
| `create_rfp`          | Create RFP             | Tạo Request for Proposal       | `authorize_permission`, `create_record`, `send_notification`, `publish_event`     | `audit_log_required`     |
| `manage_credit_terms` | Manage Credit Terms    | Quản lý credit terms cho buyer | `authorize_permission`, `create_record`, `update_record`, `call_external_service` | `audit_log_required`     |
| `bulk_pricing`        | Apply Bulk Pricing     | Áp dụng bulk pricing           | `validate_input`, `update_record`, `publish_event`                                | `tenant_filter_required` |
| `po_integration`      | Process Purchase Order | Xử lý PO từ buyer              | `validate_input`, `create_record`, `call_external_service`                        | `audit_log_required`     |

### Food Delivery (4 macros)

| Macro ID                   | Name                     | Description                     | Expands To                                                                    | Obligations              |
| -------------------------- | ------------------------ | ------------------------------- | ----------------------------------------------------------------------------- | ------------------------ |
| `assign_delivery_driver`   | Assign Delivery Driver   | Phân công driver cho order      | `authorize_permission`, `query_records`, `update_record`, `send_notification` | `audit_log_required`     |
| `calculate_delivery_route` | Calculate Delivery Route | Tính toán delivery route tối ưu | `call_external_service`, `update_record`                                      | `tenant_filter_required` |
| `track_realtime_location`  | Track Realtime Location  | Track driver location realtime  | `update_record`, `publish_event`, `record_metric`                             | `tenant_filter_required` |
| `process_tip`              | Process Tip              | Xử lý tip cho driver            | `create_record`, `publish_event`                                              | `audit_log_required`     |

### Warehouse Management (5 macros)

| Macro ID              | Name                | Description            | Expands To                                                                                                     | Obligations                                  |
| --------------------- | ------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `receive_inventory`   | Receive Inventory   | Nhận hàng vào kho      | `validate_input`, `begin_transaction`, `update_record`, `create_record`, `publish_event`, `commit_transaction` | `transaction_required`, `audit_log_required` |
| `pick_pack_ship`      | Pick Pack Ship      | Pick, pack, ship order | `authorize_permission`, `begin_transaction`, `update_record`, `publish_event`, `commit_transaction`            | `transaction_required`, `audit_log_required` |
| `cycle_count`         | Cycle Count         | Đếm hàng theo chu kỳ   | `authorize_permission`, `query_records`, `update_record`, `write_audit_log`                                    | `audit_log_required`                         |
| `bin_transfer`        | Bin Transfer        | Chuyển hàng giữa bins  | `begin_transaction`, `update_record`, `commit_transaction`                                                     | `transaction_required`, `audit_log_required` |
| `manage_bin_location` | Manage Bin Location | Quản lý bin locations  | `create_record`, `update_record`, `delete_record`                                                              | `audit_log_required`                         |

### Procurement SRM (5 macros)

| Macro ID              | Name                | Description                 | Expands To                                                                               | Obligations                                         |
| --------------------- | ------------------- | --------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `create_rfq`          | Create RFQ          | Tạo Request for Quotation   | `authorize_permission`, `create_record`, `send_notification`, `publish_event`            | `audit_log_required`                                |
| `evaluate_vendor`     | Evaluate Vendor     | Đánh giá vendor performance | `query_records`, `aggregate_query`, `create_record`, `publish_event`                     | `audit_log_required`                                |
| `manage_contract`     | Manage Contract     | Quản lý vendor contract     | `authorize_permission`, `create_record`, `state_machine_transition`, `send_notification` | `audit_log_required`, `immutable_evidence_required` |
| `spend_analysis`      | Spend Analysis      | Phân tích spend             | `aggregate_query`, `create_record`, `export_query`                                       | `tenant_filter_required`                            |
| `supplier_onboarding` | Supplier Onboarding | Onboarding supplier mới     | `validate_input`, `create_record`, `approval_workflow`, `send_notification`              | `audit_log_required`                                |

### CRM Platform (5 macros)

| Macro ID              | Name                | Description                         | Expands To                                                                           | Obligations          |
| --------------------- | ------------------- | ----------------------------------- | ------------------------------------------------------------------------------------ | -------------------- |
| `create_lead`         | Create Lead         | Tạo lead mới                        | `validate_input`, `create_record`, `publish_event`, `send_notification`              | `audit_log_required` |
| `convert_opportunity` | Convert Opportunity | Convert lead → opportunity          | `authorize_permission`, `state_machine_transition`, `create_record`, `publish_event` | `audit_log_required` |
| `log_activity`        | Log Activity        | Log activity (call, email, meeting) | `create_record`, `publish_event`                                                     | `audit_log_required` |
| `run_campaign`        | Run Campaign        | Chạy marketing campaign             | `authorize_permission`, `create_record`, `send_notification`, `record_metric`        | `audit_log_required` |
| `case_escalation`     | Case Escalation     | Escalate support case               | `state_machine_transition`, `send_notification`, `assign_ticket`                     | `audit_log_required` |

### ERP Finance (5 macros)

| Macro ID                     | Name                       | Description                    | Expands To                                                                                                            | Obligations                                                           |
| ---------------------------- | -------------------------- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `post_journal_entry`         | Post Journal Entry         | Post journal entry vào GL      | `authorize_permission`, `validate_input`, `begin_transaction`, `create_record`, `publish_event`, `commit_transaction` | `transaction_required`, `double_entry_balanced`, `audit_log_required` |
| `reconcile_accounts`         | Reconcile Accounts         | Reconcile accounts             | `authorize_permission`, `query_records`, `update_record`, `write_audit_log`                                           | `audit_log_required`, `double_entry_balanced`                         |
| `close_period`               | Close Period               | Close accounting period        | `authorize_permission`, `state_machine_transition`, `aggregate_query`, `publish_event`                                | `audit_log_required`, `immutable_evidence_required`                   |
| `consolidate_entities`       | Consolidate Entities       | Consolidate financial entities | `aggregate_query`, `create_record`, `financial_reporting`                                                             | `double_entry_balanced`, `audit_log_required`                         |
| `fixed_asset_capitalization` | Fixed Asset Capitalization | Capitalize fixed asset         | `create_record`, `create_ledger_entry`, `publish_event`                                                               | `audit_log_required`                                                  |

### ITSM Helpdesk (4 macros)

| Macro ID             | Name               | Description                    | Expands To                                                                           | Obligations          |
| -------------------- | ------------------ | ------------------------------ | ------------------------------------------------------------------------------------ | -------------------- |
| `create_ticket`      | Create Ticket      | Tạo ticket mới                 | `validate_input`, `create_record`, `send_notification`, `publish_event`              | `audit_log_required` |
| `approve_change`     | Approve Change     | Approve change request         | `approval_workflow`, `state_machine_transition`, `send_notification`                 | `audit_log_required` |
| `publish_kb_article` | Publish KB Article | Publish knowledge base article | `authorize_permission`, `create_record`, `state_machine_transition`, `publish_event` | `audit_log_required` |
| `escalate_ticket`    | Escalate Ticket    | Escalate ticket đến manager    | `state_machine_transition`, `send_notification`, `write_audit_log`                   | `sla_breach_check`   |

### Payroll Benefits (4 macros)

| Macro ID              | Name                | Description                  | Expands To                                                                                                                       | Obligations                                                              |
| --------------------- | ------------------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `process_payroll_run` | Process Payroll Run | Chạy payroll run             | `authorize_permission`, `begin_transaction`, `create_record`, `call_external_service`, `send_notification`, `commit_transaction` | `transaction_required`, `audit_log_required`, `tax_calculation_required` |
| `file_tax_returns`    | File Tax Returns    | File tax returns             | `authorize_permission`, `call_external_service`, `create_record`, `write_audit_log`                                              | `audit_log_required`, `immutable_evidence_required`                      |
| `enroll_benefits`     | Enroll Benefits     | Enroll employee vào benefits | `validate_input`, `create_record`, `send_notification`, `publish_event`                                                          | `audit_log_required`                                                     |
| `process_garnishment` | Process Garnishment | Xử lý wage garnishment       | `authorize_permission`, `create_record`, `update_record`, `write_audit_log`                                                      | `audit_log_required`, `immutable_evidence_required`                      |

### Healthcare - Hospital IS (4 macros)

| Macro ID                 | Name                   | Description                 | Expands To                                                                                                 | Obligations                                                   |
| ------------------------ | ---------------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `admit_patient`          | Admit Patient          | Admit patient vào bệnh viện | `authorize_permission`, `validate_input`, `create_record`, `state_machine_transition`, `send_notification` | `audit_log_required`, `hipaa_encryption`                      |
| `enter_medical_order`    | Enter Medical Order    | Nhập medical order          | `authorize_permission`, `validate_input`, `create_record`, `call_external_service`, `publish_event`        | `audit_log_required`, `hipaa_encryption`                      |
| `document_clinical_note` | Document Clinical Note | Ghi clinical note           | `authorize_permission`, `create_record`, `write_audit_log`                                                 | `audit_log_required`, `hipaa_encryption`, `phi_access_logged` |
| `manage_bed`             | Manage Bed             | Quản lý bed assignment      | `state_machine_transition`, `update_record`, `publish_event`                                               | `audit_log_required`                                          |

### Exchange Trading (4 macros)

| Macro ID             | Name               | Description                  | Expands To                                                                                                     | Obligations                                                           |
| -------------------- | ------------------ | ---------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `match_orders`       | Match Orders       | Match buy/sell orders        | `validate_input`, `begin_transaction`, `create_record`, `update_record`, `publish_event`, `commit_transaction` | `transaction_required`, `double_entry_balanced`, `audit_log_required` |
| `clear_settlement`   | Clear Settlement   | Clear và settlement trade    | `begin_transaction`, `create_record`, `update_record`, `commit_transaction`                                    | `double_entry_balanced`, `audit_log_required`                         |
| `calculate_margin`   | Calculate Margin   | Tính toán margin requirement | `aggregate_query`, `update_record`, `publish_event`                                                            | `audit_log_required`                                                  |
| `surveillance_check` | Surveillance Check | Kiểm tra market manipulation | `query_records`, `aggregate_query`, `create_record`, `write_audit_log`                                         | `audit_log_required`, `immutable_evidence_required`                   |

---

## LAYER 3: Industry Macros cho 80 Industries Còn Lại (Cần Thêm 50-100)

### Travel & Hospitality (DP03) - 12 macros

| Macro ID                    | Name                      | Industries Covered             |
| --------------------------- | ------------------------- | ------------------------------ |
| `book_reservation`          | Book Reservation          | Hotel, Flight, Vacation Rental |
| `manage_tour`               | Manage Tour               | Hotel, Vacation Rental         |
| `process_checkin`           | Process Checkin           | Hotel, Vacation Rental         |
| `manage_itinerary`          | Manage Itinerary          | Flight, Rail/Bus               |
| `calculate_dynamic_pricing` | Calculate Dynamic Pricing | Hotel, Flight, Vacation Rental |
| `process_group_booking`     | Process Group Booking     | Hotel, Vacation Rental         |
| `manage_loyalty_points`     | Manage Loyalty Points     | Hotel, Flight, Vacation Rental |
| `handle_flight_change`      | Handle Flight Change      | Flight                         |
| `process_baggage_claim`     | Process Baggage Claim     | Flight                         |
| `manage_seat_selection`     | Manage Seat Selection     | Flight, Rail/Bus               |
| `process_travel_insurance`  | Process Travel Insurance  | Flight, Vacation Rental        |
| `manage_corporate_travel`   | Manage Corporate Travel   | Flight, Hotel                  |

### Manufacturing & Industrial (DP05) - 12 macros

| Macro ID                     | Name                       | Industries Covered                      |
| ---------------------------- | -------------------------- | --------------------------------------- |
| `create_production_order`    | Create Production Order    | Discrete, Process, Garment, Electronics |
| `track_quality`              | Track Quality              | All Manufacturing                       |
| `manage_bom`                 | Manage BOM                 | Discrete, Electronics                   |
| `schedule_maintenance`       | Schedule Maintenance       | All Manufacturing                       |
| `track_material_consumption` | Track Material Consumption | All Manufacturing                       |
| `manage_work_in_progress`    | Manage WIP                 | All Manufacturing                       |
| `generate_coa`               | Generate COA               | Pharma Manufacturing                    |
| `handle_non_conformance`     | Handle Non-Conformance     | All Manufacturing                       |
| `manage_capacity_planning`   | Manage Capacity Planning   | All Manufacturing                       |
| `track_equipment_downtime`   | Track Equipment Downtime   | All Manufacturing                       |
| `process_scrap`              | Process Scrap              | All Manufacturing                       |
| `manage_batch_tracking`      | Manage Batch Tracking      | Process, Pharma Manufacturing           |

### Real Estate & Facility (DP06) - 10 macros

| Macro ID                       | Name                         | Industries Covered                     |
| ------------------------------ | ---------------------------- | -------------------------------------- |
| `list_property`                | List Property                | Real Estate Brokerage                  |
| `schedule_showing`             | Schedule Showing             | Real Estate Brokerage                  |
| `close_deal`                   | Close Deal                   | Real Estate Brokerage                  |
| `manage_lease`                 | Manage Lease                 | Property Management, Building/Facility |
| `process_rent_collection`      | Process Rent Collection      | Property Management                    |
| `schedule_maintenance_request` | Schedule Maintenance Request | Property Management, Building/Facility |
| `manage_utility_billing`       | Manage Utility Billing       | Building/Facility                      |
| `track_square_footage`         | Track Square Footage         | Property Management                    |
| `manage_vehicle_inventory`     | Manage Vehicle Inventory     | Auto Dealership, Car Rental            |
| `schedule_service_appointment` | Schedule Service Appointment | Auto Service & Repair                  |

### Utilities & Energy (DP07) - 8 macros

| Macro ID                      | Name                        | Industries Covered              |
| ----------------------------- | --------------------------- | ------------------------------- |
| `read_meter`                  | Read Meter                  | Electricity, Water, Gas Utility |
| `process_outage`              | Process Outage              | Electricity, Water, Gas Utility |
| `manage_billing_cycle`        | Manage Billing Cycle        | Electricity, Water, Gas Utility |
| `track_consumption`           | Track Consumption           | Electricity, Water, Gas Utility |
| `manage_service_connection`   | Manage Service Connection   | Electricity, Water, Gas Utility |
| `process_payment_arrangement` | Process Payment Arrangement | Electricity, Water, Gas Utility |
| `track_renewable_credits`     | Track Renewable Credits     | Renewable Energy Ops            |
| `manage_grid_maintenance`     | Manage Grid Maintenance     | Electricity Utility             |

### Agriculture & Food (DP08) - 8 macros

| Macro ID                       | Name                         | Industries Covered      |
| ------------------------------ | ---------------------------- | ----------------------- |
| `track_crop_cycle`             | Track Crop Cycle             | Crop Farming            |
| `manage_inventory_farm`        | Manage Inventory             | Crop, Livestock Farming |
| `compliance_safety_agri`       | Compliance Safety            | Crop, Livestock Farming |
| `track_animal_health`          | Track Animal Health          | Livestock Farming       |
| `manage_feeding_schedule`      | Manage Feeding Schedule      | Livestock Farming       |
| `track_harvest_yield`          | Track Harvest Yield          | Crop Farming            |
| `manage_organic_certification` | Manage Organic Certification | Crop, Livestock Farming |
| `track_food_safety`            | Track Food Safety            | Food Processing         |

### Financial Services (DP11-16) - 15 macros

| Macro ID                      | Name                                  | Industries Covered               |
| ----------------------------- | ------------------------------------- | -------------------------------- |
| `open_account`                | Open Account                          | Retail Banking                   |
| `process_loan_app`            | Process Loan Application              | Lending & Credit                 |
| `detect_fraud`                | Detect Fraud                          | Retail Banking, Payments & Cards |
| `generate_statements`         | Generate Statements                   | Retail Banking                   |
| `manage_investment_portfolio` | Manage Investment Portfolio           | Capital Markets & Wealth         |
| `process_trade_settlement`    | Process Trade Settlement              | Capital Markets & Wealth         |
| `calculate_nav`               | Calculate NAV                         | Capital Markets & Wealth         |
| `manage_risk_exposure`        | Manage Risk Exposure                  | All Financial Services           |
| `file_sar`                    | File SAR (Suspicious Activity Report) | All Financial Services           |
| `manage_collateral`           | Manage Collateral                     | Lending & Credit                 |
| `process_claim`               | Process Insurance Claim               | Insurance                        |
| `manage_policy`               | Manage Insurance Policy               | Insurance                        |
| `calculate_premium`           | Calculate Premium                     | Insurance                        |
| `handle_reinsurance`          | Handle Reinsurance                    | Insurance                        |
| `process_mortgage_refinance`  | Process Mortgage Refinance            | Lending & Credit                 |

### HR & Education (DP18-21) - 10 macros

| Macro ID                     | Name                       | Industries Covered           |
| ---------------------------- | -------------------------- | ---------------------------- |
| `manage_skills_inventory`    | Manage Skills Inventory    | Workforce Management         |
| `schedule_training`          | Schedule Training          | Vocational Training          |
| `track_compliance_training`  | Track Compliance Training  | All HR/Education             |
| `manage_academic_transcript` | Manage Academic Transcript | K-12, University             |
| `process_financial_aid`      | Process Financial Aid      | University                   |
| `manage_research_grant`      | Manage Research Grant      | University                   |
| `track_learner_progress`     | Track Learner Progress     | Vocational Training          |
| `manage_certification`       | Manage Certification       | Vocational Training          |
| `handle_student_enrollment`  | Handle Student Enrollment  | K-12, University, Vocational |
| `process_grade_submission`   | Process Grade Submission   | K-12, University             |

### Media & Entertainment (DP23-24) - 8 macros

| Macro ID                    | Name                      | Industries Covered          |
| --------------------------- | ------------------------- | --------------------------- |
| `manage_content_rights`     | Manage Content Rights     | Media Streaming, Publishing |
| `track_content_performance` | Track Content Performance | Media Streaming             |
| `manage_subscription_tier`  | Manage Subscription Tier  | Media Streaming             |
| `process_content_licensing` | Process Content Licensing | Publishing                  |
| `track_ad_impressions`      | Track Ad Impressions      | Media Streaming, Publishing |
| `manage_creator_payouts`    | Manage Creator Payouts    | Media Streaming             |
| `process_copyright_claim`   | Process Copyright Claim   | Media Streaming             |
| `manage_editorial_calendar` | Manage Editorial Calendar | Publishing                  |

### Public Sector (DP25-26) - 10 macros

| Macro ID                      | Name                        | Industries Covered     |
| ----------------------------- | --------------------------- | ---------------------- |
| `process_license_application` | Process License Application | Government Services    |
| `manage_public_records`       | Manage Public Records       | Government Services    |
| `track_case_investigation`    | Track Case Investigation    | Law Enforcement        |
| `process_permit`              | Process Permit              | Government Services    |
| `manage_benefit_eligibility`  | Manage Benefit Eligibility  | Social Services        |
| `track_emergency_response`    | Track Emergency Response    | Emergency Services     |
| `manage_public_contract`      | Manage Public Contract      | Government Procurement |
| `process_tax_assessment`      | Process Tax Assessment      | Tax Authority          |
| `track_election_voter`        | Track Election Voter        | Election Management    |
| `manage_grant_disbursement`   | Manage Grant Disbursement   | Government Grants      |

---

## Tổng Kết GAPs

### Current Status (2026-04-20)

| Category                  | Implemented | Remaining | % Complete |
| ------------------------- | ----------- | --------- | ---------- |
| Ecommerce D2C             | 4/4         | 0         | ✅ 100%    |
| Marketplace B2C           | 5/5         | 0         | ✅ 100%    |
| Marketplace B2B           | 4/4         | 0         | ✅ 100%    |
| Food Delivery             | 4/4         | 0         | ✅ 100%    |
| Warehouse Management      | 5/13        | 8         | 🔄 38%     |
| Procurement SRM           | 5/10        | 5         | 🔄 50%     |
| CRM Platform              | 5/8         | 3         | 🔄 63%     |
| ERP Finance               | 5/11        | 6         | 🔄 45%     |
| ITSM Helpdesk             | 4/6         | 2         | 🔄 67%     |
| Payroll Benefits          | 4/7         | 3         | 🔄 57%     |
| Exchange Trading          | 4/9         | 5         | 🔄 44%     |
| Healthcare Hospital IS    | 4/8         | 4         | 🔄 50%     |
| Retail Banking            | 0/8         | 8         | ❌ 0%      |
| Last-mile Delivery        | 0/5         | 5         | ❌ 0%      |
| Omni-channel Retail       | 0/6         | 6         | ❌ 0%      |
| Omnichannel               | 0/4         | 4         | ❌ 0%      |
| **Subtotal (16/20)**      | **53/99**   | **46**    | **53%**    |

### Priority by Industry Coverage

| Priority | Layer                                    | Count | Status          | Note                    |
| -------- | ---------------------------------------- | ----- | --------------- | ----------------------- |
| P0       | Layer 2 - Phase 1-3 (DONE)               | 53    | ✅ COMPLETE     | 12 industries done      |
| P0       | Layer 2 - Retail Banking                 | 8     | ❌ CRITICAL     | 4 macros missing        |
| P0       | Layer 2 - Last-mile Delivery             | 5     | ❌ CRITICAL     | Industry not covered    |
| P1       | Layer 2 - Warehouse extended             | 8     | 🔄 IN PROGRESS  | Expand current 5 macros |
| P1       | Layer 2 - ERP/Procurement extended       | 11    | 🔄 BACKLOG      | Complex workflows       |
| P2       | Layer 3 - Travel, Manufacturing, Finance | 45    | 📋 BACKLOG      | Epic E16                |
| P3       | Layer 3 - Other Industries               | 37    | 📋 BACKLOG      | Epic E16                |

### Implementation Roadmap

| Phase   | Timeline  | Macros | Status   | Industries Covered                             |
| ------- | --------- | ------ | -------- | ---------------------------------------------- |
| Phase 1 | Month 1   | 8      | ✅ DONE  | Ecommerce D2C, Healthcare (4+4)                |
| Phase 2 | Month 1   | 41     | ✅ DONE  | Marketplace, Food, Warehouse, Procurement, CRM, ERP, ITSM, Payroll, Exchange |
| Phase 3 | Month 2   | 8      | ❌ TODO  | Retail Banking (CRITICAL GAP)                  |
| Phase 4 | Month 2   | 14     | 🔄 TODO  | Last-mile, Omni-channel, Warehouse extended    |
| Phase 5 | Month 3   | 24     | 📋 TODO  | Remaining Layer 2 + extended macros            |
| Phase 6 | Month 3-6 | 82     | 📋 TODO  | Layer 3 - 80 industries (Epic E16)             |

---

## Notes

1. **Số N (Core Capabilities) = 17** - KHÔNG CẦN THAY ĐỔI
    - Đã đạt điểm hội tụ tối ưu
    - Tất cả macros có thể expand về 17 primitives

2. **Số M (Macros) = 150-200** - CẦN MỞ RỘNG
    - 50 base macros (hiện có)
    - 50 domain macros cho 20 priority industries
    - 50-100 industry macros cho 80 industries còn lại

3. **Mỗi macro PHẢI:**
    - Expand về 17 core capabilities
    - Có params_schema đầy đủ
    - Có default_obligations rõ ràng
    - Có docstrings tiếng Việt

4. **Domain Packs (DP01-DP26) sẽ map vào:**
    - DP01: Ecommerce macros
    - DP11-DP16: Financial Services macros
    - DP09-DP10: Healthcare macros
    - etc.

---

_Document Version: 1.0.0_  
_Last Updated: 2026-04-20_  
_Aligned With: backlog/requirement.md, INDUSTRY_100_SYSTEM_MAP.md_
