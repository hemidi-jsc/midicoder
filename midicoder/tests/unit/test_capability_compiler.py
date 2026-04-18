from __future__ import annotations

import json
from pathlib import Path

from midicoder.capability.builder import compile_graph_to_ir
from midicoder.capability.compiler import CapabilityCompiler
from midicoder.capability.models import CapabilityGraph
from midicoder.capability.proposal import build_contract_proposal


def test_proposal_compiles_to_ir_payload() -> None:
    proposal = build_contract_proposal(
        "Build multi-tenant SaaS with auth, RBAC and AWS baseline",
        version="v1.0.0",
    )
    graph = proposal["graph"]
    compiler = CapabilityCompiler()
    result = compiler.compile(graph)

    assert result["validation_report"]["status"] == "ok"
    ir = result["ir"]
    assert ir["meta"]["pipeline"] == "contract_graph"
    assert ir["modules"]["domain"]["entities"]
    assert ir["modules"]["application"]["commands"]
    assert ir["indexes"]["symbols"]["command"]


def test_obligation_failure_when_missing_permission_and_tenant_filter() -> None:
    proposal = build_contract_proposal("Basic SaaS", version="v1.0.1")
    graph: CapabilityGraph = proposal["graph"]
    for node in graph.nodes:
        if node.id == "command_create_user":
            node.params.pop("permission", None)
            node.params.pop("tenant_filter", None)
            node.params["transaction"] = False
            break

    compiler = CapabilityCompiler()
    result = compiler.compile(graph)

    assert result["validation_report"]["status"] == "failed"
    issue_codes = {item["code"] for item in result["validation_report"]["issues"]}
    assert "EOB001" in issue_codes
    assert "EOB002" in issue_codes
    assert "EOB003" in issue_codes


def test_compile_graph_to_ir_is_deterministic_for_same_graph(tmp_path: Path) -> None:
    version = "v2.0.0"
    version_root = tmp_path / ".midicoder" / "versions" / version
    contracts_root = version_root / "contracts"
    contracts_root.mkdir(parents=True, exist_ok=True)

    proposal = build_contract_proposal("Auth RBAC tenant AWS", version=version)
    graph_payload = proposal["graph"].model_dump(by_alias=True)
    (contracts_root / "graph.json").write_text(
        json.dumps(graph_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    first = compile_graph_to_ir(version_root, version, deterministic_hash_gate=True)
    second = compile_graph_to_ir(version_root, version, deterministic_hash_gate=True)

    assert first["graph_hash"] == second["graph_hash"]
    assert first["ir_hash"] == second["ir_hash"]


def test_event_driven_lowering_builds_events_and_operations() -> None:
    proposal = build_contract_proposal(
        "Build async event-driven SaaS with queue and pubsub",
        version="v3.0.0",
    )
    compiler = CapabilityCompiler()
    result = compiler.compile(proposal["graph"])

    assert result["validation_report"]["status"] == "ok"
    ir = result["ir"]
    assert ir["modules"]["domain"]["events"]
    operation_kinds = {
        item.get("kind") for item in ir["modules"]["integrations"]["operations"]
    }
    assert "event_publish" in operation_kinds
    assert "event_subscription" in operation_kinds


def test_datasource_reference_obligation_fails_for_unknown_datasource() -> None:
    proposal = build_contract_proposal("Basic SaaS", version="v3.0.1")
    graph: CapabilityGraph = proposal["graph"]
    for node in graph.nodes:
        if node.type == "core.table":
            node.params["datasource"] = "missing_ds"
            break

    compiler = CapabilityCompiler()
    result = compiler.compile(graph)

    assert result["validation_report"]["status"] == "failed"
    issue_codes = {item["code"] for item in result["validation_report"]["issues"]}
    assert "EOB013" in issue_codes
