# CP54: Kubernetes & Cloud Native Deployment — Changelog

## 1.0.0 (2026-05-26)

- Initial release
- Thêm K8sDeployment, K8sService, K8sIngress, K8sHPA, K8sConfigMap, K8sSecret, K8sPersistentVolume models
- Thêm K8sIR parser với from_dict và parse_to_ir
- Thêm 3 recipes: basic_deployment, full_stack, helm_chart
- Thêm infrastructure emitter với Jinja2 templates
- Thêm FastAPI và NestJS backend-specific emitters
- Thêm NodeKind cho DSL: K8S_DEPLOYMENT, K8S_SERVICE, K8S_INGRESS, K8S_HPA, HELM_CHART
- Thêm DSL loader cho kubernetes.yaml
