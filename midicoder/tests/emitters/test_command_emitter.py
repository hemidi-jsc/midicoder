"""
Tests cho Command Emitter Module (CP01 - Enhanced).

Test cases:
- Command models (EffectType, GuardType, Command, etc.)
- TransactionManager
- CommandValidator
- CommandGuards
- CommandEffects
- CommandEmitter

Author: Midicoder Team
Version: 2.0.0
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from midicoder.emitters.core.cp01_domain_model import (
    Command,
    CommandEffect,
    CommandError,
    CommandField,
    CommandGuard,
    CommandGuards,
    CommandValidator,
    EffectType,
    FastAPICommandEmitter,
    GuardType,
    NestJSCommandEmitter,
    ValidationResult,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_create_order_command():
    """Sample CreateOrder Command với đầy đủ features."""
    return Command(
        id="CreateOrder",
        description="Tạo đơn hàng mới",
        input=[
            CommandField(name="customer_id", field_type="uuid", required=True),
            CommandField(
                name="items",
                field_type="array",
                required=True,
                min_items=1,
                max_items=100,
            ),
            CommandField(
                name="notes",
                field_type="string",
                required=False,
                max_length=500,
            ),
        ],
        guards=[
            CommandGuard(guard_type=GuardType.AUTH, permission="order.create"),
            CommandGuard(guard_type=GuardType.TENANT_SCOPE, mode="tenant_isolated"),
        ],
        effects=[
            CommandEffect(effect_type=EffectType.BEGIN_TRANSACTION),
            CommandEffect(effect_type=EffectType.CREATE_RECORD, entity="Order"),
            CommandEffect(effect_type=EffectType.CREATE_RECORD, entity="OrderItem"),
            CommandEffect(effect_type=EffectType.PUBLISH_EVENT, event="OrderCreated"),
            CommandEffect(effect_type=EffectType.WRITE_AUDIT_LOG, audit_action="order_created"),
            CommandEffect(effect_type=EffectType.COMMIT_TRANSACTION),
        ],
        errors=[
            CommandError(
                code="ORDER_INVALID_ITEMS",
                message="Đơn hàng phải có ít nhất một sản phẩm",
                http_status=400,
            ),
            CommandError(
                code="ORDER_INSUFFICIENT_STOCK",
                message="Sản phẩm không đủ số lượng",
                http_status=409,
            ),
        ],
        transaction_required=True,
        on_error="rollback",
    )


@pytest.fixture
def sample_transfer_money_command():
    """Sample TransferMoney Command (Banking)."""
    return Command(
        id="TransferMoney",
        description="Chuyển tiền giữa các tài khoản",
        input=[
            CommandField(name="from_account", field_type="uuid", required=True),
            CommandField(name="to_account", field_type="uuid", required=True),
            CommandField(name="amount", field_type="decimal", required=True, min_value=0.01),
            CommandField(name="currency", field_type="string", required=True, max_length=3),
        ],
        guards=[
            CommandGuard(guard_type=GuardType.AUTH, permission="account.transfer"),
            CommandGuard(guard_type=GuardType.TENANT_SCOPE, mode="tenant_isolated"),
            CommandGuard(guard_type=GuardType.KYC_CHECK),
            CommandGuard(guard_type=GuardType.AML_SCREENING),
        ],
        effects=[
            CommandEffect(effect_type=EffectType.BEGIN_TRANSACTION),
            CommandEffect(effect_type=EffectType.QUERY_RECORDS, entity="Account"),
            CommandEffect(effect_type=EffectType.UPDATE_RECORD, entity="Account"),
            CommandEffect(effect_type=EffectType.UPDATE_RECORD, entity="Account"),
            CommandEffect(effect_type=EffectType.WRITE_AUDIT_LOG, audit_action="money_transferred"),
            CommandEffect(effect_type=EffectType.PUBLISH_EVENT, event="MoneyTransferred"),
            CommandEffect(effect_type=EffectType.COMMIT_TRANSACTION),
        ],
        errors=[
            CommandError(
                code="INSUFFICIENT_FUNDS",
                message="Sald không đủ",
                http_status=400,
            ),
            CommandError(
                code="SAME_ACCOUNT",
                message="Không thể chuyển tiền cho chính mình",
                http_status=400,
            ),
        ],
        transaction_required=True,
        on_error="rollback",
    )


@pytest.fixture
def fastapi_command_emitter():
    """FastAPI Command emitter instance."""
    stack_dir = Path("midicoder/stacks/fastapi/templates")
    return FastAPICommandEmitter(stack_dir=stack_dir)


@pytest.fixture
def nestjs_command_emitter():
    """NestJS Command emitter instance."""
    stack_dir = Path("midicoder/stacks/nestjs/templates")
    return NestJSCommandEmitter(stack_dir=stack_dir)


# ============================================================================
# Tests for Command Models
# ============================================================================


class TestCommandModels:
    """Tests cho Command models."""

    def test_command_has_auth_guard(self, sample_create_order_command: Command):
        """Test: Command.has_auth_guard() trả về True khi có AUTH guard."""
        assert sample_create_order_command.has_auth_guard() is True

    def test_command_has_tenant_guard(self, sample_create_order_command: Command):
        """Test: Command.has_tenant_guard() trả về True khi có TENANT_SCOPE guard."""
        assert sample_create_order_command.has_tenant_guard() is True

    def test_command_has_transaction_effects(
        self, sample_transfer_money_command: Command
    ):
        """Test: Command.has_transaction_effects() trả về True khi có transaction effects."""
        assert sample_transfer_money_command.has_transaction_effects() is True

    def test_command_get_required_permissions(self, sample_create_order_command: Command):
        """Test: Command.get_required_permissions() trả về danh sách permissions."""
        permissions = sample_create_order_command.get_required_permissions()
        assert "order.create" in permissions

    def test_command_to_dict_and_from_dict(self, sample_create_order_command: Command):
        """Test: Command.to_dict() và from_dict() hoạt động chính xác."""
        cmd_dict = sample_create_order_command.to_dict()
        reconstructed = Command.from_dict(cmd_dict)

        assert reconstructed.id == sample_create_order_command.id
        assert reconstructed.description == sample_create_order_command.description
        assert len(reconstructed.input) == len(sample_create_order_command.input)
        assert len(reconstructed.effects) == len(sample_create_order_command.effects)

    def test_effect_types_enum(self):
        """Test: EffectType enum có đầy đủ 19+ types."""
        # Core effects
        assert EffectType.CREATE_RECORD.value == "create_record"
        assert EffectType.UPDATE_RECORD.value == "update_record"
        assert EffectType.DELETE_RECORD.value == "delete_record"
        assert EffectType.PUBLISH_EVENT.value == "publish_event"

        # Transaction effects
        assert EffectType.BEGIN_TRANSACTION.value == "begin_transaction"
        assert EffectType.COMMIT_TRANSACTION.value == "commit_transaction"
        assert EffectType.ROLLBACK_TRANSACTION.value == "rollback_transaction"

        # Integration effects
        assert EffectType.CALL_EXTERNAL_API.value == "call_external_api"
        assert EffectType.SEND_EMAIL.value == "send_email"
        assert EffectType.SEND_SMS.value == "send_sms"

    def test_guard_types_enum(self):
        """Test: GuardType enum có đầy đủ types."""
        # Core guards
        assert GuardType.AUTH.value == "auth"
        assert GuardType.TENANT_SCOPE.value == "tenant_scope"

        # Compliance guards
        assert GuardType.KYC_CHECK.value == "kyc_check"
        assert GuardType.AML_SCREENING.value == "aml_screening"
        assert GuardType.HIPAA_ACCESS.value == "hipaa_access"


# ============================================================================
# Tests for CommandValidator
# ============================================================================


class TestCommandValidator:
    """Tests cho CommandValidator."""

    @pytest.mark.asyncio
    async def test_validate_required_field(
        self, sample_create_order_command: Command
    ):
        """Test: Validation bắt buộc field."""
        validator = CommandValidator(sample_create_order_command)
        result = await validator.validate({})

        assert result.is_valid is False
        assert any("customer_id" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_pattern(self):
        """Test: Validation pattern."""
        command = Command(
            id="TestCommand",
            description="Test",
            input=[
                CommandField(
                    name="email",
                    field_type="string",
                    required=True,
                    pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                )
            ],
        )
        validator = CommandValidator(command)
        result = await validator.validate({"email": "invalid-email"})

        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_validate_min_max_length(self):
        """Test: Validation min/max length."""
        command = Command(
            id="TestCommand",
            description="Test",
            input=[
                CommandField(
                    name="username",
                    field_type="string",
                    required=True,
                    min_length=3,
                    max_length=20,
                )
            ],
        )
        validator = CommandValidator(command)

        # Test min length
        result = await validator.validate({"username": "ab"})
        assert result.is_valid is False

        # Test max length
        result = await validator.validate({"username": "a" * 21})
        assert result.is_valid is False

        # Test valid
        result = await validator.validate({"username": "abc"})
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_cross_field_validation(self):
        """Test: Cross-field validation (end_date > start_date)."""
        command = Command(
            id="TestCommand",
            description="Test",
            input=[],
        )
        validator = CommandValidator(command)

        # Test end_date before start_date
        result = await validator.validate(
            {"start_date": "2026-05-01", "end_date": "2026-04-01"}
        )
        assert result.is_valid is False


# ============================================================================
# Tests for CommandGuards
# ============================================================================


class MockComplianceService:
    """Mock compliance service cho testing."""
    
    def __init__(self, kyc_verified: bool = True, aml_clear: bool = True, hipaa_cleared: bool = True):
        """Initialize mock compliance service."""
        self.kyc_verified = kyc_verified
        self.aml_clear = aml_clear
        self.hipaa_cleared = hipaa_cleared
    
    async def check_kyc(self, user_id: str) -> bool:
        """Check KYC verification."""
        return self.kyc_verified
    
    async def check_aml(self, user_id: str, transaction_data: dict) -> bool:
        """Check AML screening."""
        return self.aml_clear
    
    async def check_hipaa_clearance(self, user_id: str, tenant_id: str = None) -> bool:
        """Check HIPAA clearance."""
        return self.hipaa_cleared


class TestCommandGuards:
    """Tests cho CommandGuards."""

    @pytest.mark.asyncio
    async def test_check_auth_no_user(self, sample_create_order_command: Command):
        """Test: AUTH guard fail khi không có user_id."""
        guards = CommandGuards(sample_create_order_command)

        with pytest.raises(PermissionError) as exc_info:
            await guards.check_all({}, user_id=None, tenant_id="tenant_001")

        assert "không được xác thực" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_tenant_no_tenant_id(
        self, sample_create_order_command: Command
    ):
        """Test: TENANT guard fail khi không có tenant_id."""
        from midicoder.errors import MidicoderError

        guards = CommandGuards(sample_create_order_command)

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id="user_001", tenant_id=None)

        assert exc_info.value.code.value == "MDC-CP01-052"

    @pytest.mark.asyncio
    async def test_kyc_check_pass(self):
        """Test: KYC guard pass khi user đã verify."""
        command = Command(
            id="TransferMoney",
            description="Chuyển tiền",
            input=[],
            guards=[
                CommandGuard(guard_type=GuardType.KYC_CHECK),
            ],
        )
        
        compliance_service = MockComplianceService(kyc_verified=True)
        guards = CommandGuards(command, compliance_service=compliance_service)

        # Should not raise
        await guards.check_all({}, user_id="user_001", tenant_id="tenant_001")

    @pytest.mark.asyncio
    async def test_kyc_check_fail(self):
        """Test: KYC guard fail khi user chưa verify."""
        from midicoder.errors import MidicoderError

        command = Command(
            id="TransferMoney",
            description="Chuyển tiền",
            input=[],
            guards=[
                CommandGuard(guard_type=GuardType.KYC_CHECK),
            ],
        )
        
        compliance_service = MockComplianceService(kyc_verified=False)
        guards = CommandGuards(command, compliance_service=compliance_service)

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id="user_001", tenant_id="tenant_001")

        assert exc_info.value.code.value == "MDC-CP01-057"

    @pytest.mark.asyncio
    async def test_aml_screening_pass(self):
        """Test: AML guard pass khi screening clear."""
        command = Command(
            id="TransferMoney",
            description="Chuyển tiền",
            input=[
                CommandField(name="amount", field_type="decimal", required=True),
            ],
            guards=[
                CommandGuard(guard_type=GuardType.AML_SCREENING),
            ],
        )
        
        compliance_service = MockComplianceService(aml_clear=True)
        guards = CommandGuards(command, compliance_service=compliance_service)

        # Should not raise
        await guards.check_all({"amount": 1000}, user_id="user_001", tenant_id="tenant_001")

    @pytest.mark.asyncio
    async def test_aml_screening_fail(self):
        """Test: AML guard fail khi screening failed."""
        from midicoder.errors import MidicoderError

        command = Command(
            id="TransferMoney",
            description="Chuyển tiền",
            input=[
                CommandField(name="amount", field_type="decimal", required=True),
            ],
            guards=[
                CommandGuard(guard_type=GuardType.AML_SCREENING),
            ],
        )
        
        compliance_service = MockComplianceService(aml_clear=False)
        guards = CommandGuards(command, compliance_service=compliance_service)

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({"amount": 1000000}, user_id="user_001", tenant_id="tenant_001")

        assert exc_info.value.code.value == "MDC-CP01-058"

    @pytest.mark.asyncio
    async def test_hipaa_access_pass(self):
        """Test: HIPAA guard pass khi user có clearance."""
        command = Command(
            id="ViewPatientRecord",
            description="Xem hồ sơ bệnh nhân",
            input=[],
            guards=[
                CommandGuard(guard_type=GuardType.HIPAA_ACCESS),
            ],
        )
        
        compliance_service = MockComplianceService(hipaa_cleared=True)
        guards = CommandGuards(command, compliance_service=compliance_service)

        # Should not raise
        await guards.check_all({}, user_id="doctor_001", tenant_id="hospital_001")

    @pytest.mark.asyncio
    async def test_hipaa_access_fail(self):
        """Test: HIPAA guard fail khi user không có clearance."""
        from midicoder.errors import MidicoderError

        command = Command(
            id="ViewPatientRecord",
            description="Xem hồ sơ bệnh nhân",
            input=[],
            guards=[
                CommandGuard(guard_type=GuardType.HIPAA_ACCESS),
            ],
        )
        
        compliance_service = MockComplianceService(hipaa_cleared=False)
        guards = CommandGuards(command, compliance_service=compliance_service)

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id="user_001", tenant_id="hospital_001")

        assert exc_info.value.code.value == "MDC-CP01-059"


# ============================================================================
# Tests for FastAPICommandEmitter
# ============================================================================


class TestFastAPICommandEmitter:
    """Tests cho FastAPICommandEmitter."""

    def test_emit_creates_files(
        self, fastapi_command_emitter: FastAPICommandEmitter, sample_create_order_command: Command
    ):
        """Test: emit() tạo đầy đủ files."""
        files = fastapi_command_emitter.emit(sample_create_order_command, Path("/tmp"))

        # Files are named with snake_case (proper Python convention)
        assert "create_order.py" in files
        assert "create_order_handler.py" in files
        assert "create_order_validator.py" in files
        assert "create_order_guards.py" in files
        assert "create_order_effects.py" in files
        assert "create_order_errors.py" in files
        assert "__init__.py" in files

    def test_emit_content_contains_command_id(
        self, fastapi_command_emitter: FastAPICommandEmitter, sample_create_order_command: Command
    ):
        """Test: Generated content chứa command ID."""
        files = fastapi_command_emitter.emit(sample_create_order_command, Path("/tmp"))

        cmd_content = files["create_order.py"]
        assert "CreateOrder" in cmd_content


# ============================================================================
# Tests for NestJSCommandEmitter
# ============================================================================


class TestNestJSCommandEmitter:
    """Tests cho NestJSCommandEmitter."""

    def test_emit_creates_files(
        self, nestjs_command_emitter: NestJSCommandEmitter, sample_create_order_command: Command
    ):
        """Test: emit() tạo đầy đủ files cho NestJS."""
        files = nestjs_command_emitter.emit(sample_create_order_command, Path("/tmp"))

        # NestJS files are named with snake_case and .ts extension
        assert "create_order.ts" in files
        assert "create_order.handler.ts" in files
        assert "create_order.validator.ts" in files
        assert "create_order.guards.ts" in files
        assert "create_order.effects.ts" in files
        assert "create_order.errors.ts" in files
        assert "create_order.module.ts" in files
        assert "index.ts" in files

    def test_emit_content_contains_command_id(
        self, nestjs_command_emitter: NestJSCommandEmitter, sample_create_order_command: Command
    ):
        """Test: Generated content chứa command ID."""
        files = nestjs_command_emitter.emit(sample_create_order_command, Path("/tmp"))

        cmd_content = files["create_order.ts"]
        assert "CreateOrder" in cmd_content

    def test_to_snake_case(self):
        """Test: _to_snake_case() module function chuyển PascalCase sang snake_case đúng."""
        from midicoder.emitters.core.cp01_domain_model.command_nestjs import _to_snake_case

        assert _to_snake_case("CreateOrder") == "create_order"
        assert _to_snake_case("TransferMoney") == "transfer_money"
        assert _to_snake_case("CreateOrderItem") == "create_order_item"


# ============================================================================
# Tests for TransactionManagerSQL
# ============================================================================


class TestTransactionManagerSQL:
    """Tests cho TransactionManager với SQLAlchemy integration."""

    @pytest.mark.asyncio
    async def test_begin_transaction_with_sqlalchemy(self):
        """Test: Begin transaction với SQLAlchemy session."""
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from midicoder.emitters.core.cp01_domain_model.command_transaction import TransactionManagerSQL

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        session_factory = async_sessionmaker(engine, class_=AsyncSession)
        tm = TransactionManagerSQL(engine, session_factory)

        session = await tm.begin_transaction("tx_test_001")

        assert tm.is_in_transaction is True
        assert session is not None

        await tm.rollback_transaction()
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_commit_transaction_with_sqlalchemy(self):
        """Test: Commit transaction với SQLAlchemy."""
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from midicoder.emitters.core.cp01_domain_model.command_transaction import TransactionManagerSQL

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        session_factory = async_sessionmaker(engine, class_=AsyncSession)
        tm = TransactionManagerSQL(engine, session_factory)

        await tm.begin_transaction("tx_test_002")
        await tm.commit_transaction()

        assert tm.is_in_transaction is False

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_rollback_transaction_with_sqlalchemy(self):
        """Test: Rollback transaction với SQLAlchemy."""
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from midicoder.emitters.core.cp01_domain_model.command_transaction import TransactionManagerSQL

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        session_factory = async_sessionmaker(engine, class_=AsyncSession)
        tm = TransactionManagerSQL(engine, session_factory)

        await tm.begin_transaction("tx_test_003")
        await tm.rollback_transaction()

        assert tm.is_in_transaction is False

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_transaction_nested_with_sqlalchemy(self):
        """Test: Nested transactions với savepoints."""
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from midicoder.emitters.core.cp01_domain_model.command_transaction import TransactionManagerSQL

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        session_factory = async_sessionmaker(engine, class_=AsyncSession)
        tm = TransactionManagerSQL(engine, session_factory)

        # Begin outer transaction
        session1 = await tm.begin_transaction("tx_outer")
        assert tm.is_in_transaction is True

        # Begin nested transaction
        session2 = await tm.begin_transaction("tx_inner")
        assert session1 is session2  # Same session cho nested

        await tm.rollback_transaction()  # Rollback inner
        await tm.rollback_transaction()  # Rollback outer

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_transaction_error_rollback(self):
        """Test: Auto rollback khi có exception."""
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from midicoder.emitters.core.cp01_domain_model.command_transaction import TransactionManagerSQL

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        session_factory = async_sessionmaker(engine, class_=AsyncSession)
        tm = TransactionManagerSQL(engine, session_factory)

        # Raise exception inside transaction context (no pre-existing transaction)
        try:
            async with tm.transaction("tx_error_test") as session:
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected

        # Transaction should be rolled back
        assert tm.is_in_transaction is False

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_transaction_concurrent_access(self):
        """Test: Concurrent transaction access handling."""
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from midicoder.emitters.core.cp01_domain_model.command_transaction import TransactionManagerSQL

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        session_factory = async_sessionmaker(engine, class_=AsyncSession)
        tm = TransactionManagerSQL(engine, session_factory)

        # Begin first transaction
        session1 = await tm.begin_transaction("tx_concurrent_1")

        # Second transaction should be nested (same session)
        session2 = await tm.begin_transaction("tx_concurrent_2")
        assert session1 is session2

        # Commit both
        await tm.commit_transaction()
        await tm.commit_transaction()

        assert tm.is_in_transaction is False

        await engine.dispose()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
