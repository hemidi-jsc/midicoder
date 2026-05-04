"""Interactive prompt functions for user input."""

from __future__ import annotations

import getpass
import sys
from typing import Callable

import questionary


def prompt_text(
    text: str,
    default: str | None = None,
    validator: Callable[[str], bool] | None = None,
) -> str | None:
    """
    Prompt user for text input.

    Args:
        text: The prompt message
        default: Default value if user enters nothing
        validator: Optional validation function that raises ValueError on invalid input

    Returns:
        User input or default value, None if non-interactive

    Examples:
        >>> name = prompt_text("Enter name", default="John")
        >>> email = prompt_text("Enter email", validator=validate_email)
    """
    if not sys.stdin.isatty():
        return default

    prompt = text
    if default:
        prompt += f" [{default}]"
    prompt += ": "

    while True:
        try:
            value = input(prompt)
        except EOFError:
            return default
        except KeyboardInterrupt:
            print("\nCancelled by user")
            raise SystemExit(1)

        value = value.strip()
        if not value:
            return default

        if validator:
            try:
                validator(value)
                return value
            except ValueError as e:
                print(f"Invalid input: {e}")
                continue

        return value


def prompt_secret(text: str, confirm: bool = False) -> str | None:
    """
    Prompt user for secret input (hidden).

    Args:
        text: The prompt message
        confirm: If True, ask user to enter secret twice

    Returns:
        Secret value, None if non-interactive or confirmation failed

    Examples:
        >>> api_key = prompt_secret("Enter API key")
        >>> password = prompt_secret("Enter password", confirm=True)
    """
    if not sys.stdin.isatty():
        return None

    try:
        secret = getpass.getpass(f"{text}: ")

        if confirm:
            secret_confirm = getpass.getpass(f"{text} (confirm): ")
            if secret != secret_confirm:
                print("Values do not match")
                return None

        return secret if secret else None

    except EOFError:
        return None
    except KeyboardInterrupt:
        print("\nCancelled by user")
        raise SystemExit(1)


def prompt_array(
    text: str,
    separator: str = ",",
    validator: Callable[[str], bool] | None = None,
) -> list[str]:
    """
    Prompt user for array input (comma-separated by default).

    Args:
        text: The prompt message
        separator: Character to split input on
        validator: Optional validation function for each item

    Returns:
        List of strings, empty list if non-interactive

    Examples:
        >>> tags = prompt_array("Enter tags (comma-separated)")
        >>> emails = prompt_array("Enter emails", validator=validate_email)
    """
    if not sys.stdin.isatty():
        return []

    prompt = f"{text}: "

    while True:
        try:
            value = input(prompt)
        except EOFError:
            return []
        except KeyboardInterrupt:
            print("\nCancelled by user")
            raise SystemExit(1)

        items = [item.strip() for item in value.split(separator)]
        items = [item for item in items if item]

        if not items:
            return []

        if validator:
            try:
                for item in items:
                    validator(item)
                return items
            except ValueError as e:
                print(f"Invalid input: {e}")
                continue

        return items


def prompt_choice(
    text: str,
    choices: list[str],
    default: str | None = None,
) -> str:
    """
    Prompt user to choose from a list of options using questionary.

    Args:
        text: The prompt message
        choices: List of valid choices
        default: Default choice if user enters nothing

    Returns:
        Selected choice, default if non-interactive

    Examples:
        >>> stack = prompt_choice("Select stack", ["fastapi", "nest"], default="fastapi")
    """
    if not sys.stdin.isatty():
        return default or choices[0]

    # Use questionary for better UX if available
    try:
        result = questionary.select(
            text,
            choices=choices,
            default=default or choices[0],
        ).ask()

        if result is None:  # User pressed Ctrl+C
            print("\nCancelled by user")
            raise SystemExit(1)

        return result
    except Exception as e:
        # Fall back to manual input if questionary fails
        print(f"Note: Interactive selection failed ({e})")
        raise SystemExit(1)


def prompt_multichoice(
    text: str, choices: list[str], defaults: str | None = None
) -> list[str]:
    """
    Prompt user to choose multiple options from a list using questionary.

    Args:
        text: The prompt message
        choices: List of valid choices
        defaults: Default choices if user enters nothing

    Returns:
        List of selected choices, defaults if non-interactive

    Examples:
        >>> features = prompt_multichoice("Select features", ["auth", "db", "cache"])
        >>> tags = prompt_multichoice("Select tags", ["prod", "dev", "test"], defaults=["dev"])
    """
    if not sys.stdin.isatty():
        return defaults or []

    # Use questionary for better UX if available
    try:
        answer = [questionary.Choice(title=c, checked=c in defaults) for c in choices]

        result = questionary.checkbox(text, choices=answer).ask()

        if result is None:  # User pressed Ctrl+C
            print("\nCancelled by user")
            raise SystemExit(1)

        return result
    except Exception as e:
        # Fall back to manual input if questionary fails
        print(f"Note: Interactive selection failed ({e})")
        raise SystemExit(1)


def prompt_confirm(text: str, default: bool = True) -> bool:
    """
    Prompt user for yes/no confirmation.

    Args:
        text: The prompt message
        default: Default value if user enters nothing

    Returns:
        True for yes, False for no

    Examples:
        >>> if prompt_confirm("Continue?", default=True):
        ...     print("Continuing...")
    """
    if not sys.stdin.isatty():
        return default

    prompt_suffix = " [Y/n]" if default else " [y/N]"
    prompt = f"{text}{prompt_suffix}: "

    while True:
        try:
            value = input(prompt)
        except EOFError:
            return default
        except KeyboardInterrupt:
            print("\nCancelled by user")
            raise SystemExit(1)

        value = value.strip().lower()

        if not value:
            return default

        if value in ("y", "yes"):
            return True
        if value in ("n", "no"):
            return False

        print("Please enter 'y' or 'n'")


def prompt_multiline(text: str, end_marker: str = "END") -> str:
    """
    Prompt user for multiline input.

    Args:
        text: The prompt message
        end_marker: String that marks end of input

    Returns:
        Multiline string, empty string if non-interactive

    Examples:
        >>> description = prompt_multiline("Enter description (type END to finish)")
    """
    if not sys.stdin.isatty():
        return ""

    print(f"{text}")
    print(f"(Type '{end_marker}' on a new line to finish)")

    lines = []
    try:
        while True:
            line = input()
            if line.strip() == end_marker:
                break
            lines.append(line)
    except EOFError:
        pass
    except KeyboardInterrupt:
        print("\nCancelled by user")
        raise SystemExit(1)

    return "\n".join(lines)
