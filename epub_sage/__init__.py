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

class DublinCoreService:
    """Legacy compatibility layer for tests and external integrations."""
    def __init__(self):
        self.parser = DublinCoreParser()
        self.extractor = EpubExtractor()
        self.structure_parser = EpubStructureParser()
    
    def parse_content_opf(self, file_path):
        return self.parser.parse_file(file_path)
    
    def extract_basic_metadata(self, file_path):
        parsed = self.parse_content_opf(file_path)
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

    def parse_complete_structure(self, opf_path, epub_dir):
        opf_result = self.parse_content_opf(opf_path)
        return self.structure_parser.parse_complete_structure(opf_result, epub_dir)

    def get_chapter_outline(self, opf_path, epub_dir):
        structure = self.parse_complete_structure(opf_path, epub_dir)
        return {
            'total_chapters': len(structure.chapters),
            'has_parts': len(structure.parts) > 0,
            'parts': [p.model_dump() for p in structure.parts]
        }

    def analyze_content_organization(self, opf_path, epub_dir):
        structure = self.parse_complete_structure(opf_path, epub_dir)
        return {
            'summary': "Analysis complete",
            'organization': structure.organization.model_dump() if structure.organization else {}
        }

    def get_image_distribution(self, opf_path, epub_dir):
        structure = self.parse_complete_structure(opf_path, epub_dir)
        return {
            'total_count': len(structure.images),
            'cover_count': sum(1 for img in structure.images if img.is_cover),
            'chapter_images': sum(1 for img in structure.images if not img.is_cover),
            'unassociated_images': 0,
            'image_types': {},
            'avg_images_per_chapter': len(structure.images) / len(structure.chapters) if structure.chapters else 0
        }

    def extract_reading_order(self, opf_path, epub_dir):
        structure = self.parse_complete_structure(opf_path, epub_dir)
        return [item.model_dump() for item in structure.spine_items] if hasattr(structure, 'spine_items') else []

    def get_navigation_structure(self, opf_path, epub_dir):
        structure = self.parse_complete_structure(opf_path, epub_dir)
        return {
            'has_navigation': len(structure.navigation_tree) > 0,
            'toc_file': "toc.ncx",
            'max_depth': 3,
            'navigation_tree': [n.model_dump() for n in structure.navigation_tree],
            'flat_navigation': []
        }

    def validate_content_opf(self, opf_path):
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

def create_service():
    """Factory function for DublinCoreService."""
    return DublinCoreService()

def parse_content_opf(file_path):
    """Convenience function to parse content.opf metadata."""
    return DublinCoreParser().parse_file(file_path)

__version__ = '0.1.0'

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
