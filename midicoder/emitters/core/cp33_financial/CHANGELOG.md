# CP33 — Financial Engine

## Version 1.0.0 (stable)

- Thêm error codes `MDC-CP33-001` đến `MDC-CP33-015`
- Tạo models: `Currency`, `FXRate`, `Account`, `LedgerEntry`, `FinancialTransaction`, `RoundingRule`, `LedgerSnapshot`
- Tạo enums: `Currency`, `AccountType`, `EntryType`, `TransactionType`, `TransactionStatus`, `RoundingMode`
- Tạo `FinancialParser`: parse YAML/dict → typed dataclasses (7 parse methods + 6 list parse methods)
- Tạo `MultiCurrencyCalculator`: arithmetic với base currency conversion
- Tạo `FXRateService`: rate lookup, cross-rate qua base currency, add/find active rate
- Tạo `LedgerService`: double-entry ledger với immutable hash chain + tenant scoping
- Tạo `RoundingService`: ISO 4217 rounding rules (half_up, half_even, floor, ceiling)
- FastAPI emitter + 4 templates
- NestJS emitter + 4 templates
- Angular emitter + 2 templates
- React emitter + 2 templates
- 200/200 unit tests PASS (93% coverage)
- Register trong `CP_ID_TO_INTERNAL`
- Taxonomy: `status: planned → stable`
