"""
Simple EPUB Processor - One-step processing for ease of use.

Provides a simple interface similar to Epub_service for quick EPUB processing.
"""
import os
import tempfile
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

from ..extractors.epub_extractor import EpubExtractor
from ..extractors.content_extractor import extract_book_content
from ..core.dublin_core_parser import DublinCoreParser
from ..models.dublin_core import DublinCoreMetadata


@dataclass
class SimpleEpubResult:
    """
    Simple result structure for EPUB processing.
    Follows KISS principle with flat, easy-to-use structure.
    """
    # Basic metadata
    title: Optional[str]
    author: Optional[str]
    publisher: Optional[str]
    language: Optional[str]
    description: Optional[str]
    isbn: Optional[str]
    publication_date: Optional[str]

    # Content
    chapters: List[Dict[str, Any]]
    total_chapters: int
    total_words: int
    estimated_reading_time: Dict[str, int]  # hours and minutes

    # Processing info
    book_id: str
    extracted_dir: str
    content_opf_path: Optional[str]
    success: bool
    errors: List[str]

    # File info
    total_files: int
    total_size_mb: float

    # Optional detailed metadata
    full_metadata: Optional[DublinCoreMetadata] = None


class SimpleEpubProcessor:
    """
    Simple processor for one-step EPUB processing.

    Provides an easy-to-use interface that handles extraction, parsing,
    and content processing in a single call.
    """

    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize processor.

        Args:
            temp_dir: Optional temporary directory for extraction
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.extractor = EpubExtractor(base_dir=self.temp_dir)
        self.parser = DublinCoreParser()

    def process_epub(
            self,
            epub_path: str,
            cleanup: bool = True) -> SimpleEpubResult:
        """
        Process EPUB file in one step.

        Args:
            epub_path: Path to EPUB file
            cleanup: Whether to cleanup extracted files after processing

        Returns:
            SimpleEpubResult with all extracted data
        """
        extracted_dir = None

        try:
            # Step 1: Get basic info without extraction
            epub_info = self.extractor.get_epub_info(epub_path)
            if not epub_info.get('success'):
                return self._create_error_result(
                    epub_info.get('error', 'Failed to read EPUB file'),
                    epub_info
                )

            # Step 2: Extract EPUB
            try:
                extracted_dir = self.extractor.extract_epub(epub_path)
            except Exception as e:
                return self._create_error_result(
                    f"Extraction failed: {str(e)}", epub_info)

            # Step 3+ : Process extracted content
            result = self.process_directory(
                extracted_dir,
                book_id=epub_info.get('book_id'),
                epub_info=epub_info)

            # Cleanup if requested
            if cleanup and extracted_dir:
                self.extractor.cleanup_extraction(extracted_dir)

            return result

        except Exception as e:
            if cleanup and extracted_dir:
                self.extractor.cleanup_extraction(extracted_dir)
            return self._create_error_result(f"Critical error: {str(e)}", {})

    def process_directory(self,
                          extracted_dir: str,
                          book_id: Optional[str] = None,
                          epub_info: Optional[Dict[str,
                                                   Any]] = None) -> SimpleEpubResult:
        """
        Process an already extracted EPUB directory.

        Args:
            extracted_dir: Path to directory containing extracted EPUB contents
            book_id: Optional ID for the book
            epub_info: Optional dictionary with basic EPUB file info (from get_epub_info)

        Returns:
            SimpleEpubResult with all extracted data
        """
        errors = []

        # Default values for file info if epub_info is not provided
        _book_id = book_id if book_id is not None else ''
        _total_files = epub_info.get('total_files', 0) if epub_info else 0
        _total_size_mb = epub_info.get(
            'total_size_mb', 0.0) if epub_info else 0.0

        if epub_info is None:
            # Extract basic info from directory if not provided
            file_count = 0
            size_bytes = 0
            for root, _, files in os.walk(extracted_dir):
                file_count += len(files)
                for f in files:
                    try:
                        size_bytes += os.path.getsize(os.path.join(root, f))
                    except BaseException:
                        pass
            _total_files = file_count
            _total_size_mb = round(size_bytes / (1024 * 1024), 2)
            if not _book_id:
                # Use folder name as book_id if not provided
                _book_id = os.path.basename(
                    os.path.dirname(extracted_dir)) or 'local-dir'

        try:
            # Step 3: Find and parse content.opf
            content_opf_path = self.extractor.find_content_opf(extracted_dir)
            if not content_opf_path:
                errors.append("No content.opf file found")
                metadata = None
                parsed_opf = None
            else:
                try:
                    parsed_opf = self.parser.parse_file(content_opf_path)
                    metadata = parsed_opf.metadata
                except Exception as e:
                    errors.append(f"Metadata parsing error: {str(e)}")
                    metadata = None
                    parsed_opf = None

            # Step 4: Extract content
            chapters = []
            total_words = 0
            content_found = False

            try:
                # Extract all content from HTML files
                all_content = extract_book_content(extracted_dir)

                if not all_content:
                    errors.append(
                        "No content could be extracted from HTML files")
                elif parsed_opf:
                    content_found = True
                    # Step 4.1: Universal Inclusion - Use spine to process
                    # files in correct order
                    manifest_map = {item['id']: item['href']
                                    for item in parsed_opf.manifest_items}

                    processed_hrefs = set()
                    chapter_index = 0

                    # Process spine items in order (Reading Order)
                    for idref in parsed_opf.spine_items:
                        raw_href = manifest_map.get(idref)
                        if not raw_href:
                            continue

                        # Resolve path using our normalization logic
                        href = parsed_opf.resolve_href(raw_href, extracted_dir)

                        if href in all_content and href not in processed_hrefs:
                            sections = all_content[href]

                            # Consolidate all sections from this file into one
                            # chapter
                            consolidated_content = []
                            consolidated_images = []
                            main_title = None

                            # Determine main title by joining headers of the first few sections
                            # (e.g., "1" + "Introduction")
                            title_parts = []
                            for section in sections:
                                header = section.get('header')
                                if header and header not in title_parts:
                                    title_parts.append(header)
                                # Stop joining if the section has actual
                                # content beyond just the header
                                if len(section.get('content', [])) > 1:
                                    break

                            main_title = ": ".join(
                                title_parts) if title_parts else None

                            for section in sections:
                                section_content = section.get('content', [])
                                consolidated_content.extend(section_content)
                                consolidated_images.extend(
                                    section.get('images', []))

                            chapter_text = ' '.join([
                                item['text'] for item in consolidated_content
                            ])
                            word_count = len(chapter_text.split())
                            total_words += word_count

                            chapters.append({
                                'chapter_id': chapter_index,
                                'title': main_title or f'Section {chapter_index + 1}',
                                'href': href,
                                'word_count': word_count,
                                'content': consolidated_content,
                                # Deduplicate images
                                'images': list(dict.fromkeys(consolidated_images))
                            })
                            chapter_index += 1
                            processed_hrefs.add(href)

                    # Optional: Add any non-spine files that were extracted but
                    # missed
                    for href, sections in all_content.items():
                        if href not in processed_hrefs:
                            consolidated_content = []
                            consolidated_images = []
                            main_title = None

                            # Determine main title
                            title_parts = []
                            for section in sections:
                                header = section.get('header')
                                if header and header not in title_parts:
                                    title_parts.append(header)
                                if len(section.get('content', [])) > 1:
                                    break
                            main_title = ": ".join(
                                title_parts) if title_parts else None

                            for section in sections:
                                consolidated_content.extend(
                                    section.get('content', []))
                                consolidated_images.extend(
                                    section.get('images', []))

                            chapter_text = ' '.join(
                                [item['text'] for item in consolidated_content])
                            word_count = len(chapter_text.split())
                            total_words += word_count
                            chapters.append({
                                'chapter_id': chapter_index,
                                'title': main_title or f'Extra: {os.path.basename(href)}',
                                'href': href,
                                'word_count': word_count,
                                'content': consolidated_content,
                                'images': list(dict.fromkeys(consolidated_images))
                            })
                            chapter_index += 1
                            processed_hrefs.add(href)
                else:
                    # Fallback if no OPF: just use all_content directly
                    content_found = True
                    chapter_index = 0
                    for href, sections in all_content.items():
                        consolidated_content = []
                        consolidated_images = []
                        main_title = None

                        # Determine main title
                        title_parts = []
                        for section in sections:
                            header = section.get('header')
                            if header and header not in title_parts:
                                title_parts.append(header)
                            if len(section.get('content', [])) > 1:
                                break
                        main_title = ": ".join(
                            title_parts) if title_parts else None

                        for section in sections:
                            consolidated_content.extend(
                                section.get('content', []))
                            consolidated_images.extend(
                                section.get('images', []))

                        chapter_text = ' '.join(
                            [item['text'] for item in consolidated_content])
                        word_count = len(chapter_text.split())
                        total_words += word_count
                        chapters.append({
                            'chapter_id': chapter_index,
                            'title': main_title or f'Section {chapter_index + 1}',
                            'href': href,
                            'word_count': word_count,
                            'content': consolidated_content,
                            'images': list(dict.fromkeys(consolidated_images))
                        })
                        chapter_index += 1

            except Exception as e:
                errors.append(f"Content extraction error: {str(e)}")

            # Step 5: Calculate reading time (250 words per minute average)
            reading_time_minutes = total_words / 250
            reading_time = {
                'hours': int(reading_time_minutes // 60),
                'minutes': int(reading_time_minutes % 60)
            }

            # Determine success based on metadata and content presence
            is_success = (
                metadata is not None or content_found) and (
                len(errors) < 5 or content_found)

            # Create result
            result = SimpleEpubResult(
                # Metadata
                title=metadata.title if metadata else 'Unknown Title',
                author=metadata.get_primary_author() if metadata else 'Unknown Author',
                publisher=metadata.publisher if metadata else None,
                language=metadata.language if metadata else None,
                description=metadata.description if metadata else None,
                isbn=metadata.get_isbn() if metadata else None,
                publication_date=metadata.get_publication_date() if metadata else None,

                # Content
                chapters=chapters,
                total_chapters=len(chapters),
                total_words=total_words,
                estimated_reading_time=reading_time,

                # Processing info
                book_id=_book_id,
                extracted_dir=extracted_dir,
                content_opf_path=content_opf_path,
                success=is_success,
                errors=errors,

                # File info
                total_files=_total_files,
                total_size_mb=_total_size_mb,

                # Full metadata if needed
                full_metadata=metadata
            )

            return result

        except Exception as e:
            return self._create_error_result(
                f"Processing failed: {str(e)}", {})

    def quick_info(self, epub_path: str) -> Dict[str, Any]:
        """
        Get quick EPUB information without full processing.

        Args:
            epub_path: Path to EPUB file

        Returns:
            Dictionary with basic information
        """
        # Get file info
        epub_info = self.extractor.get_epub_info(epub_path)
        if not epub_info.get('success'):
            return epub_info

        # Try to get basic metadata with minimal extraction
        extracted_dir = None
        try:
            # Extract to temporary location
            extracted_dir = self.extractor.extract_epub(epub_path)

            # Find content.opf
            content_opf_path = self.extractor.find_content_opf(extracted_dir)

            if content_opf_path:
                # Parse metadata
                parsed_opf = self.parser.parse_file(content_opf_path)
                metadata = parsed_opf.metadata

                return {
                    "book_id": epub_info['book_id'],
                    "filename": epub_info['filename'],
                    "title": metadata.title or 'Unknown',
                    "author": metadata.get_primary_author() or 'Unknown',
                    "publisher": metadata.publisher,
                    "language": metadata.language,
                    "isbn": metadata.get_isbn(),
                    "total_files": epub_info['total_files'],
                    "total_size_mb": epub_info['total_size_mb'],
                    "success": True
                }
            else:
                return {
                    **epub_info,
                    "title": "Unknown",
                    "author": "Unknown",
                    "warning": "Could not parse metadata"
                }

        except Exception as e:
            return {
                **epub_info,
                "error": f"Metadata extraction failed: {str(e)}",
                "success": False
            }
        finally:
            # Always cleanup temporary extraction
            if extracted_dir:
                try:
                    self.extractor.cleanup_extraction(extracted_dir)
                except BaseException:
                    pass

    def _create_error_result(self,
                             error_message: str,
                             epub_info: Dict[str,
                                             Any]) -> SimpleEpubResult:
        """
        Create error result when processing fails.

        Args:
            error_message: Error description
            epub_info: Basic EPUB info if available

        Returns:
            SimpleEpubResult with error information
        """
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


def process_epub(epub_path: str) -> SimpleEpubResult:
    """
    Convenience function for one-line EPUB processing.

    This is the simplest way to process an EPUB file:

    ```python
    from epub_sage import process_epub
    result = process_epub('book.epub')
    print(f"Title: {result.title}")
    print(f"Chapters: {result.total_chapters}")
    ```

    Args:
        epub_path: Path to EPUB file

    Returns:
        SimpleEpubResult with all extracted data
    """
    processor = SimpleEpubProcessor()
    return processor.process_epub(epub_path)
