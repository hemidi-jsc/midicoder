"""
Tests cho Contracts Registry và Pack Emitter Router consistency (taxonomy-v2).

Kiểm tra:
- contracts/registry.py: ID_TO_INTERNAL (alias CP_ID_TO_INTERNAL) sync với taxonomy.yml
- contracts/registry.py: stack constants đúng convention
- pack_emitter_router.py: EMITTER_REGISTRY module/class tồn tại
- pack_emitter_router.py: PARSER_REGISTRY bao phủ tất cả parser_key
- Cross-consistency: internal_id trong registry khớp với EMITTER_REGISTRY module path

Taxonomy v2: 52 packs trong 6 tier (BASE, INFRA, CORE, BACKEND, FRONTEND, FULL).
IDs: B01, I01-I05, C01-C03, BE01-BE06, FE01-FE02, F01-F36.

Author: Midicoder Team
Version: 3.0.0 (taxonomy-v2)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from midicoder.contracts.registry import (
    ALL_STACKS,
    BACKEND_STACKS,
    CP_ID_TO_INTERNAL,
    FRONTEND_STACKS,
    ID_TO_INTERNAL,
    INFRA_STACK,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def taxonomy_path() -> Path:
    """Đường dẫn đến taxonomy.yml (taxonomy-v2)."""
    return Path(__file__).resolve().parent.parent.parent / "packs" / "taxonomy.yml"


@pytest.fixture
def taxonomy_data(taxonomy_path: Path) -> dict[str, Any]:
    """Load taxonomy.yml."""
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def core_pack_ids(taxonomy_data: dict[str, Any]) -> set[str]:
    """Lấy tất cả CP IDs từ taxonomy."""
    return {cp["id"] for cp in taxonomy_data.get("core_packs", [])}


@pytest.fixture
def taxonomy_cp_mapping(taxonomy_data: dict[str, Any]) -> dict[str, str]:
    """Lấy mapping CP_ID → internal_id từ taxonomy (chỉ có internal_id)."""
    return {
        cp["id"]: cp["internal_id"]
        for cp in taxonomy_data.get("core_packs", [])
        if cp.get("internal_id")
    }


# ============================================================================
# contracts/registry.py — Stack constants
# ============================================================================


class TestStackConstants:
    """Tests cho stack constants trong contracts/registry.py."""

    def test_backend_stacks_contains_expected(self):
        """BACKEND_STACKS chứa fastapi và nestjs."""
        assert "fastapi" in BACKEND_STACKS
        assert "nestjs" in BACKEND_STACKS
        assert "angular" not in BACKEND_STACKS
        assert "react" not in BACKEND_STACKS

    def test_frontend_stacks_contains_expected(self):
        """FRONTEND_STACKS chứa angular và react."""
        assert "angular" in FRONTEND_STACKS
        assert "react" in FRONTEND_STACKS
        assert "fastapi" not in FRONTEND_STACKS
        assert "nestjs" not in FRONTEND_STACKS

    def test_infra_stack_is_string(self):
        """INFRA_STACK là string, không phải set."""
        assert isinstance(INFRA_STACK, str)
        assert INFRA_STACK == "infrastructure"

    def test_all_stacks_is_union(self):
        """ALL_STACKS = BACKEND ∪ FRONTEND ∪ {INFRA}."""
        expected = BACKEND_STACKS | FRONTEND_STACKS | {INFRA_STACK}
        assert ALL_STACKS == expected
        assert len(ALL_STACKS) == len(BACKEND_STACKS) + len(FRONTEND_STACKS) + 1

    def test_no_overlap_between_backend_and_frontend(self):
        """BACKEND_STACKS và FRONTEND_STACKS không giao nhau."""
        assert BACKEND_STACKS & FRONTEND_STACKS == set()

    def test_infra_not_in_backend_or_frontend(self):
        """INFRA_STACK không nằm trong BACKEND hay FRONTEND."""
        assert INFRA_STACK not in BACKEND_STACKS
        assert INFRA_STACK not in FRONTEND_STACKS


# ============================================================================
# contracts/registry.py — CP_ID_TO_INTERNAL
# ============================================================================


class TestCPIDToInternal:
    """Tests cho CP_ID_TO_INTERNAL mapping."""

    def test_is_dict_of_strings(self):
        """CP_ID_TO_INTERNAL là dict[str, str]."""
        assert isinstance(CP_ID_TO_INTERNAL, dict)
        for k, v in CP_ID_TO_INTERNAL.items():
            assert isinstance(k, str), f"Key {k!r} không phải str"
            assert isinstance(v, str), f"Value {v!r} không phải str"

    def test_keys_are_cp_ids(self):
        """Tất cả keys là taxonomy-v2 IDs: B01, I01, C01, BE01, FE01, F01."""
        import re

        pattern = re.compile(r"^[BCFI]|BE|FE\d+$")
        valid_prefixes = {"B", "I", "C", "BE", "FE", "F"}
        for k in CP_ID_TO_INTERNAL:
            assert k[0] in {"B", "I", "C", "F"}, (
                f"Key {k!r} không bắt đầu bằng prefix hợp lệ (B/I/C/F)"
            )
            # Extract prefix: BE/FE → 2 chars, else 1 char
            if k.startswith("BE") or k.startswith("FE"):
                prefix = k[:2]
                suffix = k[2:]
            else:
                prefix = k[0]
                suffix = k[1:]
            assert prefix in valid_prefixes, f"Key {k!r} prefix {prefix!r} không hợp lệ"
            assert suffix.isdigit(), f"Key {k!r} phần số {suffix!r} không phải số"

    def test_values_are_snake_case_internal_ids(self):
        """Tất cả values là snake_case, có prefix cp_{tier}_ (taxonomy-v2)."""
        import re

        pattern = re.compile(r"^cp_(base|infra|core|backend|frontend|full)_[\w_]+$")
        for v in CP_ID_TO_INTERNAL.values():
            assert pattern.match(v), f"Value {v!r} không khớp pattern cp_{{tier}}_..."

    def test_no_duplicate_values(self):
        """Không có 2 CP ánh xạ cùng 1 internal_id."""
        values = list(CP_ID_TO_INTERNAL.values())
        assert len(values) == len(set(values)), "Có internal_id bị duplicate"

    def test_sync_with_taxonomy(self, taxonomy_cp_mapping: dict[str, str]):
        """CP_ID_TO_INTERNAL phải sync với internal_id trong taxonomy.yml (v2).

        Các CP có trong registry và cũng có trong taxonomy → mapping phải khớp.
        Registry có thể chưa chứa hết CP (taxonomy có 52 CP, registry chỉ có CP
        đã implement). Test không enforce taxonomy ⊆ registry.
        """
        registry_keys = set(CP_ID_TO_INTERNAL.keys())
        taxonomy_keys = set(taxonomy_cp_mapping.keys())

        # Giá trị mapping phải khớp cho các CP nằm trong cả 2 nơi
        mismatched = []
        for cp_id in registry_keys & taxonomy_keys:
            if CP_ID_TO_INTERNAL[cp_id] != taxonomy_cp_mapping[cp_id]:
                mismatched.append(
                    f"{cp_id}: registry={CP_ID_TO_INTERNAL[cp_id]!r}, "
                    f"taxonomy={taxonomy_cp_mapping[cp_id]!r}"
                )
        assert not mismatched, f"Các mapping không khớp: {mismatched}"

        # Các CP có internal_id trong taxonomy nhưng KHÔNG có trong registry
        # → chỉ warning, không fail (registry chỉ chứa CP đã implement)
        missing_in_registry = taxonomy_keys - registry_keys
        # Ghi nhận số lượng để dễ theo dõi drift
        assert len(missing_in_registry) <= 30, (
            f"Registry thiếu quá nhiều CP so với taxonomy: {len(missing_in_registry)} CP "
            f"({missing_in_registry}). Có thể taxonomy đã thêm nhiều CP mới nhưng registry chưa update."
        )

    def test_known_packs_present(self):
        """Các pack quan trọng (taxonomy-v2) phải có trong registry.

        Bỏ CP51/CP52/CP53 vì đã REMOVE (compiler internal).
        """
        essential = {"B01", "I01", "C01", "C02", "BE01", "BE02", "F01", "F02", "F08"}
        missing = essential - set(CP_ID_TO_INTERNAL.keys())
        assert not missing, f"Các pack quan trọng thiếu trong registry: {missing}"

    def test_known_internal_ids(self):
        """Kiểm tra các internal_id cụ thể (taxonomy-v2).

        Bỏ CP51/CP52/CP53 vì đã REMOVE.
        """
        assert CP_ID_TO_INTERNAL["B01"] == "cp_base_domain_model"
        assert CP_ID_TO_INTERNAL["C01"] == "cp_core_multi_tenant"
        assert CP_ID_TO_INTERNAL["F01"] == "cp_full_auth"
        assert CP_ID_TO_INTERNAL["C02"] == "cp_core_event_driven"
        assert CP_ID_TO_INTERNAL["I01"] == "cp_infra_iac"
        assert CP_ID_TO_INTERNAL["BE01"] == "cp_backend_database"
        assert CP_ID_TO_INTERNAL["F08"] == "cp_full_notification"

    def test_folder_exists_for_each_internal_id(self):
        """Mỗi internal_id phải tương ứng với folder tồn tại trong packs/."""
        packs_dir = Path(__file__).resolve().parent.parent.parent / "packs"
        missing_folders = []
        for internal_id in CP_ID_TO_INTERNAL.values():
            pack_dir = packs_dir / internal_id
            if not pack_dir.is_dir():
                missing_folders.append(internal_id)
        assert not missing_folders, (
            f"Các internal_id trong registry nhưng folder KHÔNG tồn tại: "
            f"{missing_folders}"
        )


# ============================================================================
# pack_emitter_router.py — EMITTER_REGISTRY
# ============================================================================


class TestEmitterRegistry:
    """Tests cho EMITTER_REGISTRY trong pack_emitter_router.py."""

    def setup_method(self):
        """Import EMITTER_REGISTRY và PARSER_REGISTRY (deferred)."""
        from midicoder.pipeline.pack_emitter_router import (
            EMITTER_REGISTRY,
            PARSER_REGISTRY,
        )
        self.emitter_registry = EMITTER_REGISTRY
        self.parser_registry = PARSER_REGISTRY

    def test_is_non_empty_dict(self):
        """EMITTER_REGISTRY không rỗng."""
        assert len(self.emitter_registry) > 0

    def test_values_are_tuples_of_three(self):
        """Mỗi value là tuple(module_path, class_name, parser_key)."""
        for key, value in self.emitter_registry.items():
            assert isinstance(value, tuple), f"{key}: value phải là tuple"
            assert len(value) == 3, f"{key}: tuple phải có 3 phần tử"
            module_path, class_name, parser_key = value
            assert isinstance(module_path, str), f"{key}: module_path phải là str"
            assert isinstance(class_name, str), f"{key}: class_name phải là str"
            assert parser_key is None or isinstance(parser_key, str), (
                f"{key}: parser_key phải là str hoặc None"
            )

    def test_keys_follow_convention(self):
        """Key convention: {cp_internal}.{capability}.{stack} hoặc {cp_internal}.{type} (2 segment).

        Ví dụ: "cp01.entity.fastapi" (3 segment) hoặc "cp07.docker" (2 segment).
        """
        import re

        pattern = re.compile(r"^cp\d{2}\.\w+(\.\w+)?$")
        for key in self.emitter_registry:
            assert pattern.match(key), f"Key {key!r} không khớp convention cpNN.capability[.stack]"

    def test_modules_exist(self):
        """Mỗi module_path trong EMITTER_REGISTRY phải import được."""
        for key, (module_path, class_name, parser_key) in self.emitter_registry.items():
            try:
                __import__(module_path)
            except ImportError as exc:
                pytest.fail(f"{key}: Không thể import {module_path!r}: {exc}")

    def test_classes_exist(self):
        """Mỗi class_name trong EMITTER_REGISTRY phải tồn tại trong module."""
        for key, (module_path, class_name, parser_key) in self.emitter_registry.items():
            mod = __import__(module_path, fromlist=[class_name])
            assert hasattr(mod, class_name), (
                f"{key}: Class {class_name!r} không tồn tại trong {module_path!r}"
            )

    def test_parser_keys_are_registered(self):
        """Tất cả parser_key non-Null trong EMITTER_REGISTRY phải có trong PARSER_REGISTRY."""
        used_parser_keys = {
            pk for _, (_, _, pk) in self.emitter_registry.items() if pk is not None
        }
        for pk in used_parser_keys:
            assert pk in self.parser_registry, (
                f"parser_key {pk!r} được dùng trong EMITTER_REGISTRY "
                f"nhưng không có trong PARSER_REGISTRY"
            )

    def test_emitter_classes_are_callable(self):
        """Mỗi emitter class phải là class (callable)."""
        for key, (module_path, class_name, parser_key) in self.emitter_registry.items():
            mod = __import__(module_path, fromlist=[class_name])
            cls = getattr(mod, class_name)
            assert callable(cls), f"{key}: {class_name!r} phải là callable"

    def test_emitter_keys_cover_registered_packs(self):
        """Các CP có internal_id trong registry và có folder, nên có ít nhất 1 emitter.

        Đây là test aspirational — fail cảnh báo khi pack mới nhưng chưa có emitter.
        """
        import importlib

        used_internal_ids = set()
        for key, (module_path, _, _) in self.emitter_registry.items():
            # Extract internal_id from module path
            # "midicoder.packs.cp_base_domain_model.entity_fastapi"
            parts = module_path.split(".")
            for i, p in enumerate(parts):
                if p in CP_ID_TO_INTERNAL.values():
                    used_internal_ids.add(p)
                    break

        # Các CP đã harden nên có emitter
        expected_harden = {"cp_base_domain_model", "cp_full_auth", "cp_core_event_driven",
                           "cp_infra_iac", "cp_backend_database", "cp_full_search"}
        missing_emitters = expected_harden - used_internal_ids
        assert not missing_emitters, (
            f"Các CP đã harden nhưng chưa có emitter trong EMITTER_REGISTRY: "
            f"{missing_emitters}"
        )


# ============================================================================
# Cross-consistency: CP_ID_TO_INTERNAL ↔ EMITTER_REGISTRY
# ============================================================================


class TestCrossConsistency:
    """Tests cross-consistency giữa registry và emitter router."""

    def setup_method(self):
        from midicoder.pipeline.pack_emitter_router import EMITTER_REGISTRY
        self.emitter_registry = EMITTER_REGISTRY

    def test_emitter_module_paths_use_internal_ids_from_registry(self):
        """Module path trong EMITTER_REGISTRY phải dùng internal_id từ CP_ID_TO_INTERNAL.

        Ví dụ: "midicoder.packs.cp_base_domain_model.entity_fastapi"
        → "cp_base_domain_model" phải là value trong CP_ID_TO_INTERNAL.
        """
        internal_values = set(CP_ID_TO_INTERNAL.values())
        mismatches = []

        for key, (module_path, _, _) in self.emitter_registry.items():
            parts = module_path.split(".")
            for p in parts:
                if p.startswith("cp") and "_" in p:
                    if p not in internal_values:
                        mismatches.append(f"{key}: '{p}' không có trong CP_ID_TO_INTERNAL values")

        assert not mismatches, f"Module path không khớp internal_id registry: {mismatches}"

    def test_file_contributions_loader_imports_from_registry(self):
        """file_contributions_loader phải import CP_ID_TO_INTERNAL từ contracts.registry,
        không tự define."""
        import midicoder.pipeline.file_contributions_loader as fcl_mod

        # Check that the module has CP_ID_TO_INTERNAL in its namespace
        assert hasattr(fcl_mod, "CP_ID_TO_INTERNAL"), (
            "file_contributions_loader không export CP_ID_TO_INTERNAL"
        )

        # Verify it's the same object as in contracts.registry
        from midicoder.contracts import registry as reg_mod
        assert fcl_mod.CP_ID_TO_INTERNAL is reg_mod.CP_ID_TO_INTERNAL, (
            "file_contributions_loader.CP_ID_TO_INTERNAL không phải là same object "
            "với contracts.registry.CP_ID_TO_INTERNAL — có thể đang tự define duplicate"
        )

    @pytest.mark.skip(reason="CP51 Blueprint đã REMOVE trong taxonomy-v2 — compiler internal")
    def test_cp51_resolver_imports_from_registry(self):
        """cp51_blueprint/resolver phải import CP_ID_TO_INTERNAL từ contracts.registry.

        SKIP: CP51 đã được REMOVE khỏi taxonomy-v2 (compiler internal).
        """
        import midicoder.packs.cp51_blueprint.resolver as resolver_mod

        # Source-level check: resolver.py should import from contracts.registry
        resolver_file = Path(resolver_mod.__file__).resolve()
        source = resolver_file.read_text(encoding="utf-8")
        assert "from midicoder.contracts.registry import" in source, (
            "cp51/resolver.py không import từ contracts.registry"
        )
        assert "CP_ID_TO_INTERNAL" in source, (
            "cp51/resolver.py không import CP_ID_TO_INTERNAL"
        )

    def test_no_duplicate_cp_id_mapping_in_codebase(self):
        """Không có file nào khác (ngoài contracts/registry.py) tự define
        CP_ID_TO_INTERNAL dict.

        Scan toàn bộ midicoder/ để tìm 'CP_ID_TO_INTERNAL =' (define, không phải import).
        """
        midicoder_root = Path(__file__).resolve().parent.parent
        offenders = []

        for py_file in midicoder_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            # Exclude chính file test này
            if py_file.name == "test_registry_and_emitter_consistency.py":
                continue
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            # Find lines that DEFINE CP_ID_TO_INTERNAL (not just import it)
            for line in content.split("\n"):
                stripped = line.strip()
                # Skip comments and imports
                if stripped.startswith("#") or stripped.startswith("from ") or stripped.startswith("import "):
                    continue
                # Check for definition pattern: CP_ID_TO_INTERNAL = { or CP_ID_TO_INTERNAL: Final
                if "CP_ID_TO_INTERNAL" in stripped and ("=" in stripped and "{" in stripped):
                    rel = py_file.relative_to(midicoder_root)
                    expected = midicoder_root / "contracts" / "registry.py"
                    if str(py_file) != str(expected):
                        offenders.append(f"{rel}: {stripped}")

        assert not offenders, (
            f"Các file tự define CP_ID_TO_INTERNAL (duplicate của contracts/registry.py): "
            f"{offenders}"
        )
