"""HTML parsing utilities for content extraction."""

import os
from typing import List, Optional

from bs4 import BeautifulSoup, Tag


def is_generic_header(element: Optional[Tag]) -> bool:
    """Identifies if an element is a header using tags, classes, and roles."""
    if not element or not hasattr(element, 'name') or not element.name:
        return False

    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        return True

    if element.get('role') == 'heading':
        return True

    keywords = [
        'title', 'heading', 'chapter-head', 'ch-title', 'section-title',
        'chapter-label', 'ch-label', 'title-prefix', 'chapter-number',
        'label', 'title-text'
    ]

    class_attr = element.get('class')
    cls = " ".join(class_attr) if isinstance(
        class_attr, list) else (class_attr or "")
    id_val = element.get('id', '') or ""
    id_str = id_val if isinstance(id_val, str) else ""
    combined = (cls + " " + id_str).lower()

    if any(kw in combined for kw in keywords):
        text = element.get_text(strip=True)
        if 0 < len(text) < 200:
            return True

    return False


def parse_html_file(html_file_path: str) -> Optional[BeautifulSoup]:
    """Parse HTML file with fallback parsers."""
    if not os.path.exists(html_file_path):
        return None

    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            try:
                return BeautifulSoup(file, 'lxml-xml')
            except Exception:
                file.seek(0)
                return BeautifulSoup(file, 'html.parser')
    except Exception:
        return None


def clean_body_content(body: Tag) -> None:
    """Remove boilerplate elements from body."""
    for junk_tag in ['nav', 'aside', 'script', 'style', 'footer', 'header']:
        for junk in body.find_all(junk_tag):
            if not is_generic_header(junk) and not any(
                is_generic_header(c if isinstance(c, Tag) else None)
                for c in junk.descendants if getattr(c, 'name', None)
            ):
                junk.decompose()


def find_content_container(body: Tag) -> Tag:
    """Navigate to content level using child count logic."""
    current_container = body

    while True:
        children: List[Tag] = [
            child for child in current_container.children
            if isinstance(child, Tag) and child.name
        ]

        if len(children) == 1:
            current_container = children[0]
        else:
            header_tags = [
                child for child in children if is_generic_header(child)]
            if header_tags:
                break
            elif children and all(child.name in ['div', 'section', 'article'] for child in children):
                break
            else:
                break

    return current_container


def get_content_children(container: Tag) -> List[Tag]:
    """Get content children from container."""
    all_direct_children: List[Tag] = [
        child for child in container.children
        if isinstance(child, Tag) and child.name
    ]

    direct_headers = [
        child for child in all_direct_children if is_generic_header(child)]

    if direct_headers:
        return all_direct_children

    content_children = []
    for child in all_direct_children:
        if child.name in ['div', 'section', 'article']:
            child_elements = [
                subchild for subchild in child.children
                if isinstance(subchild, Tag) and subchild.name
            ]
            if child_elements:
                content_children.extend(child_elements)
            elif child.get_text().strip():
                content_children.append(child)
        else:
            content_children.append(child)

    return content_children
