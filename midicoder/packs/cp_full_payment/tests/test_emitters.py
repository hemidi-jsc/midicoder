# coding: utf-8
"""
Tests cho CP45 emitters — Payment Gateway Abstraction.
"""

from __future__ import annotations

import pytest
from pathlib import Path
import yaml

from midicoder.packs.cp_full_payment.parser import parse_to_ir, PaymentIR

PACK_DIR = Path(__file__).resolve().parent.parent
PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent


class TestFastAPIEmitter:
    @pytest.fixture
    def emitter(self):
        from midicoder.packs.cp_full_payment.fastapi import FastAPIPaymentEmitter
        stacks_dir = PACKAGE_DIR / "stacks"
        return FastAPIPaymentEmitter(stacks_dir / "fastapi" / "core")

    @pytest.fixture
    def ir(self):
        return parse_to_ir({
            "gateways": [
                {"config_id": "stripe", "gateway_type": "stripe"},
                {"config_id": "vnpay", "gateway_type": "vnpay"},
            ],
            "default_gateway": "stripe",
            "enable_idempotency": True,
            "enable_refunds": True,
        })

    def test_emit_returns_files(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) > 0

    def test_emit_template_count(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) == 6

    def test_emit_has_models(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        paths = [f.path for f in files]
        assert any("payment_models" in p for p in paths)

    def test_emit_has_service(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        paths = [f.path for f in files]
        assert any("payment_service" in p for p in paths)

    def test_invalid_dir_raises_error(self):
        from midicoder.packs.cp_full_payment.fastapi import FastAPIPaymentEmitter
        from midicoder.errors import MidicoderError
        with pytest.raises(MidicoderError):
            FastAPIPaymentEmitter("/nonexistent/path")


class TestNestJSEmitter:
    @pytest.fixture
    def emitter(self):
        from midicoder.packs.cp_full_payment.nestjs import NestJSPaymentEmitter
        stacks_dir = PACKAGE_DIR / "stacks"
        return NestJSPaymentEmitter(stacks_dir / "nestjs" / "core")

    @pytest.fixture
    def ir(self):
        return parse_to_ir({"gateways": [{"config_id": "stripe", "gateway_type": "stripe"}]})

    def test_emit_returns_files(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) > 0

    def test_emit_template_count(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) == 6

    def test_invalid_dir_raises_error(self):
        from midicoder.packs.cp_full_payment.nestjs import NestJSPaymentEmitter
        from midicoder.errors import MidicoderError
        with pytest.raises(MidicoderError):
            NestJSPaymentEmitter("/nonexistent/path")


class TestAngularEmitter:
    @pytest.fixture
    def emitter(self):
        from midicoder.packs.cp_full_payment.angular import AngularPaymentEmitter
        stacks_dir = PACKAGE_DIR / "stacks"
        return AngularPaymentEmitter(stacks_dir / "angular" / "core")

    @pytest.fixture
    def ir(self):
        return parse_to_ir({})

    def test_emit_returns_files(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) > 0

    def test_emit_template_count(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) == 6

    def test_invalid_dir_raises_error(self):
        from midicoder.packs.cp_full_payment.angular import AngularPaymentEmitter
        from midicoder.errors import MidicoderError
        with pytest.raises(MidicoderError):
            AngularPaymentEmitter("/nonexistent/path")


class TestReactEmitter:
    @pytest.fixture
    def emitter(self):
        from midicoder.packs.cp_full_payment.react import ReactPaymentEmitter
        stacks_dir = PACKAGE_DIR / "stacks"
        return ReactPaymentEmitter(stacks_dir / "react" / "core")

    @pytest.fixture
    def ir(self):
        return parse_to_ir({})

    def test_emit_returns_files(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) > 0

    def test_emit_with_context(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        for f in files:
            assert len(f.content) > 0

    def test_invalid_dir_raises_error(self):
        from midicoder.packs.cp_full_payment.react import ReactPaymentEmitter
        from midicoder.errors import MidicoderError
        with pytest.raises(MidicoderError):
            ReactPaymentEmitter("/nonexistent/path")


class TestEmitterIntegration:
    """Test IR data flows through emitter correctly."""

    def test_ir_data_flows_through_emitter(self, tmp_path):
        from midicoder.packs.cp_full_payment.fastapi import FastAPIPaymentEmitter
        stacks_dir = PACKAGE_DIR / "stacks"
        emitter = FastAPIPaymentEmitter(stacks_dir / "fastapi" / "core")
        ir = parse_to_ir({
            "gateways": [
                {"config_id": "stripe", "gateway_type": "stripe"},
            ],
            "default_currency": "EUR",
        })
        files = emitter.emit(ir, tmp_path)
        assert len(files) > 0
        for f in files:
            assert f.content  # có nội dung


class TestPackManifest:
    def test_pack_yml_exists(self):
        assert (PACK_DIR / "pack.yml").exists()

    def test_pack_yml_valid_yaml(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert "pack" in data

    def test_pack_id(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["id"] == "CP45"

    def test_pack_internal_id(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["internal_id"] == "cp_full_payment"

    def test_pack_version(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["version"] == "1.0.0"

    def test_pack_status(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["status"] == "stable"

    def test_pack_category(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["category"] == "financial"

    def test_pack_definitions_count(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["definitions_count"] == 4

    def test_pack_obligations_count(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["obligations_count"] == 2

    def test_pack_capabilities_provided(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        caps = data["pack"]["capabilities_provided"]
        assert "payment_process" in caps
        assert "payment_method_manage" in caps
        assert "transaction_flow" in caps
        assert "refund_process" in caps

    def test_pack_depends_on(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "CP01" in data["pack"]["depends_on"]
        assert "CP05" in data["pack"]["depends_on"]
        assert "CP14" in data["pack"]["depends_on"]
        assert "CP33" in data["pack"]["depends_on"]
        assert "CP40" in data["pack"]["depends_on"]

    def test_pack_error_codes_prefix(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["error_codes"]["prefix"] == "MDC-CP45"

    def test_pack_definitions(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        defs = data["pack"]["definitions"]
        def_names = [d["name"] for d in defs]
        assert "PaymentTransaction" in def_names
        assert "PaymentMethod" in def_names
        assert "PaymentRefund" in def_names
        assert "PaymentGatewayConfig" in def_names

    def test_pack_file_contributions_count(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        contributions = data["pack"]["file_contributions"]["infrastructure"]
        assert len(contributions) >= 20

    def test_pack_file_contributions_by_stack(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        contributions = data["pack"]["file_contributions"]["infrastructure"]
        stacks_found = set()
        for contrib in contributions:
            stacks_found.update(contrib["stacks"])
        assert "fastapi" in stacks_found
        assert "nestjs" in stacks_found
        assert "angular" in stacks_found
        assert "react" in stacks_found

    def test_pack_frontend_integration(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        fe = data["pack"]["frontend_integration"]
        assert "react" in fe
        assert "angular" in fe
        assert "PaymentDashboard" in fe["react"]
        assert "PaymentDashboardComponent" in fe["angular"]

    def test_pack_recipes(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        recipes = data["pack"]["recipes"]
        assert "basic_payment_recipe" in recipes
        assert "full_payment_recipe" in recipes


class TestStackTemplates:
    """Kiểm tra templates tồn tại và có nội dung."""

    def _check_templates(self, stack_dir_name, expected_count):
        stacks_dir = PACKAGE_DIR / "stacks"
        template_dir = stacks_dir / stack_dir_name / "core" / "cp_full_payment"
        templates = list(template_dir.glob("*.jinja2"))
        assert len(templates) == expected_count, f"Expected {expected_count} templates in {stack_dir_name}, found {len(templates)}"
        for t in templates:
            content = t.read_text(encoding="utf-8")
            assert len(content) > 50, f"Template {t.name} quá ngắn"

    def test_fastapi_templates(self):
        self._check_templates("fastapi", 6)

    def test_nestjs_templates(self):
        self._check_templates("nestjs", 6)

    def test_angular_templates(self):
        self._check_templates("angular", 6)

    def test_react_templates(self):
        self._check_templates("react", 6)


class TestChangelog:
    def test_changelog_exists(self):
        assert (PACK_DIR / "CHANGELOG.md").exists()

    def test_changelog_has_version(self):
        content = (PACK_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "1.0.0" in content


class TestRegistry:
    def test_cp45_in_registry(self):
        from midicoder.contracts.registry import CP_ID_TO_INTERNAL
        assert "CP45" in CP_ID_TO_INTERNAL
        assert CP_ID_TO_INTERNAL["CP45"] == "cp_full_payment"


class TestInitModule:
    def test_init_exists(self):
        assert (PACK_DIR / "__init__.py").exists()

    def test_init_exports_models(self):
        from midicoder.packs.cp_full_payment import (
            PaymentEngine,
            PaymentTransaction,
            PaymentMethod,
            PaymentRefund,
            PaymentGatewayConfig,
        )
        assert PaymentEngine is not None

    def test_init_exports_parser(self):
        from midicoder.packs.cp_full_payment import (
            PaymentIR,
            parse_to_ir,
            parse_gateways,
        )
        assert PaymentIR is not None

    def test_init_exports_recipes(self):
        from midicoder.packs.cp_full_payment import (
            basic_payment_recipe,
            full_payment_recipe,
        )
        assert callable(basic_payment_recipe)
        assert callable(full_payment_recipe)
