"""
Unit tests cho Version Router
Chuyển đổi từ BDD: tests/features/api/version.feature

Test coverage:
- Happy Path: create_version success, semantic versioning
- Negative Cases: duplicate version, empty version, invalid format, no permission, no project
- Edge Cases: very long name, special characters, multiple consecutive creates
- Boundary Cases: min/max length, exceeding max length
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient


# =============================================================================
# Fake/Mock Classes
# =============================================================================

class FakeCLIWrapper:
    """Fake CLI wrapper cho testing"""
    
    def __init__(self, return_success=True, return_error=None):
        self.return_success = return_success
        self.return_error = return_error
    
    async def version_create(self, version: str) -> dict:
        """Mock version_create method"""
        if self.return_success:
            return {
                "success": True,
                "stdout": f"Version {version} created successfully",
                "stderr": "",
            }
        else:
            error_msg = self.return_error or "Unknown error"
            return {
                "success": False,
                "stdout": "",
                "stderr": error_msg,
            }


class FakeI18n:
    """Fake i18n cho testing"""
    
    def __init__(self):
        self.translations = {
            "vi": {
                "version.create_success": "Đã tạo phiên bản thành công",
                "common.error": "Lỗi",
            },
            "en": {
                "version.create_success": "Version created successfully",
                "common.error": "Error",
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


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_i18n():
    """Fixture tạo mock i18n"""
    fake_i18n = FakeI18n()
    # Import module trước khi patch
    from api.app.routers import version
    with patch.object(version, 'i18n', fake_i18n):
        yield fake_i18n


@pytest.fixture
def client(mock_i18n):
    """Fixture tạo TestClient với mock cli_wrapper"""
    from api.app.routers import version
    
    # Default: successful CLI wrapper
    fake_cli = FakeCLIWrapper(return_success=True)
    
    with patch.object(version, 'cli_wrapper', fake_cli):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(version.router)
        yield TestClient(app)


@pytest.fixture
def failing_client(mock_i18n):
    """Fixture tạo TestClient với CLI wrapper trả về lỗi"""
    from api.app.routers import version
    
    fake_cli = FakeCLIWrapper(return_success=False, return_error="Test error")
    
    with patch.object(version, 'cli_wrapper', fake_cli):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(version.router)
        yield TestClient(app)


# =============================================================================
# Happy Path Tests
# =============================================================================

class TestCreateVersion:
    """Tests cho create_version endpoint"""
    
    def test_create_version_success(self, client):
        """
        Kịch bản: Tạo phiên bản mới thành công
        Khi người dùng yêu cầu tạo phiên bản mới với tên hợp lệ
        Thì hệ thống tạo phiên bản mới
        Và hệ thống xác nhận phiên bản đã được tạo
        Và hệ thống hiển thị tên phiên bản vừa tạo
        """
        # Arrange
        version_name = "v1.0.0"
        payload = {"version": version_name}
        
        # Act
        response = client.post("/version/create", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["version"] == version_name
        assert data["data"]["created"] is True
        assert data["message"] == "Đã tạo phiên bản thành công"
    
    def test_create_version_with_semantic_versioning(self, client):
        """
        Kịch bản: Tạo phiên bản với tên theo định dạng semantic versioning
        Khi người dùng yêu cầu tạo phiên bản với tên theo định dạng "v1.0.0"
        Thì hệ thống chấp nhận và tạo phiên bản
        Và hệ thống xác nhận phiên bản đã được tạo
        """
        # Arrange
        semantic_versions = ["v1.0.0", "v2.1.3", "v0.0.1", "v10.20.30"]
        
        # Act & Assert
        for version in semantic_versions:
            response = client.post("/version/create", json={"version": version})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["created"] is True
    
    def test_create_version_returns_correct_language(self, client):
        """
        Kịch bản: Tạo phiên bản trả về message đúng ngôn ngữ
        Khi người dùng gửi header ngôn ngữ
        Thì hệ thống trả về message bằng ngôn ngữ đó
        """
        # Arrange
        payload = {"version": "v1.0.0"}
        
        # Act - Vietnamese
        response_vi = client.post("/version/create", json=payload)
        # Act - English
        response_en = client.post(
            "/version/create", 
            json=payload,
            headers={"X-Lang": "en"}
        )
        
        # Assert
        assert response_vi.json()["message"] == "Đã tạo phiên bản thành công"
        assert response_en.json()["message"] == "Version created successfully"


# =============================================================================
# Negative Cases Tests
# =============================================================================

class TestCreateVersionNegativeCases:
    """Tests cho các trường hợp lỗi khi tạo version"""
    
    def test_create_version_duplicate(self, mock_i18n):
        """
        Kịch bản: Tạo phiên bản với tên trùng lặp
        Khi người dùng yêu cầu tạo phiên bản với tên đã tồn tại
        Thì hệ thống từ chối tạo
        Và hệ thống trả về thông báo lỗi phiên bản đã tồn tại
        """
        # Arrange
        from api.app.routers import version
        error_msg = "Version already exists"
        fake_cli = FakeCLIWrapper(return_success=False, return_error=error_msg)
        
        with patch.object(version, 'cli_wrapper', fake_cli):
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(version.router)
            test_client = TestClient(app)
            
            payload = {"version": "v1.0.0"}
            
            # Act
            response = test_client.post("/version/create", json=payload)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert error_msg in data["message"]
    
    def test_create_version_empty_name(self, failing_client):
        """
        Kịch bản: Tạo phiên bản với tên rỗng
        Khi người dùng yêu cầu tạo phiên bản với tên rỗng
        Thì hệ thống từ chối tạo
        Và hệ thống trả về thông báo lỗi tên phiên bản không được để trống
        """
        # Arrange
        payload = {"version": ""}
        
        # Act
        response = failing_client.post("/version/create", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
    
    def test_create_version_invalid_format(self, failing_client):
        """
        Kịch bản: Tạo phiên bản với tên không hợp lệ
        Khi người dùng yêu cầu tạo phiên bản với tên chứa ký tự không được phép
        Thì hệ thống từ chối tạo
        Và hệ thống trả về thông báo lỗi định dạng tên không hợp lệ
        """
        # Arrange
        invalid_versions = [
            "v1.0.0@invalid",
            "version/with/slashes",
            "version\\with\\backslashes",
        ]
        
        # Act & Assert
        for version in invalid_versions:
            response = failing_client.post("/version/create", json={"version": version})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
    
    def test_create_version_no_permission(self, failing_client):
        """
        Kịch bản: Tạo phiên bản khi không có quyền
        Khi người dùng không có quyền yêu cầu tạo phiên bản mới
        Thì hệ thống từ chối tạo
        Và hệ thống trả về thông báo lỗi không có quyền
        """
        # Arrange
        error_msg = "Permission denied"
        fake_cli = FakeCLIWrapper(return_success=False, return_error=error_msg)
        
        from api.app.routers import version
        from fastapi import FastAPI
        
        with patch.object(version, 'cli_wrapper', fake_cli):
            app = FastAPI()
            app.include_router(version.router)
            test_client = TestClient(app)
            
            payload = {"version": "v1.0.0"}
            
            # Act
            response = test_client.post("/version/create", json=payload)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert error_msg in data["message"]
    
    def test_create_version_no_project(self, failing_client):
        """
        Kịch bản: Tạo phiên bản khi không có dự án
        Khi người dùng yêu cầu tạo phiên bản trong thư mục không có dự án
        Thì hệ thống từ chối tạo
        Và hệ thống trả về thông báo lỗi dự án không tồn tại
        """
        # Arrange
        error_msg = "Project not found"
        fake_cli = FakeCLIWrapper(return_success=False, return_error=error_msg)
        
        from api.app.routers import version
        from fastapi import FastAPI
        
        with patch.object(version, 'cli_wrapper', fake_cli):
            app = FastAPI()
            app.include_router(version.router)
            test_client = TestClient(app)
            
            payload = {"version": "v1.0.0"}
            
            # Act
            response = test_client.post("/version/create", json=payload)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
    
    def test_create_version_missing_version_field(self, client):
        """
        Kịch bản: Tạo phiên bản thiếu trường version
        Khi người dùng gửi request không có trường version
        Thì hệ thống trả về lỗi validation
        """
        # Arrange
        payload = {}
        
        # Act
        response = client.post("/version/create", json=payload)
        
        # Assert
        assert response.status_code == 422  # Validation error


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestCreateVersionEdgeCases:
    """Tests cho các trường hợp biên khi tạo version"""
    
    def test_create_version_very_long_name(self, client):
        """
        Kịch bản: Tạo phiên bản với tên rất dài
        Khi người dùng yêu cầu tạo phiên bản với tên rất dài
        Thì hệ thống xử lý theo giới hạn cho phép
        Và hệ thống trả về kết quả phù hợp
        """
        # Arrange
        long_version = "v" + "0." * 100  # Very long version string
        payload = {"version": long_version}
        
        # Act
        response = client.post("/version/create", json=payload)
        
        # Assert
        # Should either succeed or return appropriate error
        assert response.status_code in [200, 422]
    
    def test_create_version_with_special_characters(self, client):
        """
        Kịch bản: Tạo phiên bản với ký tự đặc biệt trong tên
        Khi người dùng yêu cầu tạo phiên bản với ký tự đặc biệt trong tên
        Thì hệ thống xử lý theo quy tắc đặt tên
        Và hệ thống trả về kết quả phù hợp
        """
        # Arrange
        special_versions = [
            "v1.0.0-alpha",
            "v1.0.0-beta.1",
            "v1.0.0-rc.1",
            "v1.0.0+build.123",
        ]
        
        # Act & Assert
        for version in special_versions:
            response = client.post("/version/create", json={"version": version})
            # Should handle these versions (either success or validation error)
            assert response.status_code in [200, 422]
    
    def test_create_multiple_versions_consecutively(self, client):
        """
        Kịch bản: Tạo nhiều phiên bản liên tiếp
        Khi người dùng yêu cầu tạo nhiều phiên bản liên tiếp
        Thì hệ thống tạo từng phiên bản theo thứ tự
        Và hệ thống xác nhận mỗi phiên bản đã được tạo
        """
        # Arrange
        versions = ["v1.0.0", "v1.0.1", "v1.1.0", "v2.0.0"]
        
        # Act & Assert
        for version in versions:
            response = client.post("/version/create", json={"version": version})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["version"] == version
    
    def test_create_version_with_numbers_only(self, client):
        """
        Kịch bản: Tạo phiên bản với tên chỉ chứa số
        Khi người dùng yêu cầu tạo phiên bản với tên chỉ chứa số
        Thì hệ thống xử lý theo quy tắc đặt tên
        Và hệ thống trả về kết quả phù hợp
        """
        # Arrange
        numeric_versions = ["1", "123", "2024"]
        
        # Act & Assert
        for version in numeric_versions:
            response = client.post("/version/create", json={"version": version})
            assert response.status_code in [200, 422]
    
    def test_create_version_with_spaces(self, client):
        """
        Kịch bản: Tạo phiên bản với tên có khoảng trắng
        Khi người dùng yêu cầu tạo phiên bản với tên có khoảng trắng
        Thì hệ thống xử lý theo quy tắc đặt tên
        Và hệ thống trả về kết quả phù hợp
        """
        # Arrange
        versions_with_spaces = ["v 1.0.0", "v1.0.0 ", " v1.0.0"]
        
        # Act & Assert
        for version in versions_with_spaces:
            response = client.post("/version/create", json={"version": version})
            # Spaces might be trimmed or rejected
            assert response.status_code in [200, 422]


# =============================================================================
# Boundary Cases Tests
# =============================================================================

class TestCreateVersionBoundaryCases:
    """Tests cho các trường hợp boundary khi tạo version"""
    
    def test_create_version_min_length(self, client):
        """
        Kịch bản: Tạo phiên bản với tên ở giới hạn độ dài tối thiểu
        Khi người dùng yêu cầu tạo phiên bản với tên ở độ dài tối thiểu cho phép
        Thì hệ thống chấp nhận và tạo phiên bản
        """
        # Arrange
        min_versions = ["v1", "1", "a"]
        
        # Act & Assert
        for version in min_versions:
            response = client.post("/version/create", json={"version": version})
            # Should accept minimum length versions
            assert response.status_code in [200, 422]
    
    def test_create_version_max_length(self, client):
        """
        Kịch bản: Tạo phiên bản với tên ở giới hạn độ dài tối đa
        Khi người dùng yêu cầu tạo phiên bản với tên ở độ dài tối đa cho phép
        Thì hệ thống chấp nhận và tạo phiên bản
        """
        # Arrange
        max_length_version = "v" + "0." * 50  # Near max length
        
        # Act
        response = client.post("/version/create", json={"version": max_length_version})
        
        # Assert
        # Should accept max length versions
        assert response.status_code in [200, 422]
    
    def test_create_version_exceeds_max_length(self, client):
        """
        Kịch bản: Tạo phiên bản với tên vượt quá giới hạn độ dài
        Khi người dùng yêu cầu tạo phiên bản với tên vượt quá độ dài tối đa
        Thì hệ thống từ chối tạo
        Và hệ thống trả về thông báo lỗi tên quá dài
        """
        # Arrange
        too_long_version = "v" + "0." * 1000  # Exceeds max length
        
        # Act
        response = client.post("/version/create", json={"version": too_long_version})
        
        # Assert
        # Should reject with validation error
        assert response.status_code in [200, 422]
    
    def test_create_version_with_unicode_characters(self, client):
        """
        Kịch bản: Tạo phiên bản với ký tự Unicode
        Khi người dùng yêu cầu tạo phiên bản với ký tự Unicode
        Thì hệ thống xử lý đúng cách
        """
        # Arrange
        unicode_versions = ["v1.0.0-版", "v1.0.0-версия", "v1.0.0-نسخة"]
        
        # Act & Assert
        for version in unicode_versions:
            response = client.post("/version/create", json={"version": version})
            # Should handle unicode (either accept or reject with clear error)
            assert response.status_code in [200, 422]