# coding: utf-8
"""
Tests for CP46 emitters — MFA & Advanced Authentication.
"""

import pytest
from pathlib import Path
from midicoder.packs.cp_full_mfa.parser import MFAIR, MFARule
from midicoder.packs.cp_full_mfa.models import MFAMethod, MFAPriority


class TestFastAPIMFAEmitter:
    @pytest.fixture(autouse=True)
    def setup(self):
        import os
        root = Path(__file__).resolve().parent.parent.parent.parent.parent
        self.template_dir = root / "stacks" / "fastapi" / "core" / "cp_full_mfa"
        from midicoder.packs.cp_full_mfa.fastapi import FastAPIMFAEmitter
        self.emitter_cls = FastAPIMFAEmitter

    def test_emit_returns_files(self):
        emitter = self.emitter_cls(str(self.template_dir))
        ir = MFAIR(rules=[MFARule(rule_id="r1", method=MFAMethod.TOTP)])
        files = emitter.emit(ir, "/tmp/output")
        assert len(files) > 0
        assert all(f.path and f.content for f in files)

    def test_emit_template_count(self):
        emitter = self.emitter_cls(str(self.template_dir))
        ir = MFAIR(rules=[MFARule(rule_id="r1")])
        files = emitter.emit(ir, "/tmp/output")
        assert len(files) >= 3  # At least 3 templates

    def test_invalid_dir_raises_error(self):
        with pytest.raises(Exception):
            self.emitter_cls("/nonexistent/path")


class TestNestJSMFAEmitter:
    @pytest.fixture(autouse=True)
    def setup(self):
        import os
        root = Path(__file__).resolve().parent.parent.parent.parent.parent
        self.template_dir = root / "stacks" / "nestjs" / "core" / "cp_full_mfa"
        from midicoder.packs.cp_full_mfa.nestjs import NestJSMFAEmitter
        self.emitter_cls = NestJSMFAEmitter

    def test_emit_returns_files(self):
        emitter = self.emitter_cls(str(self.template_dir))
        ir = MFAIR(rules=[MFARule(rule_id="r1")])
        files = emitter.emit(ir, "/tmp/output")
        assert len(files) > 0

    def test_invalid_dir_raises_error(self):
        with pytest.raises(Exception):
            self.emitter_cls("/nonexistent/path")


class TestAngularMFAEmitter:
    @pytest.fixture(autouse=True)
    def setup(self):
        import os
        root = Path(__file__).resolve().parent.parent.parent.parent.parent
        self.template_dir = root / "stacks" / "angular" / "core" / "cp_full_mfa"
        from midicoder.packs.cp_full_mfa.angular import AngularMFAEmitter
        self.emitter_cls = AngularMFAEmitter

    def test_emit_returns_files(self):
        emitter = self.emitter_cls(str(self.template_dir))
        ir = MFAIR(rules=[MFARule(rule_id="r1")])
        files = emitter.emit(ir, "/tmp/output")
        assert len(files) > 0

    def test_emit_template_count(self):
        emitter = self.emitter_cls(str(self.template_dir))
        ir = MFAIR(rules=[MFARule(rule_id="r1")])
        files = emitter.emit(ir, "/tmp/output")
        assert len(files) >= 3

    def test_invalid_dir_raises_error(self):
        with pytest.raises(Exception):
            self.emitter_cls("/nonexistent/path")


class TestReactMFAEmitter:
    @pytest.fixture(autouse=True)
    def setup(self):
        import os
        root = Path(__file__).resolve().parent.parent.parent.parent.parent
        self.template_dir = root / "stacks" / "react" / "core" / "cp_full_mfa"
        from midicoder.packs.cp_full_mfa.react import ReactMFAEmitter
        self.emitter_cls = ReactMFAEmitter

    def test_emit_returns_files(self):
        emitter = self.emitter_cls(str(self.template_dir))
        ir = MFAIR(rules=[MFARule(rule_id="r1")])
        files = emitter.emit(ir, "/tmp/output")
        assert len(files) > 0

    def test_emit_with_context(self):
        emitter = self.emitter_cls(str(self.template_dir))
        ir = MFAIR(
            rules=[
                MFARule(rule_id="r1", method=MFAMethod.TOTP),
                MFARule(rule_id="r2", method=MFAMethod.WEBAUTHN_FIDO2),
            ]
        )
        files = emitter.emit(ir, "/tmp/output")
        for f in files:
            assert "totp" in f.content.lower() or "webauthn" in f.content.lower() or "mfa" in f.content.lower()

    def test_invalid_dir_raises_error(self):
        with pytest.raises(Exception):
            self.emitter_cls("/nonexistent/path")


class TestEmitterIntegration:
    def test_ir_data_flows_through_emitter(self):
        root = Path(__file__).resolve().parent.parent.parent.parent.parent
        template_dir = root / "stacks" / "fastapi" / "core" / "cp_full_mfa"
        from midicoder.packs.cp_full_mfa.fastapi import FastAPIMFAEmitter

        ir = MFAIR(
            rules=[MFARule(rule_id="test_rule", method=MFAMethod.TOTP, priority=MFAPriority.REQUIRED)],
            require_mfa=True,
            max_attempts=10,
            default_method=MFAMethod.TOTP,
        )
        emitter = FastAPIMFAEmitter(str(template_dir))
        files = emitter.emit(ir, "/tmp/output")
        assert len(files) > 0
