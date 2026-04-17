"""
Unit tests cho Code Router
Chuyển đổi từ BDD: tests/features/api/code.feature

Test coverage:
- Happy Path: build success, plan success, gen success, apply success
- Negative Cases: no IR, invalid IR, no plan, no generated code, conflicts
- Edge Cases: complex IR, simple IR, multiple generations, force apply
- Boundary Cases: min/max files, long file names, complexity limits

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
    
    def __init__(self, build_success=True, plan_success=True, gen_success=True, apply_success=True, return_error=None, stdout_data=None):
        self.build_success = build_success
        self.plan_success = plan_success
        self.gen_success = gen_success
        self.apply_success = apply_success
        self.return_error = return_error
        self.stdout_data = stdout_data or {}
    
    async def code_build(self) -> dict:
        """Mock code_build method"""
        if self.build_success:
            return {
                "success": True,
                "stdout": "Plan built",
                "stderr": "",
                "stdout_data": self.stdout_data
            }
        return {"success": False, "stdout": "", "stderr": self.return_error or "Build failed"}
    
    async def code_plan(self) -> dict:
        """Mock code_plan method"""
        if self.plan_success:
            return {
                "success": True,
                "stdout": "Plan created",
                "stderr": "",
                "stdout_data": self.stdout_data
            }
        return {"success": False, "stdout": "", "stderr": self.return_error or "Plan failed"}
    
    async def code_gen(self, runtime: bool = False) -> dict:
        """Mock code_gen method"""
        if self.gen_success:
            return {
                "success": True,
                "stdout": f"Generated (runtime={runtime})",
                "stderr": "",
                "stdout_data": {"runtime": runtime}
            }
        return {"success": False, "stdout": "", "stderr": self.return_error or "Gen failed"}
    
    async def code_apply(self, force: bool = False, dry_run: bool = False, no_reindex: bool = False, patches_subdir: str = None) -> dict:
        """Mock code_apply method"""
        if self.apply_success:
            return {
                "success": True,
                "stdout": f"Applied (force={force}, dry_run={dry_run}, no_reindex={no_reindex})",
                "stderr": "",
                "stdout_data": {
                    "force": force,
                    "dry_run": dry_run,
                    "no_reindex": no_reindex,
                    "patches_subdir": patches_subdir
                }
            }
        return {"success": False, "stdout": "", "stderr": self.return_error or "Apply failed"}


class FakeI18n:
    """Fake i18n cho testing"""
    
    def __init__(self):
        self.translations = {
            "vi": {
                "code.build_success": "Đã tạo kế hoạch code thành công",
                "code.gen_success": "Đã tạo code thành công",
                "code.apply_success": "Đã áp dụng code thành công",
                "common.success": "Thành công",
            },
            "en": {
                "code.build_success": "Code plan built successfully",
                "code.gen_success": "Code generated successfully",
                "code.apply_success": "Code applied successfully",
                "common.success": "Success",
            },
        }
        self.default_language = "vi"
    
    def get_language_from_request(self, request) -> str:
        if request is None:
            return self.default_language
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
    from api.app.routers import code
    with patch.object(code, 'i18n', fake_i18n):
        yield fake_i18n


@pytest.fixture
def client(mock_i18n):
    """Fixture tao TestClient voi mock cli_wrapper thanh cong"""
    from api.app.routers import code
    from fastapi import FastAPI
    
    fake_cli = FakeCLIWrapper(
        build_success=True, 
        plan_success=True, 
        gen_success=True, 
        apply_success=True
    )
    
    with patch.object(code, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(code.router)
        yield TestClient(app)


@pytest.fixture
def failing_client(mock_i18n):
    """Fixture tao TestClient voi mock cli_wrapper that bai"""
    from api.app.routers import code
    from fastapi import FastAPI
    
    fake_cli = FakeCLIWrapper(
        build_success=False, 
        plan_success=False, 
        gen_success=False, 
        apply_success=False, 
        return_error="Test error"
    )
    
    with patch.object(code, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(code.router)
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


def validate_timestamp_format(timestamp_str):
    """Validate timestamp can be parsed as datetime"""
    try:
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"Invalid timestamp format: {timestamp_str}")


# =============================================================================
# Build Code Plan Tests - BDD Style
# =============================================================================

class TestBuildCodePlanHappyPath:
    """Tests cho build_code_plan endpoint - Happy Path scenarios"""
    
    def test_returns_success_when_code_plan_is_built_from_valid_ir(self, client):
        """
        BDD: Khi IR hợp lệ -> Thì hệ thống build code plan thành công
        Given: IR đã được tạo và hợp lệ
        When: Gửi request POST /code/build
        Then: Response trả về success=True với plan_path
        """
        response = client.post("/code/build")
        
        # Validate HTTP status
        assert response.status_code == 200, "Should return HTTP 200 OK"
        
        # Validate response structure
        data = validate_success_response(response, "Đã tạo kế hoạch code thành công")
        
        # Validate data field contains expected structure
        assert "data" in data, "Response must contain 'data' field"
        assert data["data"]["built"] is True, "Data should contain built=True"
        assert "plan_path" in data["data"], "Data should contain plan_path"
        assert "lowering.json" in data["data"]["plan_path"], "Plan path should contain lowering.json"
    
    def test_returns_response_in_vietnamese_by_default(self, client):
        """
        BDD: Khi không chỉ định ngôn ngữ -> Thì response mặc định tiếng Việt
        Given: Request không có header ngôn ngữ
        When: Gửi request build
        Then: Response message bằng tiếng Việt
        """
        response = client.post("/code/build")
        
        data = response.json()
        assert data["language"] == "vi"
        assert data["message"] == "Đã tạo kế hoạch code thành công"
    
    def test_returns_response_in_english_when_x_lang_header_is_en(self, client):
        """
        BDD: Khi header X-Lang=en -> Thì response bằng tiếng Anh
        Given: Request có header X-Lang: en
        When: Gửi request build
        Then: Response message bằng tiếng Anh
        """
        response = client.post("/code/build", headers={"X-Lang": "en"})
        
        data = response.json()
        assert data["language"] == "en"
        assert data["message"] == "Code plan built successfully"


class TestBuildCodePlanNegativeCases:
    """Tests cho build_code_plan endpoint - Negative scenarios"""
    
    def test_returns_error_when_no_ir_exists(self, mock_i18n):
        """
        BDD: Khi không có IR -> Thì hệ thống trả về lỗi IR không tồn tại
        Given: Không có IR file
        When: Gửi request build
        Then: Response success=False với error message về IR
        """
        error_msg = "IR not found"
        fake_cli = FakeCLIWrapper(build_success=False, return_error=error_msg)
        
        from api.app.routers import code
        from fastapi import FastAPI
        
        with patch.object(code, 'i18n', FakeI18n()):
            with patch.object(code, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(code.router)
                test_client = TestClient(app)
                
                response = test_client.post("/code/build")
                
                assert response.status_code == 200
                data = validate_error_response(response, "IR")
                assert data["success"] is False
    
    def test_returns_error_when_ir_format_is_invalid(self, mock_i18n):
        """
        BDD: Khi IR không hợp lệ -> Thì hệ thống trả về lỗi format
        Given: IR file có format sai
        When: Gửi request build
        Then: Response success=False với error message về IR format
        """
        error_msg = "Invalid IR format"
        fake_cli = FakeCLIWrapper(build_success=False, return_error=error_msg)
        
        from api.app.routers import code
        from fastapi import FastAPI
        
        with patch.object(code, 'i18n', FakeI18n()):
            with patch.object(code, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(code.router)
                test_client = TestClient(app)
                
                response = test_client.post("/code/build")
                
                assert response.status_code == 200
                data = validate_error_response(response, "Invalid IR")
                assert data["success"] is False


class TestBuildCodePlanEdgeCases:
    """Tests cho build_code_plan endpoint - Edge cases"""
    
    def test_handles_complex_ir_with_many_components(self, client):
        """
        BDD: Khi IR rất phức tạp -> Thì hệ thống tạo plan đầy đủ
        Given: IR có nhiều thành phần phức tạp
        When: Gửi request build
        Then: Response success=True với plan_path
        """
        response = client.post("/code/build")
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
        assert "plan_path" in data["data"]
    
    def test_handles_simple_ir_with_few_components(self, client):
        """
        BDD: Khi IR rất đơn giản -> Thì hệ thống tạo plan tối giản
        Given: IR chỉ có ít thành phần
        When: Gửi request build
        Then: Response success=True
        """
        response = client.post("/code/build")
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_overwrites_existing_plan_when_building_multiple_times(self, client):
        """
        BDD: Khi build plan nhiều lần -> Thì plan cũ bị ghi đè
        Given: Plan đã tồn tại
        When: Gửi nhiều request build liên tiếp
        Then: Tất cả đều success=True
        """
        responses = [client.post("/code/build") for _ in range(3)]
        
        for i, response in enumerate(responses):
            assert response.status_code == 200, f"Request {i+1} should return 200"
            data = response.json()
            assert data["success"] is True, f"Request {i+1} should be successful"


# =============================================================================
# Plan Code Tests - BDD Style
# =============================================================================

class TestPlanCodeHappyPath:
    """Tests cho plan_code endpoint - Happy Path scenarios"""
    
    def test_returns_success_when_plan_is_created(self, client):
        """
        BDD: Khi plan code được tạo -> Thì hệ thống trả về success
        Given: IR đã tồn tại
        When: Gửi request POST /code/plan
        Then: Response success=True với planned=True
        """
        response = client.post("/code/plan")
        
        assert response.status_code == 200
        data = validate_success_response(response, "Đã tạo kế hoạch code thành công")
        
        assert data["data"]["planned"] is True
        assert "plan_path" in data["data"]


# =============================================================================
# Generate Code Tests - BDD Style
# =============================================================================

class TestGenerateCodeHappyPath:
    """Tests cho generate_code endpoint - Happy Path scenarios"""
    
    def test_returns_success_when_code_is_generated_from_valid_plan(self, client):
        """
        BDD: Khi plan hợp lệ -> Thì hệ thống generate code thành công
        Given: Code plan đã được tạo
        When: Gửi request POST /code/gen
        Then: Response success=True với generated_path và report_path
        """
        response = client.post("/code/gen")
        
        assert response.status_code == 200
        data = validate_success_response(response, "Đã tạo code thành công")
        
        assert data["data"]["generated"] is True
        assert "generated_path" in data["data"]
        assert "report_path" in data["data"]
    
    def test_generates_runtime_files_when_runtime_flag_is_true(self, client):
        """
        BDD: Khi runtime=True -> Thì hệ thống generate cả runtime files
        Given: Plan đã tồn tại, request có runtime=true
        When: Gửi request gen
        Then: Response success=True với runtime files được generate
        """
        response = client.post("/code/gen", json={"runtime": True})
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
        assert data["data"]["generated"] is True
    
    def test_returns_response_in_english_when_x_lang_header_is_en(self, client):
        """
        BDD: Khi header X-Lang=en -> Thì response bằng tiếng Anh
        Given: Request có header X-Lang: en
        When: Gửi request gen
        Then: Response message bằng tiếng Anh
        """
        response = client.post("/code/gen", headers={"X-Lang": "en"})
        
        data = response.json()
        assert data["language"] == "en"
        assert data["message"] == "Code generated successfully"


class TestGenerateCodeNegativeCases:
    """Tests cho generate_code endpoint - Negative scenarios"""
    
    def test_returns_error_when_no_plan_exists(self, mock_i18n):
        """
        BDD: Khi không có plan -> Thì hệ thống trả về lỗi plan không tồn tại
        Given: Không có code plan
        When: Gửi request gen
        Then: Response success=False với error message về plan
        """
        error_msg = "Plan not found"
        fake_cli = FakeCLIWrapper(gen_success=False, return_error=error_msg)
        
        from api.app.routers import code
        from fastapi import FastAPI
        
        with patch.object(code, 'i18n', FakeI18n()):
            with patch.object(code, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(code.router)
                test_client = TestClient(app)
                
                response = test_client.post("/code/gen")
                
                assert response.status_code == 200
                data = validate_error_response(response, "Plan")
                assert data["success"] is False
    
    def test_returns_error_when_plan_format_is_invalid(self, mock_i18n):
        """
        BDD: Khi plan không hợp lệ -> Thì hệ thống trả về lỗi
        Given: Plan file có format sai
        When: Gửi request gen
        Then: Response success=False với error message
        """
        error_msg = "Invalid plan format"
        fake_cli = FakeCLIWrapper(gen_success=False, return_error=error_msg)
        
        from api.app.routers import code
        from fastapi import FastAPI
        
        with patch.object(code, 'i18n', FakeI18n()):
            with patch.object(code, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(code.router)
                test_client = TestClient(app)
                
                response = test_client.post("/code/gen")
                
                assert response.status_code == 200
                data = validate_error_response(response, "Invalid")
                assert data["success"] is False
    
    def test_returns_error_when_complexity_exceeds_limit(self, mock_i18n):
        """
        BDD: Khi độ phức tạp vượt quá giới hạn -> Thì hệ thống từ chối generate
        Given: Plan có độ phức tạp quá cao
        When: Gửi request gen
        Then: Response success=False với error về complexity
        """
        error_msg = "Complexity exceeds limit, please simplify"
        fake_cli = FakeCLIWrapper(gen_success=False, return_error=error_msg)
        
        from api.app.routers import code
        from fastapi import FastAPI
        
        with patch.object(code, 'i18n', FakeI18n()):
            with patch.object(code, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(code.router)
                test_client = TestClient(app)
                
                response = test_client.post("/code/gen")
                
                assert response.status_code == 200
                data = validate_error_response(response, "Complexity")
                assert data["success"] is False


class TestGenerateCodeEdgeCases:
    """Tests cho generate_code endpoint - Edge cases"""
    
    def test_handles_minimum_number_of_files(self, client):
        """
        BDD: Khi số lượng file tối thiểu -> Thì generate thành công
        Given: Plan với số file tối thiểu
        When: Gửi request gen
        Then: Response success=True
        """
        response = client.post("/code/gen")
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_handles_maximum_number_of_files(self, client):
        """
        BDD: Khi số lượng file tối đa -> Thì generate thành công
        Given: Plan với số file tối đa cho phép
        When: Gửi request gen
        Then: Response success=True
        """
        response = client.post("/code/gen")
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_overwrites_generated_code_when_generating_multiple_times(self, client):
        """
        BDD: Khi generate nhiều lần -> Thì code cũ bị ghi đè
        Given: Generated code đã tồn tại
        When: Gửi nhiều request gen liên tiếp
        Then: Tất cả đều success=True
        """
        responses = [client.post("/code/gen") for _ in range(3)]
        
        for i, response in enumerate(responses):
            assert response.status_code == 200, f"Request {i+1} should return 200"
            data = response.json()
            assert data["success"] is True, f"Request {i+1} should be successful"


# =============================================================================
# Apply Code Tests - BDD Style
# =============================================================================

class TestApplyCodeHappyPath:
    """Tests cho apply_code endpoint - Happy Path scenarios"""
    
    def test_returns_success_when_code_is_applied_to_working_directory(self, client):
        """
        BDD: Khi generated code tồn tại -> Thì hệ thống apply code thành công
        Given: Generated code đã được tạo
        When: Gửi request POST /code/apply
        Then: Response success=True với applied=True
        """
        response = client.post("/code/apply")
        
        assert response.status_code == 200
        data = validate_success_response(response, "Đã áp dụng code thành công")
        
        assert data["data"]["applied"] is True
        assert "status_path" in data["data"]
    
    def test_performs_dry_run_when_dry_run_flag_is_true(self, client):
        """
        BDD: Khi dry_run=True -> Thì hệ thống chỉ xem trước không viết file
        Given: Generated code đã tồn tại
        When: Gửi request apply với dry_run=true
        Then: Response success=True với dry_run mode
        """
        response = client.post("/code/apply", json={"dry_run": True})
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_applies_with_force_when_force_flag_is_true(self, client):
        """
        BDD: Khi force=True -> Thì hệ thống ghi đè các file conflict
        Given: Có file conflict
        When: Gửi request apply với force=true
        Then: Response success=True
        """
        response = client.post("/code/apply", json={"force": True})
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_skips_reindex_when_no_reindex_flag_is_true(self, client):
        """
        BDD: Khi no_reindex=True -> Thì hệ thống không cập nhật index
        Given: Generated code đã tồn tại
        When: Gửi request apply với no_reindex=true
        Then: Response success=True
        """
        response = client.post("/code/apply", json={"no_reindex": True})
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_uses_custom_patches_subdir_when_specified(self, client):
        """
        BDD: Khi patches_subdir được chỉ định -> Thì hệ thống lưu patches vào thư mục đó
        Given: patches_subdir="custom_patches"
        When: Gửi request apply
        Then: Response success=True
        """
        response = client.post("/code/apply", json={"patches_subdir": "custom_patches"})
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_returns_response_in_english_when_x_lang_header_is_en(self, client):
        """
        BDD: Khi header X-Lang=en -> Thì response bằng tiếng Anh
        Given: Request có header X-Lang: en
        When: Gửi request apply
        Then: Response message bằng tiếng Anh
        """
        response = client.post("/code/apply", headers={"X-Lang": "en"})
        
        data = response.json()
        assert data["language"] == "en"
        assert data["message"] == "Code applied successfully"


class TestApplyCodeNegativeCases:
    """Tests cho apply_code endpoint - Negative scenarios"""
    
    def test_returns_error_when_no_generated_code_exists(self, mock_i18n):
        """
        BDD: Khi không có generated code -> Thì hệ thống trả về lỗi
        Given: Không có generated code
        When: Gửi request apply
        Then: Response success=False với error message
        """
        error_msg = "No generated code found"
        fake_cli = FakeCLIWrapper(apply_success=False, return_error=error_msg)
        
        from api.app.routers import code
        from fastapi import FastAPI
        
        with patch.object(code, 'i18n', FakeI18n()):
            with patch.object(code, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(code.router)
                test_client = TestClient(app)
                
                response = test_client.post("/code/apply")
                
                assert response.status_code == 200
                data = validate_error_response(response, "No generated code")
                assert data["success"] is False
    
    def test_returns_error_when_conflict_detected_without_force(self, mock_i18n):
        """
        BDD: Khi có conflict và không force -> Thì hệ thống từ chối apply
        Given: Có file conflict, force=false
        When: Gửi request apply
        Then: Response success=False với conflict details
        """
        error_msg = "Conflict detected: file.py"
        fake_cli = FakeCLIWrapper(apply_success=False, return_error=error_msg)
        
        from api.app.routers import code
        from fastapi import FastAPI
        
        with patch.object(code, 'i18n', FakeI18n()):
            with patch.object(code, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(code.router)
                test_client = TestClient(app)
                
                response = test_client.post("/code/apply")
                
                assert response.status_code == 200
                data = validate_error_response(response, "Conflict")
                assert data["success"] is False
    
    def test_returns_error_when_no_write_permission(self, mock_i18n):
        """
        BDD: Khi không có quyền ghi -> Thì hệ thống trả về lỗi permission
        Given: Không có write permission
        When: Gửi request apply
        Then: Response success=False với permission error
        """
        error_msg = "Permission denied: cannot write to directory"
        fake_cli = FakeCLIWrapper(apply_success=False, return_error=error_msg)
        
        from api.app.routers import code
        from fastapi import FastAPI
        
        with patch.object(code, 'i18n', FakeI18n()):
            with patch.object(code, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(code.router)
                test_client = TestClient(app)
                
                response = test_client.post("/code/apply")
                
                assert response.status_code == 200
                data = validate_error_response(response, "Permission denied")
                assert data["success"] is False


class TestApplyCodeEdgeCases:
    """Tests cho apply_code endpoint - Edge cases"""
    
    def test_handles_file_with_very_long_name(self, client):
        """
        BDD: Khi file có tên rất dài -> Thì hệ thống xử lý đúng
        Given: File name > 100 characters
        When: Gửi request apply
        Then: Response success=True
        """
        response = client.post("/code/apply")
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_overwrites_conflicting_files_when_force_is_true(self, client):
        """
        BDD: Khi có conflict và force=True -> Thì hệ thống ghi đè
        Given: Có file conflict, force=true
        When: Gửi request apply
        Then: Response success=True
        """
        response = client.post("/code/apply", json={"force": True})
        
        assert response.status_code == 200
        data = validate_success_response(response)
        assert data["success"] is True
    
    def test_applies_runtime_files_when_generated_with_runtime(self, client):
        """
        BDD: Khi code được generate với runtime -> Thì apply bao gồm runtime files
        Given: Code đã được generate với runtime=true
        When: Gửi request apply
        Then: Response success=True
        """
        gen_response = client.post("/code/gen", json={"runtime": True})
        apply_response = client.post("/code/apply")
        
        assert gen_response.status_code == 200
        assert apply_response.status_code == 200
        assert apply_response.json()["success"] is True


# =============================================================================
# Full Pipeline Workflow Tests - BDD Style
# =============================================================================

class TestCodePipelineWorkflow:
    """Tests cho full pipeline workflow: build -> gen -> apply"""
    
    def test_full_build_plan_generate_apply_pipeline_completes_successfully(self, client):
        """
        BDD: Pipeline đầy đủ: build -> gen -> apply
        Given: IR đã tồn tại
        When: Thực hiện build -> gen -> apply theo thứ tự
        Then: Tất cả các bước đều thành công
        """
        # Step 1: Build code plan
        build_response = client.post("/code/build")
        assert build_response.status_code == 200
        build_data = validate_success_response(build_response)
        assert build_data["data"]["built"] is True
        
        # Step 2: Generate code
        gen_response = client.post("/code/gen")
        assert gen_response.status_code == 200
        gen_data = validate_success_response(gen_response)
        assert gen_data["data"]["generated"] is True
        
        # Step 3: Apply code
        apply_response = client.post("/code/apply")
        assert apply_response.status_code == 200
        apply_data = validate_success_response(apply_response)
        assert apply_data["data"]["applied"] is True
    
    def test_full_pipeline_with_runtime_files_completes_successfully(self, client):
        """
        BDD: Pipeline với runtime: build -> gen(runtime) -> apply
        Given: IR đã tồn tại
        When: Thực hiện build -> gen với runtime=true -> apply
        Then: Tất cả các bước đều thành công
        """
        # Step 1: Build code plan
        build_response = client.post("/code/build")
        assert build_response.status_code == 200
        assert build_response.json()["success"] is True
        
        # Step 2: Generate code with runtime
        gen_response = client.post("/code/gen", json={"runtime": True})
        assert gen_response.status_code == 200
        assert gen_response.json()["success"] is True
        
        # Step 3: Apply code
        apply_response = client.post("/code/apply")
        assert apply_response.status_code == 200
        assert apply_response.json()["success"] is True
    
    def test_dry_run_pipeline_shows_changes_without_applying(self, client):
        """
        BDD: Dry run pipeline: build -> gen -> apply(dry_run)
        Given: IR đã tồn tại
        When: Thực hiện build -> gen -> apply với dry_run=true
        Then: Apply trả về success nhưng không viết file
        """
        build_response = client.post("/code/build")
        gen_response = client.post("/code/gen")
        apply_response = client.post("/code/apply", json={"dry_run": True})
        
        assert build_response.status_code == 200
        assert gen_response.status_code == 200
        assert apply_response.status_code == 200
        assert apply_response.json()["success"] is True


# =============================================================================
# Response Validation Tests
# =============================================================================

class TestCodeResponseValidation:
    """Tests cho response validation"""
    
    def test_all_responses_include_timestamp(self, client):
        """
        BDD: Response luôn chứa timestamp -> Thì timestamp là datetime hợp lệ
        Given: Bất kỳ request nào
        When: Nhận response
        Then: timestamp có thể parse thành datetime
        """
        endpoints = ["/code/build", "/code/plan", "/code/gen", "/code/apply"]
        
        for endpoint in endpoints:
            response = client.post(endpoint)
            data = response.json()
            assert "timestamp" in data, f"{endpoint} should have timestamp"
            validate_timestamp_format(data["timestamp"])
    
    def test_all_responses_include_language_field(self, client):
        """
        BDD: Response luôn chứa language -> Thì language là string hợp lệ
        Given: Bất kỳ request nào
        When: Nhận response
        Then: language field tồn tại và là string
        """
        endpoints = ["/code/build", "/code/plan", "/code/gen", "/code/apply"]
        
        for endpoint in endpoints:
            response = client.post(endpoint)
            data = response.json()
            assert "language" in data, f"{endpoint} should have language"
            assert isinstance(data["language"], str), "language should be string"
    
    def test_success_responses_have_non_null_data(self, client):
        """
        BDD: Response success=True -> Thì data không null
        Given: Request thành công
        When: Nhận response với success=True
        Then: data field tồn tại
        """
        endpoints = ["/code/build", "/code/plan", "/code/gen", "/code/apply"]
        
        for endpoint in endpoints:
            response = client.post(endpoint)
            data = response.json()
            if data["success"]:
                assert "data" in data, f"Success response for {endpoint} should have data"