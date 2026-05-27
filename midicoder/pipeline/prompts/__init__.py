"""
Prompt Templates cho Midicoder Pipeline.

Mỗi file .md trong thư mục này là một prompt template
được sử dụng cho các LLM calls khác nhau.

Lý do: Tách prompt ra file riêng để:
- Dễ dàng benchmark hiệu suất của từng prompt
- Theo dõi phiên bản prompt qua git
- Tinh chỉnh prompt mà không cần re-compile code

Cấu trúc:
    prompts/
    ├── contract_entities.md          # Generic contract prompts
    ├── default-brief-analyze.md      # Default brief prompt
    ├── ecommerce/                    # Domain-specific prompts
    │   ├── brief-analyze.md
    │   └── brief-clarify.md
    ├── healthcare/
    │   └── brief-analyze.md
    └── ...

Sử dụng:
    from midicoder.pipeline.prompts import load_prompt

    # Load generic prompt
    system_prompt = load_prompt("contract_entities")

    # Load domain-specific prompt (subfolder)
    analyze_prompt = load_prompt("ecommerce/brief-analyze")

    # List available prompts
    prompts = list_available_prompts()
"""

from __future__ import annotations

from pathlib import Path

# Đường dẫn đến thư mục prompts
_PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """
    Load prompt template từ file Markdown.

    Supports:
    - Flat names: "contract_entities" → prompts/contract_entities.md
    - Subfolder names: "ecommerce/brief-analyze" → prompts/ecommerce/brief-analyze.md
    - Dot names: "ecommerce.brief-analyze" → prompts/ecommerce/brief-analyze.md

    Args:
        name: Tên prompt (không có phần mở rộng .md).
            Ví dụ: "contract_entities", "ecommerce/brief-analyze"

    Returns:
        Nội dung prompt (string)

    Raises:
        FileNotFoundError: Nếu file prompt không tồn tại
    """
    # Support cả "/" và "." làm separator cho subfolder
    safe_name = name.replace(".", "/")

    # Build path — nếu có separator thì là subfolder, nếu không thì flat
    prompt_path = _PROMPTS_DIR / (safe_name + ".md")

    if not prompt_path.exists():
        # Fallback: try without subfolder (legacy)
        fallback = _PROMPTS_DIR / f"{name}.md"
        if fallback.exists():
            prompt_path = fallback
        else:
            raise FileNotFoundError(
                f"Không tìm thấy prompt template: {name}\n"
                f"Đã thử: {prompt_path}\n"
                f"Kiểm tra trong: {_PROMPTS_DIR}"
            )

    return prompt_path.read_text(encoding="utf-8").strip()


def list_available_prompts(include_subdirs: bool = True) -> list[str]:
    """
    Lấy danh sách tất cả prompt templates có sẵn.

    Args:
        include_subdirs: Nếu True, bao gồm prompts trong subfolder (vd: "ecommerce/brief-analyze")

    Returns:
        List các tên prompt (không có phần mở rộng .md)
    """
    prompts: list[str] = []

    # Flat files (root level)
    for f in _PROMPTS_DIR.glob("*.md"):
        if f.is_file():
            prompts.append(f.stem)

    # Subfolder files
    if include_subdirs:
        for f in _PROMPTS_DIR.rglob("*.md"):
            if f.is_file() and f.parent != _PROMPTS_DIR:
                rel = f.relative_to(_PROMPTS_DIR).with_suffix("")
                prompts.append(str(rel).replace("\\", "/"))

    return sorted(prompts)


__all__ = ["load_prompt", "list_available_prompts"]