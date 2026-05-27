"""
Tests cho WebGUI start functionality trong init command.

Mục tiêu: Test các functions liên quan đến việc khởi động WebGUI (Backend FastAPI + Frontend Angular)
theo requirement P1-001-F.

SoT Reference: E00 (Installation & Setup)
"""

import os
import socket
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from midicoder.pipeline.commands.init import (
    _build_angular,
    _check_nodejs_installed,
    _check_port_available,
    _check_uvicorn_installed,
    _get_pid_from_file,
    _is_process_running,
    _save_pid_to_file,
    _start_backend,
    _start_frontend,
    _start_webgui,
    _wait_for_port,
)


class TestDependencyChecks:
    """Test các hàm check dependencies."""

    def test_check_uvicorn_installed_success(self):
        """Test uvicorn đã được cài đặt."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = _check_uvicorn_installed()
            assert result is True

    def test_check_uvicorn_installed_not_found(self):
        """Test uvicorn chưa được cài đặt (FileNotFoundError)."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("uvicorn not found")
            result = _check_uvicorn_installed()
            assert result is False

    def test_check_uvicorn_installed_timeout(self):
        """Test uvicorn check timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("uvicorn", timeout=5)
            result = _check_uvicorn_installed()
            assert result is False

    def test_check_nodejs_installed_success(self):
        """Test Node.js đã được cài đặt."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = _check_nodejs_installed()
            assert result is True

    def test_check_nodejs_installed_not_found(self):
        """Test Node.js chưa được cài đặt."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("node not found")
            result = _check_nodejs_installed()
            assert result is False

    def test_check_port_available_true(self):
        """Test port đang available."""
        # Find an available port first
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            available_port = s.getsockname()[1]
        
        result = _check_port_available(available_port)
        assert result is True

    def test_check_port_available_false(self):
        """Test port đang bị chiếm."""
        # Start a server on a port and keep it listening
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 0))
        server.listen()
        occupied_port = server.getsockname()[1]
        
        # Check while server is still listening
        result = _check_port_available(occupied_port)
        assert result is False
        
        # Cleanup
        server.close()


class TestPidFileOperations:
    """Test các operations với PID files."""

    def test_save_pid_to_file(self, tmp_path):
        """Test lưu PID vào file."""
        pid_file = tmp_path / "test.pid"
        _save_pid_to_file(pid_file, 12345)
        
        assert pid_file.exists()
        assert pid_file.read_text().strip() == "12345"

    def test_get_pid_from_file_exists(self, tmp_path):
        """Test đọc PID từ file tồn tại."""
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("12345")
        
        pid = _get_pid_from_file(pid_file)
        assert pid == 12345

    def test_get_pid_from_file_not_exists(self, tmp_path):
        """Test đọc PID từ file không tồn tại."""
        pid_file = tmp_path / "nonexistent.pid"
        pid = _get_pid_from_file(pid_file)
        assert pid is None

    def test_get_pid_from_file_empty(self, tmp_path):
        """Test đọc PID từ file rỗng."""
        pid_file = tmp_path / "empty.pid"
        pid_file.write_text("")
        pid = _get_pid_from_file(pid_file)
        assert pid is None


class TestProcessRunning:
    """Test check process running."""

    def test_is_process_running_true(self):
        """Test process đang chạy."""
        # Start a background process
        if os.name == "nt":  # Windows
            process = subprocess.Popen(
                ["cmd", "/c", "ping", "-n", "3", "127.0.0.1"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:  # Unix
            process = subprocess.Popen(
                ["sleep", "3"],
                start_new_session=True
            )
        
        pid = process.pid
        time.sleep(0.5)  # Wait for process to start
        
        result = _is_process_running(pid)
        assert result is True
        
        # Cleanup
        process.terminate()
        process.wait(timeout=5)

    def test_is_process_running_false(self):
        """Test process không chạy."""
        # Use a very unlikely PID (40999 is a high PID unlikely to exist on most systems)
        result = _is_process_running(40999)
        assert result is False


class TestWaitForPort:
    """Test wait for port to be available."""

    def test_wait_for_port_success(self):
        """Test wait for port thành công."""
        # Start a simple HTTP server in background
        server_script = """
import http.server
import socketserver
import threading
import time

# Wait a bit before starting
time.sleep(0.5)

server = socketserver.TCPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler)
port = server.server_address[1]

# Run server in background
thread = threading.Thread(target=server.serve_forever)
thread.daemon = True
thread.start()

print(port)
"""
        result = subprocess.run(
            ["python", "-c", server_script],
            capture_output=True,
            text=True,
            timeout=5
        )
        port = int(result.stdout.strip())
        
        # Wait for port to be available
        success = _wait_for_port(port, timeout=5)
        assert success is True

    @patch("midicoder.pipeline.commands.init._check_port_available")
    def test_wait_for_port_timeout(self, mock_check):
        """Test wait for port timeout."""
        # Mock to always return False
        mock_check.return_value = False
        success = _wait_for_port(1, timeout=1)
        assert success is False


class TestBuildAngular:
    """Test Angular build."""

    def test_build_angular_success(self):
        """Test build Angular thành công."""
        with (
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.exists", return_value=True)
        ):
            mock_run.return_value.returncode = 0
            result = _build_angular(Path("webgui"))
            assert result is True

    def test_build_angular_failure(self):
        """Test build Angular thất bại."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            result = _build_angular(Path("webgui"))
            assert result is False

    def test_build_angular_timeout(self):
        """Test build Angular timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("ng", timeout=300)
            result = _build_angular(Path("webgui"))
            assert result is False


class TestStartBackend:
    """Test Backend FastAPI start."""

    def test_start_backend_success(self, tmp_path):
        """Test start Backend thành công."""
        runtime_dir = tmp_path / "runtime"
        runtime_dir.mkdir()
        
        # Mock uvicorn installed check
        with (
            patch("midicoder.pipeline.commands.init._check_uvicorn_installed", return_value=True),
            patch("midicoder.pipeline.commands.init._check_port_available", return_value=True),
            patch("midicoder.pipeline.commands.init._wait_for_port", return_value=True),
            patch("subprocess.Popen") as mock_popen,
        ):
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process
            
            result, pid = _start_backend(
                api_dir=Path("api"),
                runtime_dir=runtime_dir,
                host="localhost",
                port=6868
            )
            
            assert result is True
            assert pid == 12345
            # Check PID file was created
            assert (runtime_dir / "backend.pid").exists()

    def test_start_backend_uvicorn_not_installed(self, tmp_path):
        """Test start Backend khi uvicorn chưa cài đặt."""
        runtime_dir = tmp_path / "runtime"
        runtime_dir.mkdir()
        
        with (
            patch("midicoder.pipeline.commands.init._check_uvicorn_installed", return_value=False),
        ):
            result, pid = _start_backend(
                api_dir=Path("api"),
                runtime_dir=runtime_dir,
                host="localhost",
                port=6868
            )
            
            assert result is False
            assert pid is None

    def test_start_backend_port_in_use(self, tmp_path):
        """Test start Backend khi port đã bị chiếm."""
        runtime_dir = tmp_path / "runtime"
        runtime_dir.mkdir()
        
        with (
            patch("midicoder.pipeline.commands.init._check_uvicorn_installed", return_value=True),
            patch("midicoder.pipeline.commands.init._check_port_available", return_value=False),
        ):
            result, pid = _start_backend(
                api_dir=Path("api"),
                runtime_dir=runtime_dir,
                host="localhost",
                port=6868
            )
            
            assert result is False
            assert pid is None


class TestStartFrontend:
    """Test Frontend Angular start."""

    def test_start_frontend_success(self, tmp_path):
        """Test start Frontend thành công."""
        runtime_dir = tmp_path / "runtime"
        runtime_dir.mkdir()
        
        # Create mock dist folder
        webgui_dir = tmp_path / "webgui"
        dist_dir = webgui_dir / "dist" / "browser"
        dist_dir.mkdir(parents=True)
        (dist_dir / "index.html").write_text("<html></html>")
        
        with (
            patch("midicoder.pipeline.commands.init._check_nodejs_installed", return_value=True),
            patch("midicoder.pipeline.commands.init._build_angular", return_value=True),
            patch("midicoder.pipeline.commands.init._check_port_available", return_value=True),
            patch("midicoder.pipeline.commands.init._wait_for_port", return_value=True),
            patch("subprocess.Popen") as mock_popen,
            patch("builtins.open", MagicMock()),  # Mock file open for log file
        ):
            mock_process = MagicMock()
            mock_process.pid = 54321
            mock_popen.return_value = mock_process
            
            result, pid = _start_frontend(
                webgui_dir=webgui_dir,
                runtime_dir=runtime_dir,
                port=7272
            )
            
            assert result is True
            assert pid == 54321
            assert (runtime_dir / "frontend.pid").exists()

    def test_start_frontend_nodejs_not_installed(self, tmp_path):
        """Test start Frontend khi Node.js chưa cài đặt."""
        runtime_dir = tmp_path / "runtime"
        runtime_dir.mkdir()
        
        with (
            patch("midicoder.pipeline.commands.init._check_nodejs_installed", return_value=False),
        ):
            result, pid = _start_frontend(
                webgui_dir=Path("webgui"),
                runtime_dir=runtime_dir,
                port=7272
            )
            
            assert result is False
            assert pid is None

    def test_start_frontend_build_failure(self, tmp_path):
        """Test start Frontend khi build thất bại."""
        runtime_dir = tmp_path / "runtime"
        runtime_dir.mkdir()
        
        with (
            patch("midicoder.pipeline.commands.init._check_nodejs_installed", return_value=True),
            patch("midicoder.pipeline.commands.init._build_angular", return_value=False),
        ):
            result, pid = _start_frontend(
                webgui_dir=Path("webgui"),
                runtime_dir=runtime_dir,
                port=7272
            )
            
            assert result is False
            assert pid is None


class TestStartWebgui:
    """Test _start_webgui main function."""

    def test_start_webgui_success(self, tmp_path):
        """Test start WebGUI thành công."""
        workspace_dir = tmp_path / ".midicoder"
        runtime_dir = workspace_dir / "runtime"
        runtime_dir.mkdir(parents=True)
        
        with (
            patch("midicoder.pipeline.commands.init._start_backend", return_value=(True, 12345)),
            patch("midicoder.pipeline.commands.init._start_frontend", return_value=(True, 54321)),
            patch("midicoder.pipeline.commands.init._open_browser") as mock_browser,
            patch("midicoder.pipeline.commands.init.get_config") as mock_config,
        ):
            mock_config.return_value.get = MagicMock(side_effect=lambda key, default=None: {
                "webgui.auto_start": True,
                "webgui.open_browser": True,
            }.get(key, default))
            
            _start_webgui(workspace_dir)
            
            mock_browser.assert_called_once_with("http://localhost:7272")

    def test_start_webgui_skip_if_already_running(self, tmp_path):
        """Test skip start nếu WebGUI đã đang chạy."""
        workspace_dir = tmp_path / ".midicoder"
        runtime_dir = workspace_dir / "runtime"
        runtime_dir.mkdir(parents=True)
        
        # Create PID files with existing PIDs
        (runtime_dir / "backend.pid").write_text("12345")
        (runtime_dir / "frontend.pid").write_text("54321")
        
        with (
            patch("midicoder.pipeline.commands.init._is_process_running", return_value=True),
            patch("midicoder.pipeline.commands.init._start_backend") as mock_backend,
            patch("midicoder.pipeline.commands.init._start_frontend") as mock_frontend,
        ):
            _start_webgui(workspace_dir)
            
            mock_backend.assert_not_called()
            mock_frontend.assert_not_called()

    def test_start_webgui_backend_failure(self, tmp_path):
        """Test start WebGUI khi Backend start thất bại."""
        workspace_dir = tmp_path / ".midicoder"
        runtime_dir = workspace_dir / "runtime"
        runtime_dir.mkdir(parents=True)
        
        # Create mock api directory
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        
        with (
            patch("pathlib.Path.cwd", return_value=tmp_path),
            patch("midicoder.pipeline.commands.init._start_backend", return_value=(False, None)),
            patch("midicoder.pipeline.commands.init._start_frontend") as mock_frontend,
            patch("midicoder.pipeline.commands.init._open_browser") as mock_browser,
            patch("midicoder.pipeline.commands.init.get_config") as mock_config,
        ):
            mock_config.return_value.get = MagicMock(side_effect=lambda key, default=None: {
                "webgui.auto_start": True,
                "webgui.open_browser": True,
            }.get(key, default))
            
            _start_webgui(workspace_dir)
            
            # When backend fails, frontend should NOT be called (we return early)
            mock_frontend.assert_not_called()
            mock_browser.assert_not_called()

    def test_start_webgui_frontend_failure(self, tmp_path):
        """Test start WebGUI khi Frontend start thất bại."""
        workspace_dir = tmp_path / ".midicoder"
        runtime_dir = workspace_dir / "runtime"
        runtime_dir.mkdir(parents=True)
        
        with (
            patch("midicoder.pipeline.commands.init._start_backend", return_value=(True, 12345)),
            patch("midicoder.pipeline.commands.init._start_frontend", return_value=(False, None)),
            patch("midicoder.pipeline.commands.init._open_browser") as mock_browser,
        ):
            _start_webgui(workspace_dir)
            
            mock_browser.assert_not_called()

    def test_start_webgui_no_browser_open(self, tmp_path):
        """Test start WebGUI không mở browser (config disabled)."""
        workspace_dir = tmp_path / ".midicoder"
        runtime_dir = workspace_dir / "runtime"
        runtime_dir.mkdir(parents=True)
        
        with (
            patch("midicoder.pipeline.commands.init._start_backend", return_value=(True, 12345)),
            patch("midicoder.pipeline.commands.init._start_frontend", return_value=(True, 54321)),
            patch("midicoder.pipeline.commands.init._open_browser") as mock_browser,
            patch("midicoder.pipeline.commands.init.get_config") as mock_config,
        ):
            mock_config.return_value.get = MagicMock(side_effect=lambda key, default=None: {
                "webgui.auto_start": True,
                "webgui.open_browser": False,
            }.get(key, default))
            
            _start_webgui(workspace_dir)
            
            mock_browser.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])