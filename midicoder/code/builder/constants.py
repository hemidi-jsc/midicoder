"""Shared constants for code build planner."""

from __future__ import annotations

CODE_PLAN_SCHEMA_VERSION = "1.0.0"

TARGET_MAP_FASTAPI: dict[str, str] = {
    "controller": "fastapi_endpoint",
    "route": "fastapi_route",
    "service": "fastapi_service",
    "model": "fastapi_model",
    "workflow": "fastapi_workflow",
    "projection": "fastapi_projection",
    "repository": "fastapi_repository",
}

TARGET_MAP_NEST: dict[str, str] = {
    "controller": "nest_endpoint",
    "route": "nest_route",
    "service": "nest_service",
    "model": "nest_model",
    "workflow": "nest_workflow",
    "projection": "nest_projection",
    "repository": "nest_repository",
}

GROUP_MAP: dict[str, str] = {
    "Command": "commands",
    "Query": "queries",
    "Projection": "projections",
    "Entity": "entities",
    "ValueObject": "value-objects",
    "Enum": "enums",
    "Workflow": "workflows",
    "HttpRoute": "api",
}
