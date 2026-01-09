"""Processor helper functions."""

import os
import re
from typing import Dict, Any, List, Optional

from ..extractors.toc_content_extractor import ExtractedSection
from ..models.structure import NavigationPoint


def is_generated_title(title: str) -> bool:
    """Check if title looks auto-generated from manifest ID."""
    if not title:
        return True
    return bool(re.search(r'\d+$', title))


def format_part_roman(part_number: Optional[int]) -> Optional[str]:
    """Convert part number to Roman numeral string."""
    if part_number is None:
        return None
    roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
                      'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX']
    if 1 <= part_number <= 20:
        return roman_numerals[part_number - 1]
    return str(part_number)


def get_chapter_id(href: str) -> str:
    """Extract short ID from href path."""
    return os.path.splitext(os.path.basename(href))[0]


def get_best_title(struct_title: Optional[str], html_title: Optional[str], fallback: str) -> str:
    """Determine best title: prefer HTML header over generated manifest ID."""
    if struct_title and is_generated_title(struct_title) and html_title:
        return html_title
    elif struct_title:
        return struct_title
    return html_title or fallback


def build_nested_section(nav_point: NavigationPoint, content_lookup: Dict[str, ExtractedSection]) -> Dict[str, Any]:
    """Recursively build nested section from NavigationPoint."""
    section_key = nav_point.id
    extracted = content_lookup.get(section_key)

    image_count = 0
    word_count = 0
    if extracted:
        for block in extracted.content_blocks:
            if block.get('type') == 'image':
                image_count += 1
            elif block.get('images'):
                image_count += len(block['images'])
            word_count += len(block.get('text', '').split())

    section = {
        'id': nav_point.anchor or nav_point.id,
        'title': nav_point.label,
        'level': nav_point.level,
        'word_count': word_count,
        'content': extracted.content_blocks if extracted else [],
        'subsections': [build_nested_section(child, content_lookup) for child in nav_point.children]
    }
    if extracted and extracted.keywords:
        section['keywords'] = extracted.keywords
    if extracted and extracted.references:
        section['references'] = extracted.references
    return section


def enrich_with_sections(chapters: List[Dict], structure: Any, extracted_dir: str,
                         structure_parser: Any, include_html: bool = False) -> None:
    """Add nested sections to chapters matching TOC tree structure."""
    if not structure or not structure.navigation_tree:
        for chapter in chapters:
            chapter['sections'] = []
        return

    toc_content = structure_parser.extract_content_by_toc(
        extracted_dir, structure, include_html)

    content_lookup: Dict[str, ExtractedSection] = {}
    for sections in toc_content.values():
        for section in sections:
            content_lookup[section.nav_point.id] = section

    nav_by_file: Dict[str, List[NavigationPoint]] = {}
    for nav_point in structure.navigation_tree:
        file_path = nav_point.href.split('#')[0]
        if file_path not in nav_by_file:
            nav_by_file[file_path] = []
        nav_by_file[file_path].append(nav_point)

    for chapter in chapters:
        top_level_navs = nav_by_file.get(chapter['href'], [])
        chapter['sections'] = [build_nested_section(
            nav, content_lookup) for nav in top_level_navs]


def calculate_section_stats(chapters: List[Dict]) -> tuple:
    """Calculate total sections and max depth."""
    def recurse(sections, depth=1):
        count = len(sections)
        max_d = depth if sections else 0
        for s in sections:
            sub_count, sub_depth = recurse(s.get('subsections', []), depth + 1)
            count += sub_count
            max_d = max(max_d, sub_depth)
        return count, max_d

    total, max_depth = 0, 0
    for ch in chapters:
        c, d = recurse(ch.get('sections', []))
        total += c
        max_depth = max(max_depth, d)
    return total, max_depth


def calculate_reading_time(total_words: int) -> Dict[str, int]:
    """Calculate reading time (250 words per minute)."""
    reading_time_minutes = total_words / 250
    return {
        'hours': int(reading_time_minutes // 60),
        'minutes': int(reading_time_minutes % 60)
    }
