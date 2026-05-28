# I02: Kubernetes & Cloud Native Deployment (cp_infra_kubernetes) — Changelog

## 2.0.0 (2026-05-28)

- **Migrated from CP54 to I02**: Renamed from `cp54_kubernetes` to `cp_infra_kubernetes` (taxonomy-v2)
- **Pack ID**: `CP54` → `I02`
- **Internal ID**: `cp54_kubernetes` → `cp_infra_kubernetes`
- **Error codes**: `MDC-CP54-*` → `MDC-I02-*`
- **Template paths**: Updated from `k8s/` → `cp_infra_kubernetes/k8s/`, `helm/` → `cp_infra_kubernetes/helm/`
- **Pack emitters**: Updated from `cp54.kubernetes.*` → `cp_infra_kubernetes.*`
- **Dependencies**: `[CP01, CP07, CP08]` → `[B01, I01, BE01]`
- Added `render_context_support: true` and `type: infra` fields

## 1.0.0 (2026-05-26)

- Initial release
- Thêm K8sDeployment, K8sService, K8sIngress, K8sHPA, K8sConfigMap, K8sSecret, K8sPersistentVolume models
- Thêm K8sIR parser với from_dict và parse_to_ir
- Thêm 3 recipes: basic_deployment, full_stack, helm_chart
- Thêm infrastructure emitter với Jinja2 templates
- Thêm FastAPI và NestJS backend-specific emitters
- Thêm NodeKind cho DSL: K8S_DEPLOYMENT, K8S_SERVICE, K8S_INGRESS, K8S_HPA, HELM_CHART
- Thêm DSL loader cho kubernetes.yaml
