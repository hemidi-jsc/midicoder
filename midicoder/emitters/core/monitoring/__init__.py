# coding: utf-8
"""
CP16: API & System Monitoring Generator.

Cung cấp các models và runtime engines cho:
- DashboardProfile, Panel: Dashboard management
- AlertRule, FiredAlert: Alert evaluation
- SLIDefinition, SLIStatus: SLI monitoring

Cung cấp các emitter cho:
- FastAPI, NestJS, Angular, React
"""

from midicoder.emitters.core.monitoring.models import (
    AlertCondition,
    AlertRule,
    AlertSeverity,
    DashboardProfile,
    DashboardType,
    FiredAlert,
    Panel,
    SLIDefinition,
    SLIStatus,
    SLIMetricType,
)
from midicoder.emitters.core.monitoring.parser import MonitoringParser
from midicoder.emitters.core.monitoring.dashboard import DashboardManager
from midicoder.emitters.core.monitoring.alert import AlertEngine
from midicoder.emitters.core.monitoring.sli import SLIMonitor
from midicoder.emitters.core.monitoring.fastapi import FastAPIMonitoringEmitter
from midicoder.emitters.core.monitoring.nestjs import NestJSMonitoringEmitter
from midicoder.emitters.core.monitoring.angular import AngularMonitoringEmitter
from midicoder.emitters.core.monitoring.react import ReactMonitoringEmitter

__all__ = [
    # Enums
    "AlertCondition",
    "AlertSeverity",
    "SLIMetricType",
    "DashboardType",
    # Models
    "DashboardProfile",
    "Panel",
    "AlertRule",
    "FiredAlert",
    "SLIDefinition",
    "SLIStatus",
    # Parser
    "MonitoringParser",
    # Engine
    "DashboardManager",
    "AlertEngine",
    "SLIMonitor",
    # Emitters
    "FastAPIMonitoringEmitter",
    "NestJSMonitoringEmitter",
    "AngularMonitoringEmitter",
    "ReactMonitoringEmitter",
]
