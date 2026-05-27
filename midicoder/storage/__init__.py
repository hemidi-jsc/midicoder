"""
Storage Module cho Midicoder.

Module này cung cấp persistence layer cho:
- SQLite databases (primary storage)
- Neo4j graph database (knowledge graph)

E09: SQLite Persistence

Các databases:
- briefs.db: Brief library + clarifications + lineage
- artifacts.db: Artifacts + activity_log
- provenance.db: Lineage + decisions
- context.db: Codebase index (symbols, references)
"""

__all__ = [
    # Configuration
    "DATABASE_DIR",
    "DEFAULT_TIMEOUT",
    "DB_BRIEFS",
    "DB_ARTIFACTS",
    "DB_PROVENANCE",
    "DB_CONTEXT",
    # Schema definitions
    "SCHEMA_BRIEFS",
    "SCHEMA_ARTIFACTS",
    "SCHEMA_ACTIVITY",
    "SCHEMA_PROVENANCE",
    "SCHEMA_CONTEXT",
    # Helpers
    "get_connection",
    "init_database",
    # Managers
    "BriefsManager",
    "ArtifactsManager",
    "ActivityLogger",
    "ProvenanceManager",
    # Initialization
    "init_all_databases",
]

from midicoder.storage.sqlite import (
    # Configuration
    DATABASE_DIR,
    DEFAULT_TIMEOUT,
    DB_BRIEFS,
    DB_ARTIFACTS,
    DB_PROVENANCE,
    DB_CONTEXT,
    # Schema definitions
    SCHEMA_BRIEFS,
    SCHEMA_ARTIFACTS,
    SCHEMA_ACTIVITY,
    SCHEMA_PROVENANCE,
    SCHEMA_CONTEXT,
    # Helpers
    get_connection,
    init_database,
    # Managers
    BriefsManager,
    ArtifactsManager,
    ActivityLogger,
    ProvenanceManager,
    # Initialization
    init_all_databases,
)

# Pydantic models (Q24=A)
from midicoder.storage.models import (
    # Brief models
    BriefData,
    ClarificationData,
    BriefLineageData,
    # Artifact models
    ArtifactData,
    ActivityLogData,
    # Provenance models
    LineageData,
    DecisionData,
    # Context models
    SymbolData,
    FileData,
    ReferenceData,
)
