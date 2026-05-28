"""
Integration Test cho CP03 Auth Framework.

Test full flow: YAML -> AuthIR -> 4 stack code files -> verify output.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import yaml

from midicoder.packs.cp_full_auth.parser import AuthParser
from midicoder.packs.cp_full_auth.fastapi import FastAPIAuthEmitter
from midicoder.packs.cp_full_auth.nestjs import NestJSEmitter
from midicoder.packs.cp_full_auth.angular import AngularEmitter
from midicoder.packs.cp_full_auth.react import ReactEmitter


@pytest.fixture
def auth_dsl_file():
    """Tao YAML DSL file cho Auth."""
    tmp = Path(tempfile.mkdtemp())
    dsl_file = tmp / "auth.yml"
    dsl_file.write_text(yaml.dump({
        "authentication": {
            "providers": [
                {
                    "id": "jwt_auth",
                    "type": "jwt",
                    "config": {
                        "expire_minutes": 30,
                        "refresh_expire_days": 7,
                        "algorithm": "HS256",
                        "tenant_scoped": True,
                    },
                },
                {
                    "id": "google_oauth2",
                    "type": "oauth2",
                    "config": {
                        "authorization_url": "https://accounts.google.com/o/oauth2/auth",
                        "token_url": "https://oauth2.googleapis.com/token",
                        "scopes": ["email", "profile"],
                    },
                },
            ],
            "session": {
                "cookie_name": "session_id",
                "max_age_minutes": 480,
                "secure": True,
                "http_only": True,
                "same_site": "lax",
            },
        },
        "authorization": {
            "permissions": [
                {"id": "user:create", "description": "Tao user moi"},
                {"id": "user:read", "description": "Doc thong tin user"},
                {"id": "user:update", "description": "Cap nhat user"},
                {"id": "user:delete", "description": "Xoa user"},
                {"id": "order:*", "description": "Tat ca actions tren order"},
            ],
        },
    }), encoding="utf-8")
    yield dsl_file
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def stack_dir():
    """Tao template directory."""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "auth").mkdir()
    return tmp


@pytest.fixture
def output_dir():
    """Tao output directory."""
    tmp = Path(tempfile.mkdtemp())
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


class TestAuthIntegration:
    """Integration tests cho CP03 Auth Framework."""

    def test_parse_yaml_to_auth_ir(self, auth_dsl_file):
        """Test: Parse YAML DSL -> AuthIR."""
        parser = AuthParser(auth_dsl_file)
        auth_ir = parser.parse()
        assert len(auth_ir.providers) == 2
        jwt_provider = auth_ir.get_jwt_provider()
        assert jwt_provider is not None
        assert jwt_provider.id == "jwt_auth"
        assert jwt_provider.config.expire_minutes == 30
        oauth2 = auth_ir.get_oauth2_providers()
        assert len(oauth2) == 1
        assert auth_ir.session.cookie_name == "session_id"
        perms = auth_ir.get_all_permission_ids()
        assert len(perms) == 5

    def test_full_flow_fastapi(self, auth_dsl_file, stack_dir, output_dir):
        """Test: YAML -> AuthIR -> FastAPI code."""
        auth_ir = AuthParser(auth_dsl_file).parse()
        files = FastAPIAuthEmitter(stack_dir).emit(auth_ir, output_dir)
        assert len(files) >= 3
        assert (output_dir / "core" / "security" / "jwt_auth.py").exists()
        assert (output_dir / "core" / "security" / "session.py").exists()

    def test_full_flow_nestjs(self, auth_dsl_file, stack_dir, output_dir):
        """Test: YAML -> AuthIR -> NestJS code."""
        auth_ir = AuthParser(auth_dsl_file).parse()
        files = NestJSEmitter(stack_dir).emit(auth_ir, output_dir)
        assert len(files) >= 4
        assert (output_dir / "src" / "auth" / "auth.module.ts").exists()

    def test_full_flow_angular(self, auth_dsl_file, stack_dir, output_dir):
        """Test: YAML -> AuthIR -> Angular code."""
        auth_ir = AuthParser(auth_dsl_file).parse()
        files = AngularEmitter(stack_dir).emit(auth_ir, output_dir)
        assert len(files) >= 4
        assert (output_dir / "src" / "app" / "core" / "auth" / "auth.service.ts").exists()

    def test_full_flow_react(self, auth_dsl_file, stack_dir, output_dir):
        """Test: YAML -> AuthIR -> React code."""
        auth_ir = AuthParser(auth_dsl_file).parse()
        files = ReactEmitter(stack_dir).emit(auth_ir, output_dir)
        assert len(files) >= 4
        assert (output_dir / "src" / "auth" / "AuthContext.tsx").exists()

    def test_full_flow_all_stacks(self, auth_dsl_file, stack_dir, output_dir):
        """Test: YAML -> AuthIR -> 4 stack code files."""
        auth_ir = AuthParser(auth_dsl_file).parse()
        fastapi_files = FastAPIAuthEmitter(stack_dir).emit(auth_ir, output_dir / "fastapi")
        nestjs_files = NestJSEmitter(stack_dir).emit(auth_ir, output_dir / "nestjs")
        angular_files = AngularEmitter(stack_dir).emit(auth_ir, output_dir / "angular")
        react_files = ReactEmitter(stack_dir).emit(auth_ir, output_dir / "react")
        total = len(fastapi_files) + len(nestjs_files) + len(angular_files) + len(react_files)
        assert total >= 15

    def test_output_python_valid_syntax(self, auth_dsl_file, stack_dir, output_dir):
        """Test: Output Python files co valid syntax."""
        auth_ir = AuthParser(auth_dsl_file).parse()
        files = FastAPIAuthEmitter(stack_dir).emit(auth_ir, output_dir)
        for f in files:
            if f.path.suffix == ".py":
                compile(f.content, str(f.path), "exec")

    def test_pack_self_contained(self):
        """Test: Pack khong import tu CP01, CP02, hay authnz/."""
        import importlib
        auth_module = importlib.import_module("midicoder.packs.cp_full_auth")
        models = importlib.import_module("midicoder.packs.cp_full_auth.models")
        parser = importlib.import_module("midicoder.packs.cp_full_auth.parser")
        for mod in [auth_module, models, parser]:
            source = Path(mod.__file__).read_text(encoding="utf-8")
            assert "authnz" not in source.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])