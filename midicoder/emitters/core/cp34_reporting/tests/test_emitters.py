# coding: utf-8
"""
Test cases cho CP34 stack emitters (FastAPI, NestJS, Angular, React).

Kiểm tra:
- FastAPIReportEmitter: emit() trả về đầy đủ files
- NestJSReportEmitter: emit() trả về đầy đủ files
- AngularReportEmitter: emit() trả về components
- ReactReportEmitter: emit() trả về components
- Empty collection raises error
"""

import pytest
from pathlib import Path

from midicoder.emitters.core.cp34_reporting.models import (
    ReportCollection,
    ReportFormat,
    ReportLayout,
    ReportSpec,
)
from midicoder.emitters.core.cp34_reporting.fastapi import FastAPIReportEmitter
from midicoder.emitters.core.cp34_reporting.nestjs import NestJSReportEmitter
from midicoder.emitters.core.cp34_reporting.angular import AngularReportEmitter
from midicoder.emitters.core.cp34_reporting.react import ReactReportEmitter
from midicoder.errors import ErrorCode, MidicoderError


def _make_collection():
    """Tạo collection mẫu cho test."""
    c = ReportCollection()
    c.add_report(ReportSpec(
        id="product_report",
        name="Báo cáo sản phẩm",
        entity="Product",
        fields=["id", "name", "price"],
        format=ReportFormat.PDF,
    ))
    c.add_report(ReportSpec(
        id="order_export",
        name="Xuất đơn hàng",
        entity="Order",
        fields=["id", "total", "status"],
        format=ReportFormat.XLSX,
    ))
    return c


# ===========================================================================
# Test FastAPIReportEmitter
# ===========================================================================


class TestFastAPIReportEmitter:
    """Test FastAPIReportEmitter."""

    def test_emit_returns_list_of_dicts(self):
        """Kiểm tra emit trả về list của dict có path và content."""
        emitter = FastAPIReportEmitter()
        result = emitter.emit(_make_collection())
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, dict)
            assert "path" in item
            assert "content" in item

    def test_emit_has_all_files(self):
        """Kiểm tra emit có đầy đủ các file cần thiết."""
        emitter = FastAPIReportEmitter()
        result = emitter.emit(_make_collection())
        paths = [item["path"] for item in result]
        assert any("report_service" in p for p in paths)
        assert any("reports" in p for p in paths)  # app/routes/reports.py
        assert any("report_worker" in p for p in paths)
        assert any("pdf_generator" in p for p in paths)
        assert any("excel_generator" in p for p in paths)
        assert any("csv_generator" in p for p in paths)

    def test_emit_content_has_report_ids(self):
        """Kiểm tra content có chứa report IDs."""
        emitter = FastAPIReportEmitter()
        result = emitter.emit(_make_collection())
        all_content = " ".join(item["content"] for item in result)
        assert "product_report" in all_content
        assert "order_export" in all_content

    def test_emit_empty_collection_raises_error(self):
        """Kiểm tra emit collection rỗng báo lỗi."""
        emitter = FastAPIReportEmitter()
        with pytest.raises(MidicoderError) as exc_info:
            emitter.emit(ReportCollection())
        assert exc_info.value.code == ErrorCode.CP34_REPORT_SPEC_INVALID

    def test_generate_service_has_pdf_import(self):
        """Kiểm tra service có import PDFGenerator khi có PDF format."""
        emitter = FastAPIReportEmitter()
        result = emitter.emit(_make_collection())
        service = [i for i in result if "report_service" in i["path"]]
        assert len(service) == 1
        assert "PDFGenerator" in service[0]["content"]

    def test_generate_service_has_excel_import(self):
        """Kiểm tra service có import ExcelGenerator khi có XLSX format."""
        emitter = FastAPIReportEmitter()
        result = emitter.emit(_make_collection())
        service = [i for i in result if "report_service" in i["path"]]
        assert "ExcelGenerator" in service[0]["content"]


# ===========================================================================
# Test NestJSReportEmitter
# ===========================================================================


class TestNestJSReportEmitter:
    """Test NestJSReportEmitter."""

    def test_emit_returns_list_of_dicts(self):
        """Kiểm tra emit trả về list của dict."""
        emitter = NestJSReportEmitter()
        result = emitter.emit(_make_collection())
        assert isinstance(result, list)
        for item in result:
            assert "path" in item
            assert "content" in item

    def test_emit_has_all_files(self):
        """Kiểm tra emit có đầy đủ files NestJS."""
        emitter = NestJSReportEmitter()
        result = emitter.emit(_make_collection())
        paths = [item["path"] for item in result]
        assert any("report.service" in p for p in paths)
        assert any("report.controller" in p for p in paths)
        assert any("pdf-generator" in p for p in paths)
        assert any("excel-generator" in p for p in paths)
        assert any("csv-generator" in p for p in paths)
        assert any("batch-worker" in p for p in paths)

    def test_emit_has_typescript_syntax(self):
        """Kiểm tra content có cú pháp TypeScript."""
        emitter = NestJSReportEmitter()
        result = emitter.emit(_make_collection())
        all_content = " ".join(item["content"] for item in result)
        assert "export class" in all_content
        assert "interface" in all_content
        assert "@Injectable" in all_content or "@Controller" in all_content

    def test_emit_empty_collection_raises_error(self):
        """Kiểm tra emit collection rỗng báo lỗi."""
        emitter = NestJSReportEmitter()
        with pytest.raises(MidicoderError):
            emitter.emit(ReportCollection())


# ===========================================================================
# Test AngularReportEmitter
# ===========================================================================


class TestAngularReportEmitter:
    """Test AngularReportEmitter."""

    def test_emit_returns_list_of_dicts(self):
        """Kiểm tra emit trả về list của dict."""
        emitter = AngularReportEmitter()
        result = emitter.emit(_make_collection())
        assert isinstance(result, list)
        for item in result:
            assert "path" in item
            assert "content" in item

    def test_emit_has_all_components(self):
        """Kiểm tra emit có đầy đủ components."""
        emitter = AngularReportEmitter()
        result = emitter.emit(_make_collection())
        paths = [item["path"] for item in result]
        assert any("report-list" in p for p in paths)
        assert any("report-viewer" in p for p in paths)
        assert any("batch-status" in p for p in paths)

    def test_emit_has_angular_syntax(self):
        """Kiểm tra content có cú pháp Angular."""
        emitter = AngularReportEmitter()
        result = emitter.emit(_make_collection())
        all_content = " ".join(item["content"] for item in result)
        assert "@Component" in all_content
        assert "selector:" in all_content

    def test_emit_empty_collection_raises_error(self):
        """Kiểm tra emit collection rỗng báo lỗi."""
        emitter = AngularReportEmitter()
        with pytest.raises(MidicoderError):
            emitter.emit(ReportCollection())


# ===========================================================================
# Test ReactReportEmitter
# ===========================================================================


class TestReactReportEmitter:
    """Test ReactReportEmitter."""

    def test_emit_returns_list_of_dicts(self):
        """Kiểm tra emit trả về list của dict."""
        emitter = ReactReportEmitter()
        result = emitter.emit(_make_collection())
        assert isinstance(result, list)
        for item in result:
            assert "path" in item
            assert "content" in item

    def test_emit_has_all_components(self):
        """Kiểm tra emit có đầy đủ components."""
        emitter = ReactReportEmitter()
        result = emitter.emit(_make_collection())
        paths = [item["path"] for item in result]
        assert any("ReportList" in p for p in paths)
        assert any("ReportViewer" in p for p in paths)
        assert any("BatchStatus" in p for p in paths)

    def test_emit_has_react_syntax(self):
        """Kiểm tra content có cú pháp React."""
        emitter = ReactReportEmitter()
        result = emitter.emit(_make_collection())
        all_content = " ".join(item["content"] for item in result)
        assert "React.FC" in all_content or "React," in all_content
        assert "useState" in all_content or "useEffect" in all_content

    def test_emit_empty_collection_raises_error(self):
        """Kiểm tra emit collection rỗng báo lỗi."""
        emitter = ReactReportEmitter()
        with pytest.raises(MidicoderError):
            emitter.emit(ReportCollection())
