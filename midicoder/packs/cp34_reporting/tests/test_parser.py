# coding: utf-8
"""
Test cases cho CP34 Report Parser.

Kiểm tra:
- ReportParser: Parse YAML DSL hợp lệ
- Error handling: Invalid YAML, invalid format, invalid layout, invalid aggregation
- Edge cases: Empty input, comment-only
- parse_from_metadata: Parse dict từ MIR
"""

import pytest

from midicoder.packs.cp34_reporting.parser import ReportParser
from midicoder.packs.cp34_reporting.models import (
    ReportCollection,
    ReportFormat,
    ReportLayout,
    ReportSpec,
)
from midicoder.errors import ErrorCode, MidicoderError


class TestReportParser:
    """Test ReportParser."""

    def setup_method(self):
        """Setup parser cho mỗi test."""
        self.parser = ReportParser()

    def test_parse_empty_string_returns_empty_collection(self):
        """Kiểm tra parse string rỗng trả về collection rỗng."""
        result = self.parser.parse("")
        assert isinstance(result, ReportCollection)
        assert len(result.reports) == 0

    def test_parse_whitespace_only_returns_empty_collection(self):
        """Kiểm tra parse whitespace trả về collection rỗng."""
        result = self.parser.parse("   \n\n  ")
        assert isinstance(result, ReportCollection)
        assert len(result.reports) == 0

    def test_parse_comment_only_returns_empty_collection(self):
        """Kiểm tra parse comment-only YAML trả về collection rỗng."""
        result = self.parser.parse("# Chỉ là comment\n# Không có data")
        assert isinstance(result, ReportCollection)
        assert len(result.reports) == 0

    def test_parse_single_report(self):
        """Kiểm tra parse 1 report spec."""
        dsl = """
reports:
  - id: product_report
    name: Báo cáo sản phẩm
    entity: Product
    fields: [id, name, price]
    format: pdf
    layout: table
"""
        result = self.parser.parse(dsl)
        assert len(result.reports) == 1
        spec = result.reports[0]
        assert spec.id == "product_report"
        assert spec.name == "Báo cáo sản phẩm"
        assert spec.entity == "Product"
        assert spec.fields == ["id", "name", "price"]
        assert spec.format == ReportFormat.PDF
        assert spec.layout == ReportLayout.TABLE

    def test_parse_multiple_reports(self):
        """Kiểm tra parse nhiều report specs."""
        dsl = """
reports:
  - id: product_pdf
    name: Product PDF
    entity: Product
    format: pdf
  - id: order_xlsx
    name: Order Excel
    entity: Order
    format: xlsx
  - id: customer_csv
    name: Customer CSV
    entity: Customer
    format: csv
"""
        result = self.parser.parse(dsl)
        assert len(result.reports) == 3
        assert result.reports[0].format == ReportFormat.PDF
        assert result.reports[1].format == ReportFormat.XLSX
        assert result.reports[2].format == ReportFormat.CSV

    def test_parse_report_with_filter_and_aggregation(self):
        """Kiểm tra parse report có filter, group_by, aggregations."""
        dsl = """
reports:
  - id: sales_summary
    name: Tổng hợp bán hàng
    entity: Order
    fields: [id, total, status]
    filter:
      status: active
    format: xlsx
    layout: dashboard
    group_by: status
    aggregations: [SUM, COUNT, AVG]
    description: Báo cáo tổng hợp
"""
        result = self.parser.parse(dsl)
        spec = result.reports[0]
        assert spec.filter == {"status": "active"}
        assert spec.group_by == "status"
        assert spec.aggregations == ["SUM", "COUNT", "AVG"]
        assert spec.layout == ReportLayout.DASHBOARD

    def test_parse_invalid_format_raises_error(self):
        """Kiểm tra báo lỗi khi format không hợp lệ."""
        dsl = """
reports:
  - id: bad_format
    name: Bad
    entity: Product
    format: invalid_format
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP34_INVALID_FORMAT

    def test_parse_invalid_layout_raises_error(self):
        """Kiểm tra báo lỗi khi layout không hợp lệ."""
        dsl = """
reports:
  - id: bad_layout
    name: Bad
    entity: Product
    layout: invalid_layout
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP34_INVALID_LAYOUT

    def test_parse_invalid_aggregation_raises_error(self):
        """Kiểm tra báo lỗi khi aggregation không hợp lệ."""
        dsl = """
reports:
  - id: bad_agg
    name: Bad
    entity: Product
    aggregations: [INVALID]
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP34_INVALID_AGGREGATION

    def test_parse_invalid_yaml_raises_error(self):
        """Kiểm tra báo lỗi khi YAML không hợp lệ."""
        dsl = "{{{{invalid yaml}}}"
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP34_PARSER_ERROR

    def test_parse_non_dict_yaml_raises_error(self):
        """Kiểm tra báo lỗi khi YAML không phải mapping."""
        dsl = "- just a list\n- not a mapping"
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP34_PARSER_ERROR

    def test_parse_defaults(self):
        """Kiểm tra defaults khi thiếu fields."""
        dsl = """
reports:
  - id: minimal
    name: Minimal
    entity: Product
"""
        result = self.parser.parse(dsl)
        spec = result.reports[0]
        assert spec.format == ReportFormat.PDF
        assert spec.layout == ReportLayout.TABLE
        assert spec.fields == []
        assert spec.aggregations == []
        assert spec.filter == {}
        assert spec.group_by == ""

    def test_parse_aggregation_case_insensitive(self):
        """Kiểm tra aggregation không phân biệt hoa thường."""
        dsl = """
reports:
  - id: case_test
    name: Case
    entity: Product
    aggregations: [sum, count, avg]
"""
        result = self.parser.parse(dsl)
        spec = result.reports[0]
        assert spec.aggregations == ["SUM", "COUNT", "AVG"]


class TestReportParserFromMetadata:
    """Test parse_from_metadata."""

    def setup_method(self):
        self.parser = ReportParser()

    def test_parse_empty_dict(self):
        """Kiểm tra parse dict rỗng."""
        result = self.parser.parse_from_metadata({})
        assert isinstance(result, ReportCollection)
        assert len(result.reports) == 0

    def test_parse_dict_with_reports(self):
        """Kiểm tra parse dict có reports."""
        data = {
            "reports": [
                {
                    "id": "r1",
                    "name": "Report 1",
                    "entity": "Product",
                    "fields": ["id", "name"],
                    "format": "pdf",
                }
            ]
        }
        result = self.parser.parse_from_metadata(data)
        assert len(result.reports) == 1
        assert result.reports[0].id == "r1"
        assert result.reports[0].format == ReportFormat.PDF

    def test_parse_non_dict_raises_error(self):
        """Kiểm tra parse non-dict báo lỗi."""
        with pytest.raises(MidicoderError):
            self.parser.parse_from_metadata("not a dict")

    def test_parse_with_multiple_reports(self):
        """Kiểm tra parse nhiều reports từ metadata."""
        data = {
            "reports": [
                {"id": "a", "name": "A", "entity": "E1", "format": "pdf"},
                {"id": "b", "name": "B", "entity": "E2", "format": "xlsx"},
                {"id": "c", "name": "C", "entity": "E3", "format": "csv"},
            ]
        }
        result = self.parser.parse_from_metadata(data)
        assert len(result.reports) == 3
