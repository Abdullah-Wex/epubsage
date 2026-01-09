"""TOC-Based Content Extractor for EPUB files.

Extracts content between TOC anchor boundaries for precise section splitting.
"""

import os
from typing import List, Dict, Any, Set, Optional

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from ..models.structure import NavigationPoint
from .content_extractor import discover_epub_images, resolve_and_validate_images
from .element_extractors import collect_keywords, collect_references
from .section_builder import (
    SectionBoundary,
    build_section_boundaries,
    extract_section_between_anchors,
)


class ExtractedSection(BaseModel):
    """Content extracted for a single TOC section."""
    nav_point: NavigationPoint
    content_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    text_length: int = 0
    keywords: Optional[List[Dict[str, str]]] = None
    references: Optional[List[Dict[str, str]]] = None


def extract_by_toc(
    html_file_path: str,
    boundaries: List[SectionBoundary],
    valid_images: Set[str],
    all_anchors: Optional[Set[str]] = None,
    include_html: bool = False
) -> List[ExtractedSection]:
    """Extract content from HTML file using TOC-defined boundaries."""
    if not os.path.exists(html_file_path):
        return []

    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            try:
                soup = BeautifulSoup(f, 'lxml-xml')
            except Exception:
                f.seek(0)
                soup = BeautifulSoup(f, 'html.parser')
    except Exception:
        return []

    html_rel_dir = os.path.dirname(html_file_path)

    if all_anchors is None:
        all_anchors = {b.start_anchor for b in boundaries if b.start_anchor}

    sections: List[ExtractedSection] = []

    for boundary in boundaries:
        content_blocks = extract_section_between_anchors(
            soup, boundary.start_anchor, boundary.end_anchor,
            all_anchors, include_html
        )

        keywords: List[Dict[str, str]] = []
        references: List[Dict[str, str]] = []
        if boundary.start_anchor:
            start_elem = soup.find(id=boundary.start_anchor)
            if start_elem:
                indexterms = start_elem.find_all(
                    'a', attrs={'data-type': 'indexterm'})
                keywords = collect_keywords(indexterms)
                xrefs = start_elem.find_all('a', attrs={'data-type': 'xref'})
                references = collect_references(xrefs)

        all_images: List[str] = []
        total_text = 0

        for block in content_blocks:
            block_images = block.get('images', [])
            if block.get('src'):
                block_images = [block['src']] + block_images

            resolved_images = resolve_and_validate_images(
                block_images, html_rel_dir, valid_images
            )

            if 'images' in block:
                block['images'] = resolved_images
            elif block.get('src') and resolved_images:
                block['src'] = resolved_images[0]

            all_images.extend(resolved_images)
            total_text += len(block.get('text', ''))

        sections.append(ExtractedSection(
            nav_point=boundary.nav_point,
            content_blocks=content_blocks,
            images=list(set(all_images)),
            text_length=total_text,
            keywords=keywords if keywords else None,
            references=references if references else None
        ))

    return sections


def extract_book_by_toc(
    epub_directory_path: str,
    nav_points: List[NavigationPoint],
    include_html: bool = False
) -> Dict[str, List[ExtractedSection]]:
    """Extract entire book content using TOC structure."""
    valid_images = discover_epub_images(epub_directory_path)
    boundaries = build_section_boundaries(nav_points)
    all_anchors: Set[str] = {nav.anchor for nav in nav_points if nav.anchor}

    result: Dict[str, List[ExtractedSection]] = {}

    for file_path, file_boundaries in boundaries.items():
        full_path = os.path.join(epub_directory_path, file_path)
        sections = extract_by_toc(
            full_path, file_boundaries, valid_images, all_anchors, include_html)
        if sections:
            result[file_path] = sections

    return result
