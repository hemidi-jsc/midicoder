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
import subprocess
import webbrowser
import socket
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import click

from midicoder.pipeline.config import get_config, get_global_config_path, DEFAULT_GLOBAL_CONFIG


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
            "domain_packs": [],  # Ví dụ: DP01 (E-commerce)
            "regulatory_overlays": [],  # Ví dụ: RX01 (GDPR)
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


def _start_webgui() -> None:
    """
    Khởi động WebGUI (FastAPI + Angular).

    Theo SoT E00, WebGUI bao gồm:
    - Backend: FastAPI chạy trên port 6868
    - Frontend: Angular chạy trên port 7272

    Hiện tại: Stub function, hiển thị hướng dẫn manual start.
    """
    click.echo("   ⚠️  WebGUI chưa được start tự động.")
    click.echo("   💡 Để start WebGUI thủ công:")
    click.echo("")
    click.echo("   Backend (FastAPI):")
    click.echo("     cd webgui/backend")
    click.echo("     uvicorn main:app --host 0.0.0.0 --port 6868 --reload")
    click.echo("")
    click.echo("   Frontend (Angular):")
    click.echo("     cd webgui/frontend")
    click.echo("     ng serve --port 7272")
    click.echo("")
    click.echo("   Sau đó mở browser: http://localhost:7272")


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