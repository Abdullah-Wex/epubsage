"""Element content extractor - main dispatch function."""

from typing import Dict, Any, List, Optional

from bs4 import Tag

from .specialized_extractors import (
    normalize_text,
    extract_table, extract_definition_list, extract_list,
    extract_admonition, extract_sidebar, extract_epigraph, extract_figure,
    collect_keywords, collect_references,
)

# Container elements that wrap section content
CONTAINER_TAGS = {'div', 'section', 'article', 'aside', 'main', 'nav'}

# Admonition types
ADMONITION_TYPES = {'note', 'tip', 'warning'}

# HTML tag to semantic type mapping
TYPE_MAP = {
    'h1': 'heading', 'h2': 'heading', 'h3': 'heading',
    'h4': 'heading', 'h5': 'heading', 'h6': 'heading',
    'p': 'paragraph', 'pre': 'code', 'code': 'code',
    'ul': 'list', 'ol': 'list', 'li': 'list_item',
    'blockquote': 'quote', 'img': 'image', 'figure': 'image',
    'table': 'table', 'dl': 'definition_list',
    'dt': 'definition_term', 'dd': 'definition',
}

# Re-export for backwards compatibility
__all__ = [
    'normalize_text', 'extract_element', 'is_content_container',
    'collect_keywords', 'collect_references', 'CONTAINER_TAGS',
    'ADMONITION_TYPES', 'TYPE_MAP',
]


def is_content_container(element: Tag) -> bool:
    """Check if element is a container that holds content children."""
    return element.name in CONTAINER_TAGS


def extract_element(element: Tag, include_html: bool = False) -> Optional[Dict[str, Any]]:
    """Extract content from a single element."""
    if element.name == 'table':
        result = extract_table(element)
        if include_html:
            result['html'] = str(element)
        return result

    if element.name == 'dl':
        dl_result = extract_definition_list(element)
        element_class = element.get('class', '')
        if isinstance(element_class, list):
            element_class = ' '.join(element_class)
        if element_class and 'calloutlist' in element_class:
            dl_result['type'] = 'callout_list'
        if include_html:
            dl_result['html'] = str(element)
        return dl_result

    if element.name in ('ul', 'ol'):
        result = extract_list(element)
        if include_html:
            result['html'] = str(element)
        return result

    if element.get('data-type') == 'indexterm':
        return None

    data_type = element.get('data-type', '')
    if data_type in ADMONITION_TYPES:
        result = extract_admonition(element)
        if include_html:
            result['html'] = str(element)
        return result

    if data_type == 'sidebar' or element.name == 'aside':
        result = extract_sidebar(element)
        if include_html:
            result['html'] = str(element)
        return result

    if data_type == 'epigraph':
        result = extract_epigraph(element)
        if include_html:
            result['html'] = str(element)
        return result

    if data_type == 'equation':
        result = {'type': 'equation', 'text': normalize_text(
            element.get_text(separator=' '))}
        if include_html:
            result['html'] = str(element)
        return result

    if element.name == 'figure':
        result = extract_figure(element)
        if include_html:
            result['html'] = str(element)
        return result

    block_type = TYPE_MAP.get(element.name, 'paragraph')
    block_result: Dict[str, Any] = {
        'type': block_type,
        'text': normalize_text(element.get_text(separator=' ')),
    }

    if element.name == 'pre':
        lang = element.get('data-code-language')
        if lang:
            block_result['language'] = lang

    if include_html:
        block_result['html'] = str(element)

    if block_type == 'image':
        img = element if element.name == 'img' else element.find('img')
        if img:
            if img.get('src'):
                block_result['src'] = img.get('src')
            if img.get('alt'):
                block_result['alt'] = img.get('alt')
        svg_img = element.find('image')
        if svg_img:
            href = svg_img.get('href') or svg_img.get('xlink:href')
            if href:
                block_result['src'] = href
    else:
        images: List[str] = []
        for img in element.find_all('img'):
            src = img.get('src')
            if src and isinstance(src, str):
                images.append(src)
        for svg_img in element.find_all('image'):
            href = svg_img.get('href') or svg_img.get('xlink:href')
            if href and isinstance(href, str):
                images.append(href)
        if images:
            block_result['images'] = images

    return block_result
