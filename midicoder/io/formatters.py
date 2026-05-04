"""Output formatting utilities."""

from __future__ import annotations

from typing import Any


def format_list(items: list[str], numbered: bool = True) -> str:
    """
    Format a list of items.

    Args:
        items: List of strings to format
        numbered: If True, use numbered list, otherwise use bullets

    Returns:
        Formatted string

    Examples:
        >>> print(format_list(["a", "b", "c"], numbered=True))
        1. a
        2. b
        3. c
        >>> print(format_list(["a", "b"], numbered=False))
        - a
        - b
    """
    if not items:
        return ""

    if numbered:
        return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))
    else:
        return "\n".join(f"- {item}" for item in items)


def format_table(data: dict, indent: int = 2) -> str:
    """
    Format a dictionary as a table-like output.

    Args:
        data: Dictionary to format
        indent: Indentation level for nested items

    Returns:
        Formatted string

    Examples:
        >>> print(format_table({"name": "John", "age": 30}))
        name: John
        age: 30
    """
    lines = []
    _format_dict_recursive(data, lines, indent_level=0, indent_size=indent)
    return "\n".join(lines)


def _format_dict_recursive(
    data: dict | Any,
    lines: list[str],
    indent_level: int,
    indent_size: int,
) -> None:
    """Helper function to recursively format nested dictionaries."""
    if not isinstance(data, dict):
        return

    for key, value in data.items():
        indent = " " * (indent_level * indent_size)

        if isinstance(value, dict):
            lines.append(f"{indent}{key}:")
            _format_dict_recursive(value, lines, indent_level + 1, indent_size)
        elif isinstance(value, list):
            lines.append(f"{indent}{key}:")
            for item in value:
                if isinstance(item, dict):
                    _format_dict_recursive(item, lines, indent_level + 1, indent_size)
                else:
                    item_indent = " " * ((indent_level + 1) * indent_size)
                    lines.append(f"{item_indent}- {item}")
        else:
            lines.append(f"{indent}{key}: {value}")


def format_success(message: str) -> str:
    """
    Format a success message.

    Args:
        message: Success message

    Returns:
        Formatted string

    Examples:
        >>> format_success("Operation completed")
        'Success: Operation completed'
    """
    return f"Success: {message}"


def format_error(message: str) -> str:
    """
    Format an error message.

    Args:
        message: Error message

    Returns:
        Formatted string

    Examples:
        >>> format_error("Something went wrong")
        'Error: Something went wrong'
    """
    return f"Error: {message}"


def format_warning(message: str) -> str:
    """
    Format a warning message.

    Args:
        message: Warning message

    Returns:
        Formatted string

    Examples:
        >>> format_warning("This is deprecated")
        'Warning: This is deprecated'
    """
    return f"Warning: {message}"


def format_config_value(key: str, value: Any, mask_secrets: bool = True) -> str:
    """
    Format a config key-value pair for display.

    Args:
        key: Configuration key
        value: Configuration value
        mask_secrets: If True, mask secret values

    Returns:
        Formatted string

    Examples:
        >>> format_config_value("api_key", "sk-123456", mask_secrets=True)
        'api_key: sk-1...456'
        >>> format_config_value("name", "myapp", mask_secrets=False)
        'name: myapp'
    """
    if value is None:
        return f"{key}: None"

    if mask_secrets and _is_secret_key(key):
        masked_value = _mask_value(str(value))
        return f"{key}: {masked_value}"

    if isinstance(value, list):
        return f"{key}: [{', '.join(str(v) for v in value)}]"

    if isinstance(value, dict):
        return f"{key}: {value}"

    return f"{key}: {value}"


def _is_secret_key(key: str) -> bool:
    """Check if a key name indicates it contains a secret."""
    key_lower = key.lower()
    secret_indicators = ["key", "password", "secret", "token", "credential"]
    return any(indicator in key_lower for indicator in secret_indicators)


def _mask_value(value: str, show_chars: int = 4) -> str:
    """
    Mask a secret value for display.

    Args:
        value: Value to mask
        show_chars: Number of characters to show at start and end

    Returns:
        Masked value

    Examples:
        >>> _mask_value("sk-1234567890abcdef", show_chars=4)
        'sk-1...cdef'
        >>> _mask_value("short", show_chars=4)
        '****'
    """
    if len(value) <= show_chars * 2:
        return "****"

    start = value[:show_chars]
    end = value[-show_chars:]
    return f"{start}...{end}"
