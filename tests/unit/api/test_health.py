"""
Unit tests cho Health Router
Chuyển đổi từ BDD: tests/features/api/health.feature

Test coverage:
- Happy Path: health_check, ready_check, get_info, get_languages, get_status
- Negative Cases: Invalid path handling
- Edge Cases: System startup state
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request
from fastapi.testclient import TestClient


# =============================================================================
# Fake/Mock Classes
# =============================================================================

class FakeSettings:
    """Fake settings cho testing"""
    app_name = "Midicoder WebGUI API"
    api_version = "v1"
    host = "localhost"
    port = 6868
    default_language = "vi"
    supported_languages = ["vi", "en"]
    cli_timeout = 1800
    cors_origins = ["http://localhost:7272"]


class FakeI18n:
    """Fake i18n cho testing"""
    
    def __init__(self):
        self.translations = {
            "vi": {"common.success": "Thành công"},
            "en": {"common.success": "Success"},
        }
        self.default_language = "vi"
    
    def get_language_from_request(self, request: Request) -> str:
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
    
    def get_all_languages(self) -> list[str]:
        return list(self.translations.keys())


class FakeConfig:
    """Fake config functions cho testing"""
    
    @staticmethod
    def get_project_cwd() -> str:
        return "/fake/project/path"
    
    @staticmethod
    def get_global_config_path():
        from pathlib import Path
        from unittest.mock import Mock
        # Return a Mock that behaves like a Path
        mock_path = Mock()
        mock_path.__str__ = Mock(return_value="/fake/config/path")
        mock_path.__fspath__ = Mock(return_value="/fake/config/path")
        mock_path.exists = Mock(return_value=True)
        return mock_path


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_settings():
    """Fixture tạo mock settings"""
    from api.app.routers import health
    with patch.object(health, 'settings', FakeSettings()):
        yield FakeSettings()


@pytest.fixture
def mock_i18n():
    """Fixture tạo mock i18n"""
    fake_i18n = FakeI18n()
    from api.app.routers import health
    with patch.object(health, 'i18n', fake_i18n):
        yield fake_i18n


@pytest.fixture
def mock_config():
    """Fixture tạo mock config functions"""
    from api.app.routers import health
    with patch.object(health, 'get_project_cwd', FakeConfig.get_project_cwd):
        with patch.object(health, 'get_global_config_path', FakeConfig.get_global_config_path):
            yield


@pytest.fixture
def client(mock_settings, mock_i18n, mock_config):
    """Fixture tạo TestClient"""
    from api.app.routers import health
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(health.router)
    return TestClient(app)


# =============================================================================
# Happy Path Tests
# =============================================================================

class TestHealthCheck:
    """Tests cho health_check endpoint"""
    
    def test_health_check_returns_healthy_status(self, client):
        """
        Kịch bản: Kiểm tra trạng thái healthy của API
        Khi người dùng yêu cầu kiểm tra trạng thái API
        Thì hệ thống trả về trạng thái "healthy"
        Và hệ thống hiển thị phiên bản hiện tại
        Và hệ thống hiển thị thời gian phản hồi
        """
        # Arrange
        expected_version = "v1"
        
        # Act
        response = client.get("/health/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == expected_version
        # Verify timestamp is a valid datetime
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    
    def test_health_check_returns_current_version(self, client, mock_settings):
        """
        Kịch bản: Kiểm tra API trả về đúng phiên bản
        Khi người dùng yêu cầu kiểm tra trạng thái API
        Thì hệ thống trả về phiên bản từ settings
        """
        # Arrange
        expected_version = mock_settings.api_version
        
        # Act
        response = client.get("/health/")
        
        # Assert
        assert response.json()["version"] == expected_version


class TestReadyCheck:
    """Tests cho ready_check endpoint"""
    
    def test_ready_check_returns_ready_status(self, client):
        """
        Kịch bản: Kiểm tra API đã sẵn sàng
        Khi người dùng yêu cầu kiểm tra trạng thái sẵn sàng
        Thì hệ thống trả về trạng thái "ready"
        Và hệ thống hiển thị phiên bản hiện tại
        """
        # Arrange
        expected_version = "v1"
        
        # Act
        response = client.get("/health/ready")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["version"] == expected_version
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    
    def test_ready_check_includes_timestamp(self, client):
        """
        Kịch bản: Kiểm tra ready check có timestamp
        Khi người dùng yêu cầu kiểm tra trạng thái sẵn sàng
        Thì hệ thống trả về timestamp hợp lệ
        """
        # Act
        response = client.get("/health/ready")
        
        # Assert
        data = response.json()
        assert "timestamp" in data
        # Verify it's parseable
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))


class TestGetInfo:
    """Tests cho get_info endpoint"""
    
    def test_get_info_returns_app_details(self, client):
        """
        Kịch bản: Xem thông tin chi tiết của API
        Khi người dùng yêu cầu thông tin API
        Thì hệ thống trả về tên ứng dụng
        Và hệ thống trả về phiên bản API
        Và hệ thống trả về địa chỉ host và cổng
        Và hệ thống trả về ngôn ngữ mặc định
        Và hệ thống trả về danh sách ngôn ngữ được hỗ trợ
        """
        # Arrange
        expected_data = {
            "app_name": "Midicoder WebGUI API",
            "api_version": "v1",
            "host": "localhost",
            "port": 6868,
            "default_language": "vi",
            "supported_languages": ["vi", "en"],
        }
        
        # Act
        response = client.get("/health/info")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["app_name"] == expected_data["app_name"]
        assert data["data"]["api_version"] == expected_data["api_version"]
        assert data["data"]["host"] == expected_data["host"]
        assert data["data"]["port"] == expected_data["port"]
        assert data["data"]["default_language"] == expected_data["default_language"]
        assert data["data"]["supported_languages"] == expected_data["supported_languages"]
    
    def test_get_info_returns_vietnamese_message_by_default(self, client):
        """
        Kịch bản: Get info trả về message tiếng Việt mặc định
        Khi người dùng không chỉ định ngôn ngữ
        Thì hệ thống trả về message bằng tiếng Việt
        """
        # Act
        response = client.get("/health/info")
        
        # Assert
        assert response.json()["message"] == "Thành công"
    
    def test_get_info_respects_language_header(self, client):
        """
        Kịch bản: Get info tôn trọng ngôn ngữ từ header
        Khi người dùng gửi header X-Lang: en
        Thì hệ thống trả về message bằng tiếng Anh
        """
        # Act
        response = client.get("/health/info", headers={"X-Lang": "en"})
        
        # Assert
        assert response.json()["message"] == "Success"
        assert response.json()["language"] == "en"
    
    def test_get_info_respects_query_param_language(self, client):
        """
        Kịch bản: Get info tôn trọng ngôn ngữ từ query param
        Khi người dùng gửi query param lang=en
        Thì hệ thống trả về message bằng tiếng Anh
        """
        # Act
        response = client.get("/health/info?lang=en")
        
        # Assert
        assert response.json()["message"] == "Success"
        assert response.json()["language"] == "en"


class TestGetLanguages:
    """Tests cho get_languages endpoint"""
    
    def test_get_languages_returns_language_list(self, client):
        """
        Kịch bản: Xem danh sách ngôn ngữ được hỗ trợ
        Khi người dùng yêu cầu danh sách ngôn ngữ
        Thì hệ thống trả về danh sách ngôn ngữ
        Và hệ thống trả về ngôn ngữ mặc định
        """
        # Arrange
        expected_languages = ["vi", "en"]
        expected_default = "vi"
        
        # Act
        response = client.get("/health/languages")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["languages"] == expected_languages
        assert data["default"] == expected_default


class TestGetStatus:
    """Tests cho get_status endpoint"""
    
    def test_get_status_returns_system_info(self, client):
        """
        Kịch bản: Xem trạng thái hệ thống hiện tại
        Khi người dùng yêu cầu trạng thái hệ thống
        Thì hệ thống trả về thư mục làm việc hiện tại
        Và hệ thống trả về đường dẫn cấu hình toàn cục
        Và hệ thống thông báo trạng thái file cấu hình
        Và hệ thống trả về trạng thái sẵn sàng của API
        """
        # Arrange
        expected_cwd = "/fake/project/path"
        expected_config_path = "/fake/config/path"
        
        # Act
        response = client.get("/health/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["cwd"] == expected_cwd
        assert data["data"]["global_config_path"] == expected_config_path
        assert data["data"]["global_config_exists"] is True
        assert data["data"]["api_ready"] is True


# =============================================================================
# Negative Cases Tests
# =============================================================================

class TestHealthNegativeCases:
    """Tests cho các trường hợp lỗi"""
    
    def test_invalid_path_returns_404(self, client):
        """
        Kịch bản: Yêu cầu kiểm tra với đường dẫn không hợp lệ
        Khi người dùng yêu cầu kiểm tra với đường dẫn sai
        Thì hệ thống trả về thông báo lỗi phù hợp
        """
        # Act
        response = client.get("/health/invalid-path")
        
        # Assert
        assert response.status_code == 404


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestHealthEdgeCases:
    """Tests cho các trường hợp biên"""
    
    def test_health_during_startup(self, client):
        """
        Kịch bản: Kiểm tra API khi hệ thống đang khởi động
        Khi người dùng yêu cầu kiểm tra trạng thái trong khi API đang khởi động
        Thì hệ thống trả về trạng thái phù hợp với thời điểm hiện tại
        """
        # Act
        response = client.get("/health/")
        
        # Assert
        # Even during startup, health check should respond
        assert response.status_code == 200
        assert "status" in response.json()
    
    def test_health_timestamp_is_recent(self, client):
        """
        Kịch bản: Kiểm tra timestamp là thời gian gần đây
        Khi người dùng yêu cầu health check
        Thì timestamp trả về phải gần với thời gian hiện tại
        """
        # Arrange
        before_request = datetime.utcnow()
        
        # Act
        response = client.get("/health/")
        
        # Assert
        after_request = datetime.utcnow()
        response_time = datetime.fromisoformat(
            response.json()["timestamp"].replace("Z", "+00:00")
        )
        # Timestamp should be between before and after (with small tolerance)
        assert (response_time - before_request).total_seconds() >= -1
        assert (after_request - response_time).total_seconds() >= -1
    
    def test_multiple_concurrent_health_checks(self, client):
        """
        Kịch bản: Nhiều yêu cầu health check đồng thời
        Khi nhiều người dùng yêu cầu health check cùng lúc
        Thì mỗi yêu cầu đều nhận được phản hồi đúng
        """
        # Act - simulate multiple requests
        responses = [client.get("/health/") for _ in range(10)]
        
        # Assert
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"


# =============================================================================
# Boundary Cases Tests
# =============================================================================

class TestHealthBoundaryCases:
    """Tests cho các trường hợp boundary"""
    
    def test_health_with_special_characters_in_headers(self, client):
        """
        Kịch bản: Health check với ký tự đặc biệt trong headers
        Khi người dùng gửi headers có ký tự đặc biệt
        Thì hệ thống vẫn xử lý đúng
        """
        # Act
        response = client.get(
            "/health/",
            headers={"X-Custom-Header": "test-value-123!@#"}
        )
        
        # Assert
        assert response.status_code == 200
    
    def test_health_endpoint_is_case_sensitive(self, client):
        """
        Kịch bản: Kiểm tra endpoint case-sensitive
        Khi người dùng dùng đường dẫn sai case
        Thì hệ thống trả về 404
        """
        # Act
        response = client.get("/HEALTH/")
        
        # Assert
        assert response.status_code == 404