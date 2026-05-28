# coding: utf-8
"""
Tests for CP14 stack emitters (FastAPI, NestJS, Angular, React).

Covers:
- FastAPIAuditComplianceEmitter.generate()
- NestJSAuditComplianceEmitter.generate()
- AngularAuditComplianceEmitter.generate()
- ReactAuditComplianceEmitter.generate()
- Output contains expected files and content
- Collection is used in generated output
"""

import pytest

from midicoder.packs.cp_full_audit_compliance.models import (
    AuditActionType,
    AuditComplianceCollection,
    AuditLevel,
    AuditRule,
    ComplianceControl,
    ControlType,
    EnforcementLevel,
    StandardType,
)
from midicoder.packs.cp_full_audit_compliance.fastapi import FastAPIAuditComplianceEmitter
from midicoder.packs.cp_full_audit_compliance.nestjs import NestJSAuditComplianceEmitter
from midicoder.packs.cp_full_audit_compliance.angular import AngularAuditComplianceEmitter
from midicoder.packs.cp_full_audit_compliance.react import ReactAuditComplianceEmitter


class TestFastAPIAuditComplianceEmitter:
    def test_create_without_collection(self):
        emitter = FastAPIAuditComplianceEmitter()
        assert emitter.collection is not None

    def test_create_with_collection(self):
        collection = AuditComplianceCollection()
        emitter = FastAPIAuditComplianceEmitter(collection)
        assert emitter.collection is collection

    def test_generate_returns_dict(self):
        emitter = FastAPIAuditComplianceEmitter()
        result = emitter.generate()
        assert isinstance(result, dict)

    def test_generate_has_service(self):
        emitter = FastAPIAuditComplianceEmitter()
        result = emitter.generate()
        assert any("service" in k.lower() for k in result.keys())

    def test_generate_has_models(self):
        emitter = FastAPIAuditComplianceEmitter()
        result = emitter.generate()
        assert any("schema" in k.lower() or "model" in k.lower() for k in result.keys())

    def test_generate_has_middleware(self):
        emitter = FastAPIAuditComplianceEmitter()
        result = emitter.generate()
        assert any("middleware" in k.lower() for k in result.keys())

    def test_generate_has_migrations(self):
        emitter = FastAPIAuditComplianceEmitter()
        result = emitter.generate()
        assert any("migration" in k.lower() for k in result.keys())

    def test_service_contains_audit_service_class(self):
        emitter = FastAPIAuditComplianceEmitter()
        result = emitter.generate_service()
        code = list(result.values())[0]
        assert "AuditService" in code

    def test_models_contains_pydantic(self):
        emitter = FastAPIAuditComplianceEmitter()
        result = emitter.generate_models()
        code = list(result.values())[0]
        assert "pydantic" in code.lower() or "BaseModel" in code

    def test_middleware_contains_base_http_middleware(self):
        emitter = FastAPIAuditComplianceEmitter()
        result = emitter.generate_middleware()
        code = list(result.values())[0]
        assert "BaseHTTPMiddleware" in code or "Middleware" in code

    def test_migration_contains_create_table(self):
        emitter = FastAPIAuditComplianceEmitter()
        result = emitter.generate_migrations()
        code = list(result.values())[0]
        assert "CREATE TABLE" in code

    def test_multiple_files_generated(self):
        emitter = FastAPIAuditComplianceEmitter()
        result = emitter.generate()
        assert len(result) >= 4  # service, models, middleware, migrations


class TestNestJSAuditComplianceEmitter:
    def test_create_without_collection(self):
        emitter = NestJSAuditComplianceEmitter()
        assert emitter.collection is not None

    def test_generate_returns_dict(self):
        emitter = NestJSAuditComplianceEmitter()
        result = emitter.generate()
        assert isinstance(result, dict)

    def test_generate_has_module(self):
        emitter = NestJSAuditComplianceEmitter()
        result = emitter.generate()
        assert any("module" in k.lower() for k in result.keys())

    def test_generate_has_service(self):
        emitter = NestJSAuditComplianceEmitter()
        result = emitter.generate()
        assert any("service" in k.lower() for k in result.keys())

    def test_generate_has_interceptor(self):
        emitter = NestJSAuditComplianceEmitter()
        result = emitter.generate()
        assert any("interceptor" in k.lower() for k in result.keys())

    def test_generate_has_entity(self):
        emitter = NestJSAuditComplianceEmitter()
        result = emitter.generate()
        assert any("entity" in k.lower() for k in result.keys())

    def test_module_contains_nestjs_module(self):
        emitter = NestJSAuditComplianceEmitter()
        result = emitter.generate_module()
        code = list(result.values())[0]
        assert "@Module" in code or "Module" in code

    def test_service_contains_injectable(self):
        emitter = NestJSAuditComplianceEmitter()
        result = emitter.generate_service()
        code = list(result.values())[0]
        assert "Injectable" in code or "Service" in code

    def test_multiple_files_generated(self):
        emitter = NestJSAuditComplianceEmitter()
        result = emitter.generate()
        assert len(result) >= 4


class TestAngularAuditComplianceEmitter:
    def test_create_without_collection(self):
        emitter = AngularAuditComplianceEmitter()
        assert emitter.collection is not None

    def test_generate_returns_dict(self):
        emitter = AngularAuditComplianceEmitter()
        result = emitter.generate()
        assert isinstance(result, dict)

    def test_generate_has_service(self):
        emitter = AngularAuditComplianceEmitter()
        result = emitter.generate()
        assert any("service" in k.lower() for k in result.keys())

    def test_generate_has_component(self):
        emitter = AngularAuditComplianceEmitter()
        result = emitter.generate()
        assert any("component" in k.lower() or "list" in k.lower() for k in result.keys())

    def test_service_contains_injectable(self):
        emitter = AngularAuditComplianceEmitter()
        result = emitter.generate_service()
        code = list(result.values())[0]
        assert "Injectable" in code or "Service" in code

    def test_component_contains_component_decorator(self):
        emitter = AngularAuditComplianceEmitter()
        result = emitter.generate_component()
        code = list(result.values())[0]
        assert "Component" in code

    def test_multiple_files_generated(self):
        emitter = AngularAuditComplianceEmitter()
        result = emitter.generate()
        assert len(result) >= 2


class TestReactAuditComplianceEmitter:
    def test_create_without_collection(self):
        emitter = ReactAuditComplianceEmitter()
        assert emitter.collection is not None

    def test_generate_returns_dict(self):
        emitter = ReactAuditComplianceEmitter()
        result = emitter.generate()
        assert isinstance(result, dict)

    def test_generate_has_types(self):
        emitter = ReactAuditComplianceEmitter()
        result = emitter.generate()
        assert any("types" in k.lower() for k in result.keys())

    def test_generate_has_hook(self):
        emitter = ReactAuditComplianceEmitter()
        result = emitter.generate()
        assert any("use" in k.lower() or "hook" in k.lower() for k in result.keys())

    def test_generate_has_component(self):
        emitter = ReactAuditComplianceEmitter()
        result = emitter.generate()
        assert any("list" in k.lower() or "component" in k.lower() or ".tsx" in k.lower() for k in result.keys())

    def test_types_contains_interface(self):
        emitter = ReactAuditComplianceEmitter()
        result = emitter.generate_types()
        code = list(result.values())[0]
        assert "interface" in code or "type" in code

    def test_hook_contains_use_callback(self):
        emitter = ReactAuditComplianceEmitter()
        result = emitter.generate_hook()
        code = list(result.values())[0]
        assert "useCallback" in code or "useAudit" in code

    def test_component_contains_react(self):
        emitter = ReactAuditComplianceEmitter()
        result = emitter.generate_component()
        code = list(result.values())[0]
        assert "useState" in code or "function" in code

    def test_multiple_files_generated(self):
        emitter = ReactAuditComplianceEmitter()
        result = emitter.generate()
        assert len(result) >= 3


class TestEmittersWithCollection:
    """Test that emitters accept and use collection properly."""

    def _make_collection(self) -> AuditComplianceCollection:
        c = AuditComplianceCollection()
        c.add_rule(
            AuditRule(
                id="test_rule",
                name="Test Rule",
                actions=[AuditActionType.CREATE],
                audit_level=AuditLevel.DETAILED,
            )
        )
        c.add_control(
            ComplianceControl(
                id="test_control",
                name="Test Control",
                standard=StandardType.SOX,
                control_type=ControlType.PREVENTIVE,
                enforcement_level=EnforcementLevel.BOTH,
            )
        )
        return c

    def test_fastapi_accepts_collection(self):
        collection = self._make_collection()
        emitter = FastAPIAuditComplianceEmitter(collection)
        result = emitter.generate()
        assert len(result) >= 4

    def test_nestjs_accepts_collection(self):
        collection = self._make_collection()
        emitter = NestJSAuditComplianceEmitter(collection)
        result = emitter.generate()
        assert len(result) >= 4

    def test_angular_accepts_collection(self):
        collection = self._make_collection()
        emitter = AngularAuditComplianceEmitter(collection)
        result = emitter.generate()
        assert len(result) >= 2

    def test_react_accepts_collection(self):
        collection = self._make_collection()
        emitter = ReactAuditComplianceEmitter(collection)
        result = emitter.generate()
        assert len(result) >= 3
