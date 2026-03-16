"""Analyzer registry and orchestration."""

from __future__ import annotations

import logging

from ..core.models import ErrorRecord, Symbol
from ..core.scanner import ProjectScanner
from .javascript_analyzer import JavaScriptAnalyzer
from .python_analyzer import PythonAnalyzer

logger = logging.getLogger(__name__)


def analyze_symbols(scanner: ProjectScanner, target_files: set[str] | None = None) -> tuple[list[Symbol], list[ErrorRecord]]:
    symbols: list[Symbol] = []
    errors: list[ErrorRecord] = []

    if scanner.has_python:
        python_analyzer = PythonAnalyzer()
        python_symbols, python_errors = python_analyzer.analyze(scanner, target_files=target_files)
        symbols.extend(python_symbols)
        errors.extend(python_errors)
        logger.debug(f"Analyzed {len(python_symbols)} Python symbols")

    if scanner.has_javascript:
        js_analyzer = JavaScriptAnalyzer()
        js_symbols, js_errors = js_analyzer.analyze(scanner, target_files=target_files)
        symbols.extend(js_symbols)
        errors.extend(js_errors)
        logger.debug(f"Analyzed {len(js_symbols)} JavaScript/TypeScript symbols")

    logger.debug(f"Total symbols analyzed: {len(symbols)}")
    return symbols, errors
