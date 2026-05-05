"""
Mô-đun Event Emitter cho CP05 Event-Driven Architecture.

Module này cung cấp implementation hoàn chỉnh cho Event pattern với:
- EventDefinition models (event_name, payload_fields, topic, version, tenant_id)
- EventParser (parse YAML/dict to EventDefinition)
- FastAPIEventEmitter (generate FastAPI event code)
- NestJSEventEmitter (generate NestJS event code)
- KPI-029: Tenant Isolation support

Author: Midicoder Team
Version: 1.0.0
"""

# Import models
from .models import EventDefinition

# Import parser
from .parser import EventParser

# Import emitters
try:
    from .fastapi import FastAPIEventEmitter, GeneratedFile as FastAPIGeneratedFile
    from .nestjs import NestJSEventEmitter, GeneratedFile as NestJSGeneratedFile
except ImportError as e:
    FastAPIEventEmitter = None  # type: ignore
    NestJSEventEmitter = None  # type: ignore
    FastAPIGeneratedFile = None  # type: ignore
    NestJSGeneratedFile = None  # type: ignore

__all__ = [
    # Models
    "EventDefinition",
    # Parser
    "EventParser",
    # Emitters
    "FastAPIEventEmitter",
    "NestJSEventEmitter",
    # GeneratedFile
    "FastAPIGeneratedFile",
    "NestJSGeneratedFile",
]