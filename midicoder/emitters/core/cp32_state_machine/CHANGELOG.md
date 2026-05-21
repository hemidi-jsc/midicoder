# CP32 — State Machine Engine

## Version 1.1.0 (stable)

- Thêm error codes `MDC-CP32-001` đến `MDC-CP32-006`
- Tạo models: `StateMachineDefinition`, `StateInstance`, `TransitionRecord`, `TransitionResult`, `TransitionAction`
- Tạo `StateMachineEngine`: runtime validate/transition với audit (CP14) và event (CP05)
- Tạo `StateMachineParser`: parse YAML/dict → `StateMachineDefinition`
- FastAPI emitter + 2 templates
- NestJS emitter + 2 templates
- 54/54 unit tests PASS
- Register trong `CP_ID_TO_INTERNAL`
