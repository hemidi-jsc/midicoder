# coding: utf-8
"""
Test cases cho CP34 recipes.

Kiểm tra:
- basic_report_recipe: Trả về collection đúng
- pdf_report_recipe: Có aggregation và grouping
- excel_export_recipe: Có XLSX và CSV
- batch_report_recipe: Có collection và batch job
"""

import pytest

from midicoder.packs.cp34_reporting.recipes import (
    basic_report_recipe,
    pdf_report_recipe,
    excel_export_recipe,
)
from midicoder.packs.cp34_reporting.models import (
    ReportCollection,
    ReportFormat,
)


class TestBasicReportRecipe:
    """Test basic_report_recipe."""

    def test_returns_collection(self):
        """Kiểm tra recipe trả về ReportCollection."""
        result = basic_report_recipe()
        assert isinstance(result, ReportCollection)

    def test_has_one_report(self):
        """Kiểm tra recipe có 1 report."""
        result = basic_report_recipe()
        assert len(result.reports) == 1

    def test_default_entity(self):
        """Kiểm tra entity mặc định là Product."""
        result = basic_report_recipe()
        assert result.reports[0].entity == "Product"

    def test_custom_entity(self):
        """Kiểm tra entity tùy chỉnh."""
        result = basic_report_recipe(entity="Order")
        assert result.reports[0].entity == "Order"

    def test_custom_fields(self):
        """Kiểm tra fields tùy chỉnh."""
        result = basic_report_recipe(fields=["id", "total", "status"])
        assert result.reports[0].fields == ["id", "total", "status"]

    def test_default_format(self):
        """Kiểm tra format mặc định là PDF."""
        result = basic_report_recipe()
        assert result.reports[0].format == ReportFormat.PDF

    def test_custom_format(self):
        """Kiểm tra format tùy chỉnh."""
        result = basic_report_recipe(format=ReportFormat.XLSX)
        assert result.reports[0].format == ReportFormat.XLSX


class TestPDFReportRecipe:
    """Test pdf_report_recipe."""

    def test_returns_collection(self):
        """Kiểm tra recipe trả về ReportCollection."""
        result = pdf_report_recipe()
        assert isinstance(result, ReportCollection)

    def test_format_is_pdf(self):
        """Kiểm tra format là PDF."""
        result = pdf_report_recipe()
        assert result.reports[0].format == ReportFormat.PDF

    def test_has_aggregations(self):
        """Kiểm tra có aggregation mặc định."""
        result = pdf_report_recipe()
        assert len(result.reports[0].aggregations) > 0
        assert "COUNT" in result.reports[0].aggregations

    def test_custom_aggregations(self):
        """Kiểm tra aggregation tùy chỉnh."""
        result = pdf_report_recipe(aggregations=["AVG", "MIN"])
        assert result.reports[0].aggregations == ["AVG", "MIN"]

    def test_custom_group_by(self):
        """Kiểm tra group_by tùy chỉnh."""
        result = pdf_report_recipe(group_by="category")
        assert result.reports[0].group_by == "category"


class TestExcelExportRecipe:
    """Test excel_export_recipe."""

    def test_returns_collection(self):
        """Kiểm tra recipe trả về ReportCollection."""
        result = excel_export_recipe()
        assert isinstance(result, ReportCollection)

    def test_has_xlsx_report(self):
        """Kiểm tra có XLSX report."""
        result = excel_export_recipe()
        formats = [r.format for r in result.reports]
        assert ReportFormat.XLSX in formats

    def test_has_csv_by_default(self):
        """Kiểm tra có CSV mặc định."""
        result = excel_export_recipe()
        formats = [r.format for r in result.reports]
        assert ReportFormat.CSV in formats

    def test_no_csv_when_disabled(self):
        """Kiểm tra không có CSV khi disable."""
        result = excel_export_recipe(include_csv=False)
        formats = [r.format for r in result.reports]
        assert ReportFormat.CSV not in formats
        assert len(result.reports) == 1

    def test_two_reports_with_csv(self):
        """Kiểm tra 2 reports khi có CSV."""
        result = excel_export_recipe(include_csv=True)
        assert len(result.reports) == 2
