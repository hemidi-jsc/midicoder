# coding: utf-8
"""
Mô-đun parser cho Report & Document Generator (CP34).

Parse YAML DSL thành ReportCollection chứa:
- ReportSpec: Spec cho 1 report (entity, fields, format, layout, aggregations)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.packs.cp_full_reporting.models import (
    AggregationFunc,
    ReportCollection,
    ReportFormat,
    ReportLayout,
    ReportSpec,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class ReportParser:
    """
    Parser cho DSL report spec.

    Parse YAML DSL thành ReportCollection.

    Ví dụ DSL:
        reports:
          - id: "product_report"
            name: "Báo cáo sản phẩm"
            entity: "Product"
            fields: ["id", "name", "price", "category"]
            filter:
              status: "active"
            format: "pdf"
            layout: "table"
            group_by: "category"
            aggregations: ["COUNT", "SUM"]
    """

    def parse(self, raw: str) -> ReportCollection:
        """
        Parse YAML DSL string thành ReportCollection.

        Args:
            raw: YAML string chứa danh sách report specs

        Returns:
            ReportCollection chứa report specs

        Raises:
            MidicoderError: Nếu YAML không hợp lệ hoặc parse thất bại
        """
        if not raw or not raw.strip():
            return ReportCollection()

        # Parse YAML
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.MDC-F22_PARSER_ERROR,
                message=f"Lỗi parse YAML report spec: {e}",
                error=str(e)
            )

        # YAML comment-only hoặc null → treat as empty collection
        if data is None:
            return ReportCollection()
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.MDC-F22_PARSER_ERROR,
                message="DSL report spec phải là YAML mapping"
            )

        collection = ReportCollection()

        # Parse reports
        raw_reports = data.get("reports", [])
        if isinstance(raw_reports, list):
            for report_data in raw_reports:
                report = self._parse_report_spec(report_data)
                collection.add_report(report)

        return collection

    def parse_from_metadata(self, data: dict[str, Any]) -> ReportCollection:
        """
        Parse dict từ MIR metadata thành ReportCollection.

        Args:
            data: Dict chứa report specs từ MIR metadata

        Returns:
            ReportCollection chứa report specs
        """
        if not isinstance(data, dict):
            EM.raise_error(ErrorCode.MDC-F22_PARSER_ERROR, message="Report metadata phải là dict")

        collection = ReportCollection()
        raw_reports = data.get("reports", [])

        if isinstance(raw_reports, list):
            for report_data in raw_reports:
                report = self._parse_report_spec(report_data)
                collection.add_report(report)

        return collection

    def _parse_report_spec(self, data: dict[str, Any]) -> ReportSpec:
        """
        Parse dict thành ReportSpec.

        Args:
            data: Dict chứa thông tin report spec

        Returns:
            ReportSpec instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(ErrorCode.MDC-F22_PARSER_ERROR, message="Report spec phải là YAML mapping")

        # Parse format
        fmt_str = data.get("format", "pdf")
        try:
            fmt = ReportFormat(fmt_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F22_INVALID_FORMAT,
                fmt=fmt_str,
                valid_formats=[f.value for f in ReportFormat]
            )

        # Parse layout
        layout_str = data.get("layout", "table")
        try:
            layout = ReportLayout(layout_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F22_INVALID_LAYOUT,
                layout=layout_str,
                valid_layouts=[l.value for l in ReportLayout]
            )

        # Validate aggregation functions
        aggregations = data.get("aggregations", [])
        valid_funcs = {af.value for af in AggregationFunc}
        for agg in aggregations:
            if agg.upper() not in valid_funcs:
                EM.raise_error(
                    ErrorCode.MDC-F22_INVALID_AGGREGATION,
                    func=agg,
                    valid_funcs=list(valid_funcs)
                )

        return ReportSpec(
            id=data.get("id", ""),
            name=data.get("name", ""),
            entity=data.get("entity", ""),
            fields=data.get("fields", []),
            filter=data.get("filter", {}),
            format=fmt,
            layout=layout,
            group_by=data.get("group_by", ""),
            aggregations=[a.upper() for a in aggregations],
            description=data.get("description", ""),
        )
