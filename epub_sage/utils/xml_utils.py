"""
Utility functions for Dublin Core metadata parsing from EPUB content.opf files.
"""
import re
from datetime import datetime
from typing import Dict, Optional, Any
from xml.etree import ElementTree as ET


class EpubNamespaces:
    """Standard namespaces used in EPUB content.opf files."""

    # Dublin Core namespaces
    DC_ELEMENTS_1_1 = "http://purl.org/dc/elements/1.1/"
    DC_TERMS = "http://purl.org/dc/terms/"

    # EPUB/OPF namespaces
    OPF_2_0 = "http://www.idpf.org/2007/opf"
    OPF_1_0 = "http://openebook.org/namespaces/oeb-package/1.0/"

    # Common namespace prefixes
    PREFIXES = {
        "dc": DC_ELEMENTS_1_1,
        "dcterms": DC_TERMS,
        "opf": OPF_2_0,
        "": OPF_2_0  # Default namespace
    }


def get_namespaces_from_root(root_element: ET.Element) -> Dict[str, str]:
    """
    Extract namespace mappings from the root element.

    Args:
        root_element: Root XML element

    Returns:
        Dictionary mapping namespace prefixes to URIs
    """
    namespaces = {}

    # Get namespaces from element tag and attributes
    for key, value in root_element.attrib.items():
        if key.startswith('xmlns'):
            prefix = key.split(':', 1)[1] if ':' in key else ''
            namespaces[prefix] = value

    # Add default namespaces if not present
    if 'dc' not in namespaces:
        namespaces['dc'] = EpubNamespaces.DC_ELEMENTS_1_1
    if 'dcterms' not in namespaces:
        namespaces['dcterms'] = EpubNamespaces.DC_TERMS
    if 'opf' not in namespaces:
        namespaces['opf'] = EpubNamespaces.OPF_2_0

    # Handle default namespace for OPF elements
    if '' not in namespaces and 'xmlns' in root_element.attrib:
        namespaces[''] = root_element.attrib['xmlns']

    return namespaces


def find_element_with_namespace(
        parent: ET.Element, tag: str, namespaces: Dict[str, str]) -> Optional[ET.Element]:
    """
    Find element by tag name, handling namespace variations.

    Args:
        parent: Parent element to search in
        tag: Tag name (e.g., 'dc:title', 'title', 'metadata')
        namespaces: Namespace mapping

    Returns:
        Found element or None
    """
    # Try with namespace prefix
    if ':' in tag:
        prefix, local_name = tag.split(':', 1)
        if prefix in namespaces:
            full_tag = f"{{{namespaces[prefix]}}}{local_name}"
            element = parent.find(full_tag)
            if element is not None:
                return element
    else:
        # For unprefixed tags, try with default namespace first
        local_name = tag
        if '' in namespaces:
            full_tag = f"{{{namespaces['']}}}{local_name}"
            element = parent.find(full_tag)
            if element is not None:
                return element

    # Try without namespace
    element = parent.find(tag)
    if element is not None:
        return element

    # Try with common namespaces
    local_name = tag.split(':', 1)[-1]  # Get local name
    for namespace_uri in [
            EpubNamespaces.OPF_2_0,
            EpubNamespaces.DC_ELEMENTS_1_1,
            EpubNamespaces.DC_TERMS]:
        full_tag = f"{{{namespace_uri}}}{local_name}"
        element = parent.find(full_tag)
        if element is not None:
            return element

    return None


def find_all_elements_with_namespace(
        parent: ET.Element, tag: str, namespaces: Dict[str, str]) -> list:
    """
    Find all elements by tag name, handling namespace variations.

    Args:
        parent: Parent element to search in
        tag: Tag name (e.g., 'dc:creator', 'creator')
        namespaces: Namespace mapping

    Returns:
        List of found elements
    """
    elements = []

    # Try with namespace prefix
    if ':' in tag:
        prefix, local_name = tag.split(':', 1)
        if prefix in namespaces:
            full_tag = f"{{{namespaces[prefix]}}}{local_name}"
            elements.extend(parent.findall(full_tag))
    else:
        # For unprefixed tags, try with default namespace first
        local_name = tag
        if '' in namespaces:
            full_tag = f"{{{namespaces['']}}}{local_name}"
            elements.extend(parent.findall(full_tag))

    # Try without namespace
    elements.extend(parent.findall(tag))

    # Try with common namespaces
    local_name = tag.split(':', 1)[-1]  # Get local name
    for namespace_uri in [
            EpubNamespaces.OPF_2_0,
            EpubNamespaces.DC_ELEMENTS_1_1,
            EpubNamespaces.DC_TERMS]:
        full_tag = f"{{{namespace_uri}}}{local_name}"
        elements.extend(parent.findall(full_tag))

    # Remove duplicates while preserving order
    seen = set()
    unique_elements = []
    for elem in elements:
        elem_id = id(elem)
        if elem_id not in seen:
            seen.add(elem_id)
            unique_elements.append(elem)

    return unique_elements


def parse_datetime(date_string: str) -> Optional[datetime]:
    """
    Parse various datetime formats commonly found in EPUB metadata.

    Args:
        date_string: Date string to parse

    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not date_string:
        return None

    # Common date formats in EPUB files
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",      # ISO 8601 with Z
        "%Y-%m-%dT%H:%M:%S",       # ISO 8601 without timezone
        "%Y-%m-%d",                # Date only
        "%Y-%m",                   # Year-month
        "%Y",                      # Year only
        "%Y-%m-%dT%H:%M:%S.%fZ",   # ISO 8601 with microseconds
    ]

    # Clean the date string
    date_string = date_string.strip()

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    # Try to extract year from string if other formats fail
    year_match = re.search(r'\b(\d{4})\b', date_string)
    if year_match:
        try:
            return datetime(int(year_match.group(1)), 1, 1)
        except ValueError:
            pass

    return None


def clean_text(text: str) -> str:
    """
    Clean and normalize text content from XML.

    Args:
        text: Raw text content

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = ' '.join(text.split())

    # Remove HTML entities and special characters
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")

    return text.strip()


def extract_opf_attributes(
        element: ET.Element, namespaces: Dict[str, str]) -> Dict[str, str]:
    """
    Extract OPF-specific attributes from an element.

    Args:
        element: XML element
        namespaces: Namespace mapping

    Returns:
        Dictionary of OPF attributes
    """
    attributes = {}
    opf_namespace = namespaces.get('opf', EpubNamespaces.OPF_2_0)

    for key, value in element.attrib.items():
        # Handle namespaced attributes
        if key.startswith('{'):
            # Already fully qualified
            if opf_namespace in key:
                local_name = key.split('}', 1)[-1]
                attributes[local_name] = value
        elif key.startswith('opf:'):
            # Remove prefix
            local_name = key.split(':', 1)[-1]
            attributes[local_name] = value
        elif key in ['role', 'file-as', 'event', 'scheme', 'id']:
            # Common OPF attributes
            attributes[key] = value

    return attributes


def get_element_text_and_attributes(
        element: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Any]:
    """
    Get both text content and attributes from an element.

    Args:
        element: XML element
        namespaces: Namespace mapping

    Returns:
        Dictionary with 'text' and 'attributes' keys
    """
    return {
        'text': clean_text(element.text or ''),
        'attributes': extract_opf_attributes(element, namespaces)
    }
