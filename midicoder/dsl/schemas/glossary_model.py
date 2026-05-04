from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta


class GlossaryTerm(BaseModel):
    id: str
    term: str
    definition: str
    description: Optional[str] = None
    category: Optional[str] = None
    synonyms: list[str] = Field(default_factory=list)
    related_terms: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    source: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


GLOSSARY_CATEGORY_CATALOG = {
    "business",
    "technical",
    "domain",
    "process",
    "integration",
    "api",
    "security",
    "data",
}


class Glossary(BaseModel):
    terms: list[GlossaryTerm]

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="meta.glossary",
        usage_en=(
            "Domain terminology and glossary definitions providing shared vocabulary "
            "and consistent understanding of business and technical terms across the project."
        ),
        included_by=[
            "domain.entity",
            "app.command",
            "app.query",
            "api.http_route",
            "workflow.definition",
        ],
        includes=[],
        real_world_examples=[
            "Business domain glossary for e-commerce platform",
            "Technical terminology for API documentation",
            "Industry-specific terms for healthcare software",
            "Financial services glossary for fintech apps",
            "Multi-language terminology for global applications",
        ],
        visualizers=[
            "Glossary documentation generators",
            "Term relationship diagrams",
            "Domain knowledge maps",
        ],
    )


class GlossaryFile(BaseModel):
    glossary: Glossary

    model_config = {"extra": "forbid"}
