"""
Mô-đun Event Emitter cho CP05 Event-Driven Architecture.

Module này cung cấp implementation hoàn chỉnh cho Event pattern với:
- EventDefinition models (event_name, payload_fields, topic, version, tenant_id)
- OutboxEntry (outbox pattern for reliable event delivery)
- TransportConfig, DLQConfig, EventStoreConfig, RetryPolicy (infrastructure)
- EventStream, CQRSProjection (event sourcing + CQRS backbone)
- IdempotentConsumer, EventSchemaVersion (reliability + schema evolution)
- EventParser (parse YAML/dict to EventDefinition)
- FastAPIEventEmitter (generate FastAPI event code)
- NestJSEventEmitter (generate NestJS event code)
- KPI-029: Tenant Isolation support

Author: Midicoder Team
Version: 1.0.0
"""

# Import core models
from .models import (
    CQRSProjection,
    DeliveryGuarantee,
    DLQConfig,
    DLQPolicy,
    EventDefinition,
    EventSchemaVersion,
    EventStoreBackend,
    EventStoreConfig,
    EventStream,
    IdempotencyStrategy,
    IdempotentConsumer,
    MaterializationStrategy,
    OutboxEntry,
    RetryPolicy,
    RetryStrategy,
    SchemaEvolutionPolicy,
    SnapshotStrategy,
    TransportConfig,
    TransportType,
)

# Import parser
from .parser import EventParser

# Import emitters
try:
    from .fastapi import FastAPIEventEmitter, GeneratedFile as FastAPIGeneratedFile
    from .nestjs import NestJSEventEmitter, GeneratedFile as NestJSGeneratedFile
except ImportError as e:  # pragma: no cover
    FastAPIEventEmitter = None  # type: ignore
    NestJSEventEmitter = None  # type: ignore
    FastAPIGeneratedFile = None  # type: ignore
    NestJSGeneratedFile = None  # type: ignore

__all__ = [
    # Core models
    "EventDefinition",
    "OutboxEntry",
    # Transport abstraction
    "TransportType",
    "DeliveryGuarantee",
    "TransportConfig",
    # Dead Letter Queue
    "DLQPolicy",
    "DLQConfig",
    # Event Sourcing
    "EventStoreBackend",
    "SnapshotStrategy",
    "EventStoreConfig",
    # Retry
    "RetryStrategy",
    "RetryPolicy",
    # Idempotent Consumer
    "IdempotencyStrategy",
    "IdempotentConsumer",
    # Schema Versioning
    "SchemaEvolutionPolicy",
    "EventSchemaVersion",
    # Event Stream
    "EventStream",
    # CQRS Projection
    "MaterializationStrategy",
    "CQRSProjection",
    # Parser
    "EventParser",
    # Emitters
    "FastAPIEventEmitter",
    "NestJSEventEmitter",
    # GeneratedFile
    "FastAPIGeneratedFile",
    "NestJSGeneratedFile",
]