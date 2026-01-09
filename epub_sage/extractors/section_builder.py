"""Section boundary building for TOC-based content extraction."""

from typing import Dict, List, Optional, Set

from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel

from ..models.structure import NavigationPoint
from .element_extractors import extract_element, is_content_container


class SectionBoundary(BaseModel):
    """Defines content boundaries for a TOC section."""
    start_anchor: Optional[str] = None
    end_anchor: Optional[str] = None
    nav_point: NavigationPoint


def build_section_boundaries(
    nav_points: List[NavigationPoint]
) -> Dict[str, List[SectionBoundary]]:
    """Group navigation points by file and compute section boundaries."""
    by_file: Dict[str, List[NavigationPoint]] = {}

    for nav in nav_points:
        file_path = nav.href.split('#')[0] if nav.href else nav.file_path
        if not file_path:
            continue

        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(nav)

    boundaries: Dict[str, List[SectionBoundary]] = {}

    for file_path, nav_list in by_file.items():
        sorted_navs = sorted(nav_list, key=lambda n: n.play_order)

        file_boundaries: List[SectionBoundary] = []
        for i, nav in enumerate(sorted_navs):
            start_anchor = nav.anchor
            end_anchor = sorted_navs[i + 1].anchor if i + \
                1 < len(sorted_navs) else None

            file_boundaries.append(SectionBoundary(
                start_anchor=start_anchor,
                end_anchor=end_anchor,
                nav_point=nav
            ))

        boundaries[file_path] = file_boundaries

    return boundaries


def find_element_by_id(soup: BeautifulSoup, anchor_id: str) -> Optional[Tag]:
    """Find element by ID, checking both id and name attributes."""
    element = soup.find(id=anchor_id)
    if element:
        return element
    return soup.find(attrs={'name': anchor_id})


def extract_container_children(
    container: Tag,
    all_anchors: Set[str],
    include_html: bool = False
) -> List[Dict]:
    """Extract direct children from a container element.

    Stops at child with any TOC anchor ID (subsection boundary).
    """
    content_blocks = []

    for child in container.children:
        if not isinstance(child, Tag):
            continue

        child_id = child.get('id')
        if child_id and child_id in all_anchors:
            break

        if child.find(lambda el: isinstance(el, Tag) and el.get('id') in all_anchors):
            break

        block = extract_element(child, include_html)
        if block is not None:
            content_blocks.append(block)

    return content_blocks


def extract_section_between_anchors(
    soup: BeautifulSoup,
    start_anchor: Optional[str],
    end_anchor: Optional[str],
    all_anchors: Optional[Set[str]] = None,
    include_html: bool = False
) -> List[Dict]:
    """Extract all content between two anchor IDs in an HTML document.

    Supports:
    1. Header-anchored: <h1 id="x">Title</h1><p>content</p>
    2. Container-anchored: <div id="x"><h1>Title</h1><p>content</p></div>
    """
    content_blocks: List[Dict] = []
    all_anchors = all_anchors or set()

    body = soup.find('body')
    if not body:
        return content_blocks

    start_element = None
    if start_anchor:
        start_element = find_element_by_id(soup, start_anchor)
        if not start_element:
            return content_blocks

    end_element = None
    if end_anchor:
        end_element = find_element_by_id(soup, end_anchor)

    if start_element:
        if is_content_container(start_element):
            content_blocks = extract_container_children(
                start_element, all_anchors, include_html)
        else:
            block = extract_element(start_element, include_html)
            if block is not None:
                content_blocks.append(block)

            current = start_element.next_sibling
            while current:
                if isinstance(current, Tag):
                    if end_element and current == end_element:
                        break
                    if end_anchor and current.find(id=end_anchor):
                        break
                    if end_anchor and current.get('id') == end_anchor:
                        break
                    current_id = current.get('id')
                    if current_id and current_id in all_anchors:
                        break

                    block = extract_element(current, include_html)
                    if block is not None:
                        content_blocks.append(block)
                current = current.next_sibling
    else:
        for child in body.children:
            if isinstance(child, Tag):
                if end_element and child == end_element:
                    break
                if end_anchor and child.get('id') == end_anchor:
                    break
                child_id = child.get('id')
                if child_id and child_id in all_anchors:
                    break

                block = extract_element(child, include_html)
                if block is not None:
                    content_blocks.append(block)

    return content_blocks
