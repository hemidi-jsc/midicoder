# UAT Briefs — Capability: global_error_handler

> Capability ID: `global_error_handler` | CP B01: Domain Model DSL & IR Builder  
> Total: 20 briefs covering GlobalErrorHandler DSL definition

---

### B01-GEH-01: Basic FALLBACK handler with ERROR level

**Capability:** `global_error_handler`  
**Stack:** `fastapi`

**Use Case:** Production application with fallback error strategy — returns user-friendly error messages on exceptions without exposing internal details.

**Input DSL:**
```yaml
global_error_handler:
  id: app_error_handler
  name: Application Error Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  default_error_message: "An error occurred while processing your request"
  sanitize_output: true
  cors_enabled: false
```

**Expected Output:**
- File: `src/error_handling/app_error_handler.py`
- Contains: `GlobalErrorHandler` with strategy=FALLBACK, log_level=ERROR, include_stack_trace=False, sanitize_output=True

---

### B01-GEH-02: RETRY strategy with common mappers

**Capability:** `global_error_handler`  
**Stack:** `both`

**Use Case:** API gateway that retries transient failures — ConnectionError and TimeoutError are marked retryable with automatic backoff.

**Input DSL:**
```yaml
global_error_handler:
  id: api_retry_handler
  name: API Retry Handler
  strategy: retry
  log_level: warning
  include_stack_trace: false
  sanitize_output: true
error_mappers:
  - id: connection_error
    exception_type: ConnectionError
    http_status: 503
    error_code: SERVICE_UNAVAILABLE
    user_message: "Service temporarily unavailable, please retry"
    retryable: true
    public: true
  - id: timeout_error
    exception_type: TimeoutError
    http_status: 504
    error_code: GATEWAY_TIMEOUT
    user_message: "Request timed out, please try again"
    retryable: true
    public: true
  - id: value_error
    exception_type: ValueError
    http_status: 400
    error_code: INVALID_INPUT
    user_message: "Invalid input provided"
    retryable: false
    public: true
  - id: key_error
    exception_type: KeyError
    http_status: 404
    error_code: NOT_FOUND
    user_message: "Resource not found"
    retryable: false
    public: true
```

**Expected Output:**
- File: `src/error_handling/api_retry_handler.py`
- Contains: GlobalErrorHandler with strategy=RETRY, 4 ErrorMappers with retryable=True for ConnectionError/TimeoutError

---

### B01-GEH-03: CIRCUIT_BREAKER strategy with timeout mappers

**Capability:** `global_error_handler`  
**Stack:** `fastapi`

**Use Case:** Microservice with circuit breaker — opens circuit after repeated ConnectionError/TimeoutError to prevent cascading failures.

**Input DSL:**
```yaml
global_error_handler:
  id: circuit_breaker_handler
  name: Circuit Breaker Handler
  strategy: circuit_breaker
  log_level: error
  include_stack_trace: false
  sanitize_output: true
error_mappers:
  - id: connection_breaker
    exception_type: ConnectionError
    http_status: 503
    error_code: CIRCUIT_OPEN
    user_message: "Service circuit is open, please try later"
    retryable: false
    public: true
  - id: timeout_breaker
    exception_type: TimeoutError
    http_status: 504
    error_code: CIRCUIT_OPEN_TIMEOUT
    user_message: "Service timeout circuit is open"
    retryable: false
    public: true
```

**Expected Output:**
- File: `src/error_handling/circuit_breaker_handler.py`
- Contains: GlobalErrorHandler with strategy=CIRCUIT_BREAKER, 2 ErrorMappers with circuit-open error codes

---

### B01-GEH-04: GRACEFUL_DEGRADATION with fallback messages

**Capability:** `global_error_handler`  
**Stack:** `nestjs`

**Use Case:** High-availability system degrades gracefully — returns cached/stale data when primary services fail, with user-friendly fallback messages.

**Input DSL:**
```yaml
global_error_handler:
  id: graceful_degradation_handler
  name: Graceful Degradation Handler
  strategy: graceful_degradation
  log_level: warning
  include_stack_trace: false
  default_error_message: "Some features may be limited, please try again later"
  sanitize_output: true
  cors_enabled: true
error_mappers:
  - id: external_api_down
    exception_type: ConnectionError
    http_status: 206
    error_code: PARTIAL_DATA
    user_message: "Returning cached data, live data temporarily unavailable"
    retryable: false
    public: true
  - id: slow_response
    exception_type: TimeoutError
    http_status: 206
    error_code: STALE_DATA
    user_message: "Showing previously cached results"
    retryable: false
    public: true
```

**Expected Output:**
- File: `src/error_handling/graceful_degradation_handler.ts`
- Contains: GlobalErrorHandler with strategy=GRACEFUL_DEGRADATION, ErrorMappers returning HTTP 206 (Partial Content)

---

### B01-GEH-05: Handler with structured JSON logging to file

**Capability:** `global_error_handler`  
**Stack:** `fastapi`

**Use Case:** Production app with structured JSON error logging to a rotating file — enables centralized log parsing and aggregation.

**Input DSL:**
```yaml
global_error_handler:
  id: file_logger_handler
  name: File Logger Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  sanitize_output: true
logging:
  id: error_file_logger
  name: Error File Logger
  log_format: json
  log_destination: file
  log_file_path: /var/log/app/errors.log
  max_log_size_mb: 100
  log_rotation_days: 30
  include_request_context: true
  include_user_context: true
  redact_fields:
    - password
    - token
```

**Expected Output:**
- File: `src/error_handling/file_logger_handler.py`
- Contains: GlobalErrorHandler + ErrorLoggingConfig with log_format=JSON, log_destination=FILE, rotation 100MB/30 days

---

### B01-GEH-06: Handler with logging to elasticsearch

**Capability:** `global_error_handler`  
**Stack:** `both`

**Use Case:** Enterprise application with centralized error logging to Elasticsearch — enables Kibana dashboards and real-time error monitoring.

**Input DSL:**
```yaml
global_error_handler:
  id: elasticsearch_handler
  name: Elasticsearch Logger Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  sanitize_output: true
logging:
  id: es_error_logger
  name: Elasticsearch Error Logger
  log_format: json
  log_destination: elasticsearch
  max_log_size_mb: 100
  log_rotation_days: 90
  include_request_context: true
  include_user_context: true
  redact_fields:
    - password
    - ssn
    - credit_card
    - api_key
```

**Expected Output:**
- File: `src/error_handling/elasticsearch_handler.py`
- Contains: ErrorLoggingConfig with log_destination=ELASTICSEARCH, JSON format, 90-day retention, 4 redacted fields

---

### B01-GEH-07: Handler with logging to cloudwatch

**Capability:** `global_error_handler`  
**Stack:** `fastapi`

**Use Case:** AWS-hosted application streaming error logs to CloudWatch Logs — integrates with AWS alarm and SNS alerting.

**Input DSL:**
```yaml
global_error_handler:
  id: cloudwatch_handler
  name: CloudWatch Logger Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  sanitize_output: true
logging:
  id: cw_error_logger
  name: CloudWatch Error Logger
  log_format: json
  log_destination: cloudwatch
  max_log_size_mb: 50
  log_rotation_days: 14
  include_request_context: true
  include_user_context: true
  redact_fields:
    - password
    - auth_token
    - ssn
```

**Expected Output:**
- File: `src/error_handling/cloudwatch_handler.py`
- Contains: ErrorLoggingConfig with log_destination=CLOUDWATCH, JSON format, 14-day rotation

---

### B01-GEH-08: Handler with Slack webhook notification

**Capability:** `global_error_handler`  
**Stack:** `both`

**Use Case:** Startup application that posts error alerts to a Slack #incidents channel for rapid team response.

**Input DSL:**
```yaml
global_error_handler:
  id: slack_handler
  name: Slack Alert Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  sanitize_output: true
notification:
  id: slack_notifier
  name: Slack Error Notifier
  notify_on_level: error
  slack_webhook: https://hooks.slack.com/services/T0123/B0123/xxxxxx
  rate_limit_per_hour: 50
logging:
  id: stdout_logger
  name: Stdout Logger
  log_format: structured
  log_destination: stdout
```

**Expected Output:**
- File: `src/error_handling/slack_handler.py`
- Contains: ErrorNotificationConfig with slack_webhook configured, notify_on_level=ERROR, rate_limit=50/hr

---

### B01-GEH-09: Handler with email notification to multiple recipients

**Capability:** `global_error_handler`  
**Stack:** `fastapi`

**Use Case:** Financial application sends error notifications to the engineering team and compliance officers via email.

**Input DSL:**
```yaml
global_error_handler:
  id: email_handler
  name: Email Alert Handler
  strategy: fallback
  log_level: critical
  include_stack_trace: true
  sanitize_output: true
notification:
  id: email_notifier
  name: Email Error Notifier
  notify_on_level: critical
  email_recipients:
    - eng-leads@company.com
    - ops-team@company.com
    - compliance@company.com
  rate_limit_per_hour: 20
logging:
  id: critical_logger
  name: Critical Logger
  log_format: structured
  log_destination: file
  log_file_path: /var/log/app/critical_errors.log
  max_log_size_mb: 50
  log_rotation_days: 365
```

**Expected Output:**
- File: `src/error_handling/email_handler.py`
- Contains: ErrorNotificationConfig with 3 email_recipients, notify_on_level=CRITICAL, rate_limit=20/hr

---

### B01-GEH-10: Handler with PagerDuty integration

**Capability:** `global_error_handler`  
**Stack:** `both`

**Use Case:** On-call system integration — PagerDuty receives alerts for ERROR-level and above, triggering incident response workflow.

**Input DSL:**
```yaml
global_error_handler:
  id: pagerduty_handler
  name: PagerDuty Alert Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  sanitize_output: true
notification:
  id: pd_notifier
  name: PagerDuty Notifier
  notify_on_level: error
  pagerduty_service_key: xxxxxxxxxx123456789
  rate_limit_per_hour: 100
logging:
  id: pd_logger
  name: PagerDuty Logger
  log_format: json
  log_destination: stdout
  redact_fields:
    - api_key
    - service_key
```

**Expected Output:**
- File: `src/error_handling/pagerduty_handler.py`
- Contains: ErrorNotificationConfig with pagerduty_service_key, notify_on_level=ERROR, rate_limit=100/hr

---

### B01-GEH-11: Handler with Sentry integration (DSN configured)

**Capability:** `global_error_handler`  
**Stack:** `fastapi`

**Use Case:** Application with Sentry error tracking — captures exceptions, stack traces, and breadcrumbs for real-time error monitoring and postmortem analysis.

**Input DSL:**
```yaml
global_error_handler:
  id: sentry_handler
  name: Sentry Error Handler
  strategy: fallback
  log_level: error
  include_stack_trace: true
  sanitize_output: true
notification:
  id: sentry_notifier
  name: Sentry Notifier
  notify_on_level: error
  include_sentry: true
  sentry_dsn: https://abc123@sentry.io/98765
  rate_limit_per_hour: 200
error_mappers:
  - id: type_error_sentry
    exception_type: TypeError
    http_status: 500
    error_code: INTERNAL_ERROR
    user_message: "An unexpected error occurred"
    retryable: false
    public: true
```

**Expected Output:**
- File: `src/error_handling/sentry_handler.py`
- Contains: ErrorNotificationConfig with include_sentry_integration=True, sentry_dsn configured, GlobalErrorHandler with include_stack_trace=True

---

### B01-GEH-12: Handler with all notifications (Slack + Email + PagerDuty + Sentry)

**Capability:** `global_error_handler`  
**Stack:** `both`

**Use Case:** Mission-critical system with full notification coverage — Slack for team chat, email for management, PagerDuty for on-call, Sentry for postmortem.

**Input DSL:**
```yaml
global_error_handler:
  id: fullstack_handler
  name: Full Stack Error Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  sanitize_output: true
  cors_enabled: true
notification:
  id: fullstack_notifier
  name: Full Stack Notifier
  notify_on_level: error
  slack_webhook: https://hooks.slack.com/services/T00/B00/incidents
  email_recipients:
    - eng-leads@company.com
    - cto@company.com
  pagerduty_service_key: pd_service_key_12345
  include_sentry: true
  sentry_dsn: https://sentry_key@sentry.io/11111
  rate_limit_per_hour: 50
logging:
  id: fullstack_logger
  name: Full Stack Logger
  log_format: json
  log_destination: file
  log_file_path: /var/log/app/errors.log
  max_log_size_mb: 200
  log_rotation_days: 60
  redact_fields:
    - password
    - token
    - ssn
    - credit_card
    - api_key
```

**Expected Output:**
- File: `src/error_handling/fullstack_handler.py`
- Contains: GlobalErrorHandler with ErrorNotificationConfig containing Slack, 2 emails, PagerDuty, and Sentry, plus JSON file logging

---

### B01-GEH-13: Handler with custom error mappers (DomainError, BusinessRuleError)

**Capability:** `global_error_handler`  
**Stack:** `fastapi`

**Use Case:** Domain-driven application maps custom business exceptions to appropriate HTTP status codes and user-friendly messages.

**Input DSL:**
```yaml
global_error_handler:
  id: domain_handler
  name: Domain Error Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  sanitize_output: true
error_mappers:
  - id: domain_error
    exception_type: DomainError
    http_status: 400
    error_code: DOMAIN_VIOLATION
    user_message: "The requested operation violates a business rule"
    retryable: false
    public: true
  - id: business_rule_error
    exception_type: BusinessRuleError
    http_status: 422
    error_code: BUSINESS_RULE_VIOLATED
    user_message: "Operation cannot be completed due to business constraints"
    retryable: false
    public: true
  - id: aggregate_concurrency_error
    exception_type: AggregateConcurrencyError
    http_status: 409
    error_code: CONFLICT
    user_message: "The resource was modified by another operation, please refresh and try again"
    retryable: true
    public: true
```

**Expected Output:**
- File: `src/error_handling/domain_handler.py`
- Contains: 3 custom ErrorMappers (DomainError→400, BusinessRuleError→422, AggregateConcurrencyError→409)

---

### B01-GEH-14: Handler with redacted fields (password, ssn, credit_card)

**Capability:** `global_error_handler`  
**Stack:** `both`

**Use Case:** PCI/DSS-compliant application that redacts sensitive fields from all error logs and notifications to prevent data leakage.

**Input DSL:**
```yaml
global_error_handler:
  id: pci_handler
  name: PCI Compliant Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  sanitize_output: true
logging:
  id: pci_logger
  name: PCI Logger
  log_format: json
  log_destination: file
  log_file_path: /var/log/app/secure_errors.log
  max_log_size_mb: 100
  log_rotation_days: 365
  include_request_context: true
  include_user_context: false
  redact_fields:
    - password
    - ssn
    - credit_card
    - cvv
    - banking_pin
    - account_number
    - social_security
```

**Expected Output:**
- File: `src/error_handling/pci_handler.py`
- Contains: ErrorLoggingConfig with 7 redacted PII/PCI fields, include_user_context=False, sanitize_output=True

---

### B01-GEH-15: Handler with CRITICAL level + stack trace

**Capability:** `global_error_handler`  
**Stack:** `fastapi`

**Use Case:** Development/staging environment with CRITICAL-level logging and full stack traces for debugging production-like failures.

**Input DSL:**
```yaml
global_error_handler:
  id: debug_handler
  name: Debug Error Handler
  strategy: fallback
  log_level: critical
  include_stack_trace: true
  default_error_message: "Critical system error occurred"
  sanitize_output: false
  cors_enabled: true
error_mappers:
  - id: critical_error
    exception_type: Exception
    http_status: 500
    error_code: CRITICAL_FAILURE
    user_message: "A critical system error has occurred"
    retryable: false
    public: true
logging:
  id: debug_logger
  name: Debug Logger
  log_format: plain
  log_destination: stdout
  include_request_context: true
  include_user_context: true
```

**Expected Output:**
- File: `src/error_handling/debug_handler.py`
- Contains: GlobalErrorHandler with log_level=CRITICAL, include_stack_trace=True, sanitize_output=False, plain format logging

---

### B01-GEH-16: Handler with CORS enabled + sanitize output

**Capability:** `global_error_handler`  
**Stack:** `fastapi`

**Use Case:** Public API served via reverse proxy — CORS headers on error responses, sanitized output to prevent information disclosure.

**Input DSL:**
```yaml
global_error_handler:
  id: public_api_handler
  name: Public API Error Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  default_error_message: "The API encountered an error"
  sanitize_output: true
  cors_enabled: true
error_mappers:
  - id: rate_limit
    exception_type: ValueError
    http_status: 429
    error_code: RATE_LIMITED
    user_message: "Too many requests, please slow down"
    retryable: false
    public: true
  - id: not_found
    exception_type: KeyError
    http_status: 404
    error_code: RESOURCE_NOT_FOUND
    user_message: "The requested resource was not found"
    retryable: false
    public: true
  - id: forbidden
    exception_type: PermissionError
    http_status: 403
    error_code: ACCESS_DENIED
    user_message: "You do not have permission to access this resource"
    retryable: false
    public: true
```

**Expected Output:**
- File: `src/error_handling/public_api_handler.py`
- Contains: GlobalErrorHandler with cors_enabled=True, sanitize_output=True, 3 public-facing ErrorMappers (429/404/403)

---

### B01-GEH-17: Handler with custom error pages (404, 500)

**Capability:** `global_error_handler`  
**Stack:** `fastapi`

**Use Case:** Customer-facing web application with branded error pages — custom HTML templates for 404 (Not Found) and 500 (Server Error).

**Input DSL:**
```yaml
global_error_handler:
  id: webapp_handler
  name: Web Application Error Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  sanitize_output: true
  cors_enabled: true
  custom_error_pages:
    404: templates/errors/404.html
    500: templates/errors/500.html
error_mappers:
  - id: page_not_found
    exception_type: KeyError
    http_status: 404
    error_code: PAGE_NOT_FOUND
    user_message: "The page you are looking for does not exist"
    retryable: false
    public: true
  - id: server_error
    exception_type: Exception
    http_status: 500
    error_code: SERVER_ERROR
    user_message: "We are experiencing technical difficulties"
    retryable: false
    public: true
logging:
  id: webapp_logger
  name: Web App Logger
  log_format: structured
  log_destination: stdout
```

**Expected Output:**
- File: `src/error_handling/webapp_handler.py`
- Contains: GlobalErrorHandler with custom_error_pages={404: templates/errors/404.html, 500: templates/errors/500.html}

---

### B01-GEH-18: Handler with rate-limited notifications (50/hour)

**Capability:** `global_error_handler`  
**Stack:** `both`

**Use Case:** High-traffic application with rate-limited notifications to prevent alert fatigue — maximum 50 notifications per hour across all channels.

**Input DSL:**
```yaml
global_error_handler:
  id: rate_limited_handler
  name: Rate Limited Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  sanitize_output: true
notification:
  id: rate_limited_notifier
  name: Rate Limited Notifier
  notify_on_level: error
  slack_webhook: https://hooks.slack.com/services/T00/B00/alerts
  email_recipients:
    - oncall@company.com
  rate_limit_per_hour: 50
logging:
  id: rl_logger
  name: Rate Limited Logger
  log_format: json
  log_destination: stdout
```

**Expected Output:**
- File: `src/error_handling/rate_limited_handler.py`
- Contains: ErrorNotificationConfig with rate_limit_per_hour=50, Slack + email channels

---

### B01-GEH-19: Handler with non-public internal errors

**Capability:** `global_error_handler`  
**Stack:** `fastapi`

**Use Case:** Internal microservice that returns generic error messages to consumers while logging detailed internal errors for diagnostics.

**Input DSL:**
```yaml
global_error_handler:
  id: internal_handler
  name: Internal Service Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  default_error_message: "Internal service error"
  sanitize_output: true
error_mappers:
  - id: internal_db_error
    exception_type: ConnectionError
    http_status: 500
    error_code: INTERNAL_ERROR
    user_message: "An internal error occurred"
    retryable: false
    public: false
  - id: internal_timeout
    exception_type: TimeoutError
    http_status: 500
    error_code: INTERNAL_ERROR
    user_message: "An internal error occurred"
    retryable: false
    public: false
  - id: validation_error
    exception_type: ValueError
    http_status: 400
    error_code: INVALID_INPUT
    user_message: "Invalid request payload"
    retryable: false
    public: true
logging:
  id: internal_logger
  name: Internal Logger
  log_format: json
  log_destination: file
  log_file_path: /var/log/app/internal_errors.log
  max_log_size_mb: 500
  log_rotation_days: 30
```

**Expected Output:**
- File: `src/error_handling/internal_handler.py`
- Contains: ErrorMappers with public=False for internal errors, generic user_message masking internal details

---

### B01-GEH-20: Minimal handler (defaults only, no custom config)

**Capability:** `global_error_handler`  
**Stack:** `both`

**Use Case:** Prototype or test application with minimal error handling — uses all default values, no custom mappers, logging, or notifications.

**Input DSL:**
```yaml
global_error_handler:
  id: minimal_handler
  name: Minimal Error Handler
  strategy: fallback
  log_level: error
  include_stack_trace: false
  sanitize_output: true
  cors_enabled: true
```

**Expected Output:**
- File: `src/error_handling/minimal_handler.py`
- Contains: GlobalErrorHandler with only id, name, strategy=FALLBACK, log_level=ERROR, default_error_message="Internal Server Error", no ErrorMappers, no logging, no notification
