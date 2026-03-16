# Feedback và sửa Contracts

Midi Coder hỗ trợ vòng lặp feedback để cải thiện contracts mà không cần sửa tay toàn bộ.

## Tạo feedback file

```bash
midicoder contract feedback
```

Tạo `.midicoder/versions/<ver>/contract-feedbacks.yml` với template chuẩn.

## Prepare (chỉ validate)

```bash
midicoder contract repair prepare
```

Validate feedback và references mà không chạy LLM.

## Run repair

```bash
midicoder contract repair run
```

Việc này sẽ:

- Áp dụng sửa đổi lên các file contract YAML.
- Đồng bộ `master-brief.md`.
- Trích memo ngắn vào `.midicoder/context/memos/`.
- Cập nhật trạng thái từng feedback item.

## Trường trong feedback

- `id`
- `file`
- `location`
- `status`
- `issue`
- `suggestion`
- `last_error`
