"""
midicoder.presets — Preset CSS styles cho 5 UI framework variants.

Mỗi preset file (YAML) chứa đầy đủ CSS properties cho tất cả components
trong stack React + Angular. Preset được load bởi StyleResolver và dùng
làm layer thấp nhất trong 4-layer merge chain.

Preset files:
    - material.yml   — Angular Material / React Material-UI
    - tailwind.yml   — Tailwind CSS utility classes
    - bootstrap.yml  — Bootstrap (4/5)
    - antd.yml       — Ant Design
    - carbon.yml     — IBM Carbon Design

Preset load path: midicoder/presets/{name}.yml
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

_PRESETS_DIR = Path(__file__).parent


def load_preset(name: str) -> dict[str, Any]:
    """Load một preset YAML file."""
    p = _PRESETS_DIR / f"{name}.yml"
    if not p.exists():
        return {}
    with open(p) as f:
        return yaml.safe_load(f) or {}


def list_presets() -> list[str]:
    """List tất cả available preset names."""
    return sorted(
        stem
        for stem in [p.stem for p in _PRESETS_DIR.glob("*.yml")]
        if stem != "__init__"
    )
