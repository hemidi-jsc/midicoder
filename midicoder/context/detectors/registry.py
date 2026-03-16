"""Stack detection registry."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ..core.scanner import ProjectScanner
from .base import StackDetector
from .javascript_stack import AngularDetector, ExpressDetector, NestJSDetector
from .python_stack import FastAPIDetector

logger = logging.getLogger(__name__)


def detect_stack(scanner: ProjectScanner, config_stack: str | None = None) -> str:
    candidates: set[str] = set()

    if config_stack:
        candidates.add(config_stack.lower())

    detectors: list[StackDetector] = [
        FastAPIDetector(),
        NestJSDetector(),
        AngularDetector(),
        ExpressDetector(),
    ]

    for detector in detectors:
        if detector.detect(scanner):
            candidates.add(detector.get_name())

    priority = ["fastapi", "nest", "angular", "express"]
    for stack in priority:
        if stack in candidates:
            logger.debug(f"Stack detected: {stack} (candidates: {candidates})")
            return stack

    if config_stack:
        logger.debug(f"Using config stack: {config_stack}")
        return config_stack.lower()

    logger.debug("No specific stack detected, using generic")
    return "generic"


def read_config_stack(root: Path) -> str | None:
    config_path = root / ".midicoder" / "config.json"
    if not config_path.exists():
        return None

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    stack_value = payload.get("stack")
    if isinstance(stack_value, dict):
        stack_value = stack_value.get("target") or stack_value.get("name")

    if isinstance(stack_value, str) and stack_value.strip():
        return stack_value.strip().lower()

    return None
