"""
epub-sage CLI - Professional EPUB content extraction and analysis.

Built with Typer + Rich for a modern CLI experience.
"""

import typer
import sys
import json
from pathlib import Path
from typing import Optional
from enum import Enum

from .cli_utils import (
    console,
    OutputFormatter,
    ExitCode,
    handle_error,
    validate_epub_path,
    format_reading_time,
    DateTimeEncoder,
)
from .processors import process_epub, SimpleEpubProcessor
from .services.search_service import SearchService
from .services.export_service import save_to_json
from .extractors.content_extractor import IMAGE_EXTENSIONS
from . import DublinCoreService, EpubExtractor

__version__ = "0.2.0"


# --- Module Constants ---

FILE_TYPE_FILTERS = {
    "html": ('.html', '.xhtml', '.htm'),
    "css": ('.css',),
    "images": IMAGE_EXTENSIONS,
    "fonts": ('.ttf', '.otf', '.woff', '.woff2'),
    "xml": ('.xml', '.opf', '.ncx'),
}


class Format(str, Enum):
    """Output format options."""
    text = "text"
    json = "json"
    table = "table"


# Global state for verbose/quiet options
class CliState:
    """Global CLI state - shared across commands."""
    verbose: bool = False
    quiet: bool = False
    no_color: bool = False


state = CliState()


# Main Typer app
app = typer.Typer(
    name="epub-sage",
    help="Professional EPUB content extraction and analysis.",
    no_args_is_help=True,
    pretty_exceptions_enable=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"epub-sage version {__version__}")
        raise typer.Exit()


def verbose_log(message: str) -> None:
    """Print message only if verbose mode is enabled."""
    if state.verbose and not state.quiet:
        console.print(f"[dim]{message}[/dim]")


def info_print(message: str) -> None:
    """Print info message unless quiet mode."""
    if not state.quiet:
        console.print(message)


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Enable verbose output"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q",
        help="Suppress non-error output"
    ),
    no_color: bool = typer.Option(
        False, "--no-color",
        help="Disable colored output"
    ),
) -> None:
    """EpubSage: Professional EPUB content extraction and analysis."""
    state.verbose = verbose
    state.quiet = quiet
    state.no_color = no_color
    if no_color:
        console.no_color = True


# ==================== TIER 1 COMMANDS ====================


@app.command()
def info(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    format: Format = typer.Option(Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Display basic book information."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        result = process_epub(str(path))

        if not result.success:
            handle_error(f"Failed to process EPUB: {', '.join(result.errors)}")

        # Count only actual chapters (not front/back matter)
        chapter_count = sum(
            1 for ch in result.chapters
            if ch.get("content_type", "chapter") == "chapter"
        )

        data = {
            "title": result.title or "Unknown",
            "author": result.author or "Unknown",
            "publisher": result.publisher or "Unknown",
            "language": result.language or "Unknown",
            "words": result.total_words,
            "reading_time": format_reading_time(result.estimated_reading_time),
            "chapters": chapter_count,
        }

        if format == Format.text:
            console.print()
            console.print(f"[bold blue]Title:[/bold blue]     {data['title']}")
            console.print(f"[bold blue]Author:[/bold blue]    {data['author']}")
            console.print(f"[bold blue]Publisher:[/bold blue] {data['publisher']}")
            console.print(f"[bold blue]Language:[/bold blue]  {data['language']}")
            console.print(f"[bold blue]Words:[/bold blue]     {data['words']:,}")
            console.print(f"[bold blue]Est. Time:[/bold blue] {data['reading_time']}")
            console.print(f"[bold blue]Chapters:[/bold blue]  {data['chapters']}")
            console.print()
        else:
            formatter.output(data, "Book Information")

    except Exception as e:
        handle_error(str(e))


@app.command()
def extract(
    path: Path = typer.Argument(..., help="Path to EPUB file or directory"),
    output: Optional[Path] = typer.Option(
        None, "-o", "--output",
        help="Output file/directory path (default: extracted_book.json or ./extracted/)"
    ),
    raw: bool = typer.Option(
        False, "-r", "--raw",
        help="Extract raw EPUB files to directory instead of JSON"
    ),
    metadata_only: bool = typer.Option(
        False, "-m", "--metadata-only",
        help="Export only metadata (no chapter content)"
    ),
    stdout: bool = typer.Option(
        False, "--stdout",
        help="Output JSON to stdout (ignores --output)"
    ),
    compact: bool = typer.Option(
        False, "--compact",
        help="Compact JSON output (no indentation)"
    ),
) -> None:
    """Extract book content to JSON or raw files.

    Examples:
        epub-sage extract book.epub                    # JSON to extracted_book.json
        epub-sage extract book.epub -o data.json      # JSON to custom file
        epub-sage extract book.epub --raw -o ./book/  # Raw files to directory
        epub-sage extract book.epub --stdout          # JSON to stdout (pipe-friendly)
        epub-sage extract book.epub -m                # Metadata only, no content
    """
    path = validate_epub_path(path)

    try:
        # Raw extraction mode - extract EPUB files to directory
        if raw:
            extractor = EpubExtractor()
            output_dir = str(output) if output else "./extracted"
            verbose_log(f"Extracting raw files to: {output_dir}")

            extracted_path = extractor.extract_epub(str(path), output_dir)
            info_print(f"[green]Extracted to:[/green] {extracted_path}")

            # List extracted files in verbose mode
            if state.verbose:
                file_count = sum(1 for _ in Path(extracted_path).rglob("*") if _.is_file())
                verbose_log(f"Total files extracted: {file_count}")
            return

        # JSON extraction mode
        verbose_log(f"Processing: {path}")

        processor = SimpleEpubProcessor()

        if path.is_dir():
            result = processor.process_directory(str(path))
        else:
            result = processor.process_epub(str(path))

        if not result.success:
            handle_error(f"Processing failed: {', '.join(result.errors)}")

        # Build output data
        if metadata_only:
            output_data: dict[str, object] = {
                "metadata": result.full_metadata.model_dump() if result.full_metadata else {
                    "title": result.title,
                    "author": result.author,
                    "publisher": result.publisher,
                    "language": result.language,
                    "description": result.description,
                    "isbn": result.isbn,
                    "publication_date": result.publication_date
                },
                "statistics": {
                    "total_words": result.total_words,
                    "reading_time": result.estimated_reading_time,
                    "chapter_count": len(result.chapters)
                }
            }
        else:
            output_data = {
                "metadata": result.full_metadata.model_dump() if result.full_metadata else {
                    "title": result.title,
                    "author": result.author,
                    "publisher": result.publisher,
                    "language": result.language,
                    "description": result.description,
                    "isbn": result.isbn,
                    "publication_date": result.publication_date
                },
                "statistics": {
                    "total_words": result.total_words,
                    "reading_time": result.estimated_reading_time,
                    "chapter_count": len(result.chapters)
                },
                "chapters": result.chapters,
                "errors": result.errors
            }

        # Output handling
        indent = None if compact else 2

        if stdout:
            # Output to stdout for piping
            json_str = json.dumps(output_data, indent=indent, cls=DateTimeEncoder, ensure_ascii=False)
            sys.stdout.write(json_str + "\n")
        else:
            # Output to file
            output_path = output or Path("extracted_book.json")
            save_to_json(output_data, str(output_path), indent=indent)
            info_print(f"[green]Data saved to:[/green] {output_path}")

    except Exception as e:
        handle_error(str(e))


@app.command()
def metadata(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    full: bool = typer.Option(False, "--full", help="Show all Dublin Core fields"),
    format: Format = typer.Option(Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Display Dublin Core metadata."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        service = DublinCoreService()
        parsed = service.parse_content_opf(str(path))
        meta = parsed.metadata

        # MARC relator code to human-readable mapping
        role_names = {
            'aut': 'author', 'edt': 'editor', 'trl': 'translator',
            'ill': 'illustrator', 'nrt': 'narrator', 'ctb': 'contributor',
        }

        def format_creator(c):
            """Format creator with role if available."""
            if c.role:
                role_display = role_names.get(c.role, c.role)
                return f"{c.name} ({role_display})"
            return c.name

        def format_identifier(i):
            """Format identifier, extracting clean ISBN if applicable."""
            value = i.value
            # Clean up URN prefixes for cleaner display
            if value and value.startswith('urn:isbn:'):
                return f"ISBN: {value[9:]}"
            elif value and value.startswith('urn:uuid:'):
                return f"UUID: {value[9:]}"
            elif i.scheme and i.scheme.upper() == 'ISBN':
                return f"ISBN: {value}"
            elif i.scheme:
                return f"{i.scheme}: {value}"
            return value

        if full:
            # Show all fields including raw metadata
            data = meta.model_dump() if meta else {}
        else:
            # Show common fields only
            data = {
                "title": meta.title if meta else None,
                "creators": [format_creator(c) for c in meta.creators] if meta and meta.creators else [],
                "publisher": meta.publisher if meta else None,
                "language": meta.language if meta else None,
                "description": meta.description if meta else None,
                "subjects": [s.value for s in meta.subjects] if meta and meta.subjects else [],
                "identifiers": [format_identifier(i) for i in meta.identifiers] if meta and meta.identifiers else [],
                "dates": [d.value for d in meta.dates] if meta and meta.dates else [],
                "epub_version": meta.epub_version if meta else None,
                "modified_date": meta.modified_date if meta else None,
            }

        if format == Format.text:
            console.print()
            console.print("[bold cyan]Dublin Core Metadata[/bold cyan]")
            console.print("-" * 40)

            for key, value in data.items():
                if value is not None and value != [] and value != "":
                    key_display = key.replace("_", " ").title()
                    if isinstance(value, list):
                        value_display = ", ".join(str(v) for v in value)
                    else:
                        value_display = str(value)
                    console.print(f"[green]{key_display}:[/green] {value_display}")

            console.print()
        else:
            formatter.output(data, "Dublin Core Metadata")

    except Exception as e:
        handle_error(str(e))


@app.command()
def toc(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    flat: bool = typer.Option(False, "--flat", help="Flatten hierarchy to list"),
    format: Format = typer.Option(Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Display table of contents."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        service = DublinCoreService()
        nav = service.get_navigation_structure(str(path))

        if format == Format.text and not flat:
            # Use tree output
            console.print()
            console.print("[bold cyan]Table of Contents[/bold cyan]")
            console.print()

            if nav.get("navigation_tree"):
                formatter.output_tree(nav["navigation_tree"], "Contents")
            else:
                console.print("[yellow]No table of contents found[/yellow]")
            console.print()
        else:
            # Flatten if requested
            if flat and nav.get("navigation_tree"):
                flat_list = []

                def flatten(items, level=0):
                    for item in items:
                        flat_list.append({
                            "level": level,
                            "title": item.get("label", item.get("title", "Unknown")),
                            "href": item.get("content_src", item.get("href", "")),
                            "nav_type": item.get("nav_type", ""),
                        })
                        children = item.get("children", [])
                        if children:
                            flatten(children, level + 1)

                flatten(nav["navigation_tree"])
                formatter.output(flat_list, "Table of Contents")
            else:
                formatter.output(nav, "Table of Contents")

    except Exception as e:
        handle_error(str(e))


@app.command()
def search(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "-n", "--limit", help="Maximum results to show"),
    case_sensitive: bool = typer.Option(False, "-c", "--case-sensitive", help="Case-sensitive search"),
    format: Format = typer.Option(Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Search for text in book content."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        # Process EPUB to get chapters
        result = process_epub(str(path))

        if not result.success:
            handle_error(f"Failed to process EPUB: {', '.join(result.errors)}")

        # Prepare chapters for search
        chapters_for_search = []
        for chapter in result.chapters:
            # Combine content into single string
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

        # Search
        search_service = SearchService(context_size=100)
        results = search_service.search_content(
            chapters_for_search, query, case_sensitive=case_sensitive
        )

        if not results:
            console.print(f"[yellow]No matches found for:[/yellow] {query}")
            raise typer.Exit(ExitCode.NO_RESULTS)

        # Limit results
        results = results[:limit]

        if format == Format.text:
            console.print()
            console.print(f"[bold cyan]Found {len(results)} matches for:[/bold cyan] {query}")
            console.print()

            for i, r in enumerate(results, 1):
                # Highlight match in context
                highlighted = search_service.highlight_matches(
                    r.context, query,
                    highlight_start="[bold yellow]",
                    highlight_end="[/bold yellow]"
                )
                console.print(f"[green]{i}. {r.chapter_title}[/green]")
                console.print(f"   {highlighted}")
                console.print()
        else:
            data = [
                {
                    "chapter_id": r.chapter_id,
                    "chapter_title": r.chapter_title,
                    "context": r.context,
                    "relevance": round(r.relevance_score, 2),
                }
                for r in results
            ]
            formatter.output(data, f"Search Results for: {query}")

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(str(e))


@app.command()
def stats(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    format: Format = typer.Option(Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Display book statistics."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        result = process_epub(str(path))

        if not result.success:
            handle_error(f"Failed to process EPUB: {', '.join(result.errors)}")

        # Calculate statistics
        total_words = result.total_words
        chapter_count = len(result.chapters)
        avg_words_per_chapter = round(total_words / chapter_count, 1) if chapter_count > 0 else 0

        # Find longest and shortest chapters
        chapter_stats = []
        for ch in result.chapters:
            word_count = ch.get("word_count", 0)
            chapter_stats.append({
                "title": ch.get("title", f"Chapter {ch.get('chapter_id', 0)}"),
                "words": word_count,
            })

        chapter_stats.sort(key=lambda x: x["words"], reverse=True)

        data = {
            "total_words": total_words,
            "total_chapters": chapter_count,
            "reading_time": format_reading_time(result.estimated_reading_time),
            "avg_words_per_chapter": avg_words_per_chapter,
            "longest_chapter": chapter_stats[0] if chapter_stats else None,
            "shortest_chapter": chapter_stats[-1] if chapter_stats else None,
            "file_size_mb": result.total_size_mb,
            "total_files": result.total_files,
        }

        if format == Format.text:
            console.print()
            console.print("[bold cyan]Book Statistics[/bold cyan]")
            console.print("-" * 40)
            console.print(f"[green]Total Words:[/green]     {data['total_words']:,}")
            console.print(f"[green]Total Chapters:[/green]  {data['total_chapters']}")
            console.print(f"[green]Reading Time:[/green]    {data['reading_time']}")
            console.print(f"[green]Avg Words/Ch:[/green]    {data['avg_words_per_chapter']:,}")

            longest = chapter_stats[0] if chapter_stats else None
            shortest = chapter_stats[-1] if chapter_stats else None
            if longest:
                console.print(f"[green]Longest Chapter:[/green] {longest['title']} ({longest['words']:,} words)")
            if shortest:
                console.print(f"[green]Shortest Chapter:[/green] {shortest['title']} ({shortest['words']:,} words)")

            console.print(f"[green]File Size:[/green]       {data['file_size_mb']:.2f} MB")
            console.print(f"[green]Total Files:[/green]     {data['total_files']}")
            console.print()
        else:
            formatter.output(data, "Book Statistics")

    except Exception as e:
        handle_error(str(e))


@app.command()
def validate(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    format: Format = typer.Option(Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Validate EPUB structure."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        # Check basic EPUB structure
        extractor = EpubExtractor()
        epub_info = extractor.get_epub_info(str(path))

        # Validate metadata
        service = DublinCoreService()
        validation = service.validate_content_opf(str(path))

        data = {
            "is_valid": validation.get("is_valid", False),
            "quality_score": validation.get("quality_score", 0),
            "epub_info": {
                "total_files": epub_info.get("total_files", 0),
                "html_files": epub_info.get("html_files_count", 0),  # Fixed key name
                "image_files": epub_info.get("image_files_count", 0),  # Fixed key name
                "css_files": epub_info.get("css_files_count", 0),  # Fixed key name
                "size_mb": epub_info.get("total_size_mb", 0),
            },
            "required_fields": validation.get("required_fields", {}),
            "manifest_items": validation.get("manifest_items_count", 0),
            "spine_items": validation.get("spine_items_count", 0),
        }

        if format == Format.text:
            console.print()
            if data["is_valid"]:
                console.print("[bold green]EPUB is valid[/bold green]")
            else:
                console.print("[bold red]EPUB has issues[/bold red]")

            console.print()
            console.print("[bold cyan]Structure[/bold cyan]")
            console.print("-" * 40)
            console.print(f"[green]Total Files:[/green]    {data['epub_info']['total_files']}")
            console.print(f"[green]HTML Files:[/green]     {data['epub_info']['html_files']}")
            console.print(f"[green]Image Files:[/green]    {data['epub_info']['image_files']}")
            console.print(f"[green]CSS Files:[/green]      {data['epub_info']['css_files']}")
            console.print(f"[green]Manifest Items:[/green] {data['manifest_items']}")
            console.print(f"[green]Spine Items:[/green]    {data['spine_items']}")

            console.print()
            console.print("[bold cyan]Required Fields[/bold cyan]")
            console.print("-" * 40)
            for field, present in data["required_fields"].items():
                status = "[green]Present[/green]" if present else "[red]Missing[/red]"
                console.print(f"  {field.title()}: {status}")

            # Show warnings in verbose mode
            if state.verbose:
                warnings = validation.get("warnings", [])
                if warnings:
                    console.print()
                    console.print("[bold yellow]Warnings[/bold yellow]")
                    console.print("-" * 40)
                    for warning in warnings:
                        console.print(f"  [yellow]![/yellow] {warning}")

            console.print()
        else:
            formatter.output(data, "EPUB Validation")

    except Exception as e:
        handle_error(str(e))


# ==================== TIER 2 COMMANDS ====================


@app.command()
def chapters(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    show_all: bool = typer.Option(
        False, "--all", "-a",
        help="Show all content including front/back matter"
    ),
    format: Format = typer.Option(Format.table, "-f", "--format", help="Output format"),
) -> None:
    """List chapters with details.

    By default, shows only actual chapters. Use --all to include front/back matter.
    """
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        result = process_epub(str(path))

        if not result.success:
            handle_error(f"Failed to process EPUB: {', '.join(result.errors)}")

        # Filter chapters based on content_type unless --all is specified
        filtered_chapters = []
        for ch in result.chapters:
            content_type = ch.get("content_type", "chapter")
            if show_all or content_type == "chapter":
                filtered_chapters.append(ch)

        chapters_data = []
        for ch in filtered_chapters:
            data = {
                "id": ch.get("chapter_id", 0),
                "title": ch.get("title", "Untitled"),
                "href": ch.get("href", ""),
                "words": ch.get("word_count", 0),
                "images": len(ch.get("images", [])),
            }
            # Add content_type when showing all
            if show_all:
                data["type"] = ch.get("content_type", "chapter")
            chapters_data.append(data)

        title = "All Content" if show_all else "Chapters"
        if format == Format.text:
            console.print()
            console.print(f"[bold cyan]{title} ({len(chapters_data)} total)[/bold cyan]")
            console.print()
            for ch in chapters_data:
                type_label = f" [{ch['type']}]" if show_all else ""
                console.print(f"[green]{ch['id']:3}.[/green] {ch['title']}{type_label}")
                console.print(f"     Words: {ch['words']:,} | Images: {ch['images']} | File: {ch['href']}")
            console.print()
        else:
            formatter.output(chapters_data, title)

    except Exception as e:
        handle_error(str(e))


@app.command()
def images(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    extract_to: Optional[Path] = typer.Option(
        None, "--extract", "-e",
        help="Extract images to directory"
    ),
    list_files: bool = typer.Option(
        False, "-l", "--list",
        help="List individual image files"
    ),
    format: Format = typer.Option(Format.table, "-f", "--format", help="Output format"),
) -> None:
    """List or extract images from EPUB.

    Examples:
        epub-sage images book.epub               # Show image statistics
        epub-sage images book.epub -l            # List all image files
        epub-sage images book.epub -e ./images/  # Extract images to directory
    """
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        extractor = EpubExtractor()

        # Get list of all files in EPUB
        all_files = extractor.list_epub_contents(str(path))
        image_files = [f for f in all_files if f.lower().endswith(IMAGE_EXTENSIONS)]

        # Extract images if requested
        if extract_to:
            extract_to.mkdir(parents=True, exist_ok=True)
            extracted_count = 0

            for img_path in image_files:
                # Get just the filename
                img_name = Path(img_path).name
                output_path = extract_to / img_name

                # Handle duplicate names
                counter = 1
                while output_path.exists():
                    stem = Path(img_name).stem
                    suffix = Path(img_name).suffix
                    output_path = extract_to / f"{stem}_{counter}{suffix}"
                    counter += 1

                if extractor.extract_single_file(str(path), img_path, str(output_path)):
                    extracted_count += 1
                    verbose_log(f"Extracted: {img_name}")

            info_print(f"[green]Extracted {extracted_count} images to:[/green] {extract_to}")
            return

        # List individual files if requested
        if list_files:
            if format == Format.text:
                console.print()
                console.print(f"[bold cyan]Images ({len(image_files)} files)[/bold cyan]")
                console.print()
                for img in image_files:
                    console.print(f"  {img}")
                console.print()
            else:
                formatter.output([{"path": img} for img in image_files], "Image Files")
            return

        # Default: show statistics (using lightweight ZIP listing - already have image_files)
        cover_count = sum(1 for f in image_files if 'cover' in Path(f).name.lower())
        chapter_images = len(image_files) - cover_count

        data = {
            "total_images": len(image_files),
            "cover_images": cover_count,
            "chapter_images": chapter_images,
        }

        if format == Format.text:
            console.print()
            console.print("[bold cyan]Image Distribution[/bold cyan]")
            console.print("-" * 40)
            console.print(f"[green]Total Images:[/green]      {data['total_images']}")
            console.print(f"[green]Cover Images:[/green]      {data['cover_images']}")
            console.print(f"[green]Chapter Images:[/green]    {data['chapter_images']}")
            console.print()
        else:
            formatter.output(data, "Image Distribution")

    except Exception as e:
        handle_error(str(e))


@app.command("list")
def list_contents(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    filter_type: Optional[str] = typer.Option(
        None, "-t", "--type",
        help="Filter by file type (html, css, images, fonts, all)"
    ),
    format: Format = typer.Option(Format.text, "-f", "--format", help="Output format"),
) -> None:
    """List raw contents of EPUB file.

    Examples:
        epub-sage list book.epub               # List all files
        epub-sage list book.epub -t html       # List only HTML files
        epub-sage list book.epub -t images     # List only image files
        epub-sage list book.epub -f json       # Output as JSON
    """
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        extractor = EpubExtractor()
        all_files = extractor.list_epub_contents(str(path))

        # Filter by type if requested
        if filter_type and filter_type != "all":
            extensions = FILE_TYPE_FILTERS.get(filter_type.lower())
            if extensions:
                all_files = [f for f in all_files if f.lower().endswith(extensions)]
            else:
                handle_error(f"Unknown filter type: {filter_type}. Use: html, css, images, fonts, xml, all")

        if format == Format.text:
            console.print()
            console.print(f"[bold cyan]EPUB Contents ({len(all_files)} files)[/bold cyan]")
            if filter_type:
                console.print(f"[dim]Filter: {filter_type}[/dim]")
            console.print()
            for f in sorted(all_files):
                console.print(f"  {f}")
            console.print()
        else:
            data = [{"path": f, "type": Path(f).suffix[1:] if Path(f).suffix else "unknown"} for f in all_files]
            formatter.output(data, "EPUB Contents")

    except Exception as e:
        handle_error(str(e))


@app.command()
def cover(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    output: Optional[Path] = typer.Option(
        None, "-o", "--output",
        help="Output path for cover image (default: cover.<ext>)"
    ),
    show_info: bool = typer.Option(
        False, "-i", "--info",
        help="Show cover info without extracting"
    ),
) -> None:
    """Extract or display cover image.

    Examples:
        epub-sage cover book.epub                    # Extract to cover.<ext>
        epub-sage cover book.epub -o my-cover.jpg   # Extract to custom path
        epub-sage cover book.epub -i                 # Show cover info only
    """
    path = validate_epub_path(path)

    try:
        extractor = EpubExtractor()
        all_files = extractor.list_epub_contents(str(path))

        # Find cover image - common patterns
        cover_file = None
        cover_patterns = ['cover.', 'Cover.', 'COVER.', 'cover-image', 'coverimage']

        for f in all_files:
            fname = Path(f).name.lower()
            if any(p.lower() in fname for p in cover_patterns):
                if fname.endswith(IMAGE_EXTENSIONS):
                    cover_file = f
                    break

        # Fallback: look for cover in manifest (typically first image)
        if not cover_file:
            image_files = [f for f in all_files if f.lower().endswith(IMAGE_EXTENSIONS)]
            if image_files:
                # Often the cover is in images/ or OEBPS/images/
                for img in image_files:
                    if 'cover' in img.lower():
                        cover_file = img
                        break
                # If still not found, take first image as fallback
                if not cover_file and image_files:
                    cover_file = image_files[0]

        if not cover_file:
            handle_error("No cover image found in EPUB")

        # Show info only
        if show_info:
            console.print()
            console.print("[bold cyan]Cover Image[/bold cyan]")
            console.print(f"[green]Path:[/green] {cover_file}")
            console.print(f"[green]Type:[/green] {Path(cover_file).suffix}")
            console.print()
            return

        # Extract cover
        ext = Path(cover_file).suffix
        output_path = output or Path(f"cover{ext}")

        if extractor.extract_single_file(str(path), cover_file, str(output_path)):
            info_print(f"[green]Cover saved to:[/green] {output_path}")
        else:
            handle_error("Failed to extract cover image")

    except Exception as e:
        handle_error(str(e))


@app.command()
def spine(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    format: Format = typer.Option(Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Display reading order (spine).

    The spine defines the default reading order of the EPUB content.
    """
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        service = DublinCoreService()
        spine_items = service.extract_reading_order(str(path))

        if format == Format.text:
            console.print()
            console.print(f"[bold cyan]Reading Order ({len(spine_items)} items)[/bold cyan]")
            console.print()
            for i, item in enumerate(spine_items, 1):
                idref = item.get("idref", "unknown")
                linear = "linear" if item.get("linear", True) else "non-linear"
                console.print(f"  {i:3}. {idref} [{linear}]")
            console.print()
        else:
            formatter.output(spine_items, "Spine (Reading Order)")

    except Exception as e:
        handle_error(str(e))


@app.command()
def manifest(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    filter_type: Optional[str] = typer.Option(
        None, "-t", "--type",
        help="Filter by media type (e.g., 'image', 'text/html')"
    ),
    format: Format = typer.Option(Format.table, "-f", "--format", help="Output format"),
) -> None:
    """Display EPUB manifest (all resources).

    The manifest lists all resources (files) included in the EPUB.
    """
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        service = DublinCoreService()
        parsed = service.parse_content_opf(str(path))

        manifest_items = []
        for item in parsed.manifest:
            media_type = item.get("media_type", item.get("media-type", "unknown"))

            # Filter by type if requested
            if filter_type and filter_type.lower() not in media_type.lower():
                continue

            manifest_items.append({
                "id": item.get("id", "unknown"),
                "href": item.get("href", ""),
                "media_type": media_type,
            })

        if format == Format.text:
            console.print()
            console.print(f"[bold cyan]Manifest ({len(manifest_items)} items)[/bold cyan]")
            if filter_type:
                console.print(f"[dim]Filter: {filter_type}[/dim]")
            console.print()
            for item in manifest_items:
                console.print(f"  [green]{item['id']}[/green]")
                console.print(f"    {item['href']} ({item['media_type']})")
            console.print()
        else:
            formatter.output(manifest_items, "Manifest")

    except Exception as e:
        handle_error(str(e))


# Entry point
def cli_entry() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli_entry()
