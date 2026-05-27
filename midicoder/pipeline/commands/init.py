"""
Init Command Implementation.

Lệnh `midicoder init` khởi tạo workspace Midicoder theo SoT E00-E01.

Thực hiện:
1. Tạo cấu trúc thư mục `.midicoder/`
2. Tạo global config `~/.midicoder/midicoder.json` nếu chưa có
3. Khởi tạo SQLite databases trong `.midicoder/data/`
4. Start Neo4j Docker container (nếu chưa chạy)
5. Start WebGUI (FastAPI + Angular)
6. Mở browser đến http://localhost:7272

SoT Reference: E00, E01
"""

import json
import os
import socket
import subprocess
import sys
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Tuple

import click

from midicoder.pipeline.config import get_config, get_global_config_path, DEFAULT_GLOBAL_CONFIG

# Constants cho WebGUI ports
WEBGUI_BACKEND_PORT = 6868
WEBGUI_FRONTEND_PORT = 7272

# Windows process flags
if sys.platform == "win32":
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    DETACHED_PROCESS = 0x00000008
else:
    CREATE_NEW_PROCESS_GROUP = 0
    DETACHED_PROCESS = 0


def run_init(
    force: bool = False,
    version: str = "v1.0.0"
) -> None:
    """
    Khởi tạo Midicoder workspace.

    Theo SoT E00, lệnh này thực hiện:
    1. Tạo .midicoder/ directory structure
    2. Tạo global config ~/.midicoder/midicoder.json nếu chưa có
    3. Khởi tạo SQLite databases
    4. Start Neo4j Docker container
    5. Start WebGUI
    6. Mở browser

    Args:
        force: Ghi đè .midicoder/ nếu đã tồn tại (không hỏi confirm)
        version: Version ban đầu cho project (ví dụ: v1.0.0)

    Raises:
        Exception: Nếu bước nào đó thất bại
    """
    click.echo("🚀 Khởi tạo Midicoder workspace...")

    # Lưu current working directory để update vào config
    current_cwd = str(Path.cwd().resolve())

    # Bước 1: Kiểm tra workspace đã tồn tại chưa
    workspace_dir = Path.cwd() / ".midicoder"
    if workspace_dir.exists():
        if force:
            click.echo("⚠️  Workspace đã tồn tại, ghi đè với --force.")
        else:
            click.echo("⚠️  Workspace đã tồn tại.")
            click.echo("💡 Sử dụng 'init --force' để ghi đè workspace cũ.")
            click.echo("❌ Hủy bỏ.")
            return

    # Bước 2: Tạo cấu trúc thư mục
    click.echo("📁 Tạo cấu trúc thư mục...")
    _create_workspace_structure(workspace_dir)

    # Bước 3: Khởi tạo global config và update project.cwd
    click.echo("⚙️  Khởi tạo global config...")
    _ensure_global_config(current_cwd)

    # Bước 4: Khởi tạo project config
    click.echo("📋 Khởi tạo project config...")
    _create_project_config(workspace_dir, version)

    # Bước 5: Khởi tạo SQLite databases
    click.echo("💾 Khởi tạo SQLite databases...")
    _initialize_sqlite_databases(workspace_dir / "data")

    # Bước 6: Kiểm tra và start Neo4j
    click.echo("🔍 Kiểm tra Neo4j...")
    _ensure_neo4j_running()

    # Bước 7: Start WebGUI
    click.echo("🌐 Khởi động WebGUI...")
    _start_webgui()

    # Xong
    click.echo("")
    click.echo("✅ Workspace được khởi tạo thành công!")
    click.echo("")
    click.echo("Tiếp theo:")
    click.echo("  1. Tạo brief.md để mô tả yêu cầu")
    click.echo("  2. Chạy: midicoder brief analyze")
    click.echo("  3. Chạy: midicoder contract gen")


def _create_workspace_structure(workspace_dir: Path) -> None:
    """
    Tạo cấu trúc thư mục .midicoder/ theo E01.

    Args:
        workspace_dir: Đường dẫn đến .midicoder/

    Cấu trúc:
        .midicoder/
        ├── config/
        ├── data/
        ├── versions/
        ├── runtime/
        └── cache/
    """
    folders = [
        workspace_dir / "config",
        workspace_dir / "data",
        workspace_dir / "versions",
        workspace_dir / "runtime",
        workspace_dir / "cache",
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
        click.echo(f"   ✓ {folder.relative_to(workspace_dir.parent)}")


def _ensure_global_config(current_cwd: str) -> None:
    """
    Đảm bảo global config file tồn tại và update project info.

    Tạo ~/.midicoder/midicoder.json nếu chưa có.
    Update project.cwd và project.last_opened mỗi khi init.

    Args:
        current_cwd: Đường dẫn project hiện tại
    """
    config_path = get_global_config_path()
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if not config_path.exists():
        config_dir = config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)

        config_data = DEFAULT_GLOBAL_CONFIG.copy()
        config_data["created_at"] = now
        config_data["last_run"] = now
        config_data["project"]["cwd"] = current_cwd
        config_data["project"]["last_opened"] = now

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        click.echo(f"   ✓ Global config: {config_path}")
        click.echo(f"   ✓ Project directory: {current_cwd}")
    else:
        # Update project.cwd và last_opened mỗi khi init
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        config_data["last_run"] = now
        config_data["project"]["cwd"] = current_cwd
        config_data["project"]["last_opened"] = now

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        click.echo(f"   ✓ Global config: {config_path}")
        click.echo(f"   ✓ Updated project directory: {current_cwd}")


def _create_project_config(workspace_dir: Path, version: str = "v1.0.0") -> None:
    """
    Tạo project config file theo SoT E01.

    Args:
        workspace_dir: Đường dẫn đến .midicoder/
        version: Version ban đầu cho project

    Tạo file: .midicoder/config/midicoder.yml
    """
    import yaml

    config_file = workspace_dir / "config" / "midicoder.yml"
    
    # Tạo parent directory nếu chưa có
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    config_data = {
        "midicoder_version": "1.0.0",
        "created_at": now,
        "active_version": version,
        "max_versions": 5,  # Auto-cleanup khi vượt quá
        "capabilities": {
            "enabled": [],  # Ví dụ: CP01, CP02, CP03
        },
    }

    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

    click.echo(f"   ✓ Project config: {config_file}")


def _initialize_sqlite_databases(data_dir: Path) -> None:
    """
    Khởi tạo SQLite databases theo E09.

    Args:
        data_dir: Đường dẫn đến .midicoder/data/

    Tạo các databases:
        - briefs.db        # Brief library + clarifications
        - artifacts.db     # Artifacts + activity_log
        - provenance.db    # Lineage + decisions
        - context.db       # Codebase index
    """
    # Import SQLite module
    from midicoder.storage.sqlite import (
        init_database,
        SCHEMA_BRIEFS,
        SCHEMA_ARTIFACTS,
        SCHEMA_ACTIVITY,
        SCHEMA_PROVENANCE,
        SCHEMA_CONTEXT,
    )

    # Briefs database
    briefs_db = data_dir / "briefs.db"
    init_database(briefs_db, SCHEMA_BRIEFS)
    click.echo(f"   ✓ {briefs_db.name}")

    # Artifacts database (bao gồm activity_log)
    artifacts_db = data_dir / "artifacts.db"
    artifacts_schema = SCHEMA_ARTIFACTS + SCHEMA_ACTIVITY
    init_database(artifacts_db, artifacts_schema)
    click.echo(f"   ✓ {artifacts_db.name}")

    # Provenance database
    provenance_db = data_dir / "provenance.db"
    init_database(provenance_db, SCHEMA_PROVENANCE)
    click.echo(f"   ✓ {provenance_db.name}")

    # Context database (codebase index)
    context_db = data_dir / "context.db"
    init_database(context_db, SCHEMA_CONTEXT)
    click.echo(f"   ✓ {context_db.name}")


def _ensure_neo4j_running() -> None:
    """
    Kiểm tra và start Neo4j nếu cần.

    Theo config neo4j.docker_auto_start

    Neo4j là dependency bắt buộc cho Midicoder.
    Nếu không thể start, hiển thị hướng dẫn chi tiết.
    """
    config = get_config()
    neo4j_config = config.get("neo4j", {})

    if not neo4j_config.get("docker_auto_start", True):
        click.echo("   ℹ️  Docker auto-start disabled trong config")
        click.echo("   💡 Để start Neo4j thủ công:")
        click.echo("      docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5")
        return

    # Kiểm tra Neo4j có đang chạy không
    if _is_neo4j_running():
        click.echo("   ✓ Neo4j đang chạy")
        return

    # Try to start Neo4j
    click.echo("   ⏳ Đang start Neo4j...")

    # Kiểm tra Docker
    if not _docker_installed():
        click.echo("")
        click.echo("   ╔═══════════════════════════════════════════════════════════╗")
        click.echo("   ║  DOCKER CHƯA ĐƯỢC CÀI ĐẶT HOẶC KHÔNG CHẠY                 ║")
        click.echo("   ║                                                           ║")
        click.echo("   ║  Neo4j là dependency BẮT BUỘC cho Midicoder.              ║")
        click.echo("   ║  Bạn cần cài đặt Docker và Neo4j để tiếp tục.             ║")
        click.echo("   ║                                                           ║")
        click.echo("   ║ Hướng dẫn cài đặt:                                        ║")
        click.echo("   ║  - docs/neo4j-setup.md (tiếng Anh)                        ║")
        click.echo("   ║  - docs/neo4j-setup-vi.md (tiếng Việt)                    ║")
        click.echo("   ║                                                           ║")
        click.echo("   ║  Cách nhanh nhất (Docker):                                ║")
        click.echo("   ║  docker run -d --name midicoder-neo4j                     ║")
        click.echo("   ║    -p 7474:7474 -p 7687:7687                              ║")
        click.echo("   ║    -e NEO4J_AUTH=neo4j/password neo4j:5                   ║")
        click.echo("   ║                                                           ║")
        click.echo("   ║  Sau đó chạy lại: midicoder init                          ║")
        click.echo("   ╚═══════════════════════════════════════════════════════════╝")
        click.echo("")
        return

    try:
        # Start Neo4j container
        result = subprocess.run(
            [
                "docker", "run", "-d",
                "--name", "midicoder-neo4j",
                "-p", "7474:7474",
                "-p", "7687:7687",
                "-e", "NEO4J_AUTH=neo4j/password",
                "neo4j:5"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            click.echo("   ✓ Neo4j container started")
            click.echo("   ℹ️  Đợi 10 giây để Neo4j khởi động...")
            import time
            time.sleep(10)
            
            # Kiểm tra lại sau khi đợi
            if _is_neo4j_running():
                click.echo("   ✓ Neo4j đã sẵn sàng!")
            else:
                click.echo("   ⚠️  Neo4j container started nhưng chưa sẵn sàng")
                click.echo("   💡 Kiểm tra: docker logs midicoder-neo4j")
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            click.echo("")
            click.echo("   ╔═══════════════════════════════════════════════════════════╗")
            click.echo("   ║  KHÔNG THỂ START NEO4J CONTAINER                          ║")
            click.echo("   ║                                                           ║")
            click.echo(f"  ║  Lỗi: {error_msg[:60]}                                    ║")
            click.echo("   ║                                                           ║")
            click.echo("   ║  Nguyên nhân có thể:                                      ║")
            click.echo("   ║  - Container đã tồn tại: docker rm -f midicoder-neo4j     ║")
            click.echo("   ║  - Port bị chiếm: docker ps | grep neo4j                  ║")
            click.echo("   ║  - Image chưa pull: docker pull neo4j:5                   ║")
            click.echo("   ║                                                           ║")
            click.echo("   ║  Hướng dẫn chi tiết: docs/neo4j-setup-vi.md               ║")
            click.echo("   ╚═══════════════════════════════════════════════════════════╝")
            click.echo("")

    except subprocess.TimeoutExpired:
        click.echo("   ⚠️  Timeout khi start Neo4j")
        click.echo("   💡 Kiểm tra: docker logs midicoder-neo4j")
    except Exception as e:
        click.echo(f"   ⚠️  Lỗi khi start Neo4j: {e}")
        click.echo("   💡 Hướng dẫn: docs/neo4j-setup-vi.md")


def _is_neo4j_running() -> bool:
    """
    Kiểm tra Neo4j có đang chạy không.

    Returns:
        True nếu Neo4j đang chạy ở localhost:7687
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("localhost", 7687))
        sock.close()
        return result == 0
    except Exception:
        return False


def _docker_installed() -> bool:
    """
    Kiểm tra Docker có được cài đặt không.

    Returns:
        True nếu Docker đã cài đặt
    """
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_uvicorn_installed() -> bool:
    """
    Kiểm tra uvicorn có được cài đặt không.

    Returns:
        True nếu uvicorn đã cài đặt và có thể chạy
    """
    try:
        result = subprocess.run(
            ["uvicorn", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_nodejs_installed() -> bool:
    """
    Kiểm tra Node.js có được cài đặt không.

    Returns:
        True nếu Node.js đã cài đặt và có thể chạy
    """
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_port_available(port: int) -> bool:
    """
    Kiểm tra port có available không.

    Args:
        port: Port number để check

    Returns:
        True nếu port đang available (không bị chiếm)
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            result = s.connect_ex(("127.0.0.1", port))
            return result != 0
    except socket.error:
        return False


def _wait_for_port(port: int, timeout: int = 10) -> bool:
    """
    Đợi port trở nên available.

    Args:
        port: Port number để wait
        timeout: Timeout tối đa (giây)

    Returns:
        True nếu port trở nên available trong timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if _check_port_available(port):
            return True
        time.sleep(0.5)
    return False


def _save_pid_to_file(pid_file: Path, pid: int) -> None:
    """
    Lưu PID vào file.

    Args:
        pid_file: Path đến file PID
        pid: Process ID cần lưu
    """
    pid_file.write_text(str(pid), encoding="utf-8")


def _get_pid_from_file(pid_file: Path) -> Optional[int]:
    """
    Đọc PID từ file.

    Args:
        pid_file: Path đến file PID

    Returns:
        PID nếu file tồn tại và có nội dung, None nếu không
    """
    if not pid_file.exists():
        return None
    try:
        content = pid_file.read_text(encoding="utf-8").strip()
        return int(content) if content else None
    except ValueError:
        return None


def _is_process_running(pid: int) -> bool:
    """
    Kiểm tra process có đang chạy không.

    Args:
        pid: Process ID cần check

    Returns:
        True nếu process đang chạy
    """
    try:
        if sys.platform == "win32":
            # Windows: dùng tasklist để check process
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Nếu process tồn tại, tasklist sẽ trả về dòng chứa PID
            return result.returncode == 0 and str(pid) in str(result.stdout)
        else:
            # Unix: kill -0 để check
            os.kill(pid, 0)
            return True
    except (ProcessLookupError, PermissionError):
        return False
    except (OSError, subprocess.TimeoutExpired):
        return False


def _build_angular(webgui_dir: Path) -> bool:
    """
    Build Angular project.

    Args:
        webgui_dir: Path đến folder webgui

    Returns:
        True nếu build thành công
    """
    click.echo("   ⏳ Đang build Angular...")
    
    try:
        result = subprocess.run(
            ["ng", "build", "--configuration=development"],
            cwd=webgui_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 phút cho build
        )
        
        if result.returncode == 0:
            click.echo("   ✓ Angular build thành công")
            return True
        else:
            click.echo(f"   ❌ Angular build thất bại: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        click.echo("   ❌ Angular build timeout")
        return False
    except FileNotFoundError:
        click.echo("   ❌ 'ng' command not found. Vui lòng cài đặt Angular CLI.")
        click.echo("   💡 Cài đặt: npm install -g @angular/cli")
        return False


def _start_backend(
    api_dir: Path,
    runtime_dir: Path,
    host: str = "localhost",
    port: int = WEBGUI_BACKEND_PORT
) -> Tuple[bool, Optional[int]]:
    """
    Start Backend FastAPI.

    Args:
        api_dir: Path đến folder api/
        runtime_dir: Path đến .midicoder/runtime/
        host: Host để start backend
        port: Port để start backend

    Returns:
        Tuple (success, pid) - success là True nếu start thành công, pid là process ID
    """
    # Check uvicorn
    if not _check_uvicorn_installed():
        click.echo("")
        click.echo("   ╔═══════════════════════════════════════════════════════════╗")
        click.echo("   ║  UVICORN CHƯA ĐƯỢC CÀI ĐẶT                             ║")
        click.echo("   ║                                                           ║")
        click.echo("   ║  Uvicorn là dependency BẮT BUỘC cho Backend FastAPI.      ║")
        click.echo("   ║                                                           ║")
        click.echo("   ║  Cách cài đặt:                                            ║")
        click.echo("   ║  pip install uvicorn                                      ║")
        click.echo("   ╚═══════════════════════════════════════════════════════════╝")
        click.echo("")
        return False, None
    
    # Check port
    if not _check_port_available(port):
        click.echo("")
        click.echo("   ╔═══════════════════════════════════════════════════════════╗")
        click.echo("   ║  PORT {} ĐANG BỊ CHIẾM                                 ║".format(port))
        click.echo("   ║                                                           ║")
        click.echo("   ║  Vui lòng kill process đang chiếm port hoặc thay đổi port ║")
        click.echo("   ║                                                           ║")
        click.echo("   ║  Windows: netstat -ano | findstr :{}                     ║".format(port))
        click.echo("   ║  Unix: lsof -i :{}                                       ║".format(port))
        click.echo("   ╚═══════════════════════════════════════════════════════════╝")
        click.echo("")
        return False, None
    
    # Start backend
    click.echo("   ⏳ Đang start Backend FastAPI...")
    
    log_file = runtime_dir / "webgui-backend.log"
    pid_file = runtime_dir / "backend.pid"
    
    try:
        # Start uvicorn process
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port)],
            cwd=api_dir,
            stdout=open(log_file, "a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            start_new_session=True if sys.platform != "win32" else False
        )
        
        # Save PID
        _save_pid_to_file(pid_file, process.pid)
        
        # Wait for port to be available
        if _wait_for_port(port, timeout=10):
            click.echo(f"   ✓ Backend started (PID: {process.pid}, Port: {port})")
            return True, process.pid
        else:
            click.echo("   ❌ Backend start timeout")
            return False, None
            
    except Exception as e:
        click.echo(f"   ❌ Backend start failed: {e}")
        return False, None


def _start_frontend(
    webgui_dir: Path,
    runtime_dir: Path,
    port: int = WEBGUI_FRONTEND_PORT
) -> Tuple[bool, Optional[int]]:
    """
    Start Frontend Angular.

    Args:
        webgui_dir: Path đến folder webgui/
        runtime_dir: Path đến .midicoder/runtime/
        port: Port để start frontend

    Returns:
        Tuple (success, pid) - success là True nếu start thành công, pid là process ID
    """
    # Check Node.js
    if not _check_nodejs_installed():
        click.echo("")
        click.echo("   ╔═══════════════════════════════════════════════════════════╗")
        click.echo("   ║  NODE.JS CHƯA ĐƯỢC CÀI ĐẶT                               ║")
        click.echo("   ║                                                           ║")
        click.echo("   ║  Node.js là dependency BẮT BUỘC cho Frontend Angular.    ║")
        click.echo("   ║                                                           ║")
        click.echo("   ║  Cách cài đặt:                                            ║")
        click.echo("   ║  https://nodejs.org/                                      ║")
        click.echo("   ╚═══════════════════════════════════════════════════════════╝")
        click.echo("")
        return False, None
    
    # Build Angular
    if not _build_angular(webgui_dir):
        return False, None
    
    # Check dist folder exists
    dist_dir = webgui_dir / "dist" / "browser"
    if not dist_dir.exists():
        click.echo("   ❌ Angular build output not found. Vui lòng kiểm tra.")
        return False, None
    
    # Check port
    if not _check_port_available(port):
        click.echo("")
        click.echo("   ╔═══════════════════════════════════════════════════════════╗")
        click.echo("   ║  PORT {} ĐANG BỊ CHIẾM                                 ║".format(port))
        click.echo("   ║                                                           ║")
        click.echo("   ║  Vui lòng kill process đang chiếm port hoặc thay đổi port ║")
        click.echo("   ║                                                           ║")
        click.echo("   ║  Windows: netstat -ano | findstr :{}                     ║".format(port))
        click.echo("   ║  Unix: lsof -i :{}                                       ║".format(port))
        click.echo("   ╚═══════════════════════════════════════════════════════════╝")
        click.echo("")
        return False, None
    
    # Start frontend using Python HTTP server
    click.echo("   ⏳ Đang start Frontend Angular...")
    
    log_file = runtime_dir / "webgui-frontend.log"
    pid_file = runtime_dir / "frontend.pid"
    
    # Create a script to serve static files
    server_script = f'''
import http.server
import socketserver
import os

PORT = {port}
DIRECTORY = r"{dist_dir}"

os.chdir(DIRECTORY)

Handler = http.server.SimpleHTTPRequestHandler
Handler.extensions_map.update({{
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}})

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Frontend server running on http://localhost:{{PORT}}")
    httpd.serve_forever()
'''
    
    try:
        # Write server script
        server_script_file = runtime_dir / "frontend_server.py"
        server_script_file.write_text(server_script, encoding="utf-8")
        
        # Start Python HTTP server process
        process = subprocess.Popen(
            [sys.executable, str(server_script_file)],
            stdout=open(log_file, "a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            start_new_session=True if sys.platform != "win32" else False
        )
        
        # Save PID
        _save_pid_to_file(pid_file, process.pid)
        
        # Wait for port to be available
        if _wait_for_port(port, timeout=15):
            click.echo(f"   ✓ Frontend started (PID: {process.pid}, Port: {port})")
            return True, process.pid
        else:
            click.echo("   ❌ Frontend start timeout")
            return False, None
            
    except Exception as e:
        click.echo(f"   ❌ Frontend start failed: {e}")
        return False, None


def _open_browser(url: str) -> None:
    """
    Mở browser đến URL.

    Args:
        url: URL để mở
    """
    click.echo("   ⏳ Đang mở browser...")
    webbrowser.open(url)
    click.echo(f"   ✓ Browser mở đến {url}")


def _start_webgui(workspace_dir: Optional[Path] = None) -> None:
    """
    Khởi động WebGUI (FastAPI + Angular).

    Theo SoT E00, WebGUI bao gồm:
    - Backend: FastAPI chạy trên port 6868
    - Frontend: Angular chạy trên port 7272

    Args:
        workspace_dir: Path đến .midicoder/ (optional, mặc định là current directory)
    """
    if workspace_dir is None:
        workspace_dir = Path.cwd() / ".midicoder"
    
    runtime_dir = workspace_dir / "runtime"
    
    # Load config
    config = get_config()
    auto_start = config.get("webgui.auto_start", True)
    open_browser = config.get("webgui.open_browser", True)
    
    if not auto_start:
        click.echo("   ℹ️  WebGUI auto-start disabled trong config")
        click.echo("   💡 Để start WebGUI thủ công, chạy 'midicoder webgui start'")
        return
    
    # Check if already running
    backend_pid_file = runtime_dir / "backend.pid"
    frontend_pid_file = runtime_dir / "frontend.pid"
    
    backend_pid = _get_pid_from_file(backend_pid_file)
    frontend_pid = _get_pid_from_file(frontend_pid_file)
    
    if backend_pid and _is_process_running(backend_pid):
        click.echo("   ℹ️  Backend đã đang chạy (PID: {})".format(backend_pid))
    else:
        # Get api_dir từ current directory
        api_dir = Path.cwd() / "api"
        if not api_dir.exists():
            click.echo("   ❌ Folder 'api/' không tồn tại. Không thể start Backend.")
            return
        
        success, backend_pid = _start_backend(api_dir, runtime_dir)
        if not success:
            click.echo("   ⚠️  Backend start thất bại, tiếp tục với Frontend...")
            return

    # Start frontend
    webgui_dir = Path.cwd() / "webgui"
    if frontend_pid and _is_process_running(frontend_pid):
        click.echo("   ℹ️  Frontend đã đang chạy (PID: {})".format(frontend_pid))
    else:
        if not webgui_dir.exists():
            click.echo("   ❌ Folder 'webgui/' không tồn tại. Không thể start Frontend.")
            return
        
        success, frontend_pid = _start_frontend(webgui_dir, runtime_dir)
        if not success:
            click.echo("   ⚠️  Frontend start thất bại")
            return
    
    # Open browser
    if open_browser and backend_pid and frontend_pid:
        _open_browser("http://localhost:{}".format(WEBGUI_FRONTEND_PORT))
    
    click.echo("")
    click.echo("   🌐 WebGUI URLs:")
    click.echo("     - Backend: http://localhost:{}".format(WEBGUI_BACKEND_PORT))
    click.echo("     - Frontend: http://localhost:{}".format(WEBGUI_FRONTEND_PORT))


def run_init_interactive() -> None:
    """
    Interactive init mode với user prompts.

    Tương lai sẽ có:
    - Chọn stack (FastAPI, NestJS, etc.)
    - Chọn database (PostgreSQL, etc.)
    - Cấu hình LLM provider
    """
    click.echo("Interactive init mode chưa được implement.")
    click.echo("   💡 Sử dụng 'midicoder init' (không interactive) hoặc 'midicoder config' để cấu hình.")