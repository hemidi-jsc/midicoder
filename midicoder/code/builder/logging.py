"""Code build logging helpers."""

from __future__ import annotations

from midicoder.io.messages import print_error, print_info, print_success, print_warning


def format_message(code: str, summary: str, *, phase: str, action: str) -> str:
    action_value = f"({action})" if "=" in action else action
    return f"[{code}] {summary} | phase={phase} | action={action_value}"


def emit_info(code: str, summary: str, *, phase: str, action: str) -> None:
    print_info(format_message(code, summary, phase=phase, action=action))


def emit_warning(code: str, summary: str, *, phase: str, action: str) -> str:
    message = format_message(code, summary, phase=phase, action=action)
    print_warning(message)
    return message


def emit_error(code: str, summary: str, *, phase: str, action: str) -> str:
    message = format_message(code, summary, phase=phase, action=action)
    print_error(message)
    return message


def emit_success(message: str) -> None:
    print_success(message)
