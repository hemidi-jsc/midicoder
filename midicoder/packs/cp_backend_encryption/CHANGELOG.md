# Changelog — CP58 Data Encryption at Rest

## 1.0.0 (2026-05-26)

### Added

- **Data Encryption at Rest** — Mã hóa dữ liệu lưu trữ với nhiều thuật toán và key management providers
- **3 Encryption Algorithms**: AES256_GCM, ChaCha20, RSA4096
- **5 Key Management Types**: local, AWS KMS, GCP KMS, Azure Key Vault, HashiCorp Vault
- **EncryptionConfig** — Cấu hình mã hóa tổng thể (thuật toán, key_size, mode, key_management)
- **EncryptedField** — Mã hóa từng field với auto encrypt/decrypt
- **EncryptionKey** — Quản lý vòng đời khóa (active → rotating → retired)
- **EncryptionPolicy** — Chính sách mã hóa với compliance standards (HIPAA, SOX, PCI-DSS)
- **12 Jinja2 Templates** (6 files × 2 stacks: FastAPI, NestJS)
- **6 Error Codes** (MDC-CP58-001 ~ MDC-CP58-006)
- **4 Recipes**: aes256_field_encryption_recipe, table_encryption_recipe, key_rotation_recipe, compliance_encryption_recipe
- **Registry Integration** — CP58 registered trong contracts/registry.py

### Dependencies

- CP01 (Domain Model)
- CP08 (Database)
- CP14 (Audit Trail & Compliance)
