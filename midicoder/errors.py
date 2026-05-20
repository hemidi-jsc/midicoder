"""
Mô-đun quản lý lỗi dùng chung cho toàn bộ Midicoder.

Cung cấp:
- ErrorCode enum: Mã lỗi chuẩn cho toàn hệ thống
- MidicoderError: Exception class với context và traceback support
- MidicoderErrorManager: Factory pattern cho error creation

Sử dụng:
    from midicoder.errors import MidicoderErrorManager as EM

    # Tạo và throw error với context
    raise EM.raise_error(
        ErrorCode.DSL_LOAD_FAILED,
        file_path="dsl/entities.yaml",
        line_number=42
    )

    # Xử lý error
    try:
        ...
    except MidicoderError as e:
        print(str(e))  # [DSL-001] Cannot load DSL (file=dsl/entities.yaml, line=42)
        print(e.context)  # {'file': 'dsl/entities.yaml', 'line': 42}
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ErrorCode(str, Enum):
    """
    Danh sách mã lỗi chuẩn để các module tái sử dụng thống nhất.

    Cấu trúc mã lỗi:
    - MDC-CLI-XXX: CLI errors
    - MDC-BRIEF-XXX: Brief/DSL errors
    - MDC-COMP-XXX: Contract/Compilation errors
    - MDC-DSL-XXX: DSL v1 specific errors
    - MDC-VALID-XXX: Validation errors
    - MDC-RUNTIME-XXX: Runtime errors
    """

    # =========================================================================
    # CLI Errors
    # =========================================================================
    NO_CURRENT_VERSION = "MDC-CLI-001"

    # =========================================================================
    # Brief/DSL Errors
    # =========================================================================
    MASTER_BRIEF_MISSING = "MDC-BRIEF-001"

    # =========================================================================
    # Contract/Compilation Errors
    # =========================================================================
    CONTRACT_GRAPH_NOT_FOUND = "MDC-COMP-001"
    CONTRACT_GRAPH_VALIDATION_FAILED = "MDC-COMP-002"
    CONTRACT_COMPILE_FAILED = "MDC-COMP-003"
    DETERMINISTIC_HASH_GATE_FAILED = "MDC-COMP-004"
    CONTRACT_PACK_NOT_FOUND = "MDC-COMP-005"
    CONTRACT_GRAPH_READ_FAILED = "MDC-COMP-006"
    CONTRACT_GRAPH_SCHEMA_INVALID = "MDC-COMP-007"
    CAPABILITY_PARAMS_INVALID = "MDC-COMP-008"
    CAPABILITY_TYPE_UNKNOWN = "MDC-COMP-009"
    CAPABILITY_OBLIGATION_UNSATISFIED = "MDC-COMP-010"
    CAPABILITY_EXPAND_FAILED = "MDC-COMP-011"

    # =========================================================================
    # Blueprint Errors
    # =========================================================================
    BLUEPRINT_FILE_NOT_FOUND = "MDC-BLUEPRINT-001"
    BLUEPRINT_YAML_PARSE_ERROR = "MDC-BLUEPRINT-002"
    BLUEPRINT_MISSING_P0_PACKS = "MDC-BLUEPRINT-003"
    BLUEPRINT_MISSING_RX_OVERLAY = "MDC-BLUEPRINT-004"
    BLUEPRINT_INVALID_PROFILE = "MDC-BLUEPRINT-005"
    BLUEPRINT_INVARIANT_VIOLATION = "MDC-BLUEPRINT-006"
    BLUEPRINT_SCHEMA_INVALID = "MDC-BLUEPRINT-007"
    BLUEPRINT_DEPENDENCY_RESOLUTION_FAILED = "MDC-BLUEPRINT-008"
    BLUEPRINT_COMPILE_FAILED = "MDC-BLUEPRINT-009"

    # =========================================================================
    # DSL v1 Errors
    # =========================================================================
    DSL_LOAD_FAILED = "MDC-DSL-001"
    DSL_FILE_NOT_FOUND = "MDC-DSL-002"
    DSL_YAML_PARSE_ERROR = "MDC-DSL-003"
    DSL_INVALID_NODE_KIND = "MDC-DSL-004"
    DSL_MISSING_REQUIRED_FIELD = "MDC-DSL-005"
    DSL_INVALID_CATALOG_VALUE = "MDC-DSL-006"
    DSL_DUPLICATE_NODE_ID = "MDC-DSL-007"
    DSL_INVALID_REFERENCE = "MDC-DSL-008"

    # =========================================================================
    # Validation Errors
    # =========================================================================
    VALIDATION_FAILED = "MDC-VALID-001"
    CONSTRAINT_VIOLATION = "MDC-VALID-002"
    CROSS_NODE_VALIDATION_FAILED = "MDC-VALID-003"

    # =========================================================================
    # Dependency/Cycle Errors
    # =========================================================================
    DEPENDENCY_CYCLE_DETECTED = "MDC-DEP-001"
    MISSING_DEPENDENCY = "MDC-DEP-002"

    # =========================================================================
    # Runtime Errors
    # =========================================================================
    GENERATION_FAILED = "MDC-RUNTIME-001"
    TEMPLATE_RENDER_FAILED = "MDC-RUNTIME-002"
    FILE_WRITE_FAILED = "MDC-RUNTIME-003"

    # =========================================================================
    # LLM Errors
    # =========================================================================
    LLM_CONFIG_INVALID = "MDC-LLM-001"
    LLM_REQUEST_FAILED = "MDC-LLM-002"
    LLM_AUTH_FAILED = "MDC-LLM-003"
    LLM_RATE_LIMIT = "MDC-LLM-004"
    LLM_TIMEOUT = "MDC-LLM-005"

    # =========================================================================
    # Config Errors
    # =========================================================================
    CONFIG_READ_FAILED = "MDC-CONFIG-001"
    CONFIG_WRITE_FAILED = "MDC-CONFIG-002"
    CONFIG_FORMAT_INVALID = "MDC-CONFIG-003"
    CONFIG_KEY_NOT_FOUND = "MDC-CONFIG-004"
    CONFIG_VALUE_INVALID = "MDC-CONFIG-005"

    # =========================================================================
    # Database Errors
    # =========================================================================
    DB_CONNECTION_FAILED = "MDC-DB-001"
    DB_SCHEMA_ERROR = "MDC-DB-002"
    DB_CONSTRAINT_VIOLATION = "MDC-DB-003"
    DB_TRANSACTION_FAILED = "MDC-DB-004"
    DB_TIMEOUT = "MDC-DB-005"
    DB_FILE_CORRUPTED = "MDC-DB-006"
    DB_PERMISSION_DENIED = "MDC-DB-007"

    # =========================================================================
    # IR/MIR Build Errors
    # =========================================================================
    MIR_GRAPH_NOT_FOUND = "MDC-IR-001"
    MIR_DSL_PARSE_FAILED = "MDC-IR-002"
    MIR_BUILD_FAILED = "MDC-IR-003"
    MIR_VALIDATION_FAILED = "MDC-IR-004"
    MIR_SAVE_FAILED = "MDC-IR-005"

    # =========================================================================
    # Code Generation Errors
    # =========================================================================
    CODE_MIR_NOT_FOUND = "MDC-CODE-001"
    CODE_PLAN_NOT_FOUND = "MDC-CODE-002"
    CODE_PLAN_CREATE_FAILED = "MDC-CODE-003"
    CODE_GENERATION_FAILED = "MDC-CODE-004"
    CODE_APPLY_FAILED = "MDC-CODE-005"
    CODE_FILE_CONFLICT = "MDC-CODE-006"
    CODE_TEMPLATE_NOT_FOUND = "MDC-CODE-007"
    CODE_OUTPUT_DIR_ERROR = "MDC-CODE-008"

    # =========================================================================
    # Invariant Enforcement Errors
    # =========================================================================
    INV_NOT_REGISTERED = "MDC-INV-001"
    INV_VALIDATION_FAILED = "MDC-INV-002"
    INV_BLUEPRINT_MISSING = "MDC-INV-003"
    INV_CATEGORY_UNKNOWN = "MDC-INV-004"
    INV_ENFORCEMENT_UNKNOWN = "MDC-INV-005"
    INV_BUSINESS_ENTITY_REF = "MDC-INV-006"
    INV_BUSINESS_MUTATION_TXN = "MDC-INV-007"
    INV_BUSINESS_QUERY_WRITE = "MDC-INV-008"
    INV_BUSINESS_EVENT_ORDER = "MDC-INV-009"
    INV_BUSINESS_STATE_TRANSITION = "MDC-INV-010"
    INV_COMP_PII_ENCRYPTION = "MDC-INV-011"
    INV_COMP_AUDIT_TRAIL = "MDC-INV-012"
    INV_COMP_TENANT_ISOLATION = "MDC-INV-013"
    INV_COMP_PERMISSION_CHECK = "MDC-INV-014"
    INV_FM_ERROR_HANDLER = "MDC-INV-015"

    # =========================================================================
    # Preview Errors
    # =========================================================================
    PREVIEW_DOCKER_NOT_INSTALLED = "MDC-PRV-001"
    PREVIEW_DOCKER_NOT_RUNNING = "MDC-PRV-002"
    PREVIEW_COMPOSE_FILE_NOT_FOUND = "MDC-PRV-003"
    PREVIEW_ALREADY_RUNNING = "MDC-PRV-004"
    PREVIEW_START_FAILED = "MDC-PRV-005"
    PREVIEW_NOT_RUNNING = "MDC-PRV-006"
    PREVIEW_STOP_FAILED = "MDC-PRV-007"
    PREVIEW_RESTART_FAILED = "MDC-PRV-008"
    PREVIEW_HEALTH_CHECK_TIMEOUT = "MDC-PRV-009"

    # =========================================================================
    # Infrastructure Errors
    # =========================================================================
    INFRA_MIR_NOT_FOUND = "MDC-INFRA-001"
    INFRA_TEMPLATE_NOT_FOUND = "MDC-INFRA-002"
    INFRA_TEMPLATE_RENDER_FAILED = "MDC-INFRA-003"
    INFRA_WRITE_FAILED = "MDC-INFRA-004"
    INFRA_INVALID_CONFIG = "MDC-INFRA-005"

    # =========================================================================
    # CP07: Infrastructure as Code Generator Errors
    # =========================================================================
    CP07_MIR_NOT_FOUND = "MDC-CP07-001"
    CP07_TEMPLATE_NOT_FOUND = "MDC-CP07-002"
    CP07_RENDER_FAILED = "MDC-CP07-003"
    CP07_WRITE_FAILED = "MDC-CP07-004"
    CP07_INVALID_CONFIG = "MDC-CP07-005"

    # =========================================================================
    # Version Management Errors
    # =========================================================================
    VERSION_NOT_FOUND = "MDC-VER-001"
    VERSION_INVALID_NAME = "MDC-VER-002"
    VERSION_DELETE_ACTIVE = "MDC-VER-003"
    VERSION_CREATE_FAILED = "MDC-VER-004"
    VERSION_SWITCH_FAILED = "MDC-VER-005"
    VERSION_CLEANUP_FAILED = "MDC-VER-006"
    VERSION_METADATA_INVALID = "MDC-VER-007"
    VERSION_ALREADY_EXISTS = "MDC-VER-008"

    # =========================================================================
    # Index Command Errors
    # =========================================================================
    INDEX_PROJECT_NOT_FOUND = "MDC-IDX-001"
    INDEX_NEO4J_CONNECTION_FAILED = "MDC-IDX-002"
    INDEX_PARSE_FAILED = "MDC-IDX-003"
    INDEX_EMBEDDING_FAILED = "MDC-IDX-004"
    INDEX_LOCKED = "MDC-IDX-005"

    # =========================================================================
    # Utility Command Errors
    # =========================================================================
    UTIL_PROJECT_NOT_INITIALIZED = "MDC-UTIL-001"
    UTIL_VERSION_NOT_FOUND = "MDC-UTIL-002"
    UTIL_NO_ACTIVE_BRIEF = "MDC-UTIL-003"
    UTIL_INVALID_FEEDBACK_TYPE = "MDC-UTIL-004"
    UTIL_INVALID_CONFIG_KEY = "MDC-UTIL-005"
    UTIL_CONFIG_WRITE_FAILED = "MDC-UTIL-006"
    UTIL_NEO4J_CONNECTION_FAILED = "MDC-UTIL-007"
    UTIL_PIPELINE_TRIGGER_FAILED = "MDC-UTIL-008"

    # =========================================================================
    # CP01: Entity/Command/Query/Workflow Emitter Errors
    # =========================================================================
    CP01_ENTITY_NOT_FOUND = "MDC-CP01-001"
    CP01_INVALID_FIELD_TYPE = "MDC-CP01-002"
    CP01_RELATIONSHIP_TARGET_NOT_FOUND = "MDC-CP01-003"
    CP01_INVALID_LIFECYCLE_EVENT = "MDC-CP01-004"
    CP01_TEMPLATE_NOT_FOUND = "MDC-CP01-005"
    CP01_INVALID_CONSTRAINT = "MDC-CP01-006"
    CP01_MODEL_EMIT_FAILED = "MDC-CP01-007"
    CP01_RELATIONSHIP_EMIT_FAILED = "MDC-CP01-008"
    CP01_HOOK_EMIT_FAILED = "MDC-CP01-009"
    CP01_INVALID_ENUM_VALUE = "MDC-CP01-010"
    CP01_VALUE_OBJECT_NOT_FOUND = "MDC-CP01-011"
    CP01_VALUE_OBJECT_INVALID_FIELD_TYPE = "MDC-CP01-012"
    CP01_VALUE_OBJECT_INVALID_VALIDATION_RULE = "MDC-CP01-013"
    CP01_VALUE_OBJECT_TEMPLATE_NOT_FOUND = "MDC-CP01-014"
    CP01_VALUE_OBJECT_EMIT_FAILED = "MDC-CP01-015"
    CP01_VALUE_OBJECT_NESTED_REF_NOT_FOUND = "MDC-CP01-016"
    CP01_VALUE_OBJECT_METHOD_SIGNATURE_INVALID = "MDC-CP01-017"
    CP01_VALUE_OBJECT_COMPARABLE_NO_HASH = "MDC-CP01-018"
    CP01_VALUE_OBJECT_IMMUTABLE_HAS_SETTER = "MDC-CP01-019"
    CP01_VALUE_OBJECT_INVALID_TAG = "MDC-CP01-020"
    CP01_COMMAND_NOT_FOUND = "MDC-CP01-021"
    CP01_COMMAND_INVALID_INPUT = "MDC-CP01-022"
    CP01_COMMAND_GUARD_FAILED = "MDC-CP01-023"
    CP01_COMMAND_EFFECT_FAILED = "MDC-CP01-024"
    CP01_COMMAND_VALIDATION_FAILED = "MDC-CP01-025"
    CP01_COMMAND_TEMPLATE_NOT_FOUND = "MDC-CP01-026"
    CP01_COMMAND_EMIT_FAILED = "MDC-CP01-027"
    CP01_QUERY_NOT_FOUND = "MDC-CP01-028"
    CP01_QUERY_INVALID_FILTER = "MDC-CP01-029"
    CP01_QUERY_INVALID_PAGINATION = "MDC-CP01-030"
    CP01_QUERY_INVALID_PROJECTION = "MDC-CP01-031"
    CP01_QUERY_TEMPLATE_NOT_FOUND = "MDC-CP01-032"
    CP01_QUERY_EMIT_FAILED = "MDC-CP01-033"
    CP01_QUERY_HANDLER_INVALID = "MDC-CP01-034"
    CP01_QUERY_SCHEMA_INVALID = "MDC-CP01-035"
    CP01_WORKFLOW_NOT_FOUND = "MDC-CP01-036"
    CP01_WORKFLOW_INVALID_STATE = "MDC-CP01-037"
    CP01_WORKFLOW_INVALID_TRANSITION = "MDC-CP01-038"
    CP01_WORKFLOW_GUARD_FAILED = "MDC-CP01-039"
    CP01_WORKFLOW_EFFECT_FAILED = "MDC-CP01-040"
    CP01_WORKFLOW_ALREADY_IN_STATE = "MDC-CP01-041"
    CP01_WORKFLOW_INVALID_EVENT = "MDC-CP01-042"
    CP01_WORKFLOW_COMPENSATION_FAILED = "MDC-CP01-043"
    CP01_WORKFLOW_EVENT_STORE_ERROR = "MDC-CP01-044"
    CP01_WORKFLOW_SYNC_FAILED = "MDC-CP01-045"
    CP01_ENTITY_PARSER_ERROR = "MDC-CP01-046"
    CP01_ENTITY_INVALID_FIELD = "MDC-CP01-047"
    CP01_ENTITY_INVALID_RELATIONSHIP = "MDC-CP01-048"
    CP01_ENTITY_INVALID_CONSTRAINT = "MDC-CP01-049"
    CP01_ENTITY_INVALID_LIFECYCLE = "MDC-CP01-050"
    CP01_ENTITY_EMIT_FAILED = "MDC-CP01-051"
    CP01_GUARD_TENANT_MISSING = "MDC-CP01-052"
    CP01_GUARD_TENANT_VIOLATION = "MDC-CP01-053"
    CP01_GUARD_USER_NOT_AUTHENTICATED = "MDC-CP01-054"
    CP01_GUARD_PERMISSION_DENIED = "MDC-CP01-055"
    CP01_GUARD_RATE_LIMIT_EXCEEDED = "MDC-CP01-056"
    CP01_GUARD_KYC_NOT_VERIFIED = "MDC-CP01-057"
    CP01_GUARD_AML_SCREENING_FAILED = "MDC-CP01-058"
    CP01_GUARD_HIPAA_NO_CLEARANCE = "MDC-CP01-059"
    CP01_GUARD_GDPR_NO_CONSENT = "MDC-CP01-060"
    CP01_GUARD_PCI_RESTRICTED = "MDC-CP01-061"
    CP01_TRANSACTION_NOT_ACTIVE = "MDC-CP01-062"
    CP01_TRANSACTION_COMMIT_FAILED = "MDC-CP01-063"
    CP01_TRANSACTION_ROLLBACK_FAILED = "MDC-CP01-064"
    CP01_TRANSACTION_ALREADY_COMMITTED = "MDC-CP01-065"
    CP01_TRANSACTION_ALREADY_ROLLED_BACK = "MDC-CP01-066"
    CP01_GUARD_COMPLIANCE_LOG_FAILED = "MDC-CP01-068"
    CP01_GUARD_EXTERNAL_API_TIMEOUT = "MDC-CP01-069"
    CP01_GUARD_CLAIMS_VALIDATION_FAILED = "MDC-CP01-070"
    CP01_GUARD_UNDERWRITING_FAILED = "MDC-CP01-071"
    CP01_GUARD_DOUBLE_ENTRY_IMBALANCE = "MDC-CP01-072"
    CP01_GUARD_PHI_NOT_ENCRYPTED = "MDC-CP01-073"
    CP01_GUARD_MINIMUM_NECESSARY_VIOLATION = "MDC-CP01-074"
    CP01_GUARD_FRAUD_VELOCITY_EXCEEDED = "MDC-CP01-075"
    CP01_GUARD_FRAUD_AMOUNT_THRESHOLD = "MDC-CP01-076"
    CP01_GUARD_FRAUD_PATTERN_ANOMALY = "MDC-CP01-077"
    CP01_GUARD_FRAUD_EXTERNAL_BLOCKED = "MDC-CP01-078"
    CP01_GUARD_FRAUD_EXTERNAL_TIMEOUT = "MDC-CP01-079"
    CP01_GUARD_SAFETY_EQUIPMENT_UNSAFE = "MDC-CP01-080"
    CP01_GUARD_SAFETY_PERSONNEL_UNCERTIFIED = "MDC-CP01-081"
    CP01_GUARD_SAFETY_PROCESS_NON_COMPLIANT = "MDC-CP01-082"
    CP01_GUARD_SAFETY_HAZARD_DETECTED = "MDC-CP01-083"
    CP01_GUARD_CLAIMS_NOT_COVERED = "MDC-CP01-084"
    CP01_GUARD_CLAIMS_OUTSIDE_PERIOD = "MDC-CP01-085"
    CP01_GUARD_CLAIMS_EXCEEDS_LIMIT = "MDC-CP01-086"
    CP01_GUARD_CLAIMS_EXCLUDED = "MDC-CP01-087"
    CP01_EFFECT_DOUBLE_ENTRY_MISMATCH = "MDC-CP01-088"
    CP01_EFFECT_LEDGER_ENTRY_FAILED = "MDC-CP01-089"
    CP01_EFFECT_TRANSACTION_IMMUTABLE = "MDC-CP01-090"
    CP01_EFFECT_INSUFFICIENT_STOCK = "MDC-CP01-091"
    CP01_EFFECT_RESERVATION_EXPIRED = "MDC-CP01-092"
    CP01_EFFECT_RESERVATION_NOT_FOUND = "MDC-CP01-093"
    CP01_EFFECT_PAYMENT_FAILED = "MDC-CP01-094"
    CP01_EFFECT_PAYMENT_GATEWAY_ERROR = "MDC-CP01-095"
    CP01_EFFECT_PAYMENT_DUPLICATE = "MDC-CP01-096"
    CP01_EFFECT_INVALID_STATE_TRANSITION = "MDC-CP01-097"
    CP01_EFFECT_CLINICAL_CHECK_FAILED = "MDC-CP01-098"
    CP01_EFFECT_PROVIDER_NOT_CERTIFIED = "MDC-CP01-099"

    # =========================================================================
    # CP02: Multi-Tenant Architecture Errors
    # =========================================================================
    CP02_TENANT_MODE_INVALID = "MDC-CP02-001"
    CP02_TENANT_ID_MISSING = "MDC-CP02-002"
    CP02_TENANT_MISMATCH = "MDC-CP02-003"
    CP02_TENANT_CONTEXT_NOT_SET = "MDC-CP02-004"
    CP02_TENANT_FILTER_MISSING = "MDC-CP02-005"

    # =========================================================================
    # CP03: Authentication & Authorization Errors
    # =========================================================================
    CP03_AUTH_PROVIDER_NOT_FOUND = "MDC-CP03-001"
    CP03_TOKEN_EXPIRED = "MDC-CP03-002"
    CP03_TOKEN_INVALID = "MDC-CP03-003"
    CP03_CREDENTIALS_INVALID = "MDC-CP03-004"
    CP03_AUTH_CONFIG_INVALID = "MDC-CP03-005"
    CP03_JWT_SECRET_MISSING = "MDC-CP03-006"

    # =========================================================================
    # CP04: RBAC & Policy Engine Errors
    # =========================================================================
    CP04_ROLE_NOT_FOUND = "MDC-CP04-001"
    CP04_PERMISSION_NOT_FOUND = "MDC-CP04-002"
    CP04_POLICY_NOT_FOUND = "MDC-CP04-003"
    CP04_ROLE_BINDING_INVALID = "MDC-CP04-004"
    CP04_POLICY_EVALUATION_FAILED = "MDC-CP04-005"
    CP04_PERMISSION_DENIED = "MDC-CP04-006"
    CP04_POLICY_SYNTAX_ERROR = "MDC-CP04-007"
    CP04_ROLE_CYCLE_DETECTED = "MDC-CP04-008"

    # =========================================================================
    # CP05: Event Emitter Errors
    # =========================================================================
    EVT_BUS_NOT_INITIALIZED = "MDC-EVT-001"
    EVT_SUBSCRIBER_NOT_FOUND = "MDC-EVT-002"
    EVT_SCHEMA_VALIDATION_FAILED = "MDC-EVT-003"
    EVT_OUTBOX_WRITE_FAILED = "MDC-EVT-004"
    EVT_PUBLISHER_NOT_FOUND = "MDC-EVT-005"
    EVT_HANDLER_FAILED = "MDC-EVT-006"
    EVT_TOPIC_INVALID = "MDC-EVT-007"
    EVT_MESSAGE_SERIALIZATION_FAILED = "MDC-EVT-008"
    EVT_DEAD_LETTER_FAILED = "MDC-EVT-009"
    EVT_TENANT_ISOLATION_VIOLATION = "MDC-EVT-010"
    
    # =========================================================================
    # CP06: API Gateway & Service Mesh Errors
    # =========================================================================
    # Route validation errors (001-005)
    CP06_ROUTE_NOT_FOUND = "MDC-CP06-001"
    CP06_INVALID_METHOD = "MDC-CP06-002"
    CP06_DUPLICATE_PATH = "MDC-CP06-003"
    CP06_INVALID_AUTH_CONFIG = "MDC-CP06-004"
    CP06_HANDLER_NOT_FOUND = "MDC-CP06-005"
    # Gateway configuration errors (006-010)
    CP06_GATEWAY_CONFIG_INVALID = "MDC-CP06-006"
    CP06_SERVICE_URL_INVALID = "MDC-CP06-007"
    CP06_ROUTE_BIND_FAILED = "MDC-CP06-008"
    CP06_PLUGIN_CONFIG_INVALID = "MDC-CP06-009"
    CP06_UPSTREAM_EMPTY = "MDC-CP06-010"
    # Service mesh errors (011-015)
    CP06_MESH_CONFIG_INVALID = "MDC-CP06-011"
    CP06_HEALTH_CHECK_FAILED = "MDC-CP06-012"
    CP06_CONNECT_PROXY_ERROR = "MDC-CP06-013"
    CP06_SERVICE_REG_FAILED = "MDC-CP06-014"
    CP06_TLS_CONFIG_INVALID = "MDC-CP06-015"
    # Kong/Consul integration errors (016-020)
    CP06_KONG_YAML_ERROR = "MDC-CP06-016"
    CP06_CONSUL_HCL_ERROR = "MDC-CP06-017"
    CP06_PLUGIN_NOT_FOUND = "MDC-CP06-018"
    CP06_RATE_LIMIT_EXCEEDED = "MDC-CP06-019"
    CP06_CIRCUIT_BREAKER_OPEN = "MDC-CP06-020"

    # =========================================================================
    # CP08: Database & Data Access Layer Errors
    # =========================================================================
    CP08_EMPTY_NAME = "MDC-CP08-001"
    CP08_INVALID_COLUMN_TYPE = "MDC-CP08-002"
    CP08_DUPLICATE_COLUMN_NAME = "MDC-CP08-003"
    CP08_DUPLICATE_TABLE_NAME = "MDC-CP08-004"
    CP08_DSL_PARSE_ERROR = "MDC-CP08-005"
    CP08_MISSING_DATASOURCE = "MDC-CP08-006"
    CP08_CIRCULAR_FOREIGN_KEY = "MDC-CP08-007"
    CP08_MISSING_PRIMARY_KEY = "MDC-CP08-008"
    CP08_MIGRATION_ERROR = "MDC-CP08-009"
    CP08_RUNTIME_DATASOURCE_ERROR = "MDC-CP08-010"

    # =========================================================================
    # CP09: Caching & Performance Layer Errors
    # =========================================================================
    CP09_BACKEND_INVALID = "MDC-CP09-001"
    CP09_TTL_INVALID = "MDC-CP09-002"
    CP09_KEY_EMPTY = "MDC-CP09-003"
    CP09_PATTERN_INVALID = "MDC-CP09-004"
    CP09_SERIALIZATION_FAILED = "MDC-CP09-005"

    # =========================================================================
    # CP10: Search & Indexing Errors
    # =========================================================================
    CP10_EMPTY_INDEX_NAME = "MDC-CP10-001"
    CP10_INVALID_PROVIDER = "MDC-CP10-002"
    CP10_SYNC_STRATEGY_INVALID = "MDC-CP10-003"
    CP10_INVALID_COLUMN_TYPE = "MDC-CP10-004"
    CP10_INDEX_CREATE_FAILED = "MDC-CP10-005"
    CP10_MISSING_VECTOR_COLUMN = "MDC-CP10-006"
    CP10_INVALID_VECTOR_DIMENSIONS = "MDC-CP10-007"
    CP10_MISSING_GEO_COLUMN = "MDC-CP10-008"
    CP10_INVALID_GEO_TYPE = "MDC-CP10-009"
    CP10_MISSING_FACET_SOURCE = "MDC-CP10-010"

    # =========================================================================
    # CP11: File Storage & Media Processing Errors
    # =========================================================================
    CP11_EMPTY_PROFILE_NAME = "MDC-CP11-001"
    CP11_INVALID_BACKEND_TYPE = "MDC-CP11-002"
    CP11_EMPTY_BUCKET_NAME = "MDC-CP11-003"
    CP11_INVALID_CONTENT_TYPE = "MDC-CP11-004"
    CP11_FILE_SIZE_EXCEEDED = "MDC-CP11-005"
    CP11_INVALID_EXTENSION = "MDC-CP11-006"
    CP11_DSL_PARSE_ERROR = "MDC-CP11-007"
    CP11_MISSING_POLICY = "MDC-CP11-008"
    CP11_TRANSFORM_INVALID_PARAM = "MDC-CP11-009"
    CP11_PROVIDER_NOT_FOUND = "MDC-CP11-010"

    # =========================================================================
    # CP12: Notification & Communication Errors
    # =========================================================================
    CP12_NOTIFICATION_CHANNEL_NOT_SUPPORTED = "MDC-CP12-001"
    CP12_NOTIFICATION_TEMPLATE_NOT_FOUND = "MDC-CP12-002"
    CP12_NOTIFICATION_TEMPLATE_RENDER_FAILED = "MDC-CP12-003"
    CP12_NOTIFICATION_PROVIDER_NOT_CONFIGURED = "MDC-CP12-004"
    CP12_NOTIFICATION_DISPATCH_FAILED = "MDC-CP12-005"
    CP12_NOTIFICATION_RATE_LIMIT_EXCEEDED = "MDC-CP12-006"
    CP12_NOTIFICATION_INVALID_RECIPIENT = "MDC-CP12-007"

    # =========================================================================
    # CP13: Background Job & Workflow Errors
    # =========================================================================
    CP13_JOB_SCHEDULE_FAILED = "MDC-CP13-001"
    CP13_JOB_NOT_FOUND = "MDC-CP13-002"
    CP13_WORKFLOW_INVALID_TRANSITION = "MDC-CP13-003"
    CP13_WORKFLOW_GUARD_FAILED = "MDC-CP13-004"
    CP13_WORKFLOW_EFFECT_FAILED = "MDC-CP13-005"
    CP13_WORKFLOW_STATE_MACHINE_ERROR = "MDC-CP13-006"
    CP13_SCHEDULE_POLICY_INVALID = "MDC-CP13-007"
    CP13_JOB_RETRY_EXHAUSTED = "MDC-CP13-008"
    CP13_JOB_SPEC_INVALID = "MDC-CP13-009"
    CP13_WORKER_CONFIG_INVALID = "MDC-CP13-010"
    CP13_DEADLOCK_CONFIG_INVALID = "MDC-CP13-011"

    # =========================================================================
    # CP14: Audit Trail & Compliance Errors
    # =========================================================================
    CP14_AUDIT_EMPTY_ID = "MDC-CP14-001"
    CP14_AUDIT_INVALID_ACTION = "MDC-CP14-002"
    CP14_AUDIT_INVALID_ACTOR_TYPE = "MDC-CP14-003"
    CP14_AUDIT_INVALID_LEVEL = "MDC-CP14-004"
    CP14_AUDIT_RETENTION_INVALID = "MDC-CP14-005"
    CP14_AUDIT_ARCHIVE_EXCEEDS_RETENTION = "MDC-CP14-006"
    CP14_AUDIT_CONTROL_INVALID_STANDARD = "MDC-CP14-007"
    CP14_AUDIT_CONTROL_INVALID_TYPE = "MDC-CP14-008"
    CP14_AUDIT_CONTROL_INVALID_ENFORCEMENT = "MDC-CP14-009"
    CP14_AUDIT_HASH_VERIFICATION_FAILED = "MDC-CP14-010"

    # =========================================================================
    # CP15: Observability Stack Generator Errors
    # =========================================================================
    CP15_EMPTY_METRIC_NAME = "MDC-CP15-001"
    CP15_INVALID_METRIC_TYPE = "MDC-CP15-002"
    CP15_INVALID_LOG_LEVEL = "MDC-CP15-003"
    CP15_METRIC_RETENTION_INVALID = "MDC-CP15-004"
    CP15_DUPLICATE_METRIC_NAME = "MDC-CP15-005"
    CP15_EMPTY_LOG_MESSAGE = "MDC-CP15-006"
    CP15_EMPTY_TRACE_NAME = "MDC-CP15-007"
    CP15_INVALID_TRACE_FORMAT = "MDC-CP15-008"
    CP15_LOG_HASH_VERIFICATION_FAILED = "MDC-CP15-009"
    CP15_OBSERVABILITY_PARSE_ERROR = "MDC-CP15-010"

    # =========================================================================
    # CP16: API & System Monitoring Generator Errors
    # =========================================================================
    CP16_EMPTY_DASHBOARD_NAME = "MDC-CP16-001"
    CP16_INVALID_ALERT_SEVERITY = "MDC-CP16-002"
    CP16_INVALID_ALERT_CONDITION = "MDC-CP16-003"
    CP16_INVALID_SLI_METRIC_TYPE = "MDC-CP16-004"
    CP16_ALERT_EVALUATION_INTERVAL_INVALID = "MDC-CP16-005"
    CP16_DUPLICATE_ALERT_RULE = "MDC-CP16-006"
    CP16_EMPTY_ALERT_NAME = "MDC-CP16-007"
    CP16_INVALID_SLI_TARGET = "MDC-CP16-008"
    CP16_EMPTY_PANEL_NAME = "MDC-CP16-009"
    CP16_MONITORING_PARSE_ERROR = "MDC-CP16-010"
    CP16_EMPTY_SLI_NAME = "MDC-CP16-011"
    CP16_EMPTY_HEALTH_CHECK_NAME = "MDC-CP16-012"
    CP16_INVALID_HEALTH_CHECK_PATH = "MDC-CP16-013"
    CP16_EMPTY_ESCALATION_NAME = "MDC-CP16-014"
    CP16_INVALID_NOTIFICATION_CHANNEL_TYPE = "MDC-CP16-015"
    CP16_EMPTY_SLO_NAME = "MDC-CP16-016"
    CP16_INVALID_SLO_TARGET = "MDC-CP16-017"

    # =========================================================================
    # CP17: Business Intelligence & Analytics Generator Errors
    # =========================================================================
    CP17_EMPTY_MODEL_NAME = "MDC-CP17-001"
    CP17_INVALID_AGGREGATION_TYPE = "MDC-CP17-002"
    CP17_INVALID_REPORT_FREQUENCY = "MDC-CP17-003"
    CP17_INVALID_VISUALIZATION_TYPE = "MDC-CP17-004"
    CP17_DATA_FRESHNESS_VIOLATED = "MDC-CP17-005"
    CP17_DUPLICATE_ANALYTICS_MODEL = "MDC-CP17-006"
    CP17_EMPTY_REPORT_NAME = "MDC-CP17-007"
    CP17_INVALID_SOURCE_TYPE = "MDC-CP17-008"
    CP17_EMPTY_DASHBOARD_NAME = "MDC-CP17-009"
    CP17_ANALYTICS_PARSE_ERROR = "MDC-CP17-010"
    CP17_INVALID_STALE_SECONDS = "MDC-CP17-011"
    CP17_INVALID_REFRESH_INTERVAL = "MDC-CP17-012"
    CP17_MISSING_NEXT_RUN = "MDC-CP17-013"
    CP17_INVALID_OUTPUT_FORMAT = "MDC-CP17-014"
    CP17_DUPLICATE_MODEL_NAME = "MDC-CP17-015"

    # =========================================================================
    # CP18: Frontend Framework Generator Errors
    # =========================================================================
    CP18_EMPTY_APP_NAME = "MDC-CP18-001"
    CP18_INVALID_FRAMEWORK = "MDC-CP18-002"
    CP18_INVALID_STATE_STORE = "MDC-CP18-003"
    CP18_DUPLICATE_ROUTE = "MDC-CP18-004"
    CP18_INVALID_ROUTE_PATH = "MDC-CP18-005"
    CP18_INVALID_UI_FRAMEWORK = "MDC-CP18-006"
    CP18_INVALID_LAYOUT = "MDC-CP18-007"
    CP18_EMPTY_ROUTE_COMPONENT = "MDC-CP18-008"
    CP18_FRONTEND_PARSE_ERROR = "MDC-CP18-009"
    CP18_INVALID_ROUTER_STRATEGY = "MDC-CP18-010"

    # =========================================================================
    # CP19: UI Component Generator Errors
    # =========================================================================
    CP19_INVALID_COMPONENT_TYPE = "MDC-CP19-001"
    CP19_MISSING_FORM_BINDING = "MDC-CP19-002"
    CP19_EMPTY_TABLE_COLUMNS = "MDC-CP19-003"
    CP19_INVALID_FIELD_TYPE = "MDC-CP19-004"
    CP19_SCHEMA_VALIDATION_FAILED = "MDC-CP19-005"

    # =========================================================================
    # CP20: API Client & Integration Generator Errors
    # =========================================================================
    CP20_OPENAPI_PARSE_ERROR = "MDC-CP20-001"
    CP20_TYPE_MISMATCH = "MDC-CP20-002"
    CP20_MISSING_AUTH_INJECT = "MDC-CP20-003"
    CP20_BRIDGE_CONFIG_INVALID = "MDC-CP20-004"
    CP20_ENDPOINT_DUPLICATE = "MDC-CP20-005"

    # =========================================================================
    # CP21: Authentication UI Generator Errors
    # =========================================================================
    CP21_INVALID_UI_FRAMEWORK = "MDC-CP21-001"
    CP21_TEMPLATE_NOT_FOUND = "MDC-CP21-002"
    CP21_RENDER_FAILED = "MDC-CP21-003"
    CP21_MISSING_PAGE_CONFIG = "MDC-CP21-004"
    CP21_INVALID_SESSION_TIMEOUT = "MDC-CP21-005"

    # =========================================================================
    # CP22: Real-time UI Generator Errors
    # =========================================================================
    CP22_CHANNEL_NOT_FOUND = "MDC-CP22-001"
    CP22_INVALID_TRANSPORT = "MDC-CP22-002"
    CP22_TEMPLATE_NOT_FOUND = "MDC-CP22-003"
    CP22_RENDER_FAILED = "MDC-CP22-004"
    CP22_TENANT_ISOLATION_VIOLATION = "MDC-CP22-005"
    CP22_INVALID_WIDGET_TYPE = "MDC-CP22-006"
    CP22_EVENT_PARSE_FAILED = "MDC-CP22-007"

    # =========================================================================
    # CP23: Testing Framework Generator Errors
    # =========================================================================
    CP23_EMPTY_TEST_ID = "MDC-CP23-001"
    CP23_INVALID_TEST_TYPE = "MDC-CP23-002"
    CP23_MISSING_TEST_TARGET = "MDC-CP23-003"
    CP23_INVALID_ASSERTION = "MDC-CP23-004"
    CP23_TEMPLATE_NOT_FOUND = "MDC-CP23-005"
    CP23_RENDER_FAILED = "MDC-CP23-006"
    CP23_INVALID_COVERAGE_THRESHOLD = "MDC-CP23-007"
    CP23_INVALID_FRAMEWORK = "MDC-CP23-008"
    CP23_DSL_PARSE_ERROR = "MDC-CP23-009"
    CP23_DUPLICATE_TEST_ID = "MDC-CP23-010"

    # =========================================================================
    # CP24: Code Quality & Security Scanner Generator Errors
    # =========================================================================
    CP24_QUALITY_GATE_FAILED = "MDC-CP24-001"
    CP24_SECURITY_SCAN_FAILED = "MDC-CP24-002"
    CP24_PROFILE_INVALID = "MDC-CP24-003"
    CP24_SCAN_CONFIG_INVALID = "MDC-CP24-004"
    CP24_TEMPLATE_NOT_FOUND = "MDC-CP24-005"
    CP24_RENDER_FAILED = "MDC-CP24-006"
    CP24_DSL_PARSE_ERROR = "MDC-CP24-007"
    CP24_EMPTY_PROFILE_NAME = "MDC-CP24-008"
    CP24_INVALID_STACK = "MDC-CP24-009"
    CP24_REPORT_WRITE_FAILED = "MDC-CP24-010"

    # =========================================================================
    # CP25: Performance Testing Generator Errors
    # =========================================================================
    CP25_EMPTY_SCENARIO_ID = "MDC-CP25-001"
    CP25_MISSING_SCENARIO_TARGET = "MDC-CP25-002"
    CP25_INVALID_SCENARIO_TYPE = "MDC-CP25-003"
    CP25_INVALID_CONCURRENCY = "MDC-CP25-004"
    CP25_INVALID_DURATION = "MDC-CP25-005"
    CP25_THRESHOLD_INVALID = "MDC-CP25-006"
    CP25_DSL_PARSE_ERROR = "MDC-CP25-007"
    CP25_TEMPLATE_NOT_FOUND = "MDC-CP25-008"
    CP25_RENDER_FAILED = "MDC-CP25-009"
    CP25_INVALID_STACK = "MDC-CP25-010"
    CP25_EMPTY_SUITE_NAME = "MDC-CP25-011"
    CP25_DUPLICATE_SCENARIO_ID = "MDC-CP25-012"
    CP25_BASELINE_SAVE_FAILED = "MDC-CP25-013"
    CP25_BASELINE_NOT_FOUND = "MDC-CP25-014"
    CP25_INVALID_METRIC_VALUE = "MDC-CP25-015"

    # =========================================================================
    # CP26: Documentation Generator Errors
    # =========================================================================
    CP26_EMPTY_PORTAL_NAME = "MDC-CP26-001"
    CP26_MISSING_SECTION_TITLE = "MDC-CP26-002"
    CP26_INVALID_PORTAL_TYPE = "MDC-CP26-003"
    CP26_INVALID_API_VERSION = "MDC-CP26-004"
    CP26_DSL_PARSE_ERROR = "MDC-CP26-005"
    CP26_TEMPLATE_NOT_FOUND = "MDC-CP26-006"
    CP26_RENDER_FAILED = "MDC-CP26-007"
    CP26_INVALID_STACK = "MDC-CP26-008"
    CP26_DUPLICATE_SECTION_ID = "MDC-CP26-009"
    CP26_EMPTY_SECTION_PATH = "MDC-CP26-010"
    CP26_INVALID_NAV_ENTRY = "MDC-CP26-011"
    CP26_SECTION_SOURCE_INVALID = "MDC-CP26-012"

    # =========================================================================
    # CP53: Domain Pack Runtime Bridge Errors
    # =========================================================================
    CP53_BRIDGE_CAPABILITY_INVALID = "MDC-CP53-001"
    CP53_DP_NOT_REGISTERED = "MDC-CP53-002"
    CP53_DUPLICATE_DP_ID = "MDC-CP53-003"
    CP53_INVALID_BINDING_ID = "MDC-CP53-004"
    CP53_INVOKER_CONFIG_EMPTY = "MDC-CP53-005"


class ExitCode(Enum):
    """
    Exit codes cho CLI commands.

    Theo standard Unix conventions:
    - 0: Success
    - 1-125: Errors from command
    - 126: Command invoked cannot execute
    - 127: Command not found
    - 128+n: Fatal error signal

    Midicoder exit codes:
    - 0: Success
    - 1: Generic Error
    - 2: Bad Arguments
    - 3: File Not Found
    - 4: Permission Denied
    - 5: Config Error
    - 6: Command Not Found
    - 7: Already Initialized
    - 130: Interrupt (Ctrl+C)
    """

    SUCCESS = 0
    GENERIC_ERROR = 1
    BAD_ARGUMENTS = 2
    FILE_NOT_FOUND = 3
    PERMISSION_DENIED = 4
    CONFIG_ERROR = 5
    COMMAND_NOT_FOUND = 6
    ALREADY_INITIALIZED = 7
    INTERRUPT = 130

    @classmethod
    def get_description(cls, code: int) -> str:
        """
        Lấy mô tả tiếng Việt cho exit code.

        Args:
            code: Exit code integer

        Returns:
            Mô tả tiếng Việt của exit code
        """
        descriptions = {
            0: "Thành công",
            1: "Lỗi không xác định",
            2: "Lỗi arguments CLI",
            3: "File/thư mục không tìm thấy",
            4: "Không có quyền truy cập",
            5: "Lỗi cấu hình",
            6: "Command không tồn tại",
            7: "Project đã được khởi tạo",
            130: "Người dùng hủy bỏ (Ctrl+C)",
        }
        return descriptions.get(code, f"Exit code: {code}")


@dataclass
class MidicoderError(RuntimeError):
    """
    Exception chuẩn hóa của hệ thống, luôn kèm mã lỗi và context.

    Attributes:
        code: ErrorCode từ enum để dễ dàng categorization
        message: Message tiếng Việt mô tả lỗi
        context: Context thông tin cho debugging (file, line, node_id, etc.)
        cause: Nguyên nhân gốc (nếu có)
        suggestions: Gợi ý khắc phục (optional)

    Ví dụ:
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
            context={"path": "dsl/entities.yaml"},
            suggestions=["Kiểm tra đường dẫn file", "Đảm bảo file tồn tại"]
        )
        print(error)
        # Output: [MDC-DSL-002] Không tìm thấy file DSL (path='dsl/entities.yaml')
    """

    code: ErrorCode
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    cause: Optional[Exception] = None
    suggestions: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        """
        Format error message với context.

        Returns:
            Formatted error string với code, message, và context
        """
        parts = [f"[{self.code.value}] {self.message}"]

        if self.context:
            items = ", ".join(f"{key}={value!r}" for key, value in sorted(self.context.items()))
            parts.append(f"({items})")

        if self.cause:
            parts.append(f"(Caused by: {self.cause})")

        return " ".join(parts)

    def __repr__(self) -> str:
        """Debug representation của error."""
        return f"MidicoderError(code={self.code.value!r}, message={self.message!r}, context={self.context!r})"

    def get_full_message(self) -> str:
        """
        Lấy full message với stack trace và suggestions.

        Returns:
            Complete error message với traceback và suggestions
        """
        lines = [str(self)]

        if self.cause and isinstance(self.cause, Exception):
            lines.append("")
            lines.append("Nguyên nhân gốc:")
            lines.extend(traceback.format_exception(type(self.cause), self.cause, self.cause.__traceback__))

        if self.suggestions:
            lines.append("")
            lines.append("Gợi ý khắc phục:")
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"  {i}. {suggestion}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển error sang dict cho serialization.

        Returns:
            Dictionary representation của error
        """
        return {
            "code": self.code.value,
            "message": self.message,
            "context": self.context,
            "has_cause": self.cause is not None,
            "suggestions": self.suggestions,
        }


class MidicoderErrorManager:
    """
    Factory quản lý template lỗi và tạo exception tái sử dụng toàn source.

    Cung cấp:
    - create(): Tạo error object mà không throw
    - raise_error(): Tạo và throw error ngay
    - wrap_exception(): Wrap general exception thành MidicoderError

    Ví dụ:
        # Create error
        error = EM.create(ErrorCode.DSL_FILE_NOT_FOUND, path="test.yaml")

        # Raise error
        EM.raise_error(ErrorCode.DSL_FILE_NOT_FOUND, path="test.yaml")

        # Wrap exception
        try:
            yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise EM.wrap_exception(e, ErrorCode.DSL_YAML_PARSE_ERROR, file_path="test.yaml")
    """

    _TEMPLATES: dict[ErrorCode, str] = {
        # CLI Errors
        ErrorCode.NO_CURRENT_VERSION: "Không có version hiện tại. Hãy chạy `version create` trước.",

        # Brief Errors
        ErrorCode.MASTER_BRIEF_MISSING: "Thiếu `master-brief.md` nên không thể biên dịch.",

        # Contract Errors
        ErrorCode.CONTRACT_GRAPH_NOT_FOUND: "Không tìm thấy contract graph để biên dịch.",
        ErrorCode.CONTRACT_GRAPH_VALIDATION_FAILED: "Contract graph không hợp lệ theo các ràng buộc compile-time.",
        ErrorCode.CONTRACT_COMPILE_FAILED: "Compile contract graph thất bại.",
        ErrorCode.DETERMINISTIC_HASH_GATE_FAILED: "Deterministic hash gate thất bại cho cùng một contract graph.",
        ErrorCode.CONTRACT_PACK_NOT_FOUND: "Không tìm thấy contract pack trong builtin registry.",
        ErrorCode.CONTRACT_GRAPH_READ_FAILED: "Không đọc được contract graph từ đĩa.",
        ErrorCode.CONTRACT_GRAPH_SCHEMA_INVALID: "Contract graph không đúng schema mong đợi.",
        ErrorCode.CAPABILITY_PARAMS_INVALID: "Params của capability instance không hợp lệ.",
        ErrorCode.CAPABILITY_TYPE_UNKNOWN: "Capability type không được hỗ trợ.",
        ErrorCode.CAPABILITY_OBLIGATION_UNSATISFIED: "Obligation không được satisfy trong capability.",
        ErrorCode.CAPABILITY_EXPAND_FAILED: "Không thể expand macro capability thành core capabilities.",

        # DSL v1 Errors
        ErrorCode.DSL_LOAD_FAILED: "Không thể load DSL từ path đã chỉ định.",
        ErrorCode.DSL_FILE_NOT_FOUND: "Không tìm thấy file DSL tại path.",
        ErrorCode.DSL_YAML_PARSE_ERROR: "Lỗi YAML parsing trong file DSL.",
        ErrorCode.DSL_INVALID_NODE_KIND: "Node kind không hợp lệ trong DSL.",
        ErrorCode.DSL_MISSING_REQUIRED_FIELD: "Thiếu field bắt buộc trong node.",
        ErrorCode.DSL_INVALID_CATALOG_VALUE: "Giá trị không nằm trong catalog cho phép.",
        ErrorCode.DSL_DUPLICATE_NODE_ID: "Node ID trùng lặp trong DSL.",
        ErrorCode.DSL_INVALID_REFERENCE: "Reference đến node không tồn tại.",

        # Validation Errors
        ErrorCode.VALIDATION_FAILED: "Validation thất bại với errors và warnings.",
        ErrorCode.CONSTRAINT_VIOLATION: "Constraint violation trong node.",
        ErrorCode.CROSS_NODE_VALIDATION_FAILED: "Cross-node validation thất bại.",

        # Dependency Errors
        ErrorCode.DEPENDENCY_CYCLE_DETECTED: "Phát hiện cycle trong dependency graph.",
        ErrorCode.MISSING_DEPENDENCY: "Thiếu dependency cần thiết.",

        # Runtime Errors
        ErrorCode.GENERATION_FAILED: "Code generation thất bại.",
        ErrorCode.TEMPLATE_RENDER_FAILED: "Template rendering thất bại.",
        ErrorCode.FILE_WRITE_FAILED: "Không thể ghi file output.",

        # Config Errors
        ErrorCode.CONFIG_READ_FAILED: "Không thể đọc config file.",
        ErrorCode.CONFIG_WRITE_FAILED: "Không thể lưu config file.",
        ErrorCode.CONFIG_FORMAT_INVALID: "Config file không đúng format.",
        ErrorCode.CONFIG_KEY_NOT_FOUND: "Config key không tồn tại.",
        ErrorCode.CONFIG_VALUE_INVALID: "Config value không hợp lệ.",

        # Database Errors
        ErrorCode.DB_CONNECTION_FAILED: "Không thể kết nối đến database.",
        ErrorCode.DB_SCHEMA_ERROR: "Lỗi schema database.",
        ErrorCode.DB_CONSTRAINT_VIOLATION: "Vi phạm ràng buộc database.",
        ErrorCode.DB_TRANSACTION_FAILED: "Giao dịch database thất bại.",
        ErrorCode.DB_TIMEOUT: "Hết thời gian chờ database.",
        ErrorCode.DB_FILE_CORRUPTED: "File database bị hỏng.",
        ErrorCode.DB_PERMISSION_DENIED: "Không có quyền truy cập database.",

        # IR/MIR Build Errors
        ErrorCode.MIR_GRAPH_NOT_FOUND: "Không tìm thấy Capability Graph trong artifacts.",
        ErrorCode.MIR_DSL_PARSE_FAILED: "DSL parsing thất bại.",
        ErrorCode.MIR_BUILD_FAILED: "MIR build thất bại.",
        ErrorCode.MIR_VALIDATION_FAILED: "MIR validation thất bại.",
        ErrorCode.MIR_SAVE_FAILED: "Cannot save MIR to artifacts.",

        # Code Generation Errors
        ErrorCode.CODE_MIR_NOT_FOUND: "Không tìm thấy MIR trong artifacts. Hãy chạy `midicoder ir build` trước.",
        ErrorCode.CODE_PLAN_NOT_FOUND: "Không tìm thấy implementation plan. Hãy chạy `midicoder code plan` trước.",
        ErrorCode.CODE_PLAN_CREATE_FAILED: "Không thể tạo implementation plan từ MIR.",
        ErrorCode.CODE_GENERATION_FAILED: "Code generation thất bại.",
        ErrorCode.CODE_APPLY_FAILED: "Không thể apply code vào target directory.",
        ErrorCode.CODE_FILE_CONFLICT: "File conflict khi apply code.",
        ErrorCode.CODE_TEMPLATE_NOT_FOUND: "Không tìm thấy template cho code generation.",
        ErrorCode.CODE_OUTPUT_DIR_ERROR: "Lỗi khi tạo output directory.",

        # Preview Errors
        ErrorCode.PREVIEW_DOCKER_NOT_INSTALLED: "Docker không được cài đặt. Vui lòng cài đặt Docker Desktop.",
        ErrorCode.PREVIEW_DOCKER_NOT_RUNNING: "Docker daemon không chạy. Vui lòng start Docker Desktop.",
        ErrorCode.PREVIEW_COMPOSE_FILE_NOT_FOUND: "File docker-compose.yml không tìm thấy. Hãy chạy `midicoder code gen` trước.",
        ErrorCode.PREVIEW_ALREADY_RUNNING: "Preview đã đang chạy. Hãy `midicoder preview stop` trước hoặc dùng `restart`.",
        ErrorCode.PREVIEW_START_FAILED: "Không thể start preview services.",
        ErrorCode.PREVIEW_NOT_RUNNING: "Preview không đang chạy. Hãy chạy `midicoder preview start` trước.",
        ErrorCode.PREVIEW_STOP_FAILED: "Không thể stop preview services.",
        ErrorCode.PREVIEW_RESTART_FAILED: "Không thể restart preview services.",
        ErrorCode.PREVIEW_HEALTH_CHECK_TIMEOUT: "Timeout chờ services healthy. Vui lòng kiểm tra logs.",

        # Invariant Enforcement Errors
        ErrorCode.INV_NOT_REGISTERED: "Invariant không được đăng ký trong registry.",
        ErrorCode.INV_VALIDATION_FAILED: "Validation invariant thất bại.",
        ErrorCode.INV_BLUEPRINT_MISSING: "Blueprint không tìm thấy để validate invariants.",
        ErrorCode.INV_CATEGORY_UNKNOWN: "Invariant category không hợp lệ.",
        ErrorCode.INV_ENFORCEMENT_UNKNOWN: "Enforcement mode không hợp lệ.",
        ErrorCode.INV_BUSINESS_ENTITY_REF: "Entity reference không thể resolve trong business invariant.",
        ErrorCode.INV_BUSINESS_MUTATION_TXN: "Mutation không có transaction scope.",
        ErrorCode.INV_BUSINESS_QUERY_WRITE: "Query có write operation (phải read-only).",
        ErrorCode.INV_BUSINESS_EVENT_ORDER: "Event publish không đúng thứ tự sau mutation commit.",
        ErrorCode.INV_BUSINESS_STATE_TRANSITION: "State machine transition không hợp lệ.",
        ErrorCode.INV_COMP_PII_ENCRYPTION: "PII fields không được encrypt.",
        ErrorCode.INV_COMP_AUDIT_TRAIL: "Thiếu audit trail cho operation.",
        ErrorCode.INV_COMP_TENANT_ISOLATION: "Tenant isolation không được enforce.",
        ErrorCode.INV_COMP_PERMISSION_CHECK: "Thiếu permission check cho operation.",
        ErrorCode.INV_FM_ERROR_HANDLER: "Thiếu error handler cho mutation.",

        # Infrastructure Errors
        ErrorCode.INFRA_MIR_NOT_FOUND: "Không tìm thấy MIR trong artifacts. Hãy chạy `midicoder ir build` trước.",
        ErrorCode.INFRA_TEMPLATE_NOT_FOUND: "Không tìm thấy Docker Compose template.",
        ErrorCode.INFRA_TEMPLATE_RENDER_FAILED: "Không thể render Docker Compose template.",
        ErrorCode.INFRA_WRITE_FAILED: "Không thể ghi file docker-compose.yml.",
        ErrorCode.INFRA_INVALID_CONFIG: "Infrastructure configuration không hợp lệ.",

        # CP01 Value Object Errors
        ErrorCode.CP01_VALUE_OBJECT_NOT_FOUND: "Value Object không tìm thấy trong DSL.",
        ErrorCode.CP01_VALUE_OBJECT_INVALID_FIELD_TYPE: "Field type không hợp lệ cho Value Object.",
        ErrorCode.CP01_VALUE_OBJECT_INVALID_VALIDATION_RULE: "Validation rule không hợp lệ.",
        ErrorCode.CP01_VALUE_OBJECT_TEMPLATE_NOT_FOUND: "Template cho Value Object không tìm thấy.",
        ErrorCode.CP01_VALUE_OBJECT_EMIT_FAILED: "Không thể emit Value Object code.",
        ErrorCode.CP01_VALUE_OBJECT_NESTED_REF_NOT_FOUND: "Nested reference không tìm thấy.",
        ErrorCode.CP01_VALUE_OBJECT_METHOD_SIGNATURE_INVALID: "Method signature không hợp lệ.",
        ErrorCode.CP01_VALUE_OBJECT_COMPARABLE_NO_HASH: "Comparable Value Object cần __hash__ method.",
        ErrorCode.CP01_VALUE_OBJECT_IMMUTABLE_HAS_SETTER: "Immutable Value Object không thể có setter.",
        ErrorCode.CP01_VALUE_OBJECT_INVALID_TAG: "Tag không hợp lệ cho Value Object.",

        # Version Management Errors
        ErrorCode.VERSION_NOT_FOUND: "Version không tồn tại. Vui lòng kiểm tra tên version.",
        ErrorCode.VERSION_INVALID_NAME: "Tên version không hợp lệ. Sử dụng SemVer format (ví dụ: v1.0.0, v1.0.1-alpha).",
        ErrorCode.VERSION_DELETE_ACTIVE: "Không thể xóa active version. Hãy switch sang version khác trước hoặc dùng --force.",
        ErrorCode.VERSION_CREATE_FAILED: "Tạo version thất bại.",
        ErrorCode.VERSION_SWITCH_FAILED: "Switch version thất bại.",
        ErrorCode.VERSION_CLEANUP_FAILED: "Auto-cleanup version thất bại.",
        ErrorCode.VERSION_METADATA_INVALID: "Version metadata không hợp lệ.",
        ErrorCode.VERSION_ALREADY_EXISTS: "Version đã tồn tại. Vui lòng chọn tên khác.",

        # Index Command Errors
        ErrorCode.INDEX_PROJECT_NOT_FOUND: "Không tìm thấy project directory. Hãy chạy `midicoder init` trước.",
        ErrorCode.INDEX_NEO4J_CONNECTION_FAILED: "Không thể kết nối đến Neo4j. Vui lòng kiểm tra Neo4j Docker container đang chạy.",
        ErrorCode.INDEX_PARSE_FAILED: "Lỗi khi parse file source code.",
        ErrorCode.INDEX_EMBEDDING_FAILED: "Không thể generate embedding cho symbol.",
        ErrorCode.INDEX_LOCKED: "Index đang bị lock bởi một quá trình khác. Vui lòng thử lại sau.",

        # CP12 Notification Errors
        ErrorCode.CP12_NOTIFICATION_CHANNEL_NOT_SUPPORTED: "Channel type không được hỗ trợ cho notification.",
        ErrorCode.CP12_NOTIFICATION_TEMPLATE_NOT_FOUND: "Template notification không tìm thấy.",
        ErrorCode.CP12_NOTIFICATION_TEMPLATE_RENDER_FAILED: "Render template notification thất bại.",
        ErrorCode.CP12_NOTIFICATION_PROVIDER_NOT_CONFIGURED: "Provider notification chưa được cấu hình.",
        ErrorCode.CP12_NOTIFICATION_DISPATCH_FAILED: "Dispatch notification thất bại.",
        ErrorCode.CP12_NOTIFICATION_RATE_LIMIT_EXCEEDED: "Vượt quá rate limit cho notification channel.",
        ErrorCode.CP12_NOTIFICATION_INVALID_RECIPIENT: "Người nhận notification không hợp lệ.",

        # CP13: Background Job & Workflow Errors
        ErrorCode.CP13_JOB_SCHEDULE_FAILED: "Không thể lên lịch job '{job_id}'",
        ErrorCode.CP13_JOB_NOT_FOUND: "Không tìm thấy job '{job_id}'",
        ErrorCode.CP13_WORKFLOW_INVALID_TRANSITION: "Transition không hợp lệ cho workflow '{workflow_id}': {reason}",
        ErrorCode.CP13_WORKFLOW_GUARD_FAILED: "Guard failed cho workflow '{workflow_id}': {guard_type} — {reason}",
        ErrorCode.CP13_WORKFLOW_EFFECT_FAILED: "Effect failed cho workflow '{workflow_id}': {effect_type} — {reason}",
        ErrorCode.CP13_WORKFLOW_STATE_MACHINE_ERROR: "Lỗi state machine: {reason}",
        ErrorCode.CP13_SCHEDULE_POLICY_INVALID: "Schedule policy không hợp lệ: {reason}",
        ErrorCode.CP13_JOB_RETRY_EXHAUSTED: "Job '{job_id}' đã hết lượt retry ({max_retries} lần)",

        # CP
        ErrorCode.CP08_DUPLICATE_COLUMN_NAME: "Column name trùng lặp trong model.",
        ErrorCode.CP08_DUPLICATE_TABLE_NAME: "Table name trùng lặp trong collection.",
        ErrorCode.CP08_DSL_PARSE_ERROR: "Lỗi parsing DSL YAML cho database configuration.",
        ErrorCode.CP08_MISSING_DATASOURCE: "Thiếu datasource config bắt buộc.",
        ErrorCode.CP08_CIRCULAR_FOREIGN_KEY: "Phát hiện circular foreign key reference.",
        ErrorCode.CP08_MISSING_PRIMARY_KEY: "Model có columns nhưng không có primary key.",
        ErrorCode.CP08_MIGRATION_ERROR: "Lỗi generate migration file.",
        ErrorCode.CP08_RUNTIME_DATASOURCE_ERROR: "Lỗi runtime datasource connection.",

        # CP09: Caching & Performance Layer Error Templates
        ErrorCode.CP09_BACKEND_INVALID: "Backend cache không hợp lệ. Chọn trong redis hoặc memory.",
        ErrorCode.CP09_TTL_INVALID: "TTL phải lớn hơn 0 giây.",
        ErrorCode.CP09_KEY_EMPTY: "Cache key không được đặt trống.",
        ErrorCode.CP09_PATTERN_INVALID: "Pattern invalidation không hợp lệ. Sử dụng glob format.",
        ErrorCode.CP09_SERIALIZATION_FAILED: "Serialize cache data thất bại. Kiểm tra serializer.",

        # CP10: Search & Indexing Error Templates
        ErrorCode.CP10_EMPTY_INDEX_NAME: "Search index id không được để trống.",
        ErrorCode.CP10_INVALID_PROVIDER: "Search provider không hợp lệ. Chọn trong elasticsearch hoặc meilisearch.",
        ErrorCode.CP10_SYNC_STRATEGY_INVALID: "Sync strategy không hợp lệ. Chọn trong realtime, near_realtime, hoặc batch.",
        ErrorCode.CP10_INVALID_COLUMN_TYPE: "Column type không hợp lệ. Chọn trong text, keyword, numeric, date, hoặc geo.",
        ErrorCode.CP10_INDEX_CREATE_FAILED: "Tạo search index thất bại. Kiểm tra configuration.",

        # CP14 Audit Trail & Compliance Errors
        ErrorCode.CP14_AUDIT_EMPTY_ID: "ID không được để trống (audit_rule/compliance_control).",
        ErrorCode.CP14_AUDIT_INVALID_ACTION: "Audit action type không hợp lệ.",
        ErrorCode.CP14_AUDIT_INVALID_ACTOR_TYPE: "Actor type không hợp lệ.",
        ErrorCode.CP14_AUDIT_INVALID_LEVEL: "Audit level không hợp lệ.",
        ErrorCode.CP14_AUDIT_RETENTION_INVALID: "Retention days phải lớn hơn 0.",
        ErrorCode.CP14_AUDIT_ARCHIVE_EXCEEDS_RETENTION: "Archive days không được lớn hơn retention days.",
        ErrorCode.CP14_AUDIT_CONTROL_INVALID_STANDARD: "Compliance standard không hợp lệ.",
        ErrorCode.CP14_AUDIT_CONTROL_INVALID_TYPE: "Control type không hợp lệ.",
        ErrorCode.CP14_AUDIT_CONTROL_INVALID_ENFORCEMENT: "Enforcement level không hợp lệ.",
        ErrorCode.CP14_AUDIT_HASH_VERIFICATION_FAILED: "Xác minh hash integrity thất bại.",
        ErrorCode.CP17_EMPTY_MODEL_NAME: "Analytics model name không được để trống.",
        ErrorCode.CP17_INVALID_SOURCE_TYPE: "Analytics source type không hợp lệ.",
        ErrorCode.CP17_INVALID_AGGREGATION_TYPE: "Aggregation type không hợp lệ.",
        ErrorCode.CP17_INVALID_REPORT_FREQUENCY: "Report frequency không hợp lệ.",
        ErrorCode.CP17_INVALID_VISUALIZATION_TYPE: "Visualization type không hợp lệ.",
        ErrorCode.CP17_DUPLICATE_MODEL_NAME: "Analytics model name trùng lặp.",
        ErrorCode.CP17_EMPTY_DASHBOARD_NAME: "Dashboard name không được để trống.",
        ErrorCode.CP17_EMPTY_REPORT_NAME: "Report name không được để trống.",
        ErrorCode.CP17_INVALID_OUTPUT_FORMAT: "Report output format không hợp lệ.",
        ErrorCode.CP17_ANALYTICS_PARSE_ERROR: "Lỗi parse YAML analytics.",
        ErrorCode.CP18_EMPTY_APP_NAME: "Frontend app name không được để trống.",
        ErrorCode.CP18_INVALID_FRAMEWORK: "Frontend framework không hợp lệ. Chọn trong angular hoặc react.",
        ErrorCode.CP18_INVALID_STATE_STORE: "State store type không hợp lệ.",
        ErrorCode.CP18_DUPLICATE_ROUTE: "Route path trùng lặp.",
        ErrorCode.CP18_INVALID_ROUTE_PATH: "Route path không hợp lệ. Phải bắt đầu bằng /.",
        ErrorCode.CP18_INVALID_UI_FRAMEWORK: "UI framework không được hỗ trợ.",
        ErrorCode.CP18_INVALID_LAYOUT: "App shell layout type không hợp lệ.",
        ErrorCode.CP18_EMPTY_ROUTE_COMPONENT: "Route component name không được để trống.",
        ErrorCode.CP18_FRONTEND_PARSE_ERROR: "Lỗi parse YAML frontend config.",
        ErrorCode.CP18_INVALID_ROUTER_STRATEGY: "Router strategy không hợp lệ.",
        ErrorCode.CP19_INVALID_COMPONENT_TYPE: "Component type không hợp lệ.",
        ErrorCode.CP19_MISSING_FORM_BINDING: "Form field thiếu binding path.",
        ErrorCode.CP19_EMPTY_TABLE_COLUMNS: "TableSpec không có columns.",
        ErrorCode.CP19_INVALID_FIELD_TYPE: "Field type không được hỗ trợ.",
        ErrorCode.CP19_SCHEMA_VALIDATION_FAILED: "Schema validation giữa form và entity thất bại.",
        ErrorCode.CP20_OPENAPI_PARSE_ERROR: "Lỗi parse OpenAPI spec.",
        ErrorCode.CP20_TYPE_MISMATCH: "Type mismatch giữa client và backend.",
        ErrorCode.CP20_MISSING_AUTH_INJECT: "Thiếu auth injection trong client.",
        ErrorCode.CP20_BRIDGE_CONFIG_INVALID: "Config realtime bridge không hợp lệ.",
        ErrorCode.CP20_ENDPOINT_DUPLICATE: "Duplicate endpoint trong ApiSpec.",
        ErrorCode.CP53_BRIDGE_CAPABILITY_INVALID: "CP capability trong BridgeBinding khong hop le.",
        ErrorCode.CP53_DP_NOT_REGISTERED: "Domain pack target chua duoc dang ky.",
        ErrorCode.CP53_DUPLICATE_DP_ID: "Domain pack ID trung lap.",
        ErrorCode.CP53_INVALID_BINDING_ID: "Binding ID khong hop le.",
        ErrorCode.CP53_INVOKER_CONFIG_EMPTY: "RuntimeInvoker cau hinh rong.",
    }

    _SUGGESTIONS: dict[ErrorCode, list[str]] = {
        ErrorCode.DSL_FILE_NOT_FOUND: [
            "Kiểm tra đường dẫn file có chính xác không",
            "Đảm bảo file tồn tại trong filesystem",
            "Kiểm tra quyền truy cập file",
        ],
        ErrorCode.DSL_YAML_PARSE_ERROR: [
            "Kiểm tra YAML syntax (sử dụng YAML validator online)",
            "Đảm bảo indentation đúng (2 spaces, không dùng tabs)",
            "Kiểm tra quotes cho strings có special characters",
        ],
        ErrorCode.DSL_INVALID_CATALOG_VALUE: [
            "Xem lại catalog values cho phép trong documentation",
            "Kiểm tra spelling của value (case-sensitive)",
        ],
        ErrorCode.DEPENDENCY_CYCLE_DETECTED: [
            "Review dependency graph để tìm cycle",
            "Xét lại design để loại bỏ circular dependencies",
            "Sử dụng dependency injection thay vì direct references",
        ],
        ErrorCode.VALIDATION_FAILED: [
            "Xem validation report để biết chi tiết errors",
            "Fix errors trước khi continue",
        ],
        ErrorCode.CAPABILITY_PARAMS_INVALID: [
            "Kiểm tra params schema cho capability type tương ứng",
            "Đảm bảo các required fields đã được cung cấp",
            "Xem documentation cho capability params",
        ],
        ErrorCode.CAPABILITY_TYPE_UNKNOWN: [
            "Kiểm tra capability type spelling (case-sensitive)",
            "Xem danh sách capability types được hỗ trợ",
        ],
        ErrorCode.CAPABILITY_OBLIGATION_UNSATISFIED: [
            "Review obligations list cho capability",
            "Đảm bảo obligations đã được satisfy trong code",
        ],
        ErrorCode.CAPABILITY_EXPAND_FAILED: [
            "Kiểm tra macro capability definition",
            "Đảm bảo core capabilities được reference tồn tại",
        ],

        # Config Errors
        ErrorCode.CONFIG_READ_FAILED: [
            "Kiểm tra đường dẫn config file",
            "Đảm bảo file tồn tại trong filesystem",
            "Kiểm tra quyền truy cập file",
        ],
        ErrorCode.CONFIG_WRITE_FAILED: [
            "Kiểm tra quyền ghi vào thư mục config",
            "Đảm bảo đủ dung lượng đĩa",
            "Kiểm tra file không bị lock bởi process khác",
        ],
        ErrorCode.CONFIG_FORMAT_INVALID: [
            "Kiểm tra JSON/YAML syntax",
            "Sử dụng validator online để kiểm tra format",
            "So sánh với schema mặc định",
        ],
        ErrorCode.CONFIG_KEY_NOT_FOUND: [
            "Kiểm tra spelling của key (case-sensitive)",
            "Xem danh sách config keys được hỗ trợ",
        ],
        ErrorCode.CONFIG_VALUE_INVALID: [
            "Kiểm tra type của value (string, int, bool, etc.)",
            "Xem documentation cho config value constraints",
        ],

        # Database Errors
        ErrorCode.DB_CONNECTION_FAILED: [
            "Kiểm tra đường dẫn database có chính xác không",
            "Đảm bảo thư mục database tồn tại và có quyền ghi",
            "Kiểm tra database không bị lock bởi process khác",
        ],
        ErrorCode.DB_SCHEMA_ERROR: [
            "Kiểm tra schema SQL syntax",
            "Chạy `midicoder init` để recreate databases",
        ],
        ErrorCode.DB_CONSTRAINT_VIOLATION: [
            "Kiểm tra dữ liệu không vi phạm unique constraint",
            "Kiểm tra foreign key references tồn tại",
        ],
        ErrorCode.DB_TRANSACTION_FAILED: [
            "Retry transaction",
            "Kiểm tra không có concurrent writes",
        ],
        ErrorCode.DB_TIMEOUT: [
            "Tăng timeout configuration",
            "Kiểm tra không có long-running transactions",
        ],
        ErrorCode.DB_FILE_CORRUPTED: [
            "Khôi phục từ backup nếu có",
            "Chạy `midicoder init --force` để recreate databases",
        ],
        ErrorCode.DB_PERMISSION_DENIED: [
            "Kiểm tra quyền đọc/ghi thư mục database",
            "Chạy với elevated permissions nếu cần",
        ],

        # CP08 Database Errors
        ErrorCode.CP08_EMPTY_NAME: [
            "Kiểm tra tên datasource/column/table/index không được để trống",
            "Đảm bảo field 'name' có giá trị",
        ],
        ErrorCode.CP08_INVALID_COLUMN_TYPE: [
            "Kiểm tra column type nằm trong catalog: string, integer, boolean, decimal, text, json, datetime, uuid",
            "Xem documentation cho supported types",
        ],
        ErrorCode.CP08_DUPLICATE_COLUMN_NAME: [
            "Kiểm tra không có 2 column cùng tên trong một model",
            "Đổi tên column trùng lặp",
        ],
        ErrorCode.CP08_DUPLICATE_TABLE_NAME: [
            "Kiểm tra không có 2 model cùng table_name",
            "Đổi table_name trùng lặp",
        ],
        ErrorCode.CP08_DSL_PARSE_ERROR: [
            "Kiểm tra YAML syntax trong DSL file",
            "Đảm bảo indentation đúng (2 spaces)",
            "Sử dụng YAML validator online",
        ],
        ErrorCode.CP08_MISSING_DATASOURCE: [
            "Cung cấp datasource config trong DSL hoặc metadata",
            "Kiểm tra section 'datasources' trong DSL YAML",
        ],
        ErrorCode.CP08_CIRCULAR_FOREIGN_KEY: [
            "Review foreign key relationships để tìm circular reference",
            "Xét lại design để loại bỏ circular dependencies",
            "Sử dụng intermediate table cho many-to-many",
        ],
        ErrorCode.CP08_MISSING_PRIMARY_KEY: [
            "Thêm column với primary_key=True vào model",
            "Mỗi model có columns cần ít nhất một primary key",
        ],
        ErrorCode.CP08_MIGRATION_ERROR: [
            "Kiểm tra migration template có tồn tại không",
            "Xem logs để biết chi tiết lỗi",
        ],
        ErrorCode.CP08_RUNTIME_DATASOURCE_ERROR: [
            "Kiểm tra connection_string hợp lệ",
            "Đảm bảo database server đang chạy",
            "Kiểm tra network connectivity",
        ],
        
        # CP09: Caching & Performance Layer Suggestions
        ErrorCode.CP09_BACKEND_INVALID: [
            "Kiểm tra backend giả trị nằm trong catalog: redis, memory",
            "Đối với redis, đảm bảo Redis server đang chạy",
        ],
        ErrorCode.CP09_TTL_INVALID: [
            "Đặt ttl > 0 (đvị: giây)",
            "TTL mặc định là 300 giây nếu không cần đặt đặc biệt",
        ],
        ErrorCode.CP09_KEY_EMPTY: [
            "Cung cấp cache key khác trống",
            "Đảm bảo key_prefix của profile không trống",
        ],
        ErrorCode.CP09_PATTERN_INVALID: [
            "Sử dụng glob format: user:*, order:*, product:*",
            "Tránh sử dụng ký tự đặc biệt không được hỗ trợ",
        ],
        ErrorCode.CP09_SERIALIZATION_FAILED: [
            "Kiểm tra data cần serialize phải JSON-serializable",
            "Đổi serializer sang pickle nếu dữ liệu phức tạp",
        ],

        # CP10: Search & Indexing Suggestions
        ErrorCode.CP10_EMPTY_INDEX_NAME: [
            "Cung cấp index id khác trống (ví dụ: 'products', 'orders')",
            "Sử dụng snake_case cho index id",
        ],
        ErrorCode.CP10_INVALID_PROVIDER: [
            "Kiểm tra provider nằm trong catalog: elasticsearch, meilisearch",
            "Elasticsearch là provider mặc định",
        ],
        ErrorCode.CP10_SYNC_STRATEGY_INVALID: [
            "Kiểm tra sync_strategy nằm trong catalog: realtime, near_realtime, batch",
            "near_realtime là strategy khuyến nghị cho hầu hết use cases",
        ],
        ErrorCode.CP10_INVALID_COLUMN_TYPE: [
            "Kiểm tra column_type nằm trong catalog: text, keyword, numeric, date, geo",
            "Dùng 'text' cho full-text search, 'keyword' cho exact match",
        ],
        ErrorCode.CP10_INDEX_CREATE_FAILED: [
            "Kiểm tra Elasticsearch server đang chạy",
            "Đảm bảo connection config (ELASTICSEARCH_URL) đúng",
            "Kiểm tra index mappings hợp lệ",
        ],

        # CP13: Background Job & Workflow Suggestions
        ErrorCode.CP13_JOB_SCHEDULE_FAILED: [
            "Kiểm tra Celery worker đang chạy",
            "Kiểm tra Redis/RabbitMQ connection",
            "Xem log worker cho lỗi chi tiết",
        ],
        ErrorCode.CP13_JOB_NOT_FOUND: [
            "Kiểm tra job_id có đúng không",
            "List jobs hiện tại: GET /api/jobs",
        ],
        ErrorCode.CP13_WORKFLOW_INVALID_TRANSITION: [
            "Kiểm tra workflow definition — state hiện tại có transition đến state đích không",
            "Xem logs cho trạng thái hiện tại của instance",
        ],
        ErrorCode.CP13_WORKFLOW_GUARD_FAILED: [
            "Kiểm tra điều kiện guard — permission, business rule, hoặc compliance",
            "Debug guard evaluation bằng cách bật verbose logging",
        ],
        ErrorCode.CP13_WORKFLOW_EFFECT_FAILED: [
            "Kiểm tra service dependency (EventService, NotificationService, AuditService)",
            "Effects chạy best-effort — failure không block transition",
        ],
        ErrorCode.CP13_WORKFLOW_STATE_MACHINE_ERROR: [
            "Kiểm tra workflow definition có valid không (cycle, missing states)",
            "Xem logs cho error chi tiết",
        ],
        ErrorCode.CP13_SCHEDULE_POLICY_INVALID: [
            "Cron expression phải có đúng 5-6 fields",
            "Hoặc dùng interval_seconds (positive integer)",
        ],
        ErrorCode.CP13_JOB_RETRY_EXHAUSTED: [
            "Kiểm tra Dead Letter Queue cho job đã fail",
            "Tăng max_retries hoặc điều chỉnh backoff policy",
            "Xem logs cho root cause của failure",
        ],

        ErrorCode.CP14_AUDIT_INVALID_ACTION: [
            "Kiểm tra action type nằm trong catalog: CREATE, UPDATE, DELETE, READ, LOGIN, LOGOUT, EXPORT, APPROVE, REJECT, CUSTOM",
            "Xem documentation cho supported audit actions",
        ],
        ErrorCode.CP14_AUDIT_INVALID_ACTOR_TYPE: [
            "Kiểm tra actor type nằm trong catalog: user, system, background_job",
        ],
        ErrorCode.CP14_AUDIT_INVALID_LEVEL: [
            "Kiểm tra audit level nằm trong catalog: basic, detailed",
        ],
        ErrorCode.CP14_AUDIT_RETENTION_INVALID: [
            "Đặt retention_days > 0",
            "Xem yêu cầu compliance standard về retention period tối thiểu",
        ],
        ErrorCode.CP14_AUDIT_ARCHIVE_EXCEEDS_RETENTION: [
            "Đặt archive_after_days < retention_days",
            "Archive phải xảy ra trước khi retention period kết thúc",
        ],
        ErrorCode.CP14_AUDIT_CONTROL_INVALID_STANDARD: [
            "Kiểm tra standard nằm trong catalog: sox, hipaa, gdpr, pci_dss, custom",
            "Xem documentation cho supported compliance standards",
        ],
        ErrorCode.CP14_AUDIT_CONTROL_INVALID_TYPE: [
            "Kiểm tra control_type nằm trong catalog: preventive, detective, corrective",
        ],
        ErrorCode.CP14_AUDIT_CONTROL_INVALID_ENFORCEMENT: [
            "Kiểm tra enforcement_level nằm trong catalog: compile, runtime, both",
        ],
        ErrorCode.CP14_AUDIT_HASH_VERIFICATION_FAILED: [
            "Kiểm tra audit log không bị tamper",
            "Xét lại storage integrity của audit logs",
        ],
        ErrorCode.CP17_INVALID_SOURCE_TYPE: [
            "Kiểm tra source_type nằm trong catalog: metric_registry, database, external_api, custom",
            "Xem documentation cho supported analytics source types",
        ],
        ErrorCode.CP17_INVALID_AGGREGATION_TYPE: [
            "Kiểm tra aggregation nằm trong catalog: sum, average, max, min, count, percentage",
            "Xem documentation cho supported aggregation types",
        ],
        ErrorCode.CP17_INVALID_REPORT_FREQUENCY: [
            "Kiểm tra frequency nằm trong catalog: hourly, daily, weekly, monthly",
            "Xem documentation cho supported report frequencies",
        ],
        ErrorCode.CP17_INVALID_VISUALIZATION_TYPE: [
            "Kiểm tra visualization_type nằm trong catalog: line_chart, bar_chart, pie_chart, table, gauge, heatmap",
            "Xem documentation cho supported visualization types",
        ],
        ErrorCode.CP17_ANALYTICS_PARSE_ERROR: [
            "Kiểm tra YAML syntax (sử dụng YAML validator online)",
            "Đảm bảo indentation đúng (2 spaces, không dùng tabs)",
            "Kiểm tra quotes cho strings có special characters",
        ],
    }

    @classmethod
    def create(
        cls,
        code: ErrorCode,
        *,
        message: str | None = None,
        suggestions: list[str] | None = None,
        **context: Any,
    ) -> MidicoderError:
        """
        Tạo MidicoderError từ ErrorCode.

        Args:
            code: ErrorCode từ enum
            message: Custom message (nếu không cung cấp, lấy từ template)
            suggestions: Custom suggestions (nếu không, lấy từ template)
            **context: Context thông tin cho debugging

        Returns:
            MidicoderError instance
        """
        base_message = message or cls._TEMPLATES.get(code, "Lỗi không xác định.")
        base_suggestions = suggestions or cls._SUGGESTIONS.get(code, [])

        return MidicoderError(
            code=code,
            message=base_message,
            context=context,
            suggestions=base_suggestions,
        )

    @classmethod
    def raise_error(
        cls,
        code: ErrorCode,
        *,
        message: str | None = None,
        suggestions: list[str] | None = None,
        **context: Any,
    ) -> None:
        """
        Tạo và throw MidicoderError ngay lập tức.

        Args:
            code: ErrorCode từ enum
            message: Custom message
            suggestions: Custom suggestions
            **context: Context thông tin

        Raises:
            MidicoderError: Với code, message, context đã cung cấp
        """
        raise cls.create(code, message=message, suggestions=suggestions, **context)

    @classmethod
    def wrap_exception(
        cls,
        exception: Exception,
        code: ErrorCode,
        *,
        message: str | None = None,
        **context: Any,
    ) -> MidicoderError:
        """
        Wrap general exception thành MidicoderError.

        Preserve original exception làm cause cho debugging.

        Args:
            exception: Original exception để wrap
            code: ErrorCode cho wrapped error
            message: Custom message (optional)
            **context: Context thông tin

        Returns:
            MidicoderError với cause là original exception
        """
        # Add original exception info to context
        context["original_exception_type"] = type(exception).__name__
        context["original_exception_message"] = str(exception)

        return MidicoderError(
            code=code,
            message=message or f"Lỗi không mong muốn: {exception}",
            context=context,
            cause=exception,
            suggestions=cls._SUGGESTIONS.get(code, []),
        )