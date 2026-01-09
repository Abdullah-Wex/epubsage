"""Specialized extractors for complex HTML elements."""

import re
from typing import Dict, Any, List

from bs4 import Tag

# Unicode whitespace normalization pattern
_WHITESPACE_RE = re.compile(r'[\u00a0\u2000-\u200b\u202f\u205f\u3000\ufeff]+')


def normalize_text(text: str) -> str:
    """Normalize Unicode whitespace to regular spaces and collapse."""
    return ' '.join(_WHITESPACE_RE.sub(' ', text).split())


def extract_table(element: Tag) -> Dict[str, Any]:
    """Extract table with caption, headers and rows."""
    result: Dict[str, Any] = {'type': 'table'}

    caption = element.find('caption')
    if caption:
        result['caption'] = normalize_text(
            caption.get_text(separator=' ', strip=True))

    result['headers'] = [normalize_text(th.get_text(separator=' ', strip=True))
                         for th in element.find_all('th')]

    rows = []
    for tr in element.find_all('tr'):
        cells = [normalize_text(td.get_text(separator=' ', strip=True))
                 for td in tr.find_all('td')]
        if cells:
            rows.append(cells)
    result['rows'] = rows
    result['text'] = normalize_text(element.get_text(separator=' '))
    return result


def extract_definition_list(element: Tag) -> Dict[str, Any]:
    """Extract definition list with term-definition pairs."""
    items = []
    current_term = None

    for child in element.children:
        if not isinstance(child, Tag):
            continue
        if child.name == 'dt':
            current_term = normalize_text(
                child.get_text(separator=' ', strip=True))
        elif child.name == 'dd' and current_term:
            items.append({
                'term': current_term,
                'definition': normalize_text(child.get_text(separator=' ', strip=True))
            })

    return {
        'type': 'definition_list',
        'items': items,
        'text': normalize_text(element.get_text(separator=' '))
    }


def extract_list(element: Tag) -> Dict[str, Any]:
    """Extract list with structured items supporting nested lists."""
    list_type = 'ordered' if element.name == 'ol' else 'unordered'

    def extract_item(li: Tag) -> Any:
        nested = li.find(['ul', 'ol'], recursive=False)
        if nested:
            text_parts = []
            for child in li.children:
                if isinstance(child, Tag):
                    if child.name in ('ul', 'ol'):
                        break
                    text_parts.append(child.get_text(
                        separator=' ', strip=True))
                elif isinstance(child, str) and child.strip():
                    text_parts.append(child.strip())

            item_text = normalize_text(' '.join(text_parts))
            nested_content = extract_list(nested)
            return {
                'text': item_text,
                'items': nested_content['items'],
                'list_type': nested_content['list_type']
            }
        else:
            return normalize_text(li.get_text(separator=' ', strip=True))

    items = [extract_item(li)
             for li in element.find_all('li', recursive=False)]
    return {
        'type': 'list',
        'list_type': list_type,
        'items': items,
        'text': normalize_text(element.get_text(separator=' '))
    }


def extract_admonition(element: Tag) -> Dict[str, Any]:
    """Extract admonition (note/tip/warning) with type and text."""
    admonition_type = element.get('data-type', 'note')

    text_parts = []
    for child in element.descendants:
        if isinstance(child, Tag) and child.name == 'h6':
            continue
        if isinstance(child, str) and child.strip():
            text_parts.append(child.strip())

    return {
        'type': 'admonition',
        'admonition_type': admonition_type,
        'text': normalize_text(' '.join(text_parts))
    }


def extract_sidebar(element: Tag) -> Dict[str, Any]:
    """Extract sidebar with title and text."""
    title = ''
    heading = element.find(['h1', 'h2', 'h3'])
    if heading:
        title = normalize_text(heading.get_text(separator=' ', strip=True))

    return {
        'type': 'sidebar',
        'title': title,
        'text': normalize_text(element.get_text(separator=' '))
    }


def extract_epigraph(element: Tag) -> Dict[str, Any]:
    """Extract epigraph (quote) with attribution."""
    quote_parts = []
    attribution = ''

    for child in element.children:
        if not isinstance(child, Tag):
            continue
        if child.get('data-type') == 'attribution':
            attribution = normalize_text(
                child.get_text(separator=' ', strip=True))
        elif child.name == 'p':
            quote_parts.append(child.get_text(separator=' ', strip=True))

    return {
        'type': 'epigraph',
        'text': normalize_text(' '.join(quote_parts)),
        'attribution': attribution
    }


def extract_figure(element: Tag) -> Dict[str, Any]:
    """Extract figure with image src, alt, and caption."""
    result: Dict[str, Any] = {'type': 'figure'}

    img = element.find('img')
    if img:
        src = img.get('src')
        if src:
            result['src'] = src if isinstance(src, str) else src[0]
        alt = img.get('alt')
        if alt:
            alt_str = alt if isinstance(alt, str) else ' '.join(alt)
            result['alt'] = normalize_text(alt_str)

    caption_elem = element.find('h6')
    if caption_elem:
        result['caption'] = normalize_text(
            caption_elem.get_text(separator=' ', strip=True))

    result['text'] = normalize_text(element.get_text(separator=' '))
    return result


def collect_keywords(elements: List[Tag]) -> List[Dict[str, str]]:
    """Collect keywords from indexterm elements."""
    keywords: List[Dict[str, str]] = []
    for elem in elements:
        if elem.get('data-type') != 'indexterm':
            continue
        keyword: Dict[str, str] = {}
        for key in ['data-primary', 'data-secondary', 'data-tertiary', 'data-seealso']:
            val = elem.get(key)
            if val:
                val_str = val if isinstance(val, str) else ' '.join(val)
                keyword[key.replace('data-', '')] = val_str
        if keyword:
            keywords.append(keyword)
    return keywords


def collect_references(elements: List[Tag]) -> List[Dict[str, str]]:
    """Collect cross-references from xref elements."""
    references: List[Dict[str, str]] = []
    for elem in elements:
        if elem.get('data-type') != 'xref':
            continue
        href_val = elem.get('href', '')
        href = href_val if isinstance(href_val, str) else href_val[0] if href_val else ''
        text = normalize_text(elem.get_text(separator=' ', strip=True))
        if href and text:
            references.append({'text': text, 'href': href})
    return references
