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
def gen():
    """
    Generate DSL contracts từ brief analysis.

    Sử dụng LLM + DSL schema để tạo contracts hợp lệ.
    """
    from midicoder.pipeline.commands.contract import generate_contracts
    generate_contracts()


@contract.command()
def check():
    """
    Validate contracts với DSL schema.
    """
    from midicoder.pipeline.commands.contract import check_contracts
    check_contracts()


@contract.command()
def repair():
    """
    Sửa contracts có lỗi bằng LLM.
    """
    click.echo("Contract repair - coming soon")


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


@cli.group()
def code():
    """
    Code planning, generation, và application.

    Plan: Tạo kế hoạch implementation
    Gen: Generate code từ MIR + templates
    Apply: Apply code vào target system
    """
    pass


@code.command()
def plan():
    """
    Generate implementation plan từ MIR.
    """
    from midicoder.pipeline.commands.code import create_plan
    create_plan()


@code.command()
@click.option("--target", "-t", type=click.Choice(["backend", "frontend", "all"]),
              default="all", help="Target to generate")
def gen(target):
    """
    Generate code từ plan.

    Supports: FastAPI, NestJS, Angular, React
    """
    from midicoder.pipeline.commands.code import generate_code
    generate_code(target)


@code.command()
@click.option("--target-dir", "-d", type=click.Path(), default=".",
              help="Target directory for code application")
def apply(target_dir):
    """
    Apply generated code vào target.
    """
    from midicoder.pipeline.commands.code import apply_code
    apply_code(target_dir)


@cli.group()
def preview():
    """
    Local preview với Docker Compose.

    Start/Stop/Status của local development stack.
    """
    pass


@preview.command()
def start():
    """
    Start local preview stack.
    """
    from midicoder.pipeline.commands.preview import start_preview
    start_preview()


@preview.command()
def stop():
    """
    Stop local preview stack.
    """
    from midicoder.pipeline.commands.preview import stop_preview
    stop_preview()


@preview.command()
def status():
    """
    Show preview stack status.
    """
    from midicoder.pipeline.commands.preview import show_status
    show_status()


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
    from midicoder.pipeline.config import get_config
    cfg = get_config()
    global_conf = cfg.load_global_config()
    import json
    click.echo("Global Config:")
    click.echo(json.dumps(global_conf, indent=2))


@config.command()
@click.argument("key")
@click.argument("value")
def set(key, value):
    """
    Set configuration value.

    Ví dụ: midicoder config set llm.model "gpt-4"
    """
    from midicoder.pipeline.config import get_config
    cfg = get_config()
    cfg.set(key, value)
    click.echo(f"Set {key} = {value}")


@config.command()
@click.argument("key", required=False)
def reset(key):
    """
    Reset configuration về mặc định.

    Nếu không có key, reset toàn bộ config.
    """
    from midicoder.pipeline.config import get_config
    cfg = get_config()
    cfg.reset(key)
    click.echo(f"Reset {'all' if key is None else key} to defaults")


@cli.command()
def status():
    """
    Hiển thị project status.
    """
    click.echo("Midicoder Project Status")
    click.echo("=" * 40)
    from midicoder.pipeline.config import get_config
    cfg = get_config()
    try:
        project = cfg.load_project_config()
        click.echo(f"Active Version: {project.get('active_version', 'N/A')}")
        click.echo(f"Capabilities: {project.get('capabilities', {})}")
    except Exception as e:
        click.echo(f"Project not initialized: {e}")


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
