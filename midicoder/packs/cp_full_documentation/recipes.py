# coding: utf-8
"""
Mô-đun recipes cho Documentation Generator (CP26).

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.packs.cp_full_documentation.models import (
    ApiDocConfig,
    DocCollection,
    DocPortal,
    DocPortalType,
    DocSection,
)


def auto_generate_docs_from_mir(
    metadata: dict[str, Any],
    stack: str = "fastapi",
) -> DocCollection:
    """Tự động tạo doc portal từ MIR metadata. Trả về collection rỗng nếu không có dữ liệu."""
    entities = metadata.get("entities", [])
    commands = metadata.get("commands", [])
    queries = metadata.get("queries", [])
    if not entities and not commands and not queries:
        return DocCollection()

    collection = DocCollection()
    portal_type = DocPortalType.MKDOCS if stack in ("fastapi", "nestjs") else DocPortalType.STORYBOOK
    portal = DocPortal(
        id=f"{stack}_docs",
        type=portal_type,
        title=f"{stack.title()} Documentation",
    )

    if entities:
        portal.add_section(DocSection(
            id="entities", portal_id=portal.id, title="Entities",
            path="entities.md", content_source="entities",
        ))

    if commands:
        portal.add_section(DocSection(
            id="commands", portal_id=portal.id, title="Commands",
            path="commands.md", content_source="commands",
        ))

    if queries:
        portal.add_section(DocSection(
            id="queries", portal_id=portal.id, title="Queries",
            path="queries.md", content_source="queries",
        ))

    portal.api_config = ApiDocConfig(
        id=f"{stack}_api", title=f"{stack.title()} API",
        version="1.0.0", servers=[{"url": "http://localhost:8000", "description": "Local dev"}],
    )
    collection.add_portal(portal)
    return collection


def generate_api_docs(
    title: str,
    version: str = "1.0.0",
    entities: list[dict[str, Any]] | None = None,
    commands: list[dict[str, Any]] | None = None,
) -> DocCollection:
    """Sinh API docs (OpenAPI/Swagger) từ entities và commands."""
    collection = DocCollection()
    config = ApiDocConfig(
        id="api_spec", title=title, version=version,
        servers=[{"url": "http://localhost:8000", "description": "Local dev"}],
    )
    collection.add_api_config(config)
    return collection


def generate_component_docs(
    components: list[str],
    stack: str = "react",
) -> DocCollection:
    """Sinh component docs (Storybook stories)."""
    collection = DocCollection()
    portal = DocPortal(
        id=f"{stack}_storybook", type=DocPortalType.STORYBOOK,
        title=f"{stack.title()} Components",
    )
    for comp in components:
        portal.add_section(DocSection(
            id=f"comp_{comp.lower()}", portal_id=portal.id,
            title=comp, path=f"components/{comp.lower()}.md",
            content_source="manual",
        ))
    collection.add_portal(portal)
    return collection


def generate_project_docs(
    title: str,
    description: str = "",
    stack: str = "fastapi",
) -> DocCollection:
    """Sinh project documentation portal."""
    collection = DocCollection()
    portal_type = DocPortalType.MKDOCS if stack in ("fastapi", "nestjs") else DocPortalType.STORYBOOK
    portal = DocPortal(id=f"{stack}_portal", type=portal_type, title=title, description=description)
    portal.add_section(DocSection(
        id="index", portal_id=portal.id, title="Home",
        path="index.md", content_source="manual",
    ))
    collection.add_portal(portal)
    return collection
