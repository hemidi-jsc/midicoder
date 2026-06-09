"""
Git helpers — đọc thông tin từ git repo của project.

Tất cả logic nằm trong pipeline, API delegate qua pipeline_bridge.
"""

import subprocess
from pathlib import Path
from typing import Optional


def get_repo_url(project_path: str) -> Optional[str]:
    """Lấy remote URL của project từ `git remote get-url origin`.

    Trả về URL đầy đủ (https/ssh). Nếu không có remote hoặc không phải git repo
    thì trả về None.
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Convert SSH URL to HTTPS cho dễ click
            if url.startswith("git@"):
                url = _ssh_to_https(url)
            return url
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def get_git_branch(project_path: str) -> Optional[str]:
    """Lấy tên branch hiện tại của project.

    Dùng `git branch --show-current`, fallback sang `git rev-parse --abbrev-ref HEAD`.
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            if branch:
                return branch
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    # Fallback: rev-parse
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            if branch and branch != "HEAD":
                return branch
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    return None


def _ssh_to_https(ssh_url: str) -> str:
    """Convert SSH git URL to HTTPS.

    git@github.com:user/repo.git → https://github.com/user/repo.git
    git@gitlab.com:user/repo.git → https://gitlab.com/user/repo.git
    """
    if ssh_url.startswith("git@"):
        host_part = ssh_url[4:]  # github.com:user/repo.git
        if ":" in host_part:
            host, path = host_part.split(":", 1)
            return f"https://{host}/{path}"
    return ssh_url
