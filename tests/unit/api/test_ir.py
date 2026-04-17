"""
Unit tests cho IR Router
Chuyển đổi từ BDD: tests/features/api/ir.feature
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


class FakeCLIWrapper:
    def __init__(self, build_success=True, return_error=None):
        self.build_success = build_success
        self.return_error = return_error
    
    async def ir_build(self, skip_diagrams: bool = False) -> dict:
        if self.build_success:
            return {"success": True, "stdout": f"IR built (skip_diagrams={skip_diagrams})", "stderr": ""}
        return {"success": False, "stdout": "", "stderr": self.return_error or "Build failed"}


class FakeI18n:
    def __init__(self):
        self.translations = {
            "vi": {
                "ir.build_success": "Đã xây dựng MIR thành công",
                "common.success": "Thành công",
            },
            "en": {
                "ir.build_success": "MIR built successfully",
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
    from api.app.routers import ir
    with patch.object(ir, 'i18n', fake_i18n):
        yield fake_i18n


@pytest.fixture
def client(mock_i18n):
    from api.app.routers import ir
    from fastapi import FastAPI
    fake_cli = FakeCLIWrapper(build_success=True)
    with patch.object(ir, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(ir.router)
        yield TestClient(app)


@pytest.fixture
def failing_client(mock_i18n):
    from api.app.routers import ir
    from fastapi import FastAPI
    fake_cli = FakeCLIWrapper(build_success=False, return_error="Test error")
    with patch.object(ir, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(ir.router)
        yield TestClient(app)


class TestBuildIR:
    def test_build_ir_success(self, client):
        response = client.post("/ir/build")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["built"] is True
        assert "mir_path" in data["data"]
        assert "symbol_table_path" in data["data"]
    
    def test_build_ir_with_diagrams(self, client):
        payload = {"skip_diagrams": False}
        response = client.post("/ir/build", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["built"] is True
    
    def test_build_ir_returns_file_paths(self, client):
        response = client.post("/ir/build")
        data = response.json()
        assert "mir_path" in data["data"]
        assert "mir.json" in data["data"]["mir_path"]
        assert "symbol_table_path" in data["data"]
        assert "symbol-table.json" in data["data"]["symbol_table_path"]


class TestBuildIRNegativeCases:
    def test_build_ir_no_contract(self, mock_i18n):
        error_msg = "Contract not found"
        fake_cli = FakeCLIWrapper(build_success=False, return_error=error_msg)
        from api.app.routers import ir
        from fastapi import FastAPI
        with patch.object(ir, 'i18n', FakeI18n()):
            with patch.object(ir, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(ir.router)
                test_client = TestClient(app)
                response = test_client.post("/ir/build")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_build_ir_invalid_contract(self, mock_i18n):
        error_msg = "Invalid contract format"
        fake_cli = FakeCLIWrapper(build_success=False, return_error=error_msg)
        from api.app.routers import ir
        from fastapi import FastAPI
        with patch.object(ir, 'i18n', FakeI18n()):
            with patch.object(ir, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(ir.router)
                test_client = TestClient(app)
                response = test_client.post("/ir/build")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_build_ir_contract_not_checked(self, mock_i18n):
        error_msg = "Contract not checked"
        fake_cli = FakeCLIWrapper(build_success=False, return_error=error_msg)
        from api.app.routers import ir
        from fastapi import FastAPI
        with patch.object(ir, 'i18n', FakeI18n()):
            with patch.object(ir, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(ir.router)
                test_client = TestClient(app)
                response = test_client.post("/ir/build")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_build_ir_cli_error(self, mock_i18n):
        error_msg = "CLI system error: process failed"
        fake_cli = FakeCLIWrapper(build_success=False, return_error=error_msg)
        from api.app.routers import ir
        from fastapi import FastAPI
        with patch.object(ir, 'i18n', FakeI18n()):
            with patch.object(ir, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(ir.router)
                test_client = TestClient(app)
                response = test_client.post("/ir/build")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False


class TestBuildIREdgeCases:
    def test_build_ir_with_null_request(self, client):
        response = client.post("/ir/build")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_build_ir_skip_diagrams(self, client):
        payload = {"skip_diagrams": True}
        response = client.post("/ir/build", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["built"] is True
    
    def test_build_ir_multiple_times(self, client):
        responses = [client.post("/ir/build") for _ in range(3)]
        for response in responses:
            assert response.status_code == 200
            assert response.json()["success"] is True
    
    def test_build_ir_with_different_languages(self, client):
        response_vi = client.post("/ir/build")
        response_en = client.post("/ir/build", headers={"X-Lang": "en"})
        assert response_vi.json()["message"] == "Đã xây dựng MIR thành công"
        assert response_en.json()["message"] == "MIR built successfully"


class TestBuildIRBoundaryCases:
    def test_build_ir_response_structure(self, client):
        response = client.post("/ir/build")
        data = response.json()
        assert data["success"] is True
        assert data["data"]["built"] is True
        assert isinstance(data["data"]["mir_path"], str)
        assert isinstance(data["data"]["symbol_table_path"], str)
        assert len(data["data"]["mir_path"]) > 0
        assert len(data["data"]["symbol_table_path"]) > 0
    
    def test_build_ir_error_response_structure(self, mock_i18n):
        error_msg = "Build failed"
        fake_cli = FakeCLIWrapper(build_success=False, return_error=error_msg)
        from api.app.routers import ir
        from fastapi import FastAPI
        with patch.object(ir, 'i18n', FakeI18n()):
            with patch.object(ir, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(ir.router)
                test_client = TestClient(app)
                response = test_client.post("/ir/build")
                data = response.json()
                assert data["success"] is False
                assert "message" in data
                assert len(data["message"]) > 0
    
    def test_build_ir_with_empty_request(self, client):
        response = client.post("/ir/build", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_build_ir_with_invalid_skip_diagrams_type(self, client):
        response = client.post("/ir/build", json={"skip_diagrams": "true"})
        # API may accept string "true" and convert it, or return 200
        assert response.status_code in [200, 422]
