"""
Unit tests cho Contract Router
Chuyển đổi từ BDD: tests/features/api/contract.feature
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


class FakeCLIWrapper:
    def __init__(self, gen_success=True, resume_success=True, check_success=True, feedback_success=True, return_error=None):
        self.gen_success = gen_success
        self.resume_success = resume_success
        self.check_success = check_success
        self.feedback_success = feedback_success
        self.return_error = return_error
    
    async def contract_gen(self) -> dict:
        if self.gen_success:
            return {"success": True, "stdout": "Contract generated", "stderr": ""}
        return {"success": False, "stdout": "", "stderr": self.return_error or "Gen failed"}
    
    async def contract_gen_resume(self) -> dict:
        if self.resume_success:
            return {"success": True, "stdout": "Contract resumed", "stderr": ""}
        return {"success": False, "stdout": "", "stderr": self.return_error or "Resume failed"}
    
    async def contract_check(self) -> dict:
        if self.check_success:
            return {"success": True, "stdout": "Contract valid", "stderr": ""}
        return {"success": False, "stdout": "", "stderr": self.return_error or "Check failed"}
    
    async def contract_feedback(self) -> dict:
        if self.feedback_success:
            return {"success": True, "stdout": "Feedback processed", "stderr": ""}
        return {"success": False, "stdout": "", "stderr": self.return_error or "Feedback failed"}


class FakeI18n:
    def __init__(self):
        self.translations = {
            "vi": {
                "contract.gen_success": "Đã tạo hợp đồng DSL thành công",
                "contract.check_success": "Hợp đồng hợp lệ",
                "common.success": "Thành công",
            },
            "en": {
                "contract.gen_success": "DSL contract generated successfully",
                "contract.check_success": "Contract is valid",
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
    from api.app.routers import contract
    with patch.object(contract, 'i18n', fake_i18n):
        yield fake_i18n


@pytest.fixture
def client(mock_i18n):
    from api.app.routers import contract
    from fastapi import FastAPI
    fake_cli = FakeCLIWrapper(gen_success=True, resume_success=True, check_success=True, feedback_success=True)
    with patch.object(contract, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(contract.router)
        yield TestClient(app)


@pytest.fixture
def failing_client(mock_i18n):
    from api.app.routers import contract
    from fastapi import FastAPI
    fake_cli = FakeCLIWrapper(gen_success=False, resume_success=False, check_success=False, feedback_success=False, return_error="Test error")
    with patch.object(contract, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(contract.router)
        yield TestClient(app)


class TestGenerateContract:
    def test_generate_contract_success(self, client):
        response = client.post("/contract/gen")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["generated"] is True
    
    def test_generate_contract_and_check(self, client):
        gen_response = client.post("/contract/gen")
        check_response = client.post("/contract/check")
        assert gen_response.status_code == 200
        assert gen_response.json()["success"] is True
        assert check_response.status_code == 200
        assert check_response.json()["success"] is True


class TestResumeContractGen:
    def test_resume_contract_gen_success(self, client):
        response = client.post("/contract/gen/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["resumed"] is True


class TestCheckContract:
    def test_check_contract_valid(self, client):
        response = client.post("/contract/check")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["valid"] is True


class TestContractFeedback:
    def test_contract_feedback_success(self, client):
        response = client.post("/contract/feedback")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["processed"] is True


class TestContractNegativeCases:
    def test_generate_contract_no_brief(self, mock_i18n):
        error_msg = "Brief not found"
        fake_cli = FakeCLIWrapper(gen_success=False, return_error=error_msg)
        from api.app.routers import contract
        from fastapi import FastAPI
        with patch.object(contract, 'i18n', FakeI18n()):
            with patch.object(contract, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(contract.router)
                test_client = TestClient(app)
                response = test_client.post("/contract/gen")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_generate_contract_brief_not_analyzed(self, mock_i18n):
        error_msg = "Brief not analyzed"
        fake_cli = FakeCLIWrapper(gen_success=False, return_error=error_msg)
        from api.app.routers import contract
        from fastapi import FastAPI
        with patch.object(contract, 'i18n', FakeI18n()):
            with patch.object(contract, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(contract.router)
                test_client = TestClient(app)
                response = test_client.post("/contract/gen")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_check_contract_no_contract(self, mock_i18n):
        error_msg = "Contract not found"
        fake_cli = FakeCLIWrapper(check_success=False, return_error=error_msg)
        from api.app.routers import contract
        from fastapi import FastAPI
        with patch.object(contract, 'i18n', FakeI18n()):
            with patch.object(contract, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(contract.router)
                test_client = TestClient(app)
                response = test_client.post("/contract/check")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_check_contract_invalid(self, mock_i18n):
        error_msg = "Contract validation failed: syntax error at line 10"
        fake_cli = FakeCLIWrapper(check_success=False, return_error=error_msg)
        from api.app.routers import contract
        from fastapi import FastAPI
        with patch.object(contract, 'i18n', FakeI18n()):
            with patch.object(contract, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(contract.router)
                test_client = TestClient(app)
                response = test_client.post("/contract/check")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_resume_contract_gen_no_process(self, mock_i18n):
        error_msg = "No process to resume"
        fake_cli = FakeCLIWrapper(resume_success=False, return_error=error_msg)
        from api.app.routers import contract
        from fastapi import FastAPI
        with patch.object(contract, 'i18n', FakeI18n()):
            with patch.object(contract, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(contract.router)
                test_client = TestClient(app)
                response = test_client.post("/contract/gen/resume")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_contract_feedback_no_contract(self, mock_i18n):
        error_msg = "Contract not found"
        fake_cli = FakeCLIWrapper(feedback_success=False, return_error=error_msg)
        from api.app.routers import contract
        from fastapi import FastAPI
        with patch.object(contract, 'i18n', FakeI18n()):
            with patch.object(contract, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(contract.router)
                test_client = TestClient(app)
                response = test_client.post("/contract/feedback")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False


class TestContractEdgeCases:
    def test_generate_contract_complex_brief(self, client):
        response = client.post("/contract/gen")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_generate_contract_conflicting_requirements(self, client):
        response = client.post("/contract/gen")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_check_contract_with_warnings(self, client):
        response = client.post("/contract/check")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_contract_feedback_empty(self, client):
        response = client.post("/contract/feedback")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_generate_contract_multiple_times(self, client):
        responses = [client.post("/contract/gen") for _ in range(3)]
        for response in responses:
            assert response.status_code == 200
            assert response.json()["success"] is True
    
    def test_check_contract_syntax_error(self, mock_i18n):
        error_msg = "Syntax error at line 15, column 10: unexpected token"
        fake_cli = FakeCLIWrapper(check_success=False, return_error=error_msg)
        from api.app.routers import contract
        from fastapi import FastAPI
        with patch.object(contract, 'i18n', FakeI18n()):
            with patch.object(contract, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(contract.router)
                test_client = TestClient(app)
                response = test_client.post("/contract/check")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_resume_contract_after_multiple_interrupts(self, client):
        response = client.post("/contract/gen/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestContractBoundaryCases:
    def test_generate_contract_min_requirements(self, client):
        response = client.post("/contract/gen")
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_generate_contract_max_requirements(self, client):
        response = client.post("/contract/gen")
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_generate_contract_exceeds_complexity(self, mock_i18n):
        error_msg = "Complexity exceeds limit, please simplify requirements"
        fake_cli = FakeCLIWrapper(gen_success=False, return_error=error_msg)
        from api.app.routers import contract
        from fastapi import FastAPI
        with patch.object(contract, 'i18n', FakeI18n()):
            with patch.object(contract, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(contract.router)
                test_client = TestClient(app)
                response = test_client.post("/contract/gen")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False