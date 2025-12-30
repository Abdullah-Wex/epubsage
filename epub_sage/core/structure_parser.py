"""
Main EPUB structure parser that integrates all components.

Combines Dublin Core metadata, manifest analysis, and TOC parsing to provide
comprehensive EPUB structure understanding.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..models.dublin_core import ParsedContentOpf
from ..models.structure import (
    EpubStructure, StructureItem, ImageItem, NavigationPoint,
    ContentOrganization, ContentType
)
from .content_classifier import ContentClassifier
from .toc_parser import TocParser


logger = logging.getLogger(__name__)


class EpubStructureParser:
    """
    Main parser for EPUB structure analysis.

    Integrates all components to provide comprehensive structure understanding
    while following SOLID principles and keeping complexity manageable (KISS).
    """

    def __init__(self):
        self.classifier = ContentClassifier()
        self.toc_parser = TocParser()
        self.parsing_errors = []

    def parse_complete_structure(self, opf_result: ParsedContentOpf,
                               epub_dir: Optional[str] = None) -> EpubStructure:
        """
        Parse complete EPUB structure from content.opf result.

        Args:
            opf_result: Parsed content.opf data
            epub_dir: Directory containing extracted EPUB files

        Returns:
            EpubStructure with complete structural analysis
        """
        return self.parse_structure(opf_result, epub_dir)

    def parse_structure(self, opf_result: ParsedContentOpf,
                        epub_dir: Optional[str] = None) -> EpubStructure:
        """
        Deprecated. Use parse_complete_structure instead.
        """
        logger.info("Starting EPUB structure analysis")
        self.parsing_errors = []

        structure = EpubStructure()

        # Store context for path resolution
        self._opf_result = opf_result
        self._epub_dir = epub_dir

        # Step 1: Classify and organize manifest items
        self._classify_manifest_items(opf_result, structure)

        # Step 2: Parse TOC if available
        if epub_dir:
            self._parse_toc_structure(epub_dir, structure)

        # Step 3: Associate images with chapters
        self._associate_images_with_content(structure, epub_dir)

        # Step 4: Build reading order
        self._build_reading_order(opf_result, structure)

        # Step 5: Generate organization summary
        self._generate_organization_summary(structure)

        # Step 6: Cross-validate structure
        self._validate_structure(structure)

        structure.parsing_errors = self.parsing_errors
        logger.info(
            f"Structure analysis complete. Found {len(structure.chapters)} chapters, {len(structure.images)} images")

        return structure

    def _classify_manifest_items(
            self,
            opf_result: ParsedContentOpf,
            structure: EpubStructure):
        """Classify all manifest items into structural categories."""
        logger.debug(
            f"Classifying {len(opf_result.manifest_items)} manifest items")

        for order, item in enumerate(opf_result.manifest_items):
            item_id = item.get('id', '')
            href = item.get('href', '')
            media_type = item.get('media-type', '')

            # Classify content type
            content_type = self.classifier.classify_content_item(
                item_id, href, media_type)

            if content_type == ContentType.IMAGE:
                # Create image item
                image_item = self._create_image_item(item, order)
                structure.images.append(image_item)

            elif content_type in [ContentType.STYLESHEET, ContentType.FONT]:
                # Create asset item
                asset_item = self._create_structure_item(
                    item, content_type, order)
                if content_type == ContentType.STYLESHEET:
                    structure.stylesheets.append(asset_item)
                else:
                    structure.fonts.append(asset_item)

            else:
                # Create content item
                content_item = self._create_structure_item(
                    item, content_type, order)
                self._categorize_content_item(content_item, structure)

    def _create_structure_item(self,
                               manifest_item: Dict[str,
                                                   str],
                               content_type: ContentType,
                               order: int) -> StructureItem:
        """Create StructureItem from manifest item."""
        item_id = manifest_item.get('id', '')
        raw_href = manifest_item.get('href', '')

        # Resolve path to be relative to EPUB root if context is available
        href = raw_href
        if self._opf_result and self._epub_dir:
            href = self._opf_result.resolve_href(raw_href, self._epub_dir)

        media_type = manifest_item.get('media-type', '')
        properties = manifest_item.get('properties', '').split(
        ) if manifest_item.get('properties') else []

        # Extract title from ID (fallback)
        title = self._generate_title_from_id(item_id)

        # Extract numbers
        chapter_num = self.classifier.extract_chapter_number(item_id, href)
        part_num = self.classifier.extract_part_number(item_id, href)

        # Determine if in spine (linear reading)
        linear = item_id in [
            item for item in getattr(
                self, '_spine_items', [])]

        return StructureItem(
            id=item_id,
            title=title,
            href=href,
            content_type=content_type,
            order=order,
            chapter_number=chapter_num,
            part_number=part_num,
            media_type=media_type,
            properties=properties,
            linear=linear
        )

    def _create_image_item(
            self, manifest_item: Dict[str, str], order: int) -> ImageItem:
        """Create ImageItem from manifest item."""
        item_id = manifest_item.get('id', '')
        raw_href = manifest_item.get('href', '')

        # Resolve path to be relative to EPUB root if context is available
        href = raw_href
        if self._opf_result and self._epub_dir:
            href = self._opf_result.resolve_href(raw_href, self._epub_dir)

        media_type = manifest_item.get('media-type', '')
        properties = manifest_item.get('properties', '').split(
        ) if manifest_item.get('properties') else []

        filename = Path(href).name

        # Classify image type
        image_type = self.classifier.classify_image_type(filename, item_id)

        # Check if cover image
        is_cover = ('cover-image' in properties or
                    'cover' in item_id.lower() or
                    image_type == 'cover')

        # Extract chapter association
        chapter_num = self.classifier.extract_chapter_from_image_name(filename)

        return ImageItem(
            id=item_id,
            filename=filename,
            href=href,
            media_type=media_type,
            image_type=image_type,
            is_cover=is_cover,
            chapter_number=chapter_num
        )

    def _categorize_content_item(
            self,
            item: StructureItem,
            structure: EpubStructure):
        """Categorize content item into appropriate structure list."""
        if item.content_type == ContentType.CHAPTER:
            structure.chapters.append(item)
        elif item.content_type == ContentType.PART:
            structure.parts.append(item)
        elif item.content_type == ContentType.FRONT_MATTER:
            structure.front_matter.append(item)
        elif item.content_type == ContentType.BACK_MATTER:
            structure.back_matter.append(item)
        elif item.content_type == ContentType.INDEX:
            structure.index_items.append(item)
        # Other types are handled elsewhere or ignored

    def _parse_toc_structure(self, epub_dir: str, structure: EpubStructure):
        """Parse TOC file to extract navigation structure."""
        epub_path = Path(epub_dir)

        # Look for TOC files in common locations
        toc_candidates = [
            epub_path / "toc.ncx",
            epub_path / "OEBPS" / "toc.ncx",
            epub_path / "nav.xhtml",
            epub_path / "OEBPS" / "nav.xhtml",
            epub_path / "toc.xhtml",
            epub_path / "OEBPS" / "toc.xhtml",
        ]

        toc_file = None
        for candidate in toc_candidates:
            if candidate.exists():
                toc_file = candidate
                break

        if not toc_file:
            logger.warning("No TOC file found")
            return

        logger.debug(f"Parsing TOC file: {toc_file}")

        try:
            nav_points = self.toc_parser.parse_toc_file(str(toc_file))

            # Normalize navigation points to EPUB root paths
            if epub_dir:
                self._normalize_navigation_points(
                    nav_points, str(toc_file), epub_dir)

            structure.navigation_tree = nav_points
            structure.toc_file_path = str(toc_file)

            # Update content items with TOC information
            self._enhance_items_with_toc_info(structure, nav_points)

        except Exception as e:
            logger.error(f"Error parsing TOC file: {e}")
            self.parsing_errors.append(f"TOC parsing error: {e}")

    def _normalize_navigation_points(
            self,
            nav_points: List[NavigationPoint],
            toc_file_path: str,
            epub_root: str):
        """Recursively normalize navigation point hrefs relative to EPUB root."""
        import os
        toc_dir = os.path.dirname(os.path.abspath(toc_file_path))
        epub_root_abs = os.path.abspath(epub_root)

        for point in nav_points:
            if not point.href:
                continue

            # Normalize href
            parts = point.href.split('#', 1)
            pure_href = parts[0]
            fragment = f"#{parts[1]}" if len(parts) > 1 else ""

            # Handle absolute paths or already normalized paths if necessary
            # (usually they are relative to the TOC file)
            abs_target = os.path.normpath(os.path.join(toc_dir, pure_href))
            try:
                rel_path = os.path.relpath(abs_target, epub_root_abs)
                point.href = rel_path.replace('\\', '/') + fragment
            except Exception:
                pass

            if point.children:
                self._normalize_navigation_points(
                    point.children, toc_file_path, epub_root)

    def _enhance_items_with_toc_info(
            self,
            structure: EpubStructure,
            nav_points: List[NavigationPoint]):
        """Enhance structure items with information from TOC."""
        # Create mapping of href to navigation info
        nav_map: Dict[str, List[NavigationPoint]] = {}
        for nav_point in self.toc_parser.flatten_navigation_tree(nav_points):
            # Clean href (remove fragments)
            clean_href = nav_point.href.split('#')[0]
            if clean_href not in nav_map:
                nav_map[clean_href] = []
            nav_map[clean_href].append(nav_point)

        # Update structure items with TOC titles and hierarchy
        all_items = (
            structure.chapters +
            structure.parts +
            structure.front_matter +
            structure.back_matter +
            structure.index_items)

        for item in all_items:
            clean_href = item.href.split('#')[0]
            if clean_href in nav_map:
                nav_info = nav_map[clean_href]
                # Use the first (main) navigation entry for title
                if nav_info and nav_info[0].label:
                    item.title = nav_info[0].label

                # Update section numbering
                section_num = self.classifier.detect_section_numbering(
                    item.title)
                if section_num:
                    item.section_number = section_num

        # Associate chapters with parts based on order and structure
        self._associate_chapters_with_parts(structure)

    def _associate_chapters_with_parts(self, structure: EpubStructure):
        """Associate chapters with parts based on order and structure."""
        if not structure.parts or not structure.chapters:
            return

        # Sort parts and chapters by order
        sorted_parts = sorted(structure.parts, key=lambda x: x.order)
        sorted_chapters = sorted(structure.chapters, key=lambda x: x.order)

        # Simple distribution: assign chapters to parts based on order
        chapters_per_part = len(sorted_chapters) // len(sorted_parts)
        remaining_chapters = len(sorted_chapters) % len(sorted_parts)

        chapter_index = 0
        for part_index, part in enumerate(sorted_parts):
            # Calculate how many chapters for this part
            chapters_for_this_part = chapters_per_part
            if part_index < remaining_chapters:
                chapters_for_this_part += 1

            # Assign chapters to this part
            for _ in range(chapters_for_this_part):
                if chapter_index < len(sorted_chapters):
                    sorted_chapters[chapter_index].part_number = part.part_number
                    chapter_index += 1

    def _associate_images_with_content(
            self,
            structure: EpubStructure,
            epub_dir: Optional[str] = None):
        """Associate images with chapters and content based on naming patterns and content discovery."""
        logger.debug(
            f"Associating {len(structure.images)} images with content")

        # Build discovery map from HTML content if epub_dir is provided
        discovery_map = {}
        if epub_dir:
            try:
                # Import here to avoid circular dependency
                from ..extractors.content_extractor import extract_book_content
                content_data = extract_book_content(epub_dir)
                for file_href, sections in content_data.items():
                    for section in sections:
                        for img_href in section.get('images', []):
                            discovery_map[img_href] = file_href
            except Exception as e:
                logger.warning(f"Content-based image discovery failed: {e}")

        for image in structure.images:
            # 1. Try discovery map first (most accurate)
            if image.href in discovery_map:
                file_href = discovery_map[image.href]
                content_item = self._find_item_by_href(structure, file_href)
                if content_item:
                    image.associated_content_id = content_item.id
                    if content_item.chapter_number:
                        image.chapter_number = content_item.chapter_number
                    continue

            # 2. Fallback to naming patterns
            if image.chapter_number is None:
                # Try to infer chapter association from other images or context
                image.chapter_number = self._infer_chapter_from_context(
                    image, structure)

            # Find associated content item by chapter number
            if image.chapter_number:
                matching_chapters = [
                    ch for ch in structure.chapters if ch.chapter_number == image.chapter_number]
                if matching_chapters:
                    image.associated_content_id = matching_chapters[0].id

    def _find_item_by_href(
            self,
            structure: EpubStructure,
            href: str) -> Optional[StructureItem]:
        """Find a structure item by its href."""
        all_items = (
            structure.chapters +
            structure.parts +
            structure.front_matter +
            structure.back_matter +
            structure.index_items)
        for item in all_items:
            if item.href == href:
                return item
        return None

    def _infer_chapter_from_context(
            self,
            image: ImageItem,
            structure: EpubStructure) -> Optional[int]:
        """Infer chapter number from image context and patterns."""
        # If image is clearly a cover, don't associate with chapter
        if image.is_cover or image.image_type == 'cover':
            return None

        # Look for chapter references in image path
        path_parts = Path(image.href).parts
        for part in path_parts:
            chapter_num = self.classifier.extract_chapter_number("", part)
            if chapter_num:
                return chapter_num

        # Fallback: associate with nearest chapter by order if no explicit
        # pattern found
        if not image.chapter_number and structure.chapters:
            # Simple proximity-based assignment for unassociated images
            # Distribute images evenly across chapters based on manifest order
            total_chapters = len(structure.chapters)
            if total_chapters > 0:
                # Get image position in manifest (rough approximation)
                image_name = Path(image.href).name
                # Use simple hash-based distribution for consistency
                chapter_index = hash(image_name) % total_chapters
                return structure.chapters[chapter_index].chapter_number

        return None

    def _build_reading_order(
            self,
            opf_result: ParsedContentOpf,
            structure: EpubStructure):
        """Build reading order from spine information."""
        structure.reading_order = opf_result.spine_items.copy()

        # Store spine items for linear determination
        self._spine_items = opf_result.spine_items

        # Update linear property for all items
        all_items = (
            structure.chapters +
            structure.parts +
            structure.front_matter +
            structure.back_matter +
            structure.index_items)

        for item in all_items:
            item.linear = item.id in opf_result.spine_items

    def _generate_organization_summary(self, structure: EpubStructure):
        """Generate organization summary statistics."""
        org = ContentOrganization()

        # Basic counts
        org.total_chapters = len(structure.chapters)
        org.total_parts = len(structure.parts)
        org.total_images = len(structure.images)

        # Flags
        org.has_index = len(structure.index_items) > 0
        org.has_toc = len(structure.navigation_tree) > 0
        org.has_parts = len(structure.parts) > 0

        # Content counts
        org.front_matter_count = len(structure.front_matter)
        org.back_matter_count = len(structure.back_matter)

        # Structure analysis
        if structure.navigation_tree:
            flattened_nav = self.toc_parser.flatten_navigation_tree(
                structure.navigation_tree)
            org.max_toc_depth = max(
                [nav.level for nav in flattened_nav], default=1)

        # Image distribution
        org.cover_images_count = len(
            [img for img in structure.images if img.is_cover])

        for image in structure.images:
            if image.chapter_number:
                if image.chapter_number not in org.images_per_chapter:
                    org.images_per_chapter[image.chapter_number] = 0
                org.images_per_chapter[image.chapter_number] += 1

        structure.organization = org

    def _validate_structure(self, structure: EpubStructure):
        """Perform validation and consistency checks on parsed structure."""
        warnings = []

        # Check for chapters without numbers
        unnumbered_chapters = [
            ch for ch in structure.chapters if ch.chapter_number is None]
        if unnumbered_chapters:
            warnings.append(
                f"{len(unnumbered_chapters)} chapters without numbers")

        # Check for duplicate chapter numbers
        chapter_numbers = [
            ch.chapter_number for ch in structure.chapters if ch.chapter_number]
        if len(chapter_numbers) != len(set(chapter_numbers)):
            warnings.append("Duplicate chapter numbers found")

        # Check for images without associations
        unassociated_images = [img for img in structure.images
                               if not img.is_cover and not img.associated_content_id]
        if unassociated_images:
            warnings.append(
                f"{len(unassociated_images)} images not associated with content")

        # Check reading order consistency
        spine_ids = set(structure.reading_order)
        linear_items = [
            item.id for item in (
                structure.chapters +
                structure.front_matter +
                structure.back_matter +
                structure.index_items) if item.linear]
        missing_from_spine = set(linear_items) - spine_ids
        if missing_from_spine:
            warnings.append(
                f"{len(missing_from_spine)} linear items missing from spine")

        if warnings:
            self.parsing_errors.extend(warnings)
            logger.warning(f"Structure validation warnings: {warnings}")

    def _generate_title_from_id(self, item_id: str) -> str:
        """Generate human-readable title from item ID."""
        # Remove common prefixes
        title = item_id

        # Clean up common patterns
        title = title.replace('_', ' ').replace('-', ' ')

        # Capitalize words
        words = title.split()
        cleaned_words = []
        for word in words:
            # Handle special cases
            if word.lower() in ['id', 'idref', 'href']:
                continue
            if word.isdigit():
                cleaned_words.append(word)
            else:
                cleaned_words.append(word.capitalize())

        return ' '.join(cleaned_words) if cleaned_words else item_id
