"""Metadata commands: metadata, validate, is_calibre."""

import typer
from pathlib import Path
from enum import Enum

from ..utils import (
    console, OutputFormatter, handle_error, validate_epub_path,
    format_creator, format_identifier,
)
from ... import DublinCoreService, EpubExtractor
from ...utils.calibre_detector import is_calibre_generated


class Format(str, Enum):
    text = "text"
    json = "json"
    table = "table"


class CliState:
    verbose: bool = False
    quiet: bool = False


state = CliState()


def metadata(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    full: bool = typer.Option(
        False, "--full", help="Show all Dublin Core fields"),
    format: Format = typer.Option(
        Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Display Dublin Core metadata."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        service = DublinCoreService()
        parsed = service.parse_content_opf(str(path))
        meta = parsed.metadata

        if full:
            data = meta.model_dump() if meta else {}
        else:
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
            _print_metadata_text(data)
        else:
            formatter.output(data, "Dublin Core Metadata")

    except Exception as e:
        handle_error(str(e))


def _print_metadata_text(data: dict) -> None:
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


def validate(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    format: Format = typer.Option(
        Format.text, "-f", "--format", help="Output format"),
) -> None:
    """Validate EPUB structure."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        extractor = EpubExtractor()
        epub_info = extractor.get_epub_info(str(path))

        service = DublinCoreService()
        validation = service.validate_content_opf(str(path))

        data = {
            "is_valid": validation.get("is_valid", False),
            "quality_score": validation.get("quality_score", 0),
            "epub_info": {
                "total_files": epub_info.get("total_files", 0),
                "html_files": epub_info.get("html_files_count", 0),
                "image_files": epub_info.get("image_files_count", 0),
                "css_files": epub_info.get("css_files_count", 0),
                "size_mb": epub_info.get("total_size_mb", 0),
            },
            "required_fields": validation.get("required_fields", {}),
            "manifest_items": validation.get("manifest_items_count", 0),
            "spine_items": validation.get("spine_items_count", 0),
        }

        if format == Format.text:
            _print_validation_text(data, validation)
        else:
            formatter.output(data, "EPUB Validation")

    except Exception as e:
        handle_error(str(e))


def _print_validation_text(data: dict, validation: dict) -> None:
    console.print()
    if data["is_valid"]:
        console.print("[bold green]EPUB is valid[/bold green]")
    else:
        console.print("[bold red]EPUB has issues[/bold red]")

    console.print()
    console.print("[bold cyan]Structure[/bold cyan]")
    console.print("-" * 40)
    console.print(
        f"[green]Total Files:[/green]    {data['epub_info']['total_files']}")
    console.print(
        f"[green]HTML Files:[/green]     {data['epub_info']['html_files']}")
    console.print(
        f"[green]Image Files:[/green]    {data['epub_info']['image_files']}")
    console.print(
        f"[green]CSS Files:[/green]      {data['epub_info']['css_files']}")
    console.print(f"[green]Manifest Items:[/green] {data['manifest_items']}")
    console.print(f"[green]Spine Items:[/green]    {data['spine_items']}")

    console.print()
    console.print("[bold cyan]Required Fields[/bold cyan]")
    console.print("-" * 40)
    for field, present in data["required_fields"].items():
        status = "[green]Present[/green]" if present else "[red]Missing[/red]"
        console.print(f"  {field.title()}: {status}")

    if state.verbose:
        warnings = validation.get("warnings", [])
        if warnings:
            console.print()
            console.print("[bold yellow]Warnings[/bold yellow]")
            console.print("-" * 40)
            for warning in warnings:
                console.print(f"  [yellow]![/yellow] {warning}")
    console.print()


def is_calibre(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
) -> None:
    """Check if EPUB was generated/processed by Calibre."""
    path = validate_epub_path(path)

    try:
        extractor = EpubExtractor()
        extracted_dir = extractor.extract_epub(str(path))
        content_opf = extractor.find_content_opf(extracted_dir)

        if not content_opf:
            handle_error("Could not find content.opf")

        result = is_calibre_generated(content_opf)

        if state.quiet:
            raise typer.Exit(0 if result else 1)

        if result:
            console.print(
                "[green]Yes[/green] - This EPUB was generated/processed by Calibre")
        else:
            console.print(
                "[yellow]No[/yellow] - This EPUB was not generated by Calibre")

        raise typer.Exit(0 if result else 1)

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(str(e))
