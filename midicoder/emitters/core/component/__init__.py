"""Core Component Emitter Package (P2-002-E).

Package này chứa frontend framework generator — app shell, routing, state store:
- Foundation: FrontendApp, RouteDefinition, StateStoreConfig + enums
- Parser: FrontendFrameworkParser
- Frontend Emitters: Angular (Standalone components), React (Functional components)
- Backend Emitters: FastAPI (config service), NestJS (config module)

Exports:
    Models: FrontendApp, RouteDefinition, StateStoreConfig, FrontendFramework, StateStoreType, RouterStrategy, AppShellLayout
    Parser: FrontendFrameworkParser, parse_frontend_dsl
    Frontend: AngularComponentEmitter, ReactComponentEmitter
    Backend: FastAPIFrontendEmitter, NestJSFrontendEmitter
"""

from midicoder.emitters.core.component.models import (
    AppShellLayout,
    FrontendApp,
    FrontendFramework,
    RouteDefinition,
    RouterStrategy,
    StateStoreConfig,
    StateStoreType,
)
from midicoder.emitters.core.component.parser import (
    FrontendFrameworkParser,
    parse_frontend_dsl,
)
from midicoder.emitters.core.component.angular import AngularComponentEmitter
from midicoder.emitters.core.component.react import ReactComponentEmitter
from midicoder.emitters.core.component.fastapi import FastAPIFrontendEmitter
from midicoder.emitters.core.component.nestjs import NestJSFrontendEmitter

__all__ = [
    # Models
    "FrontendApp",
    "RouteDefinition",
    "StateStoreConfig",
    # Enums
    "FrontendFramework",
    "StateStoreType",
    "RouterStrategy",
    "AppShellLayout",
    # Parser
    "FrontendFrameworkParser",
    "parse_frontend_dsl",
    # Frontend Emitters
    "AngularComponentEmitter",
    "ReactComponentEmitter",
    # Backend Emitters
    "FastAPIFrontendEmitter",
    "NestJSFrontendEmitter",
]