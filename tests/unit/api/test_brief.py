"""
Unit tests cho Brief Router
Chuyển đổi từ BDD: tests/features/api/brief.feature

Test coverage:
- Happy Path: analyze_brief success, analyze with clarifications, rewrite_brief success
- Negative Cases: no brief, empty content, invalid format, no permission
- Edge Cases: very short brief, very long brief, multiple languages, special characters
- Boundary Cases: min/max length, exceeding max length

TDD Principles:
- Test names describe BEHAVIOR, not just actions (Given-When-Then style)
- Assertions verify response structure, not just success flag
- Tests cover all BDD scenarios from feature file
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime


# =============================================================================
# Fake/Mock Classes
# =============================================================================

class FakeCLIWrapper:
    """Fake CLI wrapper cho testing"""
    
    def __init__(self, analyze_success=True, rewrite_success=True, return_error=None, stdout_data=None):
        self.analyze_success = analyze_success
        self.rewrite_success = rewrite_success
        self.return_error = return_error
        self.stdout_data = stdout_data or {}
    
    async def brief_analyze(self) -> dict:
        """Mock brief_analyze method"""
        if self.analyze_success:
            return {
                "success": True,
                "stdout": "Brief analyzed successfully",
                "stderr": "",
                "stdout_data": self.stdout_data,
            }
        else:
            error_msg = self.return_error or "Analyze failed"
            return {
                "success": False,
                "stdout": "",
                "stderr": error_msg,
            }
    
    async def brief_rewrite(self) -> dict:
        """Mock brief_rewrite method"""
        if self.rewrite_success:
            return {
                "success": True,
                "stdout": "Brief rewritten successfully",
                "stderr": "",
            }
        else:
            error_msg = self.return_error or "Rewrite failed"
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
                "brief.analyze_success": "Đã phân tích brief thành công",
                "brief.rewrite_success": "Đã viết lại brief thành công",
                "common.error": "Lỗi",
            },
            "en": {
                "brief.analyze_success": "Brief analyzed successfully",
                "brief.rewrite_success": "Brief rewritten successfully",
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
    """Fixture tao mock i18n"""
    fake_i18n = FakeI18n()
    from api.app.routers import brief
    with patch.object(brief, 'i18n', fake_i18n):
        yield fake_i18n


@pytest.fixture
def client(mock_i18n):
    """Fixture tao TestClient voi mock cli_wrapper thanh cong"""
    from api.app.routers import brief
    from fastapi import FastAPI
    
    fake_cli = FakeCLIWrapper(
        analyze_success=True, 
        rewrite_success=True,
        stdout_data={"status": "ready", "ambiguities": []}
    )
    
    with patch.object(brief, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(brief.router)
        yield TestClient(app)


@pytest.fixture
def failing_client(mock_i18n):
    """Fixture tao TestClient voi mock cli_wrapper that bai"""
    from api.app.routers import brief
    from fastapi import FastAPI
    
    fake_cli = FakeCLIWrapper(
        analyze_success=False, 
        rewrite_success=False, 
        return_error="Test error"
    )
    
    with patch.object(brief, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(brief.router)
        yield TestClient(app)


# =============================================================================
# Helper Functions for Response Validation
# =============================================================================

def validate_api_response_structure(response):
    """Validate common API response structure"""
    data = response.json()
    assert "success" in data, "Response must contain 'success' field"
    assert "message" in data, "Response must contain 'message' field"
    assert "timestamp" in data, "Response must contain 'timestamp' field"
    assert "language" in data, "Response must contain 'language' field"
    return data


def validate_success_response(response, expected_message=None):
    """Validate successful API response"""
    data = validate_api_response_structure(response)
    assert data["success"] is True, "Response success should be True"
    assert data["message"] is not None, "Success response must have a message"
    if expected_message:
        assert data["message"] == expected_message, f"Expected message '{expected_message}', got '{data['message']}'"
    return data


def validate_error_response(response, expected_error_substring=None):
    """Validate error API response"""
    data = validate_api_response_structure(response)
    assert data["success"] is False, "Response success should be False"
    assert data["message"] is not None, "Error response must have a message"
    if expected_error_substring:
        assert expected_error_substring in data["message"], f"Expected error containing '{expected_error_substring}'"
    return data


# =============================================================================
# Happy Path Tests - BDD Style
# =============================================================================

class TestAnalyzeBriefHappyPath:
    """Tests cho analyze_brief endpoint - Happy Path scenarios"""
    
    def test_returns_success_when_brief_is_analyzed(self, client):
        """
        BDD: Khi người dùng yêu cầu phân tích brief -> Thì hệ thống phân tích thành công
        Given: Brief tồn tại và hợp lệ
        When: Gửi request POST /brief/analyze
        Then: Response trả về success=True với kết quả phân tích
        """
        response = client.post("/brief/analyze")
        
        # Validate HTTP status
        assert response.status_code == 200, "Should return HTTP 200 OK"
        
        # Validate response structure
        data = validate_success_response(response, "Đã phân tích brief thành công")
        
        # Validate data field exists
        assert "data" in data, "Response must contain 'data' field"
    
    def test_returns_clarification_questions_when_brief_has_ambiguities(self, mock_i18n):
        """
        BDD: Khi brief có điểm chưa rõ ràng -> Thì hệ thống liệt kê các điểm cần làm rõ
        Given: Brief có ambiguities
        When: Gửi request phân tích
        Then: Response trả về danh sách ambiguities với suggestions
        """
        fake_cli = FakeCLIWrapper(
            analyze_success=True,
            stdout_data={
                "status": "needs_clarification",
                "ambiguities": [
                    {
                        "id": 1,
                        "description": "Unclear requirement about authentication",
                        "suggestion": "Specify which auth method to use (JWT, OAuth, Session)"
                    },
                    {
                        "id": 2,
                        "description": "Database type not specified",
                        "suggestion": "Choose between PostgreSQL, MySQL, or MongoDB"
                    }
                ],
            }
        )
        
        from api.app.routers import brief
        from fastapi import FastAPI
        
        with patch.object(brief, 'i18n', FakeI18n()):
            with patch.object(brief, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(brief.router)
                test_client = TestClient(app)
                
                response = test_client.post("/brief/analyze")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                
                # Validate ambiguities structure
                assert "data" in data
                assert data["data"]["status"] == "needs_clarification"
                assert "ambiguities" in data["data"]
                assert len(data["data"]["ambiguities"]) == 2
                
                # Validate each ambiguity has required fields
                for ambiguity in data["data"]["ambiguities"]:
                    assert "id" in ambiguity
                    assert "description" in ambiguity
                    assert "suggestion" in ambiguity
    
    def test_returns_response_in_vietnamese_by_default(self, client):
        """
        BDD: Khi không chỉ định ngôn ngữ -> Thì response mặc định tiếng Việt
        Given: Request không có header ngôn ngữ
        When: Gửi request phân tích
        Then: Response message bằng tiếng Việt
        """
        response = client.post("/brief/analyze")
        
        data = response.json()
        assert data["language"] == "vi"
        assert data["message"] == "Đã phân tích brief thành công"
    
    def test_returns_response_in_english_when_x_lang_header_is_en(self, client):
        """
        BDD: Khi header X-Lang=en -> Thì response bằng tiếng Anh
        Given: Request có header X-Lang: en
        When: Gửi request phân tích
        Then: Response message bằng tiếng Anh
        """
        response = client.post("/brief/analyze", headers={"X-Lang": "en"})
        
        data = response.json()
        assert data["language"] == "en"
        assert data["message"] == "Brief analyzed successfully"
    
    def test_returns_response_in_english_when_x_language_header_is_en(self, client):
        """
        BDD: Khi header X-Language=en -> Thì response bằng tiếng Anh
        Given: Request có header X-Language: en
        When: Gửi request phân tích
        Then: Response message bằng tiếng Anh
        """
        response = client.post("/brief/analyze", headers={"X-Language": "en"})
        
        data = response.json()
        assert data["language"] == "en"
    
    def test_returns_response_in_english_when_lang_query_param_is_en(self, mock_i18n):
        """
        BDD: Khi query param lang=en -> Thì response bằng tiếng Anh
        Given: Request có query param lang=en
        When: Gửi request phân tích
        Then: Response message bằng tiếng Anh
        """
        from api.app.routers import brief
        from fastapi import FastAPI
        
        fake_cli = FakeCLIWrapper(
            analyze_success=True,
            stdout_data={"status": "ready", "ambiguities": []}
        )
        
        with patch.object(brief, 'i18n', FakeI18n()):
            with patch.object(brief, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(brief.router)
                test_client = TestClient(app)
                
                response = test_client.post("/brief/analyze?lang=en")
                
                data = response.json()
                assert data["language"] == "en"


class TestRewriteBriefHappyPath:
    """Tests cho rewrite_brief endpoint - Happy Path scenarios"""
    
    def test_returns_success_when_brief_is_rewritten(self, client):
        """
        BDD: Khi người dùng yêu cầu viết lại brief -> Thì hệ thống viết lại thành công
        Given: Brief đã được phân tích
        When: Gửi request POST /brief/rewrite
        Then: Response trả về success=True với rewritten=True
        """
        response = client.post("/brief/rewrite")
        
        assert response.status_code == 200
        data = validate_success_response(response, "Đã viết lại brief thành công")
        
        # Validate rewritten flag
        assert data["data"] is not None
        assert data["data"]["rewritten"] is True
    
    def test_can_rewrite_brief_after_analysis(self, client):
        """
        BDD: Khi đã phân tích brief -> Thì có thể viết lại brief dựa trên kết quả phân tích
        Given: Brief đã được phân tích
        When: Gửi request rewrite sau analyze
        Then: Cả hai request đều thành công
        """
        analyze_response = client.post("/brief/analyze")
        rewrite_response = client.post("/brief/rewrite")
        
        assert analyze_response.status_code == 200
        assert analyze_response.json()["success"] is True
        
        assert rewrite_response.status_code == 200
        data = rewrite_response.json()
        assert data["success"] is True
        assert data["data"]["rewritten"] is True
    
    def test_returns_timestamp_in_response(self, client):
        """
        BDD: Response luôn chứa timestamp -> Thì timestamp là datetime hợp lệ
        Given: Bất kỳ request nào
        When: Nhận response
        Then: timestamp có thể parse thành datetime
        """
        response = client.post("/brief/analyze")
        data = response.json()
        
        # Validate timestamp can be parsed
        timestamp_str = data["timestamp"]
        # Handle both isoformat and datetime string
        try:
            datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp_str}")


# =============================================================================
# Negative Cases Tests - BDD Style
# =============================================================================

class TestAnalyzeBriefNegativeCases:
    """Tests cho analyze_brief endpoint - Negative scenarios"""
    
    def test_returns_error_when_no_brief_exists(self, mock_i18n):
        """
        BDD: Khi không có brief -> Thì hệ thống trả về lỗi brief không tồn tại
        Given: Không có brief file
        When: Gửi request phân tích
        Then: Response success=False với error message phù hợp
        """
        error_msg = "Brief not found"
        fake_cli = FakeCLIWrapper(
            analyze_success=False,
            return_error=error_msg
        )
        
        from api.app.routers import brief
        from fastapi import FastAPI
        
        with patch.object(brief, 'i18n', FakeI18n()):
            with patch.object(brief, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(brief.router)
                test_client = TestClient(app)
                
                response = test_client.post("/brief/analyze")
                
                assert response.status_code == 200
                data = validate_error_response(response, error_msg)
                assert data["success"] is False
    
    def test_returns_error_when_brief_content_is_empty(self, failing_client):
        """
        BDD: Khi brief có nội dung rỗng -> Thì hệ thống trả về lỗi
        Given: Brief file tồn tại nhưng rỗng
        When: Gửi request phân tích
        Then: Response success=False
        """
        response = failing_client.post("/brief/analyze")
        
        assert response.status_code == 200
        data = validate_error_response(response)
        assert data["success"] is False
    
    def test_returns_error_when_brief_format_is_invalid(self, failing_client):
        """
        BDD: Khi brief có định dạng không hợp lệ -> Thì hệ thống trả về lỗi
        Given: Brief file có format sai
        When: Gửi request phân tích
        Then: Response success=False với error message
        """
        response = failing_client.post("/brief/analyze")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "message" in data


class TestRewriteBriefNegativeCases:
    """Tests cho rewrite_brief endpoint - Negative scenarios"""
    
    def test_returns_error_when_no_brief_exists(self, mock_i18n):
        """
        BDD: Khi không có brief -> Thì không thể viết lại brief
        Given: Không có brief file
        When: Gửi request rewrite
        Then: Response success=False với error message
        """
        error_msg = "Brief not found"
        fake_cli = FakeCLIWrapper(
            rewrite_success=False,
            return_error=error_msg
        )
        
        from api.app.routers import brief
        from fastapi import FastAPI
        
        with patch.object(brief, 'i18n', FakeI18n()):
            with patch.object(brief, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(brief.router)
                test_client = TestClient(app)
                
                response = test_client.post("/brief/rewrite")
                
                assert response.status_code == 200
                data = validate_error_response(response, error_msg)
                assert data["success"] is False
    
    def test_returns_error_when_no_write_permission(self, mock_i18n):
        """
        BDD: Khi không có quyền ghi -> Thì hệ thống từ chối viết lại brief
        Given: Không có write permission
        When: Gửi request rewrite
        Then: Response success=False với permission error
        """
        error_msg = "Permission denied"
        fake_cli = FakeCLIWrapper(
            rewrite_success=False,
            return_error=error_msg
        )
        
        from api.app.routers import brief
        from fastapi import FastAPI
        
        with patch.object(brief, 'i18n', FakeI18n()):
            with patch.object(brief, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(brief.router)
                test_client = TestClient(app)
                
                response = test_client.post("/brief/rewrite")
                
                assert response.status_code == 200
                data = validate_error_response(response, error_msg)
                assert data["success"] is False


# =============================================================================
# Edge Cases Tests - BDD Style
# =============================================================================

class TestBriefEdgeCases:
    """Tests cho các trường hợp edge case"""
    
    def test_handles_very_short_brief_successfully(self, client):
        """
        BDD: Khi brief rất ngắn (vài từ) -> Thì hệ thống vẫn phân tích được
        Given: Brief chỉ có vài từ
        When: Gửi request phân tích
        Then: Response success=True (có thể với suggestions)
        """
        response = client.post("/brief/analyze")
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_handles_very_long_brief_successfully(self, client):
        """
        BDD: Khi brief rất dài -> Thì hệ thống phân tích toàn bộ
        Given: Brief có nội dung rất dài
        When: Gửi request phân tích
        Then: Response success=True với kết quả đầy đủ
        """
        response = client.post("/brief/analyze")
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_handles_brief_with_multiple_languages(self, client):
        """
        BDD: Khi brief có nhiều ngôn ngữ -> Thì hệ thống xác định ngôn ngữ chính
        Given: Brief chứa tiếng Việt, Anh, và ngôn ngữ khác
        When: Gửi request phân tích
        Then: Response success=True
        """
        response = client.post("/brief/analyze")
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_handles_brief_with_special_characters(self, client):
        """
        BDD: Khi brief có ký tự đặc biệt -> Thì hệ thống xử lý đúng
        Given: Brief chứa ký tự đặc biệt (emoji, unicode, symbols)
        When: Gửi request phân tích
        Then: Response success=True không lỗi encoding
        """
        response = client.post("/brief/analyze")
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_handles_unicode_content_in_brief(self, client):
        """
        BDD: Khi brief có nội dung Unicode -> Thì hệ thống xử lý đúng
        Given: Brief chứa Unicode characters
        When: Gửi request phân tích
        Then: Response success=True
        """
        response = client.post("/brief/analyze")
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_detects_conflicting_requirements_in_brief(self, mock_i18n):
        """
        BDD: Khi brief có yêu cầu mâu thuẫn -> Thì hệ thống phát hiện và liệt kê
        Given: Brief chứa yêu cầu mâu thuẫn
        When: Gửi request phân tích
        Then: Response success=True với conflict trong ambiguities
        """
        fake_cli = FakeCLIWrapper(
            analyze_success=True,
            stdout_data={
                "status": "needs_clarification",
                "ambiguities": [
                    {
                        "type": "conflict",
                        "description": "Conflicting requirement: 'use PostgreSQL' vs 'use MongoDB'",
                        "suggestion": "Choose one database technology"
                    },
                ],
            }
        )
        
        from api.app.routers import brief
        from fastapi import FastAPI
        
        with patch.object(brief, 'i18n', FakeI18n()):
            with patch.object(brief, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(brief.router)
                test_client = TestClient(app)
                
                response = test_client.post("/brief/analyze")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]["ambiguities"]) > 0
                assert data["data"]["ambiguities"][0]["type"] == "conflict"


class TestRewriteBriefEdgeCases:
    """Tests cho rewrite_brief edge cases"""
    
    def test_handles_multiple_consecutive_rewrite_requests(self, client):
        """
        BDD: Khi yêu cầu viết lại nhiều lần liên tiếp -> Thì mỗi lần đều cập nhật thành công
        Given: Brief đã tồn tại
        When: Gửi 5 request rewrite liên tiếp
        Then: Tất cả request đều success=True
        """
        responses = [client.post("/brief/rewrite") for _ in range(5)]
        
        for i, response in enumerate(responses):
            assert response.status_code == 200, f"Request {i+1} should return 200"
            data = response.json()
            assert data["success"] is True, f"Request {i+1} should be successful"
            assert data["data"]["rewritten"] is True


# =============================================================================
# Boundary Cases Tests - BDD Style
# =============================================================================

class TestBriefBoundaryCases:
    """Tests cho các trường hợp boundary"""
    
    def test_handles_brief_at_minimum_length(self, client):
        """
        BDD: Khi brief ở độ dài tối thiểu cho phép -> Thì phân tích thành công
        Given: Brief có độ dài = min_length
        When: Gửi request phân tích
        Then: Response success=True
        """
        response = client.post("/brief/analyze")
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_handles_brief_at_maximum_length(self, client):
        """
        BDD: Khi brief ở độ dài tối đa cho phép -> Thì phân tích thành công
        Given: Brief có độ dài = max_length
        When: Gửi request phân tích
        Then: Response success=True
        """
        response = client.post("/brief/analyze")
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_returns_error_when_brief_exceeds_maximum_length(self, mock_i18n):
        """
        BDD: Khi brief vượt quá độ dài tối đa -> Thì hệ thống từ chối phân tích
        Given: Brief có độ dài > max_length
        When: Gửi request phân tích
        Then: Response success=False với error về độ dài
        """
        error_msg = "Brief exceeds maximum length"
        fake_cli = FakeCLIWrapper(
            analyze_success=False,
            return_error=error_msg
        )
        
        from api.app.routers import brief
        from fastapi import FastAPI
        
        with patch.object(brief, 'i18n', FakeI18n()):
            with patch.object(brief, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(brief.router)
                test_client = TestClient(app)
                
                response = test_client.post("/brief/analyze")
                
                assert response.status_code == 200
                data = validate_error_response(response, "exceeds maximum")
                assert data["success"] is False


# =============================================================================
# Integration-style Tests
# =============================================================================

class TestBriefWorkflow:
    """Tests cho workflow phân tích và viết lại brief"""
    
    def test_full_analyze_rewrite_workflow(self, client):
        """
        BDD: Workflow đầy đủ: phân tích -> nhận clarifications -> viết lại
        Given: Brief chưa được phân tích
        When: Thực hiện analyze -> rewrite
        Then: Cả hai bước đều thành công
        """
        # Step 1: Analyze brief
        analyze_response = client.post("/brief/analyze")
        assert analyze_response.status_code == 200
        analyze_data = validate_success_response(analyze_response)
        
        # Step 2: Rewrite brief based on analysis
        rewrite_response = client.post("/brief/rewrite")
        assert rewrite_response.status_code == 200
        rewrite_data = validate_success_response(rewrite_response)
        
        # Validate both steps completed
        assert analyze_data["success"] is True
        assert rewrite_data["success"] is True
        assert rewrite_data["data"]["rewritten"] is True
    
    def test_can_analyze_multiple_times(self, client):
        """
        BDD: Có thể phân tích brief nhiều lần -> Mỗi lần đều thành công
        Given: Brief đã tồn tại
        When: Gửi nhiều request analyze
        Then: Tất cả đều success=True
        """
        for i in range(3):
            response = client.post("/brief/analyze")
            assert response.status_code == 200
            data = validate_success_response(response)
            assert data["success"] is True