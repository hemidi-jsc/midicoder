# coding: utf-8
"""
Mô-đun parser cho Documentation Generator (CP26).

Parse DSL doc nodes từ MIR metadata / Contract YAML thành DocCollection.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.packs.cp26_documentation.models import (
    ApiDocConfig,
    DocCollection,
    DocPortal,
    DocPortalType,
    DocSection,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class DocParser:
    """
    Parser cho DSL doc nodes.

    Parse YAML DSL hoặc dict metadata thành DocCollection.
    """

    def parse(self, raw: str | dict[str, Any]) -> DocCollection:
        """Parse YAML string hoặc dict thành DocCollection."""
        if isinstance(raw, str):
            if not raw or not raw.strip():
                return DocCollection()
            try:
                data = yaml.safe_load(raw)
            except yaml.YAMLError as e:
                EM.raise_error(
                    ErrorCode.CP26_DSL_PARSE_ERROR,
                    message=f"Lỗi parse YAML doc nodes: {e}",
                    error=str(e)
                )
            if data is None:
                return DocCollection()
        elif isinstance(raw, dict):
            data = raw
        else:
            return DocCollection()

        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP26_DSL_PARSE_ERROR,
                message="DSL doc nodes phải là YAML mapping"
            )

        return self._parse_from_dict(data)

    def parse_from_metadata(self, metadata: dict[str, Any], stack: str = "fastapi") -> DocCollection:
        """Parse từ MIR metadata dict."""
        collection = DocCollection()

        # Parse explicit doc portals
        portals_data = metadata.get("doc_portals", metadata.get("portals", []))
        if portals_data and isinstance(portals_data, list):
            for portal_data in portals_data:
                if isinstance(portal_data, dict):
                    portal = self._parse_portal(portal_data)
                    collection.add_portal(portal)

        # Parse API configs
        api_configs = metadata.get("api_doc_configs", metadata.get("api_docs", []))
        if api_configs and isinstance(api_configs, list):
            for config_data in api_configs:
                if isinstance(config_data, dict):
                    config = self._parse_api_config(config_data)
                    collection.add_api_config(config)

        # Auto-generate từ entities/commands nếu không có explicit docs VÀ có dữ liệu
        if not collection.portals and (metadata.get("entities") or metadata.get("commands") or metadata.get("queries")):
            collection = self._auto_generate_from_mir(metadata, stack)

        return collection

    def _auto_generate_from_mir(self, metadata: dict[str, Any], stack: str) -> DocCollection:
        """Tự động generate doc portal từ MIR metadata."""
        collection = DocCollection()

        portal_type = DocPortalType.MKDOCS if stack in ("fastapi", "nestjs") else DocPortalType.STORYBOOK
        portal = DocPortal(
            id=f"{stack}_docs",
            type=portal_type,
            title=f"{stack.title()} Documentation",
        )

        # Tạo section cho entities
        entities = metadata.get("entities", [])
        if entities:
            section = DocSection(
                id="entities",
                portal_id=portal.id,
                title="Entities",
                path="entities.md",
                content_source="entities",
            )
            portal.add_section(section)

        # Tạo section cho commands
        commands = metadata.get("commands", [])
        if commands:
            section = DocSection(
                id="commands",
                portal_id=portal.id,
                title="Commands",
                path="commands.md",
                content_source="commands",
            )
            portal.add_section(section)

        # Tạo section cho queries
        queries = metadata.get("queries", [])
        if queries:
            section = DocSection(
                id="queries",
                portal_id=portal.id,
                title="Queries",
                path="queries.md",
                content_source="queries",
            )
            portal.add_section(section)

        # Tạo API config
        api_config = ApiDocConfig(
            id=f"{stack}_api",
            title=f"{stack.title()} API",
            version="1.0.0",
            servers=[{"url": "http://localhost:8000", "description": "Local dev"}],
        )
        portal.api_config = api_config
        collection.add_portal(portal)

        return collection

    def _parse_from_dict(self, data: dict[str, Any]) -> DocCollection:
        """Parse từ dict đã load."""
        collection = DocCollection()

        # Parse portals
        for portal_data in data.get("doc_portals", data.get("portals", [])):
            if isinstance(portal_data, dict):
                portal = self._parse_portal(portal_data)
                collection.add_portal(portal)

        # Parse standalone API configs
        for config_data in data.get("api_doc_configs", data.get("api_docs", [])):
            if isinstance(config_data, dict):
                config = self._parse_api_config(config_data)
                collection.add_api_config(config)

        return collection

    def _parse_portal(self, data: dict[str, Any]) -> DocPortal:
        """Parse portal definition."""
        type_str = data.get("type", "mkdocs")
        try:
            portal_type = DocPortalType(type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP26_INVALID_PORTAL_TYPE,
                portal_type=type_str,
                valid=[t.value for t in DocPortalType]
            )

        portal = DocPortal(
            id=data.get("id", "default_docs"),
            type=portal_type,
            title=data.get("title", "Documentation"),
            description=data.get("description", ""),
            theme=data.get("theme", ""),
            nav=data.get("nav", []),
        )

        # Parse API config
        if data.get("api_config"):
            portal.api_config = self._parse_api_config(data["api_config"])

        # Parse sections
        for section_data in data.get("sections", []):
            if isinstance(section_data, dict):
                section = DocSection(
                    id=section_data.get("id", ""),
                    portal_id=portal.id,
                    title=section_data.get("title", ""),
                    path=section_data.get("path", ""),
                    content_source=section_data.get("content_source", "manual"),
                    content=section_data.get("content", ""),
                    enabled=section_data.get("enabled", True),
                )
                portal.add_section(section)

        return portal

    def _parse_api_config(self, data: dict[str, Any]) -> ApiDocConfig:
        """Parse API doc config."""
        return ApiDocConfig(
            id=data.get("id", "default_api"),
            openapi_version=data.get("openapi_version", "3.1.0"),
            title=data.get("title", "API Documentation"),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            servers=data.get("servers", []),
        )
