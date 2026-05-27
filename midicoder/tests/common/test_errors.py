"""
Tests cho E00-T07: Setup error management.

Viết theo TDD, bám sát SoT:
- ErrorCode enum: Mã lỗi chuẩn cho toàn hệ thống
- MidicoderError: Exception class với context và traceback support
- MidicoderErrorManager: Factory pattern cho error creation

Không dùng mock, test với real implementations.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from enum import Enum

import yaml

import pytest

from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager


# ============================================================================
# Test ErrorCode Enum
# ============================================================================


class TestErrorCode:
    """Tests cho ErrorCode enum theo SoT."""

    def test_error_code_is_enum(self) -> None:
        """Kiểm tra ErrorCode là Enum."""
        assert issubclass(ErrorCode, Enum), "ErrorCode phải kế thừa từ Enum"

    def test_error_code_is_str_enum(self) -> None:
        """Kiểm tra ErrorCode kế thừa từ str."""
        code = ErrorCode.DSL_FILE_NOT_FOUND
        assert isinstance(code, str), "ErrorCode phải là str enum"

    def test_cli_error_codes_exist(self) -> None:
        """Kiểm tra CLI error codes tồn tại."""
        # MDC-CLI-001
        assert ErrorCode.NO_CURRENT_VERSION.value == "MDC-CLI-001"

    def test_brief_error_codes_exist(self) -> None:
        """Kiểm tra Brief error codes tồn tại."""
        # MDC-BRIEF-001
        assert ErrorCode.MASTER_BRIEF_MISSING.value == "MDC-BRIEF-001"

    def test_contract_error_codes_exist(self) -> None:
        """Kiểm tra Contract error codes tồn tại theo SoT."""
        # MDC-COMP-001 to MDC-COMP-011
        assert ErrorCode.CONTRACT_GRAPH_NOT_FOUND.value == "MDC-COMP-001"
        assert ErrorCode.CONTRACT_GRAPH_VALIDATION_FAILED.value == "MDC-COMP-002"
        assert ErrorCode.CONTRACT_COMPILE_FAILED.value == "MDC-COMP-003"
        assert ErrorCode.DETERMINISTIC_HASH_GATE_FAILED.value == "MDC-COMP-004"
        assert ErrorCode.CONTRACT_PACK_NOT_FOUND.value == "MDC-COMP-005"
        assert ErrorCode.CONTRACT_GRAPH_READ_FAILED.value == "MDC-COMP-006"
        assert ErrorCode.CONTRACT_GRAPH_SCHEMA_INVALID.value == "MDC-COMP-007"
        assert ErrorCode.CAPABILITY_PARAMS_INVALID.value == "MDC-COMP-008"
        assert ErrorCode.CAPABILITY_TYPE_UNKNOWN.value == "MDC-COMP-009"
        assert ErrorCode.CAPABILITY_OBLIGATION_UNSATISFIED.value == "MDC-COMP-010"
        assert ErrorCode.CAPABILITY_EXPAND_FAILED.value == "MDC-COMP-011"

    def test_blueprint_error_codes_exist(self) -> None:
        """Kiểm tra Blueprint error codes tồn tại."""
        assert ErrorCode.BLUEPRINT_FILE_NOT_FOUND.value == "MDC-BLUEPRINT-001"
        assert ErrorCode.BLUEPRINT_YAML_PARSE_ERROR.value == "MDC-BLUEPRINT-002"
        assert ErrorCode.BLUEPRINT_MISSING_P0_PACKS.value == "MDC-BLUEPRINT-003"
        assert ErrorCode.BLUEPRINT_MISSING_RX_OVERLAY.value == "MDC-BLUEPRINT-004"
        assert ErrorCode.BLUEPRINT_INVALID_PROFILE.value == "MDC-BLUEPRINT-005"
        assert ErrorCode.BLUEPRINT_INVARIANT_VIOLATION.value == "MDC-BLUEPRINT-006"
        assert ErrorCode.BLUEPRINT_SCHEMA_INVALID.value == "MDC-BLUEPRINT-007"
        assert ErrorCode.BLUEPRINT_DEPENDENCY_RESOLUTION_FAILED.value == "MDC-BLUEPRINT-008"
        assert ErrorCode.BLUEPRINT_COMPILE_FAILED.value == "MDC-BLUEPRINT-009"

    def test_dsl_error_codes_exist(self) -> None:
        """Kiểm tra DSL error codes tồn tại."""
        assert ErrorCode.DSL_LOAD_FAILED.value == "MDC-DSL-001"
        assert ErrorCode.DSL_FILE_NOT_FOUND.value == "MDC-DSL-002"
        assert ErrorCode.DSL_YAML_PARSE_ERROR.value == "MDC-DSL-003"
        assert ErrorCode.DSL_INVALID_NODE_KIND.value == "MDC-DSL-004"
        assert ErrorCode.DSL_MISSING_REQUIRED_FIELD.value == "MDC-DSL-005"
        assert ErrorCode.DSL_INVALID_CATALOG_VALUE.value == "MDC-DSL-006"
        assert ErrorCode.DSL_DUPLICATE_NODE_ID.value == "MDC-DSL-007"
        assert ErrorCode.DSL_INVALID_REFERENCE.value == "MDC-DSL-008"

    def test_validation_error_codes_exist(self) -> None:
        """Kiểm tra Validation error codes tồn tại."""
        assert ErrorCode.VALIDATION_FAILED.value == "MDC-VALID-001"
        assert ErrorCode.CONSTRAINT_VIOLATION.value == "MDC-VALID-002"
        assert ErrorCode.CROSS_NODE_VALIDATION_FAILED.value == "MDC-VALID-003"

    def test_dependency_error_codes_exist(self) -> None:
        """Kiểm tra Dependency error codes tồn tại."""
        assert ErrorCode.DEPENDENCY_CYCLE_DETECTED.value == "MDC-DEP-001"
        assert ErrorCode.MISSING_DEPENDENCY.value == "MDC-DEP-002"

    def test_runtime_error_codes_exist(self) -> None:
        """Kiểm tra Runtime error codes tồn tại."""
        assert ErrorCode.GENERATION_FAILED.value == "MDC-RUNTIME-001"
        assert ErrorCode.TEMPLATE_RENDER_FAILED.value == "MDC-RUNTIME-002"
        assert ErrorCode.FILE_WRITE_FAILED.value == "MDC-RUNTIME-003"

    def test_error_code_format(self) -> None:
        """Kiểm tra format error code theo chuẩn MDC-XXX-NNN."""
        for code in ErrorCode:
            value = code.value
            # Format phải là MDC-XXX-NNN
            parts = value.split("-")
            assert len(parts) == 3, f"Error code {value} phải có format MDC-XXX-NNN"
            assert parts[0] == "MDC", f"Error code {value} phải bắt đầu với MDC"
            assert len(parts[2]) == 3, f"Error code {value} số phải có 3 chữ số"


# ============================================================================
# Test MidicoderError Class
# ============================================================================


class TestMidicoderError:
    """Tests cho MidicoderError class theo SoT."""

    def test_error_creation_with_code_and_message(self) -> None:
        """Kiểm tra tạo error với code và message."""
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
        )

        assert error.code == ErrorCode.DSL_FILE_NOT_FOUND
        assert error.message == "Không tìm thấy file DSL"

    def test_error_creation_with_context(self) -> None:
        """Kiểm tra tạo error với context."""
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
            context={"path": "dsl/entities.yaml", "line": 42},
        )

        assert error.context == {"path": "dsl/entities.yaml", "line": 42}

    def test_error_creation_with_cause(self) -> None:
        """Kiểm tra tạo error với cause."""
        original_exception = FileNotFoundError("File not found")
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
            cause=original_exception,
        )

        assert error.cause is original_exception

    def test_error_creation_with_suggestions(self) -> None:
        """Kiểm tra tạo error với suggestions."""
        suggestions = [
            "Kiểm tra đường dẫn file",
            "Đảm bảo file tồn tại",
        ]
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
            suggestions=suggestions,
        )

        assert error.suggestions == suggestions

    def test_error_str_format_without_context(self) -> None:
        """Kiểm tra str format không có context."""
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
        )

        error_str = str(error)
        assert "[MDC-DSL-002]" in error_str
        assert "Không tìm thấy file DSL" in error_str
        assert "(" not in error_str.split("Không tìm thấy file DSL")[1]

    def test_error_str_format_with_context(self) -> None:
        """Kiểm tra str format có context."""
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
            context={"path": "dsl/entities.yaml"},
        )

        error_str = str(error)
        assert "[MDC-DSL-002]" in error_str
        assert "Không tìm thấy file DSL" in error_str
        assert "path='dsl/entities.yaml'" in error_str

    def test_error_str_format_with_cause(self) -> None:
        """Kiểm tra str format có cause."""
        original_exception = ValueError("Invalid value")
        error = MidicoderError(
            code=ErrorCode.DSL_YAML_PARSE_ERROR,
            message="Lỗi YAML parsing",
            cause=original_exception,
        )

        error_str = str(error)
        assert "Caused by:" in error_str
        assert "Invalid value" in error_str

    def test_error_repr(self) -> None:
        """Kiểm tra repr format."""
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
            context={"path": "test.yaml"},
        )

        error_repr = repr(error)
        assert "MidicoderError" in error_repr
        assert "MDC-DSL-002" in error_repr
        assert "Không tìm thấy file DSL" in error_repr

    def test_error_get_full_message_without_suggestions(self) -> None:
        """Kiểm tra get_full_message không có suggestions."""
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
        )

        full_message = error.get_full_message()
        assert "Không tìm thấy file DSL" in full_message
        assert "Gợi ý khắc phục:" not in full_message

    def test_error_get_full_message_with_suggestions(self) -> None:
        """Kiểm tra get_full_message có suggestions."""
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
            suggestions=["Kiểm tra đường dẫn", "Đảm bảo file tồn tại"],
        )

        full_message = error.get_full_message()
        assert "Gợi ý khắc phục:" in full_message
        assert "1. Kiểm tra đường dẫn" in full_message
        assert "2. Đảm bảo file tồn tại" in full_message

    def test_error_get_full_message_with_cause(self) -> None:
        """Kiểm tra get_full_message có cause."""
        original_exception = FileNotFoundError("File not found")
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
            cause=original_exception,
        )

        full_message = error.get_full_message()
        assert "Nguyên nhân gốc:" in full_message

    def test_error_to_dict(self) -> None:
        """Kiểm tra to_dict serialization."""
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
            context={"path": "test.yaml"},
            suggestions=["Kiểm tra đường dẫn"],
        )

        error_dict = error.to_dict()

        assert error_dict["code"] == "MDC-DSL-002"
        assert error_dict["message"] == "Không tìm thấy file DSL"
        assert error_dict["context"] == {"path": "test.yaml"}
        assert error_dict["has_cause"] is False
        assert error_dict["suggestions"] == ["Kiểm tra đường dẫn"]

    def test_error_to_dict_with_cause(self) -> None:
        """Kiểm tra to_dict với cause."""
        original_exception = ValueError("Invalid")
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Không tìm thấy file DSL",
            cause=original_exception,
        )

        error_dict = error.to_dict()
        assert error_dict["has_cause"] is True

    def test_error_is_runtime_error(self) -> None:
        """Kiểm tra MidicoderError kế thừa RuntimeError."""
        error = MidicoderError(
            code=ErrorCode.DSL_FILE_NOT_FOUND,
            message="Test error",
        )

        assert isinstance(error, RuntimeError)


# ============================================================================
# Test MidicoderErrorManager Factory
# ============================================================================


class TestMidicoderErrorManager:
    """Tests cho MidicoderErrorManager factory theo SoT."""

    def test_create_error_with_code(self) -> None:
        """Kiểm tra create error với code."""
        error = MidicoderErrorManager.create(
            ErrorCode.DSL_FILE_NOT_FOUND,
            path="test.yaml",
        )

        assert isinstance(error, MidicoderError)
        assert error.code == ErrorCode.DSL_FILE_NOT_FOUND
        assert error.context == {"path": "test.yaml"}

    def test_create_error_with_custom_message(self) -> None:
        """Kiểm tra create error với custom message."""
        error = MidicoderErrorManager.create(
            ErrorCode.DSL_FILE_NOT_FOUND,
            message="Custom error message",
        )

        assert error.message == "Custom error message"

    def test_create_error_with_custom_suggestions(self) -> None:
        """Kiểm tra create error với custom suggestions."""
        error = MidicoderErrorManager.create(
            ErrorCode.DSL_FILE_NOT_FOUND,
            suggestions=["Custom suggestion 1", "Custom suggestion 2"],
        )

        assert error.suggestions == ["Custom suggestion 1", "Custom suggestion 2"]

    def test_create_error_uses_template_message(self) -> None:
        """Kiểm tra create error dùng template message nếu không cung cấp."""
        error = MidicoderErrorManager.create(ErrorCode.DSL_FILE_NOT_FOUND)

        # Template message phải được dùng
        assert "Không tìm thấy file DSL" in error.message

    def test_create_error_uses_template_suggestions(self) -> None:
        """Kiểm tra create error dùng template suggestions nếu có."""
        error = MidicoderErrorManager.create(ErrorCode.DSL_FILE_NOT_FOUND)

        # DSL_FILE_NOT_FOUND có template suggestions
        assert len(error.suggestions) > 0
        assert "Kiểm tra đường dẫn file có chính xác không" in error.suggestions

    def test_raise_error_throws_exception(self) -> None:
        """Kiểm tra raise_error throw exception."""
        with pytest.raises(MidicoderError) as exc_info:
            MidicoderErrorManager.raise_error(
                ErrorCode.DSL_FILE_NOT_FOUND,
                path="test.yaml",
            )

        assert exc_info.value.code == ErrorCode.DSL_FILE_NOT_FOUND
        assert exc_info.value.context == {"path": "test.yaml"}

    def test_raise_error_with_custom_message(self) -> None:
        """Kiểm tra raise_error với custom message."""
        with pytest.raises(MidicoderError) as exc_info:
            MidicoderErrorManager.raise_error(
                ErrorCode.DSL_FILE_NOT_FOUND,
                message="Custom message",
            )

        assert exc_info.value.message == "Custom message"

    def test_wrap_exception_preserves_cause(self) -> None:
        """Kiểm tra wrap_exception preserve original exception."""
        original_exception = yaml.YAMLError("YAML error")

        error = MidicoderErrorManager.wrap_exception(
            original_exception,
            ErrorCode.DSL_YAML_PARSE_ERROR,
            file_path="test.yaml",
        )

        assert error.cause is original_exception
        assert error.code == ErrorCode.DSL_YAML_PARSE_ERROR

    def test_wrap_exception_adds_original_info_to_context(self) -> None:
        """Kiểm tra wrap_exception thêm original exception info vào context."""
        original_exception = ValueError("Invalid value")

        error = MidicoderErrorManager.wrap_exception(
            original_exception,
            ErrorCode.VALIDATION_FAILED,
        )

        assert error.context["original_exception_type"] == "ValueError"
        assert error.context["original_exception_message"] == "Invalid value"

    def test_wrap_exception_with_custom_message(self) -> None:
        """Kiểm tra wrap_exception với custom message."""
        original_exception = ValueError("Invalid")

        error = MidicoderErrorManager.wrap_exception(
            original_exception,
            ErrorCode.VALIDATION_FAILED,
            message="Custom validation error",
        )

        assert error.message == "Custom validation error"


# ============================================================================
# Test Error Templates and Suggestions
# ============================================================================


class TestErrorTemplates:
    """Tests cho error templates và suggestions."""

    def test_dsl_file_not_found_template(self) -> None:
        """Kiểm tra template cho DSL_FILE_NOT_FOUND."""
        error = MidicoderErrorManager.create(ErrorCode.DSL_FILE_NOT_FOUND)

        assert "Không tìm thấy file DSL" in error.message
        assert len(error.suggestions) >= 1

    def test_dsl_yaml_parse_error_template(self) -> None:
        """Kiểm tra template cho DSL_YAML_PARSE_ERROR."""
        error = MidicoderErrorManager.create(ErrorCode.DSL_YAML_PARSE_ERROR)

        assert "Lỗi YAML" in error.message or "YAML parsing" in error.message
        assert len(error.suggestions) >= 1

    def test_dependency_cycle_detected_template(self) -> None:
        """Kiểm tra template cho DEPENDENCY_CYCLE_DETECTED."""
        error = MidicoderErrorManager.create(ErrorCode.DEPENDENCY_CYCLE_DETECTED)

        assert "cycle" in error.message.lower() or "vòng lặp" in error.message.lower()
        assert len(error.suggestions) >= 1

    def test_capability_params_invalid_template(self) -> None:
        """Kiểm tra template cho CAPABILITY_PARAMS_INVALID."""
        error = MidicoderErrorManager.create(ErrorCode.CAPABILITY_PARAMS_INVALID)

        assert len(error.suggestions) >= 1

    def test_capability_type_unknown_template(self) -> None:
        """Kiểm tra template cho CAPABILITY_TYPE_UNKNOWN."""
        error = MidicoderErrorManager.create(ErrorCode.CAPABILITY_TYPE_UNKNOWN)

        assert len(error.suggestions) >= 1

    def test_capability_obligationUnsatisfied_template(self) -> None:
        """Kiểm tra template cho CAPABILITY_OBLIGATION_UNSATISFIED."""
        error = MidicoderErrorManager.create(
            ErrorCode.CAPABILITY_OBLIGATION_UNSATISFIED
        )

        assert len(error.suggestions) >= 1

    def test_capability_expand_failed_template(self) -> None:
        """Kiểm tra template cho CAPABILITY_EXPAND_FAILED."""
        error = MidicoderErrorManager.create(ErrorCode.CAPABILITY_EXPAND_FAILED)

        assert len(error.suggestions) >= 1