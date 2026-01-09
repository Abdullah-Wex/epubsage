"""Media commands: cover, spine, manifest."""

import typer
from pathlib import Path
from typing import Optional
from enum import Enum

from ..utils import console, OutputFormatter, handle_error, validate_epub_path
from ... import DublinCoreService, EpubExtractor
from ...extractors.content_extractor import IMAGE_EXTENSIONS


class Format(str, Enum):
    text = "text"
    json = "json"
    table = "table"


class CliState:
    verbose: bool = False
    quiet: bool = False


state = CliState()


def info_print(message: str) -> None:
    if not state.quiet:
        console.print(message)


def cover(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    output: Optional[Path] = typer.Option(
        None, "-o", "--output", help="Output path for cover image"),
    show_info: bool = typer.Option(
        False, "-i", "--info", help="Show cover info without extracting"),
) -> None:
    """Extract or display cover image."""
    path = validate_epub_path(path)

    try:
        extractor = EpubExtractor()
        all_files = extractor.list_epub_contents(str(path))
        cover_file = _find_cover_file(all_files)

        if not cover_file:
            handle_error("No cover image found in EPUB")

        if show_info:
            console.print()
            console.print("[bold cyan]Cover Image[/bold cyan]")
            console.print(f"[green]Path:[/green] {cover_file}")
            console.print(f"[green]Type:[/green] {Path(cover_file).suffix}")
            console.print()
            return

        ext = Path(cover_file).suffix
        output_path = output or Path(f"cover{ext}")

        if extractor.extract_single_file(str(path), cover_file, str(output_path)):
            info_print(f"[green]Cover saved to:[/green] {output_path}")
        else:
            handle_error("Failed to extract cover image")

    except Exception as e:
        handle_error(str(e))


def _find_cover_file(all_files: list) -> Optional[str]:
    cover_patterns = ['cover.', 'Cover.',
                      'COVER.', 'cover-image', 'coverimage']

    for f in all_files:
        fname = Path(f).name.lower()
        if any(p.lower() in fname for p in cover_patterns) and fname.endswith(IMAGE_EXTENSIONS):
            return f

    image_files = [
        f for f in all_files if f.lower().endswith(IMAGE_EXTENSIONS)]
    for img in image_files:
        if 'cover' in img.lower():
            return img

    return image_files[0] if image_files else None


def spine(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    format: Format = typer.Option(
        Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Display reading order (spine)."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        service = DublinCoreService()
        spine_items = service.extract_reading_order(str(path))

        if format == Format.text:
            console.print()
            console.print(
                f"[bold cyan]Reading Order ({len(spine_items)} items)[/bold cyan]")
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


def manifest(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    filter_type: Optional[str] = typer.Option(
        None, "-t", "--type", help="Filter by media type"),
    format: Format = typer.Option(
        Format.table, "-f", "--format", help="Output format"),
) -> None:
    """Display EPUB manifest (all resources)."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        service = DublinCoreService()
        parsed = service.parse_content_opf(str(path))

        manifest_items = []
        for item in parsed.manifest:
            media_type = item.get(
                "media_type", item.get("media-type", "unknown"))
            if filter_type and filter_type.lower() not in media_type.lower():
                continue
            manifest_items.append({
                "id": item.get("id", "unknown"),
                "href": item.get("href", ""),
                "media_type": media_type,
            })

        if format == Format.text:
            console.print()
            console.print(
                f"[bold cyan]Manifest ({len(manifest_items)} items)[/bold cyan]")
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
