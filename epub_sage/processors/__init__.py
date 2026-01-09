"""Processing pipelines for EPUB files."""

from .orchestrator import SimpleEpubProcessor, process_epub
from .result import SimpleEpubResult

__all__ = [
    'SimpleEpubProcessor',
    'SimpleEpubResult',
    'process_epub'
]
