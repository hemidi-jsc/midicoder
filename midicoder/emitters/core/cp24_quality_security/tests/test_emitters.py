# coding: utf-8
"""
Unit tests cho 4 stack emitters của CP24.

Kiểm tra:
- FastAPIQualityEmitter generate đúng files
- NestJSQualityEmitter generate đúng files
- AngularQualityEmitter generate đúng files
- ReactQualityEmitter generate đúng files
- Template rendering hoạt động đúng

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.emitters.core.cp24_quality_security.models import (
    FormatterType,
    LinterType,
    QualityCollection,
    QualityGateConfig,
    QualityProfile,
    SecurityScanConfig,
    SecurityTool,
    SeverityLevel,
    StackType,
)
from midicoder.emitters.core.cp24_quality_security.fastapi import FastAPIQualityEmitter
from midicoder.emitters.core.cp24_quality_security.nestjs import NestJSQualityEmitter
from midicoder.emitters.core.cp24_quality_security.angular import AngularQualityEmitter
from midicoder.emitters.core.cp24_quality_security.react import ReactQualityEmitter


def _make_collection() -> QualityCollection:
    """Tạo QualityCollection mẫu cho test."""
    c = QualityCollection()

    # FastAPI profile
    c.add_profile(QualityProfile(
        name="strict",
        stack=StackType.FASTAPI,
        linter=LinterType.RUFF,
        formatter=FormatterType.BLACK,
        min_score=90,
        exclude=["tests/", "venv/"],
    ))
    c.add_security_config(SecurityScanConfig(
        stack=StackType.FASTAPI,
        tools=[SecurityTool.BANDIT, SecurityTool.SAFETY],
        fail_on_severity=SeverityLevel.HIGH,
    ))

    # NestJS profile
    c.add_profile(QualityProfile(
        name="standard",
        stack=StackType.NESTJS,
        linter=LinterType.ESLINT,
        formatter=FormatterType.PRETTIER,
    ))
    c.add_security_config(SecurityScanConfig(
        stack=StackType.NESTJS,
        tools=[SecurityTool.NPM_AUDIT, SecurityTool.ESLINT_SECURITY],
    ))

    # Angular profile
    c.add_profile(QualityProfile(
        name="standard",
        stack=StackType.ANGULAR,
        linter=LinterType.ESLINT,
        formatter=FormatterType.PRETTIER,
    ))
    c.add_security_config(SecurityScanConfig(
        stack=StackType.ANGULAR,
        tools=[SecurityTool.ESLINT_SECURITY, SecurityTool.LOCKFILE_LINT],
    ))

    # React profile
    c.add_profile(QualityProfile(
        name="standard",
        stack=StackType.REACT,
        linter=LinterType.ESLINT,
        formatter=FormatterType.PRETTIER,
    ))
    c.add_security_config(SecurityScanConfig(
        stack=StackType.REACT,
        tools=[SecurityTool.ESLINT_SECURITY, SecurityTool.LOCKFILE_LINT],
    ))

    # Gate config
    c.gate_config = QualityGateConfig(
        enabled=True,
        block_on_fail=True,
        min_coverage=80,
    )

    return c


class TestFastAPIQualityEmitter:
    """Test cho FastAPIQualityEmitter."""

    def test_init(self) -> None:
        """Kiểm tra khởi tạo emitter."""
        emitter = FastAPIQualityEmitter(stack_dir=".")
        assert emitter is not None

    def test_generate_returns_files(self) -> None:
        """Kiểm tra generate trả về danh sách files."""
        emitter = FastAPIQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        assert isinstance(results, list)
        assert len(results) > 0
        # Mỗi file có path và content
        for f in results:
            assert "path" in f
            assert "content" in f
            assert isinstance(f["path"], str)
            assert isinstance(f["content"], str)

    def test_generate_has_quality_gate_script(self) -> None:
        """Kiểm tra generate có quality gate script."""
        emitter = FastAPIQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        paths = [f["path"] for f in results]
        assert any("quality_gate" in p for p in paths)

    def test_generate_has_bandit_config(self) -> None:
        """Kiểm tra generate có bandit config."""
        emitter = FastAPIQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        paths = [f["path"] for f in results]
        assert any("bandit" in p for p in paths)

    def test_generate_content_not_empty(self) -> None:
        """Kiểm tra content không rỗng."""
        emitter = FastAPIQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        for f in results:
            assert len(f["content"].strip()) > 0

    def test_generate_empty_collection(self) -> None:
        """Kiểm tra generate với collection rỗng trả về các file mặc định."""
        emitter = FastAPIQualityEmitter(stack_dir=".")
        collection = QualityCollection()
        results = emitter.generate(collection)
        # Với collection rỗng, profile và security_config là None
        # nhưng quality_gate vẫn được sinh với giá trị mặc định
        assert isinstance(results, list)
        paths = [f["path"] for f in results]
        assert any("quality_gate" in p for p in paths)

    def test_generate_pyproject_quality_none_profile(self) -> None:
        """Kiểm tra _generate_pyproject_quality với profile=None."""
        emitter = FastAPIQualityEmitter(stack_dir=".")
        result = emitter._generate_pyproject_quality(None)
        assert result == []

    def test_generate_bandit_config_none_security(self) -> None:
        """Kiểm tra _generate_bandit_config với security_config=None."""
        emitter = FastAPIQualityEmitter(stack_dir=".")
        result = emitter._generate_bandit_config(None)
        assert result == []

    def test_generate_safety_policy_none_security(self) -> None:
        """Kiểm tra _generate_safety_policy với security_config=None."""
        emitter = FastAPIQualityEmitter(stack_dir=".")
        result = emitter._generate_safety_policy(None)
        assert result == []

    def test_generate_flake8_config_none_profile(self) -> None:
        """Kiểm tra _generate_flake8_config với profile=None."""
        emitter = FastAPIQualityEmitter(stack_dir=".")
        result = emitter._generate_flake8_config(None)
        assert result == []

    def test_generate_isort_config_none_profile(self) -> None:
        """Kiểm tra _generate_isort_config với profile=None."""
        emitter = FastAPIQualityEmitter(stack_dir=".")
        result = emitter._generate_isort_config(None)
        assert result == []

    def test_generate_quality_gate_with_none_args(self) -> None:
        """Kiểm tra _generate_quality_gate với cả hai arg là None."""
        emitter = FastAPIQualityEmitter(stack_dir=".")
        result = emitter._generate_quality_gate(None, None)
        # Vẫn sinh ra file mặc định (template dùng default values)
        assert isinstance(result, list)
        assert len(result) == 1
        assert "quality_gate" in result[0]["path"]


class TestNestJSQualityEmitter:
    """Test cho NestJSQualityEmitter."""

    def test_init(self) -> None:
        """Kiểm tra khởi tạo emitter."""
        emitter = NestJSQualityEmitter(stack_dir=".")
        assert emitter is not None

    def test_generate_returns_files(self) -> None:
        """Kiểm tra generate trả về danh sách files."""
        emitter = NestJSQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        assert isinstance(results, list)
        assert len(results) > 0
        for f in results:
            assert "path" in f
            assert "content" in f

    def test_generate_has_eslintrc(self) -> None:
        """Kiểm tra generate có eslintrc."""
        emitter = NestJSQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        paths = [f["path"] for f in results]
        assert any("eslintrc" in p for p in paths)

    def test_generate_has_prettierrc(self) -> None:
        """Kiểm tra generate có prettierrc."""
        emitter = NestJSQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        paths = [f["path"] for f in results]
        assert any("prettier" in p for p in paths)


class TestAngularQualityEmitter:
    """Test cho AngularQualityEmitter."""

    def test_init(self) -> None:
        """Kiểm tra khởi tạo emitter."""
        emitter = AngularQualityEmitter(stack_dir=".")
        assert emitter is not None

    def test_generate_returns_files(self) -> None:
        """Kiểm tra generate trả về danh sách files."""
        emitter = AngularQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        assert isinstance(results, list)
        assert len(results) > 0
        for f in results:
            assert "path" in f
            assert "content" in f

    def test_generate_has_editorconfig(self) -> None:
        """Kiểm tra generate có editorconfig."""
        emitter = AngularQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        paths = [f["path"] for f in results]
        assert any("editorconfig" in p for p in paths)

    def test_generate_has_lockfile_lint(self) -> None:
        """Kiểm tra generate có lockfile-lint config."""
        emitter = AngularQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        paths = [f["path"] for f in results]
        assert any("lockfile" in p for p in paths)


class TestReactQualityEmitter:
    """Test cho ReactQualityEmitter."""

    def test_init(self) -> None:
        """Kiểm tra khởi tạo emitter."""
        emitter = ReactQualityEmitter(stack_dir=".")
        assert emitter is not None

    def test_generate_returns_files(self) -> None:
        """Kiểm tra generate trả về danh sách files."""
        emitter = ReactQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        assert isinstance(results, list)
        assert len(results) > 0
        for f in results:
            assert "path" in f
            assert "content" in f

    def test_generate_has_eslintrc(self) -> None:
        """Kiểm tra generate có eslintrc."""
        emitter = ReactQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        paths = [f["path"] for f in results]
        assert any("eslintrc" in p for p in paths)

    def test_generate_has_editorconfig(self) -> None:
        """Kiểm tra generate có editorconfig."""
        emitter = ReactQualityEmitter(stack_dir=".")
        collection = _make_collection()
        results = emitter.generate(collection)
        paths = [f["path"] for f in results]
        assert any("editorconfig" in p for p in paths)

    def test_generate_empty_collection(self) -> None:
        """Kiểm tra generate với collection rỗng."""
        emitter = ReactQualityEmitter(stack_dir=".")
        collection = QualityCollection()
        results = emitter.generate(collection)
        assert isinstance(results, list)
        # Với collection rỗng, sinh ra file mặc định
        paths = [f["path"] for f in results]
        assert any("eslintrc" in p for p in paths)


class TestNestJSEmptyCollection:
    """Test NestJS emitter với collection rỗng."""

    def test_generate_empty_collection(self) -> None:
        """Kiểm tra NestJS generate với collection rỗng."""
        emitter = NestJSQualityEmitter(stack_dir=".")
        collection = QualityCollection()
        results = emitter.generate(collection)
        assert isinstance(results, list)
        paths = [f["path"] for f in results]
        assert any("eslintrc" in p for p in paths)

    def test_generate_eslintrc_with_empty_context(self) -> None:
        """Kiểm tra _generate_eslintrc với context rỗng."""
        emitter = NestJSQualityEmitter(stack_dir=".")
        result = emitter._generate_eslintrc({})
        assert isinstance(result, list)
        assert len(result) == 1
        assert "eslintrc" in result[0]["path"]

    def test_generate_quality_gate_with_empty_context(self) -> None:
        """Kiểm tra _generate_quality_gate với context rỗng."""
        emitter = NestJSQualityEmitter(stack_dir=".")
        result = emitter._generate_quality_gate({})
        assert isinstance(result, list)
        assert len(result) == 1


class TestAngularEmptyCollection:
    """Test Angular emitter với collection rỗng."""

    def test_generate_empty_collection(self) -> None:
        """Kiểm tra Angular generate với collection rỗng."""
        emitter = AngularQualityEmitter(stack_dir=".")
        collection = QualityCollection()
        results = emitter.generate(collection)
        assert isinstance(results, list)
        paths = [f["path"] for f in results]
        assert any("eslintrc" in p for p in paths)

    def test_render_file_with_valid_template(self) -> None:
        """Kiểm tra _render_file với template hợp lệ."""
        emitter = AngularQualityEmitter(stack_dir=".")
        result = emitter._render_file("eslintrc.json.jinja2", {})
        assert isinstance(result, dict)
        assert "path" in result
        assert "content" in result


class TestReactEmptyCollection:
    """Test React emitter với collection rỗng."""

    def test_generate_eslintrc_with_empty_collection(self) -> None:
        """Kiểm tra _generate_eslintrc với collection rỗng."""
        emitter = ReactQualityEmitter(stack_dir=".")
        result = emitter._generate_eslintrc(QualityCollection())
        assert isinstance(result, list)
        assert len(result) == 1

    def test_generate_quality_gate_with_empty_collection(self) -> None:
        """Kiểm tra _generate_quality_gate với collection rỗng."""
        emitter = ReactQualityEmitter(stack_dir=".")
        result = emitter._generate_quality_gate(QualityCollection())
        assert isinstance(result, list)
        assert len(result) == 1
