# coding: utf-8
"""
E2E integration test cho CP06 — verify pack work trong toàn bộ pipeline.

Test flow:
1. Pack registry (CP_ID_TO_INTERNAL)
2. Load pack.yml từ disk
3. FileContributionsLoader integration
4. Parse MIR metadata → RouteCollection
5. FastAPI Emitter (file count, content, Rule V1/V2)
6. NestJS Emitter
7. Angular + React Emitters
8. Template existence check
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from midicoder.packs.cp06_api_gateway.route_parser import RouteParser
from midicoder.packs.cp06_api_gateway.fastapi import FastAPIGatewayEmitter
from midicoder.packs.cp06_api_gateway.nestjs import NestJSGatewayEmitter
from midicoder.packs.cp06_api_gateway.angular import AngularGatewayEmitter
from midicoder.packs.cp06_api_gateway.react import ReactGatewayEmitter
from midicoder.packs.cp06_api_gateway.models import (
    RouteCollection,
    Route,
    RouteAuthConfig,
    HttpMethod,
    AuthMode,
    GraphQLResolver,
    GraphQLOperation,
    WebhookHandler,
    WebhookAuthConfig,
    WebhookAuthType,
    KongGateway,
    KongService,
    ConsulService,
)
from midicoder.pipeline.file_contributions_loader import FileContributionsLoader
from midicoder.contracts.registry import CP_ID_TO_INTERNAL
from midicoder.pipeline.pack_emitter_router import EMITTER_REGISTRY, PARSER_REGISTRY
import yaml
import tempfile
import shutil


def run_e2e():
    """Chạy E2E test cho CP06."""
    passed = 0
    failed = 0
    errors = []

    results = []

    # ------------------------------------------------------------------
    # Test 1: Pack registry
    # ------------------------------------------------------------------
    try:
        assert "CP06" in CP_ID_TO_INTERNAL, "CP06 not in CP_ID_TO_INTERNAL"
        assert CP_ID_TO_INTERNAL["CP06"] == "cp06_api_gateway", f"Wrong mapping: {CP_ID_TO_INTERNAL['CP06']}"
        results.append(("Pack registry", True, "CP06 → cp06_api_gateway registered"))
        passed += 1
    except Exception as e:
        results.append(("Pack registry", False, str(e)))
        failed += 1
        errors.append(f"Registry: {e}")

    # ------------------------------------------------------------------
    # Test 2: Load pack.yml
    # ------------------------------------------------------------------
    try:
        pack_yml = Path(__file__).resolve().parent.parent / "pack.yml"
        assert pack_yml.exists(), f"pack.yml not found at {pack_yml}"
        with open(pack_yml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "pack" in data, "pack.yml missing 'pack' key"
        pack = data["pack"]
        assert pack["id"] == "CP06"
        assert pack["internal_id"] == "cp06_api_gateway"
        assert "file_contributions" in pack
        assert "infrastructure" in pack["file_contributions"]
        results.append(("Load pack.yml", True, f"version {pack['version']}, {len(pack['file_contributions']['infrastructure'])} infra"))
        passed += 1
    except Exception as e:
        results.append(("Load pack.yml", False, str(e)))
        failed += 1
        errors.append(f"pack.yml: {e}")

    # ------------------------------------------------------------------
    # Test 3: FileContributionsLoader
    # ------------------------------------------------------------------
    try:
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="cp06_api_gateway", pack_id="CP06", stack="fastapi")
        assert not fc.is_empty, "No file contributions loaded for CP06"
        assert len(fc.infrastructure) > 0, "No infrastructure files"
        infra_paths = [f.path for f in fc.infrastructure]
        assert any("gateway_app.py" in p for p in infra_paths), "gateway_app.py not in infrastructure"
        results.append(("FileContributionsLoader", True, f"{len(fc.infrastructure)} infra files"))
        passed += 1
    except Exception as e:
        results.append(("FileContributionsLoader", False, str(e)))
        failed += 1
        errors.append(f"FileContributionsLoader: {e}")

    # ------------------------------------------------------------------
    # Test 4: EMITTER_REGISTRY + PARSER_REGISTRY
    # ------------------------------------------------------------------
    try:
        assert "cp06.gateway.fastapi" in EMITTER_REGISTRY
        assert "cp06.gateway.nestjs" in EMITTER_REGISTRY
        assert "cp06.gateway.angular" in EMITTER_REGISTRY
        assert "cp06.gateway.react" in EMITTER_REGISTRY
        assert "cp06_gateway" in PARSER_REGISTRY
        results.append(("Emitter/Parser registry", True, "All 4 stacks + parser registered"))
        passed += 1
    except Exception as e:
        results.append(("Emitter/Parser registry", False, str(e)))
        failed += 1
        errors.append(f"Registry: {e}")

    # ------------------------------------------------------------------
    # Test 5: Parse MIR metadata → RouteCollection
    # ------------------------------------------------------------------
    try:
        parser = RouteParser()
        mir_metadata = {
            "routes": [
                {
                    "id": "GetUsers",
                    "method": "GET",
                    "path": "/api/v1/users",
                    "handler_type": "query",
                    "handler_id": "list_users",
                    "tags": ["users"],
                    "auth": {"mode": "jwt", "tenant_scoped": True},
                },
                {
                    "id": "CreateOrder",
                    "method": "POST",
                    "path": "/api/v1/orders",
                    "handler_type": "command",
                    "handler_id": "create_order",
                    "tags": ["orders"],
                    "auth": {"mode": "jwt", "required_roles": ["admin"]},
                },
            ],
            "graphql": [
                {
                    "id": "GetUser",
                    "operation": "query",
                    "type_name": "Query",
                    "field_name": "user",
                    "handler_id": "get_user",
                    "returns": [{"name": "user", "type": "User"}],
                },
            ],
            "webhooks": [
                {
                    "id": "stripe_payment",
                    "path": "/webhooks/stripe",
                    "event_type": "payment.completed",
                    "handler_id": "handle_stripe_payment",
                    "auth_config": {
                        "auth_type": "hmac_signature",
                        "header_name": "X-Stripe-Signature",
                    },
                },
            ],
        }
        collection = parser.parse_from_metadata(
            routes_data=mir_metadata["routes"],
            graphql_data=mir_metadata["graphql"],
            webhooks_data=mir_metadata["webhooks"],
        )
        assert collection.total_count == 4
        assert len(collection.routes) == 2
        assert len(collection.resolvers) == 1
        assert len(collection.webhooks) == 1
        results.append(("Parse MIR metadata", True, f"{collection.total_count} items (2 routes, 1 graphql, 1 webhook)"))
        passed += 1
    except Exception as e:
        results.append(("Parse MIR metadata", False, str(e)))
        failed += 1
        errors.append(f"Parse MIR: {e}")

    # ------------------------------------------------------------------
    # Test 6: FastAPI Emitter
    # ------------------------------------------------------------------
    try:
        emitter = FastAPIGatewayEmitter()
        files = emitter.generate(collection)
        assert len(files) >= 2, f"Expected >= 2 files, got {len(files)}"
        for path, content in files.items():
            assert "from midicoder" not in content, f"Rule V1 violation in {path}"
            assert "__post_init__" not in content, f"Rule V2 violation in {path}"
        results.append(("FastAPI Emitter", True, f"{len(files)} files, Rule V1/V2 passed"))
        passed += 1
    except Exception as e:
        results.append(("FastAPI Emitter", False, str(e)))
        failed += 1
        errors.append(f"FastAPI emitter: {e}")

    # ------------------------------------------------------------------
    # Test 7: NestJS Emitter
    # ------------------------------------------------------------------
    try:
        emitter = NestJSGatewayEmitter()
        files = emitter.generate(collection)
        assert len(files) >= 1, f"Expected >= 1 file, got {len(files)}"
        results.append(("NestJS Emitter", True, f"{len(files)} files"))
        passed += 1
    except Exception as e:
        results.append(("NestJS Emitter", False, str(e)))
        failed += 1
        errors.append(f"NestJS emitter: {e}")

    # ------------------------------------------------------------------
    # Test 8: Angular + React Emitters
    # ------------------------------------------------------------------
    try:
        tmpdir = tempfile.mkdtemp()
        try:
            template_dir = Path(tmpdir) / "core" / "cp06_api_gateway"
            template_dir.mkdir(parents=True)
            (template_dir / "gateway.module.ts.jinja2").write_text("// gateway module")
            (template_dir / "api-client.service.ts.jinja2").write_text("// api client")
            (template_dir / "route-guard.service.ts.jinja2").write_text("// route guard")

            angular_emitter = AngularGatewayEmitter(stack_dir=template_dir.parent)
            angular_files = angular_emitter.generate(collection)
            assert len(angular_files) >= 1

            react_template_dir = Path(tmpdir) / "core" / "cp06_api_gateway"
            (react_template_dir / "api-client.ts.jinja2").write_text("// api client")
            (react_template_dir / "route-guard.tsx.jinja2").write_text("// route guard")
            (react_template_dir / "types.ts.jinja2").write_text("// types")

            react_emitter = ReactGatewayEmitter(stack_dir=react_template_dir.parent)
            react_files = react_emitter.generate(collection)
            assert len(react_files) >= 1

            results.append(("Angular + React", True, f"Angular:{len(angular_files)}, React:{len(react_files)}"))
            passed += 1
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception as e:
        results.append(("Angular + React", False, str(e)))
        failed += 1
        errors.append(f"Frontend emitters: {e}")

    # ------------------------------------------------------------------
    # Test 9: Model serialization roundtrip
    # ------------------------------------------------------------------
    try:
        route = Route(
            id="TestRoute",
            method=HttpMethod.POST,
            path="/api/test",
            auth=RouteAuthConfig(mode=AuthMode.JWT, tenant_scoped=True),
            tags=["test"],
        )
        d = route.to_dict()
        restored = Route.from_dict(d)
        assert restored.id == route.id
        assert restored.method == route.method
        assert restored.auth.tenant_scoped is True

        resolver = GraphQLResolver(
            id="TestResolver",
            operation=GraphQLOperation.MUTATION,
            field_name="createItem",
        )
        d = resolver.to_dict()
        restored = GraphQLResolver.from_dict(d)
        assert restored.operation == GraphQLOperation.MUTATION

        webhook = WebhookHandler(
            id="test_webhook",
            path="/webhooks/test",
            auth_config=WebhookAuthConfig(auth_type=WebhookAuthType.BEARER_TOKEN),
        )
        d = webhook.to_dict()
        restored = WebhookHandler.from_dict(d)
        assert restored.auth_config.auth_type == WebhookAuthType.BEARER_TOKEN

        results.append(("Model serialization", True, "Route, GraphQLResolver, WebhookHandler roundtrip OK"))
        passed += 1
    except Exception as e:
        results.append(("Model serialization", False, str(e)))
        failed += 1
        errors.append(f"Model roundtrip: {e}")

    # ------------------------------------------------------------------
    # Test 10: Template existence
    # ------------------------------------------------------------------
    try:
        stacks_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "stacks"
        required_templates = {
            "fastapi": [
                "cp06_api_gateway/__init__.py.jinja2",
                "cp06_api_gateway/circuit_breaker.py.jinja2",
                "cp06_api_gateway/gateway_app.py.jinja2",
                "cp06_api_gateway/gateway_router.py.jinja2",
                "cp06_api_gateway/gateway_service.py.jinja2",
                "cp06_api_gateway/rate_limiter.py.jinja2",
                "cp06_api_gateway/route_config.py.jinja2",
                "cp06_api_gateway/http_route.py.jinja2",
            ],
            "nestjs": [
                "cp06_api_gateway/gateway.module.ts.jinja2",
                "cp06_api_gateway/gateway.service.ts.jinja2",
                "cp06_api_gateway/gateway.controller.ts.jinja2",
                "cp06_api_gateway/circuit-breaker.providers.ts.jinja2",
                "cp06_api_gateway/rate-limiter.providers.ts.jinja2",
                "cp06_api_gateway/route-config.service.ts.jinja2",
                "cp06_api_gateway/http_route.ts.jinja2",
            ],
            "angular": [
                "cp06_api_gateway/gateway.module.ts.jinja2",
                "cp06_api_gateway/api-client.service.ts.jinja2",
                "cp06_api_gateway/route-guard.service.ts.jinja2",
            ],
            "react": [
                "cp06_api_gateway/api-client.ts.jinja2",
                "cp06_api_gateway/route-guard.tsx.jinja2",
                "cp06_api_gateway/types.ts.jinja2",
            ],
        }
        missing = []
        for stack, templates in required_templates.items():
            for t in templates:
                full = stacks_dir / stack / "core" / t
                if not full.exists():
                    missing.append(f"{stack}/{t}")
        assert not missing, f"Missing templates: {missing}"
        total = sum(len(v) for v in required_templates.values())
        results.append(("Template existence", True, f"All {total} templates exist"))
        passed += 1
    except Exception as e:
        results.append(("Template existence", False, str(e)))
        failed += 1
        errors.append(f"Template check: {e}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"CP06 E2E Result: {passed} passed, {failed} failed out of {passed + failed} tests")
    for name, ok, detail in results:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}: {detail}")
    if errors:
        print("\nFailures:")
        for e in errors:
            print(f"  - {e}")
    print("=" * 70)

    return failed == 0, results


def test_e2e():
    """pytest-compatible E2E test."""
    success, results = run_e2e()
    assert success, f"E2E test failed: {[r[2] for r in results if not r[1]]}"


if __name__ == "__main__":
    success, _ = run_e2e()
    sys.exit(0 if success else 1)