"""Input/Output utilities for Midicoder CLI."""

from .messages import (
    MessagePrinter,
    MessageType,
    print_dict,
    print_error,
    print_info,
    print_list,
    print_normal,
    print_success,
    print_table,
    print_warning,
)

try:
    from .prompt import (
        prompt_array,
        prompt_choice,
        prompt_confirm,
        prompt_multichoice,
        prompt_multiline,
        prompt_secret,
        prompt_text,
    )
except ModuleNotFoundError as exc:
    if exc.name != "questionary":
        raise

    def _prompt_dependency_missing(*args, **kwargs):
        raise ModuleNotFoundError(
            "Prompt features require optional dependency 'questionary'. "
            "Install it to use interactive prompt commands."
        )

    prompt_text = _prompt_dependency_missing
    prompt_choice = _prompt_dependency_missing
    prompt_multichoice = _prompt_dependency_missing
    prompt_array = _prompt_dependency_missing
    prompt_secret = _prompt_dependency_missing
    prompt_confirm = _prompt_dependency_missing
    prompt_multiline = _prompt_dependency_missing
from .validators import (
    validate_api_key,
    validate_array_items,
    validate_model_name,
    validate_non_empty,
    validate_stack_name,
    validate_url,
)

__all__ = [
    # Prompt functions
    "prompt_text",
    "prompt_choice",
    "prompt_multichoice",
    "prompt_array",
    "prompt_secret",
    "prompt_confirm",
    "prompt_multiline",
    # Validators
    "validate_url",
    "validate_api_key",
    "validate_stack_name",
    "validate_model_name",
    "validate_non_empty",
    "validate_array_items",
    # Message functions
    "MessagePrinter",
    "MessageType",
    "print_info",
    "print_warning",
    "print_error",
    "print_success",
    "print_normal",
    "print_dict",
    "print_list",
    "print_table",
]
