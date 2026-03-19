#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".toml",
    ".ini",
    ".yml",
    ".yaml",
    ".json",
    ".txt",
    ".cfg",
}
SPECIAL_FILES = {"Jenkinsfile"}


parser = argparse.ArgumentParser()
parser.add_argument(
    "--all", action="store_true", help="Check all tracked files instead of changed files"
)
args = parser.parse_args()

mode_flag = "--all" if args.all else ""
command = ["python", "scripts/ci/list_changed_files.py", "--text-only"]
if mode_flag:
    command.append(mode_flag)

result = subprocess.run(command, check=True, capture_output=True, text=True)
paths = [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]
violations: list[str] = []

for path in paths:
    if path.name not in SPECIAL_FILES and path.suffix not in TEXT_EXTENSIONS:
        continue
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        if line.rstrip(" ") != line:
            violations.append(f"{path}:{idx}: trailing spaces are not allowed")
        if "\t" in line and path.suffix in {".py", ".md", ".toml", ".ini", ".yml", ".yaml"}:
            violations.append(f"{path}:{idx}: tabs are not allowed in this file type")
    if text and not text.endswith("\n"):
        violations.append(f"{path}: missing trailing newline at EOF")

if violations:
    print("Code convention check failed:")
    for item in violations:
        print("-", item)
    sys.exit(1)

scope = "all tracked files" if args.all else "changed files"
print(f"Code convention check passed for {scope}.")
