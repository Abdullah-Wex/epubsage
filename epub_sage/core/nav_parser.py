"""NAV document parser for EPUB 3.0 table of contents."""

import logging
from typing import List, Optional
from xml.etree import ElementTree as ET

from ..models.structure import NavigationPoint
from .content_classifier import ContentClassifier

logger = logging.getLogger(__name__)


def parse_nav(root: ET.Element, file_path: str,
              classifier: ContentClassifier) -> List[NavigationPoint]:
    """Parse EPUB 3.0 navigation document."""
    nav_elements = root.findall(
        './/nav') + root.findall('.//{http://www.w3.org/1999/xhtml}nav')

    toc_nav = None
    for nav in nav_elements:
        epub_type = nav.get(
            '{http://www.idpf.org/2007/ops}type') or nav.get('epub:type')
        if epub_type == 'toc':
            toc_nav = nav
            break

    if toc_nav is None and nav_elements:
        toc_nav = nav_elements[0]

    if toc_nav is None:
        logger.warning(f"No TOC nav element found in: {file_path}")
        return []

    ol_element = toc_nav.find(
        './/ol') or toc_nav.find('.//{http://www.w3.org/1999/xhtml}ol')
    if ol_element is None:
        ol_element = toc_nav.find(
            './/ul') or toc_nav.find('.//{http://www.w3.org/1999/xhtml}ul')

    if ol_element is None:
        logger.warning(f"No list element found in nav document: {file_path}")
        return []

    return _parse_nav_list(ol_element, classifier, level=1)


def _parse_nav_list(ol_element: ET.Element, classifier: ContentClassifier,
                    level: int = 1, parent_id: Optional[str] = None) -> List[NavigationPoint]:
    """Parse navigation from EPUB 3.0 list structure."""
    nav_points = []
    play_order = 1

    li_elements = ol_element.findall(
        './li') + ol_element.findall('.//{http://www.w3.org/1999/xhtml}li')

    for li_element in li_elements:
        nav_point = _create_nav_point(
            li_element, classifier, level, parent_id, play_order)
        if nav_point:
            nested_list = li_element.find(
                './/ol') or li_element.find('.//{http://www.w3.org/1999/xhtml}ol')
            if nested_list is None:
                nested_list = li_element.find(
                    './/ul') or li_element.find('.//{http://www.w3.org/1999/xhtml}ul')

            if nested_list is not None:
                children = _parse_nav_list(
                    nested_list, classifier, level + 1, nav_point.id)
                nav_point.children = children

            nav_points.append(nav_point)
            play_order += 1

    return nav_points


def _create_nav_point(li_element: ET.Element, classifier: ContentClassifier,
                      level: int, parent_id: Optional[str] = None,
                      play_order: int = 1) -> Optional[NavigationPoint]:
    """Create NavigationPoint from EPUB 3.0 li element."""
    a_element = li_element.find(
        './/a') or li_element.find('.//{http://www.w3.org/1999/xhtml}a')

    if a_element is None:
        logger.warning("No anchor found in nav li element")
        return None

    href = a_element.get('href', '')
    label = a_element.text or ''
    label = label.strip()

    if not label:
        logger.warning(f"Empty label for nav entry: {href}")
        return None

    nav_id = f"nav-{play_order}"
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
