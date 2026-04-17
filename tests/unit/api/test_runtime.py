"""
Unit tests cho Runtime Router
Chuyển đổi từ BDD: tests/features/api/runtime.feature
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


class FakeCLIWrapper:
    def __init__(self, test_success=True, fix_success=True, return_error=None, stdout_output=""):
        self.test_success = test_success
        self.fix_success = fix_success
        self.return_error = return_error
        self.stdout_output = stdout_output
    
    async def runtime_test(self, timeout: int = 30, port: int = 8000, verbose: bool = False) -> dict:
        if self.test_success:
            return {"success": True, "stdout": self.stdout_output or "Tests passed", "stderr": ""}
        return {"success": False, "stdout": "", "stderr": self.return_error or "Test failed"}
    
    async def runtime_fix(self, log_timestamp: str = None, dry_run: bool = False, auto_apply: bool = False, auto_fix_loop: bool = False, test_timeout: int = 30, test_port: int = 8000) -> dict:
        if self.fix_success:
            return {"success": True, "stdout": f"Fixed (dry_run={dry_run}, auto_apply={auto_apply})", "stderr": ""}
        return {"success": False, "stdout": "", "stderr": self.return_error or "Fix failed"}


class FakeI18n:
    def __init__(self):
        self.translations = {
            "vi": {
                "runtime.test_success": "Test runtime thành công",
                "runtime.fix_success": "Đã sửa lỗi runtime thành công",
            },
            "en": {
                "runtime.test_success": "Runtime test passed",
                "runtime.fix_success": "Runtime errors fixed successfully",
            },
        }
        self.default_language = "vi"
    
    def get_language_from_request(self, request) -> str:
        x_lang = request.headers.get("x-lang") or request.headers.get("x-language")
        if x_lang and x_lang in self.translations:
            return x_lang
        lang = request.query_params.get("lang")
        if lang and lang in self.translations:
            return lang
        return self.default_language
    
    def translate(self, key: str, language: str = "vi") -> str:
        if language not in self.translations:
            language = self.default_language
        return self.translations[language].get(key, key)


@pytest.fixture
def mock_i18n():
    fake_i18n = FakeI18n()
    from api.app.routers import runtime
    with patch.object(runtime, 'i18n', fake_i18n):
        yield fake_i18n


@pytest.fixture
def client(mock_i18n):
    from api.app.routers import runtime
    from fastapi import FastAPI
    fake_cli = FakeCLIWrapper(test_success=True, fix_success=True)
    with patch.object(runtime, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(runtime.router)
        yield TestClient(app)


@pytest.fixture
def failing_client(mock_i18n):
    from api.app.routers import runtime
    from fastapi import FastAPI
    fake_cli = FakeCLIWrapper(test_success=False, fix_success=False, return_error="Test error")
    with patch.object(runtime, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(runtime.router)
        yield TestClient(app)


class TestRuntimeTest:
    def test_runtime_test_success(self, client):
        response = client.post("/runtime/test")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["passed"] is True
        assert "logs" in data["data"]
    
    def test_runtime_test_with_custom_timeout(self, client):
        payload = {"timeout": 60}
        response = client.post("/runtime/test", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_runtime_test_with_custom_port(self, client):
        payload = {"port": 9000}
        response = client.post("/runtime/test", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_runtime_test_with_verbose(self, client):
        payload = {"verbose": True}
        response = client.post("/runtime/test", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestRuntimeFix:
    def test_fix_runtime_success(self, client):
        response = client.post("/runtime/fix")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["fixed"] is True
    
    def test_fix_runtime_dry_run(self, client):
        payload = {"dry_run": True}
        response = client.post("/runtime/fix", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["applied"] is False
    
    def test_fix_runtime_auto_apply(self, client):
        payload = {"auto_apply": True}
        response = client.post("/runtime/fix", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["applied"] is True
    
    def test_fix_runtime_auto_fix_loop(self, client):
        payload = {"auto_fix_loop": True}
        response = client.post("/runtime/fix", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_fix_runtime_with_timestamp(self, client):
        payload = {"log_timestamp": "2024-01-15T10:30:00"}
        response = client.post("/runtime/fix", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestRuntimeNegativeCases:
    def test_runtime_test_no_code(self, mock_i18n):
        error_msg = "No applied code found"
        fake_cli = FakeCLIWrapper(test_success=False, return_error=error_msg)
        from api.app.routers import runtime
        from fastapi import FastAPI
        with patch.object(runtime, 'i18n', FakeI18n()):
            with patch.object(runtime, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(runtime.router)
                test_client = TestClient(app)
                response = test_client.post("/runtime/test")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
                assert data["data"]["passed"] is False
    
    def test_runtime_test_invalid_timeout(self, mock_i18n):
        error_msg = "Invalid timeout value"
        fake_cli = FakeCLIWrapper(test_success=False, return_error=error_msg)
        from api.app.routers import runtime
        from fastapi import FastAPI
        with patch.object(runtime, 'i18n', FakeI18n()):
            with patch.object(runtime, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(runtime.router)
                test_client = TestClient(app)
                response = test_client.post("/runtime/test", json={"timeout": -1})
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_runtime_test_invalid_port(self, mock_i18n):
        error_msg = "Invalid port number"
        fake_cli = FakeCLIWrapper(test_success=False, return_error=error_msg)
        from api.app.routers import runtime
        from fastapi import FastAPI
        with patch.object(runtime, 'i18n', FakeI18n()):
            with patch.object(runtime, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(runtime.router)
                test_client = TestClient(app)
                response = test_client.post("/runtime/test", json={"port": 99999})
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_runtime_test_timeout(self, mock_i18n):
        error_msg = "Test timed out after 30 seconds"
        fake_cli = FakeCLIWrapper(test_success=False, return_error=error_msg)
        from api.app.routers import runtime
        from fastapi import FastAPI
        with patch.object(runtime, 'i18n', FakeI18n()):
            with patch.object(runtime, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(runtime.router)
                test_client = TestClient(app)
                response = test_client.post("/runtime/test")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_runtime_test_port_in_use(self, mock_i18n):
        error_msg = "Port 8000 is already in use"
        fake_cli = FakeCLIWrapper(test_success=False, return_error=error_msg)
        from api.app.routers import runtime
        from fastapi import FastAPI
        with patch.object(runtime, 'i18n', FakeI18n()):
            with patch.object(runtime, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(runtime.router)
                test_client = TestClient(app)
                response = test_client.post("/runtime/test")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_fix_runtime_no_errors(self, mock_i18n):
        error_msg = "No errors to fix"
        fake_cli = FakeCLIWrapper(fix_success=False, return_error=error_msg)
        from api.app.routers import runtime
        from fastapi import FastAPI
        with patch.object(runtime, 'i18n', FakeI18n()):
            with patch.object(runtime, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(runtime.router)
                test_client = TestClient(app)
                response = test_client.post("/runtime/fix")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_fix_runtime_invalid_timestamp(self, mock_i18n):
        error_msg = "Timestamp not found"
        fake_cli = FakeCLIWrapper(fix_success=False, return_error=error_msg)
        from api.app.routers import runtime
        from fastapi import FastAPI
        with patch.object(runtime, 'i18n', FakeI18n()):
            with patch.object(runtime, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(runtime.router)
                test_client = TestClient(app)
                response = test_client.post("/runtime/fix", json={"log_timestamp": "invalid"})
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_fix_runtime_cannot_fix(self, mock_i18n):
        error_msg = "Cannot automatically fix this error"
        fake_cli = FakeCLIWrapper(fix_success=False, return_error=error_msg)
        from api.app.routers import runtime
        from fastapi import FastAPI
        with patch.object(runtime, 'i18n', FakeI18n()):
            with patch.object(runtime, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(runtime.router)
                test_client = TestClient(app)
                response = test_client.post("/runtime/fix")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False


class TestRuntimeEdgeCases:
    def test_runtime_test_multiple_tests(self, client):
        response = client.post("/runtime/test")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_runtime_test_some_fail(self, mock_i18n):
        error_msg = "2 tests failed: test_auth, test_database"
        fake_cli = FakeCLIWrapper(test_success=False, return_error=error_msg)
        from api.app.routers import runtime
        from fastapi import FastAPI
        with patch.object(runtime, 'i18n', FakeI18n()):
            with patch.object(runtime, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(runtime.router)
                test_client = TestClient(app)
                response = test_client.post("/runtime/test")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
                assert data["data"]["passed"] is False
    
    def test_fix_runtime_multiple_errors(self, client):
        response = client.post("/runtime/fix")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_fix_runtime_dependent_errors(self, client):
        response = client.post("/runtime/fix")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_fix_runtime_auto_fix_loop_multiple(self, client):
        payload = {"auto_fix_loop": True, "test_timeout": 60}
        response = client.post("/runtime/fix", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_runtime_test_with_warnings(self, mock_i18n):
        fake_cli = FakeCLIWrapper(test_success=True, stdout_output="Tests passed with warnings")
        from api.app.routers import runtime
        from fastapi import FastAPI
        with patch.object(runtime, 'i18n', FakeI18n()):
            with patch.object(runtime, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(runtime.router)
                test_client = TestClient(app)
                response = test_client.post("/runtime/test")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
    
    def test_fix_runtime_dry_run_and_auto_apply(self, client):
        payload = {"dry_run": True, "auto_apply": True}
        response = client.post("/runtime/fix", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["applied"] is True
    
    def test_runtime_test_default_port(self, client):
        response = client.post("/runtime/test")
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_runtime_test_default_timeout(self, client):
        response = client.post("/runtime/test")
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestRuntimeBoundaryCases:
    def test_runtime_test_min_timeout(self, client):
        payload = {"timeout": 1}
        response = client.post("/runtime/test", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_runtime_test_max_timeout(self, client):
        payload = {"timeout": 3600}
        response = client.post("/runtime/test", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_runtime_test_exceeds_timeout(self, mock_i18n):
        error_msg = "Timeout exceeds maximum allowed value"
        fake_cli = FakeCLIWrapper(test_success=False, return_error=error_msg)
        from api.app.routers import runtime
        from fastapi import FastAPI
        with patch.object(runtime, 'i18n', FakeI18n()):
            with patch.object(runtime, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(runtime.router)
                test_client = TestClient(app)
                response = test_client.post("/runtime/test", json={"timeout": 99999})
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_runtime_test_min_port(self, client):
        payload = {"port": 1024}
        response = client.post("/runtime/test", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_runtime_test_max_port(self, client):
        payload = {"port": 65535}
        response = client.post("/runtime/test", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_fix_runtime_max_loop_iterations(self, mock_i18n):
        error_msg = "Maximum loop iterations reached"
        fake_cli = FakeCLIWrapper(fix_success=False, return_error=error_msg)
        from api.app.routers import runtime
        from fastapi import FastAPI
        with patch.object(runtime, 'i18n', FakeI18n()):
            with patch.object(runtime, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(runtime.router)
                test_client = TestClient(app)
                response = test_client.post("/runtime/fix", json={"auto_fix_loop": True})
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False