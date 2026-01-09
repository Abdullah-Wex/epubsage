"""Organization analysis and validation for EPUB structure."""

import logging
from pathlib import Path
from typing import Optional

from ..models.structure import EpubStructure, StructureItem, ImageItem, ContentOrganization

logger = logging.getLogger(__name__)


def associate_images_with_content(structure: EpubStructure, epub_dir: Optional[str],
                                  classifier, find_item_by_href):
    """Associate images with chapters based on content discovery and patterns."""
    logger.debug(f"Associating {len(structure.images)} images with content")

    discovery_map = {}
    if epub_dir:
        try:
            from ..extractors.content_extractor import extract_book_content
            content_data = extract_book_content(epub_dir)
            for file_href, sections in content_data.items():
                for section in sections:
                    for img_href in section.get('images', []):
                        discovery_map[img_href] = file_href
        except Exception as e:
            logger.warning(f"Content-based image discovery failed: {e}")

    for image in structure.images:
        if image.href in discovery_map:
            file_href = discovery_map[image.href]
            content_item = find_item_by_href(structure, file_href)
            if content_item:
                image.associated_content_id = content_item.id
                if content_item.chapter_number:
                    image.chapter_number = content_item.chapter_number
                continue

        if image.chapter_number is None:
            image.chapter_number = infer_chapter_from_context(
                image, structure, classifier)

        if image.chapter_number:
            matching = [
                ch for ch in structure.chapters if ch.chapter_number == image.chapter_number]
            if matching:
                image.associated_content_id = matching[0].id


def infer_chapter_from_context(image: ImageItem, structure: EpubStructure, classifier) -> Optional[int]:
    """Infer chapter number from image context."""
    if image.is_cover or image.image_type == 'cover':
        return None

    for part in Path(image.href).parts:
        chapter_num = classifier.extract_chapter_number("", part)
        if chapter_num:
            return chapter_num

    if not image.chapter_number and structure.chapters:
        total = len(structure.chapters)
        if total > 0:
            image_name = Path(image.href).name
            chapter_index = hash(image_name) % total
            return structure.chapters[chapter_index].chapter_number
    return None


def build_reading_order(opf_result, structure: EpubStructure):
    """Build reading order from spine information."""
    structure.reading_order = opf_result.spine_items.copy()

    all_items = (structure.chapters + structure.parts + structure.front_matter +
                 structure.back_matter + structure.index_items)
    for item in all_items:
        item.linear = item.id in opf_result.spine_items


def generate_organization_summary(structure: EpubStructure, toc_parser):
    """Generate organization summary statistics."""
    org = ContentOrganization()

    org.total_chapters = len(structure.chapters)
    org.total_parts = len(structure.parts)
    org.total_images = len(structure.images)

    org.has_index = len(structure.index_items) > 0
    org.has_toc = len(structure.navigation_tree) > 0
    org.has_parts = len(structure.parts) > 0

    org.front_matter_count = len(structure.front_matter)
    org.back_matter_count = len(structure.back_matter)

    if structure.navigation_tree:
        flattened = toc_parser.flatten_navigation_tree(
            structure.navigation_tree)
        org.max_toc_depth = max([nav.level for nav in flattened], default=1)

    org.cover_images_count = len(
        [img for img in structure.images if img.is_cover])

    for image in structure.images:
        if image.chapter_number:
            if image.chapter_number not in org.images_per_chapter:
                org.images_per_chapter[image.chapter_number] = 0
            org.images_per_chapter[image.chapter_number] += 1

    structure.organization = org


def validate_structure(structure: EpubStructure, parsing_errors: list):
    """Perform validation and consistency checks."""
    warnings = []

    unnumbered = [ch for ch in structure.chapters if ch.chapter_number is None]
    if unnumbered:
        warnings.append(f"{len(unnumbered)} chapters without numbers")

    chapter_nums = [
        ch.chapter_number for ch in structure.chapters if ch.chapter_number]
    if len(chapter_nums) != len(set(chapter_nums)):
        warnings.append("Duplicate chapter numbers found")

    unassociated = [
        img for img in structure.images if not img.is_cover and not img.associated_content_id]
    if unassociated:
        warnings.append(
            f"{len(unassociated)} images not associated with content")

    spine_ids = set(structure.reading_order)
    linear_items = [item.id for item in (structure.chapters + structure.front_matter +
                    structure.back_matter + structure.index_items) if item.linear]
    missing = set(linear_items) - spine_ids
    if missing:
        warnings.append(f"{len(missing)} linear items missing from spine")

    if warnings:
        parsing_errors.extend(warnings)
        logger.warning(f"Structure validation warnings: {warnings}")


def associate_chapters_with_parts(structure: EpubStructure):
    """Associate chapters with parts based on order."""
    if not structure.parts or not structure.chapters:
        return

    sorted_parts = sorted(structure.parts, key=lambda x: x.order)
    sorted_chapters = sorted(structure.chapters, key=lambda x: x.order)

    per_part = len(sorted_chapters) // len(sorted_parts)
    remaining = len(sorted_chapters) % len(sorted_parts)

    chapter_index = 0
    for part_idx, part in enumerate(sorted_parts):
        count = per_part + (1 if part_idx < remaining else 0)
        for _ in range(count):
            if chapter_index < len(sorted_chapters):
                sorted_chapters[chapter_index].part_number = part.part_number
                chapter_index += 1


def find_item_by_href(structure: EpubStructure, href: str) -> Optional[StructureItem]:
    """Find a structure item by its href."""
    all_items = (structure.chapters + structure.parts + structure.front_matter +
                 structure.back_matter + structure.index_items)
    for item in all_items:
        if item.href == href:
            return item
    return None
