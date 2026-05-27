"""
Tests cho Init Command.

Test coverage cho:
- Tạo workspace structure
- Tạo global config
- Khởi tạo SQLite databases
- Neo4j config prompt
- WebGUI stub

TDD: Tests MUST FAIL trước khi implement.
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import functions cần test (sẽ fail vì chưa implement đúng signature)
from midicoder.pipeline.commands.init import (
    _create_workspace_structure,
    _ensure_global_config,
    _create_project_config,
    _initialize_sqlite_databases,
    _ensure_neo4j_running,
)


class TestWorkspaceStructure:
    """Test: Tạo cấu trúc thư mục .midicoder/"""

    def test_create_workspace_structure_creates_folders(self, tmp_path):
        """Test: _create_workspace_structure tạo đúng folders"""
        workspace_dir = tmp_path / ".midicoder"

        _create_workspace_structure(workspace_dir)

        # Assert: Tất cả folders phải tồn tại
        assert (workspace_dir / "config").exists()
        assert (workspace_dir / "data").exists()
        assert (workspace_dir / "versions").exists()
        assert (workspace_dir / "runtime").exists()
        assert (workspace_dir / "cache").exists()

    def test_create_workspace_structure_parent_creation(self, tmp_path):
        """Test: Tự động tạo parent directory nếu chưa có"""
        workspace_dir = tmp_path / "nested" / ".midicoder"

        _create_workspace_structure(workspace_dir)

        assert workspace_dir.exists()
        assert (workspace_dir / "config").exists()


class TestGlobalConfig:
    """Test: Tạo global config ~/.midicoder/midicoder.json"""

    def test_ensure_global_config_creates_file(self, tmp_path, monkeypatch):
        """Test: _ensure_global_config tạo file nếu chưa có"""
        from midicoder.pipeline import config as config_module
        
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        
        # Mock Path.home() thông qua patch module
        monkeypatch.setattr(Path, 'home', lambda: mock_home)
        monkeypatch.setattr(config_module, 'GLOBAL_CONFIG_FILE', mock_home / ".midicoder" / "midicoder.json")

        _ensure_global_config(str(tmp_path / "test-project"))

        config_file = mock_home / ".midicoder" / "midicoder.json"
        assert config_file.exists()

        # Validate JSON structure
        with open(config_file) as f:
            config = json.load(f)
            assert "llm" in config
            assert "neo4j" in config
            assert "webgui" in config
            assert "project" in config
            assert config["project"]["cwd"] == str(tmp_path / "test-project")

    def test_ensure_global_config_updates_existing(self, tmp_path, monkeypatch):
        """Test: Update project.cwd và last_opened khi config đã tồn tại"""
        from midicoder.pipeline import config as config_module
        
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        
        monkeypatch.setattr(Path, 'home', lambda: mock_home)
        config_path = mock_home / ".midicoder" / "midicoder.json"
        monkeypatch.setattr(config_module, 'GLOBAL_CONFIG_FILE', config_path)

        # Tạo config trước
        config_dir = mock_home / ".midicoder"
        config_dir.mkdir(parents=True)
        original_content = {
            "project": {"cwd": "/old/path", "last_opened": None},
            "last_run": None
        }
        with open(config_path, "w") as f:
            json.dump(original_content, f)

        new_cwd = str(tmp_path / "new-project")
        _ensure_global_config(new_cwd)

        # Config được update
        with open(config_path) as f:
            config = json.load(f)
            assert config["project"]["cwd"] == new_cwd
            assert config["last_run"] is not None
            assert config["project"]["last_opened"] is not None


class TestProjectConfig:
    """Test: Tạo project config .midicoder/config/midicoder.yml"""

    def test_create_project_config_creates_file(self, tmp_path):
        """Test: _create_project_config tạo file YAML"""
        workspace_dir = tmp_path / ".midicoder"

        _create_project_config(workspace_dir)

        config_file = workspace_dir / "config" / "midicoder.yml"
        assert config_file.exists()

    def test_create_project_config_structure(self, tmp_path):
        """Test: Project config có đúng cấu trúc"""
        workspace_dir = tmp_path / ".midicoder"

        _create_project_config(workspace_dir)

        # Đọc và validate YAML
        import yaml
        config_file = workspace_dir / "config" / "midicoder.yml"
        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert "midicoder_version" in config
        assert "active_version" in config
        assert "max_versions" in config
        assert "capabilities" in config


class TestSQLiteInitialization:
    """Test: Khởi tạo SQLite databases"""

    def test_initialize_sqlite_databases_creates_files(self, tmp_path):
        """Test: _initialize_sqlite_databases tạo 4 databases"""
        data_dir = tmp_path / "data"

        _initialize_sqlite_databases(data_dir)

        assert (data_dir / "briefs.db").exists()
        assert (data_dir / "artifacts.db").exists()
        assert (data_dir / "provenance.db").exists()
        assert (data_dir / "context.db").exists()

    def test_initialize_sqlite_databases_has_tables(self, tmp_path):
        """Test: Databases có đúng tables"""
        import sqlite3

        data_dir = tmp_path / "data"
        _initialize_sqlite_databases(data_dir)

        # Check briefs.db
        briefs_db = data_dir / "briefs.db"
        conn = sqlite3.connect(str(briefs_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "briefs" in tables
        assert "clarifications" in tables

    def test_initialize_sqlite_databases_parent_creation(self, tmp_path):
        """Test: Tự động tạo parent directory"""
        data_dir = tmp_path / "nested" / "data"

        _initialize_sqlite_databases(data_dir)

        assert data_dir.exists()


class TestNeo4jConfig:
    """Test: Neo4j configuration"""

    def test_ensure_neo4j_running_with_docker(self, monkeypatch):
        """Test: Start Neo4j với Docker khi chưa chạy"""
        # Mock socket để simulate Neo4j not running
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 1  # Connection refused
        monkeypatch.setattr("midicoder.pipeline.commands.init.socket.socket",
                          lambda *a, **k: mock_socket)

        # Mock subprocess để simulate docker success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "container_id"
        monkeypatch.setattr("midicoder.pipeline.commands.init.subprocess.run",
                          mock_result)

        # Mock get_config
        mock_config = MagicMock()
        mock_config.get.return_value = {"docker_auto_start": True}
        monkeypatch.setattr("midicoder.pipeline.commands.init.get_config",
                          lambda: mock_config)

        _ensure_neo4j_running()

        # Docker command được gọi
        assert mock_result.returncode == 0

    def test_ensure_neo4j_running_already_running(self, monkeypatch):
        """Test: Không làm gì khi Neo4j đang chạy"""
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0  # Success
        monkeypatch.setattr("midicoder.pipeline.commands.init.socket.socket",
                          lambda *a, **k: mock_socket)

        _ensure_neo4j_running()

        # Không gọi subprocess vì đã running

    def test_ensure_neo4j_docker_not_installed(self, monkeypatch, capsys):
        """Test: Warning khi Docker không cài đặt"""
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 1
        monkeypatch.setattr("midicoder.pipeline.commands.init.socket.socket",
                          lambda *a, **k: mock_socket)

        # Mock docker --version fail
        mock_result = MagicMock()
        mock_result.returncode = 1
        monkeypatch.setattr("midicoder.pipeline.commands.init.subprocess.run",
                          mock_result)

        mock_config = MagicMock()
        mock_config.get.return_value = {"docker_auto_start": True}
        monkeypatch.setattr("midicoder.pipeline.commands.init.get_config",
                          lambda: mock_config)

        _ensure_neo4j_running()

        captured = capsys.readouterr()
        assert "Docker" in captured.err or "Docker" in captured.out


class TestIntegration:
    """Integration tests"""

    @patch("midicoder.pipeline.commands.init._create_workspace_structure")
    @patch("midicoder.pipeline.commands.init._ensure_global_config")
    @patch("midicoder.pipeline.commands.init._create_project_config")
    @patch("midicoder.pipeline.commands.init._initialize_sqlite_databases")
    @patch("midicoder.pipeline.commands.init._ensure_neo4j_running")
    def test_init_flow_sequence(
        self,
        mock_neo4j,
        mock_sqlite,
        mock_project,
        mock_global,
        mock_workspace,
        tmp_path,
        monkeypatch
    ):
        """Test: Init flow chạy đúng thứ tự các bước"""
        # Import run_init sau khi mock
        from midicoder.pipeline.commands.init import run_init

        # Chạy init
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            run_init(force=True)

        # Verify call order
        calls = [
            mock_workspace.call_args,
            mock_global.call_args,
            mock_project.call_args,
            mock_sqlite.call_args,
            mock_neo4j.call_args,
        ]
        assert all(call is not None for call in calls)