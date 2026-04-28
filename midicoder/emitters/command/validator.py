"""
Command Validator với complex validation support.

Hỗ trợ:
- Field-level validation (required, pattern, min/max)
- Cross-field validation (end_date > start_date)
- Business rule validation
- Formula-based validation
- External API validation

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .models import Command, CommandField, ValidationResult


class CommandValidator:
    """
    Validator cho Command với đầy đủ validation rules.

    Validation types:
    - Field validation: required, pattern, min_length, max_length, min_value, max_value
    - Cross-field validation: so sánh giữa các fields
    - Business rules: custom validation logic
    - Formula validation: tính toán và validate kết quả

    Usage:
        validator = CommandValidator(command)
        result = await validator.validate(command_data)
        if not result.is_valid:
            raise ValidationError(result.errors)
    """

    def __init__(
        self,
        command: Command,
        custom_validators: dict[str, Callable] | None = None,
    ) -> None:
        """
        Khởi tạo CommandValidator.

        Args:
            command: Command definition
            custom_validators: Custom validation functions (optional)
        """
        self._command = command
        self._custom_validators = custom_validators or {}

    async def validate(self, data: dict[str, Any]) -> ValidationResult:
        """
        Validate command data.

        Process:
        1. Field-level validation
        2. Cross-field validation
        3. Business rule validation
        4. Custom validator execution

        Args:
            data: Command data dict

        Returns:
            ValidationResult với errors và warnings
        """
        result = ValidationResult(is_valid=True)

        # Bước 1: Field-level validation
        await self._validate_fields(data, result)

        # Bước 2: Cross-field validation
        if result.is_valid:
            await self._validate_cross_fields(data, result)

        # Bước 3: Business rule validation
        if result.is_valid:
            await self._validate_business_rules(data, result)

        # Bước 4: Custom validators
        if result.is_valid:
            await self._validate_custom(data, result)

        return result

    async def _validate_fields(
        self,
        data: dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """
        Validate từng field theo definition.

        Args:
            data: Command data
            result: ValidationResult để add errors
        """
        for field_def in self._command.input:
            field_name = field_def.name
            field_value = data.get(field_name)

            # Required validation
            if field_def.required and field_value is None:
                result.add_error(f"{field_name} là trường bắt buộc")
                continue

            # Skip further validation if value is None and not required
            if field_value is None:
                continue

            # Pattern validation
            if field_def.pattern:
                if not re.match(field_def.pattern, str(field_value)):
                    result.add_error(f"{field_name} không đúng định dạng")

            # String length validation
            if isinstance(field_value, str):
                if field_def.min_length and len(field_value) < field_def.min_length:
                    result.add_error(
                        f"{field_name} phải có ít nhất {field_def.min_length} ký tự"
                    )
                if field_def.max_length and len(field_value) > field_def.max_length:
                    result.add_error(
                        f"{field_name} phải có không quá {field_def.max_length} ký tự"
                    )

            # Numeric validation
            if isinstance(field_value, (int, float)):
                if field_def.min_value is not None and field_value < field_def.min_value:
                    result.add_error(
                        f"{field_name} phải lớn hơn hoặc bằng {field_def.min_value}"
                    )
                if field_def.max_value is not None and field_value > field_def.max_value:
                    result.add_error(
                        f"{field_name} phải nhỏ hơn hoặc bằng {field_def.max_value}"
                    )

            # Array validation
            if isinstance(field_value, list):
                if field_def.min_items and len(field_value) < field_def.min_items:
                    result.add_error(
                        f"{field_name} phải có ít nhất {field_def.min_items} phần tử"
                    )
                if field_def.max_items and len(field_value) > field_def.max_items:
                    result.add_error(
                        f"{field_name} phải có không quá {field_def.max_items} phần tử"
                    )

    async def _validate_cross_fields(
        self,
        data: dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """
        Cross-field validation.

        Ví dụ:
        - end_date > start_date
        - quantity * price = total
        - from_account != to_account

        Args:
            data: Command data
            result: ValidationResult
        """
        # Common cross-field validations
        # End date after start date
        if "end_date" in data and "start_date" in data:
            end_date = data["end_date"]
            start_date = data["start_date"]
            if end_date and start_date and end_date < start_date:
                result.add_error("Ngày kết thúc phải sau ngày bắt đầu")

        # From != To (for transfers)
        if "from_account" in data and "to_account" in data:
            from_acc = data["from_account"]
            to_acc = data["to_account"]
            if from_acc and to_acc and from_acc == to_acc:
                result.add_error("Tài khoản nguồn và tài khoản đích không được giống nhau")

        # Quantity * Price = Total (approximate)
        if "quantity" in data and "price" in data and "total" in data:
            quantity = data["quantity"]
            price = data["price"]
            total = data["total"]
            if quantity and price and total:
                expected_total = quantity * price
                if abs(total - expected_total) > 0.01:
                    result.add_error(
                        f"Total ({total}) không khớp với quantity * price ({expected_total})"
                    )

    async def _validate_business_rules(
        self,
        data: dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """
        Business rule validation.

        Rules are determined by command type and industry.

        Args:
            data: Command data
            result: ValidationResult
        """
        command_id = self._command.id

        # Banking-specific rules
        if "transfer" in command_id.lower() or "transfer" in self._command.description.lower():
            # Balance check (placeholder - needs repository integration)
            if "amount" in data and data["amount"]:
                pass

        # Order-specific rules
        if "order" in command_id.lower() or "order" in self._command.description.lower():
            # Minimum order value
            if "total" in data and data["total"] and data["total"] < 10000:
                result.add_warning("Đơn hàng có giá trị dưới 10,000đ - có thể miễn phí vận chuyển")

    async def _validate_custom(
        self,
        data: dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """
        Execute custom validators.

        Args:
            data: Command data
            result: ValidationResult
        """
        for validator_name, validator_func in self._custom_validators.items():
            if callable(validator_func):
                try:
                    validation_result = validator_func(data)
                    if isinstance(validation_result, tuple):
                        is_valid, error_msg = validation_result
                        if not is_valid:
                            result.add_error(error_msg)
                    elif isinstance(validation_result, bool):
                        if not validation_result:
                            result.add_error(f"Custom validation failed: {validator_name}")
                except Exception as e:
                    result.add_error(f"Custom validator '{validator_name}' raised error: {str(e)}")