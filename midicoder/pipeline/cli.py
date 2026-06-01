# ============================================================================
# MUST BE FIRST: Force UTF-8 encoding for Windows (before any imports)
# ============================================================================
import os

# Force UTF-8 encoding for Windows
os.environ["PYTHONUTF8"] = "1"
# ============================================================================

"""
CLI Entry Point cho Midicoder Pipeline.

CLI commands chính (theo requirement.md E20):
- midicoder init              : Khởi tạo workspace
- midicoder brief analyze     : Phân tích yêu cầu
- midicoder contract gen      : Tạo contracts
- midicoder ir build          : Build MIR
- midicoder code plan/gen     : Tạo code
- midicoder preview           : Start preview

Interactive Shell:
- midicoder                   : Mở interactive shell với Rich UI
- midicoder init              : Vào shell rồi chạy init

E00-E07: Core Pipeline Commands
"""

import sys
from pathlib import Path
from typing import Optional

import click

# Import config manager
from midicoder.pipeline.config import get_config, get_global_config_path


@click.group()
@click.version_option(version="1.0.0", prog_name="midicoder")
@click.option("--debug", is_flag=True, help="Bật chế độ debug")
@click.option("--quiet", is_flag=True, help="Ẩn output không cần thiết")
@click.option("--json", "json_output", is_flag=True, help="Output format JSON")
@click.option("--config", type=click.Path(), help="File cấu hình tùy chỉnh")
@click.option("--project", type=click.Path(), help="Thư mục project")
@click.pass_context
def cli(ctx, debug, quiet, json_output, config, project):
    """
    Midicoder v1.0.0 - Contract-First Compiler Platform.

    Midicoder là một software factory nhận vào mô tả hệ thống ở mức capability
    và biên dịch ra phần mềm hoàn chỉnh, có thể kiểm chứng và vận hành.

    Các lệnh chính:
      init       Khởi tạo workspace mới
      brief      Quản lý và phân tích yêu cầu
      contract   Tạo và kiểm tra contracts
      ir         Build MIR từ contracts
      code       Plan, generate, và apply code
      preview    Start local preview
      config     Quản lý cấu hình
      help       Hiển thị help
    """
    # Initialize context với global flags
    ctx.ensure_object(dict)
    ctx.obj["config"] = get_config()
    ctx.obj["debug"] = debug
    ctx.obj["quiet"] = quiet
    ctx.obj["json_output"] = json_output
    ctx.obj["config_path"] = config
    ctx.obj["project_path"] = project


# ============================================================================
# Sub-commands (theo requirement.md E20)
# ============================================================================

@cli.command()
@click.option("--force", is_flag=True, help="Ghi đè .midicoder/ nếu đã tồn tại")
@click.option("--version", "-v", default="v1.0.0", help="Phiên bản ban đầu (mặc định: v1.0.0)")
def init(force, version):
    """
    Khởi tạo Midicoder workspace.

    Tạo cấu trúc thư mục .midicoder/ và cấu hình ban đầu:
    1. Tạo .midicoder/ folder
    2. Tạo global config ~/.midicoder/midicoder.json (nếu chưa có)
    3. Khởi tạo SQLite databases
    4. Start Neo4j Docker container (nếu cần)
    5. Start WebGUI (FastAPI + Angular)

    EXAMPLES:
      midicoder init
      midicoder init --force --version v1.0.0
    """
    from midicoder.pipeline.commands.init import run_init
    run_init(force=force, version=version)


# Import brief group từ brief.py
from midicoder.pipeline.commands.brief import brief as brief_group
cli.add_command(brief_group)


@cli.group()
def contract():
    """
    Tạo và kiểm tra DSL contracts.

    Contracts là DSL typed schema-validated cho requirements.
    """
    pass


@contract.command()
@click.option("--force", is_flag=True, help="Ghi đè contracts nếu đã tồn tại (không hỏi)")
@click.option("--interactive", is_flag=True, help="Review contracts trước khi lưu")
def gen(force, interactive):
    """
    Generate DSL contracts từ brief analysis.

    Sử dụng LLM + DSL schema để tạo contracts hợp lệ.

    OPTIONS:
      --force         Ghi đè contracts nếu đã tồn tại (không hỏi confirmation)
      --interactive   Review contracts trước khi lưu (mở editor)

    EXAMPLES:
      midicoder contract gen
      midicoder contract gen --force
      midicoder contract gen --interactive
    """
    from midicoder.pipeline.commands.contract import generate_contracts
    generate_contracts(force=force)


@contract.command()
@click.option("--auto-fix", is_flag=True, help="Tự động sửa errors bằng LLM nếu có")
@click.option("--strict", is_flag=True, help="Coi warnings là errors (exit 1 nếu có warnings)")
def check(auto_fix, strict):
    """
    Validate contracts với DSL schema.

    Kiểm tra contracts đã tồn tại và report errors/warnings.

    OPTIONS:
      --auto-fix      Tự động chạy LLM để sửa errors nếu có
      --strict        Coi warnings là errors (exit code 1 nếu có warnings)

    EXAMPLES:
      midicoder contract check
      midicoder contract check --strict
      midicoder contract check --auto-fix
    """
    from midicoder.pipeline.commands.contract import check_contracts
    check_contracts(auto_fix=auto_fix, strict=strict)


@contract.command()
def repair():
    """
    Sửa contracts có lỗi bằng LLM.

    Tự động phát hiện và sửa validation errors trong contracts bằng LLM.
    Retry tối đa 3 lần nếu LLM fix không valid.

    EXAMPLES:
      midicoder contract repair
    """
    from midicoder.pipeline.commands.contract import repair_contracts
    repair_contracts()


@cli.group()
def ir():
    """
    Build MIR (Midicoder Intermediate Representation).

    MIR là typed IR với ops, data flows, effect flows.
    """
    pass


@ir.command()
def build():
    """
    Build MIR từ contracts.

    Chuyển contracts sang MIR cho code generation.
    """
    from midicoder.pipeline.commands.ir import build_mir
    build_mir()


# Import code group từ code.py (với full CLI implementation)
from midicoder.pipeline.commands.code import code as code_group
cli.add_command(code_group)

# Import preview group từ preview.py (với full CLI implementation)
from midicoder.pipeline.commands.preview import preview as preview_group
cli.add_command(preview_group)

# Import version group từ version.py (với full CLI implementation)
from midicoder.pipeline.commands.version import version as version_group
cli.add_command(version_group)

# Import index command
from midicoder.pipeline.commands.index import index_command
cli.add_command(index_command)


# ============================================================================
# WebGUI Command Group
# ============================================================================

@cli.group()
def webgui():
    """
    Quản lý WebGUI (FastAPI backend + Angular frontend).

    Commands:
      start   Khởi động WebGUI
      stop    Dừng WebGUI
      status  Kiểm tra trạng thái WebGUI
    """
    pass


@webgui.command()
@click.option("--force", is_flag=True, help="Rebuild Angular trước khi start")
def start(force):
    """
    Khởi động WebGUI.

    Start FastAPI backend (port 6868) và Angular frontend (port 7272).
    Tự động mở browser đến frontend.

    EXAMPLES:
      midicoder webgui start
      midicoder webgui start --force
    """
    from midicoder.pipeline.commands.init import (
        _start_webgui,
        _get_pid_from_file,
        _is_process_running,
        WEBGUI_BACKEND_PORT,
        WEBGUI_FRONTEND_PORT,
    )
    from midicoder.pipeline.config import get_config
    from pathlib import Path
    import click

    workspace_dir = Path.cwd() / ".midicoder"
    runtime_dir = workspace_dir / "runtime"

    backend_pid_file = runtime_dir / "backend.pid"
    frontend_pid_file = runtime_dir / "frontend.pid"

    backend_pid = _get_pid_from_file(backend_pid_file)
    frontend_pid = _get_pid_from_file(frontend_pid_file)

    # Check if already running
    if backend_pid and _is_process_running(backend_pid):
        click.echo(f"ℹ️  Backend đã đang chạy (PID: {backend_pid})")
    if frontend_pid and _is_process_running(frontend_pid):
        click.echo(f"ℹ️  Frontend đã đang chạy (PID: {frontend_pid})")

    if (backend_pid and _is_process_running(backend_pid) and
        frontend_pid and _is_process_running(frontend_pid)):
        click.echo(f"\n🌐 WebGUI đang chạy:")
        click.echo(f"  - Backend: http://localhost:{WEBGUI_BACKEND_PORT}")
        click.echo(f"  - Frontend: http://localhost:{WEBGUI_FRONTEND_PORT}")
        return

    click.echo("\n🚀 Đang khởi động WebGUI...")
    _start_webgui(workspace_dir)


@webgui.command()
def stop():
    """
    Dừng WebGUI.

    Dừng cả FastAPI backend (port 6868) và Angular frontend (port 7272).

    EXAMPLES:
      midicoder webgui stop
    """
    from midicoder.pipeline.commands.init import (
        _get_pid_from_file,
        _is_process_running,
    )
    from pathlib import Path
    import click
    import os
    import subprocess
    import sys

    runtime_dir = Path.cwd() / ".midicoder" / "runtime"
    backend_pid_file = runtime_dir / "backend.pid"
    frontend_pid_file = runtime_dir / "frontend.pid"

    stopped = 0

    # Stop backend
    backend_pid = _get_pid_from_file(backend_pid_file)
    if backend_pid and _is_process_running(backend_pid):
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(backend_pid)],
                    capture_output=True, timeout=5
                )
            else:
                os.kill(backend_pid, 9)
            click.echo(f"✓ Backend stopped (PID: {backend_pid})")
            stopped += 1
        except Exception as e:
            click.echo(f"⚠️  Failed to stop backend (PID: {backend_pid}): {e}")
    elif backend_pid:
        click.echo("ℹ️  Backend không đang chạy (stale PID)")
    else:
        click.echo("ℹ️  Backend không chạy")

    # Stop frontend
    frontend_pid = _get_pid_from_file(frontend_pid_file)
    if frontend_pid and _is_process_running(frontend_pid):
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(frontend_pid)],
                    capture_output=True, timeout=5
                )
            else:
                os.kill(frontend_pid, 9)
            click.echo(f"✓ Frontend stopped (PID: {frontend_pid})")
            stopped += 1
        except Exception as e:
            click.echo(f"⚠️  Failed to stop frontend (PID: {frontend_pid}): {e}")
    elif frontend_pid:
        click.echo("ℹ️  Frontend không đang chạy (stale PID)")
    else:
        click.echo("ℹ️  Frontend không chạy")

    # Clean up PID files
    for pid_file in [backend_pid_file, frontend_pid_file]:
        if pid_file.exists():
            try:
                pid_file.unlink()
            except Exception:
                pass

    if stopped > 0:
        click.echo(f"\n✓ WebGUI stopped ({stopped} processes)")
    else:
        click.echo("\nℹ️  No running WebGUI processes found")


@webgui.command()
def status():
    """
    Kiểm tra trạng thái WebGUI.

    EXAMPLES:
      midicoder webgui status
    """
    from midicoder.pipeline.commands.init import (
        _get_pid_from_file,
        _is_process_running,
        WEBGUI_BACKEND_PORT,
        WEBGUI_FRONTEND_PORT,
    )
    from pathlib import Path
    import click
    import socket

    runtime_dir = Path.cwd() / ".midicoder" / "runtime"
    backend_pid_file = runtime_dir / "backend.pid"
    frontend_pid_file = runtime_dir / "frontend.pid"

    # Check backend
    backend_pid = _get_pid_from_file(backend_pid_file)
    backend_running = False
    backend_port_open = False
    if backend_pid:
        backend_running = _is_process_running(backend_pid)
    # Check port
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("localhost", WEBGUI_BACKEND_PORT))
        s.close()
        backend_port_open = True
    except Exception:
        pass

    # Check frontend
    frontend_pid = _get_pid_from_file(frontend_pid_file)
    frontend_running = False
    frontend_port_open = False
    if frontend_pid:
        frontend_running = _is_process_running(frontend_pid)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("localhost", WEBGUI_FRONTEND_PORT))
        s.close()
        frontend_port_open = True
    except Exception:
        pass

    click.echo("\n🌐 WebGUI Status:")
    click.echo(f"  Backend (port {WEBGUI_BACKEND_PORT}):")
    if backend_port_open:
        pid_str = f" PID: {backend_pid}" if backend_pid else ""
        click.echo(f"    ✓ Running{pid_str}")
    else:
        click.echo(f"    ✗ Not running")

    click.echo(f"  Frontend (port {WEBGUI_FRONTEND_PORT}):")
    if frontend_port_open:
        pid_str = f" PID: {frontend_pid}" if frontend_pid else ""
        click.echo(f"    ✓ Running{pid_str}")
    else:
        click.echo(f"    ✗ Not running")


# ============================================================================
# Config Command Group
# ============================================================================

@cli.group()
def config():
    """
    Quản lý cấu hình Midicoder.
    """
    pass


@config.command()
def show():
    """
    Hiển thị current configuration.
    """
    from midicoder.pipeline.commands.util import run_config_show
    run_config_show()


@config.command()
@click.argument("key")
@click.argument("value")
def set(key, value):
    """
    Set configuration value với schema validation.

    Ví dụ: midicoder config set llm.model "gpt-4"
    """
    from midicoder.pipeline.commands.util import run_config_set
    run_config_set(key, value)


@config.command()
@click.argument("key", required=False)
def reset(key):
    """
    Reset configuration về mặc định.

    Nếu không có key, reset toàn bộ config.
    """
    from midicoder.pipeline.commands.util import run_config_reset
    run_config_reset(key)


@cli.command()
@click.option("--json", "json_output", is_flag=True, help="Output format JSON")
def status(json_output):
    """
    Hiển thị project status (detailed).

    Hiển thị thông tin chi tiết về:
    - Active version
    - Pipeline progress (brief, contract, MIR, code)
    - Artifacts count
    - Last activity
    - Neo4j status
    - Versions list
    """
    from midicoder.pipeline.commands.util import run_status
    run_status(json_output=json_output)


@cli.command()
@click.option("--type", "feedback_type", default="clarification", 
              type=click.Choice(["bug", "enhancement", "clarification"]),
              help="Loại feedback")
@click.option("--message", "-m", type=str, help="Nội dung feedback")
@click.option("--no-auto-apply", is_flag=True, help="Không tự động trigger pipeline")
def feedback(feedback_type, message, no_auto_apply):
    """
    Thu thập feedback từ user.

    Feedback được lưu vào SQLite và có thể trigger pipeline tự động.
    """
    from midicoder.pipeline.commands.util import run_feedback
    run_feedback(
        feedback_type=feedback_type,
        message=message,
        no_auto_apply=no_auto_apply
    )


@cli.command()
def help():
    """
    Hiển thị help đầy đủ.
    """
    click.echo(cli.get_help(click.Context(cli)))


# ============================================================================
# Main entry point
# ============================================================================

def main():
    """
    Main entry point cho CLI.

    Gọi từ __main__.py hoặc khi chạy `midicoder` command.

    Logic:
    - `midicoder` → Mở interactive shell
    - `midicoder init` → Mở shell rồi chạy init
    - `midicoder --help` → Hiển thị help (không vào shell)
    """
    try:
        # Check có command nào không (loại bỏ các global flags)
        args = sys.argv[1:]
        
        # Check nếu có --help hoặc --version thì CLI bình thường (không vào shell)
        has_help = "--help" in args or "-h" in args
        has_version = "--version" in args
        
        if has_help or has_version:
            # midicoder --help / --version → CLI bình thường
            cli(obj={})
        elif not args:
            # midicoder (không có gì) → vào shell
            from midicoder.pipeline.shell import launch_shell
            launch_shell(cli, initial_command=None)
        else:
            # Có command → vào shell rồi execute command
            # Bỏ global flags ra khỏi command
            commands = [
                arg for arg in args 
                if not arg.startswith("--") and arg not in ["-h", "-v"]
            ]
            if commands:
                initial_command = " ".join(commands)
                from midicoder.pipeline.shell import launch_shell
                launch_shell(cli, initial_command=initial_command)
            else:
                # Chỉ có flags → vào shell
                from midicoder.pipeline.shell import launch_shell
                launch_shell(cli, initial_command=None)

    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        click.echo(f"Lỗi: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
