"""Main EPUB structure parser - coordinates parsing components."""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from ..models.dublin_core import ParsedContentOpf
from ..models.structure import EpubStructure, NavigationPoint
from ..extractors.toc_content_extractor import extract_book_by_toc, ExtractedSection

from .content_classifier import ContentClassifier
from .toc_parser import TocParser
from .manifest_handler import classify_manifest_items
from .organization_analyzer import (
    associate_images_with_content, build_reading_order,
    generate_organization_summary, validate_structure,
    associate_chapters_with_parts, find_item_by_href
)

logger = logging.getLogger(__name__)


class EpubStructureParser:
    """Main parser for EPUB structure analysis."""

    def __init__(self):
        self.classifier = ContentClassifier()
        self.toc_parser = TocParser()
        self.parsing_errors = []
        self._opf_result = None
        self._epub_dir = None

    def parse_complete_structure(self, opf_result: ParsedContentOpf,
                                 epub_dir: Optional[str] = None) -> EpubStructure:
        """Parse complete EPUB structure from content.opf result."""
        return self.parse_structure(opf_result, epub_dir)

    def parse_structure(self, opf_result: ParsedContentOpf,
                        epub_dir: Optional[str] = None) -> EpubStructure:
        """Parse EPUB structure."""
        logger.info("Starting EPUB structure analysis")
        self.parsing_errors = []
        structure = EpubStructure()

        self._opf_result = opf_result
        self._epub_dir = epub_dir

        classify_manifest_items(opf_result, structure,
                                self.classifier, epub_dir)

        if epub_dir:
            self._parse_toc_structure(epub_dir, structure)

        associate_images_with_content(
            structure, epub_dir, self.classifier,
            lambda s, h: find_item_by_href(s, h)
        )
        build_reading_order(opf_result, structure)
        generate_organization_summary(structure, self.toc_parser)
        validate_structure(structure, self.parsing_errors)

        structure.parsing_errors = self.parsing_errors
        logger.info(
            f"Structure analysis complete. Found {len(structure.chapters)} chapters")
        return structure

    def _parse_toc_structure(self, epub_dir: str, structure: EpubStructure):
        """Parse TOC file to extract navigation structure."""
        toc_file = self._find_toc_file(epub_dir)
        if not toc_file:
            logger.warning("No TOC file found")
            return

        logger.debug(f"Parsing TOC file: {toc_file}")

        try:
            nav_points = self.toc_parser.parse_toc_file(str(toc_file))
            self._normalize_navigation_points(
                nav_points, str(toc_file), epub_dir)

            structure.navigation_tree = nav_points
            structure.toc_file_path = str(toc_file)

            self._enhance_items_with_toc_info(structure, nav_points)
        except Exception as e:
            logger.error(f"Error parsing TOC file: {e}")
            self.parsing_errors.append(f"TOC parsing error: {e}")

    def _find_toc_file(self, epub_dir: str) -> Optional[Path]:
        """Find TOC file in EPUB directory."""
        epub_path = Path(epub_dir)

        if self._opf_result:
            for item in self._opf_result.manifest_items:
                if 'nav' in item.get('properties', ''):
                    href = item.get('href', '')
                    if href:
                        candidate = epub_path / href
                        if candidate.exists():
                            return candidate

        candidates = [
            epub_path / "toc.ncx", epub_path / "OEBPS" / "toc.ncx",
            epub_path / "OPS" / "toc.ncx", epub_path / "nav.xhtml",
            epub_path / "OEBPS" / "nav.xhtml", epub_path / "toc.xhtml",
            epub_path / "OEBPS" / "toc.xhtml",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _normalize_navigation_points(self, nav_points: List[NavigationPoint],
                                     toc_file_path: str, epub_root: str):
        """Normalize navigation point hrefs relative to EPUB root."""
        toc_dir = os.path.dirname(os.path.abspath(toc_file_path))
        epub_root_abs = os.path.abspath(epub_root)

        for point in nav_points:
            if not point.href:
                continue

            parts = point.href.split('#', 1)
            pure_href = parts[0]
            fragment = f"#{parts[1]}" if len(parts) > 1 else ""

            abs_target = os.path.normpath(os.path.join(toc_dir, pure_href))
            try:
                rel_path = os.path.relpath(abs_target, epub_root_abs)
                point.href = rel_path.replace('\\', '/') + fragment
            except Exception:
                pass

            if point.children:
                self._normalize_navigation_points(
                    point.children, toc_file_path, epub_root)

    def _enhance_items_with_toc_info(self, structure: EpubStructure,
                                     nav_points: List[NavigationPoint]):
        """Enhance structure items with TOC information."""
        nav_map: Dict[str, List[NavigationPoint]] = {}
        for nav_point in self.toc_parser.flatten_navigation_tree(nav_points):
            clean_href = nav_point.href.split('#')[0]
            if clean_href not in nav_map:
                nav_map[clean_href] = []
            nav_map[clean_href].append(nav_point)

        all_items = (structure.chapters + structure.parts + structure.front_matter +
                     structure.back_matter + structure.index_items)

        for item in all_items:
            clean_href = item.href.split('#')[0]
            if clean_href in nav_map:
                nav_info = nav_map[clean_href]
                if nav_info and nav_info[0].label:
                    item.title = nav_info[0].label
                section_num = self.classifier.detect_section_numbering(
                    item.title)
                if section_num:
                    item.section_number = section_num

        associate_chapters_with_parts(structure)

    def extract_content_by_toc(self, epub_dir: str, structure: EpubStructure,
                               include_html: bool = False) -> Dict[str, List[ExtractedSection]]:
        """Extract content using TOC-defined boundaries."""
        if not structure.navigation_tree:
            logger.warning(
                "No navigation tree available for TOC-based extraction")
            return {}

        nav_points = self.toc_parser.flatten_navigation_tree(
            structure.navigation_tree)
        logger.info(f"Extracting content for {len(nav_points)} TOC entries")

        extracted = extract_book_by_toc(epub_dir, nav_points, include_html)
        total_sections = sum(len(sections) for sections in extracted.values())
        logger.info(
            f"Extracted {total_sections} sections from {len(extracted)} files")
        return extracted
