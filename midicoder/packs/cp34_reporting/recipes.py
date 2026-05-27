# coding: utf-8
"""
Recipe module cho CP34 Report & Document Generator.

Recipes cung cấp config sẵn dùng để map các use case phổ biến
thành ReportCollection vocabulary. Mỗi recipe trả về ReportCollection
với các ReportSpec đã được điền sẵn.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.packs.cp34_reporting.models import (
    BatchJob,
    BatchJobStatus,
    ReportCollection,
    ReportFormat,
    ReportLayout,
    ReportSpec,
)


# ===========================================================================
# Basic Report Recipe
# ===========================================================================


def basic_report_recipe(
    entity: str = "Product",
    fields: list[str] | None = None,
    format: ReportFormat = ReportFormat.PDF,
) -> ReportCollection:
    """
    Basic report recipe — báo cáo cơ bản cho 1 entity.

    Use case: Báo cáo danh sách entity với các fields cơ bản.

    Args:
        entity: Entity source
        fields: Danh sách fields (default: id, name)
        format: Định dạng output

    Returns:
        ReportCollection với 1 report spec cơ bản
    """
    collection = ReportCollection()

    collection.add_report(
        ReportSpec(
            id=f"{entity.lower()}_report",
            name=f"Báo cáo {entity}",
            entity=entity,
            fields=fields or ["id", "name"],
            format=format,
            layout=ReportLayout.TABLE,
            description=f"Báo cáo danh sách {entity} cơ bản",
        )
    )

    return collection


# ===========================================================================
# PDF Report Recipe
# ===========================================================================


def pdf_report_recipe(
    entity: str = "Order",
    fields: list[str] | None = None,
    group_by: str = "",
    aggregations: list[str] | None = None,
) -> ReportCollection:
    """
    PDF report recipe — báo cáo PDF với aggregation và grouping.

    Use case: Báo cáo tổng hợp với nhóm và thống kê.

    Args:
        entity: Entity source
        fields: Danh sách fields
        group_by: Nhóm theo field
        aggregations: Hàm aggregation (SUM, COUNT, AVG, MIN, MAX)

    Returns:
        ReportCollection với PDF report spec
    """
    collection = ReportCollection()

    collection.add_report(
        ReportSpec(
            id=f"{entity.lower()}_summary",
            name=f"Tổng hợp {entity}",
            entity=entity,
            fields=fields or ["id", "name", "total", "status"],
            format=ReportFormat.PDF,
            layout=ReportLayout.TABLE,
            group_by=group_by,
            aggregations=aggregations or ["COUNT", "SUM"],
            description=f"Báo cáo tổng hợp {entity} với thống kê",
        )
    )

    return collection


# ===========================================================================
# Excel Export Recipe
# ===========================================================================


def excel_export_recipe(
    entity: str = "Product",
    fields: list[str] | None = None,
    include_csv: bool = True,
) -> ReportCollection:
    """
    Excel export recipe — export dữ liệu sang Excel và CSV.

    Use case: Export toàn bộ data để phân tích ngoài Excel.

    Args:
        entity: Entity source
        fields: Danh sách fields
        include_csv: Có include CSV format không

    Returns:
        ReportCollection với Excel (+ CSV) report specs
    """
    collection = ReportCollection()

    collection.add_report(
        ReportSpec(
            id=f"{entity.lower()}_export_xlsx",
            name=f"Xuất {entity} (Excel)",
            entity=entity,
            fields=fields or ["id", "name", "created_at"],
            format=ReportFormat.XLSX,
            layout=ReportLayout.TABLE,
            description=f"Xuất dữ liệu {entity} sang Excel",
        )
    )

    if include_csv:
        collection.add_report(
            ReportSpec(
                id=f"{entity.lower()}_export_csv",
                name=f"Xuất {entity} (CSV)",
                entity=entity,
                fields=fields or ["id", "name", "created_at"],
                format=ReportFormat.CSV,
                layout=ReportLayout.TABLE,
                description=f"Xuất dữ liệu {entity} sang CSV",
            )
        )

    return collection


# ===========================================================================
# Batch Report Recipe
# ===========================================================================


def batch_report_recipe(
    entities: list[str] | None = None,
    formats: list[ReportFormat] | None = None,
) -> tuple[ReportCollection, BatchJob]:
    """
    Batch report recipe — generate nhiều reports cùng lúc.

    Use case: Generate tất cả reports hàng ngày/tuần.

    Args:
        entities: Danh sách entities cần report
        formats: Danh sách formats cần generate

    Returns:
        Tuple của (ReportCollection, BatchJob)
    """
    entities = entities or ["Product", "Order", "Customer"]
    formats = formats or [ReportFormat.PDF, ReportFormat.XLSX]

    collection = ReportCollection()
    report_ids: list[str] = []

    for entity in entities:
        for fmt in formats:
            report_id = f"{entity.lower()}_{fmt.value}_batch"
            collection.add_report(
                ReportSpec(
                    id=report_id,
                    name=f"{entity} Report ({fmt.value.upper()})",
                    entity=entity,
                    fields=["id", "name", "status", "created_at"],
                    format=fmt,
                    layout=ReportLayout.TABLE,
                    description=f"Báo cáo batch {entity} định dạng {fmt.value}",
                )
            )
            report_ids.append(report_id)

    job = BatchJob(
        report_spec_ids=report_ids,
        max_retries=3,
    )

    return collection, job


__all__ = [
    "basic_report_recipe",
    "pdf_report_recipe",
    "excel_export_recipe",
    "batch_report_recipe",
]
