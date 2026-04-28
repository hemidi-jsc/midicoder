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
    # CP01: Entity Model Emitter Errors
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
    
    # =========================================================================
    # CP01: Value Object Emitter Errors
    # =========================================================================
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
    
    # =========================================================================
    # CP01: Command Emitter Errors
    # =========================================================================
    CP01_COMMAND_NOT_FOUND = "MDC-CP01-021"
    CP01_COMMAND_INVALID_INPUT = "MDC-CP01-022"
    CP01_COMMAND_GUARD_FAILED = "MDC-CP01-023"
    CP01_COMMAND_EFFECT_FAILED = "MDC-CP01-024"
    CP01_COMMAND_VALIDATION_FAILED = "MDC-CP01-025"
    CP01_COMMAND_TEMPLATE_NOT_FOUND = "MDC-CP01-026"
    CP01_COMMAND_EMIT_FAILED = "MDC-CP01-027"
    
    # =========================================================================
    # CP01: Query Emitter Errors
    # =========================================================================
    CP01_QUERY_NOT_FOUND = "MDC-CP01-028"
    CP01_QUERY_INVALID_FILTER = "MDC-CP01-029"
    CP01_QUERY_INVALID_PAGINATION = "MDC-CP01-030"
    CP01_QUERY_INVALID_PROJECTION = "MDC-CP01-031"
    CP01_QUERY_TEMPLATE_NOT_FOUND = "MDC-CP01-032"
    CP01_QUERY_EMIT_FAILED = "MDC-CP01-033"
    CP01_QUERY_HANDLER_INVALID = "MDC-CP01-034"
    CP01_QUERY_SCHEMA_INVALID = "MDC-CP01-035"


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
        
        # Infrastructure Errors
        ErrorCode.INFRA_MIR_NOT_FOUND: "Không tìm thấy MIR trong artifacts. Hãy chạy `midicoder ir build` trước.",
        ErrorCode.INFRA_TEMPLATE_NOT_FOUND: "Không tìm thấy Docker Compose template.",
        ErrorCode.INFRA_TEMPLATE_RENDER_FAILED: "Không thể render Docker Compose template.",
        ErrorCode.INFRA_WRITE_FAILED: "Không thể ghi file docker-compose.yml.",
        ErrorCode.INFRA_INVALID_CONFIG: "Infrastructure configuration không hợp lệ.",
        
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
