"""
Prompt Templates cho Midicoder Pipeline.

Mỗi file .md trong thư mục này là một prompt template
được sử dụng cho các LLM calls khác nhau.

Lý do: Tách prompt ra file riêng để:
- Dễ dàng benchmark hiệu suất của từng prompt
- Theo dõi phiên bản prompt qua git
- Tinh chỉnh prompt mà không cần re-compile code

Sử dụng:
    from midicoder.pipeline.prompts import load_prompt

    # Load system prompt cho một category
    system_prompt = load_prompt("contract_entities")

    # Load repair prompt
    repair_prompt = load_prompt("contract_repair")
"""

from __future__ import annotations

from pathlib import Path

# Đường dẫn đến thư mục prompts
_PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """
    Load prompt template từ file Markdown.

    Args:
        name: Tên prompt (không có phần mở rộng .md).
            Ví dụ: "contract_entities", "contract_repair"

    Returns:
        Nội dung prompt (string)

    Raises:
        FileNotFoundError: Nếu file prompt không tồn tại
    """
    prompt_path = _PROMPTS_DIR / f"{name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy prompt template: {prompt_path.name}\n"
            f"Kiểm tra trong: {_PROMPTS_DIR}"
        )

    return prompt_path.read_text(encoding="utf-8").strip()


def list_available_prompts() -> list[str]:
    """
    Lấy danh sách tất cả prompt templates có sẵn.

    Returns:
        List các tên prompt (không có phần mở rộng .md)
    """
    return [
        f.stem for f in _PROMPTS_DIR.glob("*.md")
        if f.is_file()
    ]


__all__ = ["load_prompt", "list_available_prompts"]