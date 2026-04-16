# SkillsPro - Vocational Training Platform - Universal-Fully Brief

## Document Information

| Field         | Value                   |
| ------------- | ----------------------- |
| Document Type | Universal-Fully Brief   |
| Version       | 1.0.0                   |
| Status        | Draft                   |
| Created       | 2024-01-15              |
| Last Updated  | 2024-01-15              |
| Author        | Midicoder Industry Team |
| Reviewers     | Industry Domain Experts |

## Table of Contents

1. [Product Context](#1-product-context)
2. [Business Goals and KPIs](#2-business-goals-and-kpis)
3. [User Personas and Roles](#3-user-personas-and-roles)
4. [Core User Journeys](#4-core-user-journeys)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Domain Rules and Invariants](#7-domain-rules-and-invariants)
8. [Compliance and Regulatory Constraints](#8-compliance-and-regulatory-constraints)
9. [Integration Requirements](#9-integration-requirements)
10. [Data Model Expectations](#10-data-model-expectations)
11. [Security and Access Control](#11-security-and-access-control)
12. [Observability and Operations](#12-observability-and-operations)
13. [Acceptance Criteria](#13-acceptance-criteria)
14. [Out-of-Scope](#14-out-of-scope)
15. [Open Questions](#15-open-questions)
16. [Glossary](#16-glossary)

---

## 1. Product Context

### 1.1 Product Name

**SkillsPro - Vocational Training Management Platform**

### 1.2 Product Type

Vocational and Technical Training Management Platform for trade schools, technical colleges, and corporate training centers.

### 1.3 Target Market

#### 1.3.1 Geographic Markets

| Region               | Priority | Market Size | Growth Rate |
| -------------------- | -------- | ----------- | ----------- |
| North America        | P0       | $12B        | 5.2%        |
| Europe               | P0       | $8B         | 4.8%        |
| Asia-Pacific         | P1       | $15B        | 8.5%        |
| Latin America        | P2       | $3B         | 6.2%        |
| Middle East & Africa | P2       | $2B         | 7.1%        |

#### 1.3.2 Customer Segments

| Segment                 | Description                                    | Annual Revenue Potential | Sales Cycle |
| ----------------------- | ---------------------------------------------- | ------------------------ | ----------- |
| Trade Schools           | Construction, automotive, electrical, plumbing | $50K - $500K             | 3-6 months  |
| Technical Colleges      | Multi-program institutions, 500+ students      | $100K - $1M              | 6-12 months |
| Corporate Training      | Enterprise skills development centers          | $75K - $750K             | 2-4 months  |
| Apprenticeship Programs | Union/trade organization programs              | $25K - $250K             | 4-8 months  |
| Government Training     | Public workforce development                   | $50K - $500K             | 6-18 months |

#### 1.3.3 Program Types Supported

| Category       | Programs                              | Certifications                 |
| -------------- | ------------------------------------- | ------------------------------ |
| Construction   | Carpentry, masonry, HVAC, electrical  | OSHA, NCCER, licensed trades   |
| Manufacturing  | CNC, welding, machining, robotics     | AWS, NCCER, manufacturer certs |
| Healthcare     | CNA, medical assistant, pharmacy tech | State licenses, NHA, NCCT      |
| Technology     | IT support, networking, cybersecurity | CompTIA, Cisco, Microsoft      |
| Automotive     | Collision repair, diesel, EV systems  | ASE, manufacturer certified    |
| Hospitality    | Culinary, hotel management            | ServSafe, AHLEI                |
| Business       | Office admin, bookkeeping             | NHA, QuickBooks certified      |
| Transportation | CDL training, logistics               | State CDL, DOT certifications  |

### 1.4 Problem Statement

Vocational training organizations face unique and critical challenges that traditional LMS and SIS platforms do not address:

#### 1.4.1 Program Management Challenges

1. **Diverse Curriculum Structures**: Programs vary widely in duration (8 weeks to 2 years), delivery methods (classroom, lab, online, apprenticeship), and certification requirements.

2. **Prerequisite Complexity**: Skills build progressively with strict dependencies; students cannot access advanced equipment or certifications without demonstrating foundational competency.

3. **Schedule Management**: Coordinating classroom instruction, lab time, externships, and certification exam windows across multiple programs creates complex scheduling demands.

4. **Accreditation Documentation**: Each program may have different accreditation bodies with distinct reporting requirements and documentation standards.

#### 1.4.2 Hands-On Training Challenges

1. **Equipment Tracking**: Expensive tools and equipment ($50K+ labs) must be tracked for utilization, maintenance, and student access permissions.

2. **Lab Capacity Management**: Labs have strict capacity limits for safety; overbooking creates liability and disrupts learning.

3. **Skills Assessment**: Practical skills require observational evaluation, rubric-based scoring, and competency verification that differs from academic grading.

4. **Safety Compliance**: OSHA and industry-specific safety requirements mandate tracking training completion, incident reporting, and equipment certifications.

5. **Material Costs**: Consumables (welding rods, automotive parts, culinary ingredients) must be budgeted, tracked, and charged appropriately.

#### 1.4.3 Industry Certification Challenges

1. **Multiple Certification Bodies**: Each industry has different certification organizations (AWS for welding, CompTIA for IT, NHA for healthcare) with varying processes.

2. **Exam Scheduling**: External proctored exams require coordination with certification bodies, facility preparation, and candidate eligibility verification.

3. **Credential Expiration**: Certifications expire and require renewal tracking for both students and instructors.

4. **Cost Management**: Exam fees ($150-$500 per exam) must be tracked, billed, and sometimes subsidized.

#### 1.4.4 Employer Partnership Challenges

1. **Job Placement Tracking**: Employers expect detailed graduate outcome reporting; schools need placement data for accreditation and marketing.

2. **Apprenticeship Coordination**: Managing apprenticeship placements requires employer onboarding, schedule coordination, and progress monitoring.

3. **Feedback Collection**: Employer satisfaction data drives program improvements but is often collected inconsistently.

4. **Hiring Pipeline**: Employers want direct access to qualified candidates; schools need efficient matching systems.

#### 1.4.5 Financial Challenges

1. **Payment Plan Management**: Students often need installment plans, financial aid processing, and scholarship tracking.

2. **Cost Transparency**: Hands-on programs have variable costs (materials, certification fees) that must be clearly communicated and billed.

3. **Refund Policies**: Complex refund rules based on withdrawal timing, state regulations, and financial aid status.

4. **Revenue Recognition**: Accreditation and accounting requirements for multi-term programs and payment plans.

### 1.5 Solution Overview

SkillsPro provides a comprehensive platform specifically designed for vocational training:

#### 1.5.1 Core Capabilities

| Capability                 | Description                                      | Value                              |
| -------------------------- | ------------------------------------------------ | ---------------------------------- |
| Program Management         | Curriculum design, prerequisites, requirements   | Standardize program delivery       |
| Enrollment Management      | Applications, admissions, waitlists, orientation | Optimize enrollment operations     |
| Student Progress Tracking  | Skills assessments, grades, attendance           | Monitor individual success         |
| Lab & Equipment Management | Scheduling, checkout, maintenance                | Maximize resource utilization      |
| Certification Management   | Exam scheduling, results, credentials            | Streamline certification processes |
| Job Placement Services     | Employer partnerships, job board, tracking       | Improve employment outcomes        |
| Instructor Management      | Credentials, assignments, evaluations            | Ensure teaching quality            |
| Financial Management       | Billing, payment plans, financial aid            | Improve cash flow                  |

#### 1.5.2 Differentiators

1. **Skills-Based Tracking**: Unlike academic LMS, SkillsPro tracks practical competencies with proficiency levels and assessment rubrics.

2. **Hands-On Training Features**: Native support for lab scheduling, equipment management, and safety compliance.

3. **Certification Integration**: Direct integrations with major certification bodies for exam scheduling and credential verification.

4. **Employer Ecosystem**: Built-in job board, employer portal, and placement tracking specifically for vocational outcomes.

5. **Accreditation Reporting**: Pre-built reports and data exports for common vocational accreditation requirements.

#### 1.5.3 Platform Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                            │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Web Portal    │   Mobile App    │   Employer Portal       │
│  (Students,     │  (iOS, Android) │  (Job Postings,         │
│   Staff)        │                 │   Candidate Reviews)    │
└─────────────────┴─────────────────┴─────────────────────────┘
                        │
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway                             │
│              (Authentication, Rate Limiting)                │
└─────────────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────────────┐
│                   Microservices Layer                       │
├──────────────┬──────────────┬──────────────┬───────────────┤
│ Enrollment   │ Learning     │ Certifications│ Placement    │
│ Service      │ Service      │ Service      │ Service      │
├──────────────┼──────────────┼──────────────┼───────────────┤
│ Equipment    │ Assessment   │ Financial    │ Reporting    │
│ Service      │ Service      │ Service      │ Service      │
└──────────────┴──────────────┴──────────────┴───────────────┘
                        │
┌─────────────────────────────────────────────────────────────┐
│                   Data & Integration Layer                  │
├──────────────┬──────────────┬──────────────┬───────────────┤
│   Primary    │  Analytics   │  External    │   Document    │
│   Database   │   Warehouse  │   APIs       │   Storage     │
└──────────────┴──────────────┴──────────────┴───────────────┘
```

#### 1.5.4 Deployment Options

| Option          | Description                        | Target Customer        |
| --------------- | ---------------------------------- | ---------------------- |
| Cloud SaaS      | Multi-tenant, fully managed        | Most customers         |
| Dedicated Cloud | Single-tenant cloud instance       | Large institutions     |
| Hybrid          | Core cloud, sensitive data on-prem | Government, healthcare |
| On-Premise      | Full on-premises deployment        | Highly regulated       |

---

## 2. Business Goals and KPIs

### 2.1 Strategic Goals

#### 2.1.1 Mission Alignment

| Goal                      | Description                             | Target | Measurement           |
| ------------------------- | --------------------------------------- | ------ | --------------------- |
| Job Placement Excellence  | 85%+ graduates employed within 6 months | 85%    | Placement tracking    |
| Student Success           | 80%+ program completion rate            | 80%    | Enrollment records    |
| Employer Satisfaction     | 90%+ employer satisfaction score        | 90%    | Employer surveys      |
| Certification Achievement | 90%+ certification exam pass rate       | 90%    | Certification records |
| Sustainable Growth        | 10% annual enrollment growth            | 10%    | Enrollment trends     |

#### 2.1.2 Financial Goals

| Goal                      | Year 1 | Year 2 | Year 3 |
| ------------------------- | ------ | ------ | ------ |
| Gross Revenue             | $2M    | $5M    | $10M   |
| Gross Margin              | 70%    | 75%    | 80%    |
| Net Revenue Retention     | 105%   | 110%   | 115%   |
| Customer Acquisition Cost | $15K   | $12K   | $10K   |
| Lifetime Value            | $150K  | $180K  | $220K  |

#### 2.1.3 Market Goals

| Goal                       | Target                         | Timeline |
| -------------------------- | ------------------------------ | -------- |
| Customer Acquisition       | 50 institutions                | Year 1   |
| Market Coverage            | 30% of top 100 trade schools   | Year 2   |
| Program Coverage           | 200+ unique programs supported | Year 2   |
| Certification Partnerships | 20+ certification bodies       | Year 1   |
| Employer Network           | 5,000+ active employers        | Year 2   |

### 2.2 Tactical KPIs

#### 2.2.1 Student Success KPIs

| KPI ID | KPI Name                    | Definition                                    | Formula                                 | Target            | Frequency | Owner            |
| ------ | --------------------------- | --------------------------------------------- | --------------------------------------- | ----------------- | --------- | ---------------- |
| KPI01  | Job Placement Rate          | % employed within 6 months of graduation      | (Employed within 6mo / Graduates) × 100 | 85%               | Monthly   | Career Services  |
| KPI02  | Program Completion Rate     | % completing enrolled program                 | (Completed / Enrolled) × 100            | 80%               | Monthly   | Program Director |
| KPI03  | Certification Pass Rate     | % passing certification exams                 | (Passed / Attempted) × 100              | 90%               | Monthly   | Program Director |
| KPI04  | Student Retention Rate      | % continuing to next term                     | (Continued / Eligible) × 100            | 85%               | Quarterly | Enrollment       |
| KPI05  | Student Satisfaction (CSAT) | Average student satisfaction score            | Σ Ratings / Count                       | 4.2/5             | Quarterly | Program Director |
| KPI06  | Net Promoter Score          | Student likelihood to recommend               | %Promoters - %Detractors                | 50                | Quarterly | Program Director |
| KPI07  | Skills Mastery Rate         | % achieving proficiency in required skills    | (Proficient / Assessed) × 100           | 90%               | Monthly   | Instruction      |
| KPI08  | Average Starting Salary     | Median salary of new graduates                | Median(salary)                          | Industry avg +10% | Annually  | Career Services  |
| KPI09  | Time to Placement           | Average days from graduation to employment    | Σ Days / Placements                     | <90 days          | Monthly   | Career Services  |
| KPI10  | Return Student Rate         | % of alumni returning for additional programs | (Returners / Alumni) × 100              | 15%               | Annually  | Enrollment       |

#### 2.2.2 Operational KPIs

| KPI ID | KPI Name                      | Definition                                 | Formula                            | Target    | Frequency | Owner          |
| ------ | ----------------------------- | ------------------------------------------ | ---------------------------------- | --------- | --------- | -------------- |
| KPI11  | Instructor Utilization        | % of scheduled teaching hours utilized     | (Taught / Scheduled) × 100         | 85%       | Weekly    | Operations     |
| KPI12  | Lab Utilization               | % of lab capacity used                     | (Lab Hours Used / Available) × 100 | 75%       | Weekly    | Lab Manager    |
| KPI13  | Equipment Downtime            | % of time equipment unavailable            | (Downtime / Total Time) × 100      | <5%       | Monthly   | Lab Manager    |
| KPI14  | Safety Incidents              | Number of safety incidents                 | Count incidents                    | 0         | Monthly   | Safety Officer |
| KPI15  | Lab Safety Compliance         | % students with current safety training    | (Compliant / Lab Users) × 100      | 100%      | Weekly    | Safety Officer |
| KPI16  | Equipment Maintenance On-Time | % maintenance completed on schedule        | (On-Time / Scheduled) × 100        | 95%       | Monthly   | Lab Manager    |
| KPI17  | Class Fill Rate               | % of available seats filled                | (Enrolled / Capacity) × 100        | 90%       | Monthly   | Enrollment     |
| KPI18  | Waitlist Conversion           | % of waitlist students enrolled            | (Converted / Waitlist) × 100       | 40%       | Monthly   | Enrollment     |
| KPI19  | Application Response Time     | Average time to respond to applications    | Σ Response Time / Applications     | <48 hours | Weekly    | Admissions     |
| KPI20  | Enrollment Processing Time    | Average time from acceptance to enrollment | Σ Processing Days / Enrollments    | <1 week   | Monthly   | Enrollment     |

#### 2.2.3 Financial KPIs

| KPI ID | KPI Name                    | Definition                            | Formula                                | Target   | Frequency | Owner      |
| ------ | --------------------------- | ------------------------------------- | -------------------------------------- | -------- | --------- | ---------- |
| KPI21  | Application Conversion Rate | % of applicants who enroll            | (Enrolled / Applied) × 100             | 40%      | Monthly   | Admissions |
| KPI22  | Average Revenue Per Student | Revenue divided by active students    | Revenue / Students                     | $8,000   | Monthly   | Finance    |
| KPI23  | Cost Per Student            | Total training cost per student       | Total Cost / Students                  | <$5,000  | Quarterly | Finance    |
| KPI24  | Program Margin              | Profit margin per program             | (Revenue - Cost) / Revenue             | 40%      | Quarterly | Finance    |
| KPI25  | Accounts Receivable Days    | Average days to collect payment       | (AR / Revenue) × Days                  | <30 days | Monthly   | Finance    |
| KPI26  | Payment Plan Adoption       | % of students on payment plans        | (Payment Plans / Total) × 100          | 35%      | Monthly   | Finance    |
| KPI27  | Scholarship Coverage        | % of tuition covered by scholarships  | Scholarship / Tuition                  | 15%      | Quarterly | Finance    |
| KPI28  | Certification Cost Recovery | % of certification fees recovered     | (Fees Collected / Fees Incurred) × 100 | 95%      | Monthly   | Finance    |
| KPI29  | Refund Rate                 | % of enrollments resulting in refunds | (Refunds / Enrollments) × 100          | <10%     | Monthly   | Finance    |
| KPI30  | Cash Flow Positive          | Operating cash flow status            | Revenue - Expenses                     | Positive | Monthly   | Finance    |

#### 2.2.4 Employer Partnership KPIs

| KPI ID | KPI Name                        | Definition                                  | Formula                       | Target       | Frequency | Owner            |
| ------ | ------------------------------- | ------------------------------------------- | ----------------------------- | ------------ | --------- | ---------------- |
| KPI31  | Employer Satisfaction (CSAT)    | Average employer satisfaction score         | Σ Ratings / Count             | 4.5/5        | Quarterly | Career Services  |
| KPI32  | Job Posting to Fill Rate        | % of job postings filled with graduates     | (Filled / Posted) × 100       | 60%          | Monthly   | Career Services  |
| KPI33  | Employer Retention Rate         | % of employers posting multiple jobs        | (Repeat / Total) × 100        | 70%          | Quarterly | Career Services  |
| KPI34  | Time to Hire                    | Average days from posting to hire           | Σ Days / Hires                | <30 days     | Monthly   | Career Services  |
| KPI35  | Apprentice-to-Hire Conversion   | % of apprentices hired as regular employees | (Hired / Apprentices) × 100   | 75%          | Quarterly | Career Services  |
| KPI36  | Employer NPS                    | Employer Net Promoter Score                 | %Promoters - %Detractors      | 40           | Quarterly | Career Services  |
| KPI37  | Partnership Revenue             | Revenue from employer partnerships          | Σ Partnership Revenue         | 10% of total | Quarterly | Business Dev     |
| KPI38  | Industry Advisory Participation | % programs with active advisory boards      | (With Board / Programs) × 100 | 80%          | Annually  | Program Director |

### 2.3 KPI Dashboards

#### 2.3.1 Executive Dashboard

| Metric Category | Metrics                               | Refresh |
| --------------- | ------------------------------------- | ------- |
| Financial       | Revenue, margin, AR days              | Daily   |
| Enrollment      | Applications, conversions, capacity   | Daily   |
| Student Success | Completion, placement, certifications | Weekly  |
| Operations      | Utilization, incidents, satisfaction  | Weekly  |

#### 2.3.2 Program Director Dashboard

| Metric Category | Metrics                               | Refresh |
| --------------- | ------------------------------------- | ------- |
| Program Health  | Enrollment, completion, satisfaction  | Daily   |
| Certification   | Pass rates, exam scheduling           | Weekly  |
| Instruction     | Utilization, evaluations, credentials | Weekly  |
| Equipment       | Utilization, maintenance, incidents   | Weekly  |

#### 2.3.3 Career Services Dashboard

| Metric Category | Metrics                                  | Refresh |
| --------------- | ---------------------------------------- | ------- |
| Placement       | Placements, time to placement, salary    | Daily   |
| Employers       | Active employers, postings, satisfaction | Weekly  |
| Alumni          | Engagement, outcomes, referrals          | Monthly |
| Job Board       | Postings, applications, matches          | Daily   |

---

## 3. User Personas and Roles

### 3.1 Student/Trainee (P01)

#### 3.1.1 Profile

| Attribute  | Details                                            |
| ---------- | -------------------------------------------------- |
| Name       | Maria Rodriguez                                    |
| Age        | 24                                                 |
| Background | High school graduate, working entry-level          |
| Goals      | Learn trade skills, get certified, increase income |
| Programs   | Considering HVAC technician program                |
| Timeline   | Program starts next semester, 18-month duration    |
| Budget     | $15K available, seeking financial aid              |
| Technology | Smartphone primary, laptop occasionally            |

#### 3.1.2 Goals and Motivations

| Goal               | Priority | Description                                  |
| ------------------ | -------- | -------------------------------------------- |
| Skill Acquisition  | P0       | Learn practical skills for employable career |
| Certification      | P0       | Obtain industry-recognized credentials       |
| Job Placement      | P0       | Secure well-paying job after graduation      |
| Flexible Schedule  | P1       | Balance training with current work/family    |
| Financial Support  | P1       | Access financial aid and payment plans       |
| Career Advancement | P2       | Pathway to continued education/career growth |

#### 3.1.3 Pain Points

| Pain Point         | Severity | Description                                   |
| ------------------ | -------- | --------------------------------------------- |
| Program Complexity | High     | Unclear requirements, prerequisites, timeline |
| Cost Concerns      | High     | Tuition, materials, certification fees add up |
| Scheduling         | Medium   | Balancing classes, labs, work, family         |
| Skill Confidence   | Medium   | Worried about hands-on competency             |
| Job Uncertainty    | Medium   | Will I actually find work after graduation?   |

#### 3.1.4 Platform Usage

| Feature            | Frequency | Context                          |
| ------------------ | --------- | -------------------------------- |
| Course Materials   | Daily     | Study, review materials          |
| Lab Scheduling     | Weekly    | Book equipment time              |
| Skills Practice    | Daily     | Complete practice exercises      |
| Certification Info | Monthly   | Track exam requirements          |
| Job Board          | Weekly    | Explore employment opportunities |
| Communication      | As needed | Questions to instructors         |
| Financial          | Monthly   | View balance, make payments      |

#### 3.1.5 User Stories

| ID        | As a... | I want to...                              | So that...                           | Priority |
| --------- | ------- | ----------------------------------------- | ------------------------------------ | -------- |
| US-P01-01 | Student | view my program requirements and progress | I know what I need to complete       | P0       |
| US-P01-02 | Student | schedule lab time online                  | I can practice skills on my own time | P0       |
| US-P01-03 | Student | track my skills assessments               | I see which competencies to improve  | P0       |
| US-P01-04 | Student | check certification eligibility           | I know when I can take exams         | P0       |
| US-P01-05 | Student | browse job postings                       | I explore career opportunities       | P1       |
| US-P01-06 | Student | apply for financial aid                   | I can afford my education            | P0       |
| US-P01-07 | Student | receive reminders for assignments         | I don't miss deadlines               | P1       |
| US-P01-08 | Student | access materials on mobile                | I can study anywhere                 | P2       |
| US-P01-09 | Student | connect with career services              | I get job placement help             | P1       |
| US-P01-10 | Student | view my schedule in one place             | I manage my time effectively         | P1       |

---

### 3.2 Instructor (P02)

#### 3.2.1 Profile

| Attribute      | Details                                                  |
| -------------- | -------------------------------------------------------- |
| Name           | James Chen                                               |
| Age            | 42                                                       |
| Background     | 15 years industry experience, 5 years teaching           |
| Goals          | Teach effectively, maintain credentials, mentor students |
| Programs       | HVAC technician instructor                               |
| Certifications | NATE, EPA 608, OSHA 30                                   |
| Schedule       | 30 hours/week teaching, some industry consulting         |

#### 3.2.2 Goals and Motivations

| Goal                     | Priority | Description                        |
| ------------------------ | -------- | ---------------------------------- |
| Student Success          | P0       | Students learn skills and get jobs |
| Professional Development | P1       | Maintain and expand credentials    |
| Work-Life Balance        | P1       | Manage teaching and industry work  |
| Resource Access          | P1       | Have equipment and materials ready |
| Fair Compensation        | P1       | Get paid appropriately for work    |
| Recognition              | P2       | Acknowledged for teaching quality  |

#### 3.2.3 Pain Points

| Pain Point             | Severity | Description                                 |
| ---------------------- | -------- | ------------------------------------------- |
| Administrative Burden  | High     | Too much grading, documentation, scheduling |
| Equipment Issues       | Medium   | Equipment broken or unavailable             |
| Student Preparedness   | Medium   | Students unprepared for hands-on work       |
| Credential Maintenance | Medium   | Keeping certifications current              |
| Scheduling Conflicts   | Medium   | Lab conflicts, room availability            |

#### 3.2.4 Platform Usage

| Feature                  | Frequency | Context                                      |
| ------------------------ | --------- | -------------------------------------------- |
| Class Management         | Daily     | Lesson planning, attendance, materials       |
| Grading                  | Weekly    | Assignments, assessments, skills evaluations |
| Scheduling               | Weekly    | Class times, lab assignments                 |
| Student Communication    | Daily     | Questions, feedback, announcements           |
| Skills Assessment        | Weekly    | Evaluate hands-on competency                 |
| Professional Development | Monthly   | Track own certifications, training           |
| Reporting                | Monthly   | Program reports, student outcomes            |

#### 3.2.5 User Stories

| ID        | As a...    | I want to...                  | So that...                                | Priority |
| --------- | ---------- | ----------------------------- | ----------------------------------------- | -------- |
| US-P02-01 | Instructor | manage my class schedule      | I know when and where to teach            | P0       |
| US-P02-02 | Instructor | enter skills assessments      | I evaluate student competency efficiently | P0       |
| US-P02-03 | Instructor | track student attendance      | I maintain accurate records               | P0       |
| US-P02-04 | Instructor | book lab equipment            | I have resources for class activities     | P0       |
| US-P02-05 | Instructor | view my certification status  | I know when to renew credentials          | P1       |
| US-P02-06 | Instructor | communicate with students     | I provide timely feedback                 | P1       |
| US-P02-07 | Instructor | access teaching materials     | I prepare effective lessons               | P1       |
| US-P02-08 | Instructor | request equipment maintenance | Broken items get fixed promptly           | P1       |
| US-P02-09 | Instructor | view student progress         | I identify students needing help          | P1       |
| US-P02-10 | Instructor | receive teaching evaluations  | I improve my instruction                  | P2       |

---

### 3.3 Program Director (P03)

#### 3.3.1 Profile

| Attribute  | Details                                           |
| ---------- | ------------------------------------------------- |
| Name       | Sarah Williams                                    |
| Age        | 48                                                |
| Background | Former instructor, 10 years program leadership    |
| Goals      | Program success, accreditation, enrollment growth |
| Programs   | Manages HVAC, Electrical, Plumbing programs       |
| Team       | 8 instructors, 2 admin staff                      |
| Metrics    | Completion rates, placement rates, satisfaction   |

#### 3.3.2 Goals and Motivations

| Goal                  | Priority | Description                                  |
| --------------------- | -------- | -------------------------------------------- |
| Program Quality       | P0       | Maintain accreditation and quality standards |
| Enrollment Growth     | P0       | Fill seats while maintaining quality         |
| Student Outcomes      | P0       | High completion and job placement rates      |
| Staff Development     | P1       | Develop and retain quality instructors       |
| Resource Optimization | P1       | Use facilities and equipment effectively     |
| Budget Management     | P1       | Meet financial targets                       |

#### 3.3.3 Pain Points

| Pain Point              | Severity | Description                               |
| ----------------------- | -------- | ----------------------------------------- |
| Data Fragmentation      | High     | Information in multiple systems           |
| Accreditation Prep      | High     | Time-consuming documentation requirements |
| Staffing                | Medium   | Finding qualified instructors             |
| Equipment Budget        | Medium   | Balancing needs vs. costs                 |
| Enrollment Fluctuations | Medium   | Seasonal variations, market changes       |

#### 3.3.4 Platform Usage

| Feature            | Frequency | Context                       |
| ------------------ | --------- | ----------------------------- |
| Dashboard          | Daily     | Monitor program health        |
| Enrollment         | Weekly    | Manage applications, capacity |
| Reporting          | Weekly    | Outcomes, compliance reports  |
| Budget             | Monthly   | Financial planning            |
| Staff Management   | Weekly    | Assignments, evaluations      |
| Accreditation      | Quarterly | Documentation, self-study     |
| Strategic Planning | Monthly   | Program improvements          |

#### 3.3.5 User Stories

| ID        | As a...          | I want to...                   | So that...                                 | Priority |
| --------- | ---------------- | ------------------------------ | ------------------------------------------ | -------- |
| US-P03-01 | Program Director | view all program metrics       | I have real-time program health visibility | P0       |
| US-P03-02 | Program Director | generate accreditation reports | I maintain compliance efficiently          | P0       |
| US-P03-03 | Program Director | manage enrollment capacity     | I optimize class sizes                     | P0       |
| US-P03-04 | Program Director | track instructor performance   | I maintain teaching quality                | P1       |
| US-P03-05 | Program Director | monitor equipment utilization  | I justify capital investments              | P1       |
| US-P03-06 | Program Director | analyze placement outcomes     | I improve job placement                    | P1       |
| US-P03-07 | Program Director | compare program performance    | I identify improvement areas               | P1       |
| US-P03-08 | Program Director | forecast enrollment            | I plan resources effectively               | P2       |
| US-P03-09 | Program Director | manage program budget          | I control costs                            | P1       |
| US-P03-10 | Program Director | communicate with stakeholders  | I share progress and results               | P2       |

---

### 3.4 Admissions Counselor (P04)

#### 3.4.1 Profile

| Attribute  | Details                                                    |
| ---------- | ---------------------------------------------------------- |
| Name       | David Thompson                                             |
| Age        | 35                                                         |
| Background | Sales experience, education industry 5 years               |
| Goals      | Meet enrollment targets, help students find right programs |
| Programs   | All programs in institution                                |
| Quota      | 50 enrollments/quarter                                     |
| Tools      | CRM, communication platforms                               |

#### 3.4.2 Goals and Motivations

| Goal                  | Priority | Description                           |
| --------------------- | -------- | ------------------------------------- |
| Enrollment Targets    | P0       | Meet or exceed quarterly goals        |
| Student Matching      | P0       | Help students find suitable programs  |
| Pipeline Management   | P1       | Maintain healthy application pipeline |
| Relationship Building | P1       | Build trust with prospects            |
| Process Efficiency    | P1       | Minimize administrative time          |
| Team Recognition      | P2       | Top performer status                  |

#### 3.4.3 Pain Points

| Pain Point         | Severity | Description                          |
| ------------------ | -------- | ------------------------------------ |
| Lead Quality       | High     | Too many unqualified prospects       |
| Follow-Up          | High     | Too many touchpoints to track        |
| System Navigation  | Medium   | Multiple systems for different tasks |
| Information Access | Medium   | Need current program information     |
| Objection Handling | Medium   | Cost, time commitment concerns       |

#### 3.4.4 Platform Usage

| Feature                | Frequency | Context                       |
| ---------------------- | --------- | ----------------------------- |
| Application Management | Daily     | Process applications          |
| Communication          | Daily     | Contact prospects             |
| CRM                    | Daily     | Track interactions, pipeline  |
| Program Info           | As needed | Answer prospect questions     |
| Scheduling             | Daily     | Schedule visits, interviews   |
| Reporting              | Weekly    | Track performance             |
| Enrollment             | Weekly    | Complete enrollment processes |

#### 3.4.5 User Stories

| ID        | As a...              | I want to...                      | So that...                             | Priority |
| --------- | -------------------- | --------------------------------- | -------------------------------------- | -------- |
| US-P04-01 | Admissions Counselor | view all applications in my queue | I manage my workload efficiently       | P0       |
| US-P04-02 | Admissions Counselor | track prospect interactions       | I provide personalized follow-up       | P0       |
| US-P04-03 | Admissions Counselor | schedule campus visits            | Prospects can see facilities           | P1       |
| US-P04-04 | Admissions Counselor | check program availability        | I know which programs have capacity    | P0       |
| US-P04-05 | Admissions Counselor | send program information          | Prospects have details to decide       | P1       |
| US-P04-06 | Admissions Counselor | process enrollment applications   | Prospects become students quickly      | P0       |
| US-P04-07 | Admissions Counselor | view my performance metrics       | I track toward goals                   | P1       |
| US-P04-08 | Admissions Counselor | access financial aid info         | I answer cost questions accurately     | P1       |
| US-P04-09 | Admissions Counselor | manage waitlists                  | I fill seats as they open              | P1       |
| US-P04-10 | Admissions Counselor | collaborate with program staff    | I provide accurate program information | P2       |

---

### 3.5 Career Services Coordinator (P05)

#### 3.5.1 Profile

| Attribute  | Details                                                  |
| ---------- | -------------------------------------------------------- |
| Name       | Lisa Park                                                |
| Age        | 39                                                       |
| Background | HR background, 8 years in career services                |
| Goals      | Maximize job placements, build employer relationships    |
| Programs   | Supports all graduating students                         |
| Network    | 200+ employer partners                                   |
| Metrics    | Placement rate, time to placement, employer satisfaction |

#### 3.5.2 Goals and Motivations

| Goal                   | Priority | Description                            |
| ---------------------- | -------- | -------------------------------------- |
| Job Placements         | P0       | Get students employed in their field   |
| Employer Relationships | P0       | Build strong partner network           |
| Student Preparation    | P1       | Ensure students are job-ready          |
| Outcome Tracking       | P1       | Document and report placements         |
| Event Management       | P1       | Organize career fairs, employer visits |
| Alumni Engagement      | P2       | Maintain alumni for referrals          |

#### 3.5.3 Pain Points

| Pain Point          | Severity | Description                          |
| ------------------- | -------- | ------------------------------------ |
| Employer Engagement | High     | Getting employers to post jobs, hire |
| Data Collection     | High     | Tracking placement after graduation  |
| Student Readiness   | Medium   | Students unprepared for job search   |
| Time Management     | Medium   | Balancing many responsibilities      |
| Reporting           | Medium   | Accreditation requires detailed data |

#### 3.5.4 Platform Usage

| Feature             | Frequency | Context                       |
| ------------------- | --------- | ----------------------------- |
| Job Board           | Daily     | Post jobs, manage postings    |
| Employer Management | Weekly    | Partner communications        |
| Student Profiles    | Daily     | Review student qualifications |
| Placement Tracking  | Weekly    | Record job placements         |
| Career Counseling   | Daily     | Student appointments          |
| Resume Review       | Daily     | Help students improve resumes |
| Reporting           | Monthly   | Placement statistics          |
| Events              | Monthly   | Career fair planning          |

#### 3.5.5 User Stories

| ID        | As a...         | I want to...                 | So that...                            | Priority |
| --------- | --------------- | ---------------------------- | ------------------------------------- | -------- |
| US-P05-01 | Career Services | post job openings            | Students see employment opportunities | P0       |
| US-P05-02 | Career Services | match students to jobs       | Students apply to suitable positions  | P0       |
| US-P05-03 | Career Services | track job placements         | I document outcomes accurately        | P0       |
| US-P05-04 | Career Services | manage employer accounts     | Partners can post jobs easily         | P1       |
| US-P05-05 | Career Services | review student resumes       | I provide improvement feedback        | P1       |
| US-P05-06 | Career Services | schedule counseling sessions | Students get job search guidance      | P1       |
| US-P05-07 | Career Services | generate placement reports   | I have data for accreditation         | P1       |
| US-P05-08 | Career Services | view graduate outcomes       | I identify trends and improvements    | P2       |
| US-P05-09 | Career Services | organize career events       | Students meet potential employers     | P1       |
| US-P05-10 | Career Services | communicate with employers   | I maintain partnership relationships  | P1       |

---

### 3.6 Lab Manager (P06)

#### 3.6.1 Profile

| Attribute  | Details                                          |
| ---------- | ------------------------------------------------ |
| Name       | Michael Santos                                   |
| Age        | 52                                               |
| Background | Former trades professional, safety certification |
| Goals      | Safe, well-equipped labs; maximize utilization   |
| Facilities | 5 labs, 200+ equipment items                     |
| Budget     | $50K annual maintenance, $100K capex             |
| Metrics    | Utilization, incidents, maintenance costs        |

#### 3.6.2 Goals and Motivations

| Goal                   | Priority | Description                  |
| ---------------------- | -------- | ---------------------------- |
| Safety                 | P0       | Zero safety incidents        |
| Equipment Availability | P0       | Equipment ready when needed  |
| Utilization            | P1       | Maximize use of facilities   |
| Maintenance            | P1       | Proactive equipment care     |
| Budget Management      | P1       | Control costs                |
| Compliance             | P1       | Meet all safety requirements |

#### 3.6.3 Pain Points

| Pain Point           | Severity | Description                               |
| -------------------- | -------- | ----------------------------------------- |
| Equipment Breakage   | High     | Repairs costly, downtime affects teaching |
| Scheduling Conflicts | High     | Classes competing for same resources      |
| Safety Compliance    | High     | OSHA requirements must be met             |
| Inventory Management | Medium   | Tracking consumables, equipment           |
| Budget Constraints   | Medium   | Limited funds for upgrades                |

#### 3.6.4 Platform Usage

| Feature             | Frequency | Context                         |
| ------------------- | --------- | ------------------------------- |
| Lab Scheduling      | Daily     | Assign lab time to classes      |
| Equipment Tracking  | Daily     | Checkouts, returns, status      |
| Maintenance         | Weekly    | Schedule and track repairs      |
| Safety Logs         | As needed | Document incidents, inspections |
| Inventory           | Weekly    | Track supplies, reorder         |
| Utilization Reports | Monthly   | Analyze lab usage               |
| Budget Tracking     | Monthly   | Monitor expenses                |

#### 3.6.5 User Stories

| ID        | As a...     | I want to...                | So that...                             | Priority |
| --------- | ----------- | --------------------------- | -------------------------------------- | -------- |
| US-P06-01 | Lab Manager | manage lab schedules        | Classes have appropriate lab access    | P0       |
| US-P06-02 | Lab Manager | track equipment checkout    | I know where equipment is at all times | P0       |
| US-P06-03 | Lab Manager | schedule maintenance        | Equipment stays in good condition      | P0       |
| US-P06-04 | Lab Manager | monitor safety compliance   | Students complete required training    | P0       |
| US-P06-05 | Lab Manager | view utilization reports    | I optimize lab scheduling              | P1       |
| US-P06-06 | Lab Manager | manage equipment inventory  | I know what we have and need           | P1       |
| US-P06-07 | Lab Manager | document safety incidents   | I maintain safety records              | P0       |
| US-P06-08 | Lab Manager | control lab access          | Only authorized personnel enter        | P1       |
| US-P06-09 | Lab Manager | track consumable usage      | I manage supplies budget               | P1       |
| US-P06-10 | Lab Manager | request equipment purchases | I justify capital needs                | P2       |

---

### 3.7 Financial Administrator (P07)

#### 3.7.1 Profile

| Attribute        | Details                                                 |
| ---------------- | ------------------------------------------------------- |
| Name             | Jennifer Adams                                          |
| Age              | 44                                                      |
| Background       | Accounting background, education finance                |
| Goals            | Accurate billing, timely collections, budget compliance |
| Responsibilities | Billing, AR, financial aid processing, reporting        |
| Systems          | Billing platform, financial aid systems                 |
| Metrics          | AR days, refund accuracy, financial aid compliance      |

#### 3.7.2 Goals and Motivations

| Goal                     | Priority | Description                     |
| ------------------------ | -------- | ------------------------------- |
| Revenue Collection       | P0       | Collect payments on time        |
| Billing Accuracy         | P0       | Correct charges, avoid disputes |
| Financial Aid Compliance | P0       | Meet regulatory requirements    |
| Budget Management        | P1       | Track program budgets           |
| Reporting                | P1       | Accurate financial reports      |
| Process Efficiency       | P1       | Streamline financial operations |

#### 3.7.3 Pain Points

| Pain Point               | Severity | Description                     |
| ------------------------ | -------- | ------------------------------- |
| Payment Follow-Up        | High     | Chasing delinquent accounts     |
| Financial Aid Complexity | High     | Multiple programs, rules vary   |
| Refund Calculations      | Medium   | Complex rules, must be accurate |
| System Integration       | Medium   | Data sync between systems       |
| Audit Preparation        | Medium   | Documentation requirements      |

#### 3.7.4 Platform Usage

| Feature         | Frequency | Context                             |
| --------------- | --------- | ----------------------------------- |
| Billing         | Daily     | Generate invoices, process payments |
| Financial Aid   | Weekly    | Process aid applications            |
| Payment Plans   | Weekly    | Set up payment schedules            |
| Refunds         | As needed | Process withdrawal refunds          |
| Reporting       | Weekly    | AR reports, revenue reports         |
| Budget Tracking | Monthly   | Monitor program budgets             |
| Audit Support   | As needed | Provide documentation               |

#### 3.7.5 User Stories

| ID        | As a...         | I want to...               | So that...                           | Priority |
| --------- | --------------- | -------------------------- | ------------------------------------ | -------- |
| US-P07-01 | Financial Admin | generate student bills     | Students know what they owe          | P0       |
| US-P07-02 | Financial Admin | process payments           | Accounts get credited accurately     | P0       |
| US-P07-03 | Financial Admin | set up payment plans       | Students can pay over time           | P1       |
| US-P07-04 | Financial Admin | calculate refunds          | Withdrawals processed correctly      | P1       |
| US-P07-05 | Financial Admin | track financial aid        | Students receive entitled aid        | P0       |
| US-P07-06 | Financial Admin | view AR aging              | I prioritize collection efforts      | P1       |
| US-P07-07 | Financial Admin | generate financial reports | Leadership has accurate data         | P1       |
| US-P07-08 | Financial Admin | manage scholarship funds   | Awards applied correctly             | P1       |
| US-P07-09 | Financial Admin | track certification fees   | Exam costs billed properly           | P1       |
| US-P07-10 | Financial Admin | support audits             | I can provide required documentation | P2       |

---

### 3.8 External Employer (P08)

#### 3.8.1 Profile

| Attribute    | Details                                   |
| ------------ | ----------------------------------------- |
| Name         | TechFlow Manufacturing                    |
| Type         | Manufacturing company                     |
| Size         | 200 employees                             |
| Hiring Needs | CNC operators, welders, maintenance techs |
| Pain Points  | Difficulty finding qualified workers      |
| Engagement   | Posts jobs, attends career fairs          |
| Goals        | Hire qualified candidates efficiently     |

#### 3.8.2 Goals and Motivations

| Goal                 | Priority | Description             |
| -------------------- | -------- | ----------------------- |
| Qualified Hires      | P0       | Find skilled workers    |
| Efficient Process    | P1       | Streamlined hiring      |
| Quality Candidates   | P1       | Well-trained applicants |
| Cost Effective       | P1       | Reasonable hiring costs |
| Pipeline Development | P2       | Ongoing talent pipeline |

#### 3.8.3 Pain Points

| Pain Point        | Severity | Description                     |
| ----------------- | -------- | ------------------------------- |
| Skills Gap        | High     | Not enough qualified candidates |
| Time to Hire      | Medium   | Hiring takes too long           |
| Candidate Quality | Medium   | Resume doesn't match skills     |
| Cost              | Medium   | Recruiting expenses high        |
| Retention         | Medium   | New hires leave quickly         |

#### 3.8.4 Platform Usage

| Feature                | Frequency | Context                       |
| ---------------------- | --------- | ----------------------------- |
| Job Posting            | As needed | Post open positions           |
| Candidate Review       | Weekly    | Review graduate profiles      |
| Interview Scheduling   | As needed | Schedule candidate interviews |
| Hiring Feedback        | As needed | Provide hire/no-hire feedback |
| Partnership Management | Monthly   | Manage partnership account    |

#### 3.8.5 User Stories

| ID        | As a...  | I want to...                 | So that...                          | Priority |
| --------- | -------- | ---------------------------- | ----------------------------------- | -------- |
| US-P08-01 | Employer | post job openings            | Graduates see our opportunities     | P0       |
| US-P08-02 | Employer | view candidate profiles      | I assess qualifications             | P0       |
| US-P08-03 | Employer | search for candidates        | I find matching skills              | P1       |
| US-P08-04 | Employer | contact candidates           | I reach potential hires             | P1       |
| US-P08-05 | Employer | schedule interviews          | I meet qualified candidates         | P1       |
| US-P08-06 | Employer | provide feedback             | School knows hiring outcomes        | P2       |
| US-P08-07 | Employer | manage multiple postings     | I track all opportunities           | P2       |
| US-P08-08 | Employer | see candidate certifications | I verify qualifications             | P1       |
| US-P08-09 | Employer | partner on curriculum        | Future graduates have needed skills | P2       |
| US-P08-10 | Employer | access apprentice pipeline   | I develop talent early              | P2       |

---

## 4. Core User Journeys

### 4.1 J01: Student Application Journey

#### 4.1.1 Journey Overview

**Persona**: Prospective Student (P01)

**Goal**: Apply for and enroll in a vocational training program

**Duration**: 2 weeks to 3 months

**Success Criteria**: Student successfully enrolled and oriented

#### 4.1.2 Journey Stages

| Stage       | Steps                                    | Duration | Owner      |
| ----------- | ---------------------------------------- | -------- | ---------- |
| Discovery   | Explore programs, check eligibility      | 1-7 days | Student    |
| Inquiry     | Submit inquiry, receive response         | 1-3 days | Admissions |
| Application | Complete application, submit documents   | 3-7 days | Student    |
| Interview   | Complete admissions interview            | 1 day    | Admissions |
| Decision    | Receive admission decision               | 1-3 days | Admissions |
| Enrollment  | Accept offer, complete enrollment        | 3-7 days | Student    |
| Orientation | Attend orientation, register for classes | 1-2 days | Program    |

#### 4.1.3 Detailed Steps

**Stage 1: Discovery**

| Step | Action                            | System        | User Story              |
| ---- | --------------------------------- | ------------- | ----------------------- |
| 1.1  | Browse programs on website        | Website       | View available programs |
| 1.2  | Read program details              | Website       | Understand requirements |
| 1.3  | Check prerequisites               | Website       | Know eligibility        |
| 1.4  | View tuition and costs            | Website       | Understand investment   |
| 1.5  | Contact admissions with questions | Website/Phone | Get clarification       |

**Stage 2: Inquiry**

| Step | Action                           | System      | User Story             |
| ---- | -------------------------------- | ----------- | ---------------------- |
| 2.1  | Submit inquiry form              | Website     | Express interest       |
| 2.2  | Receive acknowledgment           | Email       | Confirmation received  |
| 2.3  | Admissions assigned to counselor | CRM         | Personalized attention |
| 2.4  | Counselor contacts prospect      | Email/Phone | Personal outreach      |
| 2.5  | Provide additional information   | CRM         | Address questions      |

**Stage 3: Application**

| Step | Action                          | System     | User Story              |
| ---- | ------------------------------- | ---------- | ----------------------- |
| 3.1  | Create applicant account        | Enrollment | Access application      |
| 3.2  | Complete personal information   | Enrollment | Provide demographics    |
| 3.3  | Submit academic history         | Enrollment | Document background     |
| 3.4  | Upload required documents       | Enrollment | Provide transcripts, ID |
| 3.5  | Complete program-specific forms | Enrollment | Program requirements    |
| 3.6  | Pay application fee             | Payment    | Submit fee              |
| 3.7  | Submit application              | Enrollment | Complete submission     |

**Stage 4: Interview**

| Step | Action                                       | System            | User Story          |
| ---- | -------------------------------------------- | ----------------- | ------------------- |
| 4.1  | Receive interview invitation                 | Email             | Scheduled interview |
| 4.2  | Schedule interview time                      | Scheduling        | Set appointment     |
| 4.3  | Complete interview                           | In-person/Virtual | Meet admissions     |
| 4.4  | Interviewer completes evaluation             | Enrollment        | Assessment recorded |
| 4.5  | Additional information requested (if needed) | Email             | Clarify details     |

**Stage 5: Decision**

| Step | Action                           | System     | User Story              |
| ---- | -------------------------------- | ---------- | ----------------------- |
| 5.1  | Admissions review application    | Enrollment | Evaluate candidate      |
| 5.2  | Verify prerequisites             | Enrollment | Confirm eligibility     |
| 5.3  | Make admission decision          | Enrollment | Accept/deny/waitlist    |
| 5.4  | Send decision letter             | Email      | Notify applicant        |
| 5.5  | Provide next steps (if accepted) | Email      | Enrollment instructions |

**Stage 6: Enrollment**

| Step | Action                                  | System        | User Story           |
| ---- | --------------------------------------- | ------------- | -------------------- |
| 6.1  | Accept admission offer                  | Enrollment    | Confirm enrollment   |
| 6.2  | Complete enrollment forms               | Enrollment    | Legal requirements   |
| 6.3  | Submit enrollment deposit               | Payment       | Secure spot          |
| 6.4  | Apply for financial aid (if applicable) | Financial Aid | Request assistance   |
| 6.5  | Set up payment plan (if applicable)     | Billing       | Payment schedule     |
| 6.6  | Complete health forms                   | Enrollment    | Medical requirements |
| 6.7  | Receive enrollment confirmation         | Email         | Welcome package      |

**Stage 7: Orientation**

| Step | Action                          | System     | User Story              |
| ---- | ------------------------------- | ---------- | ----------------------- |
| 7.1  | Register for orientation        | Enrollment | Secure orientation spot |
| 7.2  | Attend orientation sessions     | In-person  | Learn about program     |
| 7.3  | Meet instructors                | In-person  | Introduce to faculty    |
| 7.4  | Tour facilities                 | In-person  | See labs and equipment  |
| 7.5  | Register for first-term courses | Enrollment | Select classes          |
| 7.6  | Receive student credentials     | IT         | Get login access        |
| 7.7  | Access student portal           | Portal     | Begin using system      |

#### 4.1.4 Touchpoints and Channels

| Touchpoint         | Channel           | Owner      | Metrics                    |
| ------------------ | ----------------- | ---------- | -------------------------- |
| Program browsing   | Website           | Marketing  | Time on page, pages viewed |
| Inquiry submission | Website/Phone     | Marketing  | Inquiry volume             |
| Counselor contact  | Email/Phone       | Admissions | Response time              |
| Application portal | Web Portal        | Admissions | Completion rate            |
| Interview          | In-person/Virtual | Admissions | Show rate                  |
| Decision letter    | Email             | Admissions | Open rate                  |
| Enrollment forms   | Web Portal        | Admissions | Completion rate            |
| Orientation        | In-person         | Program    | Attendance                 |

#### 4.1.5 Key Metrics

| Metric                      | Definition                            | Target  |
| --------------------------- | ------------------------------------- | ------- |
| Application Completion Rate | % of started applications completed   | 70%     |
| Admissions Decision Time    | Avg days from application to decision | 5 days  |
| Offer Acceptance Rate       | % of offers accepted                  | 60%     |
| Enrollment Conversion       | % of inquiries to enrollments         | 40%     |
| Time to Enrollment          | Avg days from inquiry to enrollment   | 30 days |
| Application Satisfaction    | CSAT on application experience        | 4.0/5   |

---

### 4.2 J02: Course Enrollment and Prerequisites Journey

#### 4.2.1 Journey Overview

**Persona**: Enrolled Student (P01)

**Goal**: Register for courses meeting prerequisites

**Duration**: 1-2 weeks per term

**Success Criteria**: Successfully enrolled in appropriate courses

#### 4.2.2 Journey Stages

| Stage    | Steps                                 | Duration | Owner   |
| -------- | ------------------------------------- | -------- | ------- |
| Review   | View program requirements, transcript | 1-2 days | Student |
| Plan     | Plan course sequence for term         | 1-2 days | Student |
| Select   | Choose specific course sections       | 1 day    | Student |
| Validate | System checks prerequisites           | 1 day    | System  |
| Register | Complete enrollment                   | 1 day    | Student |
| Confirm  | Receive confirmation, add to schedule | 1 day    | System  |

#### 4.2.3 Detailed Steps

**Stage 1: Review**

| Step | Action                     | System     | User Story               |
| ---- | -------------------------- | ---------- | ------------------------ |
| 1.1  | Access student portal      | Portal     | Log in to system         |
| 1.2  | View program requirements  | Enrollment | See required courses     |
| 1.3  | Check current transcript   | Enrollment | Review completed courses |
| 1.4  | View skills proficiency    | Skills     | Check competency levels  |
| 1.5  | Review graduation progress | Enrollment | Track overall progress   |

**Stage 2: Plan**

| Step | Action                      | System     | User Story            |
| ---- | --------------------------- | ---------- | --------------------- |
| 2.1  | Identify eligible courses   | Enrollment | See available courses |
| 2.2  | Check course schedules      | Scheduling | View class times      |
| 2.3  | Verify lab requirements     | Scheduling | See lab components    |
| 2.4  | Plan course sequence        | Enrollment | Determine order       |
| 2.5  | Consult advisor (if needed) | Messaging  | Get guidance          |

**Stage 3: Select**

| Step | Action                   | System     | User Story           |
| ---- | ------------------------ | ---------- | -------------------- |
| 3.1  | Browse course catalog    | Enrollment | View course options  |
| 3.2  | Select desired courses   | Enrollment | Choose courses       |
| 3.3  | Select specific sections | Scheduling | Pick class times     |
| 3.4  | Add to enrollment cart   | Enrollment | Prepare registration |
| 3.5  | Review selected courses  | Enrollment | Confirm selections   |

**Stage 4: Validate**

| Step | Action                       | System     | User Story              |
| ---- | ---------------------------- | ---------- | ----------------------- |
| 4.1  | System checks prerequisites  | Enrollment | Verify requirements met |
| 4.2  | System checks time conflicts | Scheduling | No scheduling conflicts |
| 4.3  | System checks capacity       | Enrollment | Seats available         |
| 4.4  | System checks holds          | Enrollment | No registration holds   |
| 4.5  | Prerequisites warnings shown | Enrollment | Issues displayed        |

**Stage 5: Register**

| Step | Action                          | System     | User Story            |
| ---- | ------------------------------- | ---------- | --------------------- |
| 5.1  | Address any issues              | Enrollment | Resolve problems      |
| 5.2  | Confirm enrollment              | Enrollment | Finalize registration |
| 5.3  | Pay any fees                    | Billing    | Cover costs           |
| 5.4  | Sign enrollment agreement       | Enrollment | Accept terms          |
| 5.5  | Receive enrollment confirmation | Email      | Confirmation sent     |

**Stage 6: Confirm**

| Step | Action                            | System      | User Story           |
| ---- | --------------------------------- | ----------- | -------------------- |
| 6.1  | View updated schedule             | Scheduling  | See enrolled classes |
| 6.2  | Receive class materials list      | Enrollment  | Know what to bring   |
| 6.3  | Add schedule to personal calendar | Integration | Sync with calendar   |
| 6.4  | Receive first class notification  | Email       | Know when/where      |
| 6.5  | Access course materials           | LMS         | Start preparing      |

#### 4.2.4 Prerequisite Validation Rules

| Rule                     | Description                         | Enforcement                 |
| ------------------------ | ----------------------------------- | --------------------------- |
| Course Prerequisites     | Must pass prerequisite courses      | Hard block                  |
| Skills Prerequisites     | Must demonstrate skill proficiency  | Hard block                  |
| Attendance Prerequisites | Must meet attendance threshold      | Hard block                  |
| Safety Training          | Must complete safety certification  | Hard block                  |
| Equipment Certification  | Must be certified for equipment     | Hard block                  |
| Age Requirements         | Must meet minimum age               | Hard block                  |
| Medical Clearance        | Must have current medical clearance | Hard block for some courses |
| Behavioral Requirements  | Must meet conduct standards         | Hard block                  |

#### 4.2.5 Key Metrics

| Metric                       | Definition                        | Target |
| ---------------------------- | --------------------------------- | ------ |
| Self-Service Enrollment Rate | % enrolling without assistance    | 80%    |
| Prerequisite Issue Rate      | % with prerequisite problems      | <10%   |
| Enrollment Error Rate        | % requiring corrections           | <5%    |
| Waitlist Fill Rate           | % waitlist students enrolled      | 40%    |
| Schedule Adjustment Rate     | % making changes after enrollment | <15%   |

---

### 4.3 J03: Lab Scheduling and Equipment Journey

#### 4.3.1 Journey Overview

**Persona**: Student (P01) or Instructor (P02)

**Goal**: Book and use lab equipment safely

**Duration**: 1 hour to 2 weeks

**Success Criteria**: Equipment used successfully, returned in good condition

#### 4.3.2 Journey Stages

| Stage     | Steps                                 | Duration   | Owner  |
| --------- | ------------------------------------- | ---------- | ------ |
| Request   | Identify need, check availability     | 1-24 hours | User   |
| Book      | Reserve equipment and time            | 1 hour     | User   |
| Verify    | Confirm safety training, eligibility  | 1 hour     | System |
| Check Out | Collect equipment, sign documentation | 15 minutes | User   |
| Use       | Use equipment for intended purpose    | Variable   | User   |
| Return    | Return equipment, inspection          | 15 minutes | User   |
| Close     | Confirm return, update records        | 1 hour     | System |

#### 4.3.3 Detailed Steps

**Stage 1: Request**

| Step | Action                          | System     | User Story                   |
| ---- | ------------------------------- | ---------- | ---------------------------- |
| 1.1  | Identify equipment needed       | Planning   | Determine requirements       |
| 1.2  | Check equipment catalog         | Equipment  | View available items         |
| 1.3  | Verify equipment specifications | Equipment  | Confirm suitability          |
| 1.4  | Check availability calendar     | Scheduling | See time slots               |
| 1.5  | Verify personal eligibility     | Skills     | Check training/certification |

**Stage 2: Book**

| Step | Action                   | System     | User Story         |
| ---- | ------------------------ | ---------- | ------------------ |
| 2.1  | Select equipment item(s) | Equipment  | Choose items       |
| 2.2  | Select date and time     | Scheduling | Reserve time       |
| 2.3  | Specify duration needed  | Scheduling | Set time slot      |
| 2.4  | Add purpose notes        | Scheduling | Document reason    |
| 2.5  | Submit booking request   | Scheduling | Create reservation |

**Stage 3: Verify**

| Step | Action                            | System     | User Story            |
| ---- | --------------------------------- | ---------- | --------------------- |
| 3.1  | System checks safety training     | Safety     | Verify certifications |
| 3.2  | System checks skill prerequisites | Skills     | Verify competencies   |
| 3.3  | System checks capacity limits     | Scheduling | No overbooking        |
| 3.4  | System checks equipment status    | Equipment  | Item available        |
| 3.5  | Booking approval notification     | Email      | Confirmation sent     |

**Stage 4: Check Out**

| Step | Action                                | System    | User Story              |
| ---- | ------------------------------------- | --------- | ----------------------- |
| 4.1  | Arrive at lab during booked time      | In-person | Present at lab          |
| 4.2  | Show booking confirmation             | Portal    | Prove reservation       |
| 4.3  | Lab staff verifies eligibility        | Equipment | Confirm qualifications  |
| 4.4  | Equipment inspection and handoff      | Equipment | Check condition         |
| 4.5  | Sign checkout agreement               | Equipment | Accept responsibility   |
| 4.6  | Receive safety briefing (if required) | Safety    | Understand requirements |

**Stage 5: Use**

| Step | Action                    | System    | User Story      |
| ---- | ------------------------- | --------- | --------------- |
| 5.1  | Use equipment as intended | In-person | Complete work   |
| 5.2  | Follow safety procedures  | In-person | Maintain safety |
| 5.3  | Document work completed   | Logging   | Record output   |
| 5.4  | Report any issues         | Incident  | Log problems    |
| 5.5  | Clean work area           | In-person | Leave clean     |

**Stage 6: Return**

| Step | Action                            | System    | User Story         |
| ---- | --------------------------------- | --------- | ------------------ |
| 6.1  | Clean equipment                   | In-person | Prepare for return |
| 6.2  | Bring equipment to return station | In-person | Deliver equipment  |
| 6.3  | Lab staff inspects equipment      | Equipment | Check condition    |
| 6.4  | Report any damage/issues          | Incident  | Document problems  |
| 6.5  | Sign return documentation         | Equipment | Confirm return     |

**Stage 7: Close**

| Step | Action                                 | System     | User Story         |
| ---- | -------------------------------------- | ---------- | ------------------ |
| 7.1  | System updates equipment status        | Equipment  | Available again    |
| 7.2  | Booking marked complete                | Scheduling | Reservation closed |
| 7.3  | Usage recorded                         | Analytics  | Data captured      |
| 7.4  | Damage charges applied (if applicable) | Billing    | Fees assessed      |
| 7.5  | Return confirmation sent               | Email      | Notification       |

#### 4.3.4 Equipment Types and Requirements

| Equipment Category | Examples                          | Certification Required  | Max Users | Duration   |
| ------------------ | --------------------------------- | ----------------------- | --------- | ---------- |
| Power Tools        | Saws, drills, grinders            | Basic Safety            | 1         | 2-8 hours  |
| Welding Equipment  | MIG, TIG welders                  | Welding Safety + Skill  | 1         | 2-8 hours  |
| CNC Machines       | Lathes, mills                     | CNC Certification       | 1-2       | 2-16 hours |
| Automotive Lifts   | 2-post, 4-post lifts              | Lift Certification      | 1         | 2-8 hours  |
| HVAC Equipment     | Manifolds, vacuum pumps           | EPA Certification       | 1-4       | 1-8 hours  |
| Electronics        | Soldering stations, oscilloscopes | Basic Safety            | 1         | 1-4 hours  |
| Culinary Equipment | Ovens, ranges, mixers             | Kitchen Safety          | 1-6       | 2-8 hours  |
| Heavy Equipment    | Forklifts, skid steers            | Equipment Certification | 1         | 2-8 hours  |

#### 4.3.5 Key Metrics

| Metric                  | Definition                     | Target     |
| ----------------------- | ------------------------------ | ---------- |
| Lab Utilization Rate    | % of capacity used             | 75%        |
| Equipment Availability  | % time equipment available     | 95%        |
| Booking Completion Rate | % bookings used as scheduled   | 90%        |
| No-Show Rate            | % bookings not used            | <10%       |
| Equipment Damage Rate   | % returns with damage          | <2%        |
| Safety Incident Rate    | Incidents per 1000 hours       | 0          |
| Checkout Time           | Avg time for checkout process  | <5 minutes |
| Return Processing Time  | Avg time for return inspection | <5 minutes |

---

### 4.4 J04: Skills Assessment Journey

#### 4.4.1 Journey Overview

**Persona**: Student (P01), Instructor (P02)

**Goal**: Assess and validate practical skills competency

**Duration**: 1 week to 1 month

**Success Criteria**: Skills accurately assessed and documented

#### 4.4.2 Journey Stages

| Stage        | Steps                            | Duration  | Owner      |
| ------------ | -------------------------------- | --------- | ---------- |
| Preparation  | Review skills, prepare materials | 1-3 days  | Instructor |
| Notification | Inform student of assessment     | 1 day     | Instructor |
| Practice     | Student practices skills         | 3-7 days  | Student    |
| Assessment   | Instructor evaluates skills      | 1 day     | Instructor |
| Scoring      | Instructor records results       | 1 day     | Instructor |
| Feedback     | Student receives results         | 1 day     | Instructor |
| Remediation  | Student improves (if needed)     | 1-2 weeks | Student    |
| Retest       | Reassessment (if needed)         | 1 day     | Instructor |

#### 4.4.3 Detailed Steps

**Stage 1: Preparation**

| Step | Action                       | System     | User Story          |
| ---- | ---------------------------- | ---------- | ------------------- |
| 1.1  | Review skills rubric         | Skills     | Understand criteria |
| 1.2  | Prepare assessment materials | Planning   | Gather resources    |
| 1.3  | Schedule assessment session  | Scheduling | Set time            |
| 1.4  | Notify student of assessment | Email      | Inform student      |
| 1.5  | Book equipment if needed     | Equipment  | Reserve resources   |

**Stage 2: Notification**

| Step | Action                        | System     | User Story              |
| ---- | ----------------------------- | ---------- | ----------------------- |
| 2.1  | Student receives notification | Email      | Know about assessment   |
| 2.2  | Student reviews rubric        | Skills     | Understand expectations |
| 2.3  | Student prepares materials    | Planning   | Gather personal tools   |
| 2.4  | Student confirms attendance   | Scheduling | Acknowledge             |

**Stage 3: Practice**

| Step | Action                        | System     | User Story       |
| ---- | ----------------------------- | ---------- | ---------------- |
| 3.1  | Student books practice time   | Scheduling | Reserve lab      |
| 3.2  | Student practices skills      | In-person  | Build competency |
| 3.3  | Student seeks instructor help | Messaging  | Get guidance     |
| 3.4  | Student self-assesses         | Skills     | Check readiness  |

**Stage 4: Assessment**

| Step | Action                            | System    | User Story                |
| ---- | --------------------------------- | --------- | ------------------------- |
| 4.1  | Student arrives for assessment    | In-person | Present at scheduled time |
| 4.2  | Instructor verifies eligibility   | Skills    | Confirm prerequisites     |
| 4.3  | Instructor explains process       | In-person | Set expectations          |
| 4.4  | Student performs skills           | In-person | Demonstrate competency    |
| 4.5  | Instructor observes and records   | Skills    | Document performance      |
| 4.6  | Instructor asks probing questions | In-person | Verify understanding      |

**Stage 5: Scoring**

| Step | Action                                  | System | User Story         |
| ---- | --------------------------------------- | ------ | ------------------ |
| 5.1  | Instructor reviews observations         | Skills | Recall performance |
| 5.2  | Instructor scores each criterion        | Skills | Apply rubric       |
| 5.3  | Instructor calculates proficiency level | Skills | Determine level    |
| 5.4  | Instructor adds comments                | Skills | Provide context    |
| 5.5  | Instructor submits assessment           | Skills | Record results     |

**Stage 6: Feedback**

| Step | Action                                  | System    | User Story           |
| ---- | --------------------------------------- | --------- | -------------------- |
| 6.1  | Student receives results notification   | Email     | Know outcome         |
| 6.2  | Student accesses assessment results     | Skills    | View detailed scores |
| 6.3  | Student reviews instructor comments     | Skills    | Understand feedback  |
| 6.4  | Instructor meets to discuss (if needed) | In-person | Provide guidance     |
| 6.5  | Student acknowledges receipt            | Skills    | Confirm review       |

**Stage 7: Remediation**

| Step | Action                            | System     | User Story       |
| ---- | --------------------------------- | ---------- | ---------------- |
| 7.1  | Student identifies weak areas     | Skills     | Pinpoint gaps    |
| 7.2  | Student creates improvement plan  | Planning   | Outline approach |
| 7.3  | Student books additional practice | Scheduling | Reserve time     |
| 7.4  | Student practices targeted skills | In-person  | Build competency |
| 7.5  | Student requests reassessment     | Skills     | Apply for retest |

**Stage 8: Retest**

| Step | Action                            | System     | User Story       |
| ---- | --------------------------------- | ---------- | ---------------- |
| 8.1  | Instructor reviews retest request | Skills     | Evaluate request |
| 8.2  | Instructor approves retest        | Skills     | Authorize retest |
| 8.3  | Reassessment scheduled            | Scheduling | Set new time     |
| 8.4  | Reassessment conducted            | Skills     | Repeat process   |
| 8.5  | New results recorded              | Skills     | Update record    |

#### 4.4.4 Skills Assessment Rubric Structure

| Component           | Description                    | Weight |
| ------------------- | ------------------------------ | ------ |
| Technical Execution | Correct technique, proper form | 40%    |
| Safety Compliance   | Following safety procedures    | 20%    |
| Quality of Work     | Output meets standards         | 20%    |
| Efficiency          | Reasonable time, no waste      | 10%    |
| Problem Solving     | Handling unexpected issues     | 10%    |

#### 4.4.5 Proficiency Levels

| Level      | Description                               | Criteria                     |
| ---------- | ----------------------------------------- | ---------------------------- |
| Novice     | Basic understanding, requires supervision | Can perform with guidance    |
| Developing | Growing competence, occasional assistance | Consistent with minimal help |
| Competent  | Independent performance, meets standards  | Reliable independent work    |
| Proficient | Consistent excellence, handles variations | Adaptable to situations      |
| Expert     | Mastery level, can teach others           | Exceptional performance      |

#### 4.4.6 Key Metrics

| Metric                           | Definition                             | Target         |
| -------------------------------- | -------------------------------------- | -------------- |
| Assessment Completion Rate       | % of assessments completed on schedule | 95%            |
| First-Time Pass Rate             | % passing initial assessment           | 80%            |
| Retest Pass Rate                 | % passing retest                       | 90%            |
| Assessment to Certification Time | Avg days from first assessment to cert | 14 days        |
| Skills Consistency               | Inter-rater reliability                | >90% agreement |
| Student Satisfaction             | CSAT on assessment experience          | 4.0/5          |

---

### 4.5 J05: Certification Exam Journey

#### 4.5.1 Journey Overview

**Persona**: Student (P01), Program Director (P03)

**Goal**: Complete industry certification exam successfully

**Duration**: 2 weeks to 3 months

**Success Criteria**: Certification earned and documented

#### 4.5.2 Journey Stages

| Stage        | Steps                                | Duration  | Owner              |
| ------------ | ------------------------------------ | --------- | ------------------ |
| Eligibility  | Verify eligibility for certification | 1-3 days  | Program            |
| Preparation  | Study and prepare for exam           | 2-8 weeks | Student            |
| Registration | Register for certification exam      | 1-7 days  | Student/Program    |
| Scheduling   | Schedule exam date and time          | 1-7 days  | Program            |
| Exam         | Take certification exam              | 1 day     | Student            |
| Results      | Receive exam results                 | 1-14 days | Certification Body |
| Credential   | Receive and record credential        | 1-7 days  | Program            |
| Renewal      | Track and renew certification        | Ongoing   | Student/Program    |

#### 4.5.3 Detailed Steps

**Stage 1: Eligibility**

| Step | Action                            | System        | User Story                  |
| ---- | --------------------------------- | ------------- | --------------------------- |
| 1.1  | Review certification requirements | Certification | Understand prerequisites    |
| 1.2  | Check skills proficiency          | Skills        | Verify competencies met     |
| 1.3  | Verify completed coursework       | Enrollment    | Confirm course completion   |
| 1.4  | Confirm hours of experience       | Skills        | Validate experience         |
| 1.5  | Receive eligibility confirmation  | Email         | Notification of eligibility |

**Stage 2: Preparation**

| Step | Action                            | System        | User Story               |
| ---- | --------------------------------- | ------------- | ------------------------ |
| 2.1  | Receive exam prep materials       | LMS           | Access study materials   |
| 2.2  | Complete prep course (if offered) | LMS           | Take preparatory course  |
| 2.3  | Take practice exams               | LMS           | Simulate exam experience |
| 2.4  | Review exam content outline       | Certification | Know what to study       |
| 2.5  | Schedule study groups             | Messaging     | Collaborate with peers   |

**Stage 3: Registration**

| Step | Action                               | System      | User Story             |
| ---- | ------------------------------------ | ----------- | ---------------------- |
| 3.1  | Create certification body account    | External    | Set up account         |
| 3.2  | Complete registration form           | External    | Submit application     |
| 3.3  | Pay exam fees                        | Payment     | Cover costs            |
| 3.4  | Receive registration confirmation    | Email       | Confirmation received  |
| 3.5  | Registration synced to school system | Integration | School records updated |

**Stage 4: Scheduling**

| Step | Action                          | System      | User Story            |
| ---- | ------------------------------- | ----------- | --------------------- |
| 4.1  | View available exam dates       | Scheduling  | See options           |
| 4.2  | Select preferred date and time  | Scheduling  | Choose slot           |
| 4.3  | Confirm exam location           | Scheduling  | Know where to go      |
| 4.4  | Receive scheduling confirmation | Email       | Confirmation received |
| 4.5  | Add to personal calendar        | Integration | Reminder set          |

**Stage 5: Exam**

| Step | Action                          | System           | User Story                 |
| ---- | ------------------------------- | ---------------- | -------------------------- |
| 5.1  | Receive exam day instructions   | Email            | Know what to bring         |
| 5.2  | Arrive at exam location         | In-person        | Present at scheduled time  |
| 5.3  | Complete check-in process       | In-person        | Verify identity            |
| 5.4  | Complete exam                   | In-person/Online | Take test                  |
| 5.5  | Receive completion confirmation | Email            | Confirmation of completion |

**Stage 6: Results**

| Step | Action                           | System        | User Story           |
| ---- | -------------------------------- | ------------- | -------------------- |
| 6.1  | Receive results notification     | Email         | Know outcome         |
| 6.2  | View detailed score report       | Certification | See performance      |
| 6.3  | Results synced to school records | Integration   | School has data      |
| 6.4  | Celebrate success (if passed)    | In-person     | Recognition event    |
| 6.5  | Plan retake (if failed)          | Planning      | Determine next steps |

**Stage 7: Credential**

| Step | Action                                 | System        | User Story             |
| ---- | -------------------------------------- | ------------- | ---------------------- |
| 7.1  | Receive physical credential            | Mail          | Get certificate        |
| 7.2  | Digital credential issued              | External      | Access digital version |
| 7.3  | Credential recorded in school system   | Certification | School has record      |
| 7.4  | Credential added to student transcript | Enrollment    | Permanent record       |
| 7.5  | Credential shared with employers       | Job Board     | Job seekers benefit    |

**Stage 8: Renewal**

| Step | Action                        | System        | User Story           |
| ---- | ----------------------------- | ------------- | -------------------- |
| 8.1  | System tracks expiration date | Certification | Know when expires    |
| 8.2  | Receive renewal reminder      | Email         | Notified of deadline |
| 8.3  | Complete continuing education | LMS           | Earn renewal credits |
| 8.4  | Submit renewal application    | External      | Apply for renewal    |
| 8.5  | Renewal recorded in system    | Certification | Status updated       |

#### 4.5.4 Supported Certifications

| Industry     | Certification | Body                           | Cost     | Renewal | Exam Format         |
| ------------ | ------------- | ------------------------------ | -------- | ------- | ------------------- |
| HVAC         | NATE          | North American Tech Excellence | $400     | 4 years | Online proctored    |
| HVAC         | EPA 608       | EPA                            | $60      | None    | In-person           |
| Welding      | AWS CW        | American Welding Society       | $350     | 3 years | Practical           |
| Electrical   | NCCER Core    | NCCER                          | $250     | 5 years | Written             |
| IT           | CompTIA A+    | CompTIA                        | $246     | None    | Online proctored    |
| IT           | Cisco CCNA    | Cisco                          | $300     | 3 years | Online proctored    |
| Healthcare   | CNA           | State/NHA                      | $110     | 2 years | Written + Practical |
| Automotive   | ASE           | ASE                            | $45/each | 5 years | Written             |
| Construction | OSHA 10       | OSHA                           | $60      | None    | Online              |
| Culinary     | ServSafe      | ServSafe                       | $15      | 3 years | Written             |

#### 4.5.5 Key Metrics

| Metric                           | Definition                        | Target  |
| -------------------------------- | --------------------------------- | ------- |
| Certification Pass Rate          | % passing on first attempt        | 90%     |
| Certification Participation Rate | % eligible students taking exams  | 85%     |
| Time to Certification            | Avg days from eligibility to cert | 30 days |
| Certification Cost Recovery      | % of fees recovered from students | 95%     |
| Retake Pass Rate                 | % passing after retake            | 85%     |
| Renewal Rate                     | % certifications renewed on time  | 90%     |

---

### 4.6 J06: Job Placement Journey

#### 4.6.1 Journey Overview

**Persona**: Graduating Student (P01), Career Services (P05)

**Goal**: Secure employment in trained field

**Duration**: 1 month to 6 months

**Success Criteria**: Student employed in relevant position

#### 4.6.2 Journey Stages

| Stage       | Steps                              | Duration  | Owner           |
| ----------- | ---------------------------------- | --------- | --------------- |
| Preparation | Career counseling, resume building | 2-4 weeks | Student         |
| Exploration | Browse jobs, research employers    | 2-4 weeks | Student         |
| Application | Apply to positions                 | Ongoing   | Student         |
| Interview   | Complete interview process         | 2-4 weeks | Student         |
| Offer       | Receive and evaluate offer         | 1 week    | Student         |
| Placement   | Accept offer, begin employment     | 1 week    | Student         |
| Follow-up   | Post-placement support             | Ongoing   | Career Services |

#### 4.6.3 Detailed Steps

**Stage 1: Preparation**

| Step | Action                         | System     | User Story              |
| ---- | ------------------------------ | ---------- | ----------------------- |
| 1.1  | Schedule career counseling     | Scheduling | Book appointment        |
| 1.2  | Complete career assessment     | Career     | Identify interests      |
| 1.3  | Create/update resume           | Resume     | Document qualifications |
| 1.4  | Get resume reviewed            | Career     | Receive feedback        |
| 1.5  | Prepare cover letter templates | Resume     | Create templates        |
| 1.6  | Set up job alert preferences   | Job Board  | Customize alerts        |
| 1.7  | Complete mock interviews       | Career     | Practice interviewing   |

**Stage 2: Exploration**

| Step | Action                  | System    | User Story             |
| ---- | ----------------------- | --------- | ---------------------- |
| 2.1  | Browse job board        | Job Board | View opportunities     |
| 2.2  | Filter by preferences   | Job Board | Narrow results         |
| 2.3  | Research employers      | Job Board | Learn about companies  |
| 2.4  | Save favorite positions | Job Board | Bookmark jobs          |
| 2.5  | Attend career fair      | Events    | Meet employers         |
| 2.6  | Network with alumni     | Alumni    | Connect with graduates |

**Stage 3: Application**

| Step | Action                   | System    | User Story       |
| ---- | ------------------------ | --------- | ---------------- |
| 3.1  | Select job to apply to   | Job Board | Choose position  |
| 3.2  | Customize application    | Job Board | Tailor resume    |
| 3.3  | Submit application       | Job Board | Send application |
| 3.4  | Track application status | Job Board | Monitor progress |
| 3.5  | Follow up on application | Job Board | Send inquiry     |

**Stage 4: Interview**

| Step | Action                       | System            | User Story            |
| ---- | ---------------------------- | ----------------- | --------------------- |
| 4.1  | Receive interview invitation | Email             | Get interview request |
| 4.2  | Schedule interview time      | Scheduling        | Set appointment       |
| 4.3  | Prepare for interview        | Career            | Use prep materials    |
| 4.4  | Complete interview           | In-person/Virtual | Attend interview      |
| 4.5  | Follow up after interview    | Email             | Send thank you        |
| 4.6  | Track interview outcome      | Job Board         | Record result         |

**Stage 5: Offer**

| Step | Action                          | System    | User Story        |
| ---- | ------------------------------- | --------- | ----------------- |
| 5.1  | Receive job offer               | Email     | Get offer details |
| 5.2  | Review offer details            | Job Board | Understand terms  |
| 5.3  | Consult career counselor        | Career    | Get advice        |
| 5.4  | Negotiate offer (if applicable) | Email     | Discuss terms     |
| 5.5  | Accept or decline offer         | Job Board | Respond to offer  |

**Stage 6: Placement**

| Step | Action                       | System    | User Story        |
| ---- | ---------------------------- | --------- | ----------------- |
| 6.1  | Complete hiring paperwork    | Employer  | Finish onboarding |
| 6.2  | Begin employment             | Employer  | Start job         |
| 6.3  | Notify school of placement   | Career    | Update status     |
| 6.4  | Receive congratulations      | Email     | Recognition       |
| 6.5  | Placement recorded in system | Placement | Official record   |

**Stage 7: Follow-up**

| Step | Action                    | System | User Story          |
| ---- | ------------------------- | ------ | ------------------- |
| 7.1  | 30-day follow-up survey   | Survey | Share experience    |
| 7.2  | 90-day outcome check      | Survey | Update status       |
| 7.3  | 6-month salary report     | Survey | Report compensation |
| 7.4  | Ongoing alumni engagement | Alumni | Stay connected      |
| 7.5  | Refer other candidates    | Alumni | Help others         |

#### 4.6.4 Job Board Features

| Feature              | Description                         | User             |
| -------------------- | ----------------------------------- | ---------------- |
| Job Search           | Filter by location, salary, skills  | Student          |
| Job Alerts           | Notifications for new matching jobs | Student          |
| Application Tracking | Monitor application status          | Student          |
| Resume Database      | Employer-accessible resume library  | Employer         |
| Employer Profiles    | Company information, culture        | Student          |
| Salary Insights      | Compensation data by role           | Student          |
| Interview Prep       | Resources for interview preparation | Student          |
| Virtual Career Fair  | Online employer events              | Student/Employer |

#### 4.6.5 Key Metrics

| Metric                   | Definition                   | Target           |
| ------------------------ | ---------------------------- | ---------------- |
| Job Placement Rate       | % employed within 6 months   | 85%              |
| Time to Placement        | Avg days to first job        | 90 days          |
| Field-Relevant Placement | % in trained field           | 80%              |
| Average Starting Salary  | Median first job salary      | Industry average |
| Offer Acceptance Rate    | % of offers accepted         | 75%              |
| Employer Satisfaction    | CSAT from employers          | 4.5/5            |
| Student Satisfaction     | CSAT on placement experience | 4.0/5            |

---

### 4.7 J07: Instructor Evaluation Journey

#### 4.7.1 Journey Overview

**Persona**: Student (P01), Instructor (P02), Program Director (P03)

**Goal**: Collect and act on student feedback about instruction

**Duration**: 2 weeks per evaluation cycle

**Success Criteria**: Actionable feedback collected and addressed

#### 4.7.2 Journey Stages

| Stage       | Steps                                     | Duration | Owner      |
| ----------- | ----------------------------------------- | -------- | ---------- |
| Preparation | Prepare evaluation forms, notify students | 1 week   | Program    |
| Collection  | Students complete evaluations             | 1 week   | Student    |
| Aggregation | Compile and analyze results               | 3 days   | System     |
| Review      | Instructor reviews feedback               | 3 days   | Instructor |
| Planning    | Create improvement plan                   | 1 week   | Instructor |
| Follow-up   | Implement improvements                    | Ongoing  | Instructor |

#### 4.7.3 Detailed Steps

**Stage 1: Preparation**

| Step | Action                            | System     | User Story          |
| ---- | --------------------------------- | ---------- | ------------------- |
| 1.1  | Evaluation period announced       | Email      | Students notified   |
| 1.2  | Evaluation forms generated        | Evaluation | Create forms        |
| 1.3  | Students receive evaluation links | Email      | Access forms        |
| 1.4  | Reminder schedule set             | Email      | Automated reminders |

**Stage 2: Collection**

| Step | Action                            | System     | User Story          |
| ---- | --------------------------------- | ---------- | ------------------- |
| 2.1  | Student accesses evaluation       | Evaluation | Log in to system    |
| 2.2  | Student rates instructor          | Evaluation | Complete ratings    |
| 2.3  | Student provides written feedback | Evaluation | Share comments      |
| 2.4  | Student submits evaluation        | Evaluation | Finalize submission |
| 2.5  | Reminder sent for incomplete      | Email      | Nudge students      |

**Stage 3: Aggregation**

| Step | Action                          | System     | User Story      |
| ---- | ------------------------------- | ---------- | --------------- |
| 3.1  | System collects responses       | Evaluation | Gather data     |
| 3.2  | System calculates averages      | Evaluation | Compute scores  |
| 3.3  | System anonymizes comments      | Evaluation | Protect privacy |
| 3.4  | System generates report         | Evaluation | Create summary  |
| 3.5  | Program Director reviews report | Evaluation | Assess results  |

**Stage 4: Review**

| Step | Action                                  | System     | User Story             |
| ---- | --------------------------------------- | ---------- | ---------------------- |
| 4.1  | Instructor receives notification        | Email      | Know results available |
| 4.2  | Instructor accesses report              | Evaluation | View results           |
| 4.3  | Instructor reviews quantitative data    | Evaluation | See scores             |
| 4.4  | Instructor reviews qualitative feedback | Evaluation | Read comments          |
| 4.5  | Instructor identifies themes            | Evaluation | Spot patterns          |

**Stage 5: Planning**

| Step | Action                                 | System    | User Story        |
| ---- | -------------------------------------- | --------- | ----------------- |
| 5.1  | Instructor meets with Program Director | In-person | Discuss feedback  |
| 5.2  | Instructor creates improvement plan    | Planning  | Outline actions   |
| 5.3  | Program Director reviews plan          | Planning  | Approve plan      |
| 5.4  | Professional development identified    | Planning  | Identify training |
| 5.5  | Goals set for next evaluation          | Planning  | Set targets       |

**Stage 6: Follow-up**

| Step | Action                             | System    | User Story         |
| ---- | ---------------------------------- | --------- | ------------------ |
| 6.1  | Instructor implements changes      | In-person | Apply improvements |
| 6.2  | Mid-cycle check-in                 | In-person | Monitor progress   |
| 6.3  | Professional development completed | Planning  | Complete training  |
| 6.4  | Evidence of improvement documented | Planning  | Gather proof       |
| 6.5  | Improvement noted in file          | HR        | Record achievement |

#### 4.7.4 Evaluation Criteria

| Category               | Questions                                            | Weight |
| ---------------------- | ---------------------------------------------------- | ------ |
| Content Knowledge      | Demonstrates expertise, answers questions accurately | 25%    |
| Teaching Effectiveness | Explains clearly, uses appropriate examples          | 25%    |
| Classroom Management   | Maintains order, manages time well                   | 15%    |
| Student Engagement     | Encourages participation, shows interest             | 20%    |
| Feedback Quality       | Provides timely, constructive feedback               | 15%    |

#### 4.7.5 Key Metrics

| Metric                                 | Definition                           | Target |
| -------------------------------------- | ------------------------------------ | ------ |
| Evaluation Completion Rate             | % of students completing evaluations | 80%    |
| Average Instructor Score               | Mean evaluation score                | 4.0/5  |
| Improvement Score Increase             | Score improvement year-over-year     | +0.2   |
| Professional Development Participation | % completing required PD             | 100%   |

---

### 4.8 J08: Equipment Maintenance Journey

#### 4.8.1 Journey Overview

**Persona**: Lab Manager (P06), Instructor (P02)

**Goal**: Maintain equipment in safe, working condition

**Duration**: Ongoing, 30 minutes to 2 weeks per issue

**Success Criteria**: Equipment operational and safe

#### 4.8.2 Journey Stages

| Stage        | Steps                            | Duration        | Owner       |
| ------------ | -------------------------------- | --------------- | ----------- |
| Detection    | Identify equipment issue         | Ongoing         | User        |
| Reporting    | Document and report problem      | 1 hour          | User        |
| Triage       | Assess and prioritize issue      | 4 hours         | Lab Manager |
| Scheduling   | Schedule maintenance             | 1 day           | Lab Manager |
| Execution    | Perform maintenance/repair       | 1 hour - 1 week | Technician  |
| Verification | Test equipment after repair      | 1 hour          | Lab Manager |
| Closure      | Close work order, update records | 1 hour          | Lab Manager |

#### 4.8.3 Detailed Steps

**Stage 1: Detection**

| Step | Action                        | System    | User Story             |
| ---- | ----------------------------- | --------- | ---------------------- |
| 1.1  | User notices equipment issue  | In-person | Observe problem        |
| 1.2  | User assesses safety          | In-person | Determine urgency      |
| 1.3  | User tags equipment if unsafe | In-person | Mark as out of service |

**Stage 2: Reporting**

| Step | Action                              | System    | User Story      |
| ---- | ----------------------------------- | --------- | --------------- |
| 2.1  | User creates maintenance request    | Equipment | Log issue       |
| 2.2  | User describes problem              | Equipment | Provide details |
| 2.3  | User uploads photos (if applicable) | Equipment | Show problem    |
| 2.4  | User specifies urgency              | Equipment | Set priority    |
| 2.5  | Lab Manager receives notification   | Equipment | Alert generated |

**Stage 3: Triage**

| Step | Action                            | System    | User Story     |
| ---- | --------------------------------- | --------- | -------------- |
| 3.1  | Lab Manager reviews request       | Equipment | Assess issue   |
| 3.2  | Lab Manager inspects equipment    | In-person | Verify problem |
| 3.3  | Lab Manager categorizes issue     | Equipment | Classify type  |
| 3.4  | Lab Manager determines priority   | Equipment | Set urgency    |
| 3.5  | Lab Manager assigns to technician | Equipment | Dispatch work  |

**Stage 4: Scheduling**

| Step | Action                         | System     | User Story     |
| ---- | ------------------------------ | ---------- | -------------- |
| 4.1  | Technician receives assignment | Equipment  | Get work order |
| 4.2  | Technician schedules work      | Scheduling | Set time       |
| 4.3  | Lab time blocked if needed     | Scheduling | Reserve space  |
| 4.4  | Parts ordered if needed        | Equipment  | Request parts  |
| 4.5  | User notified of schedule      | Email      | Inform user    |

**Stage 5: Execution**

| Step | Action                                         | System    | User Story          |
| ---- | ---------------------------------------------- | --------- | ------------------- |
| 5.1  | Technician performs maintenance                | In-person | Do work             |
| 5.2  | Technician documents work                      | Equipment | Record actions      |
| 5.3  | Technician orders additional parts (if needed) | Equipment | Request more        |
| 5.4  | Technician tests equipment                     | In-person | Verify function     |
| 5.5  | Technician updates work order                  | Equipment | Document completion |

**Stage 6: Verification**

| Step | Action                                  | System    | User Story       |
| ---- | --------------------------------------- | --------- | ---------------- |
| 6.1  | Lab Manager inspects repaired equipment | In-person | Check work       |
| 6.2  | Lab Manager tests functionality         | In-person | Verify operation |
| 6.3  | Lab Manager approves completion         | Equipment | Sign off         |
| 6.4  | Equipment marked available              | Equipment | Update status    |
| 6.5  | User notified of availability           | Email     | Inform user      |

**Stage 7: Closure**

| Step | Action                             | System    | User Story        |
| ---- | ---------------------------------- | --------- | ----------------- |
| 7.1  | Work order closed                  | Equipment | Finalize          |
| 7.2  | Cost recorded                      | Equipment | Track expense     |
| 7.3  | History updated                    | Equipment | Add to record     |
| 7.4  | Preventive maintenance rescheduled | Equipment | Set next PM       |
| 7.5  | Metrics updated                    | Analytics | Update statistics |

#### 4.8.4 Maintenance Types

| Type       | Description                    | Trigger   | Response Time |
| ---------- | ------------------------------ | --------- | ------------- |
| Emergency  | Safety issue, critical failure | Immediate | 4 hours       |
| Urgent     | Affects scheduled classes      | 1 day     | 24 hours      |
| Standard   | Non-critical repair            | 1 week    | 72 hours      |
| Preventive | Scheduled maintenance          | Calendar  | As scheduled  |
| Predictive | Data-driven maintenance        | Analytics | Planned       |

#### 4.8.5 Key Metrics

| Metric                            | Definition                        | Target             |
| --------------------------------- | --------------------------------- | ------------------ |
| Mean Time to Repair (MTTR)        | Avg time from report to repair    | 48 hours           |
| Preventive Maintenance Compliance | % PM completed on schedule        | 95%                |
| Equipment Availability            | % time equipment operational      | 95%                |
| Maintenance Cost per Equipment    | Avg maintenance cost              | <10% of value/year |
| Repeat Issue Rate                 | % issues recurring within 30 days | <5%                |
| Safety-Related Issues             | Number of safety incidents        | 0                  |

---

### 4.9 J09: Safety Training Journey

#### 4.9.1 Journey Overview

**Persona**: Student (P01), Safety Officer (P09)

**Goal**: Complete required safety training and certification

**Duration**: 1-3 days

**Success Criteria**: Safety training completed and certified

#### 4.9.2 Journey Stages

| Stage         | Steps                               | Duration | Owner   |
| ------------- | ----------------------------------- | -------- | ------- |
| Assignment    | Safety training assigned to student | 1 day    | System  |
| Notification  | Student notified of requirement     | 1 day    | System  |
| Training      | Student completes training          | 1-2 days | Student |
| Assessment    | Student takes safety assessment     | 1 day    | Student |
| Certification | Student receives certification      | 1 day    | System  |
| Compliance    | System enforces certification       | Ongoing  | System  |

#### 4.9.3 Detailed Steps

**Stage 1: Assignment**

| Step | Action                                | System     | User Story         |
| ---- | ------------------------------------- | ---------- | ------------------ |
| 1.1  | Student enrolls in program            | Enrollment | Begins program     |
| 1.2  | System identifies safety requirements | Safety     | Determine needs    |
| 1.3  | System assigns training               | Safety     | Create assignments |
| 1.4  | Safety Officer reviews assignments    | Safety     | Verify accuracy    |

**Stage 2: Notification**

| Step | Action                                   | System | User Story        |
| ---- | ---------------------------------------- | ------ | ----------------- |
| 2.1  | Student receives assignment notification | Email  | Know requirements |
| 2.2  | Student views training requirements      | Safety | See details       |
| 2.3  | Student views deadline                   | Safety | Know timeframe    |
| 2.4  | Student accesses training materials      | LMS    | Get materials     |

**Stage 3: Training**

| Step | Action                                          | System    | User Story        |
| ---- | ----------------------------------------------- | --------- | ----------------- |
| 3.1  | Student begins training module                  | LMS       | Start training    |
| 3.2  | Student completes video content                 | LMS       | Watch videos      |
| 3.3  | Student reads safety manuals                    | LMS       | Study materials   |
| 3.4  | Student completes interactive exercises         | LMS       | Practice          |
| 3.5  | Student attends in-person session (if required) | In-person | Hands-on training |

**Stage 4: Assessment**

| Step | Action                                         | System    | User Story         |
| ---- | ---------------------------------------------- | --------- | ------------------ |
| 4.1  | Student accesses assessment                    | Safety    | Start test         |
| 4.2  | Student completes written exam                 | Safety    | Take test          |
| 4.3  | Student completes practical demo (if required) | In-person | Demonstrate skills |
| 4.4  | System grades assessment                       | Safety    | Evaluate           |
| 4.5  | Student receives score                         | Safety    | Know result        |

**Stage 5: Certification**

| Step | Action                                | System    | User Story        |
| ---- | ------------------------------------- | --------- | ----------------- |
| 5.1  | System verifies passing score         | Safety    | Confirm pass      |
| 5.2  | System issues certification           | Safety    | Grant credential  |
| 5.3  | Student receives certification        | Email     | Get certificate   |
| 5.4  | Certification added to student record | Safety    | Record credential |
| 5.5  | Lab access granted                    | Equipment | Enable access     |

**Stage 6: Compliance**

| Step | Action                             | System    | User Story      |
| ---- | ---------------------------------- | --------- | --------------- |
| 6.1  | System tracks certification status | Safety    | Monitor         |
| 6.2  | System blocks access if expired    | Equipment | Enforce         |
| 6.3  | System sends renewal reminders     | Email     | Notify          |
| 6.4  | System enforces recertification    | Safety    | Require renewal |

#### 4.9.4 Safety Training Types

| Training             | Duration  | Audience        | Recertification |
| -------------------- | --------- | --------------- | --------------- |
| OSHA 10-Hour         | 10 hours  | All students    | None            |
| Lab Safety           | 2 hours   | Lab users       | Annual          |
| Equipment-Specific   | 1-4 hours | Equipment users | Annual          |
| Hazard Communication | 1 hour    | All students    | Annual          |
| Fire Safety          | 2 hours   | All students    | Annual          |
| First Aid/CPR        | 4 hours   | Lab staff       | 2 years         |

#### 4.9.5 Key Metrics

| Metric                   | Definition                     | Target |
| ------------------------ | ------------------------------ | ------ |
| Training Completion Rate | % completing required training | 100%   |
| Assessment Pass Rate     | % passing on first attempt     | 95%    |
| Time to Completion       | Avg days to complete training  | 3 days |
| Compliance Rate          | % with current certifications  | 100%   |
| Safety Incidents         | Number of incidents            | 0      |

---

### 4.10 J10: Employer Partnership Journey

#### 4.10.1 Journey Overview

**Persona**: Employer (P08), Career Services (P05)

**Goal**: Establish productive employer partnership

**Duration**: 1-3 months to establish, ongoing

**Success Criteria**: Active partnership with job placements

#### 4.10.2 Journey Stages

| Stage       | Steps                         | Duration  | Owner           |
| ----------- | ----------------------------- | --------- | --------------- |
| Discovery   | Employer expresses interest   | 1-2 weeks | Both            |
| Onboarding  | Employer set up in system     | 1 week    | Career Services |
| Activation  | Employer posts first job      | 1 week    | Employer        |
| Engagement  | Employer hires graduates      | Ongoing   | Both            |
| Partnership | Deepened relationship         | 3+ months | Both            |
| Advisory    | Employer joins advisory board | 6+ months | Both            |

#### 4.10.3 Detailed Steps

**Stage 1: Discovery**

| Step | Action                      | System         | User Story            |
| ---- | --------------------------- | -------------- | --------------------- |
| 1.1  | Employer contacts school    | Email/Phone    | Express interest      |
| 1.2  | Career Services responds    | CRM            | Initial contact       |
| 1.3  | Needs assessment conducted  | In-person/Call | Understand needs      |
| 1.4  | Partnership proposal shared | Email          | Outline benefits      |
| 1.5  | Employer agrees to proceed  | Email          | Commit to partnership |

**Stage 2: Onboarding**

| Step | Action                              | System          | User Story       |
| ---- | ----------------------------------- | --------------- | ---------------- |
| 2.1  | Employer account created            | Employer Portal | Set up account   |
| 2.2  | Employer completes profile          | Employer Portal | Add company info |
| 2.3  | Employer receives login credentials | Email           | Access portal    |
| 2.4  | Employer training conducted         | In-person/Video | Learn system     |
| 2.5  | Partnership agreement signed        | Contract        | Formalize        |

**Stage 3: Activation**

| Step | Action                                    | System    | User Story     |
| ---- | ----------------------------------------- | --------- | -------------- |
| 3.1  | Employer creates first job posting        | Job Board | Post job       |
| 3.2  | Career Services reviews posting           | Job Board | Approve        |
| 3.3  | Job published to candidates               | Job Board | Live           |
| 3.4  | Employer receives candidate notifications | Job Board | See applicants |
| 3.5  | Employer reviews candidates               | Job Board | Evaluate       |

**Stage 4: Engagement**

| Step | Action                           | System            | User Story       |
| ---- | -------------------------------- | ----------------- | ---------------- |
| 4.1  | Employer interviews candidates   | In-person/Virtual | Meet applicants  |
| 4.2  | Employer makes hiring decision   | Employer          | Decide           |
| 4.3  | Employer notifies school of hire | Job Board         | Update status    |
| 4.4  | Placement recorded               | Placement         | Document         |
| 4.5  | Employer provides feedback       | Survey            | Share experience |

**Stage 5: Partnership**

| Step | Action                           | System    | User Story          |
| ---- | -------------------------------- | --------- | ------------------- |
| 5.1  | Multiple job postings            | Job Board | Ongoing hiring      |
| 5.2  | Employer attends career fair     | Events    | Meet candidates     |
| 5.3  | Employer provides guest lectures | In-person | Share expertise     |
| 5.4  | Employer offers apprenticeships  | Placement | Develop talent      |
| 5.5  | Partnership reviewed quarterly   | Meeting   | Assess relationship |

**Stage 6: Advisory**

| Step | Action                                     | System  | User Story     |
| ---- | ------------------------------------------ | ------- | -------------- |
| 6.1  | Employer invited to advisory board         | Email   | Join board     |
| 6.2  | Employer participates in curriculum review | Meeting | Provide input  |
| 6.3  | Employer shares industry trends            | Meeting | Share insights |
| 6.4  | Employer helps shape programs              | Meeting | Influence      |
| 6.5  | Advisory board meeting documented          | Meeting | Record         |

#### 4.10.4 Partnership Levels

| Level    | Description                | Benefits                         | Commitment         |
| -------- | -------------------------- | -------------------------------- | ------------------ |
| Bronze   | Job postings only          | Access to candidates             | Post 1+ jobs/year  |
| Silver   | Job postings + career fair | Priority candidate access        | Post 3+ jobs/year  |
| Gold     | Silver + guest speaking    | Branding, advisory input         | Post 5+ jobs/year  |
| Platinum | Gold + advisory board      | Curriculum input, logo placement | Post 10+ jobs/year |

#### 4.10.5 Key Metrics

| Metric                       | Definition                      | Target       |
| ---------------------------- | ------------------------------- | ------------ |
| Employer Retention Rate      | % posting multiple times        | 70%          |
| Jobs to Hires Ratio          | % of postings resulting in hire | 60%          |
| Employer Satisfaction        | CSAT from employers             | 4.5/5        |
| Time to Fill                 | Avg days from posting to hire   | 30 days      |
| Partnership Revenue          | Revenue from partnerships       | 10% of total |
| Advisory Board Participation | % programs with active boards   | 80%          |

---

## 5. Functional Requirements

### 5.1 FR01: Program Management

#### 5.1.1 Requirements

| ID      | Requirement                     | Priority | Description                                           |
| ------- | ------------------------------- | -------- | ----------------------------------------------------- |
| FR01-01 | Create programs                 | P0       | Create new program with name, description, duration   |
| FR01-02 | Define program structure        | P0       | Set program curriculum, courses, requirements         |
| FR01-03 | Set program requirements        | P0       | Define prerequisites, skills, certifications required |
| FR01-04 | Manage program versions         | P0       | Support curriculum versioning over time               |
| FR01-05 | Set program capacity            | P1       | Define maximum students per cohort                    |
| FR01-06 | Configure program schedule      | P1       | Set start dates, duration, term structure             |
| FR01-07 | Link programs to certifications | P1       | Associate external certifications with programs       |
| FR01-08 | Manage program status           | P1       | Active, inactive, recruiting, full                    |
| FR01-09 | Export program data             | P2       | Generate reports for accreditation                    |
| FR01-10 | Program comparison              | P2       | Compare program outcomes across versions              |

#### 5.1.2 Data Model

```
Program {
  program_id: UUID (PK)
  name: String(100)
  code: String(20)
  description: Text
  category: String(50)
  duration_weeks: Integer
  start_dates: Date[]
  capacity: Integer
  status: Enum[active, inactive, recruiting, full]
  version: Integer
  created_date: DateTime
  updated_date: DateTime

  requirements: ProgramRequirement[]
  courses: ProgramCourse[]
  certifications: ProgramCertification[]
  outcomes: ProgramOutcome[]
}

ProgramRequirement {
  requirement_id: UUID (PK)
  program_id: UUID (FK)
  type: Enum[course, skill, certification, hours]
  required_item_id: UUID
  min_proficiency: Decimal
}

ProgramCourse {
  course_id: UUID (PK)
  program_id: UUID (FK)
  course_ref_id: UUID
  sequence: Integer
  required: Boolean
  alternatives: UUID[]
}
```

### 5.2 FR02: Course Management

#### 5.2.1 Requirements

| ID      | Requirement              | Priority | Description                                      |
| ------- | ------------------------ | -------- | ------------------------------------------------ |
| FR02-01 | Create courses           | P0       | Define course with name, description, credits    |
| FR02-02 | Set course prerequisites | P0       | Define required courses/skills before enrollment |
| FR02-03 | Create course sections   | P0       | Create instances with instructor, schedule, room |
| FR02-04 | Manage course materials  | P1       | Upload and organize learning materials           |
| FR02-05 | Set course capacity      | P0       | Define maximum students per section              |
| FR02-06 | Manage course schedule   | P0       | Set meeting times, locations, duration           |
| FR02-07 | Link courses to programs | P0       | Associate courses with programs                  |
| FR02-08 | Course versioning        | P1       | Track course changes over time                   |
| FR02-09 | Export course data       | P2       | Generate curriculum reports                      |
| FR02-10 | Course catalog           | P1       | Publish course information for browsing          |

#### 5.2.2 Data Model

```
Course {
  course_id: UUID (PK)
  name: String(100)
  code: String(20)
  description: Text
  credits: Decimal
  duration_hours: Integer
  prerequisites: Prerequisite[]
  created_date: DateTime
  updated_date: DateTime

  sections: CourseSection[]
  materials: CourseMaterial[]
  skills: CourseSkill[]
}

CourseSection {
  section_id: UUID (PK)
  course_id: UUID (FK)
  term: String(20)
  instructor_id: UUID
  room: String(50)
  schedule: Schedule[]
  capacity: Integer
  enrolled: Integer
  status: Enum[open, closed, full, cancelled]

  enrollments: Enrollment[]
}

Prerequisite {
  prerequisite_id: UUID (PK)
  course_id: UUID (FK)
  type: Enum[course, skill, certification]
  required_id: UUID
  min_grade: String(5)
  min_proficiency: Decimal
}
```

### 5.3 FR03: Student Information Management

#### 5.3.1 Requirements

| ID      | Requirement               | Priority | Description                                |
| ------- | ------------------------- | -------- | ------------------------------------------ |
| FR03-01 | Create student profile    | P0       | Record student demographics, contact info  |
| FR03-02 | Track enrollment history  | P0       | Record all program/course enrollments      |
| FR03-03 | Track academic progress   | P0       | Monitor grades, completion status          |
| FR03-04 | Track skills proficiency  | P0       | Record all skills assessments              |
| FR03-05 | Track certifications      | P1       | Record earned certifications               |
| FR03-06 | Manage student status     | P0       | Active, withdrawn, graduated, suspended    |
| FR03-07 | Document management       | P1       | Store transcripts, certificates, documents |
| FR03-08 | Student communication log | P1       | Record all communications                  |
| FR03-09 | Generate transcripts      | P1       | Create official academic records           |
| FR03-10 | Student dashboard         | P1       | Personalized student view                  |

#### 5.3.2 Data Model

```
Student {
  student_id: UUID (PK)
  first_name: String(50)
  last_name: String(50)
  email: String(100)
  phone: String(20)
  address: Address
  date_of_birth: Date
  gender: String(20)
  status: Enum[prospect, enrolled, active, withdrawn, graduated, suspended]
  emergency_contact: Contact
  created_date: DateTime
  updated_date: DateTime

  enrollments: Enrollment[]
  skills: SkillAssessment[]
  certifications: CertificationRecord[]
  documents: Document[]
}

StudentProgress {
  progress_id: UUID (PK)
  student_id: UUID (FK)
  program_id: UUID (FK)
  courses_completed: Integer
  courses_required: Integer
  skills_mastered: Integer
  skills_required: Integer
  completion_percentage: Decimal
  estimated_graduation: Date
  status: Enum[on_track, at_risk, behind]
}
```

### 5.4 FR04: Enrollment Management

#### 5.4.1 Requirements

| ID      | Requirement            | Priority | Description                                     |
| ------- | ---------------------- | -------- | ----------------------------------------------- |
| FR04-01 | Application submission | P0       | Accept and process student applications         |
| FR04-02 | Application review     | P0       | Review applications for eligibility             |
| FR04-03 | Admission decisions    | P0       | Make accept/deny/waitlist decisions             |
| FR04-04 | Offer management       | P0       | Generate and send admission offers              |
| FR04-05 | Enrollment processing  | P0       | Process enrollment for accepted students        |
| FR04-06 | Waitlist management    | P1       | Manage waitlist for full programs               |
| FR04-07 | Transfer processing    | P1       | Handle credit transfers from other institutions |
| FR04-08 | Withdrawal processing  | P0       | Process student withdrawals                     |
| FR04-09 | Re-enrollment          | P1       | Handle returning student enrollment             |
| FR04-10 | Enrollment reporting   | P1       | Generate enrollment reports                     |

#### 5.4.2 Data Model

```
Application {
  application_id: UUID (PK)
  applicant_id: UUID
  program_id: UUID (FK)
  status: Enum[draft, submitted, under_review, accepted, denied, waitlisted, withdrawn]
  submitted_date: DateTime
  reviewed_date: DateTime
  decision_date: DateTime

  personal_info: PersonalInfo
  academic_history: AcademicHistory[]
  documents: ApplicationDocument[]
  interview: ApplicationInterview
  decision: ApplicationDecision
}

Enrollment {
  enrollment_id: UUID (PK)
  student_id: UUID (FK)
  section_id: UUID (FK)
  status: Enum[enrolled, dropped, completed, withdrawn]
  enrollment_date: DateTime
  completion_date: DateTime
  grade: String(5)
  attendance_percentage: Decimal

  payment_status: PaymentStatus
  holds: EnrollmentHold[]
}
```

### 5.5 FR05: Skills Assessment Management

#### 5.5.1 Requirements

| ID      | Requirement                | Priority | Description                                        |
| ------- | -------------------------- | -------- | -------------------------------------------------- |
| FR05-01 | Define skill rubrics       | P0       | Create detailed assessment criteria for each skill |
| FR05-02 | Schedule assessments       | P0       | Book student-instructor assessment sessions        |
| FR05-03 | Conduct assessments        | P0       | Instructors evaluate student practical skills      |
| FR05-04 | Record assessment results  | P0       | Document scores and proficiency levels             |
| FR05-05 | Provide feedback           | P1       | Generate detailed feedback reports for students    |
| FR05-06 | Track skill progression    | P1       | Monitor skill development over time                |
| FR05-07 | Generate skill transcripts | P1       | Create official skill competency records           |
| FR05-08 | Manage retesting           | P1       | Handle re-assessment requests and scheduling       |
| FR05-09 | Inter-rater reliability    | P2       | Ensure consistency across different assessors      |
| FR05-10 | Skills gap analysis        | P2       | Identify areas where students need improvement     |

#### 5.5.2 Data Model

```
SkillRubric {
  rubric_id: UUID (PK)
  skill_name: String(100)
  skill_category: String(50)
  description: Text

  criteria: AssessmentCriteria[]
  proficiency_levels: ProficiencyLevel[]
  assessment_duration_minutes: Integer
}

AssessmentCriteria {
  criteria_id: UUID (PK)
  rubric_id: UUID (FK)
  name: String(100)
  description: Text
  weight: Decimal
  max_score: Decimal
}

AssessmentCriteria {
  criteria_id: UUID (PK)
  rubric_id: UUID (FK)
  name: String(100)
  description: Text
  weight: Decimal
  max_score: Decimal
}

SkillAssessment {
  assessment_id: UUID (PK)
  student_id: UUID (FK)
  rubric_id: UUID (FK)
  instructor_id: UUID (FK)
  scheduled_date: DateTime
  completed_date: DateTime
  status: Enum[scheduled, in_progress, completed, cancelled]

  criteria_scores: CriteriaScore[]
  overall_score: Decimal
  proficiency_level: String(20)
  instructor_notes: Text
}

CriteriaScore {
  score_id: UUID (PK)
  assessment_id: UUID (FK)
  criteria_id: UUID (FK)
  score: Decimal
  notes: Text
}

ProficiencyLevel {
  level_id: UUID (PK)
  rubric_id: UUID (FK)
  level_name: String(20)
  min_score: Decimal
  max_score: Decimal
  description: Text
}
```

### 5.6 FR06: Certification Management

#### 5.6.1 Requirements

| ID      | Requirement                     | Priority | Description                                          |
| ------- | ------------------------------- | -------- | ---------------------------------------------------- |
| FR06-01 | Track certification eligibility | P0       | Determine which certifications students qualify for  |
| FR06-02 | Manage exam registration        | P0       | Handle external certification exam bookings          |
| FR06-03 | Record exam results             | P0       | Store pass/fail and score information                |
| FR06-04 | Issue credentials               | P1       | Generate digital and physical certificates           |
| FR06-05 | Track expiration dates          | P1       | Monitor certification validity periods               |
| FR06-06 | Manage renewals                 | P1       | Handle recertification processes                     |
| FR06-07 | Export certification data       | P2       | Generate reports for employers and accreditation     |
| FR06-08 | Sync with certifying bodies     | P2       | Integrate with external certification systems        |
| FR06-09 | Credential verification         | P2       | Allow employers to verify certification authenticity |
| FR06-10 | Blockchain credentials          | P3       | Issue tamper-proof digital credentials               |

#### 5.6.2 Data Model

```
CertificationProgram {
  certification_id: UUID (PK)
  name: String(100)
  code: String(20)
  issuing_body: String(100)
  description: Text
  validity_period_months: Integer
  renewal_required: Boolean
  exam_cost: Decimal
  prep_materials: CertificationMaterial[]
}

CertificationRecord {
  record_id: UUID (PK)
  student_id: UUID (FK)
  certification_id: UUID (FK)
  exam_date: Date
  exam_result: Enum[pending, passed, failed]
  score: Decimal
  issue_date: Date
  expiration_date: Date
  credential_number: String(50)
  status: Enum[active, expired, pending_renewal]

  documents: CertificationDocument[]
  renewal_history: CertificationRenewal[]
}

CertificationExam {
  exam_id: UUID (PK)
  student_id: UUID (FK)
  certification_id: UUID (FK)
  scheduled_date: DateTime
  location: String(200)
  status: Enum[registered, completed, cancelled]
  registration_number: String(50)
  cost: Decimal
}
```

### 5.7 FR07: Lab and Equipment Management

#### 5.7.1 Requirements

| ID      | Requirement                     | Priority | Description                                  |
| ------- | ------------------------------- | -------- | -------------------------------------------- |
| FR07-01 | Catalog equipment               | P0       | Maintain inventory of all lab equipment      |
| FR07-02 | Track equipment status          | P0       | Monitor availability and condition           |
| FR07-03 | Manage equipment bookings       | P0       | Handle student equipment reservations        |
| FR07-04 | Check-in/check-out process      | P0       | Track equipment usage                        |
| FR07-05 | Schedule maintenance            | P1       | Plan preventive maintenance                  |
| FR07-06 | Track maintenance history       | P1       | Record all repairs and service               |
| FR07-07 | Manage equipment requests       | P1       | Handle purchase requests for new equipment   |
| FR07-08 | Track equipment costs           | P1       | Monitor acquisition and maintenance expenses |
| FR07-09 | Equipment utilization analytics | P2       | Report on equipment usage patterns           |
| FR07-10 | Depreciation tracking           | P2       | Calculate equipment value over time          |

#### 5.7.2 Data Model

```
Equipment {
  equipment_id: UUID (PK)
  name: String(100)
  sku: String(50)
  category: String(50)
  manufacturer: String(100)
  model: String(100)
  serial_number: String(100)
  location: String(100)
  purchase_date: Date
  purchase_cost: Decimal
  status: Enum[available, in_use, maintenance, broken, retired]

  certifications_required: CertificationRequirement[]
  maintenance_schedule: MaintenanceSchedule[]
  usage_history: EquipmentUsage[]
}

EquipmentBooking {
  booking_id: UUID (PK)
  equipment_id: UUID (FK)
  student_id: UUID (FK)
  instructor_id: UUID (FK)
  start_time: DateTime
  end_time: DateTime
  purpose: Text
  status: Enum[pending, confirmed, completed, cancelled, no_show]

  checkout_record: EquipmentCheckout
}

EquipmentCheckout {
  checkout_id: UUID (PK)
  booking_id: UUID (FK)
  checked_out_at: DateTime
  checked_out_by: UUID
  condition_at_checkout: String(50)
  due_back_at: DateTime
  checked_in_at: DateTime
  condition_at_return: String(50)
  damage_notes: Text
  charges_applied: Decimal
}
```

### 5.8 FR08: Billing and Financial Aid

#### 5.8.1 Requirements

| ID      | Requirement                | Priority | Description                                     |
| ------- | -------------------------- | -------- | ----------------------------------------------- |
| FR08-01 | Generate tuition invoices  | P0       | Create billing statements for programs          |
| FR08-02 | Process payments           | P0       | Handle tuition and fee payments                 |
| FR08-03 | Manage payment plans       | P0       | Support installment payment options             |
| FR08-04 | Track financial aid        | P1       | Process grants, scholarships, and loans         |
| FR08-05 | Apply aid to accounts      | P1       | Reduce student balances with aid                |
| FR08-06 | Generate financial reports | P1       | Produce revenue and accounts receivable reports |
| FR08-07 | Process refunds            | P1       | Handle withdrawal refunds                       |
| FR08-08 | Manage discounts           | P2       | Apply promotional and institutional discounts   |
| FR08-09 | Third-party billing        | P2       | Bill employers for sponsored students           |
| FR08-10 | Tax document generation    | P2       | Create tax forms for aid and scholarships       |

#### 5.8.2 Data Model

```
StudentAccount {
  account_id: UUID (PK)
  student_id: UUID (FK)
  balance: Decimal
  credit_limit: Decimal
  payment_status: Enum[current, past_due, delinquent, suspended]
  created_date: DateTime

  invoices: Invoice[]
  payments: Payment[]
  financial_aid: FinancialAidAward[]
}

Invoice {
  invoice_id: UUID (PK)
  account_id: UUID (FK)
  enrollment_id: UUID (FK)
  invoice_date: Date
  due_date: Date
  amount: Decimal
  status: Enum[draft, sent, paid, partial, overdue, void]

  line_items: InvoiceLineItem[]
  payments: InvoicePayment[]
}

FinancialAidAward {
  award_id: UUID (PK)
  student_id: UUID (FK)
  aid_type: Enum[grant, scholarship, loan, work_study]
  source: String(100)
  amount: Decimal
  award_year: String(10)
  start_date: Date
  end_date: Date
  status: Enum[offered, accepted, disbursed, cancelled]
}
```

### 5.9 FR09: Job Placement and Career Services

#### 5.9.1 Requirements

| ID      | Requirement                | Priority | Description                                          |
| ------- | -------------------------- | -------- | ---------------------------------------------------- |
| FR09-01 | Manage job postings        | P0       | Post and organize job opportunities                  |
| FR09-02 | Student resume management  | P0       | Store and manage student resumes                     |
| FR09-03 | Application tracking       | P0       | Track student job applications                       |
| FR09-04 | Interview scheduling       | P1       | Coordinate interviews between students and employers |
| FR09-05 | Employer portal            | P1       | Provide employer self-service capabilities           |
| FR09-06 | Career counseling          | P1       | Schedule and track career counseling sessions        |
| FR09-07 | Track placement outcomes   | P1       | Record employment status and salary data             |
| FR09-08 | Generate placement reports | P1       | Produce employment statistics                        |
| FR09-09 | Career fair management     | P2       | Organize and manage career events                    |
| FR09-10 | Alumni networking          | P2       | Facilitate alumni-student connections                |

#### 5.9.2 Data Model

```
JobPosting {
  job_id: UUID (PK)
  employer_id: UUID (FK)
  title: String(100)
  description: Text
  requirements: Text
  salary_range: String(50)
  location: String(200)
  job_type: Enum[full_time, part_time, contract, internship]
  posted_date: DateTime
  expiration_date: Date
  status: Enum[draft, active, closed, expired]

  applications: JobApplication[]
}

JobApplication {
  application_id: UUID (PK)
  job_id: UUID (FK)
  student_id: UUID (FK)
  submitted_date: DateTime
  status: Enum[submitted, reviewed, interviewing, offered, accepted, rejected]
  resume_version: UUID
  cover_letter: Text
  employer_notes: Text
}

Employer {
  employer_id: UUID (PK)
  company_name: String(200)
  contact_name: String(100)
  contact_email: String(100)
  contact_phone: String(20)
  website: String(200)
  industry: String(100)
  size: String(20)
  partnership_level: Enum[bronze, silver, gold, platinum]
  created_date: DateTime
}
```

### 5.10 FR10: Safety Management

#### 5.10.1 Requirements

| ID      | Requirement                | Priority | Description                                   |
| ------- | -------------------------- | -------- | --------------------------------------------- |
| FR10-01 | Define safety requirements | P0       | Establish safety rules for each lab/equipment |
| FR10-02 | Track safety training      | P0       | Record completed safety certifications        |
| FR10-03 | Enforce safety compliance  | P0       | Block access without required certifications  |
| FR10-04 | Manage safety incidents    | P1       | Document and track safety incidents           |
| FR10-05 | Generate safety reports    | P1       | Produce compliance reports                    |
| FR10-06 | Safety audit management    | P1       | Schedule and conduct safety audits            |
| FR10-07 | Emergency procedures       | P2       | Document and communicate emergency protocols  |
| FR10-08 | Safety equipment tracking  | P2       | Monitor PPE and safety equipment inventory    |
| FR10-09 | Incident investigation     | P2       | Document root cause analysis                  |
| FR10-10 | Safety training reminders  | P2       | Alert users of expiring certifications        |

#### 5.10.2 Data Model

```
SafetyTraining {
  training_id: UUID (PK)
  name: String(100)
  code: String(20)
  description: Text
  duration_minutes: Integer
  validity_months: Integer
  required_for: RequirementLink[]

  content_modules: TrainingModule[]
  assessments: SafetyAssessment[]
}

SafetyCertification {
  certification_id: UUID (PK)
  student_id: UUID (FK)
  training_id: UUID (FK)
  completed_date: DateTime
  expires_date: DateTime
  score: Decimal
  status: Enum[active, expired, pending]
  instructor_id: UUID (FK)
}

SafetyIncident {
  incident_id: UUID (PK)
  reported_by: UUID
  incident_date: DateTime
  location: String(200)
  type: Enum[injury, near_miss, equipment_damage, chemical_spill, fire]
  severity: Enum[minor, moderate, serious, severe]
  description: Text
  status: Enum[reported, investigating, resolved, closed]

  affected_persons: IncidentPerson[]
  root_cause: Text
  corrective_actions: CorrectiveAction[]
}
```

### 5.11 FR11: Instructor Management

#### 5.11.1 Requirements

| ID      | Requirement                      | Priority | Description                                  |
| ------- | -------------------------------- | -------- | -------------------------------------------- |
| FR11-01 | Manage instructor profiles       | P0       | Store instructor information and credentials |
| FR11-02 | Track instructor credentials     | P0       | Monitor certification validity               |
| FR11-03 | Assign instructors to courses    | P0       | Link instructors to course sections          |
| FR11-04 | Schedule instructor availability | P1       | Manage instructor time slots                 |
| FR11-05 | Collect instructor evaluations   | P1       | Gather student feedback                      |
| FR11-06 | Generate performance reports     | P1       | Produce instructor analytics                 |
| FR11-07 | Track professional development   | P1       | Record training and certifications           |
| FR11-08 | Manage instructor contracts      | P2       | Handle contract terms and renewals           |
| FR11-09 | Payroll integration              | P2       | Calculate compensation based on hours        |
| FR11-10 | Instructor directory             | P2       | Publish instructor information for students  |

### 5.12 FR12: Attendance Tracking

#### 5.12.1 Requirements

| ID      | Requirement                     | Priority | Description                            |
| ------- | ------------------------------- | -------- | -------------------------------------- |
| FR12-01 | Record class attendance         | P0       | Log student presence for each session  |
| FR12-02 | Track lab attendance            | P0       | Monitor hands-on session participation |
| FR12-03 | Generate attendance reports     | P1       | Produce attendance summaries           |
| FR12-04 | Alert on low attendance         | P1       | Notify staff of at-risk students       |
| FR12-05 | Calculate attendance percentage | P1       | Compute completion metrics             |
| FR12-06 | Handle make-up sessions         | P2       | Track alternative attendance           |
| FR12-07 | Export attendance data          | P2       | Generate reports for compliance        |
| FR12-08 | Biometric integration           | P3       | Support fingerprint/face recognition   |

### 5.13 FR13: Program Outcomes Assessment

#### 5.13.1 Requirements

| ID      | Requirement                     | Priority | Description                          |
| ------- | ------------------------------- | -------- | ------------------------------------ |
| FR13-01 | Define outcome metrics          | P0       | Establish program success indicators |
| FR13-02 | Collect graduate data           | P1       | Gather post-graduation information   |
| FR13-03 | Track employment outcomes       | P1       | Monitor job placement statistics     |
| FR13-04 | Track salary outcomes           | P1       | Record earnings data                 |
| FR13-05 | Conduct employer surveys        | P1       | Gather employer feedback             |
| FR13-06 | Generate outcome reports        | P1       | Produce accreditation reports        |
| FR13-07 | Benchmark against industry      | P2       | Compare with industry standards      |
| FR13-08 | Continuous improvement tracking | P2       | Document program enhancements        |

### 5.14 FR14: Alumni Management

#### 5.14.1 Requirements

| ID      | Requirement             | Priority | Description                                |
| ------- | ----------------------- | -------- | ------------------------------------------ |
| FR14-01 | Maintain alumni records | P0       | Store graduate contact and employment info |
| FR14-02 | Alumni communication    | P1       | Send newsletters and updates               |
| FR14-03 | Mentor matching         | P1       | Connect alumni with current students       |
| FR14-04 | Alumni events           | P2       | Organize reunion and networking events     |
| FR14-05 | Alumni donations        | P2       | Track contributions and fundraising        |
| FR14-06 | Alumni job postings     | P2       | Enable alumni to post jobs                 |

### 5.15 FR15: Reporting and Analytics

#### 5.15.1 Requirements

| ID      | Requirement           | Priority | Description                                  |
| ------- | --------------------- | -------- | -------------------------------------------- |
| FR15-01 | Enrollment reports    | P0       | Generate enrollment statistics               |
| FR15-02 | Financial reports     | P0       | Produce revenue and billing reports          |
| FR15-03 | Outcome reports       | P0       | Create employment outcome summaries          |
| FR15-04 | Compliance reports    | P1       | Generate regulatory compliance documentation |
| FR15-05 | Custom report builder | P1       | Allow users to create custom reports         |
| FR15-06 | Dashboard creation    | P1       | Build visual analytics dashboards            |
| FR15-07 | Report scheduling     | P2       | Automate report delivery                     |
| FR15-08 | Data export           | P2       | Export data in various formats               |

---

## 6. Non-Functional Requirements

### 6.1 NFR01: Availability

| Requirement                           | Target         | Measurement                       |
| ------------------------------------- | -------------- | --------------------------------- |
| Platform uptime during business hours | 99.9%          | Minutes available / Total minutes |
| Platform uptime 24/7                  | 99.5%          | Minutes available / Total minutes |
| Scheduled maintenance windows         | <4 hours/month | Total maintenance time            |
| Incident response time                | <15 minutes    | Time to acknowledge               |
| Critical issue resolution             | <4 hours       | Time to restore                   |

### 6.2 NFR02: Response Time

| Requirement             | Target      | Measurement         |
| ----------------------- | ----------- | ------------------- |
| Page load time          | <2 seconds  | Time to interactive |
| API response time (P95) | <500ms      | 95th percentile     |
| Search results          | <1 second   | Query to results    |
| Report generation       | <30 seconds | Request to delivery |
| File upload (10MB)      | <30 seconds | Start to completion |

### 6.3 NFR03: Scalability

| Requirement           | Target  | Measurement                  |
| --------------------- | ------- | ---------------------------- |
| Concurrent users      | 5,000+  | Simultaneous active sessions |
| Students per instance | 10,000+ | Total student records        |
| Enrollments per term  | 50,000+ | Enrollment transactions      |
| Assessments per day   | 10,000+ | Assessment transactions      |
| File storage          | 10 TB+  | Total stored data            |

### 6.4 NFR04: Data Security

| Requirement                | Target                | Measurement           |
| -------------------------- | --------------------- | --------------------- |
| Data encryption at rest    | AES-256               | Storage encryption    |
| Data encryption in transit | TLS 1.3+              | Transport encryption  |
| Access control             | RBAC with MFA         | Authentication method |
| Session timeout            | 30 minutes inactivity | Session duration      |
| Password policy            | 12 chars, complexity  | Password requirements |
| Audit logging              | 100% of access events | Log coverage          |

### 6.5 NFR05: Compliance

| Requirement      | Standard         | Measurement         |
| ---------------- | ---------------- | ------------------- |
| Data retention   | 7 years minimum  | Retention policy    |
| Right to erasure | GDPR compliance  | Request fulfillment |
| Data portability | GDPR compliance  | Export capability   |
| Accessibility    | WCAG 2.1 AA      | Compliance audit    |
| Accreditation    | Program-specific | Documentation ready |

## 8. Compliance and Regulatory Constraints

### 8.1 CC01: Workforce Innovation and Opportunity Act (WIOA)

**Authority:** U.S. Department of Labor, Employment and Training Administration (ETA)

**Scope:** Applies to programs receiving WIOA funding or serving WIOA participants

**Requirements:**

#### 8.1.1 Individualized Career Services

- Core services: orientation, job counseling, career and vocational information, referral for training
- Individualized services: comprehensive assessments, service strategy development, job placement
- Training services: approved training programs with payment based on participant progress

#### 8.1.2 Eligible Trainee Identification

- Age requirements (15+ for youth, 18+ for adults)
- Priority populations: low-income individuals, basic skills deficient, recipients of public assistance
- Dislocated workers certification

#### 8.1.3 Performance Accountability

- Measurable Skill Gains (MSG) tracking
- Secondary indicators: literacy improvement, credential attainment
- First-year employment rates (quarter after quarter of exit)
- Second-year employment rates
- Median earnings in first and second year after exit
- Program effectiveness in obtaining employment in recognized industry sectors
- Competency-based credential attainment rates

#### 8.1.4 Reporting Requirements

- Performance reports to ETA via ETA 91 report
- Program Year (PY) reporting periods
- Data disaggregation by participant subgroups
- Sanction calculations and enforcement

#### 8.1.5 System Support

- Eligible trainee status tracking
- Priority population identification
- Performance measure calculation and reporting
- MSG documentation and verification
- Credential attainment tracking
- Employment outcome tracking (6 months, 12 months post-exit)

---

### 8.2 CC02: Carl D. Perkins Career and Technical Education Act (Perkins V)

**Authority:** U.S. Department of Education, Office of Career, Technical, and Adult Education (OCTAE)

**Scope:** Applies to secondary and postsecondary CTE programs receiving Perkins funding

**Requirements:**

#### 8.2.1 State Plan Requirements

- Alignment with state CTE plan (approved every 4 years)
- Career and Technical Student Organizations (CTSO) integration
- Industry advisory committee involvement
- Program of Study (POS) definition and alignment

#### 8.2.2 Program of Study (POS) Components

- Secondary education component
- Postsecondary education component
- Rigorous and relevant curriculum
- Industry-recognized credentials
- Work-based learning experiences
- Career guidance and academic counseling
- Technical skill attainment measurement
- Industry certification/credentials tracking

#### 8.2.3 Core Indicators of Performance

| Indicator                       | Description                                             | Target Setting   |
| ------------------------------- | ------------------------------------------------------- | ---------------- |
| Non-placement rate              | % not enrolled in postsecondary OR military OR employed | State-determined |
| Secondary rigor                 | % in rigorous secondary CTE courses                     | State-determined |
| Secondary rigor & relevance     | % in CTE courses aligned to postsecondary               | State-determined |
| Postsecondary rigor             | % in rigorous postsecondary CTE courses                 | State-determined |
| Postsecondary rigor & relevance | % in CTE courses aligned to labor market needs          | State-determined |
| Technical skill attainment      | % demonstrating skill attainment                        | State-determined |

#### 8.2.4 Accountability and Improvement

- Local performance reports (annual)
- State performance reports (annual)
- Comprehensive local performance reports (triennial)
- Comprehensive local evaluations (triennial)
- Program improvement plans for underperforming programs

#### 8.2.5 Equitable Participation

- Equal access for all students regardless of gender, race, disability, English proficiency
- Gender non-neutral program monitoring
- Remediation for substantial program differences (SPD)
- Disaggregated data collection by subgroup

#### 8.2.6 System Support

- POS definition and tracking
- CTSO participation tracking
- Work-based learning documentation
- Technical skill attainment tracking
- Performance indicator calculation
- Equity analysis and reporting
- Subgroup disaggregation
- State plan alignment documentation

---

### 8.3 CC03: Title IX of the Education Amendments of 1972

**Authority:** U.S. Department of Education, Office for Civil Rights (OCR)

**Scope:** Applies to all education programs receiving federal financial assistance

**Requirements:**

#### 8.3.1 Nondiscrimination Requirements

- No discrimination based on sex in any educational program
- Equal access to CTE programs traditionally dominated by one sex
- Equal treatment in program quality, resources, and opportunities
- Equal scholarship and financial aid opportunities

#### 8.3.2 Gender Non-Neutral Program Monitoring

- Annual data collection on enrollment by gender
- Program-level analysis for gender imbalances
- Substantial Program Difference (SPD) identification
- Remediation requirements for SPD findings

#### 8.3.3 Sexual Harassment Prevention

- Designated Title IX Coordinator appointment
- Grievance procedures for sexual harassment complaints
- Training for staff and students
- Prevention programs and awareness campaigns

#### 8.3.4 System Support

- Enrollment data by gender and program
- Gender disparity analysis
- SPD documentation and remediation tracking
- Complaint management workflow
- Coordinator assignment and contact management
- Training completion tracking

---

### 8.4 CC04: Americans with Disabilities Act (ADA) and Section 504

**Authority:** U.S. Department of Education OCR, Department of Justice

**Scope:** Applies to all educational programs and facilities

**Requirements:**

#### 8.4.1 Equal Access Requirements

- Physical accessibility of facilities and labs
- Program accessibility and modifications
- Reasonable accommodations for students with disabilities
- Auxiliary aids and services (interpreters, captioning)

#### 8.4.2 Documentation Requirements

- Individualized Accommodation Plans (IAP)
- Disability verification documentation
- Accommodation request and approval workflows
- Confidential record-keeping

#### 8.4.3 CTE-Specific Accommodations

- Modified equipment or adaptive tools
- Extended time for practical assessments
- Alternative demonstration methods
- Lab assistant support

#### 8.4.4 System Support

- Accommodation request management
- IAP creation and tracking
- Faculty notification of accommodations
- Accessibility audit documentation
- Equipment modification tracking

---

### 8.5 CC05: Occupational Safety and Health Administration (OSHA)

**Authority:** U.S. Department of Labor, Occupational Safety and Health Administration

**Scope:** Applies to all training facilities with employees and student workers

**Requirements:**

#### 8.5.1 Training Facility Safety Standards

- Bloodborne pathogens standard (29 CFR 1910.1030)
- Hazard communication standard (29 CFR 1910.1200)
- Personal protective equipment (29 CFR 1910.132)
- Machine guarding (29 CFR 1910.212)
- Electrical safety (29 CFR 1910.303)
- Lockout/tagout (29 CFR 1910.147)

#### 8.5.2 Student-Specific Safety Requirements

- Age-appropriate safety training
- OSHA 10-hour certification for construction programs
- OSHA 30-hour certification for supervisory training
- Hazardous operations restrictions for minors

#### 8.5.3 Recordkeeping Requirements

- OSHA 300 log of work-related injuries and illnesses
- OSHA 301 incident reports
- OSHA 300A annual summary
- Training record retention (3-5 years)

#### 8.5.4 System Support

- Safety training module integration
- OSHA certification tracking
- Incident reporting workflow
- OSHA form generation
- Exposed employees list maintenance
- Injury/illness recordkeeping

---

### 8.6 CC06: Family Educational Rights and Privacy Act (FERPA)

**Authority:** U.S. Department of Education, Family Policy Compliance Office

**Scope:** Applies to all educational institutions receiving federal funding

**Requirements:**

#### 8.6.1 Student Rights

- Right to inspect and review education records
- Right to request amendment of records
- Right to consent to disclosure of personally identifiable information
- Right to file complaints with the Department of Education

#### 8.6.2 Directory Information Management

- Definition of directory information by institution
- Opt-out mechanism for students
- Disclosure limitations and procedures

#### 8.6.3 School Official Exception

- Definition of school officials with legitimate educational interest
- Data sharing protocols
- Confidentiality agreements for contractors

#### 8.6.4 System Support

- Education record access controls
- Directory information flag management
- Student opt-out tracking
- Disclosure consent management
- Audit trail for record access

---

### 8.7 CC07: State Workforce Development Board Requirements

**Authority:** State Workforce Development Boards (varies by state)

**Scope:** Applies to programs participating in state workforce systems

**Requirements:**

#### 8.7.1 State-Specific Programs

- State grant program compliance
- State CTE standards alignment
- State workforce data system integration
- State reporting requirements

#### 8.7.2 One-Stop Career Center Integration

- Referral processes
- Shared data systems
- Co-location agreements

#### 8.7.3 System Support

- State-specific configuration
- Referral tracking
- Data exchange with state systems
- State reporting generation

---

### 8.8 CC08: Accreditation Standards

**Authority:** Various Accrediting Bodies (ACICS, DEAC, ACCSC, State Agencies)

**Scope:** Applies to accredited programs

**Requirements:**

#### 8.8.1 Common Accreditation Requirements

- Mission and objectives documentation
- Program effectiveness measurement
- Student learning outcomes assessment
- Faculty qualifications verification
- Facilities and equipment standards
- Financial stability evidence
- Student services documentation

#### 8.8.2 Program-Specific Accreditation

- ABET (engineering and technology)
- CAAHEP (health sciences)
- ACBSP (business programs)
- State nursing program approval
- State cosmetology program approval

#### 8.8.3 System Support

- Self-study report generation
- Evidence collection and organization
- Indicator calculation and trend analysis
- Survey preparation tools
- Corrective action tracking

---

### 8.9 CC09: Financial Aid Compliance

**Authority:** U.S. Department of Education, Federal Student Aid (FSA)

**Scope:** Applies to institutions participating in Title IV programs

\*\*Requirements:

#### 8.9.1 Title IV Program Participation

- FAFSA processing and verification
- Eligibility determination
- Award packaging and notification
- Disbursement procedures

#### 8.9.2 Return of Title IV Funds (R2T4)

- Withdrawal date determination
- Earnings calculation
- Return amount calculation
- Return procedures and timelines

#### 8.9.3 Cohort Default Rate

- Default tracking
- Calculation methodology
- Improvement plan requirements

#### 8.9.4 System Support

- Financial aid application integration
- Eligibility tracking
- Disbursement scheduling
- R2T4 calculation tools
- Default tracking

---

### 8.10 CC10: Cybersecurity and Data Protection

**Authority:** NIST, State Data Protection Laws

**Scope:** Applies to all system operations

**Requirements:**

#### 8.10.1 NIST Cybersecurity Framework

- Identify: Asset management, risk assessment
- Protect: Access control, awareness training, data protection
- Detect: Anomalies, continuous monitoring
- Respond: Incident response planning
- Recover: Recovery planning, improvements

#### 8.10.2 State Data Breach Notification

- 50-state breach notification compliance
- Varying notification timeframes (7 days to 45 days)
- Consumer notification requirements
- Regulatory notification requirements

#### 8.10.3 System Support

- Asset inventory management
- Vulnerability scanning integration
- Incident response workflow
- Breach notification templates
- State-specific requirement configuration

---

## 9. Integration Requirements

### 9.1 IR01: Learning Management System (LMS) Integration

#### 9.1.1 Required Integrations

- Canvas LMS
- Blackboard Learn
- Moodle
- D2L Brightspace
- Schoology

#### 9.1.2 Integration Points

- User synchronization (students, instructors)
- Course enrollment data
- Grade book integration
- Assignment submission
- Discussion participation
- Learning analytics

#### 9.1.3 Technical Specifications

- LTI 1.3 Advantage support
- REST API endpoints
- OAuth 2.0 authentication
- Webhook event notifications

---

### 9.2 IR02: Certification Body Integrations

#### 9.2.1 Supported Certification Bodies

- CompTIA (A+, Network+, Security+)
- AWS (Certified Solutions Architect, etc.)
- Microsoft (Azure, Office 365)
- Cisco (CCNA, CCNP)
- NCCER (Construction)
- AWS (Welding certifications)
- NHA (Healthcare certifications)
- ASE (Automotive)
- ServSafe (Food safety)

#### 9.2.2 Integration Capabilities

- Exam scheduling APIs
- Eligibility verification
- Exam result retrieval
- Credential verification
- Renewal notifications

---

### 9.3 IR03: HRIS and Payroll Integration

#### 9.3.1 Supported Systems

- Workday
- ADP Workforce Now
- UKG (Ultimate Kronos Group)
- BambooHR
- Gusto

#### 9.3.2 Integration Points

- Instructor time tracking
- Payroll data exchange
- Benefits enrollment
- Tax document generation

---

### 9.4 IR04: State Workforce System Integration

#### 9.4.1 Integration Requirements

- State Longitudinal Data Systems (SLDS)
- One-Stop Career Center systems
- Unemployment insurance data systems
- Apprenticeship management systems

#### 9.4.2 Data Exchange Standards

- National Occupational Information Exchange (NOIE)
- Common Education Data Standards (CEDS)
- National Skills Repository

---

### 9.5 IR05: Job Board Integrations

#### 9.5.1 Supported Job Boards

- Indeed
- LinkedIn Jobs
- Glassdoor
- CareerBuilder
- Snagajob (hourly positions)
- State workforce job banks

#### 9.5.2 Integration Capabilities

- Job posting syndication
- Candidate profile export
- Application tracking integration
- Employer relationship management

---

### 9.6 IR06: Financial Aid and Student Information System Integration

#### 9.6.1 FAFSA Integration

- Federal School Code lookup
- Expected Family Contribution (EFC) retrieval
- Award notification generation

#### 9.6.2 SIS Integrations

- Ellucian Banner
- PeopleSoft Campus Solutions
- Oracle Student Cloud
- Jenzabar

---

## 10. Data Model Expectations

### 10.1 DM01: Core Entity Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                     STUDENT ENTITY                          │
├─────────────────────────────────────────────────────────────┤
│ student_id: UUID (PK)                                       │
│ first_name: String(100)                                     │
│ last_name: String(100)                                      │
│ date_of_birth: Date                                        │
│ ssn_last_4: String(4)                                       │
│ email: String(255)                                          │
│ phone: String(20)                                           │
│ address: AddressEntity                                     │
│ created_at: DateTime                                        │
│ updated_at: DateTime                                        │
│                                                             │
│ → enrollments: Enrollment[]                                │
│ → certifications_earned: CertificationEarned[]             │
│ → skills_assessments: SkillsAssessment[]                   │
│ → safety_certifications: SafetyCertification[]             │
│ → attendance_records: AttendanceRecord[]                   │
│ → financial_accounts: StudentFinancialAccount[]            │
│ → job_placements: JobPlacement[]                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    PROGRAM ENTITY                           │
├─────────────────────────────────────────────────────────────┤
│ program_id: UUID (PK)                                       │
│ program_code: String(50)                                    │
│ program_name: String(255)                                   │
│ program_type: Enum[certificate, diploma, apprenticeship]    │
│ cip_code: String(20)                                        │
│ duration_weeks: Integer                                     │
│ total_credits: Decimal                                       │
│ status: Enum[active, inactive, deprecated]                  │
│ created_at: DateTime                                        │
│ updated_at: DateTime                                        │
│                                                             │
│ → curriculum: ProgramCurriculum[]                          │
│ → prerequisites: ProgramPrerequisite[]                     │
│ → offerings: ProgramOffering[]                             │
│ → instructors: ProgramInstructor[]                         │
│ → certifications_offered: ProgramCertification[]           │
│ → accreditation_status: ProgramAccreditation[]             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  SKILLS FRAMEWORK                           │
├─────────────────────────────────────────────────────────────┤
│ skill_id: UUID (PK)                                         │
│ skill_code: String(50)                                      │
│ skill_name: String(255)                                     │
│ skill_category: String(100)                                 │
│ description: Text                                            │
│ proficiency_levels: ProficiencyLevel[]                      │
│ assessment_methods: AssessmentMethod[]                      │
│                                                             │
│ → program_mappings: ProgramSkillMapping[]                  │
│ → assessments: SkillsAssessment[]                          │
│ → industry_standards: IndustrySkillStandard[]              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 EQUIPMENT ENTITY                            │
├─────────────────────────────────────────────────────────────┤
│ equipment_id: UUID (PK)                                     │
│ equipment_code: String(50)                                  │
│ equipment_name: String(255)                                 │
│ equipment_type: String(100)                                 │
│ manufacturer: String(100)                                    │
│ model: String(100)                                          │
│ serial_number: String(100)                                  │
│ purchase_date: Date                                          │
│ purchase_price: Decimal                                      │
│ warranty_expiration: Date                                    │
│ location: String(200)                                        │
│ status: Enum[available, in_use, maintenance, retired]       │
│ safety_cert_required: Boolean                               │
│ safety_cert_code: String(50)                                │
│                                                             │
│ → maintenance_schedule: EquipmentMaintenance[]             │
│ → usage_logs: EquipmentUsageLog[]                          │
│ → checkout_records: EquipmentCheckout[]                    │
└─────────────────────────────────────────────────────────────┘
```

---

### 10.2 DM02: Key Data Retention Requirements

| Data Category              | Retention Period            | Regulatory Basis          |
| -------------------------- | --------------------------- | ------------------------- |
| Student enrollment records | 7 years post-graduation     | FERPA, State requirements |
| Financial aid records      | 5 years                     | Title IV requirements     |
| Certification records      | Permanent                   | Accreditation             |
| Employment outcome data    | 7 years                     | WIOA, Perkins V           |
| Safety incident reports    | 5 years                     | OSHA                      |
| Instructor credentials     | Current + 3 years           | Accreditation             |
| Assessment records         | 7 years                     | Accreditation             |
| Equipment maintenance      | Life of equipment + 3 years | Safety compliance         |

---

### 10.3 DM03: Audit Trail Requirements

| Event Type                   | Required Fields                                 | Retention |
| ---------------------------- | ----------------------------------------------- | --------- |
| User login                   | User, timestamp, IP, session                    | 1 year    |
| Data creation                | User, entity, timestamp, values                 | 7 years   |
| Data modification            | User, entity, timestamp, old values, new values | 7 years   |
| Data deletion                | User, entity, timestamp, reason                 | 7 years   |
| Access to sensitive data     | User, entity, timestamp, purpose                | 1 year    |
| System configuration         | User, setting, timestamp, old value, new value  | 7 years   |
| Compliance report generation | User, report type, timestamp, recipients        | 7 years   |

---

## 11. Security and Access Control

### 11.1 S01: Role-Based Access Control (RBAC)

#### 11.1.1 Core Roles

| Role               | Data Access      | Function Access      | Notes                       |
| ------------------ | ---------------- | -------------------- | --------------------------- |
| Student            | Own records      | Student features     | Limited to own data         |
| Instructor         | Assigned classes | Teaching features    | Class-level access          |
| Lab Manager        | Lab resources    | Equipment features   | Facility-level access       |
| Program Director   | Program data     | All program features | Program-level access        |
| Admissions         | Application data | Enrollment features  | Prospective/active students |
| Financial Aid      | Financial data   | Aid features         | FERPA-trained required      |
| Career Services    | Alumni data      | Placement features   | Graduate data access        |
| Employer           | Posted jobs      | Employer features    | Limited to job functions    |
| System Admin       | All system       | Admin features       | Technical access only       |
| Compliance Officer | All compliance   | Reporting features   | Audit access                |

#### 11.1.2 Data Segregation Rules

- Student records: Student can only view own data
- Instructor access: Limited to assigned classes/programs
- Cross-program access: Requires explicit permission
- Historical data: Access restricted based on data age

---

### 11.2 S02: Authentication Requirements

#### 11.2.1 Authentication Methods

- Email/password with complexity requirements
- Multi-factor authentication (MFA) for all roles
- SSO support (SAML 2.0, OpenID Connect)
- Social login (for job board access only)

#### 11.2.2 Session Management

- Session timeout: 30 minutes inactivity
- Concurrent session limit: 5 per user
- Session tracking and logging
- Forced logout on password change

---

### 11.3 S03: Data Encryption

#### 11.3.1 Encryption Standards

| Data Type             | Encryption at Rest | Encryption in Transit |
| --------------------- | ------------------ | --------------------- |
| PII (SSN, DOB)        | AES-256            | TLS 1.3               |
| Financial data        | AES-256            | TLS 1.3               |
| Health data           | AES-256            | TLS 1.3               |
| Authentication tokens | AES-256            | TLS 1.3               |
| General data          | AES-256            | TLS 1.2+              |

#### 11.3.2 Key Management

- AWS KMS or Azure Key Vault integration
- Key rotation: Every 90 days
- Key access logging
- Emergency key escrow procedure

---

## 12. Observability and Operations

### 12.1 O01: Monitoring and Alerting

#### 12.1.1 System Metrics

| Metric                   | Threshold   | Action  |
| ------------------------ | ----------- | ------- |
| API error rate           | >1%         | Alert   |
| API latency P95          | >1 second   | Alert   |
| Database connection pool | >80%        | Warning |
| Disk usage               | >80%        | Alert   |
| Memory usage             | >85%        | Alert   |
| CPU usage                | >90%        | Alert   |
| Queue depth              | >1000 items | Warning |

#### 12.1.2 Business Metrics

| Metric                        | Threshold | Action         |
| ----------------------------- | --------- | -------------- |
| Failed enrollment submissions | >10/hour  | Alert          |
| Failed assessment submissions | >5/hour   | Alert          |
| Failed payment processing     | >1/hour   | Critical Alert |
| Unprocessed notifications     | >100      | Warning        |

---

### 12.2 O02: Logging Requirements

#### 12.2.1 Log Categories

- Application logs: INFO level, 30-day retention
- Security logs: All events, 1-year retention
- Audit logs: All data changes, 7-year retention
- Error logs: ERROR level, 90-day retention
- Access logs: All requests, 1-year retention

#### 12.2.2 Log Format

```json
{
    "timestamp": "ISO8601",
    "level": "INFO|WARN|ERROR",
    "service": "service_name",
    "request_id": "UUID",
    "user_id": "UUID|null",
    "user_role": "role_name",
    "action": "action_description",
    "resource": "resource_type:id",
    "status": "success|failure",
    "duration_ms": 123,
    "ip_address": "x.x.x.x",
    "user_agent": "string",
    "message": "description"
}
```

---

### 12.3 O03: Backup and Recovery

#### 12.3.1 Backup Strategy

| Backup Type    | Frequency  | Retention | Storage Location |
| -------------- | ---------- | --------- | ---------------- |
| Full database  | Daily      | 30 days   | Offsite cloud    |
| Incremental DB | Hourly     | 7 days    | Same region      |
| File storage   | Daily      | 30 days   | Versioned bucket |
| Config backups | Per change | 90 days   | Version control  |

#### 12.3.2 Recovery Objectives

| RPO (Recovery Point Objective) | 1 hour |
| RTO (Recovery Time Objective) | 4 hours |
| Disaster Recovery Site | Secondary region |
| DR Testing Frequency | Quarterly |

---

### 12.4 O04: Capacity Planning

#### 12.4.1 Enrollment Cycles

| Period                       | Expected Load | Scaling Strategy       |
| ---------------------------- | ------------- | ---------------------- |
| Application period (Jan-Mar) | 200% normal   | Scale web/API          |
| Enrollment period (Jul-Aug)  | 300% normal   | Full scale up          |
| Regular term                 | 100% normal   | Base capacity          |
| Grading period               | 150% normal   | Scale write operations |

---

## 13. Acceptance Criteria

### 13.1 AC01: Functional Acceptance Criteria

#### 13.1.1 Enrollment Process

- [ ] Student can complete application in <15 minutes
- [ ] System validates all required fields before submission
- [ ] Application status updates within 1 hour of submission
- [ ] Admissions staff can process applications in <2 minutes each
- [ ] Automated rejection notifications sent within 1 hour

#### 13.1.2 Program Enrollment

- [ ] Student can view all eligible programs based on prerequisites
- [ ] System prevents enrollment in programs with unmet prerequisites
- [ ] Waitlist automatically promotes students when seats open
- [ ] Enrollment confirmation sent within 5 minutes

#### 13.1.3 Lab Scheduling

- [ ] Lab booking available 4 weeks in advance
- [ ] System prevents overbooking beyond safety capacity
- [ ] Equipment checkout linked to scheduled booking
- [ ] Safety certification requirement enforced before booking

#### 13.1.4 Certification Exam Scheduling

- [ ] Student eligibility automatically verified before booking
- [ ] Exam results received within 48 hours of exam date
- [ ] Credential issued within 24 hours of passing result
- [ ] Renewal reminder sent 90 days before expiration

---

### 13.2 AC02: Performance Acceptance Criteria

| Scenario               | Users            | Response Time | Success Rate |
| ---------------------- | ---------------- | ------------- | ------------ |
| Application submission | 1,000 concurrent | <3 seconds    | 99.9%        |
| Enrollment processing  | 500 concurrent   | <2 seconds    | 99.9%        |
| Lab booking            | 100 concurrent   | <1 second     | 99.9%        |
| Skills assessment      | 500 concurrent   | <2 seconds    | 99.9%        |
| Report generation      | 50 concurrent    | <30 seconds   | 99%          |

---

### 13.3 AC03: Compliance Acceptance Criteria

- [ ] WIOA performance measures calculable and reportable
- [ ] Perkins V core indicators trackable by program and subgroup
- [ ] Title IX gender enrollment analysis automated
- [ ] ADA accommodation workflow documented and auditable
- [ ] FERPA directory information opt-out functional
- [ ] OSHA training requirements enforceable
- [ ] State-specific reporting templates available

---

## 14. Out-of-Scope

### 14.1 OS01: Explicitly Out of Scope

| Item                          | Reason                           | Alternative              |
| ----------------------------- | -------------------------------- | ------------------------ |
| K-12 curriculum management    | Separate regulatory requirements | Integration with SIS     |
| University degree programs    | Different accreditation model    | Integration with SIS     |
| Clinical healthcare education | HIPAA and clinical requirements  | Specialized integration  |
| Full HRIS functionality       | Better integrated with existing  | HRIS integration         |
| Payroll processing            | Compliance and security          | Payroll integration      |
| Student housing management    | Different domain                 | External solution        |
| Campus security systems       | Physical infrastructure          | Integration if available |
| Transportation services       | Logistics domain                 | External solution        |

---

## 15. Open Questions

### 15.1 OQ01: Questions for Stakeholders

| ID   | Question                                                          | Priority | Impact | Owner                |
| ---- | ----------------------------------------------------------------- | -------- | ------ | -------------------- |
| OQ01 | Which accreditation bodies are most important for initial launch? | P0       | High   | Program Director     |
| OQ02 | What are the state-specific requirements for target markets?      | P0       | High   | Compliance Officer   |
| OQ03 | Which LMS integrations are required for MVP?                      | P1       | Medium | IT Director          |
| OQ04 | What certification bodies are most commonly used?                 | P1       | Medium | Program Director     |
| OQ05 | Should employer job postings be free or fee-based?                | P2       | Medium | Business Development |
| OQ06 | What payment processors are preferred by customers?               | P1       | Medium | Finance              |
| OQ07 | Should the platform support multi-campus institutions?            | P1       | Medium | Product              |
| OQ08 | What is the minimum equipment tracking granularity required?      | P2       | Low    | Operations           |

---

## 16. Glossary

## 16. Glossary

| Term                   | Definition                                                   | Context                   |
| ---------------------- | ------------------------------------------------------------ | ------------------------- |
| ACCREDITATION          | Formal recognition that a program meets quality standards    | Industry oversight        |
| APPRENTICESHIP         | Paid on-the-job training combined with classroom instruction | Training model            |
| ASSESSMENT             | Evaluation of skills, knowledge, or competency               | Learning measurement      |
| CERTIFICATION          | Credential demonstrating proficiency in a skill or field     | Industry credential       |
| COMPETENCY             | Ability to perform tasks to required standard                | Skills framework          |
| COHORT                 | Group of students progressing through program together       | Program structure         |
| CSAT                   | Customer Satisfaction Score                                  | Quality metric            |
| CREDENTIAL             | Document or certification proving qualification              | Proof of skill            |
| EXTERNAL CERTIFICATION | Certification from external body (e.g., AWS, CompTIA)        | Industry credential       |
| EXTERN                 | Student learning experience at workplace                     | Practical experience      |
| GRADUATION COMPLETION  | Finishing all program requirements                           | Program outcome           |
| HANDS-ON TRAINING      | Practical, experiential learning                             | Learning method           |
| INSTRUCTOR CREDENTIAL  | Qualification certifying instructor expertise                | Staff requirement         |
| JOB PLACEMENT          | Securing employment after program completion                 | Career outcome            |
| LAB                    | Facility for hands-on practice and training                  | Physical space            |
| LMS                    | Learning Management System                                   | Digital learning platform |
| NCCER                  | National Center for Construction Education and Research      | Certification body        |
| OSHA                   | Occupational Safety and Health Administration                | Safety regulation         |
| PLACEMENT RATE         | Percentage of graduates employed in field                    | Success metric            |
| PROFICIENCY            | Level of skill mastery                                       | Competency measure        |
| RBAC                   | Role-Based Access Control                                    | Security model            |
| RPO                    | Recovery Point Objective                                     | Disaster recovery metric  |
| RTO                    | Recovery Time Objective                                      | Disaster recovery metric  |
| SAFETY COMPLIANCE      | Adherence to safety regulations and procedures               | Regulatory requirement    |
| SKILL ASSESSMENT       | Evaluation of practical ability                              | Competency measurement    |
| TRAINEE                | Person receiving vocational training                         | Student synonym           |
| VOCATIONAL             | Related to occupation or employment                          | Education type            |
| WCAG                   | Web Content Accessibility Guidelines                         | Accessibility standard    |

---

_End of Brief_
