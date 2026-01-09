"""Images command: list, extract, analyze images."""

import typer
from pathlib import Path
from typing import Optional
from enum import Enum

from ..utils import console, OutputFormatter, handle_error, validate_epub_path
from ...processors import process_epub
from ... import EpubExtractor
from ...extractors.content_extractor import IMAGE_EXTENSIONS


class Format(str, Enum):
    text = "text"
    json = "json"
    table = "table"


class CliState:
    verbose: bool = False
    quiet: bool = False


state = CliState()


def verbose_log(message: str) -> None:
    if state.verbose and not state.quiet:
        console.print(f"[dim]{message}[/dim]")


def info_print(message: str) -> None:
    if not state.quiet:
        console.print(message)


def images(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    extract_to: Optional[Path] = typer.Option(
        None, "--extract", "-e", help="Extract images to directory"),
    list_files: bool = typer.Option(
        False, "-l", "--list", help="List individual image files"),
    by_section: bool = typer.Option(
        False, "-s", "--by-section", help="Show per-section image distribution"),
    format: Format = typer.Option(
        Format.table, "-f", "--format", help="Output format"),
) -> None:
    """List or extract images from EPUB."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        extractor = EpubExtractor()
        all_files = extractor.list_epub_contents(str(path))
        image_files = [
            f for f in all_files if f.lower().endswith(IMAGE_EXTENSIONS)]

        if extract_to:
            _extract_images(path, extract_to, image_files, extractor)
        elif list_files:
            _list_image_files(image_files, format, formatter)
        elif by_section:
            _show_images_by_section(path)
        else:
            _show_image_stats(image_files, format, formatter)

    except Exception as e:
        handle_error(str(e))


def _extract_images(path: Path, extract_to: Path, image_files: list, extractor) -> None:
    extract_to.mkdir(parents=True, exist_ok=True)
    extracted_count = 0

    for img_path in image_files:
        img_name = Path(img_path).name
        output_path = extract_to / img_name

        counter = 1
        while output_path.exists():
            stem = Path(img_name).stem
            suffix = Path(img_name).suffix
            output_path = extract_to / f"{stem}_{counter}{suffix}"
            counter += 1

        if extractor.extract_single_file(str(path), img_path, str(output_path)):
            extracted_count += 1
            verbose_log(f"Extracted: {img_name}")

    info_print(
        f"[green]Extracted {extracted_count} images to:[/green] {extract_to}")


def _list_image_files(image_files: list, format: Format, formatter) -> None:
    if format == Format.text:
        console.print()
        console.print(
            f"[bold cyan]Images ({len(image_files)} files)[/bold cyan]")
        console.print()
        for img in image_files:
            console.print(f"  {img}")
        console.print()
    else:
        formatter.output([{"path": img} for img in image_files], "Image Files")


def _show_images_by_section(path: Path) -> None:
    result = process_epub(str(path))
    if not result.success:
        handle_error(f"Failed to process EPUB: {', '.join(result.errors)}")

    console.print()
    console.print("[bold cyan]Images by Section[/bold cyan]")
    console.print("-" * 40)

    total_section_images = 0
    for ch in result.chapters:
        sections = ch.get('sections', [])
        if sections:
            ch_img_count = _count_section_images(sections)
            if ch_img_count > 0:
                console.print(f"\n[bold]{ch['title']}[/bold]")
                _print_section_images(sections, indent=1)
                total_section_images += ch_img_count

    if total_section_images == 0:
        console.print("[yellow]No images found in sections[/yellow]")
    else:
        console.print(
            f"\n[dim]Total images in sections: {total_section_images}[/dim]")
    console.print()


def _count_section_images(sections: list) -> int:
    count = 0
    for s in sections:
        count += len(s.get('images', []))
        count += _count_section_images(s.get('subsections', []))
    return count


def _print_section_images(sections: list, indent: int = 0) -> None:
    for section in sections:
        images = section.get('images', [])
        if images or section.get('subsections'):
            prefix = "  " * indent
            if images:
                console.print(
                    f"{prefix}[green]{section['title']}[/green]: {len(images)} images")
            _print_section_images(section.get('subsections', []), indent + 1)


def _show_image_stats(image_files: list, format: Format, formatter) -> None:
    cover_count = sum(
        1 for f in image_files if 'cover' in Path(f).name.lower())
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
        console.print(
            f"[green]Total Images:[/green]      {data['total_images']}")
        console.print(
            f"[green]Cover Images:[/green]      {data['cover_images']}")
        console.print(
            f"[green]Chapter Images:[/green]    {data['chapter_images']}")
        console.print()
    else:
        formatter.output(data, "Image Distribution")
