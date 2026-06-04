"""
Tests cho BriefsManager.

E09: SQLite Persistence - Briefs table
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from midicoder.storage.sqlite import (
    BriefsManager,
    SCHEMA_BRIEFS,
)


class TestBriefsManager:
    """Tests cho BriefsManager class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup trước mỗi test - tạo temp database.
        
        Mỗi test chạy độc lập với database riêng để tránh
        data pollution giữa các tests.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_briefs.db"
        self.manager = BriefsManager(self.db_path)
        self.manager.init()
        yield
        # Cleanup sau mỗi test
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_tables(self):
        """
        Test: init() tạo đúng các tables theo schema.
        
        Verification: Kiểm tra briefs, clarifications, brief_lineage
        đều được tạo sau khi gọi init().
        """
        with self.manager._get_connection() as conn:
            # Kiểm tra tables tồn tại
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            
            assert "briefs" in tables
            assert "clarifications" in tables
            assert "brief_lineage" in tables

    def test_create_brief_success(self):
        """
        Test: create() tạo brief mới thành công.
        
        Verification:
        - Brief được lưu vào DB
        - Hash được tính đúng
        - Status mặc định là 'draft'
        """
        brief_id = "test-brief-001"
        content = "Test brief content"
        
        result = self.manager.create(
            brief_id=brief_id,
            version="v1.0.0",
            content=content,
            title="Test Brief",
            brief_type="working"
        )
        
        # Verify return value
        assert result["brief_id"] == brief_id
        assert result["version"] == "v1.0.0"
        assert result["type"] == "working"
        assert result["title"] == "Test Brief"
        assert result["status"] == "draft"
        assert "hash" in result

    def test_create_brief_generates_hash(self):
        """
        Test: Content hash được tính chính xác.
        
        Verification: Hash của content phải là SHA256 của content.
        """
        import hashlib
        
        content = "Test content for hash"
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        
        result = self.manager.create(
            brief_id="test-hash",
            version="v1.0.0",
            content=content
        )
        
        assert result["hash"] == expected_hash

    def test_create_brief_unique_constraint(self):
        """
        Test: Không thể tạo 2 briefs với cùng brief_id.
        
        Verification: Lỗi integrity error khi duplicate brief_id.
        """
        self.manager.create(
            brief_id="duplicate-id",
            version="v1.0.0",
            content="First"
        )
        
        with pytest.raises(Exception):
            self.manager.create(
                brief_id="duplicate-id",
                version="v1.0.0",
                content="Second"
            )

    def test_get_brief_by_id(self):
        """
        Test: get() lấy brief theo brief_id chính xác.
        
        Verification: Brief trả về khớp với brief đã tạo.
        """
        brief_id = "get-test-001"
        content = "Content to retrieve"
        
        # Create brief
        self.manager.create(
            brief_id=brief_id,
            version="v1.0.0",
            content=content,
            title="Get Test"
        )
        
        # Retrieve brief
        result = self.manager.get(brief_id=brief_id)
        
        assert result is not None
        assert result["brief_id"] == brief_id
        assert result["title"] == "Get Test"
        assert result["content"] == content

    def test_get_brief_with_version(self):
        """
        Test: get() với version parameter lấy đúng version.
        
        Verification: Brief trả về phải có version khớp.
        """
        brief_id = "version-test"
        
        # Create multiple versions
        self.manager.create(
            brief_id=brief_id,
            version="v1.0.0",
            content="Version 1"
        )
        self.manager.create(
            brief_id=brief_id,
            version="v2.0.0",
            content="Version 2"
        )
        
        # Get specific version
        result = self.manager.get(brief_id=brief_id, version="v1.0.0")
        
        assert result is not None
        assert result["version"] == "v1.0.0"
        assert result["content"] == "Version 1"

    def test_get_brief_latest_version(self):
        """
        Test: get() không version parameter trả về version mới nhất.
        
        Verification: Brief trả về phải là version được tạo sau cùng.
        """
        brief_id = "latest-test"
        
        # Create multiple versions
        self.manager.create(
            brief_id=brief_id,
            version="v1.0.0",
            content="Old"
        )
        self.manager.create(
            brief_id=brief_id,
            version="v2.0.0",
            content="New"
        )
        
        # Get latest (should be v2.0.0)
        result = self.manager.get(brief_id=brief_id)
        
        assert result is not None
        assert result["version"] == "v2.0.0"
        assert result["content"] == "New"

    def test_get_brief_not_found(self):
        """
        Test: get() brief không tồn tại trả về None.
        
        Verification: Không có lỗi, trả về None.
        """
        result = self.manager.get(brief_id="non-existent")
        
        assert result is None

    def test_list_briefs_all(self):
        """
        Test: list() trả về tất cả briefs.
        
        Verification: Số lượng briefs trả về bằng số lượng đã tạo.
        """
        # Create multiple briefs
        brief_ids = []
        for i in range(5):
            brief_id = f"list-test-{i}"
            brief_ids.append(brief_id)
            self.manager.create(
                brief_id=brief_id,
                version="v1.0.0",
                content=f"Content {i}"
            )
        
        # List all
        results = self.manager.list()
        
        # Kiểm tra số lượng
        assert len(results) == 5
        
        # Kiểm tra tất cả brief_ids đều có trong results
        result_ids = {r["brief_id"] for r in results}
        expected_ids = set(brief_ids)
        assert result_ids == expected_ids

    def test_list_briefs_by_version(self):
        """
        Test: list() với version filter chỉ trả về briefs đúng version.
        
        Verification: Tất cả briefs trong result có version khớp.
        """
        # Create briefs với different versions
        self.manager.create(
            brief_id="v1-test-1",
            version="v1.0.0",
            content="V1 Content 1"
        )
        self.manager.create(
            brief_id="v2-test-1",
            version="v2.0.0",
            content="V2 Content"
        )
        self.manager.create(
            brief_id="v1-test-2",
            version="v1.0.0",
            content="V1 Content 2"
        )
        
        # List by version
        results = self.manager.list(version="v1.0.0")
        
        assert len(results) == 2
        for brief in results:
            assert brief["version"] == "v1.0.0"

    def test_update_status_success(self):
        """
        Test: update_status() cập nhật status thành công.
        
        Verification: Brief sau khi update có status mới.
        """
        brief_id = "status-test"
        self.manager.create(
            brief_id=brief_id,
            version="v1.0.0",
            content="Status test content"
        )
        
        # Update status
        result = self.manager.update_status(brief_id, "clarified")
        
        assert result is True
        
        # Verify
        brief = self.manager.get(brief_id=brief_id)
        assert brief["status"] == "clarified"

    def test_update_status_unknown_brief(self):
        """
        Test: update_status() với brief_id không tồn tại.
        
        Verification: Không có lỗi, nhưng không có record nào được update.
        """
        result = self.manager.update_status("unknown-id", "clarified")
        
        # Returns True even if no rows affected (sqlite behavior)
        assert result is True

    def test_brief_type_defaults_to_working(self):
        """
        Test: brief_type mặc định là 'working' khi không指定.
        
        Verification: Brief tạo không có type parameter có type='working'.
        """
        result = self.manager.create(
            brief_id="default-type",
            version="v1.0.0",
            content="Content"
        )
        
        assert result["type"] == "working"

    def test_create_master_brief(self):
        """
        Test: Tạo brief với type='master'.

        Verification: Brief có type='master' khi指定.
        """
        result = self.manager.create(
            brief_id="master-test",
            version="v1.0.0",
            content="Master content",
            brief_type="master"
        )

        assert result["type"] == "master"

    # ------------------------------------------------------------------ #
    # Tests cho methods mới: library brief lifecycle
    # ------------------------------------------------------------------ #

    def test_update_type(self):
        """
        Test: update_type() chuyển type của brief.

        Verification: brief.type được cập nhật đúng.
        """
        bid = "type-change-test"
        self.manager.create(bid, "v1.0.0", "content")
        self.manager.update_type(bid, "library")

        brief = self.manager.get(bid)
        assert brief["type"] == "library"

    def test_search_by_type(self):
        """
        Test: search_by_type() filter đúng type.

        Verification: trả về danh sách briefs có type match.
        """
        self.manager.create("b1", "v1.0.0", "c1", brief_type="working")
        self.manager.create("b2", "v1.0.0", "c2", brief_type="library")
        self.manager.create("b3", "v1.0.0", "c3", brief_type="library")

        libraries = self.manager.search_by_type("library")
        assert len(libraries) == 2
        assert all(b["type"] == "library" for b in libraries)

        workings = self.manager.search_by_type("working")
        assert len(workings) == 1

    def test_save_as_library(self):
        """
        Test: save_as_library() chuyển master → library + frozen.

        Verification: type='library', status='frozen', title=name.
        """
        bid = "save-lib-test"
        self.manager.create(bid, "v1.0.0", "master content", title="Original Title", brief_type="master")
        self.manager.update_status(bid, "clarified")

        self.manager.save_as_library(bid, "my-library-brief", "productivity,api")

        brief = self.manager.get(bid)
        assert brief["type"] == "library"
        assert brief["status"] == "frozen"
        assert brief["title"] == "my-library-brief"

    def test_save_as_library_without_tags(self):
        """
        Test: save_as_library() không có tags vẫn hoạt động.
        """
        bid = "save-lib-no-tags"
        self.manager.create(bid, "v1.0.0", "content", brief_type="master")
        self.manager.save_as_library(bid, "no-tags-brief")

        brief = self.manager.get(bid)
        assert brief["type"] == "library"
        assert brief["title"] == "no-tags-brief"

    def test_get_library_brief_by_name(self):
        """
        Test: get_library_brief() tìm đúng brief theo name (title).

        Verification: trả về brief record với type='library'.
        """
        self.manager.create("lb1", "v1.0.0", "content1", title="LibA", brief_type="library")
        self.manager.create("lb2", "v1.0.0", "content2", title="LibB", brief_type="library")

        found = self.manager.get_library_brief("LibA")
        assert found is not None
        assert found["brief_id"] == "lb1"
        assert found["type"] == "library"

    def test_get_library_brief_not_found(self):
        """
        Test: get_library_brief() không tìm thấy → None.
        """
        self.manager.create("lb1", "v1.0.0", "content", title="LibA", brief_type="library")

        found = self.manager.get_library_brief("NonExistent")
        assert found is None

    def test_duplicate_brief(self):
        """
        Test: duplicate_brief() tạo bản copy với brief_id mới và type mới.

        Verification:
        - Record mới có brief_id mới, type mới, status=draft
        - Content và hash giống bản gốc
        - Bản gốc không bị thay đổi
        """
        src_id = "src-brief"
        self.manager.create(src_id, "v2.0.0", "original content", title="Src Title", brief_type="library")

        new = self.manager.duplicate_brief(src_id, "new-brief-id", "working")

        assert new is not None
        assert new["brief_id"] == "new-brief-id"
        assert new["type"] == "working"
        assert new["status"] == "draft"
        assert new["content"] == "original content"
        assert new["title"] == "Src Title"
        assert new["version"] == "v2.0.0"

        # Bản gốc không đổi
        orig = self.manager.get(src_id)
        assert orig["type"] == "library"

    def test_duplicate_brief_unknown_source(self):
        """
        Test: duplicate_brief() với source không tồn tại → None.
        """
        result = self.manager.duplicate_brief("nonexistent", "new-id", "working")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])