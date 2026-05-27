"""
Tests cho CP65 FastAPI Backup Emitter.

Unit tests cho:
- FastAPIBackupEmitter init (requires valid stack_dir)
- GeneratedFile dataclass
- emit returns files with correct structure

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from midicoder.packs.cp65_backup_recovery.models import (
    BackupPolicy,
    BackupType,
    RecoveryPlan,
    RecoveryStep,
    RestorePoint,
    StorageBackend,
    BackupMonitor,
)
from midicoder.packs.cp65_backup_recovery.parser import BackupIR
from midicoder.packs.cp65_backup_recovery.fastapi import (
    FastAPIBackupEmitter,
    GeneratedFile,
)


# ===========================================================================
# Test GeneratedFile
# ===========================================================================


class TestGeneratedFile:
    """Tests cho GeneratedFile dataclass."""

    def test_create(self):
        gf = GeneratedFile(path="test.py", content="print('hello')")
        assert gf.path == "test.py"
        assert gf.content == "print('hello')"

    def test_with_path_obj(self, tmp_path: Path):
        gf = GeneratedFile(
            path=tmp_path / "app" / "test.py",
            content="x = 1",
        )
        assert "test.py" in str(gf.path)


# ===========================================================================
# Test FastAPIBackupEmitter
# ===========================================================================


class TestFastAPIBackupEmitter:
    """Tests cho FastAPIBackupEmitter."""

    @pytest.fixture
    def backup_ir(self) -> BackupIR:
        """BackupIR fixture với basic backup policy."""
        return BackupIR(
            backup_policies=[
                BackupPolicy(
                    id="db-full",
                    name="Daily Full",
                    backup_type=BackupType.FULL,
                    target="postgresql://db:5432/app",
                    storage_backend=StorageBackend.S3,
                    retention_days=30,
                    encryption_enabled=True,
                )
            ],
            restore_points=[
                RestorePoint(
                    id="rp1",
                    backup_policy_id="db-full",
                    timestamp="2026-05-25T02:00:00Z",
                    size_bytes=1073741824,
                )
            ],
            recovery_plans=[
                RecoveryPlan(
                    id="dr-plan",
                    name="DR Plan",
                    rto_minutes=30,
                    steps=[
                        RecoveryStep(id="s1", order=1, action="restore", target="db"),
                    ],
                )
            ],
            monitors=[
                BackupMonitor(id="mon1", policy_ids=["db-full"]),
            ],
            default_retention_days=30,
            enable_encryption=True,
        )

    @pytest.fixture
    def stack_dir(self) -> Path:
        """Tạo template directory với mock templates."""
        tmp = Path(tempfile.mkdtemp())
        template_dir = tmp / "cp65_backup_recovery"
        template_dir.mkdir()
        # Tạo mock templates
        for name in [
            "backup_service.py.jinja2",
            "restore_service.py.jinja2",
            "backup_router.py.jinja2",
            "backup_scheduler.py.jinja2",
        ]:
            (template_dir / name).write_text("{{ policy_count }} files from cp65")
        return tmp

    @pytest.fixture
    def output_dir(self) -> Path:
        """Tạo output directory."""
        tmp = Path(tempfile.mkdtemp())
        yield tmp
        shutil.rmtree(tmp, ignore_errors=True)

    def test_emitter_requires_stack_dir(self):
        """Test emitter raise khi stack_dir không tồn tại."""
        with pytest.raises(Exception):
            FastAPIBackupEmitter(Path("/nonexistent/path"))

    def test_init_creates_jinja_env(self, stack_dir: Path):
        """Test emitter init tạo Jinja2 environment."""
        emitter = FastAPIBackupEmitter(stack_dir)
        assert emitter.env is not None
        assert emitter.template_dir == stack_dir / "cp65_backup_recovery"

    def test_emit_returns_generated_files(self, backup_ir: BackupIR, stack_dir: Path, output_dir: Path):
        """Test emit trả về danh sách GeneratedFile."""
        emitter = FastAPIBackupEmitter(stack_dir)
        files = emitter.emit(backup_ir, output_dir)
        assert isinstance(files, list)
        assert len(files) == 4
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_file_paths(self, backup_ir: BackupIR, stack_dir: Path, output_dir: Path):
        """Test emit tạo đúng file paths."""
        emitter = FastAPIBackupEmitter(stack_dir)
        files = emitter.emit(backup_ir, output_dir)
        paths = [f.path for f in files]
        assert "app/services/backup_service.py" in paths
        assert "app/services/restore_service.py" in paths
        assert "app/api/backup_router.py" in paths
        assert "app/services/backup_scheduler.py" in paths

    def test_emit_content_not_empty(self, backup_ir: BackupIR, stack_dir: Path, output_dir: Path):
        """Test emit tạo nội dung không rỗng."""
        emitter = FastAPIBackupEmitter(stack_dir)
        files = emitter.emit(backup_ir, output_dir)
        for f in files:
            assert len(f.content) > 0

    def test_emit_with_no_templates(self, backup_ir: BackupIR, stack_dir: Path, output_dir: Path):
        """Test emit khi không có templates (empty template dir)."""
        # Xóa tất cả templates
        for f in (stack_dir / "cp65_backup_recovery").iterdir():
            f.unlink()
        emitter = FastAPIBackupEmitter(stack_dir)
        files = emitter.emit(backup_ir, output_dir)
        assert files == []

    def test_emit_context_has_policy_count(self, backup_ir: BackupIR, stack_dir: Path, output_dir: Path):
        """Test emit context chứa policy_count."""
        emitter = FastAPIBackupEmitter(stack_dir)
        files = emitter.emit(backup_ir, output_dir)
        # mock templates render policy_count
        for f in files:
            assert "1" in f.content  # policy_count = 1

    def test_emit_multiple_policies(self, stack_dir: Path, output_dir: Path):
        """Test emit với nhiều backup policies."""
        ir = BackupIR(
            backup_policies=[
                BackupPolicy(id="a", name="A"),
                BackupPolicy(id="b", name="B"),
                BackupPolicy(id="c", name="C"),
            ]
        )
        emitter = FastAPIBackupEmitter(stack_dir)
        files = emitter.emit(ir, output_dir)
        assert len(files) == 4
        # content chứa policy_count = 3
        for f in files:
            assert "3" in f.content

    def test_emit_minimal_ir(self, stack_dir: Path, output_dir: Path):
        """Test emit với BackupIR tối thiểu."""
        ir = BackupIR()
        emitter = FastAPIBackupEmitter(stack_dir)
        files = emitter.emit(ir, output_dir)
        assert len(files) == 4

    def test_emit_with_recovery_plan(self, stack_dir: Path, output_dir: Path):
        """Test emit với recovery plan."""
        ir = BackupIR(
            backup_policies=[BackupPolicy(id="p1", name="P1")],
            recovery_plans=[
                RecoveryPlan(
                    id="plan1",
                    name="DR Plan",
                    steps=[
                        RecoveryStep(id="s1", order=1, action="restore", target="db"),
                        RecoveryStep(id="s2", order=2, action="verify", target="db", dependencies=["s1"]),
                    ],
                )
            ],
        )
        emitter = FastAPIBackupEmitter(stack_dir)
        files = emitter.emit(ir, output_dir)
        assert len(files) == 4
