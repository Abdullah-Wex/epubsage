"""epub-sage CLI - Professional EPUB content extraction and analysis."""

from typing import Any
import typer
from .utils import console
from .commands import (
    info, stats, chapters, toc, search,
    metadata, validate, is_calibre,
    extract, list_contents, images, cover, spine, manifest,
)
from .commands.metadata import state as metadata_state
from .commands.export import state as export_state
from .commands.media import state as media_state
from .commands.images import state as images_state

__version__ = "0.3.0"

app = typer.Typer(
    name="epub-sage",
    help="Professional EPUB content extraction and analysis.",
    no_args_is_help=True,
    pretty_exceptions_enable=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"epub-sage version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V", callback=version_callback, is_eager=True, help="Show version"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress non-error output"),
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable colored output"),
) -> None:
    """EpubSage: Professional EPUB content extraction and analysis."""
    state: Any
    for state in [metadata_state, export_state, media_state, images_state]:
        state.verbose = verbose
        state.quiet = quiet
    if no_color:
        console.no_color = True


# Register commands
app.command()(info)
app.command()(stats)
app.command()(chapters)
app.command()(toc)
app.command()(search)
app.command()(metadata)
app.command()(validate)
app.command(name="is-calibre")(is_calibre)
app.command()(extract)
app.command(name="list")(list_contents)
app.command()(images)
app.command()(cover)
app.command()(spine)
app.command()(manifest)


def cli_entry() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli_entry()
