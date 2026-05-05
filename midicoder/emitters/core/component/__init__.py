"""Core Component Emitter Package (P2-002-E).

Package này chứa frontend component emitters cho UI components:
- Angular: Standalone components (List, Detail, Form, Dashboard, Shell)
- React: Functional components (ListView, DetailView, FormView, Dashboard, Layout)

Exports:
    Angular: AngularComponentEmitter
    React: ReactComponentEmitter
"""

from midicoder.emitters.core.component.angular import AngularComponentEmitter
from midicoder.emitters.core.component.react import ReactComponentEmitter

__all__ = [
    "AngularComponentEmitter",
    "ReactComponentEmitter",
]