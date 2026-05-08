# coding: utf-8
"""
Tests cho CP52 — Invariant Gate Framework.

Kiem tra:
- pack.yml ton tai va dong bo voi taxonomy.yml
- FastAPIInvariantEmitter.generate() emit dung files
- NestJSInvariantEmitter.generate() emit dung files
- BlueprintCompiler gate integration (compose goi InvariantManager)
- Template files ton tai cho 4 stacks

Tac gia: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import yaml

# Root cua project
ROOT = Path(__file__).resolve().parent.parent.parent


class TestPackYml:
    """Tests cho pack.yml cua CP52."""

    def test_pack_yml_exists(self) -> None:
        """Kiem tra pack.yml ton tai."""
        pack_yml = ROOT / "emitters/core/invariant/pack.yml"
        assert pack_yml.exists(), f"pack.yml khong ton tai tai {pack_yml}"

    def test_pack_yml_has_correct_id(self) -> None:
        """Kiem tra pack.yml co id=CP52."""
        pack_yml = ROOT / "emitters/core/invariant/pack.yml"
        with open(pack_yml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["id"] == "CP52"

    def test_pack_yml_capabilities_match_taxonomy(self) -> None:
        """Kiem tra capabilities_provided trong pack.yml match taxonomy.yml."""
        pack_yml = ROOT / "emitters/core/invariant/pack.yml"
        taxonomy_yml = ROOT.parent / "industry/taxonomy.yml"

        with open(pack_yml, "r", encoding="utf-8") as f:
            pack_data = yaml.safe_load(f)

        with open(taxonomy_yml, "r", encoding="utf-8") as f:
            taxonomy_data = yaml.safe_load(f)

        # Tim CP52 trong taxonomy
        cp52 = None
        for pack in taxonomy_data.get("core_packs", []):
            if pack.get("id") == "CP52":
                cp52 = pack
                break

        assert cp52 is not None, "CP52 khong ton tai trong taxonomy.yml"

        pack_caps = set(pack_data["pack"]["capabilities_provided"])
        taxonomy_caps = set(cp52.get("capabilities_provided", []))

        assert pack_caps == taxonomy_caps, (
            f"capabilities_provided khong match: pack.yml={pack_caps}, "
            f"taxonomy.yml={taxonomy_caps}"
        )

    def test_pack_yml_capabilities_correct(self) -> None:
        """Kiem tra capabilities_provided dung: enforce_invariant, gate_check."""
        pack_yml = ROOT / "emitters/core/invariant/pack.yml"
        with open(pack_yml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        caps = data["pack"]["capabilities_provided"]
        assert "enforce_invariant" in caps
        assert "gate_check" in caps

    def test_pack_yml_depends_on_cp51(self) -> None:
        """Kiem tra pack.yml depends_on CP51."""
        pack_yml = ROOT / "emitters/core/invariant/pack.yml"
        with open(pack_yml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "CP51" in data["pack"]["depends_on"]


class TestFastAPIInvariantEmitter:
    """Tests cho FastAPIInvariantEmitter."""

    def setup_method(self) -> None:
        """Reset InvariantManager truoc moi test."""
        from midicoder.emitters.core.invariant import InvariantManager
        InvariantManager.reset()

    def test_emitter_class_exists(self) -> None:
        """Kiem tra FastAPIInvariantEmitter class ton tai."""
        from midicoder.emitters.core.invariant.fastapi import FastAPIInvariantEmitter
        emitter = FastAPIInvariantEmitter()
        assert emitter is not None

    def test_generate_returns_dict(self) -> None:
        """Kiem tra generate() tra ve dict."""
        from midicoder.emitters.core.invariant.fastapi import FastAPIInvariantEmitter
        emitter = FastAPIInvariantEmitter()
        result = emitter.generate()
        assert isinstance(result, dict)

    def test_generate_has_gate_middleware(self) -> None:
        """Kiem tra generate() co gate middleware file."""
        from midicoder.emitters.core.invariant.fastapi import FastAPIInvariantEmitter
        emitter = FastAPIInvariantEmitter()
        result = emitter.generate()
        middleware_key = "src/middleware/invariant_gate.py"
        assert middleware_key in result, f"Thieu {middleware_key} trong output"
        assert "InvariantGateMiddleware" in result[middleware_key]

    def test_generate_has_invariant_utils(self) -> None:
        """Kiem tra generate() co invariant utils file."""
        from midicoder.emitters.core.invariant.fastapi import FastAPIInvariantEmitter
        emitter = FastAPIInvariantEmitter()
        result = emitter.generate()
        utils_key = "src/utils/invariant_utils.py"
        assert utils_key in result, f"Thieu {utils_key} trong output"
        assert "validate_invariants" in result[utils_key]

    def test_generate_gate_middleware(self) -> None:
        """Kiem tra generate_gate_middleware() tra ve dung file."""
        from midicoder.emitters.core.invariant.fastapi import FastAPIInvariantEmitter
        emitter = FastAPIInvariantEmitter()
        result = emitter.generate_gate_middleware()
        assert len(result) >= 1
        assert "invariant_gate" in list(result.keys())[0]

    def test_generate_runtime_guards_initializes_manager(self) -> None:
        """Kiem tra generate_runtime_guards() initialize manager."""
        from midicoder.emitters.core.invariant.fastapi import FastAPIInvariantEmitter
        emitter = FastAPIInvariantEmitter()
        result = emitter.generate_runtime_guards()
        assert isinstance(result, dict)


class TestNestJSInvariantEmitter:
    """Tests cho NestJSInvariantEmitter."""

    def test_emitter_class_exists(self) -> None:
        """Kiem tra NestJSInvariantEmitter class ton tai."""
        from midicoder.emitters.core.invariant.nestjs import NestJSInvariantEmitter
        emitter = NestJSInvariantEmitter()
        assert emitter is not None

    def test_generate_returns_dict(self) -> None:
        """Kiem tra generate() tra ve dict."""
        from midicoder.emitters.core.invariant.nestjs import NestJSInvariantEmitter
        emitter = NestJSInvariantEmitter()
        result = emitter.generate()
        assert isinstance(result, dict)

    def test_generate_has_gate_pipe(self) -> None:
        """Kiem tra generate() co gate pipe file."""
        from midicoder.emitters.core.invariant.nestjs import NestJSInvariantEmitter
        emitter = NestJSInvariantEmitter()
        result = emitter.generate()
        pipe_key = "src/common/pipes/invariant-gate.pipe.ts"
        assert pipe_key in result, f"Thieu {pipe_key} trong output"
        assert "InvariantGatePipe" in result[pipe_key]

    def test_generate_has_runtime_guard(self) -> None:
        """Kiem tra generate() co runtime guard file."""
        from midicoder.emitters.core.invariant.nestjs import NestJSInvariantEmitter
        emitter = NestJSInvariantEmitter()
        result = emitter.generate()
        guard_key = "src/common/guards/invariant.guard.ts"
        assert guard_key in result, f"Thieu {guard_key} trong output"
        assert "InvariantGuard" in result[guard_key]

    def test_generate_has_invariant_service(self) -> None:
        """Kiem tra generate() co invariant service file."""
        from midicoder.emitters.core.invariant.nestjs import NestJSInvariantEmitter
        emitter = NestJSInvariantEmitter()
        result = emitter.generate()
        service_key = "src/common/services/invariant.service.ts"
        assert service_key in result, f"Thieu {service_key} trong output"
        assert "InvariantService" in result[service_key]

    def test_generate_gate_pipe(self) -> None:
        """Kiem tra generate_gate_pipe() tra ve dung file."""
        from midicoder.emitters.core.invariant.nestjs import NestJSInvariantEmitter
        emitter = NestJSInvariantEmitter()
        result = emitter.generate_gate_pipe()
        assert len(result) >= 1
        assert ".pipe.ts" in list(result.keys())[0]

    def test_generate_runtime_guard(self) -> None:
        """Kiem tra generate_runtime_guard() tra ve dung file."""
        from midicoder.emitters.core.invariant.nestjs import NestJSInvariantEmitter
        emitter = NestJSInvariantEmitter()
        result = emitter.generate_runtime_guard()
        assert len(result) >= 1
        assert ".guard.ts" in list(result.keys())[0]


class TestTemplateFiles:
    """Tests cho Jinja2 template files cua 4 stacks."""

    def test_fastapi_gate_middleware_template_exists(self) -> None:
        """Kiem tra FastAPI gate middleware template ton tai."""
        template = ROOT / "stacks/fastapi/core/invariant/gate_middleware.py.jinja2"
        assert template.exists(), f"Template khong ton tai: {template}"

    def test_fastapi_runtime_guard_template_exists(self) -> None:
        """Kiem tra FastAPI runtime guard template ton tai."""
        template = ROOT / "stacks/fastapi/core/invariant/runtime_guard.py.jinja2"
        assert template.exists(), f"Template khong ton tai: {template}"

    def test_nestjs_gate_pipe_template_exists(self) -> None:
        """Kiem tra NestJS gate pipe template ton tai."""
        template = ROOT / "stacks/nestjs/core/invariant/gate.pipe.ts.jinja2"
        assert template.exists(), f"Template khong ton tai: {template}"

    def test_nestjs_runtime_guard_template_exists(self) -> None:
        """Kiem tra NestJS runtime guard template ton tai."""
        template = ROOT / "stacks/nestjs/core/invariant/runtime.guard.ts.jinja2"
        assert template.exists(), f"Template khong ton tai: {template}"

    def test_angular_compliance_interceptor_template_exists(self) -> None:
        """Kiem tra Angular compliance interceptor template ton tai."""
        template = ROOT / "stacks/angular/core/invariant/compliance.interceptor.ts.jinja2"
        assert template.exists(), f"Template khong ton tai: {template}"

    def test_angular_consent_guard_template_exists(self) -> None:
        """Kiem tra Angular consent guard template ton tai."""
        template = ROOT / "stacks/angular/core/invariant/consent.guard.ts.jinja2"
        assert template.exists(), f"Template khong ton tai: {template}"

    def test_angular_audit_service_template_exists(self) -> None:
        """Kiem tra Angular audit service template ton tai."""
        template = ROOT / "stacks/angular/core/invariant/audit.service.ts.jinja2"
        assert template.exists(), f"Template khong ton tai: {template}"

    def test_react_use_invariant_template_exists(self) -> None:
        """Kiem tra React useInvariant template ton tai."""
        template = ROOT / "stacks/react/core/invariant/useInvariant.ts.jinja2"
        assert template.exists(), f"Template khong ton tai: {template}"

    def test_react_invariant_context_template_exists(self) -> None:
        """Kiem tra React InvariantContext template ton tai."""
        template = ROOT / "stacks/react/core/invariant/InvariantContext.tsx.jinja2"
        assert template.exists(), f"Template khong ton tai: {template}"


class TestBlueprintCompilerGate:
    """Tests cho CP52 gate integration trong BlueprintCompiler."""

    def _create_mock_blueprint(self):
        """Tao mock CompiledBlueprint cho tests."""
        from midicoder.contracts.blueprint_compiler import (
            BlueprintConfig,
            CompiledBlueprint,
            CorePacksConfig,
            InvariantsConfig,
            IndustryInfo,
        )
        from midicoder.emitters.core.tenant.models import TenantConfig, TenantMode

        bp = CompiledBlueprint(
            industry=IndustryInfo(
                id="ecommerce-d2c",
                name="E-commerce D2C",
                group="Commerce/Logistics/Ops",
            ),
            core_packs=CorePacksConfig(
                mandatory=["CP01", "CP02", "CP03", "CP04", "CP07"],
                included=["CP08"],
            ),
            target_profiles=["local", "aws"],
            invariants=InvariantsConfig(),
            config=BlueprintConfig(
                tenant_config=TenantConfig(mode=TenantMode.SCHEMA),
            ),
        )
        bp.id = "test-blueprint-001"
        return bp

    def setup_method(self) -> None:
        """Reset InvariantManager truoc moi test."""
        from midicoder.emitters.core.invariant import InvariantManager
        InvariantManager.reset()

    def test_compose_with_mir_does_not_crash(self) -> None:
        """Kiem tra compose() voi MIR khong crash."""
        from midicoder.contracts.blueprint_compiler import BlueprintCompiler

        compiler = BlueprintCompiler()
        blueprint = self._create_mock_blueprint()

        # MIR voi cac thuoc tu co ban
        class SimpleMIR:
            operations = []
            instances = []
            obligations = []

        plan = compiler.compose(blueprint, mir=SimpleMIR())
        assert hasattr(plan, "emit_order"), "CompositionPlan phai co emit_order"

    def test_compose_without_mir(self) -> None:
        """Kiem tra compose() khong co MIR van hoat dong."""
        from midicoder.contracts.blueprint_compiler import BlueprintCompiler

        compiler = BlueprintCompiler()
        blueprint = self._create_mock_blueprint()

        # Khong co MIR -> invariant gate skip -> compose van hoat dong
        plan = compiler.compose(blueprint)
        assert hasattr(plan, "emit_order"), "CompositionPlan phai co emit_order"

    def test_invariant_gate_code_exists_in_compose(self) -> None:
        """Kiem tra CP52 gate code ton tai trong compose method."""
        import inspect
        from midicoder.contracts.blueprint_compiler import BlueprintCompiler

        source = inspect.getsource(BlueprintCompiler.compose)
        # Kiem tra InvariantManager duoc import va goi
        assert "InvariantManager" in source, "CP52 gate phai import InvariantManager"
        assert "invariant_manager.validate" in source, "CP52 gate phai goi validate()"
        assert "BLUEPRINT_INVARIANT_VIOLATION" in source, "CP52 gate phai raise BLUEPRINT_INVARIANT_VIOLATION"


class TestDirectoryStructure:
    """Tests cho directory structure cua CP52."""

    def test_emitter_directory_exists(self) -> None:
        """Kiem tra directory emitters/core/invariant ton tai."""
        d = ROOT / "emitters/core/invariant"
        assert d.is_dir(), f"Directory khong ton tai: {d}"

    def test_models_py_exists(self) -> None:
        """Kiem tra models.py ton tai."""
        f = ROOT / "emitters/core/invariant/models.py"
        assert f.is_file(), f"models.py khong ton tai: {f}"

    def test_registry_py_exists(self) -> None:
        """Kiem tra registry.py ton tai."""
        f = ROOT / "emitters/core/invariant/registry.py"
        assert f.is_file(), f"registry.py khong ton tai: {f}"

    def test_manager_py_exists(self) -> None:
        """Kiem tra manager.py ton tai."""
        f = ROOT / "emitters/core/invariant/manager.py"
        assert f.is_file(), f"manager.py khong ton tai: {f}"

    def test_fastapi_py_exists(self) -> None:
        """Kiem tra fastapi.py ton tai."""
        f = ROOT / "emitters/core/invariant/fastapi.py"
        assert f.is_file(), f"fastapi.py khong ton tai: {f}"

    def test_nestjs_py_exists(self) -> None:
        """Kiem tra nestjs.py ton tai."""
        f = ROOT / "emitters/core/invariant/nestjs.py"
        assert f.is_file(), f"nestjs.py khong ton tai: {f}"

    def test_business_checks_exists(self) -> None:
        """Kiem tra business/checks.py ton tai."""
        f = ROOT / "emitters/core/invariant/business/checks.py"
        assert f.is_file(), f"business/checks.py khong ton tai: {f}"

    def test_compliance_checks_exists(self) -> None:
        """Kiem tra compliance/checks.py ton tai."""
        f = ROOT / "emitters/core/invariant/compliance/checks.py"
        assert f.is_file(), f"compliance/checks.py khong ton tai: {f}"

    def test_failure_mode_checks_exists(self) -> None:
        """Kiem tra failure_mode/checks.py ton tai."""
        f = ROOT / "emitters/core/invariant/failure_mode/checks.py"
        assert f.is_file(), f"failure_mode/checks.py khong ton tai: {f}"

    def test_runtime_emitter_exists(self) -> None:
        """Kiem tra runtime/emitter.py ton tai."""
        f = ROOT / "emitters/core/invariant/runtime/emitter.py"
        assert f.is_file(), f"runtime/emitter.py khong ton tai: {f}"

    def test_domain_banking_exists(self) -> None:
        """Kiem tra domain/banking.py ton tai."""
        f = ROOT / "emitters/core/invariant/domain/banking.py"
        assert f.is_file(), f"domain/banking.py khong ton tai: {f}"

    def test_old_directory_removed(self) -> None:
        """Kiem tra contracts/invariants/ da bi xoa."""
        old = ROOT.parent / "contracts/invariants"
        assert not old.exists(), f"contracts/invariants/ van ton tai"


class TestTaxonomyUpdate:
    """Tests cho taxonomy.yml update."""

    def test_cp52_status_is_developing(self) -> None:
        """Kiem tra CP52 status trong taxonomy.yml la 'developing'."""
        taxonomy_yml = ROOT.parent / "industry/taxonomy.yml"
        with open(taxonomy_yml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        cp52 = None
        for pack in data.get("core_packs", []):
            if pack.get("id") == "CP52":
                cp52 = pack
                break

        assert cp52 is not None, "CP52 khong ton tai trong taxonomy.yml"
        assert cp52.get("status") == "developing", (
            f"CP52 status phai la 'developing', hien tai: {cp52.get('status')}"
        )
