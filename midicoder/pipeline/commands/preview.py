"""
Preview Commands Implementation.

Lệnh quản lý Docker Compose preview environment theo SoT E18, E19, E20:
- preview start: Start Docker Compose services
- preview stop: Stop Docker Compose services
- preview restart: Restart Docker Compose services
- preview status: Hiển thị status của services

Pipeline:
Docker Compose File → docker compose up/down/restart/ps → Services running/stopped

E18: Target Support (Local Docker Compose)
E19: Web Fullstack Generation (Preview)
E20: CLI Commands
"""

import json
import subprocess
import time
import webbrowser
import click
from pathlib import Path
from typing import Optional, List, Tuple

from midicoder.pipeline.config import get_config
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# Constants
# ============================================================================

DEFAULT_FRONTEND_PORT = 7272
DEFAULT_BACKEND_PORT = 8000
HEALTH_CHECK_TIMEOUT = 60
HEALTH_CHECK_INTERVAL = 2


# ============================================================================
# Docker Helper Functions
# ============================================================================

def check_docker_installed() -> bool:
    """
    Kiểm tra Docker CLI đã được cài đặt chưa.
    
    Returns:
        True nếu Docker CLI có sẵn, False nếu không.
    """
    try:
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_docker_running() -> bool:
    """
    Kiểm tra Docker daemon có đang chạy không.
    
    Returns:
        True nếu Docker daemon đang chạy, False nếu không.
    """
    try:
        result = subprocess.run(
            ['docker', 'info'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def find_docker_compose_cmd() -> List[str]:
    """
    Tìm Docker Compose command (mới: 'docker compose' hoặc legacy: 'docker-compose').
    
    Returns:
        List command cho Docker Compose.
        
    Raises:
        Exception: Nếu cả hai command đều không có.
    """
    # Thử 'docker compose' trước (mới)
    try:
        result = subprocess.run(
            ['docker', 'compose', 'version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return ['docker', 'compose']
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Thử 'docker-compose' (legacy)
    try:
        result = subprocess.run(
            ['docker-compose', 'version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return ['docker-compose']
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    raise Exception("Docker Compose không tìm thấy. Vui lòng cài đặt Docker Desktop.")


def get_compose_file_path() -> Path:
    """
    Tìm đường dẫn đến docker-compose.yml file.
    
    Path: .midicoder/versions/{active_version}/src/docker-compose.yml
    
    Returns:
        Path đến docker-compose.yml file.
        
    Raises:
        Exception: Nếu không tìm thấy file.
    """
    config = get_config()
    active_version = config.get("active_version", "v1.0.0")
    
    compose_path = Path(f".midicoder/versions/{active_version}/src/docker-compose.yml")
    
    if not compose_path.exists():
        EM.raise_error(
            ErrorCode.PREVIEW_COMPOSE_FILE_NOT_FOUND,
            path=str(compose_path),
            suggestions=[
                "Chạy 'midicoder code gen' để generate Docker Compose file",
                "Kiểm tra active_version trong config file"
            ]
        )
    
    return compose_path


def is_preview_running() -> bool:
    """
    Kiểm tra preview services có đang chạy không.
    
    Returns:
        True nếu có services đang chạy, False nếu không.
    """
    try:
        compose_cmd = find_docker_compose_cmd()
        compose_file = get_compose_file_path()
        
        result = subprocess.run(
            compose_cmd + ['ps', '--format', '{{.Name}} {{.Status}}'],
            capture_output=True,
            text=True,
            cwd=compose_file.parent,
            timeout=30
        )
        
        if result.returncode != 0:
            return False
        
        # Kiểm tra output có services running không
        output = result.stdout.strip()
        if not output:
            return False
        
        # Có services nhưng kiểm tra status
        for line in output.split('\n'):
            if line.strip() and 'running' in line.lower():
                return True
        
        return False
        
    except Exception:
        return False


def wait_for_healthy(timeout: int = HEALTH_CHECK_TIMEOUT, interval: int = HEALTH_CHECK_INTERVAL) -> bool:
    """
    Chờ cho services healthy.
    
    Poll Docker Compose ps cho đến khi tất cả services running hoặc timeout.
    
    Args:
        timeout: Timeout tối đa (giây)
        interval: Poll interval (giây)
        
    Returns:
        True nếu services healthy trong timeout.
        
    Raises:
        Exception: Nếu timeout hết mà services vẫn không healthy.
    """
    start_time = time.time()
    compose_cmd = find_docker_compose_cmd()
    compose_file = get_compose_file_path()
    
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                compose_cmd + ['ps', '--format', '{{.Name}} {{.Status}}'],
                capture_output=True,
                text=True,
                cwd=compose_file.parent,
                timeout=10
            )
            
            if result.returncode != 0:
                time.sleep(interval)
                continue
            
            output = result.stdout.strip()
            if not output:
                time.sleep(interval)
                continue
            
            # Kiểm tra tất cả services đều running
            all_running = True
            for line in output.split('\n'):
                if line.strip():
                    if 'running' not in line.lower():
                        all_running = False
                        break
            
            if all_running:
                return True
            
            time.sleep(interval)
            
        except subprocess.TimeoutExpired:
            time.sleep(interval)
            continue
    
    EM.raise_error(
        ErrorCode.PREVIEW_HEALTH_CHECK_TIMEOUT,
        timeout=timeout,
        suggestions=[
            "Kiểm tra Docker logs: docker compose logs",
            "Kiểm tra có đủ resources (CPU, memory)",
            "Thử start Docker Desktop lại"
        ]
    )


def open_browser(url: str) -> None:
    """
    Mở URL trong default browser.
    
    Args:
        url: URL để mở
    """
    webbrowser.open(url)


def log_activity(action: str, success: bool, details: Optional[dict] = None) -> None:
    """
    Log preview activity vào SQLite activity_log table.
    
    Args:
        action: Action thực hiện (start, stop, restart, status)
        success: Có thành công không
        details: Chi tiết thêm (optional)
    """
    try:
        from midicoder.storage.sqlite import ActivityLogManager
        
        logger = ActivityLogManager()
        logger.init()
        
        logger.log(
            action=f"preview_{action}",
            module="preview",
            success=success,
            message=f"Preview {action}: {'success' if success else 'failed'}",
            metadata=details or {}
        )
    except Exception as e:
        click.echo(f"⚠️  Không thể log activity: {e}")


# ============================================================================
# CLI Commands
# ============================================================================

@click.group()
def preview():
    """
    Quản lý Docker Compose preview environment.
    
    Các lệnh con:
      start    Start preview services
      stop     Stop preview services
      restart  Restart preview services
      status   Hiển thị status của services
    
    Ví dụ:
      midicoder preview start           # Start services
      midicoder preview start --no-browser  # Start không mở browser
      midicoder preview status          # Xem status
      midicoder preview stop            # Stop services
    """
    pass


@preview.command()
@click.option(
    "--port", "-p",
    type=int,
    default=DEFAULT_FRONTEND_PORT,
    help="Frontend port (mặc định: 7272)"
)
@click.option(
    "--no-browser",
    is_flag=True,
    help="Không tự động mở browser"
)
@click.option(
    "--watch",
    is_flag=True,
    help="Watch mode (restart on file change)"
)
def start(port: int, no_browser: bool, watch: bool):
    """
    Start Docker Compose preview services.
    
    Start services trong detached mode và tự động mở browser.
    
    OPTIONS:
      --port, -p PORT    Frontend port (mặc định: 7272)
      --no-browser       Không tự động mở browser
      --watch            Watch mode (restart on file change)
    
    EXAMPLES:
      midicoder preview start
      midicoder preview start --port 3000
      midicoder preview start --no-browser
    """
    _execute_start(port=port, open_browser=not no_browser, watch=watch)


@preview.command()
@click.option(
    "--volumes", "-v",
    is_flag=True,
    help="Xóa anonymous volumes"
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Force stop không confirmation"
)
def stop(volumes: bool, force: bool):
    """
    Stop Docker Compose preview services.
    
    Stop tất cả services và cleanup networks.
    
    OPTIONS:
      --volumes, -v      Xóa anonymous volumes
      --force, -f        Force stop không confirmation
    
    EXAMPLES:
      midicoder preview stop
      midicoder preview stop --force
      midicoder preview stop --volumes
    """
    _execute_stop(remove_volumes=volumes, force=force)


@preview.command()
@click.option(
    "--timeout", "-t",
    type=int,
    default=60,
    help="Timeout để stop containers (giây, mặc định: 60)"
)
def restart(timeout: int):
    """
    Restart Docker Compose preview services.
    
    Restart tất cả services (stop + start).
    
    OPTIONS:
      --timeout, -t SECONDS   Timeout để stop (mặc định: 60)
    
    EXAMPLES:
      midicoder preview restart
      midicoder preview restart --timeout 120
    """
    _execute_restart(timeout=timeout)


@preview.command()
def status():
    """
    Hiển thị status của Docker Compose services.
    
    Show service status, ports, và URLs.
    
    EXAMPLES:
      midicoder preview status
    """
    _execute_status()


# ============================================================================
# Implementation Functions
# ============================================================================

def _execute_start(port: int = DEFAULT_FRONTEND_PORT, open_browser: bool = True, watch: bool = False) -> None:
    """
    Thực thi preview start command.
    
    Process:
    1. Check Docker installed và running
    2. Check compose file tồn tại
    3. Check services đã đang chạy chưa
    4. Execute docker compose up -d
    5. Wait for healthy
    6. Mở browser (nếu cần)
    7. Log activity
    
    Args:
        port: Frontend port
        open_browser: Có mở browser không
        watch: Watch mode
    """
    click.echo("🚀 Đang start preview services...")
    
    # Bước 1: Check Docker installed
    if not check_docker_installed():
        EM.raise_error(
            ErrorCode.PREVIEW_DOCKER_NOT_INSTALLED,
            suggestions=[
                "Cài đặt Docker Desktop: https://www.docker.com/products/docker-desktop",
                "Sau khi cài đặt, restart terminal và thử lại"
            ]
        )
    
    click.echo("   ✓ Docker CLI đã cài đặt")
    
    # Bước 2: Check Docker running
    if not check_docker_running():
        EM.raise_error(
            ErrorCode.PREVIEW_DOCKER_NOT_RUNNING,
            suggestions=[
                "Start Docker Desktop",
                "Chờ Docker Desktop khởi động xong",
                "Kiểm tra Docker daemon: docker info"
            ]
        )
    
    click.echo("   ✓ Docker daemon đang chạy")
    
    # Bước 3: Get compose file
    compose_file = get_compose_file_path()
    click.echo(f"   ✓ Docker Compose file: {compose_file}")
    
    # Bước 4: Check đã đang chạy chưa
    if is_preview_running():
        EM.raise_error(
            ErrorCode.PREVIEW_ALREADY_RUNNING,
            suggestions=[
                "Chạy 'midicoder preview stop' trước",
                "Hoặc dùng 'midicoder preview restart'",
                "Kiểm tra status: midicoder preview status"
            ]
        )
    
    # Bước 5: Execute docker compose up -d
    compose_cmd = find_docker_compose_cmd()
    
    try:
        click.echo("   ▶️  Chạy: docker compose up -d")
        result = subprocess.run(
            compose_cmd + ['up', '-d'],
            capture_output=True,
            text=True,
            cwd=compose_file.parent,
            timeout=120
        )
        
        if result.returncode != 0:
            click.echo(f"   stderr: {result.stderr}")
            EM.raise_error(
                ErrorCode.PREVIEW_START_FAILED,
                compose_output=result.stderr,
                suggestions=[
                    "Kiểm tra docker-compose.yml syntax",
                    "Xem logs: docker compose logs",
                    "Kiểm tra ports không bị占用"
                ]
            )
        
        click.echo("   ✓ Docker Compose up completed")
        
    except subprocess.TimeoutExpired:
        EM.raise_error(
            ErrorCode.PREVIEW_START_FAILED,
            error="timeout",
            suggestions=["Kiểm tra Docker resources", "Thử lại sau"]
        )
    
    # Bước 6: Wait for healthy
    click.echo("   ⏳ Đang chờ services healthy...")
    try:
        wait_for_healthy()
        click.echo("   ✓ Tất cả services đang running")
    except Exception as e:
        click.echo(f"   ⚠️  Health check warning: {e}")
    
    # Bước 7: Mở browser
    if open_browser:
        url = f"http://localhost:{port}"
        click.echo(f"   🌐 Mở browser: {url}")
        open_browser(url)
    
    # Bước 8: Log activity
    log_activity("start", True, {"port": port, "browser": open_browser})
    
    click.echo("")
    click.echo("✅ Preview đã start thành công!")
    click.echo("")
    click.echo("URLs:")
    click.echo(f"  Frontend: http://localhost:{port}")
    click.echo(f"  Backend:  http://localhost:{DEFAULT_BACKEND_PORT}")
    click.echo("")
    click.echo("Commands:")
    click.echo("  midicoder preview status   # Xem status")
    click.echo("  midicoder preview logs     # Xem logs")
    click.echo("  midicoder preview stop     # Stop services")


def _execute_stop(remove_volumes: bool = False, force: bool = False) -> None:
    """
    Thực thi preview stop command.
    
    Process:
    1. Check Docker running
    2. Check services có đang chạy không
    3. Execute docker compose down
    4. Log activity
    
    Args:
        remove_volumes: Có xóa volumes không
        force: Force stop
    """
    click.echo("🛑 Đang stop preview services...")
    
    # Bước 1: Check Docker running
    if not check_docker_running():
        EM.raise_error(
            ErrorCode.PREVIEW_DOCKER_NOT_RUNNING,
            suggestions=["Start Docker Desktop"]
        )
    
    # Bước 2: Get compose file
    compose_file = get_compose_file_path()
    click.echo(f"   ✓ Docker Compose file: {compose_file}")
    
    # Bước 3: Check services đang chạy không
    if not is_preview_running():
        click.echo("   ⚠️  Preview không đang chạy")
        if not force:
            click.echo("   ℹ️  Dùng --force để stop bất chấp")
            raise SystemExit(0)
    
    # Bước 4: Execute docker compose down
    compose_cmd = find_docker_compose_cmd()
    
    cmd_args = ['down']
    if remove_volumes:
        cmd_args.append('--volumes')
    
    try:
        click.echo(f"   ▶️  Chạy: docker compose {' '.join(cmd_args)}")
        result = subprocess.run(
            compose_cmd + cmd_args,
            capture_output=True,
            text=True,
            cwd=compose_file.parent,
            timeout=120
        )
        
        if result.returncode != 0:
            click.echo(f"   stderr: {result.stderr}")
            EM.raise_error(
                ErrorCode.PREVIEW_STOP_FAILED,
                compose_output=result.stderr
            )
        
        click.echo("   ✓ Docker Compose down completed")
        
    except subprocess.TimeoutExpired:
        EM.raise_error(
            ErrorCode.PREVIEW_STOP_FAILED,
            error="timeout"
        )
    
    # Bước 5: Log activity
    log_activity("stop", True, {"volumes": remove_volumes})
    
    click.echo("")
    click.echo("✅ Preview đã stop thành công!")


def _execute_restart(timeout: int = 60) -> None:
    """
    Thực thi preview restart command.
    
    Process:
    1. Check Docker running
    2. Execute docker compose restart
    3. Wait for healthy
    4. Log activity
    
    Args:
        timeout: Restart timeout
    """
    click.echo("🔄 Đang restart preview services...")
    
    # Bước 1: Check Docker running
    if not check_docker_running():
        EM.raise_error(
            ErrorCode.PREVIEW_DOCKER_NOT_RUNNING,
            suggestions=["Start Docker Desktop"]
        )
    
    # Bước 2: Get compose file
    compose_file = get_compose_file_path()
    click.echo(f"   ✓ Docker Compose file: {compose_file}")
    
    # Bước 3: Execute docker compose restart
    compose_cmd = find_docker_compose_cmd()
    
    try:
        click.echo(f"   ▶️  Chạy: docker compose restart --timeout {timeout}")
        result = subprocess.run(
            compose_cmd + ['restart', '--timeout', str(timeout)],
            capture_output=True,
            text=True,
            cwd=compose_file.parent,
            timeout=120
        )
        
        if result.returncode != 0:
            click.echo(f"   stderr: {result.stderr}")
            EM.raise_error(
                ErrorCode.PREVIEW_RESTART_FAILED,
                compose_output=result.stderr
            )
        
        click.echo("   ✓ Docker Compose restart completed")
        
    except subprocess.TimeoutExpired:
        EM.raise_error(
            ErrorCode.PREVIEW_RESTART_FAILED,
            error="timeout"
        )
    
    # Bước 4: Wait for healthy
    click.echo("   ⏳ Đang chờ services healthy...")
    try:
        wait_for_healthy()
        click.echo("   ✓ Tất cả services đang running")
    except Exception as e:
        click.echo(f"   ⚠️  Health check warning: {e}")
    
    # Bước 5: Log activity
    log_activity("restart", True, {"timeout": timeout})
    
    click.echo("")
    click.echo("✅ Preview đã restart thành công!")


def _execute_status() -> None:
    """
    Thực thi preview status command.
    
    Process:
    1. Check Docker running
    2. Execute docker compose ps
    3. Parse và hiển thị output
    4. Log activity
    """
    click.echo("📊 Đang kiểm tra preview status...")
    
    # Bước 1: Check Docker running
    if not check_docker_running():
        click.echo("❌ Docker daemon không chạy")
        click.echo("💡 Vui lòng start Docker Desktop")
        log_activity("status", False, {"error": "docker_not_running"})
        raise SystemExit(1)
    
    # Bước 2: Get compose file
    try:
        compose_file = get_compose_file_path()
        click.echo(f"   ✓ Docker Compose file: {compose_file}")
    except Exception as e:
        click.echo(f"⚠️  {e}")
        log_activity("status", False, {"error": str(e)})
        raise SystemExit(3)
    
    # Bước 3: Execute docker compose ps
    compose_cmd = find_docker_compose_cmd()
    
    try:
        result = subprocess.run(
            compose_cmd + ['ps', '--format', 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'],
            capture_output=True,
            text=True,
            cwd=compose_file.parent,
            timeout=30
        )
        
        if result.returncode != 0:
            click.echo(f"⚠️  Không thể lấy status: {result.stderr}")
            log_activity("status", False, {"error": result.stderr})
            raise SystemExit(1)
        
        output = result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        click.echo("⚠️  Timeout khi lấy status")
        log_activity("status", False, {"error": "timeout"})
        raise SystemExit(1)
    
    # Bước 4: Hiển thị output
    click.echo("")
    
    if output:
        # Kiểm tra có services running không
        if is_preview_running():
            click.echo("Preview Status: 🟢 RUNNING")
        else:
            click.echo("Preview Status: 🔴 NOT RUNNING")
        
        click.echo("")
        click.echo("Services:")
        click.echo(output)
        click.echo("")
        click.echo("URLs:")
        click.echo(f"  Frontend: http://localhost:{DEFAULT_FRONTEND_PORT}")
        click.echo(f"  Backend:  http://localhost:{DEFAULT_BACKEND_PORT}")
    else:
        click.echo("Preview Status: 🔴 NOT RUNNING")
        click.echo("")
        click.echo("Không có services nào đang chạy.")
        click.echo("💡 Chạy 'midicoder preview start' để start services")
    
    # Bước 5: Log activity
    log_activity("status", True, {"running": is_preview_running()})


# ============================================================================
# Legacy Functions (deprecated)
# ============================================================================

def start_preview(port: int = DEFAULT_FRONTEND_PORT, open_browser: bool = True) -> None:
    """
    Legacy function - gọi _execute_start.
    
    Deprecated: Dùng CLI command thay thế.
    """
    _execute_start(port=port, open_browser=open_browser, watch=False)


def stop_preview(force: bool = False) -> None:
    """
    Legacy function - gọi _execute_stop.
    
    Deprecated: Dùng CLI command thay thế.
    """
    _execute_stop(remove_volumes=False, force=force)


def restart_preview(timeout: int = 60) -> None:
    """
    Legacy function - gọi _execute_restart.
    
    Deprecated: Dùng CLI command thay thế.
    """
    _execute_restart(timeout=timeout)


def get_preview_status() -> bool:
    """
    Legacy function - trả về preview running status.
    
    Deprecated: Dùng CLI command thay thế.
    """
    return is_preview_running()