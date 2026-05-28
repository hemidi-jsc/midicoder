# Changelog — I05 Multi-Region & Geo-Replication

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-05-28

- Migrate to taxonomy-v2: I05 cp_infra_multi_region
- Add `type: infra`, `render_context_support: true`
- Update depends_on: `["I02"]` only (removed 6 unnecessary deps: CP02, CP06, CP08, CP14, CP15, CP56)
- Template path update: `cp28_multi_region` → `cp_infra_multi_region`
- Import path update: `midicoder.packs.cp28_multi_region` → `midicoder.packs.cp_infra_multi_region`
- Emitter path update: `cp28.multi_region.infrastructure` → `cp_infra_multi_region.multi_region.infrastructure`
- Stack directory rename: `stacks/infrastructure/cp28_multi_region` → `stacks/infrastructure/cp_infra_multi_region`
- Update emitter template_dir references to `cp_infra_multi_region`
- Preserved 5 infrastructure Jinja2 templates (multi-region, multi-cluster dirs)

## [Unreleased]

### Added

- **Multi-Region & Geo-Replication** — Triển khai workload đa region trên cloud
- **RegionConfig** — Region với cloud provider, availability zones, endpoint
- **ReplicationPolicy** — Replication cross-region (sync/async) với conflict resolution
- **GeoRoutingRule** — Routing dựa trên độ trễ hoặc vị trí địa lý
- **FailoverPolicy** — Failover tự động với RTO/RPO
- **DataResidencyRule** — Data residency per region/tenant theo regulation
- **RegionHealthCheck** — Health check per region với auto-failover
- **5 Infrastructure Templates**: deployment, route53, failover-lambda, vpc-peering, multi-cluster-k8s
- **3 Recipes**: basic_multi_region_recipe, full_geo_replication_recipe, data_residency_recipe
- **3 Emitter Classes**: FastAPIMultiRegionEmitter, NestJSMultiRegionEmitter, MultiRegionInfrastructureEmitter

## [1.0.0] - 2026-05-26

### Added

- Initial release as CP28

---

**Capabilities Provided:** `multi_region_deploy`, `cross_region_replication`, `latency_based_routing`, `failover_management`, `data_residency_enforce`, `geo_health_check`

**Obligations:**

1. **FailoverPlanRequired** — Mọi multi-region deployment phải có failover plan với RTO/RPO xác định
2. **DataResidencyEnforced** — Data residency rules phải được enforce để đảm bảo compliance với GDPR/CCPA

**Dependencies:** I02
