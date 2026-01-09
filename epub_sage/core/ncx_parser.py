"""NCX file parser for EPUB 2.0 table of contents."""

import logging
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

from ..models.structure import NavigationPoint
from .content_classifier import ContentClassifier

logger = logging.getLogger(__name__)

NCX_NAMESPACE = "http://www.daisy.org/z3986/2005/ncx/"


def parse_ncx(root: ET.Element, file_path: str,
              classifier: ContentClassifier) -> List[NavigationPoint]:
    """Parse NCX file and return navigation points."""
    namespaces = {'ncx': NCX_NAMESPACE}

    nav_map = root.find('.//ncx:navMap', namespaces)
    if nav_map is None:
        nav_map = root.find('.//navMap')

    if nav_map is None:
        logger.warning(f"No navMap found in NCX file: {file_path}")
        return []

    return _parse_nav_points(nav_map, namespaces, classifier, level=1)


def _parse_nav_points(parent: ET.Element, namespaces: Dict[str, str],
                      classifier: ContentClassifier, level: int = 1,
                      parent_id: Optional[str] = None) -> List[NavigationPoint]:
    """Recursively parse navPoint elements from NCX."""
    nav_points = []

    nav_point_elements = parent.findall('./ncx:navPoint', namespaces)
    if not nav_point_elements:
        nav_point_elements = parent.findall('./navPoint')

    for nav_element in nav_point_elements:
        nav_point = _create_nav_point(
            nav_element, namespaces, classifier, level, parent_id)
        if nav_point:
            children = _parse_nav_points(
                nav_element, namespaces, classifier, level + 1, nav_point.id)
            nav_point.children = children
            nav_points.append(nav_point)

    return nav_points


def _create_nav_point(nav_element: ET.Element, namespaces: Dict[str, str],
                      classifier: ContentClassifier, level: int,
                      parent_id: Optional[str] = None) -> Optional[NavigationPoint]:
    """Create NavigationPoint from NCX navPoint element."""
    nav_id = nav_element.get('id', '')
    play_order = int(nav_element.get('playOrder', '0'))

    nav_label = nav_element.find('./ncx:navLabel/ncx:text', namespaces)
    if nav_label is None:
        nav_label = nav_element.find('./navLabel/text')

    if nav_label is None or not nav_label.text:
        logger.warning(f"No label found for navPoint: {nav_id}")
        return None

    label = nav_label.text.strip()

    content = nav_element.find('./ncx:content', namespaces)
    if content is None:
        content = nav_element.find('./content')

    if content is None:
        logger.warning(f"No content found for navPoint: {nav_id}")
        return None

    href = content.get('src', '')
    file_path, anchor = _parse_href(href)
    nav_type, chapter_num, section_num = _classify_nav_entry(
        label, href, classifier)

    return NavigationPoint(
        id=nav_id, label=label, href=href, play_order=play_order,
        level=level, parent_id=parent_id, file_path=file_path, anchor=anchor,
        nav_type=nav_type, chapter_number=chapter_num, section_number=section_num
    )


def _parse_href(href: str) -> tuple[str, Optional[str]]:
    """Split href into file path and anchor."""
    if '#' in href:
        file_path, anchor = href.split('#', 1)
        return file_path, anchor
    return href, None


def _classify_nav_entry(label: str, href: str,
                        classifier: ContentClassifier) -> tuple[str, Optional[int], Optional[str]]:
    """Classify navigation entry and extract chapter/section numbers."""
    chapter_num = classifier.extract_chapter_number("", href, label)
    section_num = classifier.detect_section_numbering(label)

    label_lower = label.lower()
    href_lower = href.lower()

    if any(term in label_lower for term in ['appendix', 'colophon', 'bibliography']):
        nav_type = "back_matter"
    elif any(term in label_lower for term in ['preface', 'acknowledgment', 'about', 'title']):
        nav_type = "front_matter"
    elif 'index' in label_lower or 'index' in href_lower:
        nav_type = "index"
    elif 'part' in label_lower and chapter_num is None:
        nav_type = "part"
    elif chapter_num is not None:
        nav_type = "chapter"
    elif section_num is not None:
        nav_type = "section"
    else:
        nav_type = "other"

    return nav_type, chapter_num, section_num
