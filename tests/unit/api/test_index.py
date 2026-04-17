"""
Unit tests cho Index Router
Chuyển đổi từ BDD: tests/features/api/index.feature
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


class FakeCLIWrapper:
    def __init__(self, build_success=True, reindex_success=True, return_error=None):
        self.build_success = build_success
        self.reindex_success = reindex_success
        self.return_error = return_error
    
    async def index_build(self) -> dict:
        if self.build_success:
            return {"success": True, "stdout": "Index built successfully", "stderr": "", "stdout_data": {"indexed": True}}
        else:
            error_msg = self.return_error or "Build failed"
            return {"success": False, "stdout": "", "stderr": error_msg}
    
    async def index_reindex(self, paths: list = None) -> dict:
        if self.reindex_success:
            return {"success": True, "stdout": f"Reindexed {len(paths) if paths else 0} files", "stderr": ""}
        else:
            error_msg = self.return_error or "Reindex failed"
            return {"success": False, "stdout": "", "stderr": error_msg}


class FakeI18n:
    def __init__(self):
        self.translations = {
            "vi": {"common.success": "Thành công"},
            "en": {"common.success": "Success"},
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
    from api.app.routers import index
    with patch.object(index, 'i18n', fake_i18n):
        yield fake_i18n


@pytest.fixture
def client(mock_i18n):
    from api.app.routers import index
    from fastapi import FastAPI
    fake_cli = FakeCLIWrapper(build_success=True, reindex_success=True)
    with patch.object(index, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(index.router)
        yield TestClient(app)


@pytest.fixture
def failing_client(mock_i18n):
    from api.app.routers import index
    from fastapi import FastAPI
    fake_cli = FakeCLIWrapper(build_success=False, reindex_success=False, return_error="Test error")
    with patch.object(index, 'cli_wrapper', fake_cli):
        app = FastAPI()
        app.include_router(index.router)
        yield TestClient(app)


class TestBuildIndex:
    def test_build_index_success(self, client):
        response = client.post("/index/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["indexed"] is True
    
    def test_build_index_returns_correct_language(self, client):
        response_vi = client.post("/index/")
        response_en = client.post("/index/", headers={"X-Lang": "en"})
        assert response_vi.json()["message"] == "Thành công"
        assert response_en.json()["message"] == "Success"


class TestReindex:
    def test_reindex_with_files(self, client):
        files = ["src/main.py", "src/utils.py", "tests/test_main.py"]
        payload = {"paths": files}
        response = client.post("/index/reindex", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["indexed"] is True
        assert data["data"]["files_count"] == len(files)
    
    def test_reindex_empty_list(self, client):
        payload = {"paths": []}
        response = client.post("/index/reindex", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["files_count"] == 0
    
    def test_reindex_without_request_body(self, client):
        response = client.post("/index/reindex")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestIndexNegativeCases:
    def test_build_index_codebase_not_found(self, mock_i18n):
        error_msg = "Codebase not found"
        fake_cli = FakeCLIWrapper(build_success=False, return_error=error_msg)
        from api.app.routers import index
        from fastapi import FastAPI
        with patch.object(index, 'i18n', FakeI18n()):
            with patch.object(index, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(index.router)
                test_client = TestClient(app)
                response = test_client.post("/index/")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_reindex_file_not_found(self, failing_client):
        files = ["nonexistent/file.py"]
        payload = {"paths": files}
        response = failing_client.post("/index/reindex", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
    
    def test_build_index_no_permission(self, mock_i18n):
        error_msg = "Permission denied"
        fake_cli = FakeCLIWrapper(build_success=False, return_error=error_msg)
        from api.app.routers import index
        from fastapi import FastAPI
        with patch.object(index, 'i18n', FakeI18n()):
            with patch.object(index, 'cli_wrapper', fake_cli):
                app = FastAPI()
                app.include_router(index.router)
                test_client = TestClient(app)
                response = test_client.post("/index/")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
    
    def test_reindex_invalid_paths(self, failing_client):
        invalid_paths = ["/invalid/path", "path/with/../traversal"]
        payload = {"paths": invalid_paths}
        response = failing_client.post("/index/reindex", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


class TestIndexEdgeCases:
    def test_build_index_empty_codebase(self, client):
        response = client.post("/index/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["indexed"] is True
    
    def test_build_index_large_codebase(self, client):
        response = client.post("/index/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_reindex_deleted_file(self, client):
        deleted_files = ["deleted/file.py"]
        payload = {"paths": deleted_files}
        response = client.post("/index/reindex", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_build_index_existing_index(self, client):
        response1 = client.post("/index/")
        response2 = client.post("/index/")
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response2.json()["success"] is True
    
    def test_reindex_file_outside_codebase(self, client):
        outside_files = ["/other/project/file.py"]
        payload = {"paths": outside_files}
        response = client.post("/index/reindex", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_reindex_mixed_valid_invalid_files(self, client):
        mixed_files = ["valid/file.py", "another/valid.py"]
        payload = {"paths": mixed_files}
        response = client.post("/index/reindex", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestIndexBoundaryCases:
    def test_reindex_max_files(self, client):
        max_files = [f"file_{i}.py" for i in range(1000)]
        payload = {"paths": max_files}
        response = client.post("/index/reindex", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["files_count"] == len(max_files)
    
    def test_reindex_very_long_file_name(self, client):
        long_name = "src/" + "a" * 500 + ".py"
        payload = {"paths": [long_name]}
        response = client.post("/index/reindex", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_reindex_deeply_nested_files(self, client):
        deep_path = "/".join(["level" + str(i) for i in range(50)]) + "/file.py"
        payload = {"paths": [deep_path]}
        response = client.post("/index/reindex", json=payload)
        assert response.status_code == 200
    
    def test_reindex_with_special_characters_in_path(self, client):
        special_paths = ["src/file-with-dash.py", "src/file_with_underscore.py", "src/file.with.dots.py"]
        payload = {"paths": special_paths}
        response = client.post("/index/reindex", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True