"""SimpleEpubResult model and result helpers."""

from typing import List, Dict, Optional, Any

from pydantic import BaseModel, Field

from ..models.dublin_core import DublinCoreMetadata


class SimpleEpubResult(BaseModel):
    """Simple result structure for EPUB processing."""
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None
    publication_date: Optional[str] = None

    chapters: List[Dict[str, Any]] = Field(default_factory=list)
    total_chapters: int = 0
    total_words: int = 0
    estimated_reading_time: Dict[str, int] = Field(default_factory=dict)

    book_id: str = ""
    extracted_dir: str = ""
    content_opf_path: Optional[str] = None
    success: bool = False
    errors: List[str] = Field(default_factory=list)

    total_files: int = 0
    total_size_mb: float = 0.0

    total_sections: int = 0
    max_section_depth: int = 0

    full_metadata: Optional[DublinCoreMetadata] = None


def create_error_result(error_message: str, epub_info: Dict[str, Any]) -> SimpleEpubResult:
    """Create error result when processing fails."""
    return SimpleEpubResult(
        title=None,
        author=None,
        publisher=None,
        language=None,
        description=None,
        isbn=None,
        publication_date=None,
        chapters=[],
        total_chapters=0,
        total_words=0,
        estimated_reading_time={'hours': 0, 'minutes': 0},
        book_id=epub_info.get('book_id', ''),
        extracted_dir='',
        content_opf_path=None,
        success=False,
        errors=[error_message],
        total_files=epub_info.get('total_files', 0),
        total_size_mb=epub_info.get('total_size_mb', 0.0),
        full_metadata=None
    )


def create_success_result(
    metadata,
    chapters: List[Dict],
    total_words: int,
    reading_time: Dict[str, int],
    book_id: str,
    extracted_dir: str,
    content_opf_path: Optional[str],
    errors: List[str],
    total_files: int,
    total_size_mb: float,
    total_sections: int,
    max_section_depth: int,
    content_found: bool
) -> SimpleEpubResult:
    """Create successful processing result."""
    is_success = (metadata is not None or content_found) and (
        len(errors) < 5 or content_found)

    return SimpleEpubResult(
        title=metadata.title if metadata else 'Unknown Title',
        author=metadata.get_primary_author() if metadata else 'Unknown Author',
        publisher=metadata.publisher if metadata else None,
        language=metadata.language if metadata else None,
        description=metadata.description if metadata else None,
        isbn=metadata.get_isbn() if metadata else None,
        publication_date=metadata.get_publication_date() if metadata else None,
        chapters=chapters,
        total_chapters=len(chapters),
        total_words=total_words,
        estimated_reading_time=reading_time,
        book_id=book_id,
        extracted_dir=extracted_dir,
        content_opf_path=content_opf_path,
        success=is_success,
        errors=errors,
        total_files=total_files,
        total_size_mb=total_size_mb,
        total_sections=total_sections,
        max_section_depth=max_section_depth,
        full_metadata=metadata
    )
