"""Utility functions for Dublin Core metadata parsing from EPUB content.opf files."""

import re
from datetime import datetime
from typing import Dict, Optional, Any
from xml.etree import ElementTree as ET

from .xml_namespaces import EpubNamespaces, get_namespaces_from_root

# Re-export for backwards compatibility
__all__ = [
    'EpubNamespaces', 'get_namespaces_from_root',
    'find_element_with_namespace', 'find_all_elements_with_namespace',
    'parse_datetime', 'clean_text', 'extract_opf_attributes',
    'get_element_text_and_attributes',
]


def find_element_with_namespace(
    parent: ET.Element, tag: str, namespaces: Dict[str, str]
) -> Optional[ET.Element]:
    """Find element by tag name, handling namespace variations."""
    if ':' in tag:
        prefix, local_name = tag.split(':', 1)
        if prefix in namespaces:
            full_tag = f"{{{namespaces[prefix]}}}{local_name}"
            element = parent.find(full_tag)
            if element is not None:
                return element
    else:
        local_name = tag
        if '' in namespaces:
            full_tag = f"{{{namespaces['']}}}{local_name}"
            element = parent.find(full_tag)
            if element is not None:
                return element

    element = parent.find(tag)
    if element is not None:
        return element

    local_name = tag.split(':', 1)[-1]
    for namespace_uri in [EpubNamespaces.OPF_2_0, EpubNamespaces.DC_ELEMENTS_1_1, EpubNamespaces.DC_TERMS]:
        full_tag = f"{{{namespace_uri}}}{local_name}"
        element = parent.find(full_tag)
        if element is not None:
            return element

    return None


def find_all_elements_with_namespace(
    parent: ET.Element, tag: str, namespaces: Dict[str, str]
) -> list:
    """Find all elements by tag name, handling namespace variations."""
    elements = []

    if ':' in tag:
        prefix, local_name = tag.split(':', 1)
        if prefix in namespaces:
            full_tag = f"{{{namespaces[prefix]}}}{local_name}"
            elements.extend(parent.findall(full_tag))
    else:
        local_name = tag
        if '' in namespaces:
            full_tag = f"{{{namespaces['']}}}{local_name}"
            elements.extend(parent.findall(full_tag))

    elements.extend(parent.findall(tag))

    local_name = tag.split(':', 1)[-1]
    for namespace_uri in [EpubNamespaces.OPF_2_0, EpubNamespaces.DC_ELEMENTS_1_1, EpubNamespaces.DC_TERMS]:
        full_tag = f"{{{namespace_uri}}}{local_name}"
        elements.extend(parent.findall(full_tag))

    seen = set()
    unique_elements = []
    for elem in elements:
        elem_id = id(elem)
        if elem_id not in seen:
            seen.add(elem_id)
            unique_elements.append(elem)

    return unique_elements


def parse_datetime(date_string: str) -> Optional[datetime]:
    """Parse various datetime formats commonly found in EPUB metadata."""
    if not date_string:
        return None

    formats = [
        "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d",
        "%Y-%m", "%Y", "%Y-%m-%dT%H:%M:%S.%fZ",
    ]

    date_string = date_string.strip()

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    year_match = re.search(r'\b(\d{4})\b', date_string)
    if year_match:
        try:
            return datetime(int(year_match.group(1)), 1, 1)
        except ValueError:
            pass

    return None


def clean_text(text: str) -> str:
    """Clean and normalize text content from XML."""
    if not text:
        return ""

    text = ' '.join(text.split())
    text = text.replace('&amp;', '&').replace('&lt;', '<')
    text = text.replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    return text.strip()


def extract_opf_attributes(element: ET.Element, namespaces: Dict[str, str]) -> Dict[str, str]:
    """Extract OPF-specific attributes from an element."""
    attributes = {}
    opf_namespace = namespaces.get('opf', EpubNamespaces.OPF_2_0)

    for key, value in element.attrib.items():
        if key.startswith('{'):
            if opf_namespace in key:
                local_name = key.split('}', 1)[-1]
                attributes[local_name] = value
        elif key.startswith('opf:'):
            local_name = key.split(':', 1)[-1]
            attributes[local_name] = value
        elif key in ['role', 'file-as', 'event', 'scheme', 'id']:
            attributes[key] = value

    return attributes


def get_element_text_and_attributes(element: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Any]:
    """Get both text content and attributes from an element."""
    return {
        'text': clean_text(element.text or ''),
        'attributes': extract_opf_attributes(element, namespaces)
    }
