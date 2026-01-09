"""Manifest item handling and classification."""

import logging
from pathlib import Path
from typing import Dict, Optional

from ..models.structure import StructureItem, ImageItem, EpubStructure, ContentType
from .content_classifier import ContentClassifier

logger = logging.getLogger(__name__)


def classify_manifest_items(opf_result, structure: EpubStructure, classifier: ContentClassifier,
                            epub_dir: Optional[str] = None):
    """Classify all manifest items into structural categories."""
    logger.debug(
        f"Classifying {len(opf_result.manifest_items)} manifest items")

    for order, item in enumerate(opf_result.manifest_items):
        item_id = item.get('id', '')
        href = item.get('href', '')
        media_type = item.get('media-type', '')

        content_type = classifier.classify_content_item(
            item_id, href, media_type)

        if content_type == ContentType.IMAGE:
            image_item = create_image_item(
                item, order, opf_result, epub_dir, classifier)
            structure.images.append(image_item)
        elif content_type in [ContentType.STYLESHEET, ContentType.FONT]:
            asset_item = create_structure_item(
                item, content_type, order, opf_result, epub_dir, classifier)
            if content_type == ContentType.STYLESHEET:
                structure.stylesheets.append(asset_item)
            else:
                structure.fonts.append(asset_item)
        else:
            content_item = create_structure_item(
                item, content_type, order, opf_result, epub_dir, classifier)
            categorize_content_item(content_item, structure)


def create_structure_item(manifest_item: Dict[str, str], content_type: ContentType, order: int,
                          opf_result, epub_dir: Optional[str], classifier: ContentClassifier) -> StructureItem:
    """Create StructureItem from manifest item."""
    item_id = manifest_item.get('id', '')
    raw_href = manifest_item.get('href', '')

    href = raw_href
    if opf_result and epub_dir:
        href = opf_result.resolve_href(raw_href, epub_dir)

    media_type = manifest_item.get('media-type', '')
    properties = manifest_item.get('properties', '').split(
    ) if manifest_item.get('properties') else []

    title = generate_title_from_id(item_id)
    chapter_num = classifier.extract_chapter_number(item_id, href)
    part_num = classifier.extract_part_number(item_id, href)

    return StructureItem(
        id=item_id, title=title, href=href, content_type=content_type, order=order,
        chapter_number=chapter_num, part_number=part_num, media_type=media_type,
        properties=properties, linear=False
    )


def create_image_item(manifest_item: Dict[str, str], order: int, opf_result,
                      epub_dir: Optional[str], classifier: ContentClassifier) -> ImageItem:
    """Create ImageItem from manifest item."""
    item_id = manifest_item.get('id', '')
    raw_href = manifest_item.get('href', '')

    href = raw_href
    if opf_result and epub_dir:
        href = opf_result.resolve_href(raw_href, epub_dir)

    media_type = manifest_item.get('media-type', '')
    properties = manifest_item.get('properties', '').split(
    ) if manifest_item.get('properties') else []

    filename = Path(href).name
    image_type = classifier.classify_image_type(filename, item_id)
    is_cover = 'cover-image' in properties or 'cover' in item_id.lower() or image_type == 'cover'
    chapter_num = classifier.extract_chapter_from_image_name(filename)

    return ImageItem(
        id=item_id, filename=filename, href=href, media_type=media_type,
        image_type=image_type, is_cover=is_cover, chapter_number=chapter_num
    )


def categorize_content_item(item: StructureItem, structure: EpubStructure):
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


def generate_title_from_id(item_id: str) -> str:
    """Generate human-readable title from item ID."""
    title = item_id.replace('_', ' ').replace('-', ' ')
    words = title.split()
    cleaned_words = []
    for word in words:
        if word.lower() in ['id', 'idref', 'href']:
            continue
        if word.isdigit():
            cleaned_words.append(word)
        else:
            cleaned_words.append(word.capitalize())
    return ' '.join(cleaned_words) if cleaned_words else item_id
