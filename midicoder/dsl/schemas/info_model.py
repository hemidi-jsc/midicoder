from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta


class ProjectInfo(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    repository: Optional[str] = None
    homepage: Optional[str] = None
    documentation: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    stack: Optional[str] = None
    frameworks: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="meta.info",
        usage_en=(
            "Project metadata and information including version, description, technology stack, "
            "and other administrative details for the Midicoder contract specification."
        ),
        included_by=[],
        includes=[],
        real_world_examples=[
            "Project metadata for a SaaS application",
            "API service information and versioning",
            "Microservice documentation metadata",
            "Library or framework project details",
        ],
        visualizers=[
            "Project documentation generators",
            "Package.json equivalent viewers",
        ],
    )


class InfoFile(BaseModel):
    info: ProjectInfo

    model_config = {"extra": "forbid"}
