"""
Interactive Shell cho Midicoder CLI sử dụng Rich.

Module này cung cấp:
- Interactive REPL shell với Rich UI
- ASCII logo display
- Command completion
- Beautiful output formatting

E00: Installation & Setup
"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from rich.prompt import Prompt

# prompt_toolkit cho textbox-style input
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style as PromptStyle
from prompt_toolkit.formatted_text import HTML


# ASCII logo hardcoded
ASCII_LOGO = """
       ##                               ##       
       #####                         #####       
       #######                     #######       
       ##########               ##########       
       #############         #############       
       ###############     ###############       
       ######   #######  #######    ######       
       ######     #####  #####      ######       
       ######          ##           ######       
       ######  ###            ###   ######       
       ######  ######      ######   ######       
       ######  ######      ######   ######       
       ######    ####      ####     ######       
       ######      ##      ##       ######       
       ######                       ######       
       ######                       ######       
       ######                       ######       
        """

# Console instance với Rich styling - Force colors
console = Console(force_terminal=True, color_system="truecolor")


def get_ascii_logo() -> str:
    """
    Lấy ASCII logo.

    Returns:
        ASCII art string
    """
    return ASCII_LOGO


def display_logo():
    """Hiển thị ASCII logo với Rich panel."""
    logo = get_ascii_logo()
    
    # Tạo panel với style đẹp - Brand color: pink (#e90089)
    # Dùng màu trắng cho text để nhìn rõ trên nền tối
    panel = Panel(
        logo,
        title="[bold white]Midicoder v1.0.0[/bold white]",
        subtitle="[dim white]Contract Coding Platform[/dim white]",
        style="default",
        border_style="#e90089",
        padding=(1, 2),
    )
    console.print(panel)
    console.print()


def display_welcome_message():
    """Hiển thị welcome message."""
    # Dùng console.print với markup=True để resolve Rich tags
    # Brand color: pink (#e90089) cho các keyword, white cho text chính
    console.print(
        "[bold white]Welcome to Midicoder Interactive Shell![/bold white]"
    )
    console.print(
        "[white]Gõ [bold #e90089]help[/bold #e90089] để xem danh sách commands, [bold #e90089]exit[/bold #e90089] để thoát.[/white]"
    )
    console.print()


def get_available_commands() -> dict:
    """
    Lấy danh sách commands có sẵn.

    Returns:
        Dictionary mapping command names to descriptions
    """
    return {
        "init": "Khởi tạo Midicoder workspace",
        "brief": "Quản lý và phân tích yêu cầu (analyze, clarify, list)",
        "contract": "Tạo và kiểm tra DSL contracts (gen, check, repair)",
        "ir": "Build MIR từ contracts (build)",
        "code": "Code planning, generation, và application (plan, gen, apply)",
        "preview": "Local preview với Docker Compose (start, stop, status)",
        "config": "Quản lý cấu hình Midicoder (show, set, reset)",
        "status": "Hiển thị project status",
        "help": "Hiển thị help đầy đủ",
        "exit": "Thoát interactive shell",
        "quit": "Thoát interactive shell",
    }


def display_help():
    """Hiển thị help với Rich table."""
    from rich.table import Table

    console.print()
    # Panel header với màu trắng, border pink
    console.print(Panel("[bold white]Available Commands[/bold white]", border_style="#e90089"))
    console.print()

    # Tạo table cho commands - Brand color: pink (#e90089) cho header, white cho command names
    table = Table(show_header=True, header_style="bold white")
    table.add_column("Command", style="bold #e90089", width=15)
    table.add_column("Description", style="white", ratio=2)

    commands = get_available_commands()
    for cmd, desc in commands.items():
        if cmd not in ["exit", "quit"]:
            table.add_row(cmd, desc)

    console.print(table)
    console.print()
    console.print("[dim white]Gõ [bold #e90089]command --help[/bold #e90089] để xem chi tiết của command.[/dim white]")


def format_success(message: str) -> Text:
    """Format success message."""
    return Text(f"[✓] {message}", style="green")


def format_error(message: str) -> Text:
    """Format error message."""
    return Text(f"[✗] {message}", style="red")


def format_info(message: str) -> Text:
    """Format info message."""
    return Text(f"[ℹ] {message}", style="blue")


def format_warning(message: str) -> Text:
    """Format warning message."""
    return Text(f"[⚠] {message}", style="yellow")


def print_success(message: str):
    """In success message."""
    console.print(format_success(message))


def print_error(message: str):
    """In error message."""
    console.print(format_error(message))


def print_info(message: str):
    """In info message."""
    console.print(format_info(message))


def print_warning(message: str):
    """In warning message."""
    console.print(format_warning(message))


# Style cho prompt_toolkit textbox - Brand color: pink (#e90089)
TEXTBOX_STYLE = PromptStyle.from_dict({
    'bottom-toolbar': 'bg:#e90089 #ffffff',
    'search-toolbar': 'bg:#e90089 #ffffff',
    'scrollbar': 'bg:#e90089',
    'scrollbar-button': 'bg:#e90089',
    'scrollbar-button-background': 'bg:#e90089',
})

# Prompt với border style - Brand color: pink (#e90089)
PROMPT_MESSAGE = HTML('<style bg="#e90089" fg="white">midicoder></style> ')


class MidicoderShell:
    """
    Interactive shell cho Midicoder.

    Cung cấp REPL experience với:
    - ASCII logo display
    - Command completion
    - Rich output formatting
    """

    def __init__(self, cli_callable):
        """
        Khởi tạo shell.

        Args:
            cli_callable: Click CLI group để execute commands
        """
        self.cli = cli_callable
        self.running = False
        self.commands = get_available_commands()

    def start(self, initial_command: Optional[str] = None):
        """
        Bắt đầu interactive shell.

        Args:
            initial_command: Command để auto-execute khi start (nếu có)
        """
        self.running = True
        
        # Display logo và welcome
        display_logo()
        display_welcome_message()

        # Nếu có initial command, execute ngay
        if initial_command:
            self.execute_command(initial_command)

        # Start REPL loop
        while self.running:
            try:
                # Prompt cho user input với textbox style (cyan background)
                user_input = prompt(
                    PROMPT_MESSAGE,
                    style=TEXTBOX_STYLE,
                    default="",
                )
                console.print()

                if not user_input.strip():
                    continue

                # Parse command
                parts = user_input.strip().split()
                command = parts[0].lower()

                # Handle special commands
                if command in ["exit", "quit"]:
                    console.print("[dim]Goodbye![/dim]")
                    self.running = False
                elif command == "help":
                    display_help()
                elif command == "init":
                    # Execute command với brand color
                    self.execute_command(user_input.strip())
                elif command == "brief":
                    self.execute_command(user_input.strip())
                elif command == "contract":
                    self.execute_command(user_input.strip())
                elif command == "ir":
                    self.execute_command(user_input.strip())
                elif command == "code":
                    self.execute_command(user_input.strip())
                elif command == "preview":
                    self.execute_command(user_input.strip())
                elif command == "config":
                    self.execute_command(user_input.strip())
                elif command == "status":
                    self.execute_command(user_input.strip())
                else:
                    # Execute command
                    self.execute_command(user_input.strip())

            except KeyboardInterrupt:
                console.print()
                console.print("[dim]Ctrl+C pressed. Gõ 'exit' để thoát.[/dim]")
            except EOFError:
                console.print("[dim]Goodbye![/dim]")
                self.running = False

    def execute_command(self, command_str: str):
        """
        Execute command từ user input.

        Args:
            command_str: Command string (vd: "init --force")
        """
        from click.testing import CliRunner

        console.print()
        console.print(f"[dim]Executing:[/dim] [bold]{command_str}[/bold]")
        console.print()

        # Parse command parts
        parts = command_str.split()
        if not parts:
            return

        command = parts[0].lower()

        # Validate command
        if command not in self.commands and command not in ["exit", "quit", "help", "init", "brief", "contract", "ir", "code", "preview", "config", "status"]:
            print_error(f"Unknown command: {command}")
            console.print()
            console.print("[white]Gõ [bold #e90089]help[/bold #e90089] để xem danh sách commands.[/white]")
            return

        # Execute với Click runner (không dùng mix_stderr vì click mới không hỗ trợ)
        runner = CliRunner()
        result = runner.invoke(self.cli, parts, catch_exceptions=False)

        # Display output
        if result.output:
            console.print(result.output)

        if result.exception:
            print_error(str(result.exception))

        if result.exit_code != 0:
            print_warning(f"Command exited with code {result.exit_code}")


def launch_shell(cli_callable, initial_command: Optional[str] = None):
    """
    Launch interactive shell.

    Args:
        cli_callable: Click CLI group
        initial_command: Command để auto-execute (nếu có)
    """
    shell = MidicoderShell(cli_callable)
    shell.start(initial_command)