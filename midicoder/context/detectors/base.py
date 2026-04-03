"""Detector protocols."""

from __future__ import annotations

from typing import Protocol

from ..core.scanner import ProjectScanner


class StackDetector(Protocol):
    def detect(self, scanner: ProjectScanner) -> bool:
        ...

    def get_name(self) -> str:
        ...
