# coding: utf-8
"""
Test pack.yml sync với taxonomy.yml cho CP11 File Storage.

Kiểm tra:
- pack.yml tồn tại và hợp lệ (YAML)
- Các emitters được khai báo trong pack.yml có module thực tế
- Các error codes trong pack.yml khớp với errors.py
- Definitions trong pack.yml khớp với models
"""

from __future__ import annotations

import pathlib

import pytest
import yaml

PACK_YML = pathlib.Path(__file__).resolve().parent.parent.parent / "emitters" / "core" / "file_storage" / "pack.yml"
TAXONOMY_YML = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "industry" / "taxonomy.yml"


@pytest.fixture
def pack():
    """Load pack.yml."""
    assert PACK_YML.exists(), f"pack.yml không tồn tại tại {PACK_YML}"
    with open(PACK_YML, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def taxonomy():
    """Load taxonomy.yml."""
    assert TAXONOMY_YML.exists(), f"taxonomy.yml không tồn tại tại {TAXONOMY_YML}"
    with open(TAXONOMY_YML, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestPackStructure:
    """Kiểm tra cấu trúc pack.yml."""

    def test_pack_id(self, pack):
        assert pack["pack"]["id"] == "CP11"

    def test_pack_name(self, pack):
        assert "File Storage" in pack["pack"]["name"]

    def test_pack_phase(self, pack):
        assert pack["pack"]["phase"] == "P1"

    def test_pack_internal_id(self, pack):
        assert pack["pack"]["internal_id"] == "cp11-file-media"

    def test_pack_has_error_codes(self, pack):
        assert "MDC-CP11" in pack["pack"]["error_codes"]["prefix"]

    def test_pack_has_definitions(self, pack):
        assert pack["pack"]["definitions_count"] == 3

    def test_pack_has_obligations(self, pack):
        assert pack["pack"]["obligations_count"] == 1

    def test_pack_has_emitters(self, pack):
        emitters = pack["pack"]["emitters"]
        assert "fastapi" in emitters
        assert "nestjs" in emitters
        assert "angular" in emitters
        assert "react" in emitters


class TestPackEmittersExist:
    """Kiểm tra các emitters được khai báo có module thực tế."""

    def test_fastapi_emitter_exists(self, pack):
        mod_path = pack["pack"]["emitters"]["fastapi"]["module"]
        assert ":" in mod_path
        module_name, cls_name = mod_path.rsplit(":", 1)
        mod = __import__(module_name, fromlist=[cls_name])
        assert hasattr(mod, cls_name)

    def test_nestjs_emitter_exists(self, pack):
        mod_path = pack["pack"]["emitters"]["nestjs"]["module"]
        module_name, cls_name = mod_path.rsplit(":", 1)
        mod = __import__(module_name, fromlist=[cls_name])
        assert hasattr(mod, cls_name)

    def test_angular_emitter_exists(self, pack):
        mod_path = pack["pack"]["emitters"]["angular"]["module"]
        module_name, cls_name = mod_path.rsplit(":", 1)
        mod = __import__(module_name, fromlist=[cls_name])
        assert hasattr(mod, cls_name)

    def test_react_emitter_exists(self, pack):
        mod_path = pack["pack"]["emitters"]["react"]["module"]
        module_name, cls_name = mod_path.rsplit(":", 1)
        mod = __import__(module_name, fromlist=[cls_name])
        assert hasattr(mod, cls_name)


class TestPackTaxonomySync:
    """Kiểm tra pack.yml đồng bộ với taxonomy.yml."""

    def test_cp11_in_taxonomy(self, taxonomy):
        found = False
        for cp in taxonomy.get("core_packs", []):
            if cp.get("id") == "CP11":
                found = True
                assert "file" in cp.get("name", "").lower() or "storage" in cp.get("name", "").lower()
        assert found, "CP11 không tìm thấy trong taxonomy.yml"

    def test_error_codes_in_errors_py(self, pack):
        """Kiểm tra error codes prefix tồn tại trong errors.py."""
        from midicoder.errors import ErrorCode

        prefix = pack["pack"]["error_codes"]["prefix"]
        # Kiểm tra ít nhất 1 error code với prefix này tồn tại
        cp11_codes = [attr for attr in dir(ErrorCode) if attr.startswith("CP11_")]
        assert len(cp11_codes) >= 5, f"Chưa đủ CP11 error codes, tìm thấy {len(cp11_codes)}"

    def test_definitions_count_matches_models(self, pack):
        """Kiểm tra definitions_count khớp với số model classes."""
        from midicoder.emitters.core.file_storage.models import (
            StorageProfile,
            UploadPolicy,
            MediaTransform,
        )
        assert pack["pack"]["definitions_count"] == 3

    def test_capabilities_provided(self, pack):
        caps = pack["pack"]["capabilities_provided"]
        assert "file_upload" in caps
        assert "file_download" in caps
        assert "file_storage" in caps
        assert "media_transform" in caps
