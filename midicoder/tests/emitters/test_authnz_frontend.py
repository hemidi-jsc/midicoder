"""
Tests cho Frontend Authnz Emitters (P2-002-C).

Module mới:
- midicoder/emitters/core/authnz/angular.py - AngularAuthEmitter
- midicoder/emitters/core/authnz/react.py - ReactAuthEmitter

Test coverage:
- AngularAuthEmitter: AuthService, HttpInterceptor, AuthGuard, PermissionDirective
- ReactAuthEmitter: AuthContext, AuthInterceptor, ProtectedRoute
- Integration: emit auth module với authnz config
- Edge cases: empty config, missing fields

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile


class TestAngularAuthEmitter:
    """Tests cho AngularAuthEmitter."""

    def test_angular_auth_emitter_creates_service(self):
        """Test emit Angular AuthService."""
        from midicoder.emitters.core.authnz.angular import AngularAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            auth_config = {
                "provider": "jwt",
                "roles": ["admin", "user"],
                "permissions": ["order:create", "order:read"],
            }

            emitter = AngularAuthEmitter()
            files = emitter.emit(auth_config, output_dir)

            assert len(files) >= 1
            file_contents = "\n".join(f.content for f in files)
            assert "AuthService" in file_contents or "auth" in file_contents.lower()

    def test_angular_auth_emitter_creates_interceptor(self):
        """Test emit Angular HttpInterceptor."""
        from midicoder.emitters.core.authnz.angular import AngularAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            auth_config = {"provider": "jwt", "roles": ["admin"], "permissions": ["*"]}

            emitter = AngularAuthEmitter()
            files = emitter.emit(auth_config, output_dir)

            file_contents = "\n".join(f.content for f in files)
            assert "Interceptor" in file_contents or "intercept" in file_contents.lower()

    def test_angular_auth_emitter_creates_guard(self):
        """Test emit Angular AuthGuard."""
        from midicoder.emitters.core.authnz.angular import AngularAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            auth_config = {"provider": "jwt", "roles": ["admin", "user"], "permissions": ["order:*"]}

            emitter = AngularAuthEmitter()
            files = emitter.emit(auth_config, output_dir)

            file_contents = "\n".join(f.content for f in files)
            assert "Guard" in file_contents or "CanActivate" in file_contents

    def test_angular_auth_emitter_creates_permission_directive(self):
        """Test emit Angular PermissionDirective."""
        from midicoder.emitters.core.authnz.angular import AngularAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            auth_config = {
                "provider": "jwt",
                "roles": ["admin"],
                "permissions": ["order:create", "order:read", "product:read"],
            }

            emitter = AngularAuthEmitter()
            files = emitter.emit(auth_config, output_dir)

            file_contents = "\n".join(f.content for f in files)
            assert "Directive" in file_contents or "permission" in file_contents.lower()

    def test_angular_auth_emitter_empty_config(self):
        """Test Angular auth với empty config."""
        from midicoder.emitters.core.authnz.angular import AngularAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            emitter = AngularAuthEmitter()
            files = emitter.emit({}, output_dir)
            assert len(files) >= 1

    def test_angular_auth_emitter_with_roles(self):
        """Test Angular auth với nhiều roles."""
        from midicoder.emitters.core.authnz.angular import AngularAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            auth_config = {
                "provider": "jwt",
                "roles": ["super_admin", "admin", "manager", "user", "guest"],
                "permissions": ["user:*", "order:*", "product:*"],
            }

            emitter = AngularAuthEmitter()
            files = emitter.emit(auth_config, output_dir)
            file_contents = "\n".join(f.content for f in files)
            assert len(file_contents) > 100


class TestReactAuthEmitter:
    """Tests cho ReactAuthEmitter."""

    def test_react_auth_emitter_creates_context(self):
        """Test emit React AuthContext."""
        from midicoder.emitters.core.authnz.react import ReactAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            auth_config = {
                "provider": "jwt",
                "roles": ["admin", "user"],
                "permissions": ["order:create", "order:read"],
            }

            emitter = ReactAuthEmitter()
            files = emitter.emit(auth_config, output_dir)

            assert len(files) >= 1
            file_contents = "\n".join(f.content for f in files)
            assert "AuthContext" in file_contents or "createContext" in file_contents

    def test_react_auth_emitter_creates_interceptor(self):
        """Test emit React AuthInterceptor."""
        from midicoder.emitters.core.authnz.react import ReactAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            auth_config = {"provider": "jwt", "roles": ["admin"], "permissions": ["*"]}

            emitter = ReactAuthEmitter()
            files = emitter.emit(auth_config, output_dir)

            file_contents = "\n".join(f.content for f in files)
            assert "interceptor" in file_contents.lower() or "prepareHeaders" in file_contents

    def test_react_auth_emitter_creates_protected_route(self):
        """Test emit React ProtectedRoute."""
        from midicoder.emitters.core.authnz.react import ReactAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            auth_config = {"provider": "jwt", "roles": ["admin", "user"], "permissions": ["order:*"]}

            emitter = ReactAuthEmitter()
            files = emitter.emit(auth_config, output_dir)

            file_contents = "\n".join(f.content for f in files)
            assert "ProtectedRoute" in file_contents or "Navigate" in file_contents

    def test_react_auth_emitter_empty_config(self):
        """Test React auth với empty config."""
        from midicoder.emitters.core.authnz.react import ReactAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            emitter = ReactAuthEmitter()
            files = emitter.emit({}, output_dir)
            assert len(files) >= 1

    def test_react_auth_emitter_with_roles(self):
        """Test React auth với nhiều roles."""
        from midicoder.emitters.core.authnz.react import ReactAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            auth_config = {
                "provider": "jwt",
                "roles": ["super_admin", "admin", "manager", "user"],
                "permissions": ["user:*", "order:*"],
            }

            emitter = ReactAuthEmitter()
            files = emitter.emit(auth_config, output_dir)
            file_contents = "\n".join(f.content for f in files)
            assert len(file_contents) > 100


class TestAuthnzIntegration:
    """Integration tests cho frontend authnz."""

    def test_angular_files_structure(self):
        """Test Angular auth files có đúng structure."""
        from midicoder.emitters.core.authnz.angular import AngularAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            auth_config = {"provider": "jwt", "roles": ["admin", "user"], "permissions": ["order:*"]}

            emitter = AngularAuthEmitter()
            files = emitter.emit(auth_config, output_dir)

            file_names = [f.path.name for f in files]
            ts_files = [n for n in file_names if n.endswith('.ts') or n.endswith('.tsx')]
            assert len(ts_files) > 0

    def test_react_files_structure(self):
        """Test React auth files có đúng structure."""
        from midicoder.emitters.core.authnz.react import ReactAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            auth_config = {"provider": "jwt", "roles": ["admin", "user"], "permissions": ["order:*"]}

            emitter = ReactAuthEmitter()
            files = emitter.emit(auth_config, output_dir)

            file_names = [f.path.name for f in files]
            ts_files = [n for n in file_names if n.endswith('.ts') or n.endswith('.tsx')]
            assert len(ts_files) > 0

    def test_generated_files_are_written(self):
        """Test files được ghi ra disk."""
        from midicoder.emitters.core.authnz.angular import AngularAuthEmitter
        from midicoder.emitters.core.authnz.react import ReactAuthEmitter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            auth_config = {"provider": "jwt", "roles": ["admin"], "permissions": ["*"]}

            angular_dir = output_dir / "angular"
            react_dir = output_dir / "react"

            angular_emitter = AngularAuthEmitter()
            angular_files = angular_emitter.emit(auth_config, angular_dir)

            react_emitter = ReactAuthEmitter()
            react_files = react_emitter.emit(auth_config, react_dir)

            # Kiem tra Angular files
            for f in angular_files:
                assert (angular_dir / f.path).exists(), f"Angular file not found: {angular_dir / f.path}"

            # Kiem tra React files
            for f in react_files:
                assert (react_dir / f.path).exists(), f"React file not found: {react_dir / f.path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])