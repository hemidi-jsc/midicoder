# Hỏi đáp

## Midi Coder có viết đè file trực tiếp không

Không. LLM chỉ sinh DSL hoặc plan. CLI apply patch theo operation rõ ràng.

## Có thể target nhiều stack không

Có. `stack` trong `config.json` có thể chứa `fastapi`, `nest`, `angular`.

## Pipeline có deterministic không

Có. Các bước compile và code planning là deterministic và luôn qua validation.

## Artifacts nằm ở đâu

Toàn bộ nằm trong `.midicoder/` ở root repo.

## Khôi phục khi contract gen bị lỗi

Dùng `midicoder contract gen resume` để tiếp tục.
