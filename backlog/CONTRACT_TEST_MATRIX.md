# Contract Test Matrix - Midicoder v1.0.0

## Overview

This document outlines the comprehensive test matrix for Midicoder contracts, aligned with 20 industry briefs and 100 industry capabilities.

**Current Status:** 296 tests completed | **Target:** ~500 tests

---

## Part 1: Completed Test Files ✅

| File | Tests | Status | Coverage |
|------|-------|--------|----------|
| `test_capability_validation.py` | 36 | ✅ Passed | Capability validators |
| `test_core_capabilities.py` | 52 | ✅ Passed | 16 core capabilities |
| `test_macro_capabilities.py` | 94 | ✅ Passed | 50+ macro capabilities |
| `test_graph.py` | 33 | ✅ Passed | CapabilityGraph, MIR |
| `test_mir.py` | 28 | ✅ Passed | MIR classes |
| `test_validation.py` | 25 | ✅ Passed | Validation reports |
| `test_expansion.py` | 45 | ✅ Passed | Expansion traces |
| `test_artifact.py` | 64 | ✅ Passed | Artifact contracts |
| **TOTAL** | **377** | ✅ | Base contracts |

---

## Part 2: Remaining Test Files (Pending)

### 2.1 File: artifact.py

**Classes & Functions:**
| Name | Type | Est. Tests | Priority |
|------|------|------------|----------|
| `ArtifactVersion` | dataclass | 12 | P0 |
| `ArtifactMetadata` | dataclass | 16 | P0 |
| `ArtifactBase` | base class | 10 | P0 |
| `write_artifact()` | function | 8 | P0 |
| `read_artifact()` | function | 6 | P0 |
| `compute_content_hash()` | function | 6 | P1 |
| `compute_file_hash()` | function | 6 | P1 |

**Test Categories:**
- Constructor tests (12): Default values, custom values, edge cases
- Serialization tests (16): to_dict, from_dict, round-trip
- Validation tests (4): Metadata validation
- Integration tests (8): File I/O operations
- Edge case tests (10): Empty strings, None values, special characters

**Total: 64 tests**

---

### 2.2 File: blueprint_compiler.py

**Classes & Functions:**
| Name | Type | Est. Tests | Priority |
|------|------|------------|----------|
| `BlueprintMetadata` | dataclass | 10 | P0 |
| `IndustryInfo` | dataclass | 10 | P0 |
| `CorePacksConfig` | dataclass | 12 | P0 |
| `DomainPackRef` | dataclass | 8 | P1 |
| `RegulatoryOverlayRef` | dataclass | 8 | P1 |
| `BusinessInvariant` | dataclass | 10 | P0 |
| `ComplianceInvariant` | dataclass | 8 | P0 |
| `FailureMode` | dataclass | 8 | P1 |
| `BlueprintSpecification` | dataclass | 15 | P0 |
| `BlueprintCompiler` | class | 20 | P0 |

**Test Categories:**
- Blueprint validation tests
- Industry-specific invariant tests
- Compliance invariant tests
- Compiler pipeline tests
- Round-trip serialization

**Total: ~109 tests**

---

### 2.3 File: capability_params.py

**Classes & Functions:**
| Name | Type | Est. Tests | Priority |
|------|------|------------|----------|
| `BaseCapabilityParams` | base | 8 | P0 |
| `AuthorizedMutationParams` | dataclass | 12 | P0 |
| `AuthorizedQueryParams` | dataclass | 12 | P0 |
| `EventHandlerParams` | dataclass | 10 | P0 |
| `ScheduledTaskParams` | dataclass | 10 | P0 |
| `WorkflowDefinitionParams` | dataclass | 12 | P0 |
| `OutboundIntegrationParams` | dataclass | 10 | P1 |
| `InboundIntegrationParams` | dataclass | 10 | P1 |
| `RateLimitingParams` | dataclass | 8 | P1 |
| `CacheStrategyParams` | dataclass | 8 | P1 |
| `MonitoringParams` | dataclass | 8 | P1 |
| All params types combined | - | 15 | P2 |

**Test Categories:**
- Schema validation tests
- Default value tests
- Constraint enforcement tests
- Integration with validators

**Total: ~133 tests**

---

### 2.4 File: capability_validator.py

**Classes & Functions:**
| Name | Type | Est. Tests | Priority |
|------|------|------------|----------|
| `CapabilityValidator` base | class | 10 | P0 |
| `AuthorizedMutationValidator` | class | 15 | P0 |
| `AuthorizedQueryValidator` | class | 12 | P0 |
| `EventHandlerValidator` | class | 10 | P0 |
| `ScheduledTaskValidator` | class | 10 | P0 |
| `WorkflowValidator` | class | 12 | P0 |
| `IntegrationValidator` | class | 10 | P1 |
| `ValidatorRegistry` | class | 10 | P0 |
| `validate_capability()` | function | 15 | P0 |
| `get_validator()` | function | 8 | P0 |

**Test Categories:**
- Validation logic tests
- Error message tests
- Edge case tests
- Registry operations

**Total: ~112 tests**

---

### 2.5 File: plan.py

**Classes & Functions:**
| Name | Type | Est. Tests | Priority |
|------|------|------------|----------|
| `SurfacePlan` | dataclass | 15 | P0 |
| `TargetPlan` | dataclass | 15 | P0 |
| `PatchPlan` | dataclass | 15 | P0 |
| `FileEdit` | dataclass | 10 | P1 |
| `CodeBlock` | dataclass | 8 | P1 |
| `PlanStep` | dataclass | 10 | P1 |
| `DiffHunk` | dataclass | 8 | P1 |
| Plan validation | - | 12 | P0 |
| Plan serialization | - | 10 | P0 |

**Test Categories:**
- Plan structure tests
- File edit tests
- Diff generation tests
- Plan validation tests

**Total: ~103 tests**

---

## Summary

| Category | Files | Est. Tests | Priority |
|----------|-------|------------|----------|
| Completed | 7 | 296 | ✅ |
| Pending | 5 | ~521 | P0-P2 |
| **TOTAL** | **12** | **~817** | - |

---

## Gap Analysis (from Subagent Review)

### Critical Gaps Identified:

1. **Real-time/streaming capabilities** - Missing in capability_params.py
   - Required by: Food Delivery, Exchange Trading, Telehealth
   - Recommendation: Add `StreamCapabilityParams`, `WebSocketParams`

2. **Payment processing capabilities** - Limited coverage
   - Required by: E-commerce, Marketplace, Food Delivery
   - Recommendation: Expand `OutboundIntegrationParams` for payment gateways

3. **Geospatial capabilities** - Missing
   - Required by: Food Delivery, Last Mile Delivery, Warehouse
   - Recommendation: Add `GeospatialParams` for location-based queries

4. **Workflow state machines** - Partial coverage
   - Required by: All 20 briefs
   - Recommendation: Enhance `WorkflowDefinitionParams` with state machine support

5. **Audit trail enforcement** - Gap in validator
   - Required by: Banking, Healthcare, ERP
   - Recommendation: Add `AuditEnforcementValidator`

6. **Multi-tenancy edge cases** - Partial coverage
   - Required by: All SaaS briefs (16/20)
   - Recommendation: Add `TenantIsolationValidator`

---

## Implementation Priority

### P0 (Critical - Implement First):
1. artifact.py tests (64 tests)
2. capability_validator.py core validators (77 tests)
3. plan.py core plans (45 tests)
4. blueprint_compiler.py core (45 tests)

### P1 (Important):
1. capability_params.py extended params (54 tests)
2. blueprint_compiler.py invariants (42 tests)
3. plan.py file edits (36 tests)

### P2 (Nice to Have):
1. All remaining edge case tests
2. Integration tests across modules
3. Performance tests

---

## Next Steps

1. [ ] Implement `test_artifact.py` - 64 tests (P0)
2. [ ] Implement `test_blueprint_compiler.py` - 109 tests (P0+P1)
3. [ ] Implement `test_capability_params.py` - 133 tests (P0+P1)
4. [ ] Implement `test_capability_validator.py` - 112 tests (P0+P1)
5. [ ] Implement `test_plan.py` - 103 tests (P0+P1)
6. [ ] Address critical gaps in contract design
7. [ ] Run comprehensive validation against all 20 briefs

---

## References

- Source of Truth: `backlog/requirement.md`
- Industry Briefs: `industry/briefs/` (20 files)
- Taxonomy: `industry/taxonomy.yml`
- Priority: `industry/priority-top20.yml`