# FAQ

## Does Midi Coder rewrite my files directly

No. LLMs only generate DSL or plans. The CLI applies patch plans with explicit operations.

## Can I target multiple stacks

Yes. `stack` in `config.json` supports multiple targets such as `fastapi`, `nest`, and `angular`.

## Is the pipeline deterministic

Yes. Contract compilation and code planning are deterministic and validated by schema and lint rules.

## Where are artifacts stored

All artifacts are stored under `.midicoder/` in the repo root.

## How do I recover from a failed contract generation

Use `midicoder contract gen resume` to continue from the last failed run.
