# coding: utf-8
"""
Test cases cho CP34 Report & Document Generator models.

Kiểm tra:
- ReportFormat, ReportLayout, AggregationFunc, BatchJobStatus: Enum values
- ReportSpec: Validation, serialization, aggregation/grouping checks
- BatchJob: Status transitions, retry logic, serialization
- ReportCollection: CRUD, filtering
"""

import pytest
from datetime import datetime, timezone

from midicoder.packs.cp_full_reporting.models import (
    AggregationFunc,
    BatchJob,
    BatchJobStatus,
    ReportCollection,
    ReportFormat,
    ReportLayout,
    ReportSpec,
)
from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Test Enums
# ===========================================================================


class TestReportFormat:
    """Test ReportFormat enum."""

    def test_all_formats_exist(self):
        """Kiểm tra tất cả report formats tồn tại."""
        assert ReportFormat.PDF.value == "pdf"
        assert ReportFormat.XLSX.value == "xlsx"
        assert ReportFormat.CSV.value == "csv"

    def test_total_formats(self):
        """Kiểm tra tổng số formats = 3."""
        assert len(ReportFormat) == 3


class TestReportLayout:
    """Test ReportLayout enum."""

    def test_all_layouts_exist(self):
        """Kiểm tra tất cả report layouts tồn tại."""
        assert ReportLayout.TABLE.value == "table"
        assert ReportLayout.DASHBOARD.value == "dashboard"
        assert ReportLayout.LIST.value == "list"

    def test_total_layouts(self):
        """Kiểm tra tổng số layouts = 3."""
        assert len(ReportLayout) == 3


class TestAggregationFunc:
    """Test AggregationFunc enum."""

    def test_all_funcs_exist(self):
        """Kiểm tra tất cả aggregation functions tồn tại."""
        assert AggregationFunc.SUM.value == "SUM"
        assert AggregationFunc.COUNT.value == "COUNT"
        assert AggregationFunc.AVG.value == "AVG"
        assert AggregationFunc.MIN.value == "MIN"
        assert AggregationFunc.MAX.value == "MAX"

    def test_total_funcs(self):
        """Kiểm tra tổng số funcs = 5."""
        assert len(AggregationFunc) == 5


class TestBatchJobStatus:
    """Test BatchJobStatus enum."""

    def test_all_statuses_exist(self):
        """Kiểm tra tất cả batch job statuses tồn tại."""
        assert BatchJobStatus.PENDING.value == "pending"
        assert BatchJobStatus.RUNNING.value == "running"
        assert BatchJobStatus.COMPLETED.value == "completed"
        assert BatchJobStatus.FAILED.value == "failed"
        assert BatchJobStatus.CANCELLED.value == "cancelled"

    def test_total_statuses(self):
        """Kiểm tra tổng số statuses = 5."""
        assert len(BatchJobStatus) == 5


# ===========================================================================
# Test ReportSpec
# ===========================================================================


class TestReportSpec:
    """Test ReportSpec dataclass."""

    def test_create_basic_spec(self):
        """Kiểm tra tạo report spec cơ bản."""
        spec = ReportSpec(
            id="product_report",
            name="Báo cáo sản phẩm",
            entity="Product",
            fields=["id", "name", "price"],
        )
        assert spec.id == "product_report"
        assert spec.name == "Báo cáo sản phẩm"
        assert spec.entity == "Product"
        assert spec.fields == ["id", "name", "price"]
        assert spec.format == ReportFormat.PDF
        assert spec.layout == ReportLayout.TABLE

    def test_create_spec_with_all_options(self):
        """Kiểm tra tạo report spec đầy đủ options."""
        spec = ReportSpec(
            id="order_summary",
            name="Tổng hợp đơn hàng",
            entity="Order",
            fields=["id", "total", "status"],
            filter={"status": "active"},
            format=ReportFormat.XLSX,
            layout=ReportLayout.DASHBOARD,
            group_by="status",
            aggregations=["SUM", "COUNT"],
            description="Báo cáo tổng hợp đơn hàng theo trạng thái",
        )
        assert spec.format == ReportFormat.XLSX
        assert spec.layout == ReportLayout.DASHBOARD
        assert spec.group_by == "status"
        assert spec.aggregations == ["SUM", "COUNT"]
        assert spec.filter == {"status": "active"}

    def test_empty_report_id_raises_error(self):
        """Kiểm tra báo lỗi khi report ID trống."""
        with pytest.raises(MidicoderError) as exc_info:
            ReportSpec(id="", name="Test", entity="Product")
        assert exc_info.value.code == ErrorCode.MDC-F22_EMPTY_REPORT_ID

    def test_empty_entity_raises_error(self):
        """Kiểm tra báo lỗi khi entity trống."""
        with pytest.raises(MidicoderError) as exc_info:
            ReportSpec(id="test_report", name="Test", entity="")
        assert exc_info.value.code == ErrorCode.MDC-F22_REPORT_SPEC_INVALID

    def test_invalid_aggregation_raises_error(self):
        """Kiểm tra báo lỗi khi aggregation function không hợp lệ."""
        with pytest.raises(MidicoderError) as exc_info:
            ReportSpec(
                id="test", name="Test", entity="Product",
                aggregations=["INVALID_FUNC"],
            )
        assert exc_info.value.code == ErrorCode.MDC-F22_INVALID_AGGREGATION

    def test_has_aggregation(self):
        """Kiểm tra has_aggregation trả về đúng."""
        spec_with_agg = ReportSpec(id="t1", name="T1", entity="P", aggregations=["SUM"])
        assert spec_with_agg.has_aggregation() is True

        spec_without_agg = ReportSpec(id="t2", name="T2", entity="P")
        assert spec_without_agg.has_aggregation() is False

    def test_needs_grouping(self):
        """Kiểm tra needs_grouping trả về đúng."""
        spec_with_group = ReportSpec(id="t1", name="T1", entity="P", group_by="category")
        assert spec_with_group.needs_grouping() is True

        spec_without_group = ReportSpec(id="t2", name="T2", entity="P", group_by="")
        assert spec_without_group.needs_grouping() is False

    def test_to_dict(self):
        """Kiểm tra serialize sang dict."""
        spec = ReportSpec(
            id="test",
            name="Test Report",
            entity="Product",
            fields=["id", "name"],
            format=ReportFormat.XLSX,
            layout=ReportLayout.DASHBOARD,
            group_by="category",
            aggregations=["SUM"],
            description="Mô tả test",
        )
        d = spec.to_dict()
        assert d["id"] == "test"
        assert d["name"] == "Test Report"
        assert d["entity"] == "Product"
        assert d["fields"] == ["id", "name"]
        assert d["format"] == "xlsx"
        assert d["layout"] == "dashboard"
        assert d["group_by"] == "category"
        assert d["aggregations"] == ["SUM"]
        assert d["description"] == "Mô tả test"

    def test_from_dict(self):
        """Kiểm tra deserialize từ dict."""
        d = {
            "id": "test",
            "name": "Test Report",
            "entity": "Product",
            "fields": ["id", "name"],
            "format": "xlsx",
            "layout": "dashboard",
            "group_by": "category",
            "aggregations": ["SUM"],
            "description": "Mô tả",
            "filter": {"status": "active"},
        }
        spec = ReportSpec.from_dict(d)
        assert spec.id == "test"
        assert spec.format == ReportFormat.XLSX
        assert spec.layout == ReportLayout.DASHBOARD
        assert spec.group_by == "category"

    def test_from_dict_defaults(self):
        """Kiểm tra from_dict với dict thiếu fields."""
        d = {"id": "min", "name": "Min", "entity": "E"}
        spec = ReportSpec.from_dict(d)
        assert spec.format == ReportFormat.PDF
        assert spec.layout == ReportLayout.TABLE
        assert spec.fields == []
        assert spec.aggregations == []

    def test_roundtrip(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = ReportSpec(
            id="rt", name="RoundTrip", entity="Order",
            format=ReportFormat.CSV, layout=ReportLayout.LIST,
            aggregations=["COUNT", "AVG"],
        )
        restored = ReportSpec.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.format == original.format
        assert restored.layout == original.layout
        assert restored.aggregations == original.aggregations


# ===========================================================================
# Test BatchJob
# ===========================================================================


class TestBatchJob:
    """Test BatchJob dataclass."""

    def test_create_batch_job(self):
        """Kiểm tra tạo batch job."""
        job = BatchJob(report_spec_ids=["r1", "r2", "r3"])
        assert len(job.report_spec_ids) == 3
        assert job.status == BatchJobStatus.PENDING
        assert job.retries == 0
        assert job.max_retries == 3
        assert job.result_urls == []

    def test_empty_report_ids_raises_error(self):
        """Kiểm tra báo lỗi khi không có report IDs."""
        with pytest.raises(MidicoderError) as exc_info:
            BatchJob(report_spec_ids=[])
        assert exc_info.value.code == ErrorCode.MDC-F22_BATCH_JOB_FAILED

    def test_can_retry(self):
        """Kiểm tra logic can_retry."""
        job = BatchJob(report_spec_ids=["r1"], max_retries=3)
        job.mark_failed("error")
        assert job.can_retry() is True

        # Sau 3 lần retry
        job.retries = 3
        assert job.can_retry() is False

        # Job không ở trạng thái FAILED
        job.status = BatchJobStatus.RUNNING
        assert job.can_retry() is False

    def test_mark_running(self):
        """Kiểm tra mark_running."""
        job = BatchJob(report_spec_ids=["r1"])
        job.mark_running()
        assert job.status == BatchJobStatus.RUNNING

    def test_mark_completed(self):
        """Kiểm tra mark_completed."""
        job = BatchJob(report_spec_ids=["r1"])
        job.mark_completed(["/url1"])
        assert job.status == BatchJobStatus.COMPLETED
        assert job.result_urls == ["/url1"]
        assert job.completed_at is not None

    def test_mark_failed(self):
        """Kiểm tra mark_failed."""
        job = BatchJob(report_spec_ids=["r1"])
        job.mark_failed("Lỗi hệ thống")
        assert job.status == BatchJobStatus.FAILED
        assert job.error == "Lỗi hệ thống"
        assert job.completed_at is not None

    def test_mark_cancelled(self):
        """Kiểm tra mark_cancelled."""
        job = BatchJob(report_spec_ids=["r1"])
        job.mark_running()
        job.mark_cancelled()
        assert job.status == BatchJobStatus.CANCELLED

    def test_to_dict(self):
        """Kiểm tra serialize sang dict."""
        job = BatchJob(report_spec_ids=["r1", "r2"])
        job.mark_completed(["/url1", "/url2"])
        d = job.to_dict()
        assert d["id"] == job.id
        assert d["status"] == "completed"
        assert d["report_spec_ids"] == ["r1", "r2"]
        assert d["result_urls"] == ["/url1", "/url2"]
        assert d["created_at"] is not None

    def test_from_dict(self):
        """Kiểm tra deserialize từ dict."""
        d = {
            "id": "job-123",
            "status": "running",
            "report_spec_ids": ["r1"],
            "created_at": "2026-05-21T10:00:00+00:00",
            "result_urls": [],
            "error": "",
            "retries": 1,
            "max_retries": 3,
        }
        job = BatchJob.from_dict(d)
        assert job.id == "job-123"
        assert job.status == BatchJobStatus.RUNNING
        assert job.retries == 1

    def test_roundtrip(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = BatchJob(report_spec_ids=["a", "b"], max_retries=5)
        original.mark_running()
        restored = BatchJob.from_dict(original.to_dict())
        assert restored.report_spec_ids == original.report_spec_ids
        assert restored.max_retries == original.max_retries


# ===========================================================================
# Test ReportCollection
# ===========================================================================


class TestReportCollection:
    """Test ReportCollection dataclass."""

    def test_create_empty_collection(self):
        """Kiểm tra tạo collection rỗng."""
        c = ReportCollection()
        assert len(c.reports) == 0

    def test_add_report(self):
        """Kiểm tra thêm report vào collection."""
        c = ReportCollection()
        spec = ReportSpec(id="r1", name="R1", entity="Product")
        c.add_report(spec)
        assert len(c.reports) == 1
        assert c.get_report_by_id("r1") is not None

    def test_duplicate_id_raises_error(self):
        """Kiểm tra báo lỗi khi thêm report ID trùng."""
        c = ReportCollection()
        c.add_report(ReportSpec(id="r1", name="R1", entity="P"))
        with pytest.raises(MidicoderError):
            c.add_report(ReportSpec(id="r1", name="R1_dup", entity="P"))

    def test_get_report_by_id_not_found(self):
        """Kiểm tra tìm report không tồn tại."""
        c = ReportCollection()
        assert c.get_report_by_id("nonexistent") is None

    def test_get_reports_by_format(self):
        """Kiểm tra lọc reports theo format."""
        c = ReportCollection()
        c.add_report(ReportSpec(id="r1", name="R1", entity="P", format=ReportFormat.PDF))
        c.add_report(ReportSpec(id="r2", name="R2", entity="P", format=ReportFormat.XLSX))
        c.add_report(ReportSpec(id="r3", name="R3", entity="P", format=ReportFormat.PDF))
        assert len(c.get_reports_by_format(ReportFormat.PDF)) == 2
        assert len(c.get_reports_by_format(ReportFormat.XLSX)) == 1
        assert len(c.get_reports_by_format(ReportFormat.CSV)) == 0

    def test_get_reports_by_entity(self):
        """Kiểm tra lọc reports theo entity."""
        c = ReportCollection()
        c.add_report(ReportSpec(id="r1", name="R1", entity="Product"))
        c.add_report(ReportSpec(id="r2", name="R2", entity="Order"))
        assert len(c.get_reports_by_entity("Product")) == 1
        assert len(c.get_reports_by_entity("Order")) == 1
        assert len(c.get_reports_by_entity("Customer")) == 0

    def test_to_dict(self):
        """Kiểm tra serialize sang dict."""
        c = ReportCollection()
        c.add_report(ReportSpec(id="r1", name="R1", entity="P"))
        d = c.to_dict()
        assert "reports" in d
        assert len(d["reports"]) == 1

    def test_from_dict(self):
        """Kiểm tra deserialize từ dict."""
        d = {
            "reports": [
                {"id": "r1", "name": "R1", "entity": "Product", "format": "pdf"},
                {"id": "r2", "name": "R2", "entity": "Order", "format": "xlsx"},
            ]
        }
        c = ReportCollection.from_dict(d)
        assert len(c.reports) == 2
        assert c.reports[0].format == ReportFormat.PDF
        assert c.reports[1].format == ReportFormat.XLSX

    def test_roundtrip(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = ReportCollection()
        original.add_report(ReportSpec(id="r1", name="R1", entity="P", format=ReportFormat.CSV))
        restored = ReportCollection.from_dict(original.to_dict())
        assert len(restored.reports) == 1
        assert restored.reports[0].id == "r1"
        assert restored.reports[0].format == ReportFormat.CSV
