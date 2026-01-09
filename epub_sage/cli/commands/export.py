"""Export commands: extract, list."""

import typer
import sys
import json
from pathlib import Path
from typing import Optional
from enum import Enum

from ..utils import (
    console, OutputFormatter, DateTimeEncoder, handle_error, validate_epub_path,
)
from ...processors import SimpleEpubProcessor
from ...services.export_service import save_to_json
from ... import EpubExtractor
from ...extractors.content_extractor import IMAGE_EXTENSIONS

FILE_TYPE_FILTERS = {
    "html": ('.html', '.xhtml', '.htm'),
    "css": ('.css',),
    "images": IMAGE_EXTENSIONS,
    "fonts": ('.ttf', '.otf', '.woff', '.woff2'),
    "xml": ('.xml', '.opf', '.ncx'),
}


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


def extract(
    path: Path = typer.Argument(..., help="Path to EPUB file or directory"),
    output: Optional[Path] = typer.Option(
        None, "-o", "--output", help="Output file/directory path"),
    raw: bool = typer.Option(False, "-r", "--raw",
                             help="Extract raw EPUB files to directory"),
    metadata_only: bool = typer.Option(
        False, "-m", "--metadata-only", help="Export only metadata"),
    stdout: bool = typer.Option(
        False, "--stdout", help="Output JSON to stdout"),
    compact: bool = typer.Option(
        False, "--compact", help="Compact JSON output"),
    include_html: bool = typer.Option(
        False, "--include-html", help="Include raw HTML in content blocks"),
) -> None:
    """Extract book content to JSON or raw files."""
    path = validate_epub_path(path)

    try:
        if raw:
            _extract_raw(path, output)
            return

        verbose_log(f"Processing: {path}")
        processor = SimpleEpubProcessor()

        if path.is_dir():
            result = processor.process_directory(
                str(path), include_html=include_html)
        else:
            result = processor.process_epub(
                str(path), include_html=include_html)

        if not result.success:
            handle_error(f"Processing failed: {', '.join(result.errors)}")

        output_data = _build_output_data(result, metadata_only)
        indent = None if compact else 2

        if stdout:
            json_str = json.dumps(output_data, indent=indent,
                                  cls=DateTimeEncoder, ensure_ascii=False)
            sys.stdout.write(json_str + "\n")
        else:
            output_path = output or Path("extracted_book.json")
            save_to_json(output_data, str(output_path), indent=indent)
            info_print(f"[green]Data saved to:[/green] {output_path}")

    except Exception as e:
        handle_error(str(e))


def _extract_raw(path: Path, output: Optional[Path]) -> None:
    extractor = EpubExtractor()
    output_dir = str(output) if output else "./extracted"
    verbose_log(f"Extracting raw files to: {output_dir}")

    extracted_path = extractor.extract_epub(str(path), output_dir)
    info_print(f"[green]Extracted to:[/green] {extracted_path}")

    if state.verbose:
        file_count = sum(1 for _ in Path(
            extracted_path).rglob("*") if _.is_file())
        verbose_log(f"Total files extracted: {file_count}")


def _build_output_data(result, metadata_only: bool) -> dict:
    metadata = result.full_metadata.model_dump() if result.full_metadata else {
        "title": result.title, "author": result.author, "publisher": result.publisher,
        "language": result.language, "description": result.description,
        "isbn": result.isbn, "publication_date": result.publication_date
    }
    statistics = {
        "total_words": result.total_words,
        "reading_time": result.estimated_reading_time,
        "chapter_count": len(result.chapters)
    }

    if metadata_only:
        return {"metadata": metadata, "statistics": statistics}
    return {"metadata": metadata, "statistics": statistics, "chapters": result.chapters, "errors": result.errors}


def list_contents(
    path: Path = typer.Argument(..., help="Path to EPUB file"),
    filter_type: Optional[str] = typer.Option(
        None, "-t", "--type", help="Filter by file type"),
    format: Format = typer.Option(
        Format.text, "-f", "--format", help="Output format"),
) -> None:
    """List raw contents of EPUB file."""
    path = validate_epub_path(path)
    formatter = OutputFormatter(format.value)

    try:
        extractor = EpubExtractor()
        all_files = extractor.list_epub_contents(str(path))

        if filter_type and filter_type != "all":
            extensions = FILE_TYPE_FILTERS.get(filter_type.lower())
            if extensions:
                all_files = [
                    f for f in all_files if f.lower().endswith(extensions)]
            else:
                handle_error(
                    f"Unknown filter type: {filter_type}. Use: html, css, images, fonts, xml, all")

        if format == Format.text:
            console.print()
            console.print(
                f"[bold cyan]EPUB Contents ({len(all_files)} files)[/bold cyan]")
            if filter_type:
                console.print(f"[dim]Filter: {filter_type}[/dim]")
            console.print()
            for f in sorted(all_files):
                console.print(f"  {f}")
            console.print()
        else:
            data = [{"path": f, "type": Path(f).suffix[1:] if Path(
                f).suffix else "unknown"} for f in all_files]
            formatter.output(data, "EPUB Contents")

    except Exception as e:
        handle_error(str(e))
