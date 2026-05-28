# coding: utf-8
"""
CP16: API & System Monitoring Generator (merged with CP17 BI Analytics).

Cung cấp các models và runtime engines cho:
- DashboardProfile, Panel: Dashboard management
- AlertRule, FiredAlert: Alert evaluation
- SLIDefinition, SLIStatus: SLI monitoring
- HealthCheck: Liveness/Readiness checks
- NotificationChannel: Alert routing channels
- EscalationPolicy: Alert escalation rules
- SLOTracking: Error budget & burn rate
# CP17 merged:
- AnalyticsModel, DashboardDefinition, ScheduledReport
- AnalyticsEngine, DashboardBuilder, ReportScheduler

Cung cấp các emitter cho:
- FastAPI, NestJS, Angular, React
"""

from midicoder.packs.cp_full_monitoring.models import (
    AlertCondition,
    AlertRule,
    AlertSeverity,
    DashboardProfile,
    DashboardType,
    EscalationPolicy,
    FiredAlert,
    HealthCheck,
    HealthCheckType,
    NotificationChannel,
    NotificationChannelType,
    Panel,
    SLIDefinition,
    SLIStatus,
    SLIMetricType,
    SLOBurnRate,
    SLOTracking,
    # CP17 merged models
    AnalyticsModel,
    AnalyticsSourceType,
    AggregationType,
    VisualizationType,
    DashboardDefinition,
    ReportFrequency,
    ReportFormat,
    SchedulePolicy,
    ScheduledReport,
)
from midicoder.packs.cp_full_monitoring.parser import MonitoringParser
from midicoder.packs.cp_full_monitoring.dashboard import DashboardManager
from midicoder.packs.cp_full_monitoring.alert import AlertEngine
from midicoder.packs.cp_full_monitoring.sli import SLIMonitor
from midicoder.packs.cp_full_monitoring.analytics_engine import AnalyticsEngine, QueryResult
from midicoder.packs.cp_full_monitoring.dashboard_builder import DashboardBuilder, Widget
from midicoder.packs.cp_full_monitoring.report_scheduler import ReportScheduler, ReportSnapshot
from midicoder.packs.cp_full_monitoring.fastapi import FastAPIMonitoringEmitter
from midicoder.packs.cp_full_monitoring.nestjs import NestJSMonitoringEmitter
from midicoder.packs.cp_full_monitoring.angular import AngularMonitoringEmitter
from midicoder.packs.cp_full_monitoring.react import ReactMonitoringEmitter

__all__ = [
    # Enums
    "AlertCondition",
    "AlertSeverity",
    "SLIMetricType",
    "DashboardType",
    "HealthCheckType",
    "NotificationChannelType",
    "SLOBurnRate",
    # CP17 Enums
    "AnalyticsSourceType",
    "AggregationType",
    "VisualizationType",
    "ReportFrequency",
    "ReportFormat",
    "SchedulePolicy",
    # Models
    "DashboardProfile",
    "Panel",
    "AlertRule",
    "FiredAlert",
    "SLIDefinition",
    "SLIStatus",
    "HealthCheck",
    "NotificationChannel",
    "EscalationPolicy",
    "SLOTracking",
    # CP17 Models
    "AnalyticsModel",
    "DashboardDefinition",
    "ScheduledReport",
    # Parser
    "MonitoringParser",
    # Engine
    "DashboardManager",
    "AlertEngine",
    "SLIMonitor",
    # CP17 Engines
    "AnalyticsEngine",
    "QueryResult",
    "DashboardBuilder",
    "Widget",
    "ReportScheduler",
    "ReportSnapshot",
    # Emitters
    "FastAPIMonitoringEmitter",
    "NestJSMonitoringEmitter",
    "AngularMonitoringEmitter",
    "ReactMonitoringEmitter",
]
