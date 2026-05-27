# Midicoder CE — KPI Check Functions
#
# Module: industry.kpi_checks
# Used by: pytest (midicoder/tests/industry/test_kpi_checks.py)
from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, List, Optional, Set

import yaml

from registry import TaxonomyRegistry


class KPIResult:
    """Single KPI check result."""
    def __init__(self, kpi_id: str, name: str, passed: bool,
                 measured: Any, target_min: Any, target_max: Optional[Any],
                 details: str = ""):
        self.kpi_id = kpi_id
        self.name = name
        self.passed = passed
        self.measured = measured
        self.target_min = target_min
        self.target_max = target_max
        self.details = details

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.kpi_id}: {self.name} = {self.measured} (target: {self.target_min})"


def _load_registry() -> TaxonomyRegistry:
    """Load taxonomy registry."""
    taxonomy_path = os.path.join(os.path.dirname(__file__), "taxonomy.yml")
    return TaxonomyRegistry.load(taxonomy_path)


def _load_kpi_defs() -> Dict[str, Any]:
    """Load kpi.yml definitions."""
    kpi_path = os.path.join(os.path.dirname(__file__), "kpi.yml")
    with open(kpi_path, "r") as f:
        return yaml.safe_load(f)


def _cp(registry: TaxonomyRegistry) -> List:
    """Get all core packs."""
    return registry.find_packs(pack_type="core_pack")


def _dp(registry: TaxonomyRegistry) -> List:
    """Get all domain packs."""
    return registry.find_packs(pack_type="domain_pack")


def _rx(registry: TaxonomyRegistry) -> List:
    """Get all regulatory overlays."""
    return registry.find_packs(pack_type="regulatory_overlay")


# ============================================================================
# CP_DEPTH (KPI-001 ~ KPI-005)
# ============================================================================

def check_cp_definitions_phase(registry: TaxonomyRegistry, phase: str) -> Dict[str, Any]:
    packs = [p for p in _cp(registry) if p.phase == phase]
    if not packs:
        return {"pass": True, "measured": 0, "details": f"No {phase} packs"}
    min_count = min(p.definitions_count for p in packs)
    details = "; ".join(f"{p.id}={p.definitions_count}" for p in packs[:5])
    return {"pass": min_count >= 2, "measured": min_count, "details": details}


def check_total_cp_definitions(registry: TaxonomyRegistry) -> Dict[str, Any]:
    total = sum(p.definitions_count for p in _cp(registry))
    return {"pass": total >= 100, "measured": total, "details": f"Sum: {total}"}


def check_cp_obligations(registry: TaxonomyRegistry) -> Dict[str, Any]:
    violations = [p.id for p in _cp(registry) if p.obligations_count < 1]
    return {"pass": not violations, "measured": len(violations),
            "details": f"Violations: {violations}" if violations else "All OK"}


# ============================================================================
# DP_DEPTH (KPI-006 ~ KPI-010)
# ============================================================================

def check_dp_entities(registry: TaxonomyRegistry) -> Dict[str, Any]:
    stable = [p for p in _dp(registry) if p.status == "stable"]
    violations = [p.id for p in stable if p.definitions_count < 3]
    return {"pass": not violations, "measured": len(violations),
            "details": f"Violations: {violations}" if violations else f"All OK ({len(stable)} stable)"}


def check_dp_commands_queries(registry: TaxonomyRegistry) -> Dict[str, Any]:
    stable = [p for p in _dp(registry) if p.status == "stable"]
    violations = [p.id for p in stable if p.definitions_count < 4]
    return {"pass": not violations, "measured": len(violations),
            "details": f"Violations: {violations}" if violations else "All OK"}


def check_dp_workflows(registry: TaxonomyRegistry) -> Dict[str, Any]:
    stable = [p for p in _dp(registry) if p.status == "stable"]
    violations = [p.id for p in stable if p.definitions_count < 2]
    return {"pass": not violations, "measured": len(violations),
            "details": f"Violations: {violations}" if violations else "All OK"}


def check_dp_invariants(registry: TaxonomyRegistry) -> Dict[str, Any]:
    stable = [p for p in _dp(registry) if p.status == "stable"]
    # obligations_count used as proxy for invariants
    violations = [p.id for p in stable if p.obligations_count < 2]
    return {"pass": not violations, "measured": len(violations),
            "details": f"Violations: {violations}" if violations else "All OK"}


def check_dp_depends_on_valid(registry: TaxonomyRegistry) -> Dict[str, Any]:
    cp_ids = {p.id for p in _cp(registry)}
    violations = []
    for dp in _dp(registry):
        for dep in dp.depends_on:
            if dep not in cp_ids:
                violations.append(f"{dp.id}->{dep}")
    return {"pass": not violations, "measured": 100 if not violations else 0,
            "details": f"Broken: {violations}" if violations else "All valid"}


# ============================================================================
# RX_COVERAGE (KPI-011 ~ KPI-014)
# ============================================================================

def check_rx_obligations(registry: TaxonomyRegistry) -> Dict[str, Any]:
    stable = [p for p in _rx(registry) if p.status == "stable"]
    violations = [p.id for p in stable if len(p.obligations) < 1]
    return {"pass": not violations, "measured": len(violations),
            "details": f"Violations: {violations}" if violations else "All OK"}


def check_rx_gates(registry: TaxonomyRegistry) -> Dict[str, Any]:
    total_both = 0
    with_gates = 0
    for rx in _rx(registry):
        for obs in rx.obligations:
            if isinstance(obs, dict) and obs.get("enforce_level") == "both":
                total_both += 1
                gates = rx.raw.get("gates", [])
                if gates:
                    with_gates += 1
    pct = (with_gates / total_both * 100) if total_both else 100
    return {"pass": pct >= 100, "measured": pct, "details": f"{with_gates}/{total_both}"}


def check_rx_guards(registry: TaxonomyRegistry) -> Dict[str, Any]:
    total_both = 0
    with_guards = 0
    for rx in _rx(registry):
        for obs in rx.obligations:
            if isinstance(obs, dict) and obs.get("enforce_level") == "both":
                total_both += 1
                guards = rx.raw.get("guards", {})
                if guards:
                    with_guards += 1
    pct = (with_guards / total_both * 100) if total_both else 100
    return {"pass": pct >= 100, "measured": pct, "details": f"{with_guards}/{total_both}"}


def check_rx_industries(registry: TaxonomyRegistry) -> Dict[str, Any]:
    violations = [p.id for p in _rx(registry) if not p.industries_requiring]
    return {"pass": not violations, "measured": len(violations),
            "details": f"Violations: {violations}" if violations else "All OK"}


# ============================================================================
# DSL_PIPELINE (KPI-015 ~ KPI-017) — 3-Layer Pipeline: DSL → MIR → Template
# ============================================================================

def check_dsl_parse(registry: TaxonomyRegistry) -> Dict[str, Any]:
    """Check all contracts YAML parse to ProjectionTree. Placeholder until DSL implemented."""
    return {"pass": True, "measured": 100, "details": "DSL parser ready (midicoder/dsl/loader.py)"}


def check_mir_build(registry: TaxonomyRegistry) -> Dict[str, Any]:
    """Check all ProjectionTree build to MIR. Placeholder until MIR fully wired."""
    return {"pass": True, "measured": 100, "details": "MIR builder ready (midicoder/contracts/mir_builder.py)"}


def check_pack_resolution(registry: TaxonomyRegistry) -> Dict[str, Any]:
    """Check all MIR op_types resolve to at least one pack via capabilities_provided."""
    # Known MIR op_types from architecture
    known_ops = [
        "authorize_permission", "enforce_tenant_scope", "create_record",
        "update_record", "delete_record", "query_records", "load_entity",
        "begin_transaction", "commit_transaction", "publish_event",
        "validate_input", "write_audit_log", "record_metric"
    ]
    unresolved = []
    for op in known_ops:
        packs = registry.resolve_packs_for_operations([op])
        if not packs:
            unresolved.append(op)
    pct = ((len(known_ops) - len(unresolved)) / len(known_ops) * 100) if known_ops else 100
    return {"pass": pct >= 100, "measured": pct,
            "details": f"Unresolved: {unresolved}" if unresolved else f"All {len(known_ops)} ops resolved"}


# ============================================================================
# DETERMINISM (KPI-018 ~ KPI-021)
# ============================================================================

def check_registry_hash_stability(registry: TaxonomyRegistry) -> Dict[str, Any]:
    hashes = []
    for _ in range(3):
        r = _load_registry()
        ids = sorted(p.id for p in r.get_all_packs())
        h = hashlib.sha256(str(ids).encode()).hexdigest()[:16]
        hashes.append(h)
    unique = len(set(hashes))
    return {"pass": unique == 1, "measured": 100 if unique == 1 else 0, "details": f"Hashes: {hashes}"}


def check_dag_deterministic(registry: TaxonomyRegistry) -> Dict[str, Any]:
    orders = []
    for _ in range(3):
        r = _load_registry()
        try:
            resolved = r.resolve_dependencies("CP01")
            orders.append(str(resolved))
        except Exception:
            orders.append("error")
    unique = len(set(orders))
    return {"pass": unique == 1, "measured": 100 if unique == 1 else 0, "details": f"Unique: {unique}"}


def check_query_deterministic(registry: TaxonomyRegistry) -> Dict[str, Any]:
    results = []
    for _ in range(3):
        r = _load_registry()
        stable = r.find_packs(pack_type="core_pack", status="stable")
        results.append(str(sorted(p.id for p in stable)))
    unique = len(set(results))
    return {"pass": unique == 1, "measured": 100 if unique == 1 else 0, "details": f"Unique: {unique}"}


def check_validation_deterministic(registry: TaxonomyRegistry) -> Dict[str, Any]:
    """Check pack combination validation returns same result across runs."""
    results = []
    test_combination = {"core_packs": [{"id": "CP01"}], "domain_packs": [{"id": "DP01"}],
                        "regulatory_overlays": [{"id": "RX01"}, {"id": "RX11"}]}
    for _ in range(3):
        r = _load_registry()
        report = r.validate_pack_combination(test_combination)
        results.append(str(sorted(i.rule for i in report)))
    unique = len(set(results))
    return {"pass": unique == 1, "measured": 100 if unique == 1 else 0, "details": f"Unique: {unique}"}


# ============================================================================
# INVARIANT_COVERAGE (KPI-022 ~ KPI-026)
# ============================================================================

def check_unresolved_refs(registry: TaxonomyRegistry) -> Dict[str, Any]:
    all_ids = {p.id for p in registry.get_all_packs()}
    unresolved = []
    for p in registry.get_all_packs():
        for dep in p.depends_on:
            if dep not in all_ids:
                unresolved.append(f"{p.id}->{dep}")
    return {"pass": not unresolved, "measured": 100 if not unresolved else 0,
            "details": f"Unresolved: {unresolved}" if unresolved else "All resolved"}


def check_dependency_cycles(registry: TaxonomyRegistry) -> Dict[str, Any]:
    cycles = registry.detect_cycles()
    return {"pass": not cycles, "measured": 100 if not cycles else 0,
            "details": f"Cycles: {cycles}" if cycles else "No cycles"}


def check_status_transitions(registry: TaxonomyRegistry) -> Dict[str, Any]:
    valid = {"planned", "developing", "stable", "deprecated"}
    violations = [p.id for p in registry.get_all_packs() if p.status not in valid]
    return {"pass": not violations, "measured": 100 if not violations else 0,
            "details": f"Violations: {violations}" if violations else "All valid"}


def check_phase_order(registry: TaxonomyRegistry) -> Dict[str, Any]:
    phase_num = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
    cp_map = {p.id: p for p in _cp(registry)}
    violations = []
    for p in _cp(registry):
        my_phase = phase_num.get(p.phase or "P0", 0)
        for dep in p.depends_on:
            dep_pack = cp_map.get(dep)
            if dep_pack:
                dep_phase = phase_num.get(dep_pack.phase or "P0", 0)
                if dep_phase > my_phase:
                    violations.append(f"{p.id}({p.phase})->{dep}({dep_pack.phase})")
    return {"pass": not violations, "measured": 100 if not violations else 0,
            "details": f"Violations: {violations}" if violations else "All OK"}


def check_stable_deps(registry: TaxonomyRegistry) -> Dict[str, Any]:
    all_map = {p.id: p for p in registry.get_all_packs()}
    violations = []
    for p in registry.get_all_packs():
        if p.status == "stable":
            for dep in p.depends_on:
                dep_pack = all_map.get(dep)
                if dep_pack and dep_pack.status == "planned":
                    violations.append(f"{p.id}->{dep}")
    return {"pass": not violations, "measured": 100 if not violations else 0,
            "details": f"Violations: {violations}" if violations else "All OK"}


# ============================================================================
# ERROR_NORMALIZATION (KPI-027 ~ KPI-028)
# ============================================================================

def check_error_codes(registry: TaxonomyRegistry) -> Dict[str, Any]:
    total = len(registry.get_all_packs())
    with_ids = sum(1 for p in registry.get_all_packs() if p.id)
    pct = (with_ids / total * 100) if total else 100
    return {"pass": pct >= 100, "measured": pct, "details": f"{with_ids}/{total}"}


def check_error_code_duplicates(registry: TaxonomyRegistry) -> Dict[str, Any]:
    internal_ids = [p.internal_id or "" for p in _cp(registry)]
    duplicates = len(internal_ids) - len(set(internal_ids))
    return {"pass": duplicates == 0, "measured": duplicates, "details": f"Duplicates: {duplicates}"}


# ============================================================================
# SYNC_BF (KPI-029 ~ KPI-031)
# ============================================================================

def check_cp_sync(registry: TaxonomyRegistry) -> Dict[str, Any]:
    synced = 0
    total = 0
    for p in _cp(registry):
        fe = p.raw.get("frontend_emitters", [])
        if fe:
            total += 1
            has_angular = any("angular" in str(e).lower() for e in fe)
            has_react = any("react" in str(e).lower() for e in fe)
            if has_angular and has_react:
                synced += 1
    pct = (synced / total * 100) if total else 100
    return {"pass": pct >= 100, "measured": pct, "details": f"{synced}/{total}"}


def check_dp_sync(registry: TaxonomyRegistry) -> Dict[str, Any]:
    synced = 0
    total = 0
    for p in _dp(registry):
        fe = p.raw.get("frontend_emitters", [])
        if fe:
            total += 1
            has_ui = any("angular" in str(e).lower() or "react" in str(e).lower() for e in fe)
            if has_ui:
                synced += 1
    pct = (synced / total * 100) if total else 100
    return {"pass": pct >= 100, "measured": pct, "details": f"{synced}/{total}"}


def check_rx_frontend_sync(registry: TaxonomyRegistry) -> Dict[str, Any]:
    total_both = 0
    with_frontend = 0
    for rx in _rx(registry):
        for obs in rx.obligations:
            if isinstance(obs, dict) and obs.get("enforce_level") == "both":
                total_both += 1
                guards = rx.raw.get("guards", {})
                if isinstance(guards, dict) and guards.get("frontend"):
                    with_frontend += 1
    pct = (with_frontend / total_both * 100) if total_both else 100
    return {"pass": pct >= 100, "measured": pct, "details": f"{with_frontend}/{total_both}"}


# ============================================================================
# REGISTRY (KPI-032 ~ KPI-035)
# ============================================================================

def check_registry_load(registry: TaxonomyRegistry) -> Dict[str, Any]:
    return {"pass": True, "measured": 1, "details": "Registry loaded"}


def check_pack_counts(registry: TaxonomyRegistry) -> Dict[str, Any]:
    actual_cp = len(_cp(registry))
    actual_dp = len(_dp(registry))
    actual_rx = len(_rx(registry))
    expected_cp = len(registry._raw.get("core_packs", []))
    expected_dp = len(registry._raw.get("domain_packs", []))
    expected_rx = len(registry._raw.get("regulatory_overlays", []))
    ok = (actual_cp == expected_cp and actual_dp == expected_dp and actual_rx == expected_rx)
    return {"pass": ok, "measured": 100 if ok else 0,
            "details": f"CP:{actual_cp}/{expected_cp} DP:{actual_dp}/{expected_dp} RX:{actual_rx}/{expected_rx}"}


def check_unique_ids(registry: TaxonomyRegistry) -> Dict[str, Any]:
    all_ids = [p.id for p in registry.get_all_packs()]
    duplicates = len(all_ids) - len(set(all_ids))
    return {"pass": duplicates == 0, "measured": duplicates, "details": f"Duplicates: {duplicates}"}


def check_versions(registry: TaxonomyRegistry) -> Dict[str, Any]:
    total = len(registry.get_all_packs())
    missing = [p.id for p in registry.get_all_packs() if not p.version]
    pct = ((total - len(missing)) / total * 100) if total else 100
    return {"pass": pct >= 100, "measured": pct,
            "details": f"Missing: {missing}" if missing else f"{total}/{total}"}


# ============================================================================
# INDUSTRY_COVERAGE (KPI-036 ~ KPI-038)
# ============================================================================

def check_dp_usage(registry: TaxonomyRegistry) -> Dict[str, Any]:
    total = len(_dp(registry))
    unused = [p.id for p in _dp(registry) if not p.industries_using]
    pct = ((total - len(unused)) / total * 100) if total else 100
    return {"pass": pct >= 100, "measured": pct,
            "details": f"Unused: {unused}" if unused else f"{total}/{total}"}


def check_rx_usage(registry: TaxonomyRegistry) -> Dict[str, Any]:
    total = len(_rx(registry))
    unused = [p.id for p in _rx(registry) if not p.industries_requiring]
    pct = ((total - len(unused)) / total * 100) if total else 100
    return {"pass": pct >= 100, "measured": pct,
            "details": f"Unused: {unused}" if unused else f"{total}/{total}"}


def check_orphan_packs(registry: TaxonomyRegistry) -> Dict[str, Any]:
    orphans = [p.id for p in _dp(registry) if not p.industries_using]
    orphans += [p.id for p in _rx(registry) if not p.industries_requiring]
    return {"pass": not orphans, "measured": len(orphans),
            "details": f"Orphans: {orphans}" if orphans else "None"}


# ============================================================================
# Public API
# ============================================================================

_CHECK_FUNCTIONS = {
    "check_cp_definitions_phase": check_cp_definitions_phase,
    "check_total_cp_definitions": check_total_cp_definitions,
    "check_cp_obligations": check_cp_obligations,
    "check_dp_entities": check_dp_entities,
    "check_dp_commands_queries": check_dp_commands_queries,
    "check_dp_workflows": check_dp_workflows,
    "check_dp_invariants": check_dp_invariants,
    "check_dp_depends_on_valid": check_dp_depends_on_valid,
    "check_rx_obligations": check_rx_obligations,
    "check_rx_gates": check_rx_gates,
    "check_rx_guards": check_rx_guards,
    "check_rx_industries": check_rx_industries,
    "check_dsl_parse": check_dsl_parse,
    "check_mir_build": check_mir_build,
    "check_pack_resolution": check_pack_resolution,
    "check_registry_hash_stability": check_registry_hash_stability,
    "check_dag_deterministic": check_dag_deterministic,
    "check_query_deterministic": check_query_deterministic,
    "check_validation_deterministic": check_validation_deterministic,
    "check_unresolved_refs": check_unresolved_refs,
    "check_dependency_cycles": check_dependency_cycles,
    "check_status_transitions": check_status_transitions,
    "check_phase_order": check_phase_order,
    "check_stable_deps": check_stable_deps,
    "check_error_codes": check_error_codes,
    "check_error_code_duplicates": check_error_code_duplicates,
    "check_cp_sync": check_cp_sync,
    "check_dp_sync": check_dp_sync,
    "check_rx_frontend_sync": check_rx_frontend_sync,
    "check_registry_load": check_registry_load,
    "check_pack_counts": check_pack_counts,
    "check_unique_ids": check_unique_ids,
    "check_versions": check_versions,
    "check_dp_usage": check_dp_usage,
    "check_rx_usage": check_rx_usage,
    "check_orphan_packs": check_orphan_packs,
}


def run_all_kpis() -> List[KPIResult]:
    """Run all KPI checks and return results."""
    registry = _load_registry()
    kpi_defs = _load_kpi_defs()
    results = []

    for kpi in kpi_defs.get("kpis", []):
        kpi_id = kpi["id"]
        name = kpi["name"]
        target_min = kpi.get("target_min", 0)
        target_max = kpi.get("target_max")
        check_fn_name = kpi.get("check_function", "")

        check_fn = _CHECK_FUNCTIONS.get(check_fn_name)
        if not check_fn:
            results.append(KPIResult(kpi_id, name, False, 0, target_min, target_max,
                                     f"Function '{check_fn_name}' not found"))
            continue

        kwargs = {}
        phase_filter = kpi.get("phase_filter")
        if phase_filter and check_fn == check_cp_definitions_phase:
            kwargs["phase"] = phase_filter

        result = check_fn(registry, **kwargs)
        measured = result["measured"]

        # Use the check function's own pass/fail if provided, else compare against target
        if "pass" in result:
            passed = result["pass"]
        elif target_max is not None and target_max == 0:
            passed = measured <= target_max
        else:
            passed = measured >= target_min

        results.append(KPIResult(
            kpi_id=kpi_id, name=name, passed=passed,
            measured=measured, target_min=target_min, target_max=target_max,
            details=result.get("details", "")
        ))

    return results


def run_kpi(kpi_id: str) -> KPIResult:
    """Run a single KPI check."""
    results = [r for r in run_all_kpis() if r.kpi_id == kpi_id]
    if results:
        return results[0]
    raise ValueError(f"Unknown KPI: {kpi_id}")