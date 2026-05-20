# CP23: Testing Framework Generator — Changelog

## 1.0.0 (2026-05-20)

### Thêm mới

- Models: `TestType`, `TestFramework`, `AssertionCheck`, `TestAssertion`, `TestStep`, `TestCase`, `TestPolicy`, `TestSuite`, `TestCollection`
- Parser: `TestParser` — parse DSL test nodes từ Contract YAML / MIR metadata
- Recipes: Auto-generate test cases từ MIR metadata (entities, commands, queries)
- Stack emitters:
  - FastAPI: pytest (`conftest.py`, `pytest.ini`, unit/integration/e2e templates)
  - NestJS: Jest (`jest.config.ts`, entity/command/query/integration/e2e templates)
  - Angular: Karma/Jest (`karma.conf.js`, component/service/e2e templates)
  - React: Jest (`jest.config.js`, component/hook/e2e templates)
- Error codes: `MDC-CP23-001` đến `MDC-CP23-010`
- Tích hợp: `"CP23": "cp23_testing_framework"` trong `contracts/registry.py`
