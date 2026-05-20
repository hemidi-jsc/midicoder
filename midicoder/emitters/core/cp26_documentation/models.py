# coding: utf-8
"""
Mô-đun models cho Documentation Generator (CP26).

Định nghĩa các dataclass biểu diễn:
- DocPortalType: Enum các loại portal (mkdocs, docusaurus, storybook)
- DocPortal: Cấu hình documentation portal
- DocSection: 1 section trong portal
- ApiDocConfig: Cấu hình API docs (OpenAPI/Swagger)
- DocCollection: Output chính của DocParser

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class DocPortalType(str, Enum):
    """Enum các loại documentation portal."""
    MKDOCS = "mkdocs"
    DOCUSAURUS = "docusaurus"
    STORYBOOK = "storybook"

    __test__ = False  # Ngăn pytest thu thập enum làm test


# ===========================================================================
# ApiDocConfig
# ===========================================================================


@dataclass
class ApiDocConfig:
    """
    Cấu hình API documentation (OpenAPI/Swagger).

    Attributes:
        id: Định danh duy nhất
        openapi_version: Phiên bản OpenAPI spec (3.0.x, 3.1.0)
        title: Tiêu đề API
        description: Mô tả API (optional)
        version: Phiên bản API
        servers: Danh sách server URLs
    """
    __test__ = False  # Ngăn pytest thu thập enum làm test

    id: str
    openapi_version: str = "3.1.0"
    title: str = ""
    description: str = ""
    version: str = "1.0.0"
    servers: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate config sau khi khởi tạo."""
        valid_versions = {"3.0.0", "3.0.1", "3.0.2", "3.0.3", "3.1.0"}
        if self.openapi_version not in valid_versions:
            EM.raise_error(
                ErrorCode.CP26_INVALID_API_VERSION,
                version=self.openapi_version,
                valid=list(valid_versions)
            )
        if not self.title or not self.title.strip():
            EM.raise_error(ErrorCode.CP26_MISSING_SECTION_TITLE, field="api_doc.title")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển config sang dict format."""
        return {
            "id": self.id,
            "openapi_version": self.openapi_version,
            "title": self.title,
            "description": self.description,
            "version": self.version,
            "servers": self.servers,
        }


# ===========================================================================
# DocSection
# ===========================================================================


@dataclass
class DocSection:
    """
    1 section trong documentation portal.

    Attributes:
        id: Định danh duy nhất
        portal_id: ID của portal chứa section
        title: Tiêu đề section
        path: Đường dẫn relative
        content_source: Nguồn content (entities, commands, queries, manual)
        content: Nội dung markdown (optional)
        enabled: Có kích hoạt section không (default True)
    """
    __test__ = False  # Ngăn pytest thu thập enum làm test

    id: str
    portal_id: str
    title: str
    path: str
    content_source: str = "manual"
    content: str = ""
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate section sau khi khởi tạo."""
        if not self.title or not self.title.strip():
            EM.raise_error(
                ErrorCode.CP26_MISSING_SECTION_TITLE,
                section_id=self.id
            )
        if not self.path or not self.path.strip():
            EM.raise_error(
                ErrorCode.CP26_EMPTY_SECTION_PATH,
                section_id=self.id
            )
        valid_sources = {"entities", "commands", "queries", "events", "manual"}
        if self.content_source not in valid_sources:
            EM.raise_error(
                ErrorCode.CP26_SECTION_SOURCE_INVALID,
                source=self.content_source,
                valid=list(valid_sources)
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển section sang dict format."""
        return {
            "id": self.id,
            "portal_id": self.portal_id,
            "title": self.title,
            "path": self.path,
            "content_source": self.content_source,
            "content": self.content,
            "enabled": self.enabled,
        }


# ===========================================================================
# DocPortal
# ===========================================================================


@dataclass
class DocPortal:
    """
    Cấu hình documentation portal (MkDocs/Docusaurus/Storybook).

    Attributes:
        id: Định danh duy nhất
        type: Loại portal (mkdocs, docusaurus, storybook)
        title: Tiêu đề portal
        description: Mô tả portal (optional)
        theme: Theme CSS (optional)
        nav: Navigation entries (title: path)
        sections: Danh sách doc sections
        api_config: API doc config (optional)
    """
    __test__ = False  # Ngăn pytest thu thập enum làm test

    id: str
    type: DocPortalType
    title: str
    description: str = ""
    theme: str = ""
    nav: list[dict[str, str]] = field(default_factory=list)
    sections: list[DocSection] = field(default_factory=list)
    api_config: Optional[ApiDocConfig] = None

    def __post_init__(self) -> None:
        """Validate portal sau khi khởi tạo."""
        if not self.title or not self.title.strip():
            EM.raise_error(ErrorCode.CP26_EMPTY_PORTAL_NAME, field="portal.title")

    def add_section(self, section: DocSection) -> None:
        """Thêm section vào portal."""
        if self.get_section_by_id(section.id):
            EM.raise_error(
                ErrorCode.CP26_DUPLICATE_SECTION_ID,
                id=section.id,
                portal_id=self.id
            )
        section.portal_id = self.id
        self.sections.append(section)

    def get_section_by_id(self, section_id: str) -> Optional[DocSection]:
        """Tìm section theo ID."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def get_enabled_sections(self) -> list[DocSection]:
        """Lọc các sections đang active."""
        return [s for s in self.sections if s.enabled]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển portal sang dict format."""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "theme": self.theme,
            "nav": self.nav,
            "sections": [s.to_dict() for s in self.sections],
            "api_config": self.api_config.to_dict() if self.api_config else None,
        }


# ===========================================================================
# DocCollection — output chính của DocParser
# ===========================================================================


@dataclass
class DocCollection:
    """
    Collection chứa tất cả doc portals, sections, và API configs.

    Dùng làm output của DocParser và input cho Stack Emitters.

    Attributes:
        portals: Danh sách doc portals
        api_configs: Danh sách API doc configs
    """
    __test__ = False  # Ngăn pytest thu thập enum làm test

    portals: list[DocPortal] = field(default_factory=list)
    api_configs: list[ApiDocConfig] = field(default_factory=list)

    def add_portal(self, portal: DocPortal) -> None:
        """Thêm doc portal vào collection."""
        self.portals.append(portal)

    def add_api_config(self, config: ApiDocConfig) -> None:
        """Thêm API config vào collection."""
        self.api_configs.append(config)

    def get_portals_by_type(self, portal_type: DocPortalType) -> list[DocPortal]:
        """Lọc portals theo type."""
        return [p for p in self.portals if p.type == portal_type]

    def get_all_sections(self) -> list[DocSection]:
        """Lấy tất cả sections từ mọi portal."""
        sections: list[DocSection] = []
        for portal in self.portals:
            sections.extend(portal.sections)
        return sections

    def get_sections_by_source(self, source: str) -> list[DocSection]:
        """Lọc sections theo content source."""
        return [s for s in self.get_all_sections() if s.content_source == source]

    def count_sections(self) -> dict[str, int]:
        """Đếm số sections theo source."""
        counts: dict[str, int] = {}
        for section in self.get_all_sections():
            src = section.content_source
            counts[src] = counts.get(src, 0) + 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "portals": [p.to_dict() for p in self.portals],
            "api_configs": [c.to_dict() for c in self.api_configs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocCollection":
        """Tạo DocCollection từ dict."""
        collection = cls()

        # Parse portals
        for portal_data in data.get("portals", []):
            portal = DocPortal(
                id=portal_data["id"],
                type=DocPortalType(portal_data["type"]),
                title=portal_data["title"],
                description=portal_data.get("description", ""),
                theme=portal_data.get("theme", ""),
                nav=portal_data.get("nav", []),
            )

            # Parse API config
            if portal_data.get("api_config"):
                portal.api_config = ApiDocConfig(**portal_data["api_config"])

            # Parse sections
            for section_data in portal_data.get("sections", []):
                section = DocSection(
                    id=section_data["id"],
                    portal_id=portal_data["id"],
                    title=section_data["title"],
                    path=section_data["path"],
                    content_source=section_data.get("content_source", "manual"),
                    content=section_data.get("content", ""),
                    enabled=section_data.get("enabled", True),
                )
                portal.add_section(section)

            collection.add_portal(portal)

        # Parse standalone API configs
        for config_data in data.get("api_configs", []):
            config = ApiDocConfig(**config_data)
            collection.add_api_config(config)

        return collection
