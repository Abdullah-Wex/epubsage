"""Content Extractor for EPUB HTML files.

Provides intelligent content extraction that automatically detects
wrapper levels and groups content by headers.
"""

import os
from typing import List, Dict, Any

from bs4 import Tag

from .image_resolver import (
    discover_epub_images, resolve_and_validate_images, IMAGE_EXTENSIONS,
)
from .html_parser import (
    is_generic_header, parse_html_file, clean_body_content,
    find_content_container, get_content_children,
)

# Re-export for backwards compatibility
__all__ = [
    'discover_epub_images', 'resolve_and_validate_images', 'IMAGE_EXTENSIONS',
    'is_generic_header', 'extract_content_sections', 'extract_book_content',
]


def _extract_images_from_element(element: Tag) -> List[str]:
    """Extract all image sources from an element."""
    images: List[str] = []

    for img in element.find_all('img'):
        src = img.get('src')
        if src and isinstance(src, str):
            images.append(src)

    for svg_img in element.find_all('image'):
        href = svg_img.get('href') or svg_img.get('xlink:href')
        if href and isinstance(href, str):
            images.append(href)

    if element.name == 'img':
        src = element.get('src')
        if src and isinstance(src, str) and src not in images:
            images.append(src)
    elif element.name == 'image':
        href = element.get('href') or element.get('xlink:href')
        if href and isinstance(href, str) and href not in images:
            images.append(href)

    return images


def _is_boilerplate(element: Tag) -> bool:
    """Check if element is boilerplate (link-heavy)."""
    text = element.get_text(strip=True)
    if len(text) > 40:
        links_text = "".join([a.get_text(strip=True)
                             for a in element.find_all('a')])
        if (len(links_text) / len(text)) > 0.70:
            return True
    return False


def extract_content_sections(html_file_path: str) -> List[Dict[str, Any]]:
    """Extract content sections grouped by headers from HTML file."""
    soup = parse_html_file(html_file_path)
    if not soup:
        return []

    body = soup.find('body')
    if not body:
        return []

    clean_body_content(body)
    content_container = find_content_container(body)
    content_children = get_content_children(
        content_container) if content_container else []

    sections: List[Dict[str, Any]] = []
    current_header = None
    current_content: List[Dict[str, Any]] = []
    current_images: List[str] = []

    for child in content_children:
        child_images = _extract_images_from_element(child)
        generic_header = is_generic_header(child)

        if not generic_header:
            if _is_boilerplate(child):
                continue
            text = child.get_text(strip=True)
            if not text and not child_images:
                continue

        if generic_header:
            if current_header or current_content:
                sections.append({
                    'header': current_header or 'Intro',
                    'content': current_content,
                    'images': current_images
                })

            current_header = child.get_text().strip()
            current_content = [{
                'tag': child.name,
                'text': current_header,
                'html': str(child),
                'images': child_images,
                'is_header': True
            }]
            current_images = child_images
        else:
            current_content.append({
                'tag': child.name,
                'text': child.get_text().strip(),
                'html': str(child),
                'images': child_images
            })
            current_images.extend(child_images)

    if current_header or current_content:
        sections.append({
            'header': current_header or 'Intro',
            'content': current_content,
            'images': current_images
        })

    return sections


def extract_book_content(epub_directory_path: str) -> Dict[str, Any]:
    """Extract content from all HTML files in an EPUB directory."""
    content_data = {}
    valid_images = discover_epub_images(epub_directory_path)

    for root, dirs, files in os.walk(epub_directory_path):
        if any(skip in root for skip in ['META-INF', '__MACOSX', '.git']):
            continue

        for file in files:
            if file.endswith(('.html', '.xhtml', '.htm')):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, epub_directory_path)
                relative_path = relative_path.replace('\\', '/')

                sections = extract_content_sections(file_path)
                if sections:
                    html_rel_dir = os.path.dirname(relative_path)

                    for section in sections:
                        section['images'] = resolve_and_validate_images(
                            section.get(
                                'images', []), html_rel_dir, valid_images
                        )
                        for block in section.get('content', []):
                            block['images'] = resolve_and_validate_images(
                                block.get(
                                    'images', []), html_rel_dir, valid_images
                            )

                    content_data[relative_path] = sections

    return content_data
