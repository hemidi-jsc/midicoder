# coding: utf-8
"""
CP34: Report & Document Generator.

Cung cấp:
- models: ReportSpec, BatchJob, ReportCollection, ReportFormat, ReportLayout
- parser: ReportParser
- fastapi: FastAPIReportEmitter (backend)
- nestjs: NestJSReportEmitter (backend)
- angular: AngularReportEmitter (frontend viewer)
- react: ReactReportEmitter (frontend viewer)
- recipes: report recipes cho CP51 composition
"""

from midicoder.emitters.core.cp34_reporting.models import (
    AggregationFunc,
    BatchJob,
    BatchJobStatus,
    ReportCollection,
    ReportFormat,
    ReportLayout,
    ReportSpec,
)
from midicoder.emitters.core.cp34_reporting.parser import ReportParser
from midicoder.emitters.core.cp34_reporting.fastapi import FastAPIReportEmitter
from midicoder.emitters.core.cp34_reporting.nestjs import NestJSReportEmitter
from midicoder.emitters.core.cp34_reporting.angular import AngularReportEmitter
from midicoder.emitters.core.cp34_reporting.react import ReactReportEmitter
from midicoder.emitters.core.cp34_reporting.recipes import (
    basic_report_recipe,
    pdf_report_recipe,
    excel_export_recipe,
    batch_report_recipe,
)

__all__ = [
    "AggregationFunc",
    "AngularReportEmitter",
    "BatchJob",
    "BatchJobStatus",
    "basic_report_recipe",
    "batch_report_recipe",
    "excel_export_recipe",
    "FastAPIReportEmitter",
    "NestJSReportEmitter",
    "pdf_report_recipe",
    "ReactReportEmitter",
    "ReportCollection",
    "ReportFormat",
    "ReportLayout",
    "ReportParser",
    "ReportSpec",
]
