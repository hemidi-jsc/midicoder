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

from .models import Command, Field, ValidationResult


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
        tenant_id: str | None = None,
    ) -> None:
        """
        Business rule validation.

        Rules are determined by command type and industry.

        KPI-029: Tenant-aware validation.

        Args:
            data: Command data
            result: ValidationResult
            tenant_id: Tenant ID cho multi-tenant validation
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

    # -------------------------------------------------------------------------
    # RX02: Financial Integrity Validation (Banking - DP11)
    # -------------------------------------------------------------------------

    async def validate_rx02(
        self,
        data: dict[str, Any],
        tenant_id: str | None = None,
    ) -> ValidationResult:
        """
        Validate RX02 Financial Integrity requirements.

        RX02 Obligations:
        - double_entry_required: Mọi giao dịch phải có debit = credit
        - transaction_immutability: Transactions immutable sau commit
        - reconciliation_mandatory: Daily reconciliation required

        KPI-029: Tenant-aware validation.

        Args:
            data: Command data
            tenant_id: Tenant ID

        Returns:
            ValidationResult với errors nếu vi phạm RX02
        """
        result = ValidationResult(is_valid=True)

        # RX02-01: Double-entry validation (debit = credit)
        await self._validate_double_entry(data, result, tenant_id)

        # RX02-02: Transaction immutability check
        await self._validate_transaction_immutability(data, result, tenant_id)

        return result

    async def _validate_double_entry(
        self,
        data: dict[str, Any],
        result: ValidationResult,
        tenant_id: str | None = None,
    ) -> None:
        """
        Validate double-entry bookkeeping rule.

        Rule: Debit tổng phải bằng Credit tổng.

        Args:
            data: Command data với debit/credit fields
            result: ValidationResult
            tenant_id: Tenant ID
        """
        debit = data.get("debit") or 0
        credit = data.get("credit") or 0

        if debit > 0 or credit > 0:
            if abs(debit - credit) > 0.01:  # Allow 0.01 tolerance cho rounding
                result.add_error(
                    f"Vi phạm double-entry rule: Debit ({debit}) != Credit ({credit})"
                )

    async def _validate_transaction_immutability(
        self,
        data: dict[str, Any],
        result: ValidationResult,
        tenant_id: str | None = None,
    ) -> None:
        """
        Validate transaction immutability.

        Rule: Transaction đã commit không thể sửa đổi.

        Args:
            data: Command data
            result: ValidationResult
            tenant_id: Tenant ID
        """
        # Check nếu đây là update transaction đã commit
        if data.get("status") == "completed" and data.get("is_update"):
            result.add_error("Không thể sửa giao dịch đã hoàn thành (transaction immutability)")

    # -------------------------------------------------------------------------
    # RX03: AML/KYC Validation (Banking - DP11)
    # -------------------------------------------------------------------------

    async def validate_rx03(
        self,
        data: dict[str, Any],
        user_id: str | None = None,
        tenant_id: str | None = None,
    ) -> ValidationResult:
        """
        Validate RX03 AML/KYC requirements.

        RX03 Obligations:
        - kyc_verification_required: User phải KYC verified
        - aml_screening_required: Transactions phải qua AML screening
        - suspicious_activity_reporting: Flag transactions > threshold

        KPI-029: Tenant-aware validation.

        Args:
            data: Command data
            user_id: User ID
            tenant_id: Tenant ID

        Returns:
            ValidationResult với errors nếu vi phạm RX03
        """
        result = ValidationResult(is_valid=True)

        # RX03-01: KYC verification check
        await self._validate_kyc_verification(data, user_id, result, tenant_id)

        # RX03-02: AML screening check
        await self._validate_aml_screening(data, user_id, result, tenant_id)

        # RX03-03: Suspicious activity threshold check
        await self._validate_suspicious_activity(data, result, tenant_id)

        return result

    async def _validate_kyc_verification(
        self,
        data: dict[str, Any],
        user_id: str | None,
        result: ValidationResult,
        tenant_id: str | None = None,
    ) -> None:
        """
        Validate KYC verification status.

        Rule: User phải có KYC verified trước khi thực hiện financial transactions.

        Args:
            data: Command data
            user_id: User ID
            result: ValidationResult
            tenant_id: Tenant ID
        """
        is_kyc_verified = data.get("kyc_verified", False)

        if not is_kyc_verified and user_id:
            result.add_error(
                f"User {user_id} chưa được KYC verify (tenant: {tenant_id})"
            )

    async def _validate_aml_screening(
        self,
        data: dict[str, Any],
        user_id: str | None,
        result: ValidationResult,
        tenant_id: str | None = None,
    ) -> None:
        """
        Validate AML screening status.

        Rule: Transaction phải qua AML screening.

        Args:
            data: Command data
            user_id: User ID
            result: ValidationResult
            tenant_id: Tenant ID
        """
        is_aml_cleared = data.get("aml_cleared", False)
        amount = data.get("amount", 0)

        if not is_aml_cleared and amount > 0:
            result.add_error(
                f"Transaction {amount}đ chưa qua AML screening (tenant: {tenant_id})"
            )

    async def _validate_suspicious_activity(
        self,
        data: dict[str, Any],
        result: ValidationResult,
        tenant_id: str | None = None,
    ) -> None:
        """
        Validate suspicious activity threshold.

        Rule: Transactions > threshold phải được flag cho SAR.

        Args:
            data: Command data
            result: ValidationResult
            tenant_id: Tenant ID
        """
        amount = data.get("amount", 0)
        threshold = 100000000  # 100 triệu VND threshold

        if amount and amount > threshold:
            result.add_warning(
                f"Giao dịch {amount}đ vượt quá threshold {threshold}đ - cần báo cáo SAR (tenant: {tenant_id})"
            )

    # -------------------------------------------------------------------------
    # RX04: HIPAA Compliance Validation (Healthcare - DP09/DP10)
    # -------------------------------------------------------------------------

    async def validate_rx04(
        self,
        data: dict[str, Any],
        user_id: str | None = None,
        tenant_id: str | None = None,
    ) -> ValidationResult:
        """
        Validate RX04 HIPAA compliance requirements.

        RX04 Obligations:
        - hipaa_compliance_required: PHI data handling phải comply HIPAA
        - clinical_audit_trail: All PHI access phải được log
        - phii_encryption_required: PHI fields phải encrypted at rest
        - minimum_necessary_access: Users chỉ access necessary PHI fields

        KPI-029: Tenant-aware validation.

        Args:
            data: Command data
            user_id: User ID
            tenant_id: Tenant ID

        Returns:
            ValidationResult với errors nếu vi phạm RX04
        """
        result = ValidationResult(is_valid=True)

        # RX04-01: PHI encryption check
        await self._validate_phi_encryption(data, result, tenant_id)

        # RX04-02: Minimum necessary access check
        await self._validate_minimum_necessary_access(data, user_id, result, tenant_id)

        # RX04-03: Audit trail check
        await self._validate_audit_trail(data, user_id, result, tenant_id)

        return result

    async def _validate_phi_encryption(
        self,
        data: dict[str, Any],
        result: ValidationResult,
        tenant_id: str | None = None,
    ) -> None:
        """
        Validate PHI encryption status.

        Rule: PHI fields phải được encrypted at rest.

        Args:
            data: Command data
            result: ValidationResult
            tenant_id: Tenant ID
        """
        phi_fields = ["ssn", "full_name", "date_of_birth", "medical_history", "note_text"]

        for field in phi_fields:
            if field in data and data[field]:
                is_encrypted = data.get(f"{field}_encrypted", False)
                if not is_encrypted:
                    result.add_error(
                        f"PHI field '{field}' không được encrypt (tenant: {tenant_id})"
                    )

    async def _validate_minimum_necessary_access(
        self,
        data: dict[str, Any],
        user_id: str | None,
        result: ValidationResult,
        tenant_id: str | None = None,
    ) -> None:
        """
        Validate minimum necessary access principle.

        Rule: Users chỉ có thể access PHI fields cần thiết cho công việc.

        Args:
            data: Command data
            user_id: User ID
            result: ValidationResult
            tenant_id: Tenant ID
        """
        requested_fields = data.get("requested_phi_fields", [])
        allowed_fields = data.get("user_allowed_fields", [])

        excess_access = set(requested_fields) - set(allowed_fields)

        if excess_access:
            result.add_error(
                f"User {user_id} cố gắng truy cập PHI fields không được phép: {excess_access} (tenant: {tenant_id})"
            )

    async def _validate_audit_trail(
        self,
        data: dict[str, Any],
        user_id: str | None,
        result: ValidationResult,
        tenant_id: str | None = None,
    ) -> None:
        """
        Validate clinical audit trail.

        Rule: Tất cả PHI access phải được log.

        Args:
            data: Command data
            user_id: User ID
            result: ValidationResult
            tenant_id: Tenant ID
        """
        has_audit_log = data.get("audit_log_written", False)
        phi_accessed = any(
            field in data for field in ["ssn", "full_name", "medical_history", "note_text"]
        )

        if phi_accessed and not has_audit_log:
            result.add_error(
                f"PHI access không được ghi vào audit trail (user: {user_id}, tenant: {tenant_id})"
            )

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