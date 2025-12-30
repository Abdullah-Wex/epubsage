"""
EpubSage - Complete EPUB processing and content extraction library.

Main Features:
- Direct EPUB file processing
- Dublin Core metadata parsing
- Structure and TOC analysis
- Intelligent content extraction
- Flexible JSON export

Quick Start:
    from epub_sage import process_epub

    # Simple one-line processing
    result = process_epub('book.epub')
    print(f"Title: {result.title}")
"""

# Core parsing functionality
from .core import (
    DublinCoreParser,
    EpubStructureParser,
    TocParser,
    ContentClassifier
)

# Extraction functionality
from .extractors import (
    EpubExtractor,
    quick_extract,
    get_epub_info,
    extract_content_sections,
    extract_book_content
)

# Processing pipelines
from .processors import (
    SimpleEpubProcessor,
    SimpleEpubResult,
    process_epub  # Main convenience function
)

# Services
from .services import (
    SearchService,
    SearchResult
)

from .services.export_service import save_to_json

# Models
from .models import (
    DublinCoreMetadata,
    DublinCoreCreator,
    DublinCoreDate,
    DublinCoreSubject,
    DublinCoreIdentifier,
    ParsedContentOpf,
    EpubStructure,
    StructureItem,
    ImageItem,
    NavigationPoint,
    ContentOrganization,
    ContentType
)

# Utilities
from .utils import (
    EpubNamespaces,
    parse_datetime,
    clean_text
)

from .utils.statistics import (
    EpubStatistics,
    calculate_reading_time,
    get_text_statistics
)

from typing import Optional, Tuple
from pathlib import Path


class DublinCoreService:
    """
    Service for EPUB metadata extraction.

    Accepts both .epub files and .opf files as input.
    When given an .epub file, it automatically extracts and parses the content.
    """

    def __init__(self):
        self.parser = DublinCoreParser()
        self.extractor = EpubExtractor()
        self.structure_parser = EpubStructureParser()

    def _resolve_input(self, file_path: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Auto-detect input type and resolve to opf_path and epub_dir.

        Args:
            file_path: Path to .epub or .opf file

        Returns:
            Tuple of (opf_path, epub_dir, temp_dir_to_cleanup)
            - If .epub: extracts and returns paths with temp_dir for cleanup
            - If .opf: returns (file_path, parent_dir, None)
        """
        if file_path.lower().endswith('.epub'):
            extracted_dir = self.extractor.extract_epub(file_path)
            opf_path = self.extractor.find_content_opf(extracted_dir)
            if not opf_path:
                self.extractor.cleanup_extraction(extracted_dir)
                raise FileNotFoundError(f"No content.opf found in {file_path}")
            return opf_path, extracted_dir, extracted_dir
        else:
            # For .opf files, derive epub_dir from parent directory
            epub_dir = str(Path(file_path).parent)
            return file_path, epub_dir, None

    def _cleanup_if_needed(self, temp_dir: Optional[str]) -> None:
        """Clean up temporary extraction directory if it exists."""
        if temp_dir:
            self.extractor.cleanup_extraction(temp_dir)

    def parse_content_opf(self, file_path: str):
        """
        Parse metadata from .epub or .opf file.

        Args:
            file_path: Path to .epub or .opf file

        Returns:
            ParsedContentOpf with metadata and manifest info
        """
        opf_path, _, temp_dir = self._resolve_input(file_path)
        try:
            return self.parser.parse_file(opf_path)
        finally:
            self._cleanup_if_needed(temp_dir)

    def extract_basic_metadata(self, file_path: str) -> dict:
        """
        Extract basic metadata from .epub or .opf file.

        Args:
            file_path: Path to .epub or .opf file

        Returns:
            Dictionary with title, author, publisher, etc.
        """
        opf_path, _, temp_dir = self._resolve_input(file_path)
        try:
            parsed = self.parser.parse_file(opf_path)
            metadata = parsed.metadata
            return {
                'title': metadata.title,
                'author': metadata.get_primary_author() if metadata else None,
                'publisher': metadata.publisher if metadata else None,
                'language': metadata.language if metadata else None,
                'description': metadata.description if metadata else None,
                'isbn': metadata.get_isbn() if metadata else None,
                'epub_version': metadata.epub_version
            }
        finally:
            self._cleanup_if_needed(temp_dir)

    def parse_complete_structure(self, file_path: str, epub_dir: Optional[str] = None):
        """
        Parse complete EPUB structure from .epub or .opf file.

        Args:
            file_path: Path to .epub or .opf file
            epub_dir: Optional directory (auto-detected if .epub provided)

        Returns:
            EpubStructure with chapters, images, navigation, etc.
        """
        opf_path, resolved_epub_dir, temp_dir = self._resolve_input(file_path)
        # Use provided epub_dir if given, otherwise use resolved one
        final_epub_dir = epub_dir or resolved_epub_dir
        try:
            opf_result = self.parser.parse_file(opf_path)
            return self.structure_parser.parse_complete_structure(opf_result, final_epub_dir)
        finally:
            self._cleanup_if_needed(temp_dir)

    def get_chapter_outline(self, file_path: str, epub_dir: Optional[str] = None):
        """Get chapter outline from .epub or .opf file."""
        opf_path, resolved_epub_dir, temp_dir = self._resolve_input(file_path)
        final_epub_dir = epub_dir or resolved_epub_dir
        try:
            opf_result = self.parser.parse_file(opf_path)
            structure = self.structure_parser.parse_complete_structure(opf_result, final_epub_dir)
            return {
                'total_chapters': len(structure.chapters),
                'has_parts': len(structure.parts) > 0,
                'parts': [p.model_dump() for p in structure.parts]
            }
        finally:
            self._cleanup_if_needed(temp_dir)

    def analyze_content_organization(self, file_path: str, epub_dir: Optional[str] = None):
        """Analyze content organization from .epub or .opf file."""
        opf_path, resolved_epub_dir, temp_dir = self._resolve_input(file_path)
        final_epub_dir = epub_dir or resolved_epub_dir
        try:
            opf_result = self.parser.parse_file(opf_path)
            structure = self.structure_parser.parse_complete_structure(opf_result, final_epub_dir)
            return {
                'summary': "Analysis complete",
                'organization': structure.organization.model_dump() if structure.organization else {}
            }
        finally:
            self._cleanup_if_needed(temp_dir)

    def get_image_distribution(self, file_path: str, epub_dir: Optional[str] = None):
        """Get image distribution from .epub or .opf file."""
        opf_path, resolved_epub_dir, temp_dir = self._resolve_input(file_path)
        final_epub_dir = epub_dir or resolved_epub_dir
        try:
            opf_result = self.parser.parse_file(opf_path)
            structure = self.structure_parser.parse_complete_structure(opf_result, final_epub_dir)
            return {
                'total_count': len(structure.images),
                'cover_count': sum(1 for img in structure.images if img.is_cover),
                'chapter_images': sum(1 for img in structure.images if not img.is_cover),
                'unassociated_images': 0,
                'image_types': {},
                'avg_images_per_chapter': len(structure.images) / len(structure.chapters) if structure.chapters else 0
            }
        finally:
            self._cleanup_if_needed(temp_dir)

    def extract_reading_order(self, file_path: str, epub_dir: Optional[str] = None):
        """Extract reading order from .epub or .opf file."""
        opf_path, resolved_epub_dir, temp_dir = self._resolve_input(file_path)
        final_epub_dir = epub_dir or resolved_epub_dir
        try:
            opf_result = self.parser.parse_file(opf_path)
            structure = self.structure_parser.parse_complete_structure(opf_result, final_epub_dir)
            return [item.model_dump() for item in structure.spine_items] if hasattr(structure, 'spine_items') else []
        finally:
            self._cleanup_if_needed(temp_dir)

    def get_navigation_structure(self, file_path: str, epub_dir: Optional[str] = None):
        """Get navigation structure from .epub or .opf file."""
        opf_path, resolved_epub_dir, temp_dir = self._resolve_input(file_path)
        final_epub_dir = epub_dir or resolved_epub_dir
        try:
            opf_result = self.parser.parse_file(opf_path)
            structure = self.structure_parser.parse_complete_structure(opf_result, final_epub_dir)
            return {
                'has_navigation': len(structure.navigation_tree) > 0,
                'toc_file': "toc.ncx",
                'max_depth': 3,
                'navigation_tree': [n.model_dump() for n in structure.navigation_tree],
                'flat_navigation': []
            }
        finally:
            self._cleanup_if_needed(temp_dir)

    def validate_content_opf(self, file_path: str):
        """Validate .epub or .opf file structure."""
        opf_path, _, temp_dir = self._resolve_input(file_path)
        try:
            parsed = self.parser.parse_file(opf_path)
            metadata = parsed.metadata
            return {
                'is_valid': True,
                'quality_score': 1.0,
                'manifest_items_count': len(parsed.manifest),
                'spine_items_count': len(parsed.spine),
                'required_fields': {
                    'title': bool(metadata.title),
                    'creator': len(metadata.creators) > 0,
                    'identifier': len(metadata.identifiers) > 0,
                    'language': bool(metadata.language)
                },
                'optional_fields': {}
            }
        finally:
            self._cleanup_if_needed(temp_dir)


def create_service():
    """Factory function for DublinCoreService."""
    return DublinCoreService()


def parse_content_opf(file_path: str):
    """
    Parse metadata from .epub or .opf file.

    Args:
        file_path: Path to .epub or .opf file

    Returns:
        ParsedContentOpf with metadata and manifest info
    """
    service = DublinCoreService()
    return service.parse_content_opf(file_path)

__version__ = '0.1.1'

# --- Public API Groupings ---

__all__ = [
    # Main convenience function
    'process_epub',

    # Core parsers
    'DublinCoreParser',
    'EpubStructureParser',
    'TocParser',
    'ContentClassifier',

    # Extractors
    'EpubExtractor',
    'quick_extract',
    'get_epub_info',
    'extract_content_sections',
    'extract_book_content',

    # Processors
    'SimpleEpubProcessor',
    'SimpleEpubResult',

    # Services
    'SearchService',
    'SearchResult',
    'save_to_json',

    # Models - Dublin Core
    'DublinCoreMetadata',
    'DublinCoreCreator',
    'DublinCoreDate',
    'DublinCoreSubject',
    'DublinCoreIdentifier',
    'ParsedContentOpf',

    # Models - Structure
    'EpubStructure',
    'StructureItem',
    'ImageItem',
    'NavigationPoint',
    'ContentOrganization',
    'ContentType',

    # Utilities
    'EpubNamespaces',
    'parse_datetime',
    'clean_text',
    'EpubStatistics',
    'calculate_reading_time',
    'get_text_statistics',

    # Legacy compatibility
    'DublinCoreService',
    'create_service',
    'parse_content_opf'
]
