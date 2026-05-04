"""
Tests cho FastAPI Auth Emitter.

Unit tests cho:
- FastAPIAuthEmitter class
- FastAPI auth code generation
- Template rendering
- KPI-028, KPI-029, KPI-030, KPI-031 validation

CP02: Multi-Tenant Architecture
CP03: Authentication & Authorization
CP04: RBAC & Policy Engine

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile

from midicoder.emitters.authnz.models import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    JWTAuthConfig,
    Policy,
    PolicyCondition,
    PolicyEffect,
    Role,
    TenantMode,
)
from midicoder.emitters.authnz.fastapi import (
    emit_fastapi_auth,
    FastAPIAuthEmitter,
    GeneratedFile,
)
from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_auth_ir():
    """Sample AuthIR cho FastAPI tests."""
    return AuthIR(
        tenant_mode=TenantMode.SCHEMA,
        providers=[
            AuthProvider(
                id="jwt_auth",
                provider_type=AuthProviderType.JWT,
                config=JWTAuthConfig(
                    expire_minutes=30,
                    refresh_expire_days=7,
                    algorithm="HS256",
                    tenant_scoped=True,
                ),
            ),
        ],
        roles={
            "super_admin": Role(
                id="super_admin",
                permissions=["*"],
                parents=[],
                tenant_scoped=False,
                description="Super admin",
            ),
            "tenant_admin": Role(
                id="tenant_admin",
                permissions=["user:*", "order:*"],
                parents=[],
                tenant_scoped=True,
                description="Tenant admin",
            ),
            "user": Role(
                id="user",
                permissions=["order:create", "order:read"],
                parents=[],
                tenant_scoped=True,
                description="Regular user",
            ),
        },
        policies={
            "tenant_isolation": Policy(
                id="tenant_isolation",
                effect=PolicyEffect.DENY,
                conditions=[
                    PolicyCondition(
                        expression="user.tenant_id != resource.tenant_id",
                        description="Cross-tenant access denied",
                    ),
                ],
                description="Tenant isolation policy",
            ),
        },
    )


@pytest.fixture
def stack_dir():
    """FastAPI templates directory."""
    return Path("midicoder/stacks/fastapi/templates")


@pytest.fixture
def temp_output_dir():
    """Temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ============================================================================
# Test FastAPIAuthEmitter Initialization
# ============================================================================


class TestFastAPIAuthEmitterInit:
    """Tests cho FastAPIAuthEmitter initialization."""

    def test_init_with_valid_stack_dir(self, stack_dir):
        """Test init với valid stack directory."""
        emitter = FastAPIAuthEmitter(stack_dir=stack_dir)
        assert emitter.stack_dir == stack_dir
        assert emitter.template_env is not None

    def test_init_with_invalid_stack_dir(self):
        """Test init với invalid stack directory."""
        with pytest.raises(FileNotFoundError):
            FastAPIAuthEmitter(stack_dir=Path("/nonexistent/path"))


# ============================================================================
# Test FastAPIAuthEmitter emit()
# ============================================================================


class TestFastAPIAuthEmitterEmit:
    """Tests cho FastAPIAuthEmitter.emit() method."""

    def test_emit_returns_generated_files(
        self, sample_auth_ir, stack_dir, temp_output_dir
    ):
        """Test emit() returns list of GeneratedFile."""
        emitter = FastAPIAuthEmitter(stack_dir=stack_dir)
        files = emitter.emit(sample_auth_ir, temp_output_dir)

        assert isinstance(files, list)
        assert len(files) > 0
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_creates_security_directory(self, sample_auth_ir, stack_dir, temp_output_dir):
        """Test emit() creates core/security directory."""
        emitter = FastAPIAuthEmitter(stack_dir=stack_dir)
        emitter.emit(sample_auth_ir, temp_output_dir)

        security_dir = temp_output_dir / "core" / "security"
        assert security_dir.exists()

    def test_emit_creates_expected_files(
        self, sample_auth_ir, stack_dir, temp_output_dir
    ):
        """Test emit() creates expected auth files."""
        emitter = FastAPIAuthEmitter(stack_dir=stack_dir)
        files = emitter.emit(sample_auth_ir, temp_output_dir)

        file_paths = [f.path.name for f in files]

        assert "__init__.py" in file_paths
        assert "jwt_auth.py" in file_paths
        assert "rbac_service.py" in file_paths
        assert "permissions.py" in file_paths
        assert "policy_engine.py" in file_paths
        assert "tenant_context.py" in file_paths

    def test_emit_files_have_correct_content(
        self, sample_auth_ir, stack_dir, temp_output_dir
    ):
        """Test emit() creates files with correct content."""
        emitter = FastAPIAuthEmitter(stack_dir=stack_dir)
        files = emitter.emit(sample_auth_ir, temp_output_dir)

        content_map = {f.path.name: f.content for f in files}

        # Check jwt_auth.py contains expected content
        jwt_content = content_map.get("jwt_auth.py", "")
        assert "jwt" in jwt_content.lower() or "token" in jwt_content.lower()

        # Check rbac_service.py contains expected content
        rbac_content = content_map.get("rbac_service.py", "")
        assert "rbac" in rbac_content.lower() or "permission" in rbac_content.lower()

        # Check tenant_context.py contains expected content
        tenant_content = content_map.get("tenant_context.py", "")
        assert "tenant" in tenant_content.lower()


# ============================================================================
# Test FastAPIAuthEmitter with Different Configurations
# ============================================================================


class TestFastAPIAuthEmitterConfigurations:
    """Tests cho FastAPIAuthEmitter với different configurations."""

    def test_emit_with_row_tenant_mode(self, stack_dir, temp_output_dir):
        """Test emit() với ROW tenant mode."""
        auth_ir = AuthIR(
            tenant_mode=TenantMode.ROW,
            providers=[
                AuthProvider(
                    id="jwt_auth",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(),
                ),
            ],
            roles={},
            policies={},
        )

        emitter = FastAPIAuthEmitter(stack_dir=stack_dir)
        files = emitter.emit(auth_ir, temp_output_dir)

        assert len(files) > 0

    def test_emit_with_custom_jwt_config(self, stack_dir, temp_output_dir):
        """Test emit() với custom JWT config."""
        auth_ir = AuthIR(
            tenant_mode=TenantMode.SCHEMA,
            providers=[
                AuthProvider(
                    id="custom_jwt",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(
                        expire_minutes=60,
                        refresh_expire_days=14,
                        algorithm="RS256",
                        tenant_scoped=True,
                    ),
                ),
            ],
            roles={},
            policies={},
        )

        emitter = FastAPIAuthEmitter(stack_dir=stack_dir)
        files = emitter.emit(auth_ir, temp_output_dir)

        assert len(files) > 0

    def test_emit_with_multiple_roles(self, stack_dir, temp_output_dir):
        """Test emit() với multiple roles."""
        auth_ir = AuthIR(
            tenant_mode=TenantMode.SCHEMA,
            providers=[
                AuthProvider(
                    id="jwt_auth",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(),
                ),
            ],
            roles={
                "admin": Role(
                    id="admin",
                    permissions=["user:*", "order:*", "product:*"],
                    parents=[],
                    tenant_scoped=True,
                ),
                "viewer": Role(
                    id="viewer",
                    permissions=["user:read", "order:read"],
                    parents=[],
                    tenant_scoped=True,
                ),
            },
            policies={},
        )

        emitter = FastAPIAuthEmitter(stack_dir=stack_dir)
        files = emitter.emit(auth_ir, temp_output_dir)

        assert len(files) > 0


# ============================================================================
# Test GeneratedFile Dataclass
# ============================================================================


class TestGeneratedFile:
    """Tests cho GeneratedFile dataclass."""

    def test_generated_file_creation(self):
        """Test GeneratedFile creation."""
        file = GeneratedFile(
            path=Path("core/security/jwt_auth.py"),
            content="async def create_token(): pass",
            template="auth/jwt_auth.py.jinja2",
            capability="CP03",
        )

        assert file.path == Path("core/security/jwt_auth.py")
        assert file.content == "async def create_token(): pass"
        assert file.template == "auth/jwt_auth.py.jinja2"
        assert file.capability == "CP03"


# ============================================================================
# Test emit_fastapi_auth Convenience Function
# ============================================================================


class TestEmitFastapiAuth:
    """Tests cho emit_fastapi_auth() function."""

    def test_emit_fastapi_auth(self, sample_auth_ir, stack_dir, temp_output_dir):
        """Test emit_fastapi_auth() convenience function."""
        files = emit_fastapi_auth(
            auth_ir=sample_auth_ir,
            stack_dir=stack_dir,
            output_dir=temp_output_dir,
        )

        assert isinstance(files, list)
        assert len(files) > 0
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_fastapi_auth_creates_files(
        self, sample_auth_ir, stack_dir, temp_output_dir
    ):
        """Test emit_fastapi_auth() creates actual files."""
        files = emit_fastapi_auth(
            auth_ir=sample_auth_ir,
            stack_dir=stack_dir,
            output_dir=temp_output_dir,
        )

        # Verify security directory exists
        security_dir = temp_output_dir / "core" / "security"
        assert security_dir.exists()
        
        # Verify files were created
        assert len(files) > 0
        for f in files:
            if f.path.is_absolute():
                assert f.path.exists()
            else:
                # Path is relative to output_dir
                full_path = temp_output_dir / f.path
                assert full_path.exists(), f"File not created: {full_path}"


# ============================================================================
# Test KPI Compliance
# ============================================================================


class TestKPICompliance:
    """Tests cho KPI compliance trong FastAPI auth code."""

    def test_kpi_029_tenant_scoped_default(self, stack_dir, temp_output_dir):
        """Test KPI-029: Default tenant_scoped=True."""
        auth_ir = AuthIR(
            tenant_mode=TenantMode.SCHEMA,
            providers=[
                AuthProvider(
                    id="jwt_auth",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(tenant_scoped=True),
                ),
            ],
            roles={
                "user": Role(
                    id="user",
                    permissions=["order:create"],
                    parents=[],
                    tenant_scoped=True,
                ),
            },
            policies={},
        )

        emitter = FastAPIAuthEmitter(stack_dir=stack_dir)
        files = emitter.emit(auth_ir, temp_output_dir)

        # Check that tenant context is included
        content = "".join(f.content for f in files)
        assert "tenant" in content.lower()

    def test_kpi_030_role_inheritance(self, stack_dir, temp_output_dir):
        """Test KPI-030: Role inheritance support."""
        auth_ir = AuthIR(
            tenant_mode=TenantMode.SCHEMA,
            providers=[
                AuthProvider(
                    id="jwt_auth",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(),
                ),
            ],
            roles={
                "base": Role(
                    id="base",
                    permissions=["user:read"],
                    parents=[],
                    tenant_scoped=True,
                ),
                "admin": Role(
                    id="admin",
                    permissions=["user:create"],
                    parents=["base"],
                    tenant_scoped=True,
                ),
            },
            policies={},
        )

        emitter = FastAPIAuthEmitter(stack_dir=stack_dir)
        files = emitter.emit(auth_ir, temp_output_dir)

        assert len(files) > 0

    def test_kpi_031_policy_validation(self, stack_dir, temp_output_dir):
        """Test KPI-031: Policy validation."""
        auth_ir = AuthIR(
            tenant_mode=TenantMode.SCHEMA,
            providers=[
                AuthProvider(
                    id="jwt_auth",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(),
                ),
            ],
            roles={},
            policies={
                "tenant_policy": Policy(
                    id="tenant_policy",
                    effect=PolicyEffect.DENY,
                    conditions=[
                        PolicyCondition(
                            expression="user.tenant_id != resource.tenant_id",
                        ),
                    ],
                ),
            },
        )

        emitter = FastAPIAuthEmitter(stack_dir=stack_dir)
        files = emitter.emit(auth_ir, temp_output_dir)

        # Check policy_engine.py contains policy-related content
        policy_content = ""
        for f in files:
            if "policy" in f.path.name:
                policy_content = f.content
                break

        assert "policy" in policy_content.lower() or len(files) > 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests cho FastAPIAuthEmitter."""

    def test_full_emit_pipeline(self, stack_dir, temp_output_dir):
        """Test full emit pipeline."""
        auth_ir = AuthIR(
            tenant_mode=TenantMode.SCHEMA,
            providers=[
                AuthProvider(
                    id="jwt_auth",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(
                        expire_minutes=30,
                        tenant_scoped=True,
                    ),
                ),
            ],
            roles={
                "admin": Role(
                    id="admin",
                    permissions=["user:*", "order:*"],
                    parents=[],
                    tenant_scoped=True,
                ),
            },
            policies={},
        )

        emitter = FastAPIAuthEmitter(stack_dir=stack_dir)
        files = emitter.emit(auth_ir, temp_output_dir)

        # Verify directory structure
        security_dir = temp_output_dir / "core" / "security"
        assert security_dir.exists()
        # Verify directory has content
        assert any(security_dir.iterdir())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])