"""Project profile extraction."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from ..core.models import ProjectProfile
from ..core.scanner import ProjectScanner, normalize_path
from .constants import MAX_FILES_FOR_PROFILE

logger = logging.getLogger(__name__)

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None

DEPENDENCY_PREVIEW_LIMIT = 60
PYTHON_DEP_FILE_NAMES = {"pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"}
NODE_DEP_FILE_NAMES = {
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
}
ORM_CANDIDATE_ORDER = ("sqlalchemy", "typeorm", "prisma", "mongoose", "sequelize")
ORM_DEPENDENCY_PACKAGES = {
    "sqlalchemy": {"sqlalchemy", "sqlmodel", "alembic"},
    "typeorm": {"typeorm"},
    "prisma": {"prisma", "@prisma/client"},
    "mongoose": {"mongoose"},
    "sequelize": {"sequelize", "sequelize-typescript"},
}
ORM_STACK_COMPATIBILITY = {
    "sqlalchemy": {"fastapi"},
    "typeorm": {"nest", "express"},
    "prisma": {"nest", "express"},
    "mongoose": {"nest", "express"},
    "sequelize": {"nest", "express"},
}
ORM_CODE_PATTERNS = {
    "sqlalchemy": (
        re.compile(r"\bfrom\s+sqlalchemy\s+import\b"),
        re.compile(r"\bimport\s+sqlalchemy\b"),
        re.compile(r"\bSQLAlchemy\("),
    ),
    "typeorm": (
        re.compile(r"['\"]typeorm['\"]"),
        re.compile(r"\b@Entity\("),
        re.compile(r"\bDataSource\("),
    ),
    "prisma": (
        re.compile(r"['\"]@prisma/client['\"]"),
        re.compile(r"\bnew\s+PrismaClient\("),
    ),
    "mongoose": (
        re.compile(r"['\"]mongoose['\"]"),
        re.compile(r"\bmongoose\.(?:connect|model)\("),
    ),
    "sequelize": (
        re.compile(r"['\"]sequelize['\"]"),
        re.compile(r"\bnew\s+Sequelize\("),
    ),
}
ORM_CODE_LANGUAGES = {
    "sqlalchemy": {"python"},
    "typeorm": {"typescript", "javascript"},
    "prisma": {"typescript", "javascript"},
    "mongoose": {"typescript", "javascript"},
    "sequelize": {"typescript", "javascript"},
}


def extract_project_profile(
    scanner: ProjectScanner,
    stack: str,
    config_stack: str | None,
) -> ProjectProfile:
    if not scanner.has_code:
        return ProjectProfile(
            root=normalize_path(scanner.root),
            language="unknown",
            stack=[config_stack] if config_stack else [],
            conventions={"note": "No supported source files detected"},
        )

    languages = []
    if scanner.has_python:
        languages.append("python")
    if scanner.has_javascript:
        languages.append("javascript")

    primary_language = detect_primary_language(languages)
    frameworks = detect_frameworks(scanner)
    orm = detect_orm(scanner, stack)
    di_style = detect_di_style(stack)
    error_handling = detect_error_handling(scanner, stack)
    conventions = detect_conventions(scanner, stack)

    return ProjectProfile(
        root=normalize_path(scanner.root),
        language=primary_language,
        stack=frameworks,
        orm=orm,
        di_style=di_style,
        error_handling=error_handling,
        conventions=conventions,
    )


def detect_primary_language(languages: list[str]) -> str:
    if not languages:
        return "unknown"
    if "python" in languages:
        return "python"
    if "javascript" in languages:
        return "javascript"
    return languages[0]


def detect_frameworks(scanner: ProjectScanner) -> list[str]:
    frameworks: set[str] = set()

    # Python frameworks
    framework_patterns = {
        "fastapi": re.compile(r"(?:fastapi|from\s+fastapi\s+import)", re.IGNORECASE),
    }
    js_framework_patterns = {
        "nest": re.compile(
            r"(?:NestFactory\.create|@Controller\(|@Injectable\(|@Module\()",
            re.MULTILINE,
        ),
        "angular": re.compile(
            r"(?:platformBrowserDynamic|bootstrapApplication|@Component\(|@NgModule\()",
            re.MULTILINE,
        ),
        "express": re.compile(
            r"(?:\bexpress\s*\(|\brequire\(\s*['\"]express['\"]\s*\)|\bfrom\s+['\"]express['\"])",
            re.MULTILINE,
        ),
    }

    for path in scanner.python_files[:MAX_FILES_FOR_PROFILE]:
        content = scanner.get_content(path)
        if not content:
            continue

        for framework, pattern in framework_patterns.items():
            if pattern.search(content):
                frameworks.add(framework)

    # JavaScript/TypeScript frameworks
    deps = read_package_deps(scanner)

    if "@nestjs/core" in deps or "@nestjs/common" in deps:
        frameworks.add("nest")
    if "@angular/core" in deps:
        frameworks.add("angular")
    if "express" in deps:
        frameworks.add("express")

    for path in scanner.js_ts_files[:MAX_FILES_FOR_PROFILE]:
        content = scanner.get_content(path)
        if not content:
            continue
        for framework, pattern in js_framework_patterns.items():
            if pattern.search(content):
                frameworks.add(framework)

    return sorted(frameworks)


def detect_orm(scanner: ProjectScanner, stack: str) -> str | None:
    scores: dict[str, int] = {orm: 0 for orm in ORM_CANDIDATE_ORDER}
    evidence: dict[str, list[str]] = {orm: [] for orm in ORM_CANDIDATE_ORDER}

    config_paths_by_name: dict[str, list[Path]] = {}
    for path in scanner.config_files:
        config_paths_by_name.setdefault(path.name, []).append(path)

    requirements_paths = discover_requirements_files(scanner.root)
    python_deps = read_python_deps(
        scanner,
        config_paths_by_name.get("pyproject.toml", []),
        requirements_paths,
    )
    package_deps = read_package_deps(scanner)
    combined_deps = python_deps | package_deps

    for orm_name, packages in ORM_DEPENDENCY_PACKAGES.items():
        matched = sorted(package for package in packages if package in combined_deps)
        if not matched:
            continue
        scores[orm_name] += 2
        evidence[orm_name].append(f"deps:{','.join(matched)}")

    for path in scanner.python_files[:MAX_FILES_FOR_PROFILE]:
        content = scanner.get_content(path)
        if not content:
            continue
        for orm_name, patterns in ORM_CODE_PATTERNS.items():
            if "python" not in ORM_CODE_LANGUAGES.get(orm_name, set()):
                continue
            if any(pattern.search(content) for pattern in patterns):
                scores[orm_name] += 3
                evidence[orm_name].append(
                    f"code:{normalize_path(path.relative_to(scanner.root))}"
                )

    for path in scanner.js_ts_files[:MAX_FILES_FOR_PROFILE]:
        content = scanner.get_content(path)
        if not content:
            continue
        for orm_name, patterns in ORM_CODE_PATTERNS.items():
            if not ORM_CODE_LANGUAGES.get(orm_name, set()) & {
                "typescript",
                "javascript",
            }:
                continue
            if any(pattern.search(content) for pattern in patterns):
                scores[orm_name] += 3
                evidence[orm_name].append(
                    f"code:{normalize_path(path.relative_to(scanner.root))}"
                )

    for orm_name, compatible_stacks in ORM_STACK_COMPATIBILITY.items():
        if stack in compatible_stacks and scores[orm_name] > 0:
            scores[orm_name] += 1
            evidence[orm_name].append(f"stack:{stack}")

    best_orm = max(ORM_CANDIDATE_ORDER, key=lambda orm: scores[orm])
    if scores[best_orm] == 0:
        return None

    logger.debug(
        "ORM detected: %s (score=%s, evidence=%s)",
        best_orm,
        scores[best_orm],
        ";".join(evidence[best_orm]),
    )
    return best_orm


def detect_di_style(stack: str) -> str | None:
    """Detect dependency injection style based on stack."""
    di_map = {
        "fastapi": "function-parameter",
        "nest": "class-constructor",
        "angular": "class-constructor",
        "express": "manual",
    }
    return di_map.get(stack)


def detect_error_handling(scanner: ProjectScanner, stack: str) -> str | None:
    if stack == "fastapi":
        pattern = re.compile(r"HTTPException")
        for path in scanner.python_files[:MAX_FILES_FOR_PROFILE]:
            content = scanner.get_content(path)
            if content and pattern.search(content):
                return "raise-http-exception"

    if stack == "nest":
        pattern = re.compile(r"HttpException")
        for path in scanner.js_ts_files[:MAX_FILES_FOR_PROFILE]:
            content = scanner.get_content(path)
            if content and pattern.search(content):
                return "throw-http-exception"

    return None


def detect_conventions(scanner: ProjectScanner, stack: str) -> dict[str, Any]:
    root = scanner.root
    conventions: dict[str, Any] = {}

    if (root / "src").exists():
        conventions["module_layout"] = "src"
    elif (root / "app").exists():
        conventions["module_layout"] = "app"

    if (root / "tests").exists() or (root / "test").exists():
        conventions["tests"] = True

    if stack == "fastapi":
        conventions.setdefault("router_prefix", "/api")

    conventions.update(detect_dependency_conventions(scanner))
    return conventions


def detect_dependency_conventions(scanner: ProjectScanner) -> dict[str, Any]:
    conventions: dict[str, Any] = {}
    config_name_set: set[str] = set()
    config_paths_by_name: dict[str, list[Path]] = {}
    config_rels: list[str] = []

    for path in scanner.config_files:
        rel = normalize_path(path.relative_to(scanner.root))
        config_rels.append(rel)
        config_name_set.add(path.name)
        config_paths_by_name.setdefault(path.name, []).append(path)

    requirements_paths = discover_requirements_files(scanner.root)
    requirement_files = [
        normalize_path(path.relative_to(scanner.root)) for path in requirements_paths
    ]

    python_dependency_files = sorted(
        set(
            [
                *[
                    rel
                    for rel in config_rels
                    if Path(rel).name in PYTHON_DEP_FILE_NAMES
                ],
                *requirement_files,
            ]
        )
    )
    javascript_dependency_files = sorted(
        [rel for rel in config_rels if Path(rel).name in NODE_DEP_FILE_NAMES]
    )
    dependency_files = sorted(
        set([*python_dependency_files, *javascript_dependency_files])
    )

    should_include_aggregate_dependency_files = (
        len(python_dependency_files) > 0
        and len(javascript_dependency_files) > 0
        and dependency_files != python_dependency_files
        and dependency_files != javascript_dependency_files
    )
    if should_include_aggregate_dependency_files:
        conventions["dependency_files"] = dependency_files
    if python_dependency_files:
        conventions["python_dependency_files"] = python_dependency_files
    if javascript_dependency_files:
        conventions["javascript_dependency_files"] = javascript_dependency_files

    python_dependency_style = detect_python_dependency_style(
        config_name_set, requirements_paths
    )
    if python_dependency_style:
        conventions["python_dependency_style"] = python_dependency_style

    python_dependency_tool = detect_python_dependency_tool(
        scanner,
        config_name_set,
        config_paths_by_name.get("pyproject.toml", []),
        requirements_paths,
    )
    if python_dependency_tool:
        conventions["python_dependency_tool"] = python_dependency_tool

    javascript_package_manager = detect_javascript_package_manager(config_name_set)
    if javascript_package_manager:
        conventions["javascript_package_manager"] = javascript_package_manager

    python_dependencies = read_python_deps(
        scanner,
        config_paths_by_name.get("pyproject.toml", []),
        requirements_paths,
    )
    add_dependency_preview(conventions, "python", python_dependencies)

    javascript_dependencies = read_package_deps(scanner)
    add_dependency_preview(conventions, "javascript", javascript_dependencies)

    return conventions


def detect_python_dependency_style(
    config_name_set: set[str],
    requirements_paths: list[Path],
) -> str | None:
    has_pyproject = "pyproject.toml" in config_name_set
    has_requirements = bool(requirements_paths) or "requirements.txt" in config_name_set

    if has_pyproject and has_requirements:
        return "pyproject+requirements"
    if has_pyproject:
        return "pyproject"
    if has_requirements:
        return "requirements"
    return None


def detect_python_dependency_tool(
    scanner: ProjectScanner,
    config_name_set: set[str],
    pyproject_paths: list[Path],
    requirements_paths: list[Path],
) -> str | None:
    pyproject_path = select_preferred_config_path(scanner.root, pyproject_paths)
    if pyproject_path:
        content = read_text_with_fallback(scanner, pyproject_path)
        content = content.lower() if content else ""
        if "[tool.poetry]" in content:
            return "poetry"
        if "[tool.pdm]" in content:
            return "pdm"
        if "[tool.hatch" in content:
            return "hatch"
        if "[project]" in content:
            return "pep621"
        return "pyproject"

    if requirements_paths or "requirements.txt" in config_name_set:
        return "pip"
    return None


def detect_javascript_package_manager(config_name_set: set[str]) -> str | None:
    if "pnpm-lock.yaml" in config_name_set:
        return "pnpm"
    if "yarn.lock" in config_name_set:
        return "yarn"
    if "package-lock.json" in config_name_set:
        return "npm"
    if "package.json" in config_name_set:
        return "npm"
    return None


def add_dependency_preview(
    conventions: dict[str, Any], prefix: str, deps: set[str]
) -> None:
    if not deps:
        return
    normalized = sorted(dep for dep in deps if dep)
    if not normalized:
        return

    conventions[f"{prefix}_dependencies"] = normalized[:DEPENDENCY_PREVIEW_LIMIT]
    if len(normalized) > DEPENDENCY_PREVIEW_LIMIT:
        conventions[f"{prefix}_dependencies_truncated"] = True


def discover_requirements_files(root: Path) -> list[Path]:
    candidates: set[Path] = set()

    for path in root.glob("requirements*.txt"):
        if path.is_file():
            candidates.add(path)

    requirements_dir = root / "requirements"
    if requirements_dir.is_dir():
        for path in requirements_dir.glob("*.txt"):
            if path.is_file():
                candidates.add(path)

    return sorted(candidates, key=lambda p: normalize_path(p.relative_to(root)))


def read_python_deps(
    scanner: ProjectScanner,
    pyproject_paths: list[Path],
    requirements_paths: list[Path],
) -> set[str]:
    deps: set[str] = set()

    for path in requirements_paths:
        content = read_text_with_fallback(scanner, path)
        if content:
            deps.update(parse_requirements_dependencies(content))

    pyproject_path = select_preferred_config_path(scanner.root, pyproject_paths)
    if pyproject_path:
        content = read_text_with_fallback(scanner, pyproject_path)
        if content:
            deps.update(parse_pyproject_dependencies(content))

    return deps


def read_text_with_fallback(scanner: ProjectScanner, path: Path) -> str | None:
    cached = scanner.get_content(path)
    if cached is not None:
        return cached
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def select_preferred_config_path(root: Path, paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return min(
        paths,
        key=lambda p: (
            len(p.relative_to(root).parts),
            normalize_path(p.relative_to(root)),
        ),
    )


def parse_requirements_dependencies(content: str) -> set[str]:
    deps: set[str] = set()
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if " #" in line:
            line = line.split(" #", 1)[0].strip()
        if not line:
            continue
        if line.startswith(
            ("-r", "--requirement", "-c", "--constraint", "-e", "--editable")
        ):
            continue
        if line.startswith(("git+", "http://", "https://", ".", "/")):
            match = re.search(r"#egg=([A-Za-z0-9_.-]+)", line)
            if match:
                deps.add(match.group(1).lower())
            continue

        dep_spec = normalize_dependency_spec(line)
        if dep_spec:
            deps.add(dep_spec)

    return deps


def parse_pyproject_dependencies(content: str) -> set[str]:
    deps = parse_pyproject_dependencies_toml(content)
    if deps:
        return deps
    return parse_pyproject_dependencies_fallback(content)


def parse_pyproject_dependencies_toml(content: str) -> set[str]:
    if tomllib is None:
        return set()

    try:
        payload = tomllib.loads(content)
    except Exception:
        return set()

    deps: set[str] = set()

    project = payload.get("project")
    if isinstance(project, dict):
        deps.update(parse_dependency_list(project.get("dependencies")))
        optional = project.get("optional-dependencies")
        if isinstance(optional, dict):
            for value in optional.values():
                deps.update(parse_dependency_list(value))

    tool = payload.get("tool")
    if isinstance(tool, dict):
        poetry = tool.get("poetry")
        if isinstance(poetry, dict):
            deps.update(parse_poetry_dependency_table(poetry.get("dependencies")))
            groups = poetry.get("group")
            if isinstance(groups, dict):
                for group_payload in groups.values():
                    if isinstance(group_payload, dict):
                        deps.update(
                            parse_poetry_dependency_table(
                                group_payload.get("dependencies")
                            )
                        )

    return deps


def parse_pyproject_dependencies_fallback(content: str) -> set[str]:
    deps: set[str] = set()

    for match in re.finditer(
        r"dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL | re.IGNORECASE
    ):
        block = match.group(1)
        deps.update(parse_dependency_list(re.findall(r"['\"]([^'\"]+)['\"]", block)))

    for section in re.finditer(
        r"^\[tool\.poetry(?:\.group\.[^\]]+)?\.dependencies\]\s*(.*?)(?=^\[|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    ):
        block = section.group(1)
        for match in re.finditer(
            r"^\s*([A-Za-z0-9_.-]+)\s*=\s*([^\n#]+)", block, re.MULTILINE
        ):
            dep_name = match.group(1).strip().lower()
            dep_value = match.group(2).strip()
            if dep_name == "python":
                continue
            if dep_value.startswith(('"', "'")) and dep_value.endswith(('"', "'")):
                dep_value = dep_value[1:-1].strip()
            if dep_value and dep_value not in {"*", "{}"}:
                deps.add(f"{dep_name}{dep_value}")
            else:
                deps.add(dep_name)

    return deps


def parse_dependency_list(value: Any) -> set[str]:
    deps: set[str] = set()
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                dep_spec = normalize_dependency_spec(item)
                if dep_spec:
                    deps.add(dep_spec)
    return deps


def parse_poetry_dependency_table(value: Any) -> set[str]:
    deps: set[str] = set()
    if isinstance(value, dict):
        for dep_name, dep_value in value.items():
            if not isinstance(dep_name, str):
                continue
            normalized = dep_name.strip().lower()
            if not normalized or normalized == "python":
                continue
            if isinstance(dep_value, str):
                spec = dep_value.strip()
                if spec and spec != "*":
                    deps.add(f"{normalized}{spec}")
                else:
                    deps.add(normalized)
            elif isinstance(dep_value, dict):
                version_value = dep_value.get("version")
                if (
                    isinstance(version_value, str)
                    and version_value.strip()
                    and version_value.strip() != "*"
                ):
                    deps.add(f"{normalized}{version_value.strip()}")
                else:
                    deps.add(normalized)
            else:
                deps.add(normalized)
    return deps


def extract_dependency_name(spec: str) -> str | None:
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", spec)
    if not match:
        return None
    return match.group(1).lower()


def normalize_dependency_spec(spec: str) -> str | None:
    cleaned = spec.strip()
    if not cleaned:
        return None
    # Remove inline environment markers for stable preview value.
    if ";" in cleaned:
        cleaned = cleaned.split(";", 1)[0].strip()
    name = extract_dependency_name(cleaned)
    if not name:
        return None

    suffix = cleaned[len(name) :].strip()
    if not suffix:
        return name
    return f"{name}{suffix}"


def read_package_deps(scanner: ProjectScanner) -> set[str]:
    deps: set[str] = set()

    for path in scanner.config_files:
        if path.name != "package.json":
            continue

        content = scanner.get_content(path)
        if not content:
            continue

        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            continue

        for key in (
            "dependencies",
            "devDependencies",
            "peerDependencies",
            "optionalDependencies",
        ):
            values = payload.get(key)
            if isinstance(values, dict):
                deps.update(values.keys())

    return deps
