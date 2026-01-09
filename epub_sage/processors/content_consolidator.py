"""Content consolidation logic for chapter building."""

import os
from typing import Dict, List, Any, Optional

from .helpers import get_chapter_id, get_best_title, format_part_roman


def consolidate_sections(sections: List[Dict]) -> tuple:
    """Consolidate sections into content, images, and title."""
    consolidated_content = []
    consolidated_images = []

    title_parts = []
    for section in sections:
        header = section.get('header')
        if header and header not in title_parts:
            title_parts.append(header)
        if len(section.get('content', [])) > 1:
            break

    main_title = ": ".join(title_parts) if title_parts else None

    for section in sections:
        consolidated_content.extend(section.get('content', []))
        consolidated_images.extend(section.get('images', []))

    return consolidated_content, consolidated_images, main_title


def build_chapter_dict(
    href: str,
    content: List[Dict],
    struct_item: Optional[Any],
    main_title: Optional[str],
    chapter_index: int,
    fallback_type: str = 'chapter'
) -> Dict[str, Any]:
    """Build a chapter dictionary from content."""
    struct_title = struct_item.title if struct_item else None
    best_title = get_best_title(
        struct_title, main_title, f'Section {chapter_index + 1}')

    chapter_text = ' '.join([item['text'] for item in content])
    word_count = len(chapter_text.split())
    char_count = sum(len(item['text']) for item in content)
    reading_minutes = max(1, word_count // 250)

    return {
        'id': get_chapter_id(href),
        'title': best_title,
        'href': href,
        'type': struct_item.content_type.value if struct_item else fallback_type,
        'chapter_number': struct_item.chapter_number if struct_item else None,
        'part': format_part_roman(struct_item.part_number) if struct_item else None,
        'word_count': word_count,
        'char_count': char_count,
        'reading_minutes': reading_minutes,
        'image_count': 0,
        'linear': struct_item.linear if struct_item else True,
        '_temp_content': content,
    }


def process_spine_items(parsed_opf, all_content: Dict, structure_map: Dict, extracted_dir: str) -> tuple:
    """Process content in spine order."""
    chapters = []
    total_words = 0
    processed_hrefs = set()
    chapter_index = 0

    manifest_map = {item['id']: item['href']
                    for item in parsed_opf.manifest_items}

    for idref in parsed_opf.spine_items:
        raw_href = manifest_map.get(idref)
        if not raw_href:
            continue

        href = parsed_opf.resolve_href(raw_href, extracted_dir)
        if href not in all_content or href in processed_hrefs:
            continue

        sections = all_content[href]
        content, images, main_title = consolidate_sections(sections)

        chapter_text = ' '.join([item['text'] for item in content])
        word_count = len(chapter_text.split())
        total_words += word_count

        struct_item = structure_map.get(href)
        chapter_dict = build_chapter_dict(
            href, content, struct_item, main_title, chapter_index)
        chapter_dict['image_count'] = len(images)

        chapters.append(chapter_dict)
        chapter_index += 1
        processed_hrefs.add(href)

    return chapters, total_words, processed_hrefs, chapter_index


def process_non_spine_items(all_content: Dict, processed_hrefs: set, structure_map: Dict,
                            chapter_index: int) -> tuple:
    """Process content not in spine."""
    chapters = []
    total_words = 0

    for href, sections in all_content.items():
        if href in processed_hrefs:
            continue

        content, images, main_title = consolidate_sections(sections)

        chapter_text = ' '.join([item['text'] for item in content])
        word_count = len(chapter_text.split())
        total_words += word_count

        struct_item = structure_map.get(href)
        fallback_title = f'Extra: {os.path.basename(href)}'
        struct_title = struct_item.title if struct_item else None
        best_title = get_best_title(struct_title, main_title, fallback_title)

        chapter_dict = build_chapter_dict(
            href, content, struct_item, main_title, chapter_index, 'other')
        chapter_dict['title'] = best_title
        chapter_dict['image_count'] = len(images)
        chapter_dict['linear'] = struct_item.linear if struct_item else False

        chapters.append(chapter_dict)
        chapter_index += 1
        processed_hrefs.add(href)

    return chapters, total_words, chapter_index


def process_fallback_content(all_content: Dict) -> tuple:
    """Process content when no OPF is available."""
    chapters = []
    total_words = 0
    chapter_index = 0

    for href, sections in all_content.items():
        content, images, main_title = consolidate_sections(sections)

        chapter_text = ' '.join([item['text'] for item in content])
        word_count = len(chapter_text.split())
        total_words += word_count

        char_count = sum(len(item['text']) for item in content)
        reading_minutes = max(1, word_count // 250)

        chapters.append({
            'id': get_chapter_id(href),
            'title': main_title or f'Section {chapter_index + 1}',
            'href': href,
            'type': 'chapter',
            'chapter_number': chapter_index + 1,
            'part': None,
            'word_count': word_count,
            'char_count': char_count,
            'reading_minutes': reading_minutes,
            'image_count': len(images),
            'linear': True,
            '_temp_content': content,
        })
        chapter_index += 1

    return chapters, total_words


def finalize_chapters(chapters: List[Dict]) -> None:
    """Finalize chapter format - move _temp_content to content or remove."""
    for chapter in chapters:
        temp_content = chapter.pop('_temp_content', None)
        sections = chapter.get('sections', [])

        if not sections or all(not s.get('content') for s in sections):
            chapter['content'] = temp_content or []
