"""
Tests cho helpers và init_all_databases.

E09: SQLite Persistence - Helper functions
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from midicoder.storage.sqlite import (
    get_connection,
    init_database,
    init_all_databases,
    DATABASE_DIR,
    DB_BRIEFS,
    DB_ARTIFACTS,
    DB_PROVENANCE,
    DB_CONTEXT,
    SCHEMA_BRIEFS,
    SCHEMA_ARTIFACTS,
    SCHEMA_ACTIVITY,
    SCHEMA_PROVENANCE,
    SCHEMA_CONTEXT,
)


class TestGetConnection:
    """Tests cho get_connection context manager."""

    def test_get_connection_creates_directory(self, tmp_path):
        """
        Test: get_connection() tạo directory nếu không tồn tại.
        
        Verification: Directory được tạo tự động khi connect.
        """
        db_path = tmp_path / "nested" / "dir" / "test.db"
        
        # Directory chưa tồn tại
        assert not db_path.parent.exists()
        
        # Kết nối sẽ tạo directory
        with get_connection(db_path) as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
        
        # Sau khi kết nối, directory đã tồn tại
        assert db_path.parent.exists()
        assert db_path.exists()

    def test_get_connection_commits_on_success(self, tmp_path):
        """
        Test: get_connection() commit tự động khi thành công.
        
        Verification: Data được lưu vào DB sau khi exit context.
        """
        db_path = tmp_path / "test.db"
        
        # Insert data trong context
        with get_connection(db_path) as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.execute("INSERT INTO test VALUES (1)")
        
        # Đọc data từ connection mới (không có uncommitted changes)
        with get_connection(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM test")
            count = cursor.fetchone()[0]
            
            assert count == 1

    def test_get_connection_rollback_on_error(self, tmp_path):
        """
        Test: get_connection() rollback khi có exception.
        
        Verification: Data không được lưu khi exception xảy ra.
        """
        db_path = tmp_path / "test.db"
        
        # Tạo table và insert initial data
        with get_connection(db_path) as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.execute("INSERT INTO test VALUES (1)")
        
        initial_count = 1
        
        # Thử insert và throw error - phải rollback
        try:
            with get_connection(db_path) as conn:
                conn.execute("INSERT INTO test VALUES (2)")
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Data phải vẫn là initial count
        with get_connection(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM test")
            count = cursor.fetchone()[0]
            
            assert count == initial_count

    def test_get_connection_row_factory(self, tmp_path):
        """
        Test: get_connection() set row_factory thành sqlite3.Row.
        
        Verification: Query results có thể access bằng dict-like access.
        """
        db_path = tmp_path / "test.db"
        
        with get_connection(db_path) as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'test')")
            
            cursor = conn.execute("SELECT * FROM test")
            row = cursor.fetchone()
            
            # Dict-like access phải hoạt động
            assert row["id"] == 1
            assert row["name"] == "test"


class TestInitDatabase:
    """Tests cho init_database function."""

    def test_init_database_creates_tables(self, tmp_path):
        """
        Test: init_database() tạo tables theo schema.
        
        Verification: Tables được tạo đúng theo schema SQL.
        """
        db_path = tmp_path / "test.db"
        
        # Custom schema đơn giản
        schema = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            content TEXT
        );
        """
        
        init_database(db_path, schema)
        
        # Verify tables tồn tại
        with get_connection(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            
            assert "users" in tables
            assert "posts" in tables

    def test_init_database_idempotent(self, tmp_path):
        """
        Test: init_database() có thể chạy nhiều lần (CREATE IF NOT EXISTS).
        
        Verification: Không có lỗi khi gọi init_database nhiều lần.
        """
        db_path = tmp_path / "test.db"
        
        schema = "CREATE TABLE IF NOT EXISTS test (id INTEGER)"
        
        # Gọi nhiều lần không gây lỗi
        init_database(db_path, schema)
        init_database(db_path, schema)
        init_database(db_path, schema)
        
        # Chỉ có 1 table
        with get_connection(db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='test'"
            )
            count = cursor.fetchone()[0]
            assert count == 1


class TestInitAllDatabases:
    """Tests cho init_all_databases function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup: Save và restore DATABASE_DIR.
        """
        self.original_dir = DATABASE_DIR
        self.temp_dir = Path(tempfile.mkdtemp())
        # Mock DATABASE_DIR
        import midicoder.storage.sqlite as sqlite_module
        self.original_db_briefs = sqlite_module.DB_BRIEFS
        self.original_db_artifacts = sqlite_module.DB_ARTIFACTS
        self.original_db_provenance = sqlite_module.DB_PROVENANCE
        self.original_db_context = sqlite_module.DB_CONTEXT
        
        sqlite_module.DATABASE_DIR = self.temp_dir / ".midicoder" / "data"
        sqlite_module.DB_BRIEFS = sqlite_module.DATABASE_DIR / "briefs.db"
        sqlite_module.DB_ARTIFACTS = sqlite_module.DATABASE_DIR / "artifacts.db"
        sqlite_module.DB_PROVENANCE = sqlite_module.DATABASE_DIR / "provenance.db"
        sqlite_module.DB_CONTEXT = sqlite_module.DATABASE_DIR / "context.db"
        
        yield
        
        # Restore
        sqlite_module.DATABASE_DIR = self.original_dir
        sqlite_module.DB_BRIEFS = self.original_db_briefs
        sqlite_module.DB_ARTIFACTS = self.original_db_artifacts
        sqlite_module.DB_PROVENANCE = self.original_db_provenance
        sqlite_module.DB_CONTEXT = self.original_db_context
        
        # Cleanup
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_all_databases_creates_directory(self):
        """
        Test: init_all_databases() tạo directory .midicoder/data.
        
        Verification: Directory được tạo nếu không tồn tại.
        """
        # Directory chưa tồn tại
        assert not (self.temp_dir / ".midicoder" / "data").exists()
        
        # Init
        result = init_all_databases()
        
        # Directory đã tồn tại
        assert (self.temp_dir / ".midicoder" / "data").exists()
        assert result is True

    def test_init_all_databases_creates_all_files(self):
        """
        Test: init_all_databases() tạo đủ 4 database files.
        
        Verification: briefs.db, artifacts.db, provenance.db, context.db đều tồn tại.
        """
        result = init_all_databases()
        
        assert result is True
        assert (self.temp_dir / ".midicoder" / "data" / "briefs.db").exists()
        assert (self.temp_dir / ".midicoder" / "data" / "artifacts.db").exists()
        assert (self.temp_dir / ".midicoder" / "data" / "provenance.db").exists()
        assert (self.temp_dir / ".midicoder" / "data" / "context.db").exists()

    def test_init_all_databases_briefs_schema(self):
        """
        Test: briefs.db có đúng tables theo SCHEMA_BRIEFS.
        
        Verification: briefs, clarifications, brief_lineage đều tồn tại.
        """
        init_all_databases()
        
        briefs_db = self.temp_dir / ".midicoder" / "data" / "briefs.db"
        
        with get_connection(briefs_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            
            assert "briefs" in tables
            assert "clarifications" in tables
            assert "brief_lineage" in tables

    def test_init_all_databases_artifacts_schema(self):
        """
        Test: artifacts.db có artifacts và activity_log tables.
        
        Verification: artifacts, activity_log đều tồn tại.
        """
        init_all_databases()
        
        artifacts_db = self.temp_dir / ".midicoder" / "data" / "artifacts.db"
        
        with get_connection(artifacts_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            
            assert "artifacts" in tables
            assert "activity_log" in tables

    def test_init_all_databases_provenance_schema(self):
        """
        Test: provenance.db có lineage và decisions tables.
        
        Verification: lineage, decisions đều tồn tại.
        """
        init_all_databases()
        
        provenance_db = self.temp_dir / ".midicoder" / "data" / "provenance.db"
        
        with get_connection(provenance_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            
            assert "lineage" in tables
            assert "decisions" in tables

    def test_init_all_databases_context_schema(self):
        """
        Test: context.db có symbols và references tables.
        
        Verification: symbols, references đều tồn tại.
        """
        init_all_databases()
        
        context_db = self.temp_dir / ".midicoder" / "data" / "context.db"
        
        with get_connection(context_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            
            assert "symbols" in tables
            assert "references" in tables


class TestSchemaDefinitions:
    """Tests cho schema definitions."""

    def test_schema_briefs_has_required_tables(self):
        """
        Test: SCHEMA_BRIEFS có đầy đủ tables theo E09.
        
        Verification: Schema chứa CREATE TABLE cho briefs, clarifications, brief_lineage.
        """
        assert "CREATE TABLE IF NOT EXISTS briefs" in SCHEMA_BRIEFS
        assert "CREATE TABLE IF NOT EXISTS clarifications" in SCHEMA_BRIEFS
        assert "CREATE TABLE IF NOT EXISTS brief_lineage" in SCHEMA_BRIEFS

    def test_schema_artifacts_has_required_tables(self):
        """
        Test: SCHEMA_ARTIFACTS có artifacts table.
        
        Verification: Schema chứa CREATE TABLE artifacts.
        """
        assert "CREATE TABLE IF NOT EXISTS artifacts" in SCHEMA_ARTIFACTS

    def test_schema_activity_has_required_tables(self):
        """
        Test: SCHEMA_ACTIVITY có activity_log table.
        
        Verification: Schema chứa CREATE TABLE activity_log.
        """
        assert "CREATE TABLE IF NOT EXISTS activity_log" in SCHEMA_ACTIVITY

    def test_schema_provenance_has_required_tables(self):
        """
        Test: SCHEMA_PROVENANCE có lineage và decisions tables.
        
        Verification: Schema chứa CREATE TABLE cho cả 2.
        """
        assert "CREATE TABLE IF NOT EXISTS lineage" in SCHEMA_PROVENANCE
        assert "CREATE TABLE IF NOT EXISTS decisions" in SCHEMA_PROVENANCE

    def test_schema_context_has_required_tables(self):
        """
        Test: SCHEMA_CONTEXT có symbols và references tables.
        
        Verification: Schema chứa CREATE TABLE cho cả 2.
        """
        assert "CREATE TABLE IF NOT EXISTS symbols" in SCHEMA_CONTEXT
        assert 'CREATE TABLE IF NOT EXISTS "references"' in SCHEMA_CONTEXT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])