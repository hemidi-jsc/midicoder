#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

TEMPLATE = Path(".github/pull_request_template.md")
REQUIRED_HEADINGS = [
    "## Mục tiêu thay đổi",
    "## Thay đổi chính",
    "## Kiểm thử đã chạy",
    "## Docs và plans đã cập nhật",
    "## Chính sách review-ready",
]

if not TEMPLATE.exists():
    print("PR template is missing:", TEMPLATE)
    sys.exit(1)

content = TEMPLATE.read_text(encoding="utf-8")
missing = [heading for heading in REQUIRED_HEADINGS if heading not in content]
if missing:
    print("PR template is missing required headings:")
    for heading in missing:
        print("-", heading)
    sys.exit(1)

print("PR template policy passed.")
