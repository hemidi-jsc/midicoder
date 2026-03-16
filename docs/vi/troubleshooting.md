# Xử lý sự cố

## Init lỗi hoặc thiếu config

- Chạy lại `midicoder init` và kiểm tra `working_dir`.
- Đảm bảo `.midicoder/` tồn tại và có quyền ghi.

## Contract generation lỗi

- Kiểm tra `master-brief.md` có đủ phần.
- Sửa lỗi schema rồi chạy lại `midicoder contract gen`.
- Dùng `midicoder contract gen resume` để tiếp tục.

## IR build lỗi

- Sửa lỗi validate contracts trước khi tiếp tục.
- Kiểm tra cross-reference giữa domain, app, policy, workflows.

## Code gen ra patch không như mong muốn

- Chạy lại `midicoder index` để cập nhật Project Context.
- Kiểm tra `profile.json` có đúng stack.
- Kiểm tra `plans/index.json` và các code-plan liên quan.

## Code apply lỗi

- Đảm bảo patch plans nằm trong `.midicoder/versions/<ver>/patches/plans/`.
- Kiểm tra anchor bị thiếu hoặc file đã thay đổi.
- Xem snapshot và unified diff để xử lý conflict.
