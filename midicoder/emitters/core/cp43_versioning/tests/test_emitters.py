# coding: utf-8
"""
Test cho CP43 emitters — FastAPI, NestJS, Angular, React.
"""

import pytest

from midicoder.emitters.core.cp43_versioning.fastapi import FastAPIVersioningEmitter
from midicoder.emitters.core.cp43_versioning.nestjs import NestJSVersioningEmitter
from midicoder.emitters.core.cp43_versioning.angular import AngularVersioningEmitter
from midicoder.emitters.core.cp43_versioning.react import ReactVersioningEmitter
from midicoder.emitters.core.cp43_versioning.models import (
    VersionConfig,
    VersioningCollection,
)


class TestFastAPIVersioningEmitter:
    """Test cho FastAPIVersioningEmitter."""

    def setup_method(self) -> None:
        """Setup emitter trước mỗi test."""
        self.collection = VersioningCollection()
        self.collection.add_config(VersionConfig(entity_type="Order"))
        self.emitter = FastAPIVersioningEmitter(self.collection)

    def test_generate_returns_dict(self) -> None:
        """Kiểm tra generate trả về dict."""
        result = self.emitter.generate()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_generate_version_mixin(self) -> None:
        """Kiểm tra sinh version mixin."""
        result = self.emitter.generate_version_mixin()
        assert "app/models/mixins/version_mixin.py" in result
        code = result["app/models/mixins/version_mixin.py"]
        assert "VersionMixin" in code
        assert "check_version" in code
        assert "bump_version" in code
        assert "from midicoder" not in code

    def test_generate_soft_delete_mixin(self) -> None:
        """Kiểm tra sinh soft delete mixin."""
        result = self.emitter.generate_soft_delete_mixin()
        assert "app/models/mixins/soft_delete_mixin.py" in result
        code = result["app/models/mixins/soft_delete_mixin.py"]
        assert "SoftDeleteMixin" in code
        assert "soft_delete" in code
        assert "restore" in code
        assert "hard_delete" in code
        assert "apply_soft_delete_filter" in code

    def test_generate_history_model(self) -> None:
        """Kiểm tra sinh history model."""
        result = self.emitter.generate_history_model()
        assert "app/models/mixins/entity_history.py" in result
        code = result["app/models/mixins/entity_history.py"]
        assert "EntityHistoryMixin" in code
        assert "snapshot" in code
        assert "immutable_hash" in code
        assert "compute_hash" in code

    def test_generate_history_repository(self) -> None:
        """Kiểm tra sinh history repository."""
        result = self.emitter.generate_history_repository()
        assert "app/repositories/history_repository.py" in result
        code = result["app/repositories/history_repository.py"]
        assert "HistoryRepository" in code
        assert "get_at_version" in code
        assert "get_at_timestamp" in code
        assert "get_version_history" in code
        assert "get_changes_between" in code
        assert "get_latest_version" in code

    def test_generate_audit_integration(self) -> None:
        """Kiểm tra sinh audit integration."""
        result = self.emitter.generate_audit_integration()
        assert "app/services/version_audit_logger.py" in result
        code = result["app/services/version_audit_logger.py"]
        assert "VersionAuditLogger" in code
        assert "log_version_change" in code

    def test_generate_no_from_midicoder(self) -> None:
        """Kiểm tra generated code không có 'from midicoder'."""
        result = self.emitter.generate()
        for path, code in result.items():
            assert "from midicoder" not in code, f"File {path} contains 'from midicoder'"

    def test_generate_no_post_init(self) -> None:
        """Kiểm tra generated code không có __post_init__."""
        result = self.emitter.generate()
        for path, code in result.items():
            assert "__post_init__" not in code, f"File {path} contains '__post_init__'"


class TestNestJSVersioningEmitter:
    """Test cho NestJSVersioningEmitter."""

    def setup_method(self) -> None:
        """Setup emitter trước mỗi test."""
        self.collection = VersioningCollection()
        self.collection.add_config(VersionConfig(entity_type="Order"))
        self.emitter = NestJSVersioningEmitter(self.collection)

    def test_generate_returns_dict(self) -> None:
        """Kiểm tra generate trả về dict."""
        result = self.emitter.generate()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_generate_version_decorator(self) -> None:
        """Kiểm tra sinh version decorator."""
        result = self.emitter.generate_version_decorator()
        assert "src/common/decorators/versioned.decorator.ts" in result
        code = result["src/common/decorators/versioned.decorator.ts"]
        assert "Versioned" in code
        assert "checkVersion" in code

    def test_generate_soft_delete_decorator(self) -> None:
        """Kiểm tra sinh soft delete decorator."""
        result = self.emitter.generate_soft_delete_decorator()
        assert "src/common/decorators/soft-delete.decorator.ts" in result
        code = result["src/common/decorators/soft-delete.decorator.ts"]
        assert "SoftDelete" in code
        assert "filterSoftDeleted" in code

    def test_generate_history_entity(self) -> None:
        """Kiểm tra sinh history entity."""
        result = self.emitter.generate_history_entity()
        assert "src/common/entities/history-entity.ts" in result
        code = result["src/common/entities/history-entity.ts"]
        assert "EntityHistory" in code
        assert "snapshot" in code

    def test_generate_history_service(self) -> None:
        """Kiểm tra sinh history service."""
        result = self.emitter.generate_history_service()
        assert "src/common/services/history.service.ts" in result
        code = result["src/common/services/history.service.ts"]
        assert "HistoryService" in code
        assert "getAtVersion" in code
        assert "getAtTimestamp" in code

    def test_generate_audit_integration(self) -> None:
        """Kiểm tra sinh audit integration."""
        result = self.emitter.generate_audit_integration()
        assert "src/common/services/version-audit-logger.ts" in result
        code = result["src/common/services/version-audit-logger.ts"]
        assert "VersionAuditLogger" in code


class TestAngularVersioningEmitter:
    """Test cho AngularVersioningEmitter."""

    def setup_method(self) -> None:
        """Setup emitter trước mỗi test."""
        self.collection = VersioningCollection()
        self.collection.add_config(VersionConfig(entity_type="Order"))
        self.emitter = AngularVersioningEmitter(self.collection)

    def test_generate_returns_dict(self) -> None:
        """Kiểm tra generate trả về dict."""
        result = self.emitter.generate()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_generate_service(self) -> None:
        """Kiểm tra sinh service."""
        result = self.emitter.generate_service()
        assert "src/app/core/versioning/version-history.service.ts" in result
        code = result["src/app/core/versioning/version-history.service.ts"]
        assert "VersionHistoryService" in code
        assert "getVersionHistory" in code

    def test_generate_component(self) -> None:
        """Kiểm tra sinh component."""
        result = self.emitter.generate_component()
        assert "src/app/shared/components/version-history/version-history.component.ts" in result
        code = result["src/app/shared/components/version-history/version-history.component.ts"]
        assert "VersionHistoryComponent" in code
        assert "restoreVersion" in code

    def test_generate_restore_dialog(self) -> None:
        """Kiểm tra sinh restore dialog."""
        result = self.emitter.generate_restore_dialog()
        assert "src/app/shared/components/version-history/restore-version-dialog.component.ts" in result
        code = result["src/app/shared/components/version-history/restore-version-dialog.component.ts"]
        assert "RestoreVersionDialogComponent" in code

    def test_generate_indicator(self) -> None:
        """Kiểm tra sinh soft delete indicator."""
        result = self.emitter.generate_indicator()
        assert "src/app/shared/components/soft-delete-indicator/soft-delete-indicator.component.ts" in result
        code = result["src/app/shared/components/soft-delete-indicator/soft-delete-indicator.component.ts"]
        assert "SoftDeleteIndicatorComponent" in code


class TestReactVersioningEmitter:
    """Test cho ReactVersioningEmitter."""

    def setup_method(self) -> None:
        """Setup emitter trước mỗi test."""
        self.collection = VersioningCollection()
        self.collection.add_config(VersionConfig(entity_type="Order"))
        self.emitter = ReactVersioningEmitter(self.collection)

    def test_generate_returns_dict(self) -> None:
        """Kiểm tra generate trả về dict."""
        result = self.emitter.generate()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_generate_types(self) -> None:
        """Kiểm tra sinh types."""
        result = self.emitter.generate_types()
        assert "src/versioning/types.ts" in result
        code = result["src/versioning/types.ts"]
        assert "VersionHistoryEntry" in code
        assert "VersionHistoryProps" in code
        assert "SoftDeleteIndicatorProps" in code

    def test_generate_hook(self) -> None:
        """Kiểm tra sinh hook."""
        result = self.emitter.generate_hook()
        assert "src/versioning/useVersionHistory.ts" in result
        code = result["src/versioning/useVersionHistory.ts"]
        assert "useVersionHistory" in code
        assert "loadHistory" in code
        assert "restoreToVersion" in code

    def test_generate_component(self) -> None:
        """Kiểm tra sinh component."""
        result = self.emitter.generate_component()
        assert "src/versioning/VersionHistory.tsx" in result
        code = result["src/versioning/VersionHistory.tsx"]
        assert "VersionHistory" in code
        assert "restoreToVersion" in code

    def test_generate_restore_modal(self) -> None:
        """Kiểm tra sinh restore modal."""
        result = self.emitter.generate_restore_modal()
        assert "src/versioning/RestoreVersionModal.tsx" in result
        code = result["src/versioning/RestoreVersionModal.tsx"]
        assert "RestoreVersionModal" in code

    def test_generate_indicator(self) -> None:
        """Kiểm tra sinh soft delete indicator."""
        result = self.emitter.generate_indicator()
        assert "src/versioning/SoftDeleteIndicator.tsx" in result
        code = result["src/versioning/SoftDeleteIndicator.tsx"]
        assert "SoftDeleteIndicator" in code

    def test_no_jsx_inline_style(self) -> None:
        """Kiểm tra React templates không có {{ }} JSX inline style."""
        result = self.emitter.generate()
        for path, code in result.items():
            if path.endswith(".tsx"):
                # Check for {{ }} inside JSX style attribute (not Jinja2 template vars)
                assert "{{ }}" not in code, f"File {path} contains '{{ }}' JSX inline style"


class TestEmitterEmptyCollection:
    """Test emitters với empty collection."""

    def test_fastapi_empty(self) -> None:
        """Kiểm tra FastAPI emitter với empty collection."""
        emitter = FastAPIVersioningEmitter()
        result = emitter.generate()
        assert len(result) > 0

    def test_nestjs_empty(self) -> None:
        """Kiểm tra NestJS emitter với empty collection."""
        emitter = NestJSVersioningEmitter()
        result = emitter.generate()
        assert len(result) > 0

    def test_angular_empty(self) -> None:
        """Kiểm tra Angular emitter với empty collection."""
        emitter = AngularVersioningEmitter()
        result = emitter.generate()
        assert len(result) > 0

    def test_react_empty(self) -> None:
        """Kiểm tra React emitter với empty collection."""
        emitter = ReactVersioningEmitter()
        result = emitter.generate()
        assert len(result) > 0
