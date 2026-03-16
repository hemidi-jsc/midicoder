from __future__ import annotations

import json
from pathlib import Path

from .models import IndexManifest, PlanRef


def _plan_group(rel_path: str) -> str:
    return Path(rel_path).parts[0] if Path(rel_path).parts else "misc"


def load_index_manifest(plans_dir: Path) -> IndexManifest:
    index_path = plans_dir / "index.json"
    if not index_path.exists():
        raise RuntimeError("plans/index.json is missing. Run `code plan` before `code gen`.")

    payload = json.loads(index_path.read_text(encoding="utf-8"))
    raw_plans = payload.get("plans")
    if not isinstance(raw_plans, list) or not all(isinstance(it, str) for it in raw_plans):
        raise ValueError("plans/index.json must contain 'plans' as list[str].")

    refs = [PlanRef(rel_path=rel, group=_plan_group(rel)) for rel in raw_plans]
    return IndexManifest(
        version=str(payload.get("version", "unknown")),
        plans=refs,
        generation_order=[str(x) for x in payload.get("generation_order", []) if isinstance(x, str)],
        merge_mode={
            str(k): str(v)
            for k, v in payload.get("merge_mode", {}).items()
            if isinstance(k, str) and isinstance(v, str)
        },
        file_ownership={
            str(k): [str(v) for v in vals if isinstance(v, str)]
            for k, vals in payload.get("file_ownership", {}).items()
            if isinstance(k, str) and isinstance(vals, list)
        },
        bootstrap_entrypoint=(
            str(payload.get("bootstrap_contract", {}).get("entrypoint"))
            if isinstance(payload.get("bootstrap_contract"), dict)
            and payload["bootstrap_contract"].get("entrypoint")
            else None
        ),
    )


def resolve_execution_order(manifest: IndexManifest) -> list[PlanRef]:
    if not manifest.generation_order:
        return manifest.plans[:]

    ordered: list[PlanRef] = []
    seen: set[str] = set()
    for group in manifest.generation_order:
        for ref in manifest.plans:
            if ref.group == group and ref.rel_path not in seen:
                ordered.append(ref)
                seen.add(ref.rel_path)

    for ref in manifest.plans:
        if ref.rel_path not in seen:
            ordered.append(ref)
    return ordered
