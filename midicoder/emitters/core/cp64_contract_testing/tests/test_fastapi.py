"""
Tests cho CP64 FastAPI Contract Emitter.

Unit tests cho:
- FastAPIContractEmitter init (requires valid stack_dir)
- GeneratedFile dataclass
- emit returns files with correct structure

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from midicoder.emitters.core.cp64_contract_testing.models import (
    ConsumerSpec,
    Interaction,
    PactBrokerConfig,
    ProviderVerifier,
    RequestMatch,
    ResponseStub,
)
from midicoder.emitters.core.cp64_contract_testing.parser import ContractIR
from midicoder.emitters.core.cp64_contract_testing.fastapi import (
    FastAPIContractEmitter,
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
# Test FastAPIContractEmitter
# ===========================================================================


class TestFastAPIContractEmitter:
    """Tests cho FastAPIContractEmitter."""

    @pytest.fixture
    def contract_ir(self) -> ContractIR:
        """ContractIR fixture với basic consumer spec."""
        return ContractIR(
            consumer_specs=[
                ConsumerSpec(
                    id="test_consumer",
                    consumer_name="WebApp",
                    provider_name="API",
                    interactions=[
                        Interaction(
                            id="i1",
                            description="GET test",
                            request=RequestMatch(method="GET", path="/test"),
                            response=ResponseStub(status=200, body={"ok": True}),
                        )
                    ],
                )
            ],
            provider_verifiers=[
                ProviderVerifier(
                    id="pv1",
                    provider_name="API",
                    pact_broker_url="https://b.com",
                )
            ],
            pact_broker_config=PactBrokerConfig(
                id="b1",
                url="https://b.com",
                auto_publish=True,
            ),
            enable_auto_publish=True,
        )

    @pytest.fixture
    def stack_dir(self) -> Path:
        """Tạo template directory với mock templates."""
        tmp = Path(tempfile.mkdtemp())
        template_dir = tmp / "cp64_contract_testing"
        template_dir.mkdir()
        # Tạo mock templates
        for name in [
            "contract_service.py.jinja2",
            "pact_consumer_test.py.jinja2",
            "pact_provider_verifier.py.jinja2",
            "contract_router.py.jinja2",
        ]:
            (template_dir / name).write_text("{{ spec_count }} files from cp64")
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
            FastAPIContractEmitter(Path("/nonexistent/path"))

    def test_init_creates_jinja_env(self, stack_dir: Path):
        """Test emitter init tạo Jinja2 environment."""
        emitter = FastAPIContractEmitter(stack_dir)
        assert emitter.env is not None
        assert emitter.template_dir == stack_dir / "cp64_contract_testing"

    def test_emit_returns_generated_files(self, contract_ir: ContractIR, stack_dir: Path, output_dir: Path):
        """Test emit trả về danh sách GeneratedFile."""
        emitter = FastAPIContractEmitter(stack_dir)
        files = emitter.emit(contract_ir, output_dir)
        assert isinstance(files, list)
        assert len(files) == 4
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_file_paths(self, contract_ir: ContractIR, stack_dir: Path, output_dir: Path):
        """Test emit tạo đúng file paths."""
        emitter = FastAPIContractEmitter(stack_dir)
        files = emitter.emit(contract_ir, output_dir)
        paths = [f.path for f in files]
        assert "app/services/contract_service.py" in paths
        assert "tests/contract/pact_consumer_test.py" in paths
        assert "tests/contract/pact_provider_verifier.py" in paths
        assert "app/api/contract_router.py" in paths

    def test_emit_content_not_empty(self, contract_ir: ContractIR, stack_dir: Path, output_dir: Path):
        """Test emit tạo nội dung không rỗng."""
        emitter = FastAPIContractEmitter(stack_dir)
        files = emitter.emit(contract_ir, output_dir)
        for f in files:
            assert len(f.content) > 0

    def test_emit_with_no_templates(self, contract_ir: ContractIR, stack_dir: Path, output_dir: Path):
        """Test emit khi không có templates (empty template dir)."""
        # Xóa tất cả templates
        for f in (stack_dir / "cp64_contract_testing").iterdir():
            f.unlink()
        emitter = FastAPIContractEmitter(stack_dir)
        files = emitter.emit(contract_ir, output_dir)
        assert files == []

    def test_emit_context_has_spec_count(self, contract_ir: ContractIR, stack_dir: Path, output_dir: Path):
        """Test emit context chứa spec_count."""
        emitter = FastAPIContractEmitter(stack_dir)
        files = emitter.emit(contract_ir, output_dir)
        # mock templates render spec_count
        for f in files:
            assert "1" in f.content  # spec_count = 1

    def test_emit_multiple_consumer_specs(self, stack_dir: Path, output_dir: Path):
        """Test emit với nhiều consumer specs."""
        ir = ContractIR(
            consumer_specs=[
                ConsumerSpec(id="a", consumer_name="A", provider_name="P"),
                ConsumerSpec(id="b", consumer_name="B", provider_name="P"),
                ConsumerSpec(id="c", consumer_name="C", provider_name="P"),
            ]
        )
        emitter = FastAPIContractEmitter(stack_dir)
        files = emitter.emit(ir, output_dir)
        assert len(files) == 4
        # content chứa spec_count = 3
        for f in files:
            assert "3" in f.content

    def test_emit_minimal_ir(self, stack_dir: Path, output_dir: Path):
        """Test emit với ContractIR tối thiểu."""
        ir = ContractIR()
        emitter = FastAPIContractEmitter(stack_dir)
        files = emitter.emit(ir, output_dir)
        assert len(files) == 4

    def test_emit_with_broker_config(self, stack_dir: Path, output_dir: Path):
        """Test emit với Pact Broker config."""
        ir = ContractIR(
            consumer_specs=[
                ConsumerSpec(id="s1", consumer_name="C", provider_name="P")
            ],
            pact_broker_config=PactBrokerConfig(id="b1", url="https://b.com"),
            enable_auto_publish=True,
        )
        emitter = FastAPIContractEmitter(stack_dir)
        files = emitter.emit(ir, output_dir)
        assert len(files) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
