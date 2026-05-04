"""Python stack detectors."""

from __future__ import annotations

import logging
import re

from ..core.scanner import ProjectScanner
from .constants import MAX_FILES_TO_CHECK

logger = logging.getLogger(__name__)

FASTAPI_PATTERN = re.compile(
    r"(?:from\s+fastapi\s+import|FastAPI\(|APIRouter\(|@(?:app|router)\.(?:get|post|put|delete|patch))",
    re.MULTILINE,
)


class FastAPIDetector:
    def get_name(self) -> str:
        return "fastapi"

    def detect(self, scanner: ProjectScanner) -> bool:
        if not scanner.has_python:
            return False

        for path in scanner.config_files:
            if path.name in ("pyproject.toml", "setup.py", "setup.cfg"):
                content = scanner.get_content(path)
                if content and re.search(r'["\']fastapi["\']', content, re.IGNORECASE):
                    logger.debug(f"FastAPI detected in config: {path.name}")
                    return True
            elif path.name == "requirements.txt":
                content = scanner.get_content(path)
                if content and re.search(
                    r"^fastapi[>=<\[]", content, re.IGNORECASE | re.MULTILINE
                ):
                    logger.debug("FastAPI detected in requirements.txt")
                    return True

        for path in scanner.python_files[:MAX_FILES_TO_CHECK]:
            content = scanner.get_content(path)
            if not content:
                continue

            if FASTAPI_PATTERN.search(content):
                logger.debug(f"FastAPI detected in code: {path.name}")
                return True

        return False
