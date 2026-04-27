"""
Tests cho Commands Emitter (CP01).

Test cases:
- BackendFastAPIEmitter._emit_command()
- BackendNestJSEmitter._emit_command()
- Template rendering cho các command files
- Edge cases và error handling

TDD: Tests viết trước, sau đó verify implementation.

Author: Midicoder Team
Version: 1.0.0
"""

import tempfile
from pathlib import Path

import pytest

from midicoder.emitters.backend_fastapi import BackendFastAPIEmitter
from midicoder.emitters.backend_nestjs import BackendNestJSEmitter


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_create_order_command():
    """Sample CreateOrder Command metadata."""
    return {
        "id": "CreateOrder",
        "description": "Tạo đơn hàng mới",
        "input": [
            {
                "name": "customer_id",
                "type": "uuid",
                "required": True
            },
            {
                "name": "items",
                "type": "array",
                "item_type": "OrderItemInput",
                "required": True,
                "min_items": 1
            },
            {
                "name": "notes",
                "type": "string",
                "required": False,
                "max_length": 500
            }
        ],
        "guards": [
            {
                "type": "auth",
                "permission": "order.create"
            },
            {
                "type": "tenant_scope",
                "mode": "tenant_isolated"
            }
        ],
        "effects": [
            {
                "type": "create_record",
                "entity": "Order"
            },
            {
                "type": "create_record",
                "entity": "OrderItem"
            },
            {
                "type": "publish_event",
                "event": "OrderCreated"
            }
        ],
        "errors": [
            {
                "code": "ORDER_INVALID_ITEMS",
                "message": "Đơn hàng phải có ít nhất một sản phẩm",
                "http_status": 400
            },
            {
                "code": "ORDER_INSUFFICIENT_STOCK",
                "message": "Sản phẩm không đủ số lượng",
                "http_status": 409
            }
        ]
    }


@pytest.fixture
def sample_login_command():
    """Sample Login Command metadata (simple command)."""
    return {
        "id": "Login",
        "description": "Đăng nhập người dùng",
        "input": [
            {
                "name": "email",
                "type": "string",
                "required": True,
                "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
            },
            {
                "name": "password",
                "type": "string",
                "required": True,
                "min_length": 8
            }
        ],
        "guards": [],
        "effects": [
            {
                "type": "create_record",
                "entity": "Session"
            },
            {
                "type": "publish_event",
                "event": "UserLoggedIn"
            }
        ],
        "errors": [
            {
                "code": "AUTH_INVALID_CREDENTIALS",
                "message": "Email hoặc mật khẩu không đúng",
                "http_status": 401
            }
        ]
    }


@pytest.fixture
def fastapi_emitter():
    """FastAPI emitter instance."""
    stack_dir = Path("midicoder/stacks/fastapi/templates")
    return BackendFastAPIEmitter(stack_dir=stack_dir)


@pytest.fixture
def nestjs_emitter():
    """NestJS emitter instance."""
    stack_dir = Path("midicoder/stacks/nestjs/templates")
    return BackendNestJSEmitter(stack_dir=stack_dir)


# ============================================================================
# Tests for BackendFastAPIEmitter._emit_command()
# ============================================================================


class TestBackendFastAPIEmitterCommand:
    """Tests cho BackendFastAPIEmitter Command emitter."""

    def test_emit_command_creates_directory(
        self,
        fastapi_emitter: BackendFastAPIEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Emit command tạo directory cho command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = fastapi_emitter._emit_command(sample_create_order_command, output_dir)

            cmd_dir = output_dir / "app" / "commands" / "create_order"
            assert cmd_dir.exists()

    def test_emit_command_creates_all_files(
        self,
        fastapi_emitter: BackendFastAPIEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Emit command tạo tất cả các file cần thiết (Full DDD)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = fastapi_emitter._emit_command(sample_create_order_command, output_dir)

            # Expected files: command.py, handler.py, validator.py, guards.py, effects.py, errors.py, __init__.py
            # Plus input schema
            assert len(files) >= 7

            # Check file paths
            file_names = [f.path.name for f in files]
            assert "create_order.py" in file_names
            assert "create_order_handler.py" in file_names
            assert "create_order_validator.py" in file_names
            assert "create_order_guards.py" in file_names
            assert "create_order_effects.py" in file_names
            assert "create_order_errors.py" in file_names

    def test_emit_command_contains_class(
        self,
        fastapi_emitter: BackendFastAPIEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Command file chứa class CreateOrder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = fastapi_emitter._emit_command(sample_create_order_command, output_dir)

            # Find command.py file
            cmd_file = next((f for f in files if f.path.name == "create_order.py"), None)
            assert cmd_file is not None

            content = cmd_file.content
            assert "class CreateOrder" in content
            assert "@dataclass" in content

    def test_emit_command_handler_contains_handler_class(
        self,
        fastapi_emitter: BackendFastAPIEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Handler file chứa handler class."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = fastapi_emitter._emit_command(sample_create_order_command, output_dir)

            handler_file = next((f for f in files if f.path.name == "create_order_handler.py"), None)
            assert handler_file is not None

            content = handler_file.content
            assert "class CreateOrderHandler" in content
            assert "async def handle" in content

    def test_emit_command_validator_contains_validation(
        self,
        fastapi_emitter: BackendFastAPIEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Validator file chứa validation logic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = fastapi_emitter._emit_command(sample_create_order_command, output_dir)

            validator_file = next((f for f in files if f.path.name == "create_order_validator.py"), None)
            assert validator_file is not None

            content = validator_file.content
            assert "class CreateOrderValidator" in content
            assert "def validate" in content

    def test_emit_command_guards_contains_auth_guard(
        self,
        fastapi_emitter: BackendFastAPIEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Guards file chứa auth guard."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = fastapi_emitter._emit_command(sample_create_order_command, output_dir)

            guards_file = next((f for f in files if f.path.name == "create_order_guards.py"), None)
            assert guards_file is not None

            content = guards_file.content
            assert "CreateOrderGuards" in content
            assert "order.create" in content

    def test_emit_command_effects_contains_effects(
        self,
        fastapi_emitter: BackendFastAPIEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Effects file chứa effect implementations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = fastapi_emitter._emit_command(sample_create_order_command, output_dir)

            effects_file = next((f for f in files if f.path.name == "create_order_effects.py"), None)
            assert effects_file is not None

            content = effects_file.content
            assert "CreateOrderEffects" in content
            assert "Order" in content
            assert "_create_Order" in content

    def test_emit_command_errors_contains_error_classes(
        self,
        fastapi_emitter: BackendFastAPIEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Errors file chứa error classes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = fastapi_emitter._emit_command(sample_create_order_command, output_dir)

            errors_file = next((f for f in files if f.path.name == "create_order_errors.py"), None)
            assert errors_file is not None

            content = errors_file.content
            assert "class ORDER_INVALID_ITEMSError" in content
            assert "Đơn hàng phải có ít nhất một sản phẩm" in content
            assert "class ORDER_INSUFFICIENT_STOCKError" in content
            assert "Sản phẩm không đủ số lượng" in content

    def test_emit_command_vietnamese_comments(
        self,
        fastapi_emitter: BackendFastAPIEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Command files có Vietnamese comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = fastapi_emitter._emit_command(sample_create_order_command, output_dir)

            cmd_file = next((f for f in files if f.path.name == "create_order.py"), None)
            assert cmd_file is not None

            content = cmd_file.content
            assert "Tạo đơn hàng mới" in content

    def test_emit_simple_command_without_guards(
        self,
        fastapi_emitter: BackendFastAPIEmitter,
        sample_login_command: dict,
    ):
        """Test: Emit command không có guards vẫn hoạt động."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = fastapi_emitter._emit_command(sample_login_command, output_dir)

            # Should still create files
            assert len(files) >= 6

            guards_file = next((f for f in files if f.path.name == "login_guards.py"), None)
            assert guards_file is not None
            # Guards file should exist but be minimal
            assert "class LoginGuards" in guards_file.content


# ============================================================================
# Tests for BackendNestJSEmitter._emit_command()
# ============================================================================


class TestBackendNestJSEmitterCommand:
    """Tests cho BackendNestJSEmitter Command emitter."""

    def test_emit_command_creates_directory(
        self,
        nestjs_emitter: BackendNestJSEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Emit command tạo directory cho command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = nestjs_emitter._emit_command(sample_create_order_command, output_dir)

            cmd_dir = output_dir / "src" / "commands" / "create_order"
            assert cmd_dir.exists()

    def test_emit_command_creates_all_files(
        self,
        nestjs_emitter: BackendNestJSEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Emit command tạo tất cả các file cần thiết (Full DDD)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = nestjs_emitter._emit_command(sample_create_order_command, output_dir)

            # Expected files: command.ts, handler.ts, validator.ts, guards.ts, effects.ts, errors.ts, module.ts, index.ts
            assert len(files) >= 8

            # Check file paths
            file_names = [f.path.name for f in files]
            assert "create_order.ts" in file_names
            assert "create_order.handler.ts" in file_names
            assert "create_order.validator.ts" in file_names
            assert "create_order.guards.ts" in file_names
            assert "create_order.effects.ts" in file_names
            assert "create_order.errors.ts" in file_names
            assert "create_order.module.ts" in file_names

    def test_emit_command_contains_class(
        self,
        nestjs_emitter: BackendNestJSEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Command file chứa class CreateOrder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = nestjs_emitter._emit_command(sample_create_order_command, output_dir)

            cmd_file = next((f for f in files if f.path.name == "create_order.ts"), None)
            assert cmd_file is not None

            content = cmd_file.content
            assert "export class CreateOrder" in content

    def test_emit_command_handler_contains_handler_class(
        self,
        nestjs_emitter: BackendNestJSEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Handler file chứa handler class với @Injectable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = nestjs_emitter._emit_command(sample_create_order_command, output_dir)

            handler_file = next((f for f in files if f.path.name == "create_order.handler.ts"), None)
            assert handler_file is not None

            content = handler_file.content
            assert "export class CreateOrderHandler" in content
            assert "@Injectable()" in content

    def test_emit_command_module_contains_module(
        self,
        nestjs_emitter: BackendNestJSEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Module file chứa NestJS Module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = nestjs_emitter._emit_command(sample_create_order_command, output_dir)

            module_file = next((f for f in files if f.path.name == "create_order.module.ts"), None)
            assert module_file is not None

            content = module_file.content
            assert "@Module" in content
            assert "export class CreateOrderModule" in content

    def test_emit_command_vietnamese_comments(
        self,
        nestjs_emitter: BackendNestJSEmitter,
        sample_create_order_command: dict,
    ):
        """Test: Command files có Vietnamese comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = nestjs_emitter._emit_command(sample_create_order_command, output_dir)

            cmd_file = next((f for f in files if f.path.name == "create_order.ts"), None)
            assert cmd_file is not None

            content = cmd_file.content
            assert "Tạo đơn hàng mới" in content


# ============================================================================
# Edge Cases
# ============================================================================


class TestCommandsEmitterEdgeCases:
    """Edge case tests cho Commands emitter."""

    def test_emit_command_with_empty_input(
        self,
        fastapi_emitter: BackendFastAPIEmitter,
    ):
        """Test: Emit command với empty input không crash."""
        command = {
            "id": "EmptyInputCommand",
            "description": "Command với empty input",
            "input": [],
            "guards": [],
            "effects": [],
            "errors": []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = fastapi_emitter._emit_command(command, output_dir)
            assert len(files) >= 6

    def test_emit_command_with_many_inputs(
        self,
        fastapi_emitter: BackendFastAPIEmitter,
    ):
        """Test: Emit command với nhiều input fields."""
        command = {
            "id": "ComplexCommand",
            "description": "Command với nhiều inputs",
            "input": [
                {"name": f"field_{i}", "type": "string", "required": True}
                for i in range(20)
            ],
            "guards": [],
            "effects": [],
            "errors": []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = fastapi_emitter._emit_command(command, output_dir)

            cmd_file = next((f for f in files if f.path.name == "complex_command.py"), None)
            assert cmd_file is not None

            content = cmd_file.content
            assert "field_0" in content
            assert "field_19" in content


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])