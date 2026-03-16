"""Package.json dependency reader for JS ecosystems."""

from __future__ import annotations

import json

from ..core.scanner import ProjectScanner


def read_package_dependencies(scanner: ProjectScanner) -> set[str]:
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

        for key in ("dependencies", "devDependencies", "peerDependencies"):
            values = payload.get(key)
            if isinstance(values, dict):
                deps.update(values.keys())

    return deps
