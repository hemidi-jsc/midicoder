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
