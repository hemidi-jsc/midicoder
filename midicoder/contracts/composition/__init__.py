"""
CP51: Blueprint Composition Engine.

Module cung cấp engine để compose CompiledBlueprint thành
CompositionPlan — kế hoạch thi công chi tiết cho code gen.

Author: Midicoder Team
Version: 1.0.0
"""

from .models import (
    CompositionNode,
    PackResolution,
    TemplateBinding,
    StackBinding,
    CompositionPlan,
)
from .resolver import PackResolver
from .engine import CompositionEngine

__all__ = [
    "CompositionNode",
    "PackResolution",
    "TemplateBinding",
    "StackBinding",
    "CompositionPlan",
    "PackResolver",
    "CompositionEngine",
]