from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BackupSnapshot:
    existed: bool
    backup_path: Path | None


def create_backup(target_path: Path, *, backup_root: Path) -> BackupSnapshot:
    if not target_path.exists():
        return BackupSnapshot(existed=False, backup_path=None)

    backup_root.mkdir(parents=True, exist_ok=True)
    backup_name = target_path.as_posix().replace("/", "__")
    backup_path = backup_root / f"{backup_name}.bak"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target_path, backup_path)
    return BackupSnapshot(existed=True, backup_path=backup_path)


def restore_backup(target_path: Path, snapshot: BackupSnapshot) -> bool:
    if snapshot.existed:
        if snapshot.backup_path is None or not snapshot.backup_path.exists():
            return False
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(snapshot.backup_path, target_path)
        return True

    if target_path.exists():
        target_path.unlink()
    return True
