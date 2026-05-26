# Changelog — CP56 Environment & Secret Management

## 1.0.0 (2026-05-26)

### Added

- **Environment & Secret Management** — Quản lý biến môi trường và secret
- **3 Environment Types**: dev, staging, prod
- **4 Secret Types**: vault, aws_kms, gcp_kms, local
- **EnvConfig** — Cấu hình biến môi trường theo môi trường
- **SecretConfig** — Cấu hình secret (Vault, KMS, local)
- **VaultConfig** — HashiCorp Vault với KV v2 engine và Kubernetes auto-auth
- **KMSConfig** — AWS/GCP/Azure KMS với envelope encryption
- **ConfigMapRef** — Tham chiếu Kubernetes ConfigMap
- **Vault Policy** — HCL policy file cho Vault permissions
- **Vault Setup Script** — Shell script để setup Vault
- **Kubernetes Secret** — YAML manifest cho K8s secret
- **10 Jinja2 Templates** (FastAPI, NestJS, Infrastructure)
- **10 Error Codes** (MDC-CP56-001 ~ MDC-CP56-010)
- **4 Recipes**: dev_env_recipe, prod_env_recipe, vault_recipe, aws_kms_recipe
- **Registry Integration** — CP56 registered trong contracts/registry.py
- **3 Emitter Classes**: FastAPIEnvEmitter, NestJSSEnvEmitter, EnvInfrastructureEmitter

### Dependencies

- CP01 (Domain Model)
- CP07 (Infrastructure as Code)
- CP14 (Audit Trail & Compliance)
