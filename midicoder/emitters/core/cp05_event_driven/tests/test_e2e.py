# coding: utf-8
"""
CP05 E2E Test — End-to-end pipeline verification.

Exercises the full structured emitter pipeline:
  Pack YML → EMITTER_REGISTRY → Structured Emitter → Jinja2 templates → Generated code

Tests both stacks (FastAPI, NestJS) with a comprehensive set of Events
covering tenant-aware events, multiple topics, and all event definitions.

Author: Midicoder Team
Version: 1.0.0
"""

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
_project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(_project_root))

from midicoder.emitters.core.cp05_event_driven import (
    CQRSProjection,
    DLQConfig,
    EventDefinition,
    EventSchemaVersion,
    EventStoreConfig,
    EventStream,
    IdempotentConsumer,
    OutboxEntry,
    RetryPolicy,
    TransportConfig,
    TransportType,
)
from midicoder.emitters.core.cp05_event_driven.parser import EventParser
from midicoder.pipeline.pack_emitter_router import EMITTER_REGISTRY, PARSER_REGISTRY


def build_test_events() -> list[EventDefinition]:
    """Build a comprehensive list of EventDefinitions."""
    return [
        EventDefinition(event_name="order.created", payload_fields=["order_id", "amount", "currency"], topic="orders"),
        EventDefinition(event_name="order.cancelled", payload_fields=["order_id", "reason"], topic="orders"),
        EventDefinition(event_name="payment.completed", payload_fields=["payment_id", "amount"], topic="payments"),
        EventDefinition(event_name="payment.failed", payload_fields=["payment_id", "error"], topic="payments", tenant_id="tenant_1"),
        EventDefinition(event_name="inventory.reserved", payload_fields=["sku", "quantity"], topic="inventory", version="2.0"),
    ]


def run_e2e():
    """Run the CP05 E2E pipeline test."""
    import importlib

    events = build_test_events()
    output_dir = _project_root / "sandbox" / "cp05_e2e_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    stacks = ["fastapi", "nestjs"]
    cp05_keys = [f"cp05.event.{s}" for s in stacks]
    results = {}
    total_files = 0

    print("=" * 72)
    print("CP05 E2E Pipeline Test")
    print("=" * 72)
    print(f"Events: {len(events)} definitions")
    for e in events:
        marker = f"[tenant={e.tenant_id}]" if e.tenant_id else ""
        print(f"  - {e.event_name} (topic={e.topic}, v{e.version}) {marker}")
    print()

    # Phase 1: Registry verification
    print("[Phase 1] EMITTER & PARSER Registry Verification")
    print("-" * 40)
    all_registered = True
    for key in cp05_keys:
        if key in EMITTER_REGISTRY:
            mod_path, cls_name, parser_key = EMITTER_REGISTRY[key]
            print(f"  ✓ {key}: {cls_name} ({mod_path})")
        else:
            results[key] = "FAIL: not registered"
            print(f"  ✗ {key}: MISSING")
            all_registered = False

    # Parser registry
    if "cp05_event" in PARSER_REGISTRY:
        print(f"  ✓ cp05_event: registered in PARSER_REGISTRY")
    else:
        print(f"  ✗ cp05_event: MISSING from PARSER_REGISTRY")
        all_registered = False

    # Phase 2: Structured emitter dispatch & file generation
    print()
    print("[Phase 2] Emitter Dispatch & File Generation")
    print("-" * 40)
    for stack in stacks:
        key = f"cp05.event.{stack}"
        if key not in EMITTER_REGISTRY:
            print(f"  {stack:>8s}: SKIPPED (not in registry)")
            continue

        stack_dir = output_dir / stack
        stack_dir.mkdir(parents=True, exist_ok=True)

        mod_path, cls_name, _ = EMITTER_REGISTRY[key]
        mod = importlib.import_module(mod_path)
        emitter_cls = getattr(mod, cls_name)
        stack_base = _project_root / "midicoder" / "stacks" / stack / "core"
        emitter = emitter_cls(stack_dir=stack_base)
        files = emitter.emit(events, stack_dir)

        written = 0
        for f in files:
            target = f.path
            if not target.is_absolute():
                target = stack_dir / target
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f.content, encoding="utf-8")
            total_files += 1
            written += 1

        print(f"  {stack:>8s}: {written} files → sandbox/cp05_e2e_output/{stack}/")

    # Phase 3: Metadata roundtrip (to_dict → from_dict)
    print()
    print("[Phase 3] Metadata Roundtrip (to_dict → from_dict)")
    print("-" * 40)
    dicts = [e.to_dict() for e in events]
    restored = [EventDefinition.from_dict(d) for d in dicts]
    roundtrip_ok = (
        len(restored) == len(events)
        and all(r.event_name == e.event_name for r, e in zip(restored, events))
        and all(r.topic == e.topic for r, e in zip(restored, events))
    )
    if roundtrip_ok:
        print(f"  ✓ {len(restored)} events roundtripped successfully")
    else:
        print(f"  ✗ FAIL: roundtrip mismatch")

    # Phase 3b: Parser roundtrip (MIR metadata → parse)
    print()
    print("[Phase 3b] Parser Roundtrip (MIR metadata format)")
    print("-" * 40)
    mir_events = [e.to_dict() for e in events]
    parser = EventParser()
    parsed = parser.parse(mir_events)
    parser_ok = (
        len(parsed) == len(events)
        and all(p.event_name == e.event_name for p, e in zip(parsed, events))
    )
    if parser_ok:
        print(f"  ✓ {len(parsed)} events parsed via EventParser")
    else:
        print(f"  ✗ FAIL: parser counts mismatch")

    # Phase 4: Verify generated code quality
    print()
    print("[Phase 4] Generated Code Verification")
    print("-" * 40)
    checks = {
        "fastapi": {"suffix": ".py", "keywords": ["async", "EventBus", "tenant_id"]},
        "nestjs": {"suffix": ".ts", "keywords": ["Injectable", "OnEvent", "EventBus"]},
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

    # Phase 5: New model coverage
    print()
    print("[Phase 5] New Model Instantiation Test")
    print("-" * 40)
    model_checks = []
    try:
        t = TransportConfig(transport_type=TransportType.KAFKA)
        model_checks.append(("TransportConfig", True))
    except Exception:
        model_checks.append(("TransportConfig", False))
    try:
        d = DLQConfig()
        model_checks.append(("DLQConfig", True))
    except Exception:
        model_checks.append(("DLQConfig", False))
    try:
        es = EventStoreConfig()
        model_checks.append(("EventStoreConfig", True))
    except Exception:
        model_checks.append(("EventStoreConfig", False))
    try:
        r = RetryPolicy()
        model_checks.append(("RetryPolicy", True))
    except Exception:
        model_checks.append(("RetryPolicy", False))
    try:
        ic = IdempotentConsumer()
        model_checks.append(("IdempotentConsumer", True))
    except Exception:
        model_checks.append(("IdempotentConsumer", False))
    try:
        sv = EventSchemaVersion(event_name="test")
        model_checks.append(("EventSchemaVersion", True))
    except Exception:
        model_checks.append(("EventSchemaVersion", False))
    try:
        stream = EventStream(stream_id="s1")
        model_checks.append(("EventStream", True))
    except Exception:
        model_checks.append(("EventStream", False))
    try:
        cqrs = CQRSProjection(projection_id="p1", source_events=["e1"], target_entity="v1")
        model_checks.append(("CQRSProjection", True))
    except Exception:
        model_checks.append(("CQRSProjection", False))
    try:
        ob = OutboxEntry(event_name="test", tenant_id="t1")
        model_checks.append(("OutboxEntry.tenant_id", True))
    except Exception:
        model_checks.append(("OutboxEntry.tenant_id", False))

    all_models_ok = all(ok for _, ok in model_checks)
    for name, ok in model_checks:
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")

    # Phase 6: Summary
    print()
    print("=" * 72)
    print("E2E Summary")
    print("=" * 72)
    print(f"  Total files generated: {total_files}")
    all_ok = all_registered and roundtrip_ok and parser_ok and total_files > 0 and all_models_ok
    if all_ok:
        print(f"  Status: PASS (all {len(stacks)} stacks, {total_files} files, roundtrip OK, models OK)")
    else:
        issues = []
        if not all_registered:
            issues.append("some stacks not registered")
        if total_files == 0:
            issues.append("no files generated")
        if not roundtrip_ok:
            issues.append("roundtrip failed")
        if not parser_ok:
            issues.append("parser roundtrip failed")
        if not all_models_ok:
            issues.append("model instantiation failed")
        print(f"  Status: FAIL ({', '.join(issues)})")

    # Write summary JSON
    summary = {
        "total_files": total_files,
        "stacks": stacks,
        "events": len(events),
        "roundtrip": "OK" if roundtrip_ok else "FAIL",
        "parser_roundtrip": "OK" if parser_ok else "FAIL",
        "models": "OK" if all_models_ok else "FAIL",
        "status": "PASS" if all_ok else "FAIL",
    }
    summary_path = _project_root / "sandbox" / "cp05_e2e_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"  Summary: {summary_path.relative_to(_project_root)}")

    return all_ok


if __name__ == "__main__":
    success = run_e2e()
    sys.exit(0 if success else 1)
