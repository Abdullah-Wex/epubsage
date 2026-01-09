"""Content commands: chapters, toc, search."""

import typer
from pathlib import Path
from enum import Enum

from ..utils import (
    console, OutputFormatter, ExitCode, handle_error, validate_epub_path,
    flatten_nav_tree,
)
from ...processors import process_epub
from ...services.search_service import SearchService
from ... import DublinCoreService


class Format(str, Enum):
    text = "text"
    json = "json"
    table = "table"


def chapters(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    show_all: bool = typer.Option(
        False, "--all", "-a", help="Show all content including front/back matter"),
    format: Format = typer.Option(
        Format.table, "-f", "--format", help="Output format"),
) -> None:
    """List chapters with details."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        result = process_epub(str(path))

        if not result.success:
            handle_error(f"Failed to process EPUB: {', '.join(result.errors)}")

        filtered = [
            ch for ch in result.chapters
            if show_all or ch.get("content_type", "chapter") == "chapter"
        ]

        chapters_data = []
        for ch in filtered:
            data = {
                "id": ch.get("chapter_id", 0),
                "title": ch.get("title", "Untitled"),
                "href": ch.get("href", ""),
                "words": ch.get("word_count", 0),
                "images": len(ch.get("images", [])),
                "sections": len(ch.get("sections", [])),
            }
            if show_all:
                data["type"] = ch.get("content_type", "chapter")
            chapters_data.append(data)

        title = "All Content" if show_all else "Chapters"
        if format == Format.text:
            _print_chapters_text(chapters_data, title, show_all)
        else:
            formatter.output(chapters_data, title)

    except Exception as e:
        handle_error(str(e))


def _print_chapters_text(chapters_data: list, title: str, show_all: bool) -> None:
    console.print()
    console.print(
        f"[bold cyan]{title} ({len(chapters_data)} total)[/bold cyan]")
    console.print()
    for ch in chapters_data:
        type_label = f" [{ch['type']}]" if show_all else ""
        console.print(
            f"[green]{ch['id']:3}.[/green] {ch['title']}{type_label}")
        console.print(
            f"     Words: {ch['words']:,} | Images: {ch['images']} | Sections: {ch['sections']} | File: {ch['href']}")
    console.print()


def toc(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    flat: bool = typer.Option(
        False, "--flat", help="Flatten hierarchy to list"),
    format: Format = typer.Option(
        Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Display table of contents."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        service = DublinCoreService()
        nav = service.get_navigation_structure(str(path))

        if format == Format.text and not flat:
            console.print()
            console.print("[bold cyan]Table of Contents[/bold cyan]")
            console.print()
            if nav.get("navigation_tree"):
                formatter.output_tree(nav["navigation_tree"], "Contents")
            else:
                console.print("[yellow]No table of contents found[/yellow]")
            console.print()
        else:
            if flat and nav.get("navigation_tree"):
                flat_list = flatten_nav_tree(nav["navigation_tree"])
                formatter.output(flat_list, "Table of Contents")
            else:
                formatter.output(nav, "Table of Contents")

    except Exception as e:
        handle_error(str(e))


def search(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(
        10, "-n", "--limit", help="Maximum results to show"),
    case_sensitive: bool = typer.Option(
        False, "-c", "--case-sensitive", help="Case-sensitive search"),
    format: Format = typer.Option(
        Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Search for text in book content."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        result = process_epub(str(path))

        if not result.success:
            handle_error(f"Failed to process EPUB: {', '.join(result.errors)}")

        search_service = SearchService(context_size=100)
        results = search_service.search_sections(
            result.chapters, query, case_sensitive=case_sensitive)

        if not results:
            results = _fallback_chapter_search(
                result.chapters, search_service, query, case_sensitive)

        if not results:
            console.print(f"[yellow]No matches found for:[/yellow] {query}")
            raise typer.Exit(ExitCode.NO_RESULTS)

        results = results[:limit]

        if format == Format.text:
            _print_search_results(results, query, search_service)
        else:
            data = [
                {
                    "chapter_id": r.chapter_id, "chapter_title": r.chapter_title,
                    "section_id": r.section_id, "section_title": r.section_title,
                    "section_path": r.section_path, "context": r.context,
                    "relevance": round(r.relevance_score, 2),
                }
                for r in results
            ]
            formatter.output(data, f"Search Results for: {query}")

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(str(e))


def _fallback_chapter_search(chapters, search_service, query, case_sensitive):
    chapters_for_search = []
    for chapter in chapters:
        content_text = ""
        for content_item in chapter.get("content", []):
            if isinstance(content_item, dict):
                content_text += content_item.get("text", "") + " "
            elif isinstance(content_item, str):
                content_text += content_item + " "
        chapters_for_search.append({
            "chapter_id": chapter.get("chapter_id", 0),
            "title": chapter.get("title", f"Chapter {chapter.get('chapter_id', 0)}"),
            "content": content_text,
        })
    return search_service.search_content(chapters_for_search, query, case_sensitive=case_sensitive)


def _print_search_results(results, query, search_service) -> None:
    console.print()
    console.print(
        f"[bold cyan]Found {len(results)} matches for:[/bold cyan] {query}")
    console.print()
    for i, r in enumerate(results, 1):
        highlighted = search_service.highlight_matches(
            r.context, query, highlight_start="[bold yellow]", highlight_end="[/bold yellow]"
        )
        console.print(f"[green]{i}. {r.chapter_title}[/green]")
        if r.section_path:
            console.print(f"   [dim]-> {r.section_path}[/dim]")
        console.print(f"   {highlighted}")
        console.print()
