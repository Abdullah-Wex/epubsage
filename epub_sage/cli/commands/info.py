"""Info and stats commands."""

import typer
from pathlib import Path
from enum import Enum

from ..utils import (
    console, OutputFormatter, handle_error, validate_epub_path,
    format_reading_time, count_sections,
)
from ...processors import process_epub


class Format(str, Enum):
    text = "text"
    json = "json"
    table = "table"


def info(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    format: Format = typer.Option(
        Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Display basic book information."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        result = process_epub(str(path))

        if not result.success:
            handle_error(f"Failed to process EPUB: {', '.join(result.errors)}")

        chapter_count = sum(
            1 for ch in result.chapters
            if ch.get("content_type", "chapter") == "chapter"
        )
        total_sections = sum(count_sections(ch.get("sections", []))
                             for ch in result.chapters)

        data = {
            "title": result.title or "Unknown",
            "author": result.author or "Unknown",
            "publisher": result.publisher or "Unknown",
            "language": result.language or "Unknown",
            "words": result.total_words,
            "reading_time": format_reading_time(result.estimated_reading_time),
            "chapters": chapter_count,
            "sections": total_sections,
        }

        if format == Format.text:
            console.print()
            console.print(f"[bold blue]Title:[/bold blue]     {data['title']}")
            console.print(
                f"[bold blue]Author:[/bold blue]    {data['author']}")
            console.print(
                f"[bold blue]Publisher:[/bold blue] {data['publisher']}")
            console.print(
                f"[bold blue]Language:[/bold blue]  {data['language']}")
            console.print(
                f"[bold blue]Words:[/bold blue]     {data['words']:,}")
            console.print(
                f"[bold blue]Est. Time:[/bold blue] {data['reading_time']}")
            console.print(
                f"[bold blue]Chapters:[/bold blue]  {data['chapters']}")
            console.print(
                f"[bold blue]Sections:[/bold blue]  {data['sections']}")
            console.print()
        else:
            formatter.output(data, "Book Information")

    except Exception as e:
        handle_error(str(e))


def stats(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    format: Format = typer.Option(
        Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Display book statistics."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        result = process_epub(str(path))

        if not result.success:
            handle_error(f"Failed to process EPUB: {', '.join(result.errors)}")

        total_words = result.total_words
        chapter_count = len(result.chapters)
        avg_words = round(total_words / chapter_count,
                          1) if chapter_count > 0 else 0
        total_sections = sum(count_sections(ch.get("sections", []))
                             for ch in result.chapters)

        chapter_stats = [
            {"title": ch.get("title", f"Chapter {ch.get('chapter_id', 0)}"), "words": ch.get(
                "word_count", 0)}
            for ch in result.chapters
        ]
        chapter_stats.sort(key=lambda x: x["words"], reverse=True)

        data = {
            "total_words": total_words,
            "total_chapters": chapter_count,
            "total_sections": total_sections,
            "reading_time": format_reading_time(result.estimated_reading_time),
            "avg_words_per_chapter": avg_words,
            "longest_chapter": chapter_stats[0] if chapter_stats else None,
            "shortest_chapter": chapter_stats[-1] if chapter_stats else None,
            "file_size_mb": result.total_size_mb,
            "total_files": result.total_files,
        }

        if format == Format.text:
            _print_stats_text(data, chapter_stats)
        else:
            formatter.output(data, "Book Statistics")

    except Exception as e:
        handle_error(str(e))


def _print_stats_text(data: dict, chapter_stats: list) -> None:
    console.print()
    console.print("[bold cyan]Book Statistics[/bold cyan]")
    console.print("-" * 40)
    console.print(f"[green]Total Words:[/green]     {data['total_words']:,}")
    console.print(f"[green]Total Chapters:[/green]  {data['total_chapters']}")
    console.print(f"[green]Total Sections:[/green]  {data['total_sections']}")
    console.print(f"[green]Reading Time:[/green]    {data['reading_time']}")
    console.print(
        f"[green]Avg Words/Ch:[/green]    {data['avg_words_per_chapter']:,}")

    if chapter_stats:
        longest = chapter_stats[0]
        shortest = chapter_stats[-1]
        console.print(
            f"[green]Longest Chapter:[/green] {longest['title']} ({longest['words']:,} words)")
        console.print(
            f"[green]Shortest Chapter:[/green] {shortest['title']} ({shortest['words']:,} words)")

    console.print(
        f"[green]File Size:[/green]       {data['file_size_mb']:.2f} MB")
    console.print(f"[green]Total Files:[/green]     {data['total_files']}")
    console.print()
