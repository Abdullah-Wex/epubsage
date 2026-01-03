"""Shared CLI utilities - DRY principle.

This module contains shared utilities for the CLI following DRY principles:
- Single console instances for output
- Single error handling mechanism
- Single output formatter for all formats
- Single path validator
"""

from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax


# Single console instances - DRY
console = Console()
err_console = Console(stderr=True)


class ExitCode(IntEnum):
    """Exit codes for CLI - SOLID single enum."""

    SUCCESS = 0
    ERROR = 1           # General error
    FILE_NOT_FOUND = 2  # EPUB file not found
    INVALID_EPUB = 3    # Invalid EPUB format
    NO_RESULTS = 4      # Search found nothing


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class OutputFormatter:
    """Single class for all output formatting - DRY principle."""

    def __init__(self, format: str = "text"):
        self.format = format

    def output(self, data: Any, title: Optional[str] = None) -> None:
        """Output data in the specified format."""
        if self.format == "json":
            self._output_json(data)
        elif self.format == "table":
            self._output_table(data, title)
        else:
            self._output_text(data, title)

    def _output_json(self, data: Any) -> None:
        """Output as formatted JSON with syntax highlighting."""
        json_str = json.dumps(data, indent=2, cls=DateTimeEncoder, ensure_ascii=False)
        syntax = Syntax(json_str, "json", theme="monokai", word_wrap=True)
        console.print(syntax)

    def _output_table(self, data: Any, title: Optional[str] = None) -> None:
        """Output as Rich table."""
        if isinstance(data, dict):
            table = Table(title=title, show_header=True, header_style="bold cyan")
            table.add_column("Field", style="green")
            table.add_column("Value", style="white")

            for key, value in data.items():
                if value is not None:
                    # Format value based on type
                    if isinstance(value, list):
                        value_str = ", ".join(str(v) for v in value)
                    elif isinstance(value, dict):
                        value_str = json.dumps(value, ensure_ascii=False)
                    else:
                        value_str = str(value)
                    table.add_row(str(key), value_str)

            console.print(table)

        elif isinstance(data, list):
            if not data:
                console.print("[yellow]No data to display[/yellow]")
                return

            # Infer columns from first item
            if isinstance(data[0], dict):
                table = Table(title=title, show_header=True, header_style="bold cyan")
                columns = list(data[0].keys())
                for col in columns:
                    table.add_column(col.replace("_", " ").title(), style="white")

                for item in data:
                    row = [str(item.get(col, "")) for col in columns]
                    table.add_row(*row)

                console.print(table)
            else:
                # Simple list
                for item in data:
                    console.print(f"  - {item}")
        else:
            console.print(str(data))

    def _output_text(self, data: Any, title: Optional[str] = None) -> None:
        """Output as formatted text with colors."""
        if isinstance(data, dict):
            if title:
                console.print(Panel(title, style="bold blue"))

            for key, value in data.items():
                if value is not None:
                    key_formatted = key.replace("_", " ").title()
                    if isinstance(value, list):
                        value_str = ", ".join(str(v) for v in value) if value else "[dim]None[/dim]"
                    elif isinstance(value, dict):
                        value_str = json.dumps(value, ensure_ascii=False)
                    else:
                        value_str = str(value) if value else "[dim]None[/dim]"
                    console.print(f"[green]{key_formatted}:[/green] {value_str}")

        elif isinstance(data, list):
            if title:
                console.print(f"[bold blue]{title}[/bold blue]")

            for item in data:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if value is not None:
                            console.print(f"  [green]{key}:[/green] {value}")
                    console.print()
                else:
                    console.print(f"  - {item}")
        else:
            console.print(str(data))

    def output_tree(self, data: List[Dict], title: str = "Contents") -> None:
        """Output hierarchical data as a tree."""
        tree = Tree(f"[bold blue]{title}[/bold blue]")
        self._build_tree(tree, data)
        console.print(tree)

    def _build_tree(self, parent: Tree, items: List[Dict], level: int = 0) -> None:
        """Recursively build tree from hierarchical data."""
        for item in items:
            label = item.get("title", item.get("label", "Unknown"))
            node = parent.add(f"[green]{label}[/green]")

            children = item.get("children", item.get("items", []))
            if children:
                self._build_tree(node, children, level + 1)

    def output_panel(self, content: str, title: str, style: str = "blue") -> None:
        """Output content in a styled panel."""
        console.print(Panel(content, title=title, border_style=style))

    def output_success(self, message: str) -> None:
        """Output success message."""
        console.print(f"[green]✓[/green] {message}")

    def output_warning(self, message: str) -> None:
        """Output warning message."""
        console.print(f"[yellow]⚠[/yellow] {message}")

    def output_info(self, message: str) -> None:
        """Output info message."""
        console.print(f"[blue]ℹ[/blue] {message}")


def handle_error(msg: str, code: ExitCode = ExitCode.ERROR) -> None:
    """Single error handler - DRY principle."""
    err_console.print(f"[red]Error:[/red] {msg}")
    raise SystemExit(code)


def validate_epub_path(path: Path) -> Path:
    """Single path validator used by all commands - DRY principle."""
    if not path.exists():
        handle_error(f"File not found: {path}", ExitCode.FILE_NOT_FOUND)

    suffix = path.suffix.lower()
    if suffix != ".epub" and not path.is_dir():
        handle_error(f"Not an EPUB file: {path}", ExitCode.INVALID_EPUB)

    return path


def format_reading_time(time_dict: Dict[str, int]) -> str:
    """Format reading time dictionary to human-readable string."""
    hours = time_dict.get("hours", 0)
    minutes = time_dict.get("minutes", 0)

    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def format_file_size(size_bytes: int) -> str:
    """Format file size to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
