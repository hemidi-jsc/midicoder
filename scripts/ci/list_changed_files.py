#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
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


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def determine_base_ref() -> str:
    env_target = os.getenv("CHANGE_TARGET")
    if env_target:
        remote_ref = f"origin/{env_target}"
        try:
            git("rev-parse", "--verify", remote_ref)
            return git("merge-base", "HEAD", remote_ref)
        except subprocess.CalledProcessError:
            pass
    try:
        return git("rev-parse", "HEAD~1")
    except subprocess.CalledProcessError:
        return git("rev-parse", "HEAD")


parser = argparse.ArgumentParser()
parser.add_argument(
    "--all", action="store_true", help="List all tracked files instead of changed files"
)
parser.add_argument("--suffix", action="append", default=[], help="Filter by suffix")
parser.add_argument("--text-only", action="store_true", help="Keep only tracked text-like files")
args = parser.parse_args()

if args.all:
    raw_paths = [line for line in git("ls-files").splitlines() if line]
else:
    base = determine_base_ref()
    raw_paths = [line for line in git("diff", "--name-only", f"{base}...HEAD").splitlines() if line]

suffixes = tuple(args.suffix)
selected: list[str] = []
for raw in raw_paths:
    path = Path(raw)
    if suffixes and path.suffix not in suffixes:
        continue
    if args.text_only and path.name not in SPECIAL_FILES and path.suffix not in TEXT_EXTENSIONS:
        continue
    if path.exists() and path.is_file():
        selected.append(raw)

for item in selected:
    print(item)
