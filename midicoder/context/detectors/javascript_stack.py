"""JavaScript/TypeScript stack detectors."""

from __future__ import annotations

import logging
import re

from ..core.scanner import ProjectScanner
from .constants import MAX_FILES_TO_CHECK
from .package_json import read_package_dependencies

logger = logging.getLogger(__name__)

NEST_PATTERN = re.compile(
    r"(?:NestFactory\.create|@Controller\(|@Injectable\(|@Module\()", re.MULTILINE
)
ANGULAR_PATTERN = re.compile(
    r"(?:platformBrowserDynamic|bootstrapApplication|@Component\(|@NgModule\()",
    re.MULTILINE,
)
EXPRESS_PATTERN = re.compile(
    r"(?:\bexpress\s*\(|\brequire\(\s*['\"]express['\"]\s*\)|\bfrom\s+['\"]express['\"])",
    re.MULTILINE,
)


class NestJSDetector:
    def get_name(self) -> str:
        return "nest"

    def detect(self, scanner: ProjectScanner) -> bool:
        for path in scanner.config_files:
            if path.name == "nest-cli.json":
                logger.debug("NestJS detected: nest-cli.json found")
                return True

        deps = read_package_dependencies(scanner)
        if "@nestjs/core" in deps or "@nestjs/common" in deps:
            logger.debug("NestJS detected in package.json dependencies")
            return True

        if not scanner.has_javascript:
            return False

        for path in scanner.js_ts_files[:MAX_FILES_TO_CHECK]:
            content = scanner.get_content(path)
            if not content:
                continue

            if NEST_PATTERN.search(content):
                logger.debug(f"NestJS detected in code: {path.name}")
                return True

        return False


class AngularDetector:
    def get_name(self) -> str:
        return "angular"

    def detect(self, scanner: ProjectScanner) -> bool:
        for path in scanner.config_files:
            if path.name == "angular.json":
                logger.debug("Angular detected: angular.json found")
                return True

        deps = read_package_dependencies(scanner)
        if "@angular/core" in deps:
            logger.debug("Angular detected in package.json dependencies")
            return True

        if not scanner.has_javascript:
            return False

        for path in scanner.js_ts_files[:MAX_FILES_TO_CHECK]:
            content = scanner.get_content(path)
            if not content:
                continue

            if ANGULAR_PATTERN.search(content):
                logger.debug(f"Angular detected in code: {path.name}")
                return True

        return False


class ExpressDetector:
    def get_name(self) -> str:
        return "express"

    def detect(self, scanner: ProjectScanner) -> bool:
        deps = read_package_dependencies(scanner)
        if "express" in deps:
            logger.debug("Express detected in package.json dependencies")
            return True

        if not scanner.has_javascript:
            return False

        for path in scanner.js_ts_files[:MAX_FILES_TO_CHECK]:
            content = scanner.get_content(path)
            if not content:
                continue

            if EXPRESS_PATTERN.search(content):
                logger.debug(f"Express detected in code: {path.name}")
                return True

        return False
