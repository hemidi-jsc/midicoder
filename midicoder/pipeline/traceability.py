"""
Traceability service — map Brief Analysis items to Contract nodes.

Detects drifts (orphans, mismatches) between analysis and generated contracts.
"""

from __future__ import annotations

import json
import re
import difflib
from typing import Any, Dict, List, Optional, Tuple

# Categories that exist in both analysis and contract
TRACEABLE_CATEGORIES = [
    "entities", "commands", "queries", "events",
    "workflows", "value_objects", "guards", "roles", "ui_components",
]

# Analysis categories WITHOUT contract counterpart
ANALYSIS_ONLY_CATEGORIES = ["aggregates", "permissions", "state_machines"]

# Short prefix for trace IDs
CATEGORY_PREFIX = {
    "entities": "ENT",
    "commands": "CMD",
    "queries": "QRy",
    "events": "EVT",
    "workflows": "WKF",
    "value_objects": "VOB",
    "guards": "GRD",
    "roles": "ROL",
    "ui_components": "UI",
}


def annotate_analysis_items(analysis_data: dict) -> dict:
    """
    Annotate each analysis item with a __trace_id__ for 1-1 mapping.

    Format: "CATEGORY:INDEX:Name" e.g. "ENT:00:Order"
    """
    annotated = {}
    for category, items in analysis_data.items():
        if not isinstance(items, list):
            annotated[category] = items
            continue
        new_items = []
        prefix = CATEGORY_PREFIX.get(category, category[:3].upper())
        for idx, item in enumerate(items):
            item = dict(item)
            name = item.get("name", f"Unnamed_{idx}")
            item["__trace_id__"] = f"{prefix}:{idx:02d}:{name}"
            new_items.append(item)
        annotated[category] = new_items
    return annotated


def _normalize_name(name: str) -> str:
    """
    Normalize a name for comparison — handles PascalCase ↔ snake_case ↔ kebab-case.

    PascalCase → pascal_case: ProductCategory → product_category
    snake_case → snake_case: product_category → product_category
    kebab-case → snake_case: product-category → product_category
    """
    import re
    if not name:
        return ""
    # First: replace hyphens with underscores
    s = name.replace("-", "_")
    # Then: insert underscore before uppercase letters (PascalCase → pascal_case)
    s = re.sub(r'(?<!^)(?<!_)([A-Z])', r'_\1', s)
    # Finally: lowercase
    return s.lower().strip()


def _get_analysis_names(analysis_data: dict, category: str) -> List[Tuple[str, dict]]:
    """Return list of (name, item) for a given analysis category."""
    items = analysis_data.get(category, [])
    return [(item.get("name", ""), item) for item in items if isinstance(item, dict)]


def _get_contract_ids(contract_yaml: dict, category: str) -> List[Tuple[str, dict]]:
    """Return list of (id, node) for a given contract category."""
    nodes = contract_yaml.get(category, [])
    return [(node.get("id", ""), node) for node in nodes if isinstance(node, dict)]


def _fuzzy_ratio(a: str, b: str) -> float:
    """Return normalized similarity ratio between two strings."""
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def compute_traceability(
    analysis_data: dict,
    contract_artifacts: Dict[str, dict],
    brief_content: str = "",
) -> dict:
    """
    Compute full traceability matrix between analysis and contracts.

    Args:
        analysis_data: Full brief analysis dict (12 categories)
        contract_artifacts: {category: yaml_dict} for 9 contract categories
        brief_content: Original brief markdown text (optional, for text-level trace)

    Returns:
        dict with:
            - trace_matrix: {category: [{trace_id, analysis_name, contract_id, status, ...}]}
            - drifts: [{type, category, detail, severity}]
            - summary: {total_analysis, total_contract, matched, orphan_analysis, orphan_contract, mismatched}
    """
    trace_matrix: Dict[str, list] = {}
    drifts: list[dict] = []
    totals = {
        "total_analysis": 0,
        "total_contract": 0,
        "matched": 0,
        "orphan_analysis": 0,
        "orphan_contract": 0,
        "mismatched": 0,
    }

    for category in TRACEABLE_CATEGORIES:
        analysis_items = _get_analysis_names(analysis_data, category)
        contract_ids = _get_contract_ids(contract_artifacts.get(category, {}), category)

        # Build maps keyed by NORMALIZED name (PascalCase ↔ snake_case)
        analysis_map: Dict[str, dict] = {}
        for name, item in analysis_items:
            if name:
                key = _normalize_name(name)
                analysis_map[key] = (name, item)

        contract_map: Dict[str, dict] = {}
        for cid, node in contract_ids:
            if cid:
                key = _normalize_name(cid)
                contract_map[key] = (cid, node)

        analysis_norm_keys = set(analysis_map.keys())
        contract_norm_keys = set(contract_map.keys())

        matched_keys = analysis_norm_keys & contract_norm_keys
        orphan_analysis_keys = analysis_norm_keys - contract_norm_keys
        orphan_contract_keys = contract_norm_keys - analysis_norm_keys

        prefix = CATEGORY_PREFIX.get(category, category[:3].upper())
        category_rows = []

        # Build analysis index lookup: normalized_name -> index
        analysis_index: Dict[str, int] = {}
        for idx, (n, i) in enumerate(analysis_items):
            nk = _normalize_name(n)
            if nk and nk not in analysis_index:
                analysis_index[nk] = idx

        # Matched items — check description similarity
        for norm_key in sorted(matched_keys):
            a_orig_name, a_item = analysis_map[norm_key]
            c_orig_id, c_node = contract_map[norm_key]
            a_idx = analysis_index.get(norm_key, 0)
            trace_id = f"{prefix}:{a_idx:02d}:{a_orig_name}"

            # Check description similarity
            a_desc = a_item.get("description", "")
            c_desc = c_node.get("description", "")
            desc_similarity = _fuzzy_ratio(a_desc, c_desc)

            if desc_similarity < 0.4 and a_desc and c_desc:
                status = "mismatch"
                totals["mismatched"] += 1
                drifts.append({
                    "type": "description_mismatch",
                    "category": category,
                    "name": a_orig_name,
                    "trace_id": trace_id,
                    "severity": "warning",
                    "analysis_description": a_desc[:200],
                    "contract_description": c_desc[:200],
                    "similarity": round(desc_similarity, 2),
                    "message": f"Description of '{a_orig_name}' ({category}) differs significantly from contract ({desc_similarity:.0%} match)",
                })
            else:
                status = "matched"

            totals["matched"] += 1
            category_rows.append({
                "trace_id": trace_id,
                "analysis_name": a_orig_name,
                "contract_id": c_orig_id,
                "status": status,
                "analysis_item": a_item,
                "contract_node": c_node,
                "description_similarity": round(desc_similarity, 2),
            })

        # Orphan analysis items (in analysis but not in contract)
        for norm_key in sorted(orphan_analysis_keys):
            a_orig_name, a_item = analysis_map[norm_key]
            a_idx = analysis_index.get(norm_key, 0)
            trace_id = f"{prefix}:{a_idx:02d}:{a_orig_name}"
            totals["orphan_analysis"] += 1
            drifts.append({
                "type": "orphan_analysis",
                "category": category,
                "name": a_orig_name,
                "trace_id": trace_id,
                "severity": "error",
                "message": f"Analysis item '{a_orig_name}' ({category}) has no corresponding contract node",
            })
            category_rows.append({
                "trace_id": trace_id,
                "analysis_name": a_orig_name,
                "contract_id": None,
                "status": "orphan_analysis",
                "analysis_item": a_item,
                "contract_node": None,
            })

        # Orphan contract items (in contract but not in analysis)
        for norm_key in sorted(orphan_contract_keys):
            c_orig_id, c_node = contract_map[norm_key]
            trace_id = f"{prefix}:--:{c_orig_id}"
            totals["orphan_contract"] += 1
            drifts.append({
                "type": "orphan_contract",
                "category": category,
                "name": c_orig_id,
                "trace_id": trace_id,
                "severity": "warning",
                "message": f"Contract node '{c_orig_id}' ({category}) has no source in analysis",
            })
            category_rows.append({
                "trace_id": trace_id,
                "analysis_name": None,
                "contract_id": c_orig_id,
                "status": "orphan_contract",
                "analysis_item": None,
                "contract_node": c_node,
            })

        totals["total_analysis"] += len(analysis_norm_keys)
        totals["total_contract"] += len(contract_norm_keys)
        trace_matrix[category] = category_rows

    # Add unmapped analysis categories info
    unmapped_analysis = []
    for cat in ANALYSIS_ONLY_CATEGORIES:
        items = analysis_data.get(cat, [])
        if items:
            unmapped_analysis.append({
                "category": cat,
                "count": len(items),
                "items": items,
            })

    # Brief text analysis (simple keyword coverage)
    brief_coverage = _compute_brief_text_coverage(analysis_data, brief_content)

    # Extract graph data (nodes + edges) for visualization
    graph_data = extract_graph_data(contract_artifacts, trace_matrix)

    return {
        "trace_matrix": trace_matrix,
        "drifts": drifts,
        "summary": totals,
        "unmapped_analysis": unmapped_analysis,
        "brief_coverage": brief_coverage,
        "health_score": _compute_health_score(totals, drifts),
        "graph": graph_data,
    }


def _compute_brief_text_coverage(analysis_data: dict, brief_content: str) -> dict:
    """
    Check how well analysis items are grounded in the original brief text.

    Simple keyword-based coverage: for each analysis item name, check if
    the name (or a close variant) appears in the brief text.
    """
    if not brief_content:
        return {"coverage_ratio": 0, "covered": [], "uncovered": []}

    brief_lower = brief_content.lower()
    covered = []
    uncovered = []

    for category in TRACEABLE_CATEGORIES:
        items = analysis_data.get(category, [])
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("name", "")
            if not name:
                continue
            # Check if name (lowercase, no camelCase) appears in brief
            name_lower = name.lower().replace("_", " ")
            # Also try individual words
            name_words = name_lower.split()
            found = name_lower in brief_lower or any(w in brief_lower for w in name_words if len(w) > 3)

            if found:
                covered.append({"name": name, "category": category})
            else:
                uncovered.append({"name": name, "category": category})

    total = len(covered) + len(uncovered)
    return {
        "coverage_ratio": round(len(covered) / total, 2) if total > 0 else 0,
        "covered_count": len(covered),
        "uncovered_count": len(uncovered),
        "uncovered_items": uncovered[:20],  # limit to avoid huge payload
    }


def _compute_health_score(totals: dict, drifts: list) -> float:
    """
    Compute a 0-100 health score for the contract set.

    Deductions:
        - orphan_analysis: -10 per item (critical — requirement missing from contract)
        - orphan_contract: -2 per item (minor — LLM invented extra nodes)
        - description_mismatch: -5 per item (moderate — semantic drift)
    """
    score = 100.0

    for drift in drifts:
        if drift["type"] == "orphan_analysis":
            score -= 10
        elif drift["type"] == "orphan_contract":
            score -= 2
        elif drift["type"] == "description_mismatch":
            score -= 5

    return max(0.0, round(score, 1))


def get_fixable_categories(drifts: list) -> List[str]:
    """Return list of categories that need regeneration based on drifts."""
    categories = set()
    for drift in drifts:
        if drift["severity"] == "error":
            categories.add(drift["category"])
    return sorted(categories)


def extract_graph_data(
    contract_artifacts: Dict[str, dict],
    trace_matrix: dict,
) -> dict:
    """
    Extract graph nodes and edges from real contract YAML.

    Returns:
        {
            "nodes": [{"uid", "label", "category", "status", "fields", "foreign_keys"}],
            "edges": [{"from", "to", "type", "cardinality"}]
        }
    """
    nodes: list[dict] = []
    edges: list[dict] = []
    norm = _normalize_name

    # Build a status lookup: normalized_name -> status
    status_lookup: Dict[str, str] = {}
    for cat, rows in trace_matrix.items():
        for row in rows:
            an = row.get("analysis_name")
            ci = row.get("contract_id")
            for name in [an, ci]:
                if name:
                    nk = norm(name)
                    if nk not in status_lookup:
                        status_lookup[nk] = row.get("status", "matched")

    # Build entity name set for resolving references
    entity_nodes_raw: list[str] = []
    entities_yaml = contract_artifacts.get("entities", {})
    if entities_yaml and isinstance(entities_yaml, dict):
        entity_nodes_raw = [e.get("id", "") for e in (entities_yaml.get("entities", []) or []) if e.get("id")]

    entity_norm_to_id = {norm(e): e for e in entity_nodes_raw if e}

    # Build entity lookup dict: normalized name -> entity YAML dict
    entity_dict: Dict[str, dict] = {}
    if entities_yaml and isinstance(entities_yaml, dict):
        for e in (entities_yaml.get("entities", []) or []):
            eid = e.get("id", "")
            if eid:
                entity_dict[norm(eid)] = e

    def resolve_entity(ref: str) -> str | None:
        if not ref:
            return None
        if ref in entity_norm_to_id:
            return entity_norm_to_id[ref]
        nk = norm(ref)
        return entity_norm_to_id.get(nk)

    def add_node(category: str, name: str):
        uid = f"{category}:{name}"
        nk = norm(name)
        status = status_lookup.get(nk, "default")
        nodes.append({"uid": uid, "label": name, "category": category, "status": status})

    def add_edge(f: str, t: str, etype: str):
        if f and t:
            edges.append({"from": f, "to": t, "type": etype})

    # ── Entities ──
    for eid in entity_nodes_raw:
        uid = f"entities:{eid}"
        nk = norm(eid)
        status = status_lookup.get(nk, "default")

        # Extract fields from entity YAML
        raw_entity = entity_dict.get(nk, {})
        pk_name = raw_entity.get("primary_key", "id")
        raw_fields = raw_entity.get("fields", [])
        fields_out: list[dict] = []
        for f in raw_fields:
            fname = f.get("name", "") if isinstance(f, dict) else str(f)
            ftype = f.get("type", "string") if isinstance(f, dict) else "string"
            is_pk = fname == pk_name
            fields_out.append({"name": fname, "type": ftype, "is_pk": is_pk})

        # ── Foreign keys: from explicit constraints OR inferred from naming ──
        foreign_keys: list[dict] = []
        resolved_fk_set: set[Tuple[str, str]] = set()  # track (field, target) to avoid duplicates

        # Source 1: explicit constraints
        for c in (raw_entity.get("constraints") or []):
            if not isinstance(c, dict) or c.get("type") != "foreign_key":
                continue
            ref_str = c.get("ref", "")
            if not isinstance(ref_str, str):
                continue
            parts = ref_str.split(".")
            target_ent = resolve_entity(parts[0])
            if not target_ent:
                continue
            fk_field = c.get("field", "")
            cardinality = "1:1" if c.get("unique") else "N:1"
            fk_key = (fk_field, target_ent)
            if fk_key in resolved_fk_set:
                continue
            resolved_fk_set.add(fk_key)

            for fi, fd in enumerate(fields_out):
                if fd["name"] == fk_field:
                    fields_out[fi] = {**fd, "is_fk": True}
            foreign_keys.append({"field": fk_field, "target_entity": target_ent, "cardinality": cardinality})
            edges.append({"from": uid, "to": f"entities:{target_ent}", "type": "foreign_key", "cardinality": cardinality})

        # Source 2: infer from field naming convention (e.g. "category_id" → "category")
        for fd in fields_out:
            fname = fd["name"]
            m = re.match(r"^(.+)_id$", fname)
            if not m:
                continue
            candidate = m.group(1)
            target_ent = resolve_entity(candidate)
            if not target_ent or target_ent == eid:
                continue
            fk_key = (fname, target_ent)
            if fk_key in resolved_fk_set:
                continue
            resolved_fk_set.add(fk_key)

            # Mark field as FK
            idx = next((i for i, f in enumerate(fields_out) if f["name"] == fname), -1)
            if idx >= 0:
                fields_out[idx] = {**fd, "is_fk": True}
            foreign_keys.append({"field": fname, "target_entity": target_ent, "cardinality": "N:1"})
            edges.append({"from": uid, "to": f"entities:{target_ent}", "type": "foreign_key", "cardinality": "N:1"})

        nodes.append({
            "uid": uid,
            "label": eid,
            "category": "entities",
            "status": status,
            "fields": fields_out,
            "foreign_keys": foreign_keys,
        })

    # ── Commands ──
    commands_yaml = contract_artifacts.get("commands", {})
    if commands_yaml and isinstance(commands_yaml, dict):
        for cmd in (commands_yaml.get("commands", []) or []):
            cid = cmd.get("id", "")
            if not cid:
                continue
            add_node("commands", cid)
            # writes_to → entities
            for ref in (cmd.get("writes_to") or []):
                target = resolve_entity(ref)
                if target:
                    add_edge(f"commands:{cid}", f"entities:{target}", "writes_to")
            # fetches → entities
            for fetch in (cmd.get("fetches") or []):
                if isinstance(fetch, dict):
                    entity = fetch.get("entity") or fetch.get("entity_id")
                else:
                    entity = fetch
                target = resolve_entity(entity)
                if target:
                    add_edge(f"commands:{cid}", f"entities:{target}", "fetches")
            # emits → events
            for evt in (cmd.get("emits") or []):
                add_edge(f"commands:{cid}", f"events:{evt}", "emits")

    # ── Queries ──
    queries_yaml = contract_artifacts.get("queries", {})
    if queries_yaml and isinstance(queries_yaml, dict):
        for qry in (queries_yaml.get("queries", []) or []):
            qid = qry.get("id", "")
            if not qid:
                continue
            add_node("queries", qid)
            # reads_from → entities
            for ref in (qry.get("reads_from") or []):
                target = resolve_entity(ref)
                if target:
                    add_edge(f"queries:{qid}", f"entities:{target}", "reads_from")
            # fetches → entities
            for fetch in (qry.get("fetches") or []):
                if isinstance(fetch, dict):
                    entity = fetch.get("entity") or fetch.get("entity_id")
                else:
                    entity = fetch
                target = resolve_entity(entity)
                if target:
                    add_edge(f"queries:{qid}", f"entities:{target}", "fetches")

    # ── Events ──
    events_yaml = contract_artifacts.get("events", {})
    if events_yaml and isinstance(events_yaml, dict):
        for evt in (events_yaml.get("events", []) or []):
            eid = evt.get("id", "")
            if not eid:
                continue
            add_node("events", eid)
            src = evt.get("source_entity")
            if src:
                target = resolve_entity(src)
                if target:
                    add_edge(f"events:{eid}", f"entities:{target}", "source_entity")

    # ── Workflows ──
    workflows_yaml = contract_artifacts.get("workflows", {})
    if workflows_yaml and isinstance(workflows_yaml, dict):
        for wf in (workflows_yaml.get("workflows", []) or []):
            wid = wf.get("id", "")
            if not wid:
                continue
            add_node("workflows", wid)
            # transitions may reference commands
            for trans in (wf.get("transitions") or []):
                if isinstance(trans, dict):
                    cmd_ref = trans.get("command") or trans.get("on")
                    if cmd_ref:
                        add_edge(f"workflows:{wid}", f"commands:{cmd_ref}", "uses_command")

    # ── Value Objects ──
    vo_yaml = contract_artifacts.get("value_objects", {})
    if vo_yaml and isinstance(vo_yaml, dict):
        for vo in (vo_yaml.get("value_objects", []) or []):
            vid = vo.get("id", "")
            if not vid:
                continue
            add_node("value_objects", vid)

    # ── Guards ──
    guards_yaml = contract_artifacts.get("guards", {})
    if guards_yaml and isinstance(guards_yaml, dict):
        for gd in (guards_yaml.get("guards", []) or []):
            gid = gd.get("id", "")
            if not gid:
                continue
            add_node("guards", gid)
            target = gd.get("target")
            if target:
                # target can be a command
                add_edge(f"guards:{gid}", f"commands:{target}", "guards")

    # ── Roles ──
    roles_yaml = contract_artifacts.get("roles", {})
    if roles_yaml and isinstance(roles_yaml, dict):
        for rl in (roles_yaml.get("roles", []) or []):
            rid = rl.get("id", "")
            if not rid:
                continue
            add_node("roles", rid)

    # ── UI Components ──
    ui_yaml = contract_artifacts.get("ui_components", {})
    if ui_yaml and isinstance(ui_yaml, dict):
        for uc in (ui_yaml.get("ui_components", []) or []):
            uid = uc.get("id", "")
            if not uid:
                continue
            add_node("ui_components", uid)
            entity_ref = uc.get("entity_id")
            if entity_ref:
                target = resolve_entity(entity_ref)
                if target:
                    add_edge(f"ui_components:{uid}", f"entities:{target}", "entity_ref")

    # Deduplicate edges
    seen = set()
    unique_edges = []
    for e in edges:
        key = (e["from"], e["to"], e["type"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    return {"nodes": nodes, "edges": unique_edges}
