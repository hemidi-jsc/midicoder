"""
Tests cho CP (Core Pack) Dependency Resolution.

Tuân thủ TDD, kiểm tra:
- Resolve transitive dependencies từ taxonomy.yml
- Validate dependency order (P0 → P1 → P2 → P3)
- Detect missing dependencies
- Validate P0 mandatory packs có dependencies đúng

Author: Midicoder Team
Version: 2.0.0 (updated for 53 CPs, dynamic phase lists)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def taxonomy_path() -> Path:
    """Đường dẫn đến taxonomy.yml."""
    return Path("industry/taxonomy.yml")


@pytest.fixture
def taxonomy(taxonomy_path: Path) -> dict[str, Any]:
    """Load taxonomy.yml."""
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def cp_dependency_map(taxonomy: dict[str, Any]) -> dict[str, list[str]]:
    """
    Tạo map từ CP ID → dependencies.

    Ví dụ:
        {
            "CP01": [],
            "CP02": ["CP01"],
            "CP03": ["CP01", "CP02"],
            ...
        }
    """
    cp_map: dict[str, list[str]] = {}
    for cp in taxonomy.get("core_packs", []):
        cp_map[cp["id"]] = cp.get("depends_on", [])
    return cp_map


@pytest.fixture
def cp_phase_map(taxonomy: dict[str, Any]) -> dict[str, str]:
    """
    Tạo map từ CP ID → phase.

    Ví dụ:
        {
            "CP01": "P0",
            "CP02": "P0",
            "CP03": "P0",
            ...
        }
    """
    phase_map: dict[str, str] = {}
    for cp in taxonomy.get("core_packs", []):
        phase_map[cp["id"]] = cp.get("phase", "P0")
    return phase_map


# ============================================================================
# Test CP Dependency Map
# ============================================================================


class TestCPDependencyMap:
    """Tests cho CP dependency map structure."""

    def test_cp01_no_dependencies(self, cp_dependency_map: dict[str, list[str]]) -> None:
        """Kiểm tra CP01 không có dependencies."""
        assert cp_dependency_map.get("CP01", []) == [], "CP01 không có dependencies"

    def test_cp02_depends_on_cp01(self, cp_dependency_map: dict[str, list[str]]) -> None:
        """Kiểm tra CP02 phụ thuộc CP01."""
        deps = cp_dependency_map.get("CP02", [])
        assert "CP01" in deps, "CP02 phải phụ thuộc CP01"

    def test_cp03_depends_on_cp01_cp02(self, cp_dependency_map: dict[str, list[str]]) -> None:
        """Kiểm tra CP03 phụ thuộc CP01 và CP02."""
        deps = cp_dependency_map.get("CP03", [])
        assert "CP01" in deps, "CP03 phải phụ thuộc CP01"
        assert "CP02" in deps, "CP03 phải phụ thuộc CP02"

    def test_cp04_depends_on_cp02_cp03(self, cp_dependency_map: dict[str, list[str]]) -> None:
        """Kiểm tra CP04 phụ thuộc CP02 và CP03."""
        deps = cp_dependency_map.get("CP04", [])
        assert "CP02" in deps, "CP04 phải phụ thuộc CP02"
        assert "CP03" in deps, "CP04 phải phụ thuộc CP03"

    def test_cp07_no_dependencies(self, cp_dependency_map: dict[str, list[str]]) -> None:
        """Kiểm tra CP07 không có dependencies."""
        assert cp_dependency_map.get("CP07", []) == [], "CP07 không có dependencies"

    def test_cp29_depends_only_on_cp01(self, cp_dependency_map: dict[str, list[str]]) -> None:
        """Kiểm tra CP29 chỉ phụ thuộc CP01 (Multi-Language Support Generator)."""
        deps = cp_dependency_map.get("CP29", [])
        assert len(deps) == 1, f"CP29 nên có 1 dep, tìm thấy {len(deps)}"
        assert deps == ["CP01"], f"CP29 phải chỉ phụ thuộc CP01, tìm thấy {deps}"

    def test_cp_count_matches(self, cp_dependency_map: dict[str, list[str]], taxonomy: dict[str, Any]) -> None:
        """Kiểm tra số lượng CP trong map khớp với taxonomy."""
        cp_count = len(taxonomy.get("core_packs", []))
        assert len(cp_dependency_map) == cp_count, f"Số CP trong map ({len(cp_dependency_map)}) không khớp taxonomy ({cp_count})"


# ============================================================================
# Test Transitive Dependency Resolution
# ============================================================================


class TestTransitiveDependencyResolution:
    """Tests cho transitive dependency resolution."""

    def test_resolve_cp02_transitive(
        self, cp_dependency_map: dict[str, list[str]]
    ) -> None:
        """
        Resolve transitive dependencies cho CP02.

        CP02 → [CP01]
        CP01 → []

        Result: [CP01, CP02]
        """
        cp_list = self._resolve_transitive("CP02", cp_dependency_map)
        assert set(cp_list) == {"CP01", "CP02"}, "CP02 transitive deps phải là [CP01, CP02]"

    def test_resolve_cp03_transitive(
        self, cp_dependency_map: dict[str, list[str]]
    ) -> None:
        """
        Resolve transitive dependencies cho CP03.

        CP03 → [CP01, CP02]
        CP02 → [CP01]
        CP01 → []

        Result: [CP01, CP02, CP03]
        """
        cp_list = self._resolve_transitive("CP03", cp_dependency_map)
        assert set(cp_list) == {"CP01", "CP02", "CP03"}, "CP03 transitive deps phải là [CP01, CP02, CP03]"

    def test_resolve_cp04_transitive(
        self, cp_dependency_map: dict[str, list[str]]
    ) -> None:
        """
        Resolve transitive dependencies cho CP04.

        CP04 → [CP02, CP03]
        CP03 → [CP01, CP02]
        CP02 → [CP01]
        CP01 → []

        Result: [CP01, CP02, CP03, CP04]
        """
        cp_list = self._resolve_transitive("CP04", cp_dependency_map)
        assert set(cp_list) == {"CP01", "CP02", "CP03", "CP04"}, "CP04 transitive deps phải là [CP01, CP02, CP03, CP04]"

    def test_resolve_p0_no_external_deps(
        self, cp_dependency_map: dict[str, list[str]], cp_phase_map: dict[str, str]
    ) -> None:
        """
        Resolve transitive dependencies cho tất cả P0 packs — chỉ trả về P0.
        """
        p0_packs = [cp_id for cp_id, phase in cp_phase_map.items() if phase == "P0"]
        all_resolved: set[str] = set()

        for cp_id in p0_packs:
            resolved = self._resolve_transitive(cp_id, cp_dependency_map)
            all_resolved.update(resolved)

        # Tất cả resolved phải là P0
        for resolved_cp in all_resolved:
            assert cp_phase_map.get(resolved_cp) == "P0", (
                f"P0 pack resolve ra {resolved_cp} ({cp_phase_map.get(resolved_cp)}) — không hợp lệ"
            )

    def test_resolve_cp29_transitive(
        self, cp_dependency_map: dict[str, list[str]]
    ) -> None:
        """
        Resolve transitive dependencies cho CP29 — chỉ CP01 + CP29.
        """
        cp_list = self._resolve_transitive("CP29", cp_dependency_map)
        assert set(cp_list) == {"CP01", "CP29"}, (
            f"CP29 transitive deps phải là [CP01, CP29], tìm thấy {cp_list}"
        )

    def _resolve_transitive(
        self, cp_id: str, cp_dependency_map: dict[str, list[str]]
    ) -> list[str]:
        """
        Helper: Resolve transitive dependencies cho một CP.

        Sử dụng DFS để traverse dependency graph.
        """
        resolved: set[str] = set()
        stack = [cp_id]

        while stack:
            current = stack.pop()
            if current in resolved:
                continue

            resolved.add(current)
            deps = cp_dependency_map.get(current, [])
            for dep in deps:
                if dep not in resolved:
                    stack.append(dep)

        # Sort theo CP ID để deterministic
        return sorted(resolved, key=lambda x: int(x[2:]))


# ============================================================================
# Test Dependency Order Validation
# ============================================================================


class TestDependencyOrderValidation:
    """Tests cho dependency order validation (P0 → P1 → P2 → P3 → P4).

    Phase lists được derive từ taxonomy, không hardcode.
    """

    def _get_packs_by_phase(
        self, cp_phase_map: dict[str, str], phase: str
    ) -> list[str]:
        """Lấy danh sách CPs theo phase."""
        return sorted([cp for cp, p in cp_phase_map.items() if p == phase])

    def test_p0_packs_have_no_higher_deps(
        self,
        cp_dependency_map: dict[str, list[str]],
        cp_phase_map: dict[str, str],
    ) -> None:
        """
        P0 packs không được phụ thuộc P1/P2/P3/P4 packs.
        """
        for cp_id, phase in cp_phase_map.items():
            if phase != "P0":
                continue
            deps = cp_dependency_map.get(cp_id, [])
            for dep in deps:
                dep_phase = cp_phase_map.get(dep, "P0")
                assert dep_phase == "P0", f"{cp_id} (P0) không được phụ thuộc {dep} ({dep_phase})"

    def test_phase_order_valid(self, cp_phase_map: dict[str, str]) -> None:
        """
        Kiểm tra phase values chỉ là P0-P4.
        """
        valid_phases = {"P0", "P1", "P2", "P3", "P4"}
        for cp_id, phase in cp_phase_map.items():
            assert phase in valid_phases, f"{cp_id} có phase không valid: {phase}"

    def test_no_phase_jump(self, cp_dependency_map: dict[str, list[str]], cp_phase_map: dict[str, str]) -> None:
        """
        Một pack không được phụ thuộc pack có phase cao hơn.

        Ví dụ: P1 không được phụ thuộc P2/P3/P4.
        """
        phase_num = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}

        for cp_id, deps in cp_dependency_map.items():
            cp_phase = cp_phase_map.get(cp_id, "P0")
            cp_level = phase_num.get(cp_phase, 0)
            for dep in deps:
                dep_phase = cp_phase_map.get(dep, "P0")
                dep_level = phase_num.get(dep_phase, 0)
                assert dep_level <= cp_level, (
                    f"{cp_id} ({cp_phase}, level {cp_level}) không được phụ thuộc "
                    f"{dep} ({dep_phase}, level {dep_level})"
                )

    def test_all_phases_have_packs(self, cp_phase_map: dict[str, str]) -> None:
        """
        Kiểm tra tất cả phase P0-P4 đều có ít nhất 1 pack.
        """
        phases_present = set(cp_phase_map.values())
        expected = {"P0", "P1", "P2", "P3", "P4"}
        assert expected.issubset(phases_present), (
            f"Thiếu phase trong taxonomy: {expected - phases_present}"
        )


# ============================================================================
# Test Missing Dependency Detection
# ============================================================================


class TestMissingDependencyDetection:
    """Tests cho missing dependency detection."""

    def test_missing_dependency_detected(
        self, cp_dependency_map: dict[str, list[str]]
    ) -> None:
        """
        Detect missing dependencies khi blueprint chỉ include CP03 nhưng không có CP01, CP02.

        Blueprint: ["CP03"]
        Missing: ["CP01", "CP02"]
        """
        blueprint_packs = {"CP03"}
        missing = self._find_missing_dependencies(blueprint_packs, cp_dependency_map)

        assert "CP01" in missing, "CP01 phải được detect là missing"
        assert "CP02" in missing, "CP02 phải được detect là missing"

    def test_no_missing_for_complete_set(
        self, cp_dependency_map: dict[str, list[str]]
    ) -> None:
        """
        Không có missing dependencies khi include đầy đủ.

        Blueprint: ["CP01", "CP02", "CP03"]
        Missing: set()
        """
        blueprint_packs = {"CP01", "CP02", "CP03"}
        missing = self._find_missing_dependencies(blueprint_packs, cp_dependency_map)

        assert missing == set(), f"Không nên có missing deps, tìm thấy: {missing}"

    def test_missing_in_transitive_chain(
        self, cp_dependency_map: dict[str, list[str]]
    ) -> None:
        """
        Detect missing dependencies trong transitive chain.

        Blueprint: ["CP04"]
        CP04 → [CP02, CP03]
        CP03 → [CP01, CP02]
        CP02 → [CP01]

        Missing: ["CP01", "CP02", "CP03"]
        """
        blueprint_packs = {"CP04"}
        missing = self._find_missing_dependencies(blueprint_packs, cp_dependency_map)

        assert "CP01" in missing, "CP01 phải được detect là missing"
        assert "CP02" in missing, "CP02 phải được detect là missing"
        assert "CP03" in missing, "CP03 phải được detect là missing"

    def _find_missing_dependencies(
        self, blueprint_packs: set[str], cp_dependency_map: dict[str, list[str]]
    ) -> set[str]:
        """
        Helper: Tìm missing dependencies cho một set của blueprint packs.
        """
        all_required: set[str] = set()
        stack = list(blueprint_packs)

        while stack:
            cp_id = stack.pop()
            if cp_id in all_required:
                continue

            all_required.add(cp_id)
            deps = cp_dependency_map.get(cp_id, [])
            for dep in deps:
                if dep not in all_required:
                    stack.append(dep)

        # Missing = all_required - blueprint_packs
        return all_required - blueprint_packs


# ============================================================================
# Test Dependency Resolution Integration
# ============================================================================


class TestDependencyResolutionIntegration:
    """Tests cho dependency resolution integration với taxonomy."""

    def test_all_cp_dependencies_exist(
        self,
        taxonomy: dict[str, Any],
        cp_dependency_map: dict[str, list[str]],
    ) -> None:
        """
        Tất cả dependencies trong taxonomy đều phải tồn tại.
        """
        all_cp_ids = {cp["id"] for cp in taxonomy.get("core_packs", [])}

        for cp_id, deps in cp_dependency_map.items():
            for dep in deps:
                assert dep in all_cp_ids, f"{cp_id} phụ thuộc {dep} không tồn tại trong taxonomy"

    def test_no_circular_dependencies(
        self, cp_dependency_map: dict[str, list[str]]
    ) -> None:
        """
        Không có circular dependencies trong CP graph.
        """
        # DFS với visited và recursion stack
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def has_cycle(cp_id: str) -> bool:
            visited.add(cp_id)
            rec_stack.add(cp_id)

            for dep in cp_dependency_map.get(cp_id, []):
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(cp_id)
            return False

        for cp_id in cp_dependency_map:
            if cp_id not in visited:
                assert not has_cycle(cp_id), f"Circular dependency detected từ {cp_id}"

    def test_p0_mandatory_packs_are_resolved(
        self,
        cp_dependency_map: dict[str, list[str]],
        cp_phase_map: dict[str, str],
    ) -> None:
        """
        P0 mandatory packs (CP01-CP04, CP07) đều được resolve đúng.
        """
        p0_mandatory = {"CP01", "CP02", "CP03", "CP04", "CP07"}

        for cp_id in p0_mandatory:
            assert cp_id in cp_dependency_map, f"{cp_id} phải có trong dependency map"
            assert cp_phase_map.get(cp_id) == "P0", f"{cp_id} phải là P0"
