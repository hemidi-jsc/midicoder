# coding: utf-8
"""
Unit tests cho DocParser của CP26.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp26_documentation.parser import DocParser
from midicoder.packs.cp26_documentation.models import DocPortalType
from midicoder.errors import MidicoderError


class TestDocParser:
    """Test DocParser class."""

    def setup_method(self) -> None:
        self.parser = DocParser()

    def test_parse_empty(self) -> None:
        """Parse string rỗng trả về collection rỗng."""
        result = self.parser.parse("")
        assert len(result.portals) == 0

    def test_parse_invalid_yaml(self) -> None:
        """Parse YAML không hợp lệ throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse("::: invalid :::")

    def test_parse_portal(self) -> None:
        """Parse portal definition."""
        yaml_str = """
doc_portals:
  - id: main_docs
    type: mkdocs
    title: "Project Docs"
    sections:
      - id: index
        title: Home
        path: index.md
"""
        result = self.parser.parse(yaml_str)
        assert len(result.portals) == 1
        assert result.portals[0].title == "Project Docs"
        assert len(result.portals[0].sections) == 1

    def test_parse_api_config(self) -> None:
        """Parse API doc config."""
        yaml_str = """
api_doc_configs:
  - id: api_v1
    title: "API Docs"
    openapi_version: "3.1.0"
"""
        result = self.parser.parse(yaml_str)
        assert len(result.api_configs) == 1
        assert result.api_configs[0].title == "API Docs"

    def test_parse_invalid_portal_type(self) -> None:
        """Portal type không hợp lệ throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse("""
doc_portals:
  - id: x
    type: invalid_type
    title: T
""")

    def test_parse_dict_input(self) -> None:
        """Parse dict input."""
        data = {"api_doc_configs": [{"id": "api", "title": "API"}]}
        result = self.parser.parse(data)
        assert len(result.api_configs) == 1

    def test_parse_from_metadata_with_entities(self) -> None:
        """Parse từ MIR metadata chứa entities."""
        metadata = {"entities": [{"id": "User"}], "commands": [{"id": "CreateUser"}]}
        result = self.parser.parse_from_metadata(metadata, stack="fastapi")
        assert len(result.portals) == 1
        assert len(result.portals[0].sections) >= 2

    def test_parse_from_metadata_react(self) -> None:
        """Parse frontend metadata tạo Storybook portal."""
        metadata = {"entities": [{"id": "Widget"}]}
        result = self.parser.parse_from_metadata(metadata, stack="react")
        assert result.portals[0].type == DocPortalType.STORYBOOK

    def test_parse_from_metadata_empty(self) -> None:
        """Metadata rỗng trả về collection rỗng."""
        result = self.parser.parse_from_metadata({}, stack="fastapi")
        assert len(result.portals) == 0
