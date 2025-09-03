"""
Console output utilities with colors and formatting.
"""

from typing import Any, Optional

# Try to import rich, fall back to basic console if not available
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


def print_info(message: str, **kwargs) -> None:
    """Print an info message."""
    if RICH_AVAILABLE and console:
        console.print(f"[blue]ℹ️  {message}[/blue]", **kwargs)
    else:
        print(f"ℹ️  {message}")


def print_success(message: str, **kwargs) -> None:
    """Print a success message."""
    if RICH_AVAILABLE and console:
        console.print(f"[green]✅ {message}[/green]", **kwargs)
    else:
        print(f"✅ {message}")


def print_warning(message: str, **kwargs) -> None:
    """Print a warning message."""
    if RICH_AVAILABLE and console:
        console.print(f"[yellow]⚠️  {message}[/yellow]", **kwargs)
    else:
        print(f"⚠️  {message}")


def print_error(message: str, **kwargs) -> None:
    """Print an error message."""
    if RICH_AVAILABLE and console:
        console.print(f"[red]❌ {message}[/red]", **kwargs)
    else:
        print(f"❌ {message}")


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """Print a formatted header."""
    if RICH_AVAILABLE and console:
        if subtitle:
            console.print(
                Panel(f"[bold]{title}[/bold]\n{subtitle}", style="blue"))
        else:
            console.print(Panel(f"[bold]{title}[/bold]", style="blue"))
    else:
        print(f"\n{'='*60}")
        print(f"  {title}")
        if subtitle:
            print(f"  {subtitle}")
        print(f"{'='*60}")


def print_section(title: str) -> None:
    """Print a section header."""
    if RICH_AVAILABLE and console:
        console.print(f"\n[bold blue]🔧 {title}[/bold blue]")
        console.print("─" * (len(title) + 3))
    else:
        print(f"\n🔧 {title}")
        print("─" * (len(title) + 3))


def print_step(step: str, status: str = "running") -> None:
    """Print a step with status."""
    if RICH_AVAILABLE and console:
        if status == "running":
            console.print(f"[yellow]⏳ {step}...[/yellow]")
        elif status == "success":
            console.print(f"[green]✅ {step}[/green]")
        elif status == "error":
            console.print(f"[red]❌ {step}[/red]")
        elif status == "skip":
            console.print(f"[dim]⏭️  {step} (skipped)[/dim]")
    else:
        if status == "running":
            print(f"⏳ {step}...")
        elif status == "success":
            print(f"✅ {step}")
        elif status == "error":
            print(f"❌ {step}")
        elif status == "skip":
            print(f"⏭️  {step} (skipped)")


def print_command(command: str) -> None:
    """Print a command being executed."""
    console.print(f"[dim]$ {command}[/dim]")


def print_table(data: list, headers: list, title: Optional[str] = None) -> None:
    """Print data as a formatted table."""
    table = Table(title=title)

    for header in headers:
        table.add_column(header, style="cyan")

    for row in data:
        table.add_row(*[str(cell) for cell in row])

    console.print(table)


def print_key_value_pairs(pairs: dict, title: Optional[str] = None) -> None:
    """Print key-value pairs in a formatted way."""
    if title:
        console.print(f"\n[bold]{title}[/bold]")

    for key, value in pairs.items():
        console.print(f"  [cyan]{key}:[/cyan] {value}")


def print_list(items: list, title: Optional[str] = None, bullet: str = "•") -> None:
    """Print a formatted list."""
    if title:
        console.print(f"\n[bold]{title}[/bold]")

    for item in items:
        console.print(f"  [green]{bullet}[/green] {item}")


def create_progress():
    """Create a progress bar."""
    if RICH_AVAILABLE and console:
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        )
    else:
        return None


def print_banner(text: str, style: str = "blue") -> None:
    """Print a banner with text."""
    console.print(Panel(Text(text, justify="center"), style=style))


def print_separator(char: str = "─", length: int = 50) -> None:
    """Print a separator line."""
    console.print(char * length)


def confirm(message: str, default: bool = True) -> bool:
    """Ask for user confirmation."""
    default_text = "Y/n" if default else "y/N"
    response = console.input(
        f"[yellow]❓ {message} ({default_text}): [/yellow]")

    if not response:
        return default

    return response.lower().startswith('y')


def prompt(message: str, default: Optional[str] = None) -> str:
    """Prompt user for input."""
    if default:
        response = console.input(f"[yellow]❓ {message} [{default}]: [/yellow]")
        return response or default
    else:
        return console.input(f"[yellow]❓ {message}: [/yellow]")


def print_code_block(code: str, language: str = "bash") -> None:
    """Print a code block with syntax highlighting."""
    from rich.syntax import Syntax
    syntax = Syntax(code, language, theme="monokai", line_numbers=False)
    console.print(syntax)


def print_json(data: Any) -> None:
    """Print JSON data with syntax highlighting."""
    import json
    from rich.syntax import Syntax

    json_str = json.dumps(data, indent=2, default=str)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)


def print_file_tree(directory_structure: dict, prefix: str = "") -> None:
    """Print a file tree structure."""
    items = list(directory_structure.items())
    for i, (name, content) in enumerate(items):
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        console.print(f"{prefix}{current_prefix}[cyan]{name}[/cyan]")

        if isinstance(content, dict) and content:
            next_prefix = prefix + ("    " if is_last else "│   ")
            print_file_tree(content, next_prefix)


class StatusContext:
    """Context manager for status updates."""

    def __init__(self, message: str):
        self.message = message
        self.status = None

    def __enter__(self):
        if RICH_AVAILABLE and console:
            self.status = console.status(f"[yellow]{self.message}...[/yellow]")
            self.status.start()
        else:
            print(f"⏳ {self.message}...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.status:
            self.status.stop()

        if exc_type is None:
            print_success(f"{self.message} completed")
        else:
            print_error(f"{self.message} failed")


def with_status(message: str):
    """Decorator for functions that should show status."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with StatusContext(message):
                return func(*args, **kwargs)
        return wrapper
    return decorator
