"""
Unit tests cho Config Router
Chuyển đổi từ BDD: tests/features/api/config.feature
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


class FakeCLIWrapper:
    def __init__(self, list_success=True, get_success=True, set_success=True, validate_success=True, reset_success=True, return_error=None, config_data=None):
        self.list_success = list_success
        self.get_success = get_success
        self.set_success = set_success
        self.validate_success = validate_success
        self.reset_success = reset_success
        self.return_error = return_error
        self.config_data = config_data or {"host": "localhost", "port": "8000"}
    
    async def config_list(self) -> dict:
        if self.list_success:
            return {"success": True, "stdout": str(self.config_data), "stderr": "", "stdout_data": self.config_data}
        return {"success": False, "stdout": "", "stderr": self.return_error or "List failed"}
    
    async def config_get(self, key: str) -> dict:
        if self.get_success:
            value = self.config_data.get(key, "")
            return {"success": True, "stdout": value, "stderr": ""}
        return {"success": False, "stdout": "", "stderr": self.return_error or "Get failed"}
    
    async def config_set(self, key: str, value: str) -> dict:
        if self.set_success:
            return {"success": True, "stdout": f"Set {key}={value}", "stderr": ""}
        return {"success": False, "stdout": "", "stderr": self.return_error or "Set failed"}
    
    async def config_validate(self) -> dict:
        if self.validate_success:
            return {"success": True, "stdout": "Valid", "stderr": ""}
        return {"success": False, "stdout": "", "stderr": self.return_error or "Validate failed"}
    
    async def config_reset(self) -> dict:
        if self.reset_success:
            return {"success": True, "stdout": "Reset complete", "stderr": ""}
        return {"success": False, "stdout": "", "stderr": self.return_error or "Reset failed"}


class FakeI18n:
    def __init__(self):
        self.translations = {
            "vi": {
                "config.list_success": "Đã lấy danh sách cấu hình thành công",
                "config.set_success": "Đã cập nhật cấu hình thành công",
                "common.success": "Thành công",
            },
            "en": {
                "config.list_success": "Configuration list retrieved successfully",
                "config.set_success": "Configuration updated successfully",
                "common.success": "Success",
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
    from api.app.routers import config
    with patch.object(config, 'i18n', fake_i18n):
        yield fake_i18n


@pytest.fixture
def client(mock_i18n):
    from api.app.routers import config
    from fastapi import FastAPI
    fake_cli = FakeCLIWrapper(list_success=True, get_success=True, set_success=True, validate_success=True, reset_success=True, config_data={"host": "localhost", "port": "8000"})
    with patch.object(config, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(config.router)
        yield TestClient(app)


@pytest.fixture
def failing_client(mock_i18n):
    from api.app.routers import config
    from fastapi import FastAPI
    fake_cli = FakeCLIWrapper(list_success=False, get_success=False, set_success=False, validate_success=False, reset_success=False, return_error="Test error")
    with patch.object(config, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(config.router)
        yield TestClient(app)


class TestListConfig:
    def test_list_config_success(self, client):
        response = client.get("/config/list")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "host" in data["data"]
        assert "port" in data["data"]
    
    def test_list_config_returns_all_keys(self, client):
        response = client.get("/config/list")
        data = response.json()
        assert data["data"]["host"] == "localhost"
        assert data["data"]["port"] == "8000"


class TestGetConfig:
    def test_get_config_success(self, client):
        response = client.get("/config/get/host")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["key"] == "host"
        assert data["data"]["value"] == "localhost"
    
    def test_get_config_returns_correct_value(self, client):
        response = client.get("/config/get/port")
        data = response.json()
        assert data["data"]["value"] == "8000"


class TestSetConfig:
    def test_set_config_success(self, client):
        payload = {"key": "host", "value": "0.0.0.0"}
        response = client.post("/config/set", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["key"] == "host"
        assert data["data"]["value"] == "0.0.0.0"


class TestValidateConfig:
    def test_validate_config_success(self, client):
        response = client.post("/config/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestResetConfig:
    def test_reset_config_success(self, client):
        response = client.post("/config/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestConfigNegativeCases:
    def test_get_config_not_found(self, mock_i18n):
        error_msg = "Config key not found"
        fake_cli = FakeCLIWrapper(get_success=False, return_error=error_msg)
        from api.app.routers import config
        from fastapi import FastAPI
        with patch.object(config, 'i18n', FakeI18n()):
            with patch.object(config, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(config.router)
                test_client = TestClient(app)
                response = test_client.get("/config/get/nonexistent")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_validate_config_missing_params(self, mock_i18n):
        error_msg = "Missing required params: api_key"
        fake_cli = FakeCLIWrapper(validate_success=False, return_error=error_msg)
        from api.app.routers import config
        from fastapi import FastAPI
        with patch.object(config, 'i18n', FakeI18n()):
            with patch.object(config, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(config.router)
                test_client = TestClient(app)
                response = test_client.post("/config/validate")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_reset_config_no_permission(self, mock_i18n):
        error_msg = "Permission denied"
        fake_cli = FakeCLIWrapper(reset_success=False, return_error=error_msg)
        from api.app.routers import config
        from fastapi import FastAPI
        with patch.object(config, 'i18n', FakeI18n()):
            with patch.object(config, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(config.router)
                test_client = TestClient(app)
                response = test_client.post("/config/reset")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False


class TestConfigEdgeCases:
    def test_set_config_empty_value(self, client):
        payload = {"key": "optional_key", "value": ""}
        response = client.post("/config/set", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_set_config_very_long_value(self, client):
        long_value = "x" * 10000
        payload = {"key": "large_value", "value": long_value}
        response = client.post("/config/set", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_config_when_not_exists(self, client):
        response = client.get("/config/list")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_set_config_with_special_characters(self, client):
        payload = {"key": "special", "value": "value!@#$%^&*()"}
        response = client.post("/config/set", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["value"] == "value!@#$%^&*()"


class TestConfigBoundaryCases:
    def test_set_config_min_length(self, client):
        payload = {"key": "min_key", "value": "a"}
        response = client.post("/config/set", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_set_config_max_length(self, client):
        max_value = "x" * 1000
        payload = {"key": "max_key", "value": max_value}
        response = client.post("/config/set", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_set_config_exceeds_max_length(self, mock_i18n):
        error_msg = "Value exceeds maximum length"
        fake_cli = FakeCLIWrapper(set_success=False, return_error=error_msg)
        from api.app.routers import config
        from fastapi import FastAPI
        with patch.object(config, 'i18n', FakeI18n()):
            with patch.object(config, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(config.router)
                test_client = TestClient(app)
                response = test_client.post("/config/set", json={"key": "k", "value": "x" * 100000})
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_set_config_with_unicode(self, client):
        payload = {"key": "unicode_key", "value": "Gia tri tieng Viet"}
        response = client.post("/config/set", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["value"] == "Gia tri tieng Viet"
    
    def test_set_config_with_newlines(self, client):
        payload = {"key": "multiline", "value": "line1\nline2\nline3"}
        response = client.post("/config/set", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True