"""Validation functions for user input."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL string to validate
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If URL is invalid
    
    Examples:
        >>> validate_url("https://api.example.com")
        True
        >>> validate_url("not-a-url")
        Traceback (most recent call last):
        ValueError: URL must start with http:// or https://
    """
    if not url:
        raise ValueError("URL cannot be empty")
    
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")
    
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        raise ValueError("Invalid URL format")
    
    return True


def validate_api_key(key: str, min_length: int = 8) -> bool:
    """
    Validate API key format.
    
    Args:
        key: API key string to validate
        min_length: Minimum length required
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If API key is invalid
    
    Examples:
        >>> validate_api_key("sk-1234567890")
        True
        >>> validate_api_key("short")
        Traceback (most recent call last):
        ValueError: API key must be at least 8 characters
    """
    if not key:
        raise ValueError("API key cannot be empty")
    
    if len(key) < min_length:
        raise ValueError(f"API key must be at least {min_length} characters")
    
    if any(c.isspace() for c in key):
        raise ValueError("API key cannot contain whitespace")
    
    return True


def validate_stack_name(name: str) -> bool:
    """
    Validate tech stack name.
    
    Args:
        name: Stack name to validate
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If stack name is invalid
    
    Examples:
        >>> validate_stack_name("fastapi")
        True
        >>> validate_stack_name("my-stack")
        True
        >>> validate_stack_name("invalid stack!")
        Traceback (most recent call last):
        ValueError: Stack name can only contain alphanumeric characters, hyphens, and underscores
    """
    if not name:
        raise ValueError("Stack name cannot be empty")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValueError(
            "Stack name can only contain alphanumeric characters, hyphens, and underscores"
        )
    
    return True


def validate_model_name(name: str) -> bool:
    """
    Validate LLM model name.
    
    Args:
        name: Model name to validate
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If model name is invalid
    
    Examples:
        >>> validate_model_name("claude-3-5-sonnet")
        True
        >>> validate_model_name("gpt-4")
        True
        >>> validate_model_name("")
        Traceback (most recent call last):
        ValueError: Model name cannot be empty
    """
    if not name:
        raise ValueError("Model name cannot be empty")
    
    if not re.match(r'^[a-zA-Z0-9._-]+$', name):
        raise ValueError(
            "Model name can only contain alphanumeric characters, dots, hyphens, and underscores"
        )
    
    return True


def validate_non_empty(value: str) -> bool:
    """
    Validate that value is not empty.
    
    Args:
        value: String to validate
    
    Returns:
        True if not empty
    
    Raises:
        ValueError: If value is empty
    
    Examples:
        >>> validate_non_empty("something")
        True
        >>> validate_non_empty("   ")
        Traceback (most recent call last):
        ValueError: Value cannot be empty
    """
    if not value or not value.strip():
        raise ValueError("Value cannot be empty")
    
    return True


def validate_array_items(
    items: list[str],
    item_validator: Callable[[str], bool],
) -> bool:
    """
    Validate each item in an array.
    
    Args:
        items: List of strings to validate
        item_validator: Validator function for each item
    
    Returns:
        True if all items are valid
    
    Raises:
        ValueError: If any item is invalid, with aggregated error messages
    
    Examples:
        >>> validate_array_items(["a", "b"], validate_non_empty)
        True
        >>> validate_array_items(["", "b"], validate_non_empty)
        Traceback (most recent call last):
        ValueError: Invalid items: Item 1: Value cannot be empty
    """
    errors = []
    
    for i, item in enumerate(items, 1):
        try:
            item_validator(item)
        except ValueError as e:
            errors.append(f"Item {i}: {e}")
    
    if errors:
        raise ValueError("Invalid items: " + "; ".join(errors))
    
    return True


def validate_directory_path(path_str: str) -> bool:
    """
    Validate directory path (can be absolute or relative).
    
    Args:
        path_str: Directory path to validate
    
    Returns:
        True if valid and directory exists
    
    Raises:
        ValueError: If path is invalid or doesn't exist
    
    Examples:
        >>> validate_directory_path(".")
        True
        >>> validate_directory_path("/absolute/path")
        True  # if exists
        >>> validate_directory_path("")
        Traceback (most recent call last):
        ValueError: Directory path cannot be empty
    """
    if not path_str:
        raise ValueError("Directory path cannot be empty")
    
    # Expand user home directory (~) and environment variables
    expanded_path = os.path.expanduser(os.path.expandvars(path_str))
    
    try:
        path = Path(expanded_path)
    except Exception as e:
        raise ValueError(f"Invalid path format: {e}")
    
    # Resolve to absolute path
    try:
        resolved_path = path.resolve()
    except Exception as e:
        raise ValueError(f"Cannot resolve path: {e}")
    
    # Check if directory exists
    if not resolved_path.exists():
        raise ValueError(f"Directory does not exist: {resolved_path}")
    
    # Check if it's actually a directory
    if not resolved_path.is_dir():
        raise ValueError(f"Path is not a directory: {resolved_path}")
    
    return True


def normalize_directory_path(path_str: str) -> str:
    """
    Normalize and resolve directory path to absolute path.
    
    Args:
        path_str: Directory path (can be relative or absolute)
    
    Returns:
        Absolute path string
    
    Examples:
        >>> normalize_directory_path(".")
        '/current/working/directory'
        >>> normalize_directory_path("~/projects")
        '/home/user/projects'
    """
    expanded_path = os.path.expanduser(os.path.expandvars(path_str))
    resolved_path = Path(expanded_path).resolve()
    return str(resolved_path)
