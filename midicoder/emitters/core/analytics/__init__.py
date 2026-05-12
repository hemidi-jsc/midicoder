# coding: utf-8
"""
Mô-đun Analytics (CP17) — Business Intelligence & Analytics Generator.

Cung cấp:
- Mô hình: AnalyticsModel, DashboardDefinition, ScheduledReport
-Enums: AnalyticsSourceType, AggregationType, VisualizationType, ReportFrequency, ReportFormat, SchedulePolicy
- Trình phân tích: AnalyticsParser
- Công cụ xử lý: AnalyticsEngine, DashboardBuilder, ReportScheduler
- Trình phát mã: FastAPIAnalyticsEmitter, NestJSAnalyticsEmitter, AngularAnalyticsEmitter, ReactAnalyticsEmitter

Author: Midicoder Team
Version: 1.0.0
"""

# Mô hình
from midicoder.emitters.core.analytics.models import (
    AggregationType,
    AnalyticsModel,
    AnalyticsSourceType,
    DashboardDefinition,
    ReportFrequency,
    ReportFormat,
    SchedulePolicy,
    ScheduledReport,
    VisualizationType,
)

# Trình phân tích
from midicoder.emitters.core.analytics.parser import AnalyticsParser

# Công cụ xử lý
from midicoder.emitters.core.analytics.analytics_engine import AnalyticsEngine, QueryResult
from midicoder.emitters.core.analytics.dashboard_builder import DashboardBuilder, Widget
from midicoder.emitters.core.analytics.report_scheduler import ReportScheduler, ReportSnapshot

# Trình phát mã
from midicoder.emitters.core.analytics.fastapi import FastAPIAnalyticsEmitter
from midicoder.emitters.core.analytics.nestjs import NestJSAnalyticsEmitter
from midicoder.emitters.core.analytics.angular import AngularAnalyticsEmitter
from midicoder.emitters.core.analytics.react import ReactAnalyticsEmitter

__all__ = [
    # Mô hình
    "AnalyticsModel",
    "DashboardDefinition",
    "ScheduledReport",
    #Enums
    "AnalyticsSourceType",
    "AggregationType",
    "VisualizationType",
    "ReportFrequency",
    "ReportFormat",
    "SchedulePolicy",
    # Trình phân tích
    "AnalyticsParser",
    # Công cụ xử lý
    "AnalyticsEngine",
    "QueryResult",
    "DashboardBuilder",
    "Widget",
    "ReportScheduler",
    "ReportSnapshot",
    # Trình phát mã
    "FastAPIAnalyticsEmitter",
    "NestJSAnalyticsEmitter",
    "AngularAnalyticsEmitter",
    "ReactAnalyticsEmitter",
]
