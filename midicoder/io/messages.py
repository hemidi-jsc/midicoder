"""Standardized message output for CLI commands."""

from __future__ import annotations

from enum import Enum
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class MessageType(Enum):
    """Message type enumeration."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    NORMAL = "normal"


class MessagePrinter:
    """Standardized message printer for consistent CLI output."""
    
    def __init__(self, console: Console | None = None):
        """
        Initialize MessagePrinter.
        
        Args:
            console: Rich Console instance, creates new one if None
        """
        self.console = console or Console()
    
    def print_info(self, message: str, title: str | None = None, **kwargs) -> None:
        """
        Print an info message.
        
        Args:
            message: Message content
            title: Optional title for the message
            **kwargs: Additional arguments for rich print
        
        Examples:
            >>> printer = MessagePrinter()
            >>> printer.print_info("Configuration loaded successfully")
            >>> printer.print_info("Found 5 items", title="Search Results")
        """
        text = Text(message)
        
        if title:
            self.console.print(
                Panel(text, title=f"[i]  {title}", border_style="blue", **kwargs)
            )
        else:
            self.console.print(f"[blue][i]  {message}[/blue]", **kwargs)
    
    def print_warning(self, message: str, title: str | None = None, **kwargs) -> None:
        """
        Print a warning message.
        
        Args:
            message: Message content
            title: Optional title for the message
            **kwargs: Additional arguments for rich print
        
        Examples:
            >>> printer = MessagePrinter()
            >>> printer.print_warning("API key not configured")
            >>> printer.print_warning("Deprecated feature", title="Deprecation")
        """
        text = Text(message)
        
        if title:
            self.console.print(
                Panel(text, title=f"[!]  {title}", border_style="yellow", **kwargs)
            )
        else:
            self.console.print(f"[yellow][!]  {message}[/yellow]", **kwargs)
    
    def print_error(self, message: str, title: str | None = None, **kwargs) -> None:
        """
        Print an error message.
        
        Args:
            message: Message content
            title: Optional title for the message
            **kwargs: Additional arguments for rich print
        
        Examples:
            >>> printer = MessagePrinter()
            >>> printer.print_error("File not found")
            >>> printer.print_error("Invalid configuration", title="Validation Error")
        """
        text = Text(message)
        
        if title:
            self.console.print(
                Panel(text, title=f"[x] {title}", border_style="red", **kwargs)
            )
        else:
            self.console.print(f"[red][x] {message}[/red]", **kwargs)
    
    def print_success(self, message: str, title: str | None = None, **kwargs) -> None:
        """
        Print a success message.
        
        Args:
            message: Message content
            title: Optional title for the message
            **kwargs: Additional arguments for rich print
        
        Examples:
            >>> printer = MessagePrinter()
            >>> printer.print_success("Configuration saved")
            >>> printer.print_success("All tests passed", title="Test Results")
        """
        text = Text(message)
        
        if title:
            self.console.print(
                Panel(text, title=f"[+] {title}", border_style="green", **kwargs)
            )
        else:
            self.console.print(f"[green][+] {message}[/green]", **kwargs)
    
    def print_normal(self, message: str, **kwargs) -> None:
        """
        Print a normal message (no special formatting).
        
        Args:
            message: Message content
            **kwargs: Additional arguments for rich print
        
        Examples:
            >>> printer = MessagePrinter()
            >>> printer.print_normal("Current configuration:")
        """
        self.console.print(message, **kwargs)
    
    def print_dict(self, data: dict[str, Any], title: str | None = None) -> None:
        """
        Print a dictionary in a formatted way.
        
        Args:
            data: Dictionary to print
            title: Optional title
        
        Examples:
            >>> printer = MessagePrinter()
            >>> printer.print_dict({"name": "app", "version": "1.0"}, title="Config")
        """
        from rich.pretty import Pretty
        
        if title:
            self.console.print(f"\n[bold]{title}:[/bold]")
        
        self.console.print(Pretty(data, expand_all=True))
    
    def print_list(
        self,
        items: list[str],
        title: str | None = None,
        numbered: bool = False,
    ) -> None:
        """
        Print a list of items.
        
        Args:
            items: List of items to print
            title: Optional title
            numbered: If True, use numbered list
        
        Examples:
            >>> printer = MessagePrinter()
            >>> printer.print_list(["item1", "item2"], title="Items", numbered=True)
        """
        if title:
            self.console.print(f"\n[bold]{title}:[/bold]")
        
        for i, item in enumerate(items, 1):
            if numbered:
                self.console.print(f"  {i}. {item}")
            else:
                self.console.print(f"  • {item}")
    
    def print_table(
        self,
        data: dict[str, Any],
        title: str | None = None,
        indent: int = 2,
    ) -> None:
        """
        Print data as a table-like structure.
        
        Args:
            data: Data to print
            title: Optional title
            indent: Indentation size
        
        Examples:
            >>> printer = MessagePrinter()
            >>> printer.print_table({"key": "value"}, title="Config")
        """
        if title:
            self.console.print(f"\n[bold]{title}:[/bold]")
        
        self._print_dict_recursive(data, indent_level=0, indent_size=indent)
    
    def _print_dict_recursive(
        self,
        data: dict | Any,
        indent_level: int,
        indent_size: int,
    ) -> None:
        """Helper to recursively print nested dictionaries."""
        if not isinstance(data, dict):
            return
        
        for key, value in data.items():
            indent = " " * (indent_level * indent_size)
            
            if isinstance(value, dict):
                self.console.print(f"{indent}[cyan]{key}[/cyan]:")
                self._print_dict_recursive(value, indent_level + 1, indent_size)
            elif isinstance(value, list):
                self.console.print(f"{indent}[cyan]{key}[/cyan]:")
                for item in value:
                    if isinstance(item, dict):
                        self._print_dict_recursive(item, indent_level + 1, indent_size)
                    else:
                        item_indent = " " * ((indent_level + 1) * indent_size)
                        self.console.print(f"{item_indent}• {item}")
            else:
                self.console.print(f"{indent}[cyan]{key}[/cyan]: {value}")


# Global default printer instance
_default_printer = MessagePrinter()


# Convenience functions using the default printer
def print_info(message: str, title: str | None = None, **kwargs) -> None:
    """Print an info message using the default printer."""
    _default_printer.print_info(message, title, **kwargs)


def print_warning(message: str, title: str | None = None, **kwargs) -> None:
    """Print a warning message using the default printer."""
    _default_printer.print_warning(message, title, **kwargs)


def print_error(message: str, title: str | None = None, **kwargs) -> None:
    """Print an error message using the default printer."""
    _default_printer.print_error(message, title, **kwargs)


def print_success(message: str, title: str | None = None, **kwargs) -> None:
    """Print a success message using the default printer."""
    _default_printer.print_success(message, title, **kwargs)


def print_normal(message: str, **kwargs) -> None:
    """Print a normal message using the default printer."""
    _default_printer.print_normal(message, **kwargs)


def print_dict(data: dict[str, Any], title: str | None = None) -> None:
    """Print a dictionary using the default printer."""
    _default_printer.print_dict(data, title)


def print_list(
    items: list[str],
    title: str | None = None,
    numbered: bool = False,
) -> None:
    """Print a list using the default printer."""
    _default_printer.print_list(items, title, numbered)


def print_table(
    data: dict[str, Any],
    title: str | None = None,
    indent: int = 2,
) -> None:
    """Print a table using the default printer."""
    _default_printer.print_table(data, title, indent)
