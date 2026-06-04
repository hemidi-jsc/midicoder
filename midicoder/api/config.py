"""
API Server configuration.

Project active path: ProjectsManager (SQLite projects.db)
Global settings: SettingsManager (SQLite settings.db)
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Midicoder WebGUI API"
    api_version: str = "v1"
    host: str = "localhost"
    port: int = 6868
    cors_origins: list[str] = [
        "http://localhost:7272",
        "http://127.0.0.1:7272",
    ]
    default_language: str = "vi"
    supported_languages: list[str] = ["vi", "en"]
    cli_timeout: int = 1800
    ws_ping_interval: float = 30.0
    ws_ping_timeout: float = 10.0

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


settings = Settings()


def get_global_config_path() -> Path:
    """Path to global data directory."""
    from midicoder.storage.settings import GLOBAL_DATA_DIR
    return GLOBAL_DATA_DIR


def get_project_cwd() -> str | None:
    """Active project path from ProjectsManager, or None."""
    try:
        from midicoder.storage.projects import ProjectsManager
        mgr = ProjectsManager()
        mgr.init()
        active_path = mgr.get_active_project_path()
        if active_path:
            return active_path
    except Exception:
        pass
    return None


def get_active_version() -> str | None:
    """Active version from ProjectsManager, fallback to project YAML."""
    try:
        from midicoder.storage.projects import ProjectsManager
        cwd = get_project_cwd()
        if not cwd:
            return None
        mgr = ProjectsManager()
        mgr.init()
        active = mgr.get_active()
        if active:
            project_id = active["project_id"]
            ver = mgr.version_get_active(project_id)
            if ver:
                return ver["version_name"]
    except Exception:
        pass

    try:
        cwd = get_project_cwd()
        if not cwd:
            return None
        config_file = Path(cwd) / ".midicoder" / "config" / "midicoder.yml"
        if config_file.exists():
            import yaml
            data = yaml.safe_load(config_file.read_text()) or {}
            if "active_version" in data:
                return data["active_version"]
    except Exception:
        pass

    return None


def get_version_dir(version: str | None = None) -> Path | None:
    """Path to version directory, or None if no active project."""
    cwd = get_project_cwd()
    if not cwd:
        return None
    v = version or get_active_version()
    if not v:
        return None
    return Path(cwd) / ".midicoder" / "versions" / v
