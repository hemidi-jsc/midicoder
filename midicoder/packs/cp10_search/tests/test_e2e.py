# coding: utf-8
"""
CP10 E2E Test — End-to-end pipeline verification.

Exercises the full structured emitter pipeline:
  Pack YML → EMITTER_REGISTRY → Structured Emitter → Jinja2 templates → Generated code

Tests all 4 stacks (FastAPI, NestJS, Angular, React) with a comprehensive
SearchCollection containing basic + vector + geo + faceted indices.

Author: Midicoder Team
Version: 1.0.0
"""

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
_project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(_project_root))

from midicoder.packs.cp10_search import (
    Facet,
    FacetedSearchIndex,
    FacetType,
    GeoOperation,
    GeoSearchColumn,
    GeoSearchIndex,
    SearchCollection,
    SearchIndex,
    SearchIndexColumn,
    SearchProviderType,
    SearchQuery,
    SearchQueryType,
    SyncStrategy,
    VectorIndexColumn,
    VectorSearchIndex,
    VectorSimilarityMetric,
)
from midicoder.packs.cp10_search.parser import SearchParser
from midicoder.pipeline.pack_emitter_router import EMITTER_REGISTRY


def build_test_collection() -> SearchCollection:
    """Build a comprehensive SearchCollection with all index types."""
    c = SearchCollection()

    # Basic fulltext index
    c.add_index(SearchIndex(
        id="products",
        provider=SearchProviderType.ELASTICSEARCH,
        columns=[
            SearchIndexColumn(name="title", column_type="text", searchable=True),
            SearchIndexColumn(name="description", column_type="text", searchable=True),
            SearchIndexColumn(name="price", column_type="numeric", filterable=True, sortable=True),
        ],
        sync_strategy=SyncStrategy.NEAR_REALTIME,
        tenant_isolated=True,
    ))

    # Vector index
    c.add_vector_index(VectorSearchIndex(
        id="semantic",
        provider=SearchProviderType.ELASTICSEARCH,
        vector_column=VectorIndexColumn(
            name="embedding",
            dimensions=768,
            similarity_metric=VectorSimilarityMetric.COSINE,
        ),
        text_columns=[
            SearchIndexColumn(name="title", column_type="text", searchable=True),
        ],
        top_k=20,
    ))

    # Geo index
    c.add_geo_index(GeoSearchIndex(
        id="locations",
        provider=SearchProviderType.ELASTICSEARCH,
        geo_column=GeoSearchColumn(name="location", geo_type="point"),
        operations=[GeoOperation.CIRCLE, GeoOperation.DISTANCE],
        tenant_isolated=True,
    ))

    # Faceted index
    c.add_faceted_index(FacetedSearchIndex(
        id="product_facets",
        provider=SearchProviderType.ELASTICSEARCH,
        facets=[
            Facet(id="brand", facet_type=FacetType.TERM, source_column="brand"),
            Facet(id="price_range", facet_type=FacetType.RANGE, source_column="price", range_bounds=[0, 100, 500, 1000]),
        ],
    ))

    # Queries
    c.add_query(SearchQuery(id="search_products", query_type=SearchQueryType.FULLTEXT, target_index="products", fields=["title", "description"]))
    c.add_query(SearchQuery(id="search_similar", query_type=SearchQueryType.VECTOR, target_index="semantic"))
    c.add_query(SearchQuery(id="search_nearby", query_type=SearchQueryType.GEO, target_index="locations"))

    return c


def run_e2e():
    """Run the CP10 E2E pipeline test."""
    import importlib

    collection = build_test_collection()
    output_dir = _project_root / "sandbox" / "cp10_e2e_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    stacks = ["fastapi", "nestjs", "angular", "react"]
    cp10_keys = [f"cp10.search.{s}" for s in stacks]
    results = {}
    total_files = 0

    print("=" * 72)
    print("CP10 E2E Pipeline Test")
    print("=" * 72)
    print(f"Collection: {collection.total_count} index, "
          f"{collection.total_vector_count} vector, "
          f"{collection.total_geo_count} geo, "
          f"{collection.total_faceted_count} faceted, "
          f"{len(collection.queries)} queries")
    print()

    # Phase 1: Registry verification
    print("[Phase 1] EMITTER Registry Verification")
    print("-" * 40)
    all_registered = True
    for key in cp10_keys:
        if key in EMITTER_REGISTRY:
            mod_path, cls_name, parser_key = EMITTER_REGISTRY[key]
            print(f"  ✓ {key}: {cls_name} ({mod_path})")
        else:
            results[key] = "FAIL: not registered"
            print(f"  ✗ {key}: MISSING")
            all_registered = False

    # Phase 2: Structured emitter dispatch & file generation
    print()
    print("[Phase 2] Emitter Dispatch & File Generation")
    print("-" * 40)
    for stack in stacks:
        key = f"cp10.search.{stack}"
        if key not in EMITTER_REGISTRY:
            print(f"  {stack:>8s}: SKIPPED (not in registry)")
            continue

        stack_dir = output_dir / stack
        stack_dir.mkdir(parents=True, exist_ok=True)

        mod_path, cls_name, _ = EMITTER_REGISTRY[key]
        mod = importlib.import_module(mod_path)
        emitter_cls = getattr(mod, cls_name)
        emitter = emitter_cls()
        files = emitter.emit(collection, stack_dir)

        written = 0
        for f in files:
            target = f.path
            if not target.is_absolute():
                target = stack_dir / target
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f.content, encoding="utf-8")
            total_files += 1
            written += 1

        print(f"  {stack:>8s}: {written} files → sandbox/cp10_e2e_output/{stack}/")

    # Phase 3: Metadata roundtrip (to_dict → from_dict)
    print()
    print("[Phase 3] Metadata Roundtrip (to_dict → from_dict)")
    print("-" * 40)
    d = collection.to_dict()
    restored = SearchCollection.from_dict(d)
    roundtrip_ok = (
        restored.total_count == collection.total_count
        and restored.total_vector_count == collection.total_vector_count
        and restored.total_geo_count == collection.total_geo_count
        and restored.total_faceted_count == collection.total_faceted_count
        and len(restored.queries) == len(collection.queries)
    )
    if roundtrip_ok:
        print(f"  ✓ {restored.total_count}+{restored.total_vector_count}+{restored.total_geo_count}+{restored.total_faceted_count} indices, {len(restored.queries)} queries")
    else:
        print(f"  ✗ FAIL: counts mismatch")

    # Phase 3b: Parser roundtrip (MIR metadata → parse_from_metadata)
    print()
    print("[Phase 3b] Parser Roundtrip (MIR metadata format)")
    print("-" * 40)
    mir_meta = {
        "search_indices": d.get("indices", []),
        "vector_search_indices": d.get("vector_indices", []),
        "geo_search_indices": d.get("geo_indices", []),
        "faceted_search_indices": d.get("faceted_indices", []),
        "search_queries": d.get("queries", []),
    }
    parser = SearchParser()
    parsed = parser.parse_from_metadata(mir_meta)
    parser_ok = (
        parsed.total_count == collection.total_count
        and parsed.total_vector_count == collection.total_vector_count
        and parsed.total_geo_count == collection.total_geo_count
        and parsed.total_faceted_count == collection.total_faceted_count
        and len(parsed.queries) == len(collection.queries)
    )
    if parser_ok:
        print(f"  ✓ {parsed.total_count}+{parsed.total_vector_count}+{parsed.total_geo_count}+{parsed.total_faceted_count} indices, {len(parsed.queries)} queries")
    else:
        print(f"  ✗ FAIL: parser counts mismatch")

    # Phase 4: Verify generated code quality
    print()
    print("[Phase 4] Generated Code Verification")
    print("-" * 40)
    checks = {
        "fastapi": {"suffix": ".py", "keywords": ["async", "tenant_isolated"]},
        "nestjs": {"suffix": ".ts", "keywords": ["Injectable", "tenant"]},
        "angular": {"suffix": ".ts", "keywords": ["Injectable", "HttpClient"]},
        "react": {"suffix": ".ts", "keywords": ["useContext", "tenant"]},
    }
    for stack in stacks:
        stack_dir = output_dir / stack
        if not stack_dir.exists():
            print(f"  {stack:>8s}: SKIPPED (no output)")
            continue

        actual_files = [f for f in stack_dir.rglob("*") if f.is_file()]
        suffix = checks[stack]["suffix"]
        keywords = checks[stack]["keywords"]

        content = ""
        for f in actual_files:
            if f.suffix == suffix:
                content += f.read_text(encoding="utf-8")

        found = [kw for kw in keywords if kw in content]
        missing = [kw for kw in keywords if kw not in content]
        status = "✓" if not missing else "⚠"
        detail = f"keywords: {found}"
        if missing:
            detail += f", missing: {missing}"
        print(f"  {status} {stack:>8s}: {len(actual_files)} files ({detail})")

    # Phase 5: Summary
    print()
    print("=" * 72)
    print("E2E Summary")
    print("=" * 72)
    print(f"  Total files generated: {total_files}")
    all_ok = all_registered and roundtrip_ok and parser_ok and total_files > 0
    if all_ok:
        print(f"  Status: PASS (all {len(stacks)} stacks, {total_files} files, roundtrip OK)")
    else:
        issues = []
        if not all_registered:
            issues.append("some stacks not registered")
        if total_files == 0:
            issues.append("no files generated")
        if not roundtrip_ok:
            issues.append("roundtrip failed")
        print(f"  Status: FAIL ({', '.join(issues)})")

    # Write summary JSON
    summary = {
        "total_files": total_files,
        "stacks": stacks,
        "collection": {
            "indices": collection.total_count,
            "vector": collection.total_vector_count,
            "geo": collection.total_geo_count,
            "faceted": collection.total_faceted_count,
            "queries": len(collection.queries),
        },
        "roundtrip": "OK" if roundtrip_ok else "FAIL",
        "status": "PASS" if all_ok else "FAIL",
    }
    summary_path = _project_root / "sandbox" / "cp10_e2e_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"  Summary: {summary_path.relative_to(_project_root)}")

    return all_ok


if __name__ == "__main__":
    success = run_e2e()
    sys.exit(0 if success else 1)
