# Changelog — CP52 Invariant Gate Framework

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-12

### Added

- **Models**: Invariant, GateRule, ViolationReport
- **FastAPI Emitter**: Invariant checker, gate evaluator
- **Capability Modules**: invariant_checker, gate_evaluator

---

**Capabilities Provided:** `enforce_invariant`, `gate_check`

**Capabilities (Runtime):** `invariant_checker`, `gate_evaluator`

**Obligations:**

1. **InvariantCompleteness** — All P0 invariants must be evaluated before blueprint emission (MDC-CP52-001)
2. **GateFailFast** — Gate failure must halt pipeline immediately (MDC-CP52-002)

**Dependencies:** CP51
