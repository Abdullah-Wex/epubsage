"""CLI utilities - shared formatters and helpers."""

from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, NoReturn, Optional
import json
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax

console = Console()
err_console = Console(stderr=True)


class ExitCode(IntEnum):
    """CLI exit codes."""
    SUCCESS = 0
    ERROR = 1
    FILE_NOT_FOUND = 2
    INVALID_EPUB = 3
    NO_RESULTS = 4


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder for datetime objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class OutputFormatter:
    """Output formatter supporting text, json, and table formats."""

    def __init__(self, format: str = "text"):
        self.format = format

    def output(self, data: Any, title: Optional[str] = None) -> None:
        if self.format == "json":
            self._output_json(data)
        elif self.format == "table":
            self._output_table(data, title)
        else:
            self._output_text(data, title)

    def _output_json(self, data: Any) -> None:
        json_str = json.dumps(
            data, indent=2, cls=DateTimeEncoder, ensure_ascii=False)
        syntax = Syntax(json_str, "json", theme="monokai", word_wrap=True)
        console.print(syntax)

    def _output_table(self, data: Any, title: Optional[str] = None) -> None:
        if isinstance(data, dict):
            table = Table(title=title, show_header=True,
                          header_style="bold cyan")
            table.add_column("Field", style="green")
            table.add_column("Value", style="white")
            for key, value in data.items():
                if value is not None:
                    value_str = self._format_value(value)
                    table.add_row(str(key), value_str)
            console.print(table)
        elif isinstance(data, list):
            self._output_list_table(data, title)
        else:
            console.print(str(data))

    def _output_list_table(self, data: List, title: Optional[str]) -> None:
        if not data:
            console.print("[yellow]No data to display[/yellow]")
            return
        if isinstance(data[0], dict):
            table = Table(title=title, show_header=True,
                          header_style="bold cyan")
            columns = list(data[0].keys())
            for col in columns:
                table.add_column(col.replace("_", " ").title(), style="white")
            for item in data:
                row = [str(item.get(col, "")) for col in columns]
                table.add_row(*row)
            console.print(table)
        else:
            for item in data:
                console.print(f"  - {item}")

    def _output_text(self, data: Any, title: Optional[str] = None) -> None:
        if isinstance(data, dict):
            if title:
                console.print(Panel(title, style="bold blue"))
            for key, value in data.items():
                if value is not None:
                    key_fmt = key.replace("_", " ").title()
                    value_str = self._format_value(value) or "[dim]None[/dim]"
                    console.print(f"[green]{key_fmt}:[/green] {value_str}")
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

    def _format_value(self, value: Any) -> str:
        if isinstance(value, list):
            return ", ".join(str(v) for v in value) if value else ""
        elif isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return str(value) if value else ""

    def output_tree(self, data: List[Dict], title: str = "Contents") -> None:
        tree = Tree(f"[bold blue]{title}[/bold blue]")
        self._build_tree(tree, data)
        console.print(tree)

    def _build_tree(self, parent: Tree, items: List[Dict], level: int = 0) -> None:
        for item in items:
            label = item.get("title", item.get("label", "Unknown"))
            node = parent.add(f"[green]{label}[/green]")
            children = item.get("children", item.get("items", []))
            if children:
                self._build_tree(node, children, level + 1)


def handle_error(msg: str, code: ExitCode = ExitCode.ERROR) -> NoReturn:
    err_console.print(f"[red]Error:[/red] {msg}")
    raise SystemExit(code)


def validate_epub_path(path: Path) -> Path:
    if not path.exists():
        handle_error(f"File not found: {path}", ExitCode.FILE_NOT_FOUND)
    if path.suffix.lower() != ".epub" and not path.is_dir():
        handle_error(f"Not an EPUB file: {path}", ExitCode.INVALID_EPUB)
    return path


def format_reading_time(time_dict: Dict[str, int]) -> str:
    hours = time_dict.get("hours", 0)
    minutes = time_dict.get("minutes", 0)
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"


def count_sections(sections: List[Dict]) -> int:
    total = len(sections)
    for s in sections:
        total += count_sections(s.get('subsections', []))
    return total


# Metadata formatters
ROLE_NAMES = {
    'aut': 'author', 'edt': 'editor', 'trl': 'translator',
    'ill': 'illustrator', 'nrt': 'narrator', 'ctb': 'contributor',
}


def format_creator(creator) -> str:
    if creator.role:
        role_display = ROLE_NAMES.get(creator.role, creator.role)
        return f"{creator.name} ({role_display})"
    return creator.name


def format_identifier(identifier) -> str:
    value = identifier.value
    if value and value.startswith('urn:isbn:'):
        return f"ISBN: {value[9:]}"
    elif value and value.startswith('urn:uuid:'):
        return f"UUID: {value[9:]}"
    elif identifier.scheme and identifier.scheme.upper() == 'ISBN':
        return f"ISBN: {value}"
    elif identifier.scheme:
        return f"{identifier.scheme}: {value}"
    return value


def flatten_nav_tree(items: List[Dict], level: int = 0) -> List[Dict]:
    """Flatten navigation tree to list."""
    flat_list = []
    for item in items:
        flat_list.append({
            "level": level,
            "title": item.get("label", item.get("title", "Unknown")),
            "href": item.get("content_src", item.get("href", "")),
            "nav_type": item.get("nav_type", ""),
        })
        children = item.get("children", [])
        if children:
            flat_list.extend(flatten_nav_tree(children, level + 1))
    return flat_list
