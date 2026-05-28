# Changelog — I04 Environment & Secret Management

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-05-28

- Migrate to taxonomy-v2: I04 cp_infra_env_secrets
- Add `type: infra`, `render_context_support: true`
- Update depends_on: `["B01", "I01", "F14"]` (removed CP48 bidirectional dep)
- Template path update: `cp56_env_secrets` → `cp_infra_env_secrets`
- Import path update: `midicoder.packs.cp56_env_secrets` → `midicoder.packs.cp_infra_env_secrets`
- Rename k8s output: `k8s/secret.yaml` → `k8s/app-secret.yaml` (resolve CP54 path conflict)
- Update emitter template_dir references to `cp_infra_env_secrets`
- Create empty stack directories: fastapi, nestjs, infrastructure (no templates exist on disk)

## [Unreleased]

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
- **3 Emitter Classes**: FastAPIEnvEmitter, NestJSSEnvEmitter, EnvInfrastructureEmitter

## [1.0.0] - 2026-05-26

### Added

- Initial release as CP56

---

**Capabilities Provided:** `env_config`, `secret_management`, `vault_integration`, `kms_integration`, `configmap_ref`

**Obligations:**

1. **SecretEncryption** — Mọi secret phải được mã hóa khi lưu trữ (at-rest)
2. **EnvIsolation** — Biến môi trường phải được cách ly theo môi trường (dev/staging/prod)

**Dependencies:** B01, I01, F14
