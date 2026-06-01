# UAT Briefs Index — CP B01: Domain Model DSL & IR Builder

> Format: I/O briefs — mỗi brief là 1 use case thực tế với DSL input + expected output verification.
> Total: 12 capabilities × 20 briefs = 240 briefs

| # | Capability | File | Briefs |
|---|-----------|------|--------|
| 1 | `entity_modeling` | [entity_modeling.md](entity_modeling.md) | 20 |
| 2 | `command_query_separation` | [command_query_separation.md](command_query_separation.md) | 20 |
| 3 | `value_object` | [value_object.md](value_object.md) | 20 |
| 4 | `aggregate_root` | [aggregate_root.md](aggregate_root.md) | 20 |
| 5 | `domain_events` | [domain_events.md](domain_events.md) | 20 |
| 6 | `cqrs_projection` | [cqrs_projection.md](cqrs_projection.md) | 20 |
| 7 | `event_sourcing` | [event_sourcing.md](event_sourcing.md) | 20 |
| 8 | `temporal_entity` | [temporal_entity.md](temporal_entity.md) | 20 |
| 9 | `polymorphic_entity` | [polymorphic_entity.md](polymorphic_entity.md) | 20 |
| 10 | `saga` | [saga.md](saga.md) | 20 |
| 11 | `recipes` | [recipes.md](recipes.md) | 20 |
| 12 | `global_error_handler` | [global_error_handler.md](global_error_handler.md) | 20 |

## Brief Format

```yaml
---
id: B01-{CAP_SHORT}-{NN}
capability: {capability_id}
stack: fastapi | nestjs | both
---
**Use Case:** {description}
**Input DSL:**
```yaml
{minimal YAML DSL}
```
**Expected Output:**
- File: `{file_path}`
- Contains: `{pattern_or_content}`
```

## Capabilities Covered

1. **Entity Modeling** — CRUD entities with fields, types, relationships, constraints, indexes, lifecycle hooks
2. **Command-Query Separation** — Commands with guards/effects/transactions, Queries with filters/pagination/projection
3. **Value Object** — Immutable, equality-by-value domain primitives with inheritance and computed fields
4. **Aggregate Root** — Consistency boundaries with strict/eventual/relaxed levels
5. **Domain Events** — Fact/Intention/StateChange events with publishing
6. **CQRS Projection** — Read models derived from domain events
7. **Event Sourcing** — Aggregates that reconstruct state from event log with snapshots
8. **Temporal Entity** — SCD Type 2 with valid_from/valid_to time-bounded state
9. **Polymorphic Entity** — STI/CTI/JTI subtype inheritance with discriminator
10. **Saga** — Long-running transactions with compensating steps
11. **Recipes** — Common patterns (SimpleEntity, AggregateRoot, CQRS, etc.)
12. **Global Error Handler** — Exception mapping, logging, notification
