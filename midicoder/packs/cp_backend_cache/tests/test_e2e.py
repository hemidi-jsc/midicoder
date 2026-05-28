# coding: utf-8
"""
E2E integration test cho CP09 — verify pack work trong toàn bộ pipeline.

Test flow:
1. Load pack.yml từ disk
2. Load file contributions qua FileContributionsLoader
3. Parse MIR metadata → CacheCollection
4. Emit files qua FastAPICacheEmitter
5. Verify generated files đúng structure
6. Test template existence (Rule V1, V2)
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from midicoder.packs.cp_backend_cache.parser import CacheParser
from midicoder.packs.cp_backend_cache.fastapi import FastAPICacheEmitter
from midicoder.packs.cp_backend_cache.nestjs import NestJSCacheEmitter
from midicoder.packs.cp_backend_cache.angular import AngularEmitter, emit_angular_cache
from midicoder.packs.cp_backend_cache.react import ReactEmitter, emit_react_cache
from midicoder.packs.cp_backend_cache.models import (
    CacheCollection,
    CacheProfile,
    CacheBackend,
    CDNCacheLayer,
    StampedePrevention,
    StampedePreventionStrategy,
    CacheTier,
    CacheWarmupConfig,
    CacheWarmupStrategy,
    CacheStrategy,
    CacheInvalidationRule,
    InvalidationStrategy,
    CacheMetrics,
)
from midicoder.pipeline.file_contributions_loader import FileContributionsLoader
from midicoder.contracts.registry import CP_ID_TO_INTERNAL
import yaml
import tempfile
import shutil


def run_e2e():
    """Chạy E2E test cho CP09."""
    passed = 0
    failed = 0
    errors = []

    results = []

    # ------------------------------------------------------------------
    # Test 1: Pack registry
    # ------------------------------------------------------------------
    try:
        assert "CP09" in CP_ID_TO_INTERNAL, "CP09 not in CP_ID_TO_INTERNAL"
        assert CP_ID_TO_INTERNAL["CP09"] == "cp_backend_cache", f"Wrong mapping: {CP_ID_TO_INTERNAL['CP09']}"
        results.append(("Pack registry", True, "CP09 → cp_backend_cache registered"))
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
        assert pack["id"] == "CP09"
        assert pack["internal_id"] == "cp_backend_cache"
        assert pack["version"] == "1.1.0"
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
        fc = loader.load(pack_internal_id="cp_backend_cache", pack_id="CP09", stack="fastapi")
        assert not fc.is_empty, "No file contributions loaded for CP09"
        assert len(fc.infrastructure) > 0, "No infrastructure files"
        infra_paths = [f.path for f in fc.infrastructure]
        assert any("redis.py" in p for p in infra_paths), "redis.py not in infrastructure"
        assert any("cache_strategy.py" in p for p in infra_paths), "cache_strategy.py not in infrastructure"
        results.append(("FileContributionsLoader", True, f"{len(fc.infrastructure)} infra files"))
        passed += 1
    except Exception as e:
        results.append(("FileContributionsLoader", False, str(e)))
        failed += 1
        errors.append(f"FileContributionsLoader: {e}")

    # ------------------------------------------------------------------
    # Test 4: Parse MIR metadata → CacheCollection
    # ------------------------------------------------------------------
    try:
        parser = CacheParser()
        mir_metadata = {
            "cache_profiles": [
                {"id": "default_cache", "backend": "redis", "ttl": 300},
                {"id": "session_cache", "backend": "memory", "ttl": 60},
            ],
            "strategies": [{"profile_id": "default_cache", "strategy_type": "read_through", "load_from": "db"}],
            "invalidation_rules": [{"profile_id": "default_cache", "pattern": "*", "strategy": "pattern"}],
            "cdn_layers": [{"provider": "cloudflare", "zone_id": "z123", "default_ttl": 7200}],
            "stampede_prevention": {"enabled": True, "strategy": "mutex", "lock_ttl": 15},
            "tiers": [
                {"tier_name": "l1", "tier_order": 1, "backend": "memory", "max_size": 1000, "ttl": 60},
                {"tier_name": "l2", "tier_order": 2, "backend": "redis", "max_size": 50000, "ttl": 300},
            ],
            "warmup_config": {"strategy": "on_startup", "warmup_keys": ["popular:1", "popular:2"], "parallelism": 4},
        }
        collection = parser.parse_from_metadata(mir_metadata)
        assert collection.total_count == 2
        assert len(collection.cdn_layers) == 1
        assert collection.stampede_prevention is not None
        assert len(collection.tiers) == 2
        assert collection.warmup_config is not None
        results.append(("Parse MIR metadata", True, f"{collection.total_count} profiles, CDN, stampede, tiers, warmup"))
        passed += 1
    except Exception as e:
        results.append(("Parse MIR metadata", False, str(e)))
        failed += 1
        errors.append(f"Parse MIR: {e}")

    # ------------------------------------------------------------------
    # Test 5: FastAPI Emitter
    # ------------------------------------------------------------------
    try:
        emitter = FastAPICacheEmitter()
        files = emitter.generate(collection)
        assert len(files) >= 8, f"Expected >= 8 files, got {len(files)}"
        assert "cache/redis.py" in files
        assert "cache/cache_strategy.py" in files
        assert "cache/cdn_cache.py" in files
        assert "cache/stampede_prevention.py" in files
        assert "cache/cache_warmup.py" in files
        assert "cache/multi_tier.py" in files
        for path, content in files.items():
            assert "from midicoder" not in content, f"Rule V1 violation in {path}"
        results.append(("FastAPI Emitter", True, f"{len(files)} files, Rule V1/V2 passed"))
        passed += 1
    except Exception as e:
        results.append(("FastAPI Emitter", False, str(e)))
        failed += 1
        errors.append(f"FastAPI emitter: {e}")

    # ------------------------------------------------------------------
    # Test 6: NestJS Emitter
    # ------------------------------------------------------------------
    try:
        emitter = NestJSCacheEmitter()
        files = emitter.generate(collection)
        assert len(files) >= 3
        assert "cache/cache.module.ts" in files
        assert "cache/cache.service.ts" in files
        assert "cache/cache.interceptor.ts" in files
        results.append(("NestJS Emitter", True, f"{len(files)} files"))
        passed += 1
    except Exception as e:
        results.append(("NestJS Emitter", False, str(e)))
        failed += 1
        errors.append(f"NestJS emitter: {e}")

    # ------------------------------------------------------------------
    # Test 7: Angular + React Emitters
    # ------------------------------------------------------------------
    try:
        tmpdir = tempfile.mkdtemp()
        try:
            angular_files = emit_angular_cache(collection, Path("."), Path(tmpdir))
            assert len(angular_files) >= 3
            react_files = emit_react_cache(collection, Path("."), Path(tmpdir))
            assert len(react_files) >= 3
            results.append(("Angular + React", True, f"Angular:{len(angular_files)}, React:{len(react_files)}"))
            passed += 1
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception as e:
        results.append(("Angular + React", False, str(e)))
        failed += 1
        errors.append(f"Frontend emitters: {e}")

    # ------------------------------------------------------------------
    # Test 8: Template existence
    # ------------------------------------------------------------------
    try:
        stacks_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "stacks"
        required_templates = {
            "fastapi": ["cp_backend_cache/redis.py.jinja2", "cp_backend_cache/cache_decorators.py.jinja2",
                        "cp_backend_cache/cache_invalidate.py.jinja2", "cp_backend_cache/cache_strategy.py.jinja2",
                        "cp_backend_cache/cdn_cache.py.jinja2", "cp_backend_cache/stampede_prevention.py.jinja2",
                        "cp_backend_cache/cache_warmup.py.jinja2"],
            "nestjs": ["cp_backend_cache/redis.module.ts.jinja2", "cp_backend_cache/cache.interceptor.ts.jinja2",
                        "cp_backend_cache/cdn_cache.ts.jinja2", "cp_backend_cache/stampede_prevention.ts.jinja2",
                        "cp_backend_cache/cache_warmup.ts.jinja2", "cp_backend_cache/multi_tier.ts.jinja2"],
            "angular": ["cp_backend_cache/cache.module.ts.jinja2", "cp_backend_cache/cache.service.ts.jinja2",
                        "cp_backend_cache/cache.interceptor.ts.jinja2"],
            "react": ["cp_backend_cache/CacheProvider.tsx.jinja2", "cp_backend_cache/useCache.ts.jinja2",
                      "cp_backend_cache/cache-utils.ts.jinja2"],
        }
        missing = []
        for stack, templates in required_templates.items():
            for t in templates:
                full = stacks_dir / stack / "core" / t
                if not full.exists():
                    missing.append(str(full))
        assert not missing, f"Missing: {missing}"
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
    print(f"CP09 E2E Result: {passed} passed, {failed} failed out of {passed + failed} tests")
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
