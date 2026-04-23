"""
Unit tests cho SQLite storage layer với temp files.

Q21=C: Unit tests với temp files vì in-memory DB không share schema giữa connections.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from midicoder.storage.sqlite import (
    BriefsManager,
    ArtifactsManager,
    ActivityLogger,
    ProvenanceManager,
    get_connection,
    init_database,
    SCHEMA_BRIEFS,
    SCHEMA_ARTIFACTS,
    SCHEMA_ACTIVITY,
    SCHEMA_PROVENANCE,
    SCHEMA_CONTEXT,
)
from midicoder.storage.models import (
    BriefData,
    ArtifactData,
    DecisionData,
    LineageData,
)
from midicoder.errors import MidicoderError, ErrorCode


# ============================================================================
# Fixtures với temp files (in-memory không share schema giữa connections)
# ============================================================================

@pytest.fixture
def temp_briefs_db():
    """Temp briefs database for unit tests."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "briefs.db"
    manager = BriefsManager(db_path)
    manager.init()
    yield manager, db_path
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_artifacts_db():
    """Temp artifacts database for unit tests."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "artifacts.db"
    manager = ArtifactsManager(db_path)
    manager.init()
    yield manager, db_path
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_provenance_db():
    """Temp provenance database for unit tests."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "provenance.db"
    manager = ProvenanceManager(db_path)
    manager.init()
    yield manager, db_path
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_activity_logger():
    """Temp ActivityLogger for unit tests."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "artifacts.db"
    logger = ActivityLogger(db_path)
    logger.init()
    yield logger, db_path
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# BriefsManager Tests
# ============================================================================

class TestBriefsManager:
    """Tests for BriefsManager."""

    def test_init_creates_tables(self, temp_briefs_db):
        """Test initialization creates all required tables."""
        manager, db_path = temp_briefs_db


        with get_connection(db_path) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]

        assert "briefs" in table_names
        assert "clarifications" in table_names
        assert "brief_lineage" in table_names

    def test_create_brief(self, temp_briefs_db):
        """Test creating a new brief."""
        manager, _ = temp_briefs_db


        result = manager.create(
            brief_id="test-brief-001",
            version="v1.0.0",
            content="# Test Brief\n\nThis is a test brief.",
            title="Test Brief",
            brief_type="working",
        )

        assert result["brief_id"] == "test-brief-001"
        assert result["version"] == "v1.0.0"
        assert result["title"] == "Test Brief"
        assert result["type"] == "working"
        assert result["status"] == "draft"
        assert "hash" in result
        assert len(result["hash"]) == 64  # SHA-256 hex

    def test_get_brief(self, temp_briefs_db):
        """Test retrieving a brief by ID."""
        manager, _ = temp_briefs_db

        # Create first
        manager.create(
            brief_id="test-brief-001",
            version="v1.0.0",
            content="# Test Brief",
        )

        result = manager.get("test-brief-001")

        assert result is not None
        assert result["brief_id"] == "test-brief-001"

    def test_get_brief_not_found(self, temp_briefs_db):
        """Test retrieving non-existent brief returns None."""
        manager, _ = temp_briefs_db

        result = manager.get("non-existent-brief")

        assert result is None

    def test_get_latest_brief(self, temp_briefs_db):
        """Test get_latest returns the most recent brief."""
        manager, _ = temp_briefs_db

        # Create multiple versions
        manager.create("test-brief", "v1.0.0", "# V1")
        manager.create("test-brief", "v1.1.0", "# V1.1")
        manager.create("test-brief", "v2.0.0", "# V2")

        latest = manager.get_latest("test-brief")

        assert latest is not None
        assert latest["version"] == "v2.0.0"

    def test_search_by_status(self, temp_briefs_db):
        """Test searching briefs by status."""
        manager, _ = temp_briefs_db

        # Create briefs with different statuses
        manager.create("brief-1", "v1.0.0", "# Brief 1")
        manager.create("brief-2", "v1.0.0", "# Brief 2")
        manager.create("brief-3", "v1.0.0", "# Brief 3")

        manager.update_status("brief-1", "frozen")
        manager.update_status("brief-2", "frozen")
        # brief-3 stays draft

        frozen = manager.search_by_status("frozen")

        assert len(frozen) == 2

    def test_add_clarification(self, temp_briefs_db):
        """Test adding clarification Q&A."""
        manager, _ = temp_briefs_db

        manager.create("test-brief", "v1.0.0", "# Brief")

        clar_id = manager.add_clarification(
            brief_id="test-brief",
            round_num=1,
            question="What is the target audience?",
            answer="Small business owners",
            is_memo=True,
        )

        assert clar_id > 0

        clarifications = manager.get_clarifications("test-brief")
        assert len(clarifications) == 1
        assert clarifications[0]["question"] == "What is the target audience?"
        assert clarifications[0]["is_memo"] == 1

    def test_record_lineage(self, temp_briefs_db):
        """Test recording brief lineage."""
        manager, _ = temp_briefs_db

        manager.create("parent-brief", "v1.0.0", "# Parent")
        manager.create("child-brief", "v1.1.0", "# Child")

        lineage_id = manager.record_lineage(
            brief_id="child-brief",
            parent_brief_id="parent-brief",
            version="v1.1.0",
            change_type="clarify",
            change_description="Added clarifications",
        )

        assert lineage_id > 0


# ============================================================================
# ArtifactsManager Tests
# ============================================================================

class TestArtifactsManager:
    """Tests for ArtifactsManager."""

    def test_init_creates_tables(self, temp_artifacts_db):
        """Test initialization creates all required tables."""
        manager, db_path = temp_artifacts_db


        with get_connection(db_path) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]

        assert "artifacts" in table_names
        assert "activity_log" in table_names

    def test_create_artifact(self, temp_artifacts_db):
        """Test creating a new artifact."""
        manager, _ = temp_artifacts_db


        result = manager.create(
            artifact_id="artifact-001",
            artifact_type="contract",
            name="User Contract",
            version="v1.0.0",
            brief_id="brief-001",
            content="contract content here",
            metadata={"key": "value"},
        )

        assert result["artifact_id"] == "artifact-001"
        assert result["type"] == "contract"
        assert result["name"] == "User Contract"
        assert result["brief_id"] == "brief-001"

    def test_get_artifact(self, temp_artifacts_db):
        """Test retrieving an artifact by ID."""
        manager, _ = temp_artifacts_db

        manager.create("artifact-001", "contract", "Test", "v1.0.0")

        result = manager.get("artifact-001")

        assert result is not None
        assert result["artifact_id"] == "artifact-001"

    def test_update_status(self, temp_artifacts_db):
        """Test updating artifact status."""
        manager, _ = temp_artifacts_db

        manager.create("artifact-001", "contract", "Test", "v1.0.0")
        manager.update_status("artifact-001", "validated")

        result = manager.get("artifact-001")
        assert result["status"] == "validated"

    def test_list_by_type(self, temp_artifacts_db):
        """Test listing artifacts by type."""
        manager, _ = temp_artifacts_db

        manager.create("artifact-1", "contract", "Contract 1", "v1.0.0")
        manager.create("artifact-2", "mir", "MIR 1", "v1.0.0")
        manager.create("artifact-3", "contract", "Contract 2", "v1.0.0")

        contracts = manager.list_by_type("contract")

        assert len(contracts) == 2


# ============================================================================
# ActivityLogger Tests
# ============================================================================

class TestActivityLogger:
    """Tests for ActivityLogger."""

    def test_log_activity(self, temp_activity_logger):
        """Test logging an activity."""
        logger, _ = temp_activity_logger

        log_id = logger.log(
            action="init",
            resource_type="database",
            resource_id="briefs.db",
            details={"tables": 3},
            status="success",
            duration_ms=150,
        )

        assert log_id > 0

    def test_query_logs(self, temp_activity_logger):
        """Test querying activity logs with filters."""
        logger, _ = temp_activity_logger

        # Log multiple activities
        logger.log("init", "db", "briefs.db", status="success")
        logger.log("init", "db", "artifacts.db", status="success")
        logger.log("error", "db", "provenance.db", status="failed")

        # Query by action
        inits = logger.query(action="init")
        assert len(inits) == 2

        # Query by status
        failed = logger.query(status="failed")
        assert len(failed) == 1


# ============================================================================
# ProvenanceManager Tests
# ============================================================================

class TestProvenanceManager:
    """Tests for ProvenanceManager."""

    def test_init_creates_tables(self, temp_provenance_db):
        """Test initialization creates all required tables."""
        manager, db_path = temp_provenance_db


        with get_connection(db_path) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]

        assert "lineage" in table_names
        assert "decisions" in table_names

    def test_record_lineage(self, temp_provenance_db):
        """Test recording lineage relationship."""
        manager, _ = temp_provenance_db


        lineage_id = manager.record_lineage(
            entity_id="artifact-001",
            entity_type="artifact",
            source_id="brief-001",
            source_type="brief",
            relationship="generated_from",
            metadata={"timestamp": "2024-01-01"},
        )

        assert lineage_id > 0

    def test_get_lineage(self, temp_provenance_db):
        """Test retrieving lineage for an entity."""
        manager, _ = temp_provenance_db

        manager.record_lineage(
            "artifact-001", "artifact", "brief-001", "brief", "generated_from"
        )
        manager.record_lineage(
            "artifact-002", "artifact", "brief-001", "brief", "generated_from"
        )

        lineage = manager.get_lineage("artifact-001", "artifact")

        assert len(lineage) == 1
        assert lineage[0]["source_id"] == "brief-001"

    def test_record_decision(self, temp_provenance_db):
        """Test recording an architectural decision."""
        manager, _ = temp_provenance_db

        decision_id = manager.record_decision(
            decision_id="DEC-001",
            title="Use SQLite for persistence",
            status="accepted",
            description="Chose SQLite over PostgreSQL for simplicity",
            rationale="Fast setup, no external dependencies",
            consequences="Limited scalability",
            decided_by="team",
            related_brief_id="brief-001",
        )

        assert decision_id > 0

    def test_get_decisions(self, temp_provenance_db):
        """Test retrieving decisions with filters."""
        manager, _ = temp_provenance_db

        manager.record_decision("DEC-001", "Decision 1", "accepted")
        manager.record_decision("DEC-002", "Decision 2", "proposed")
        manager.record_decision("DEC-003", "Decision 3", "accepted")

        accepted = manager.get_decisions(status="accepted")

        assert len(accepted) == 2


# ============================================================================
# Pydantic Model Tests
# ============================================================================

class TestPydanticModels:
    """Tests for Pydantic validation models."""

    def test_brief_data_validation(self):
        """Test BriefData model validation."""
        # Valid data
        brief = BriefData(
            brief_id="test-001",
            version="v1.0.0",
            content="# Test Brief",
        )
        assert brief.brief_id == "test-001"
        assert brief.status == "draft"  # default

        # Invalid version format
        with pytest.raises(ValueError):
            BriefData(
                brief_id="test-002",
                version="1.0.0",  # Missing 'v' prefix
                content="# Test",
            )

    def test_artifact_data_validation(self):
        """Test ArtifactData model validation."""
        artifact = ArtifactData(
            artifact_id="artifact-001",
            artifact_type="contract",
            name="User Contract",
            version="v1.0.0",
        )
        assert artifact.status == "pending"  # default

    def test_decision_data_validation(self):
        """Test DecisionData model validation."""
        decision = DecisionData(
            decision_id="DEC-001",
            title="Use SQLite",
            status="accepted",
        )
        assert decision.decision_id == "DEC-001"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling in storage module."""

    def test_duplicate_brief_raises_constraint_error(self, temp_briefs_db):
        """Test that duplicate brief_id + version raises DB_CONSTRAINT_VIOLATION."""
        manager, _ = temp_briefs_db


        manager.create("test-brief", "v1.0.0", "# Brief")

        with pytest.raises(MidicoderError) as exc_info:
            manager.create("test-brief", "v1.0.0", "# Duplicate")

        assert exc_info.value.code == ErrorCode.DB_CONSTRAINT_VIOLATION

    def test_duplicate_artifact_raises_constraint_error(self, temp_artifacts_db):
        """Test that duplicate artifact_id raises DB_CONSTRAINT_VIOLATION."""
        manager, _ = temp_artifacts_db


        manager.create("artifact-001", "contract", "Test", "v1.0.0")

        with pytest.raises(MidicoderError) as exc_info:
            manager.create("artifact-001", "mir", "Test 2", "v1.0.0")

        assert exc_info.value.code == ErrorCode.DB_CONSTRAINT_VIOLATION


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])