# coding: utf-8
"""
Unit tests cho models của Documentation Generator (CP26).

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp26_documentation.models import (
    ApiDocConfig,
    DocCollection,
    DocPortal,
    DocPortalType,
    DocSection,
)
from midicoder.errors import ErrorCode, MidicoderError


class TestApiDocConfig:
    """Test ApiDocConfig dataclass."""

    def test_create_config(self) -> None:
        """Tạo config hợp lệ."""
        c = ApiDocConfig(id="api_v1", title="Order API", version="1.0.0")
        assert c.openapi_version == "3.1.0"
        assert c.title == "Order API"

    def test_invalid_version(self) -> None:
        """Phiên bản OpenAPI không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            ApiDocConfig(id="x", title="T", openapi_version="2.0.0")
        assert exc_info.value.code == ErrorCode.CP26_INVALID_API_VERSION

    def test_empty_title(self) -> None:
        """Title rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            ApiDocConfig(id="x", title="")
        assert exc_info.value.code == ErrorCode.CP26_MISSING_SECTION_TITLE

    def test_to_dict(self) -> None:
        """to_dict trả về dict đầy đủ."""
        c = ApiDocConfig(
            id="api_v1", title="API", servers=[{"url": "http://localhost:8000"}],
        )
        d = c.to_dict()
        assert d["id"] == "api_v1"
        assert d["servers"][0]["url"] == "http://localhost:8000"


class TestDocSection:
    """Test DocSection dataclass."""

    def test_create_section(self) -> None:
        """Tạo section hợp lệ."""
        s = DocSection(id="s1", portal_id="p1", title="Entities", path="entities.md")
        assert s.content_source == "manual"
        assert s.enabled is True

    def test_empty_title(self) -> None:
        """Title rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            DocSection(id="s1", portal_id="p1", title="", path="x.md")
        assert exc_info.value.code == ErrorCode.CP26_MISSING_SECTION_TITLE

    def test_empty_path(self) -> None:
        """Path rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            DocSection(id="s1", portal_id="p1", title="T", path="")
        assert exc_info.value.code == ErrorCode.CP26_EMPTY_SECTION_PATH

    def test_invalid_source(self) -> None:
        """Source không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            DocSection(id="s1", portal_id="p1", title="T", path="x.md", content_source="invalid")
        assert exc_info.value.code == ErrorCode.CP26_SECTION_SOURCE_INVALID

    def test_to_dict(self) -> None:
        """to_dict trả về dict đầy đủ."""
        s = DocSection(id="s1", portal_id="p1", title="T", path="p.md", content_source="entities")
        d = s.to_dict()
        assert d["content_source"] == "entities"


class TestDocPortal:
    """Test DocPortal dataclass."""

    def test_create_portal(self) -> None:
        """Tạo portal hợp lệ."""
        p = DocPortal(id="p1", type=DocPortalType.MKDOCS, title="Docs")
        assert p.sections == []

    def test_empty_title(self) -> None:
        """Title rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            DocPortal(id="p1", type=DocPortalType.MKDOCS, title="")
        assert exc_info.value.code == ErrorCode.CP26_EMPTY_PORTAL_NAME

    def test_add_section(self) -> None:
        """Thêm section vào portal."""
        p = DocPortal(id="p1", type=DocPortalType.MKDOCS, title="Docs")
        s = DocSection(id="s1", portal_id="p1", title="T", path="x.md")
        p.add_section(s)
        assert len(p.sections) == 1
        assert p.sections[0].portal_id == "p1"

    def test_duplicate_section(self) -> None:
        """Thêm section trùng ID throw error."""
        p = DocPortal(id="p1", type=DocPortalType.MKDOCS, title="Docs")
        p.add_section(DocSection(id="s1", portal_id="p1", title="T", path="x.md"))
        with pytest.raises(MidicoderError) as exc_info:
            p.add_section(DocSection(id="s1", portal_id="p1", title="T2", path="y.md"))
        assert exc_info.value.code == ErrorCode.CP26_DUPLICATE_SECTION_ID

    def test_get_enabled_sections(self) -> None:
        """Lọc sections active."""
        p = DocPortal(id="p1", type=DocPortalType.MKDOCS, title="Docs")
        p.add_section(DocSection(id="s1", portal_id="p1", title="T", path="x.md", enabled=True))
        p.add_section(DocSection(id="s2", portal_id="p1", title="T", path="y.md", enabled=False))
        assert len(p.get_enabled_sections()) == 1

    def test_to_dict(self) -> None:
        """to_dict trả về dict đầy đủ."""
        p = DocPortal(id="p1", type=DocPortalType.MKDOCS, title="Docs")
        p.add_section(DocSection(id="s1", portal_id="p1", title="T", path="x.md"))
        d = p.to_dict()
        assert d["type"] == "mkdocs"
        assert len(d["sections"]) == 1


class TestDocCollection:
    """Test DocCollection dataclass."""

    def test_empty(self) -> None:
        """Tạo collection rỗng."""
        c = DocCollection()
        assert c.portals == []
        assert c.api_configs == []

    def test_add_portal_and_config(self) -> None:
        """Thêm portal và API config."""
        c = DocCollection()
        c.add_portal(DocPortal(id="p1", type=DocPortalType.MKDOCS, title="Docs"))
        c.add_api_config(ApiDocConfig(id="api", title="API"))
        assert len(c.portals) == 1
        assert len(c.api_configs) == 1

    def test_get_portals_by_type(self) -> None:
        """Lọc portals theo type."""
        c = DocCollection()
        c.add_portal(DocPortal(id="p1", type=DocPortalType.MKDOCS, title="D"))
        c.add_portal(DocPortal(id="p2", type=DocPortalType.STORYBOOK, title="S"))
        assert len(c.get_portals_by_type(DocPortalType.MKDOCS)) == 1
        assert len(c.get_portals_by_type(DocPortalType.STORYBOOK)) == 1

    def test_get_all_sections(self) -> None:
        """Lấy tất cả sections."""
        c = DocCollection()
        p = DocPortal(id="p1", type=DocPortalType.MKDOCS, title="Docs")
        p.add_section(DocSection(id="s1", portal_id="p1", title="T", path="x.md"))
        p.add_section(DocSection(id="s2", portal_id="p1", title="T", path="y.md"))
        c.add_portal(p)
        assert len(c.get_all_sections()) == 2

    def test_count_sections(self) -> None:
        """Đếm sections theo source."""
        c = DocCollection()
        p = DocPortal(id="p1", type=DocPortalType.MKDOCS, title="Docs")
        p.add_section(DocSection(id="s1", portal_id="p1", title="T", path="x.md", content_source="entities"))
        p.add_section(DocSection(id="s2", portal_id="p1", title="T", path="y.md", content_source="commands"))
        c.add_portal(p)
        counts = c.count_sections()
        assert counts["entities"] == 1
        assert counts["commands"] == 1

    def test_to_dict_and_from_dict(self) -> None:
        """to_dict và from_dict là inverse."""
        c = DocCollection()
        p = DocPortal(id="p1", type=DocPortalType.MKDOCS, title="Docs")
        p.add_section(DocSection(id="s1", portal_id="p1", title="Entities", path="entities.md", content_source="entities"))
        p.api_config = ApiDocConfig(id="api", title="API")
        c.add_portal(p)

        d = c.to_dict()
        c2 = DocCollection.from_dict(d)

        assert len(c2.portals) == 1
        assert c2.portals[0].title == "Docs"
        assert len(c2.portals[0].sections) == 1
        assert c2.portals[0].api_config.title == "API"
