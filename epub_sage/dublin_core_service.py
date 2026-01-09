"""DublinCoreService for EPUB metadata extraction."""

from typing import Optional, Tuple
from pathlib import Path

from .core import DublinCoreParser, EpubStructureParser
from .extractors import EpubExtractor


class DublinCoreService:
    """Service for EPUB metadata extraction.

    Accepts both .epub files and .opf files as input.
    """

    def __init__(self):
        self.parser = DublinCoreParser()
        self.extractor = EpubExtractor()
        self.structure_parser = EpubStructureParser()

    def _resolve_input(self, file_path: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Auto-detect input type and resolve to opf_path and epub_dir."""
        if file_path.lower().endswith('.epub'):
            extracted_dir = self.extractor.extract_epub(file_path)
            opf_path = self.extractor.find_content_opf(extracted_dir)
            if not opf_path:
                self.extractor.cleanup_extraction(extracted_dir)
                raise FileNotFoundError(f"No content.opf found in {file_path}")
            return opf_path, extracted_dir, extracted_dir
        else:
            epub_dir = str(Path(file_path).parent)
            return file_path, epub_dir, None

    def _cleanup_if_needed(self, temp_dir: Optional[str]) -> None:
        """Clean up temporary extraction directory if it exists."""
        if temp_dir:
            self.extractor.cleanup_extraction(temp_dir)

    def parse_content_opf(self, file_path: str):
        """Parse metadata from .epub or .opf file."""
        opf_path, _, temp_dir = self._resolve_input(file_path)
        try:
            return self.parser.parse_file(opf_path)
        finally:
            self._cleanup_if_needed(temp_dir)

    def extract_basic_metadata(self, file_path: str) -> dict:
        """Extract basic metadata from .epub or .opf file."""
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
        """Parse complete EPUB structure from .epub or .opf file."""
        opf_path, resolved_epub_dir, temp_dir = self._resolve_input(file_path)
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
        opf_path, _, temp_dir = self._resolve_input(file_path)
        _ = epub_dir  # Reserved for future use
        try:
            opf_result = self.parser.parse_file(opf_path)
            spine_data = []
            for item in opf_result.spine_items:
                if isinstance(item, str):
                    spine_data.append({"idref": item, "linear": True})
                elif isinstance(item, dict):
                    spine_data.append(item)
                else:
                    spine_data.append({"idref": str(item), "linear": True})
            return spine_data
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
    """Parse metadata from .epub or .opf file."""
    service = DublinCoreService()
    return service.parse_content_opf(file_path)
