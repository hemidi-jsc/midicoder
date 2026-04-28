"""
Tests cho Init Command (E00, E01).

Test cases:
1. Test tạo cấu trúc thư mục .midicoder/
2. Test tạo global config ~/.midicoder/midicoder.json
3. Test tạo project config .midicoder/config/midicoder.yml
4. Test khởi tạo SQLite databases
5. Test kiểm tra Neo4j running
6. Test kiểm tra Docker installed
7. Test error handling khi workspace đã tồn tại
8. Test error handling khi không có quyền ghi
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from midicoder.pipeline.config import (
    DEFAULT_GLOBAL_CONFIG,
    ConfigError,
    ConfigManager,
    get_config,
    get_global_config_path,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_workspace():
    """
    Tạo temporary workspace cho testing.
    
    Yields:
        Path: Temporary directory path
    """
    # Tạo temp directory
    temp_dir = tempfile.mkdtemp()
    original_cwd = Path.cwd()
    
    # Chuyển sang temp directory
    os.chdir(temp_dir)
    
    yield Path(temp_dir)
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_home():
    """
    Tạo temporary home directory cho testing global config.
    
    Yields:
        Path: Temporary home directory path
    """
    # Lưu home cũ
    original_home = os.environ.get("HOME", "")
    
    # Tạo temp home
    temp_home = tempfile.mkdtemp()
    os.environ["HOME"] = temp_home
    
    yield Path(temp_home)
    
    # Cleanup
    if original_home:
        os.environ["HOME"] = original_home
    else:
        os.environ.pop("HOME", None)
    shutil.rmtree(temp_home, ignore_errors=True)


# ============================================================================
# Tests: Workspace Structure Creation
# ============================================================================

def test_create_workspace_structure_creates_directories(temp_workspace):
    """
    Test: Tạo cấu trúc thư mục .midicoder/ với các subdirectories.
    
    Expected:
    - .midicoder/config/ được tạo
    - .midicoder/data/ được tạo
    - .midicoder/versions/ được tạo
    - .midicoder/runtime/ được tạo
    - .midicoder/cache/ được tạo
    """
    from midicoder.pipeline.commands.init import _create_workspace_structure
    
    workspace_dir = temp_workspace / ".midicoder"
    
    _create_workspace_structure(workspace_dir)
    
    # Verify directories
    assert workspace_dir.exists()
    assert (workspace_dir / "config").exists()
    assert (workspace_dir / "data").exists()
    assert (workspace_dir / "versions").exists()
    assert (workspace_dir / "runtime").exists()
    assert (workspace_dir / "cache").exists()


def test_create_workspace_structure_no_error_on_existing(temp_workspace):
    """
    Test: Không lỗi khi workspace đã tồn tại (exist_ok=True).
    """
    from midicoder.pipeline.commands.init import _create_workspace_structure
    
    workspace_dir = temp_workspace / ".midicoder"
    
    # Tạo workspace lần 1
    _create_workspace_structure(workspace_dir)
    
    # Tạo lại không được lỗi
    _create_workspace_structure(workspace_dir)
    
    # Verify vẫn có các directories
    assert (workspace_dir / "config").exists()


# ============================================================================
# Tests: Global Config Creation
# ============================================================================

def test_ensure_global_config_creates_new_file(temp_home, temp_workspace):
    """
    Test: Tạo global config file mới khi chưa tồn tại.

    Expected:
    - File ~/.midicoder/midicoder.json được tạo
    - Chứa DEFAULT_GLOBAL_CONFIG
    - Có created_at và last_run timestamp
    """
    from midicoder.pipeline.commands.init import _ensure_global_config
    from midicoder.pipeline import config as config_module
    
    # Reset config singleton và xóa cache
    config_module._config_manager = None
    
    # Xóa config file cũ nếu có
    config_path = get_global_config_path()
    if config_path.exists():
        config_path.unlink()
    
    _ensure_global_config()
    
    config_path = get_global_config_path()
    
    # Verify file exists
    assert config_path.exists()
    
    # Verify content
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    
    assert "midicoder_version" in config_data
    assert config_data["midicoder_version"] == "1.0.0"
    assert "created_at" in config_data
    assert "last_run" in config_data
    assert "llm" in config_data
    assert "neo4j" in config_data
    assert "webgui" in config_data


def test_ensure_global_config_no_error_on_existing(temp_home, temp_workspace):
    """
    Test: Không lỗi khi global config đã tồn tại.
    """
    from midicoder.pipeline.commands.init import _ensure_global_config
    
    # Tạo config trước
    _ensure_global_config()
    
    # Gọi lại không được lỗi
    _ensure_global_config()


# ============================================================================
# Tests: Project Config Creation
# ============================================================================

def test_create_project_config_creates_file(temp_workspace):
    """
    Test: Tạo project config file .midicoder/config/midicoder.yml.
    
    Expected:
    - File .midicoder/config/midicoder.yml được tạo
    - Chứa cấu hình mặc định
    """
    from midicoder.pipeline.commands.init import _create_workspace_structure, _create_project_config
    
    workspace_dir = temp_workspace / ".midicoder"
    _create_workspace_structure(workspace_dir)
    
    _create_project_config(workspace_dir)
    
    config_file = workspace_dir / "config" / "midicoder.yml"
    
    # Verify file exists
    assert config_file.exists()
    
    # Verify content
    import yaml
    with open(config_file, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    
    assert config_data["version"] == "1.0.0"
    assert config_data["active_version"] == "v1.0.0"
    assert "capabilities" in config_data


# ============================================================================
# Tests: SQLite Database Initialization
# ============================================================================

def test_initialize_sqlite_databases_creates_all_dbs(temp_workspace):
    """
    Test: Khởi tạo tất cả SQLite databases.
    
    Expected:
    - briefs.db được tạo với schema briefs, clarifications, brief_lineage
    - artifacts.db được tạo với schema artifacts, activity_log
    - provenance.db được tạo với schema lineage, decisions
    - context.db được tạo với schema symbols
    """
    from midicoder.pipeline.commands.init import _initialize_sqlite_databases
    import sqlite3
    
    data_dir = temp_workspace / "data"
    data_dir.mkdir(parents=True)
    
    _initialize_sqlite_databases(data_dir)
    
    # Verify databases exist
    assert (data_dir / "briefs.db").exists()
    assert (data_dir / "artifacts.db").exists()
    assert (data_dir / "provenance.db").exists()
    assert (data_dir / "context.db").exists()
    
    # Verify briefs.db schema
    conn = sqlite3.connect(str(data_dir / "briefs.db"))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    assert "briefs" in tables
    assert "clarifications" in tables
    assert "brief_lineage" in tables


def test_initialize_sqlite_databases_no_error_on_existing(temp_workspace):
    """
    Test: Không lỗi khi databases đã tồn tại (CREATE TABLE IF NOT EXISTS).
    """
    from midicoder.pipeline.commands.init import _initialize_sqlite_databases
    
    data_dir = temp_workspace / "data"
    data_dir.mkdir(parents=True)
    
    # Init lần 1
    _initialize_sqlite_databases(data_dir)
    
    # Init lần 2 không được lỗi
    _initialize_sqlite_databases(data_dir)


# ============================================================================
# Tests: Neo4j Running Check
# ============================================================================

@patch("socket.socket")
def test_is_neo4j_running_returns_true_when_port_open(mock_socket_class, temp_workspace):
    """
    Test: Kiểm tra Neo4j đang chạy khi port 7687 mở.
    
    Expected:
    - connect_ex trả về 0 → True
    """
    from midicoder.pipeline.commands.init import _is_neo4j_running
    
    mock_socket = MagicMock()
    mock_socket.connect_ex.return_value = 0
    mock_socket_class.return_value = mock_socket
    
    result = _is_neo4j_running()
    
    assert result is True


@patch("socket.socket")
def test_is_neo4j_running_returns_false_when_port_closed(mock_socket_class, temp_workspace):
    """
    Test: Kiểm tra Neo4j không chạy khi port 7687 đóng.
    
    Expected:
    - connect_ex trả về != 0 → False
    """
    from midicoder.pipeline.commands.init import _is_neo4j_running
    
    mock_socket = MagicMock()
    mock_socket.connect_ex.return_value = 111  # Connection refused
    mock_socket_class.return_value = mock_socket
    
    result = _is_neo4j_running()
    
    assert result is False


@patch("socket.socket")
def test_is_neo4j_running_returns_false_on_exception(mock_socket_class, temp_workspace):
    """
    Test: Kiểm tra Neo4j trả về False khi có exception.
    """
    from midicoder.pipeline.commands.init import _is_neo4j_running
    
    mock_socket_class.side_effect = Exception("Connection error")
    
    result = _is_neo4j_running()
    
    assert result is False


# ============================================================================
# Tests: Docker Installed Check
# ============================================================================

@patch("subprocess.run")
def test_docker_installed_returns_true_when_docker_exists(mock_run, temp_workspace):
    """
    Test: Kiểm tra Docker đã cài đặt khi docker --version thành công.
    """
    from midicoder.pipeline.commands.init import _docker_installed
    
    mock_run.return_value = MagicMock(returncode=0)
    
    result = _docker_installed()
    
    assert result is True
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_docker_installed_returns_false_when_docker_not_found(mock_run, temp_workspace):
    """
    Test: Kiểm tra Docker trả về False khi không tìm thấy docker command.
    """
    from midicoder.pipeline.commands.init import _docker_installed
    
    mock_run.side_effect = FileNotFoundError("docker not found")
    
    result = _docker_installed()
    
    assert result is False


@patch("subprocess.run")
def test_docker_installed_returns_false_on_timeout(mock_run, temp_workspace):
    """
    Test: Kiểm tra Docker trả về False khi timeout.
    """
    from midicoder.pipeline.commands.init import _docker_installed
    
    from subprocess import TimeoutExpired
    
    mock_run.side_effect = TimeoutExpired("docker --version", 5)
    
    result = _docker_installed()
    
    assert result is False


# ============================================================================
# Tests: Full Init Flow
# ============================================================================

@patch("midicoder.pipeline.commands.init._ensure_neo4j_running")
@patch("midicoder.pipeline.commands.init._initialize_sqlite_databases")
@patch("midicoder.pipeline.commands.init._create_project_config")
@patch("midicoder.pipeline.commands.init._ensure_global_config")
@patch("midicoder.pipeline.commands.init._create_workspace_structure")
def test_run_init_executes_all_steps(
    mock_create_workspace,
    mock_ensure_global_config,
    mock_create_project_config,
    mock_init_sqlite,
    mock_ensure_neo4j,
    temp_workspace
):
    """
    Test: Chạy full init flow với tất cả các bước.
    
    Expected sequence:
    1. Create workspace structure
    2. Ensure global config
    3. Create project config
    4. Initialize SQLite databases
    5. Ensure Neo4j running
    """
    from midicoder.pipeline.commands.init import run_init
    import click
    
    # Run init
    with patch.object(click, "echo"):
        with patch.object(click, "prompt", return_value="n"):
            run_init()
    
    # Verify all steps were called
    mock_create_workspace.assert_called_once()
    mock_ensure_global_config.assert_called_once()
    mock_create_project_config.assert_called_once()
    mock_init_sqlite.assert_called_once()
    mock_ensure_neo4j.assert_called_once()


@patch("midicoder.pipeline.commands.init._ensure_neo4j_running")
@patch("midicoder.pipeline.commands.init._initialize_sqlite_databases")
@patch("midicoder.pipeline.commands.init._create_project_config")
@patch("midicoder.pipeline.commands.init._ensure_global_config")
def test_run_init_aborts_when_workspace_exists_and_user_declines(
    mock_ensure_global_config,
    mock_create_project_config,
    mock_init_sqlite,
    mock_ensure_neo4j,
    temp_workspace
):
    """
    Test: Hủy bỏ init khi workspace đã tồn tại và user từ chối overwrite.
    """
    from midicoder.pipeline.commands.init import run_init
    import click
    
    # Tạo workspace trước
    workspace_dir = temp_workspace / ".midicoder"
    workspace_dir.mkdir()
    
    # User declines overwrite
    with patch.object(click, "echo"):
        with patch.object(click, "prompt", return_value="n"):
            run_init()
    
    # Verify subsequent steps were NOT called
    mock_ensure_global_config.assert_not_called()
    mock_create_project_config.assert_not_called()
    mock_init_sqlite.assert_not_called()
    mock_ensure_neo4j.assert_not_called()


# ============================================================================
# Tests: Error Handling
# ============================================================================

def test_create_workspace_structure_handles_permission_error(temp_workspace):
    """
    Test: Xử lý lỗi khi không có quyền tạo directory.
    """
    from midicoder.pipeline.commands.init import _create_workspace_structure
    from midicoder.errors import MidicoderError
    
    # Tạo directory readonly
    workspace_dir = temp_workspace / ".midicoder"
    workspace_dir.mkdir()
    (workspace_dir / "config").mkdir()
    (workspace_dir / "config").chmod(0o444)  # Read-only
    
    # Cleanup on Windows
    try:
        _create_workspace_structure(workspace_dir)
    except PermissionError:
        pass
    finally:
        # Cleanup
        (workspace_dir / "config").chmod(0o755)
        shutil.rmtree(workspace_dir, ignore_errors=True)


# ============================================================================
# Tests: Config Integration
# ============================================================================

def test_config_manager_loads_default_global_config(temp_home, temp_workspace):
    """
    Test: ConfigManager tải default global config khi file chưa tồn tại.
    """
    from midicoder.pipeline.config import ConfigManager
    from midicoder.pipeline import config as config_module
    
    # Reset config singleton
    config_module._config_manager = None
    
    # Xóa config file cũ nếu có
    config_path = get_global_config_path()
    if config_path.exists():
        config_path.unlink()
    
    # Tạo workspace để project config có thể được tạo
    workspace_dir = temp_workspace / ".midicoder"
    (workspace_dir / "config").mkdir(parents=True)
    
    manager = ConfigManager()
    config = manager.load_global_config()
    
    assert config["midicoder_version"] == "1.0.0"
    assert config["llm"]["provider"] == "openai-compatible"


def test_config_manager_get_nested_value(temp_home, temp_workspace):
    """
    Test: ConfigManager lấy giá trị theo dot notation.
    """
    from midicoder.pipeline.config import ConfigManager
    
    # Tạo workspace để project config có thể được tạo
    workspace_dir = temp_workspace / ".midicoder"
    (workspace_dir / "config").mkdir(parents=True)
    
    manager = ConfigManager()
    manager.load_global_config()
    
    # Set value
    manager.set("cli.language", "en")
    
    # Get value
    value = manager.get("cli.language")
    
    assert value == "en"


def test_config_manager_reset_to_default(temp_home, temp_workspace):
    """
    Test: ConfigManager reset giá trị về default.
    """
    from midicoder.pipeline.config import ConfigManager
    
    # Tạo workspace để project config có thể được tạo
    workspace_dir = temp_workspace / ".midicoder"
    (workspace_dir / "config").mkdir(parents=True)
    
    manager = ConfigManager()
    manager.load_global_config()
    
    # Set custom value
    manager.set("cli.language", "en")
    
    # Reset
    manager.reset("cli.language")
    
    # Verify reset to default
    value = manager.get("cli.language")
    assert value == "vi"  # Default value
