#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys

result = subprocess.run(
    ["python", "scripts/ci/list_changed_files.py"],
    check=True,
    capture_output=True,
    text=True,
)
changed = [line.strip() for line in result.stdout.splitlines() if line.strip()]

if not changed:
    print("No changed files detected; docs update policy skipped.")
    sys.exit(0)

code_changed = [path for path in changed if path.startswith("midicoder/") and path.endswith(".py")]
docs_changed = [
    path
    for path in changed
    if path == "README.md"
    or path == ".github/pull_request_template.md"
    or path.startswith("plans/")
    or path.startswith("docs/")
]

if code_changed and not docs_changed:
    print("Docs update policy failed.")
    print("Code changes detected without updates to README/docs/plans/PR template.")
    print("Changed code files:")
    for path in code_changed:
        print("-", path)
    sys.exit(1)

print("Docs update policy passed.")
