"""Main EPUB processor orchestrator."""

import os
import tempfile
from typing import Dict, List, Optional, Any

from ..extractors.epub_extractor import EpubExtractor
from ..extractors.content_extractor import extract_book_content
from ..core.dublin_core_parser import DublinCoreParser
from ..core.structure_parser import EpubStructureParser

from .result import SimpleEpubResult, create_error_result, create_success_result
from .helpers import enrich_with_sections, calculate_section_stats, calculate_reading_time
from .content_consolidator import (
    process_spine_items, process_non_spine_items,
    process_fallback_content, finalize_chapters
)


class SimpleEpubProcessor:
    """Simple processor for one-step EPUB processing."""

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.extractor = EpubExtractor(base_dir=self.temp_dir)
        self.parser = DublinCoreParser()
        self.structure_parser = EpubStructureParser()

    def process_epub(self, epub_path: str, cleanup: bool = True,
                     include_html: bool = False) -> SimpleEpubResult:
        """Process EPUB file in one step."""
        extracted_dir = None

        try:
            epub_info = self.extractor.get_epub_info(epub_path)
            if not epub_info.get('success'):
                return create_error_result(epub_info.get('error', 'Failed to read EPUB'), epub_info)

            try:
                extracted_dir = self.extractor.extract_epub(epub_path)
            except Exception as e:
                return create_error_result(f"Extraction failed: {str(e)}", epub_info)

            result = self.process_directory(
                extracted_dir, book_id=epub_info.get('book_id'),
                epub_info=epub_info, include_html=include_html
            )

            if cleanup and extracted_dir:
                self.extractor.cleanup_extraction(extracted_dir)

            return result

        except Exception as e:
            if cleanup and extracted_dir:
                self.extractor.cleanup_extraction(extracted_dir)
            return create_error_result(f"Critical error: {str(e)}", {})

    def process_directory(self, extracted_dir: str, book_id: Optional[str] = None,
                          epub_info: Optional[Dict[str, Any]] = None,
                          include_html: bool = False) -> SimpleEpubResult:
        """Process an already extracted EPUB directory."""
        errors: List[str] = []
        _book_id, _total_files, _total_size_mb = self._get_file_info(
            extracted_dir, book_id, epub_info
        )

        try:
            content_opf_path = self.extractor.find_content_opf(extracted_dir)
            parsed_opf, metadata, errors = self._parse_metadata(
                content_opf_path, errors)
            structure, structure_map = self._parse_structure(
                parsed_opf, extracted_dir, errors)

            chapters, total_words, content_found, errors = self._extract_content(
                extracted_dir, parsed_opf, structure_map, errors
            )

            reading_time = calculate_reading_time(total_words)
            enrich_with_sections(
                chapters, structure, extracted_dir, self.structure_parser, include_html)
            finalize_chapters(chapters)
            total_sections, max_section_depth = calculate_section_stats(
                chapters)

            return create_success_result(
                metadata, chapters, total_words, reading_time, _book_id,
                extracted_dir, content_opf_path, errors, _total_files,
                _total_size_mb, total_sections, max_section_depth, content_found
            )

        except Exception as e:
            return create_error_result(f"Processing failed: {str(e)}", {})

    def _get_file_info(self, extracted_dir: str, book_id: Optional[str],
                       epub_info: Optional[Dict]) -> tuple:
        """Get file info from epub_info or calculate from directory."""
        if epub_info:
            return (book_id or '', epub_info.get('total_files', 0),
                    epub_info.get('total_size_mb', 0.0))
        file_count, size_bytes = 0, 0
        for root, _, files in os.walk(extracted_dir):
            file_count += len(files)
            for f in files:
                try:
                    size_bytes += os.path.getsize(os.path.join(root, f))
                except BaseException:
                    pass
        _book_id = book_id or os.path.basename(os.path.dirname(extracted_dir)) or 'local-dir'
        return _book_id, file_count, round(size_bytes / (1024 * 1024), 2)

    def _parse_metadata(self, content_opf_path: Optional[str], errors: list) -> tuple:
        """Parse metadata from content.opf."""
        if not content_opf_path:
            errors.append("No content.opf file found")
            return None, None, errors

        try:
            parsed_opf = self.parser.parse_file(content_opf_path)
            return parsed_opf, parsed_opf.metadata, errors
        except Exception as e:
            errors.append(f"Metadata parsing error: {str(e)}")
            return None, None, errors

    def _parse_structure(self, parsed_opf, extracted_dir: str, errors: list) -> tuple:
        """Parse EPUB structure."""
        if not parsed_opf:
            return None, {}

        try:
            structure = self.structure_parser.parse_complete_structure(
                parsed_opf, extracted_dir)
            structure_map = {}
            for item in (structure.chapters + structure.front_matter +
                         structure.back_matter + structure.parts):
                structure_map[item.href] = item
            return structure, structure_map
        except Exception as e:
            errors.append(f"Structure parsing warning: {str(e)}")
            return None, {}

    def _extract_content(self, extracted_dir: str, parsed_opf, structure_map: Dict,
                         errors: list) -> tuple:
        """Extract and consolidate content."""
        try:
            all_content = extract_book_content(extracted_dir)
            if not all_content:
                errors.append("No content could be extracted from HTML files")
                return [], 0, False, errors

            if parsed_opf:
                chapters, total_words, processed, idx = process_spine_items(
                    parsed_opf, all_content, structure_map, extracted_dir
                )
                extra_chapters, extra_words, _ = process_non_spine_items(
                    all_content, processed, structure_map, idx
                )
                chapters.extend(extra_chapters)
                total_words += extra_words
            else:
                chapters, total_words = process_fallback_content(all_content)

            return chapters, total_words, True, errors

        except Exception as e:
            errors.append(f"Content extraction error: {str(e)}")
            return [], 0, False, errors

    def quick_info(self, epub_path: str) -> Dict[str, Any]:
        """Get quick EPUB information without full processing."""
        epub_info = self.extractor.get_epub_info(epub_path)
        if not epub_info.get('success'):
            return epub_info
        extracted_dir = None
        try:
            extracted_dir = self.extractor.extract_epub(epub_path)
            content_opf_path = self.extractor.find_content_opf(extracted_dir)
            if content_opf_path:
                metadata = self.parser.parse_file(content_opf_path).metadata
                return {"book_id": epub_info['book_id'], "filename": epub_info['filename'],
                        "title": metadata.title or 'Unknown', "author": metadata.get_primary_author() or 'Unknown',
                        "publisher": metadata.publisher, "language": metadata.language, "isbn": metadata.get_isbn(),
                        "total_files": epub_info['total_files'], "total_size_mb": epub_info['total_size_mb'], "success": True}
            return {**epub_info, "title": "Unknown", "author": "Unknown", "warning": "Could not parse metadata"}
        except Exception as e:
            return {**epub_info, "error": f"Metadata extraction failed: {str(e)}", "success": False}
        finally:
            if extracted_dir:
                try:
                    self.extractor.cleanup_extraction(extracted_dir)
                except BaseException:
                    pass


def process_epub(epub_path: str, include_html: bool = False) -> SimpleEpubResult:
    """Convenience function for one-line EPUB processing."""
    processor = SimpleEpubProcessor()
    return processor.process_epub(epub_path, include_html=include_html)
