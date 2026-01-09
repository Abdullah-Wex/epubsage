"""
Extraction modules for EPUB content and media.
"""
from .epub_extractor import EpubExtractor, quick_extract, get_epub_info
from .content_extractor import extract_content_sections, extract_book_content
from .toc_content_extractor import (
    SectionBoundary,
    ExtractedSection,
    build_section_boundaries,
    extract_section_between_anchors,
    extract_by_toc,
    extract_book_by_toc,
)

__all__ = [
    'EpubExtractor',
    'quick_extract',
    'get_epub_info',
    'extract_content_sections',
    'extract_book_content',
    # TOC-based extraction
    'SectionBoundary',
    'ExtractedSection',
    'build_section_boundaries',
    'extract_section_between_anchors',
    'extract_by_toc',
    'extract_book_by_toc',
]
