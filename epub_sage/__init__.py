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

# Dublin Core Service (extracted to separate module)
from .dublin_core_service import (
    DublinCoreService,
    create_service,
    parse_content_opf
)

__version__ = '0.3.0'

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
