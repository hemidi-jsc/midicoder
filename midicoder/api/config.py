"""
Cấu hình cho API Server
Tất cả comment đều bằng tiếng Việt
"""

import json
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Cấu hình ứng dụng FastAPI"""
    
    # Tên ứng dụng
    app_name: str = "Midicoder WebGUI API"
    
    # Phiên bản API
    api_version: str = "v1"
    
    # Cấu hình server
    host: str = "localhost"
    port: int = 6868
    
    # Cấu hình CORS (cho phép frontend Angular trên cùng máy)
    cors_origins: list[str] = [
        "http://localhost:7272",
        "http://127.0.0.1:7272",
    ]
    
    # Ngôn ngữ mặc định
    default_language: str = "vi"
    supported_languages: list[str] = ["vi", "en"]
    
    # Timeout cho CLI commands (giây)
    cli_timeout: int = 1800  # 30 phút
    
    # Cấu hình WebSocket
    ws_ping_interval: float = 30.0
    ws_ping_timeout: float = 10.0

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


# Instance toàn cục
settings = Settings()


def get_global_config_path() -> Path:
    """
    Lấy đường dẫn đến file cấu hình global ~/.midicoder/midicoder.json
    
    Returns:
        Path: Đường dẫn đến file config
    """
    home_dir = Path.home()
    return home_dir / ".midicoder" / "midicoder.json"


def load_global_config() -> dict:
    """
    Load cấu hình global từ ~/.midicoder/midicoder.json
    
    Returns:
        dict: Cấu hình global, hoặc dict rỗng nếu file không tồn tại
    """
    config_path = get_global_config_path()
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def get_project_cwd() -> str | None:
    """
    Lấy đường dẫn working directory của project đang active.

    Ưu tiên:
    1. ProjectsManager.get_active_project_path() (SQLite ~/.midicoder/data/projects.db)
    2. Global config project.cwd (~/.midicoder/midicoder.json)

    Returns None nếu không có project active — không fallback Path.cwd()
    vì midicoder support multiple projects.
    """
    # Thử đọc từ ProjectsManager
    try:
        from midicoder.storage.projects import ProjectsManager
        mgr = ProjectsManager()
        mgr.init()
        active_path = mgr.get_active_project_path()
        if active_path:
            return active_path
    except Exception:
        pass

    # Fallback: đọc từ global config
    config = load_global_config()
    if "project" in config and "cwd" in config["project"]:
        return config["project"]["cwd"]

    return None


# Load global config khi khởi động
_global_config = load_global_config()
_project_cwd = get_project_cwd()


def get_active_version() -> str | None:
    """Lấy active version từ config."""
    try:
        cwd = get_project_cwd()
        if not cwd:
            return None
        active_file = Path(cwd) / ".midicoder" / "config" / "active_version.txt"
        if active_file.exists():
            return active_file.read_text().strip()
    except Exception:
        pass
    return None


def get_version_dir(version: str | None = None) -> Path | None:
    """Lấy path đến version directory. Returns None nếu không có project active."""
    cwd = get_project_cwd()
    if not cwd:
        return None
    v = version or get_active_version()
    if not v:
        v = "v1.0.0"  # fallback
    return Path(cwd) / ".midicoder" / "versions" / v
