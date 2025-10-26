"""Rich-enhanced CLI display utilities for GitHound.

This module provides visually appealing CLI interfaces using Rich library,
including startup banners, enhanced help displays, and formatted command output.
"""


from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from githound.utils.version import get_version, is_development_version


def create_startup_banner(console: Console) -> None:
    """Display an attractive startup banner for GitHound CLI.

    Args:
        console: Rich Console instance for rendering.
    """
    version = get_version()
    is_dev = is_development_version()

    # ASCII art logo with styled text
    logo = Text()
    logo.append("   _____ _ _   _    _                       _ \n", style="bold cyan")
    logo.append("  / ____(_) | | |  | |                     | |\n", style="bold cyan")
    logo.append(" | |  __ _| |_| |__| | ___  _   _ _ __   __| |\n", style="bold cyan")
    logo.append(" | | |_ | | __|  __  |/ _ \\| | | | '_ \\ / _` |\n", style="cyan")
    logo.append(" | |__| | | |_| |  | | (_) | |_| | | | | (_| |\n", style="cyan")
    logo.append("  \\_____|_|\\__|_|  |_|\\___/ \\__,_|_| |_|\\__,_|\n", style="cyan")

    # Version and tagline
    version_text = Text()
    version_text.append("v", style="dim")
    version_text.append(version, style="bold yellow" if is_dev else "bold green")
    if is_dev:
        version_text.append(" [Development]", style="dim yellow")

    tagline = Text()
    tagline.append("🔍 ", style="bold")
    tagline.append("Advanced Git Repository Analysis & Search Tool", style="bold white")

    # Feature highlights
    features = Table.grid(padding=(0, 2))
    features.add_column(style="cyan", no_wrap=True)
    features.add_column(style="white")

    features.add_row("🔍", "Multi-modal search across commits, content, and metadata")
    features.add_row("📊", "Comprehensive repository analysis and statistics")
    features.add_row("📝", "File blame analysis with line-by-line tracking")
    features.add_row("🔄", "Commit and branch comparison with detailed diffs")
    features.add_row("🌐", "Web interface for interactive exploration")
    features.add_row("🤖", "MCP server for AI integration")

    # Quick start hints
    quick_start = Table.grid(padding=(0, 1))
    quick_start.add_column(style="bold magenta", no_wrap=True)
    quick_start.add_column(style="dim white")

    quick_start.add_row("githound --help", "Show all available commands")
    quick_start.add_row("githound search --help", "Get started with search")
    quick_start.add_row("githound analyze .", "Analyze current repository")

    # Combine all elements
    content = Group(
        Align.center(logo),
        "",
        Align.center(version_text),
        "",
        Align.center(tagline),
        "",
        Panel(
            features,
            title="[bold cyan]✨ Key Features[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        ),
        "",
        Panel(
            quick_start,
            title="[bold magenta]🚀 Quick Start[/bold magenta]",
            border_style="magenta",
            padding=(1, 2),
        ),
    )

    # Render in a main panel
    console.print(
        Panel(
            content,
            border_style="bold cyan",
            padding=(1, 2),
        )
    )
    console.print()


def create_command_help_panel(
    command_name: str,
    description: str,
    usage: str | None = None,
    examples: list[tuple[str, str]] | None = None,
    console: Console | None = None,
) -> None:
    """Create an enhanced help panel for a command.

    Args:
        command_name: Name of the command.
        description: Command description.
        usage: Usage pattern string.
        examples: List of (command, description) tuples for examples.
        console: Rich Console instance (creates new one if not provided).
    """
    if console is None:
        console = Console()

    # Command header
    header = Text()
    header.append("🐕 ", style="bold cyan")
    header.append(f"GitHound {command_name}", style="bold cyan")

    # Description
    desc_text = Text(description, style="white")

    # Usage section
    usage_section = None
    if usage:
        usage_text = Text()
        usage_text.append("githound ", style="bold magenta")
        usage_text.append(usage, style="yellow")
        usage_section = Panel(
            usage_text,
            title="[bold]Usage[/bold]",
            border_style="blue",
            padding=(0, 1),
        )

    # Examples section
    examples_section = None
    if examples:
        examples_table = Table.grid(padding=(0, 2))
        examples_table.add_column(style="bold magenta", no_wrap=False)
        examples_table.add_column(style="dim white")

        for cmd, desc in examples:
            examples_table.add_row(f"$ {cmd}", desc)

        examples_section = Panel(
            examples_table,
            title="[bold]💡 Examples[/bold]",
            border_style="green",
            padding=(1, 2),
        )

    # Combine sections
    sections: list[str | Text | Panel] = [header, "", desc_text]
    if usage_section:
        sections.extend(["", usage_section])
    if examples_section:
        sections.extend(["", examples_section])

    content = Group(*sections)

    console.print(
        Panel(
            content,
            border_style="bold cyan",
            padding=(1, 2),
        )
    )


def create_command_table(commands: list[dict[str, str]], console: Console) -> None:
    """Create a formatted table of available commands.

    Args:
        commands: List of command dictionaries with 'name', 'description' keys.
        console: Rich Console instance for rendering.
    """
    table = Table(
        title="[bold cyan]Available Commands[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
        title_style="bold cyan",
        padding=(0, 1),
    )

    table.add_column("Command", style="bold green", no_wrap=True, width=20)
    table.add_column("Description", style="white")

    for cmd in commands:
        icon = cmd.get("icon", "▪")
        name = cmd.get("name", "")
        description = cmd.get("description", "")

        table.add_row(f"{icon} {name}", description)

    console.print(table)
    console.print()


def display_version_info(console: Console, detailed: bool = False) -> None:
    """Display version information in a formatted panel.

    Args:
        console: Rich Console instance for rendering.
        detailed: Whether to show detailed build information.
    """
    from githound.utils.version import get_build_info

    version = get_version()
    build_info = get_build_info()

    # Version header
    header = Text()
    header.append("GitHound ", style="bold cyan")
    header.append("v", style="dim")
    header.append(version, style="bold yellow" if is_development_version() else "bold green")

    if not detailed:
        console.print(Panel(header, border_style="cyan", padding=(1, 2)))
        return

    # Detailed information table
    info_table = Table.grid(padding=(0, 2))
    info_table.add_column(style="bold cyan", justify="right")
    info_table.add_column(style="white")

    info_table.add_row("Version:", version)

    if build_info.get("git_commit"):
        commit = str(build_info["git_commit"])[:8]
        if build_info.get("dirty"):
            commit += " [dim](dirty)[/dim]"
        info_table.add_row("Git Commit:", commit)

    if build_info.get("git_branch") and build_info["git_branch"] != "HEAD":
        info_table.add_row("Branch:", str(build_info["git_branch"]))

    if build_info.get("git_tag"):
        info_table.add_row("Tag:", str(build_info["git_tag"]))

    if build_info.get("build_date"):
        info_table.add_row("Build Date:", str(build_info["build_date"]))

    # Python info
    import platform
    import sys

    info_table.add_row("", "")  # Spacer
    info_table.add_row(
        "Python:", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    info_table.add_row("Platform:", platform.system())

    content = Group(header, "", info_table)

    console.print(
        Panel(
            content,
            title="[bold cyan]📦 Version Information[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def display_welcome_message(console: Console) -> None:
    """Display a brief welcome message for CLI invocation without command.

    Args:
        console: Rich Console instance for rendering.
    """
    # Simplified banner for quick invocation
    title = Text()
    title.append("🐕 ", style="bold cyan")
    title.append("GitHound", style="bold cyan")
    title.append(" - Advanced Git Repository Analysis", style="white")

    commands = [
        {"icon": "🔍", "name": "search", "description": "Search commits, content, and metadata"},
        {
            "icon": "📊",
            "name": "analyze",
            "description": "Analyze repository statistics and metrics",
        },
        {
            "icon": "📝",
            "name": "blame",
            "description": "File blame analysis with authorship tracking",
        },
        {"icon": "🔄", "name": "diff", "description": "Compare commits or branches"},
        {"icon": "🌐", "name": "web", "description": "Start interactive web interface"},
        {"icon": "🤖", "name": "mcp-server", "description": "Start MCP server for AI integration"},
        {"icon": "📦", "name": "version", "description": "Show version information"},
    ]

    table = Table(
        show_header=False,
        border_style="cyan",
        padding=(0, 1),
        box=None,
    )

    table.add_column(style="bold cyan", no_wrap=True, width=20)
    table.add_column(style="dim white")

    for cmd in commands:
        table.add_row(f"  {cmd['icon']} {cmd['name']}", cmd["description"])

    # Help hint
    hint = Text()
    hint.append("💡 ", style="bold yellow")
    hint.append("Use ", style="dim")
    hint.append("githound <command> --help", style="bold magenta")
    hint.append(" for detailed information", style="dim")

    content = Group(
        Align.center(title),
        "",
        table,
        "",
        Align.center(hint),
    )

    console.print(
        Panel(
            content,
            border_style="bold cyan",
            padding=(1, 2),
        )
    )
    console.print()


def format_error_message(error: str, hint: str | None = None) -> Panel:
    """Format an error message in a styled panel.

    Args:
        error: The error message.
        hint: Optional hint for resolving the error.

    Returns:
        Formatted Rich Panel.
    """
    content = Text()
    content.append("✗ ", style="bold red")
    content.append(error, style="red")

    if hint:
        content.append("\n\n")
        content.append("💡 Hint: ", style="bold yellow")
        content.append(hint, style="yellow")

    return Panel(
        content,
        title="[bold red]Error[/bold red]",
        border_style="red",
        padding=(1, 2),
    )


def format_success_message(message: str) -> Panel:
    """Format a success message in a styled panel.

    Args:
        message: The success message.

    Returns:
        Formatted Rich Panel.
    """
    content = Text()
    content.append("✓ ", style="bold green")
    content.append(message, style="green")

    return Panel(
        content,
        border_style="green",
        padding=(1, 2),
    )
