"""
Utility functions for EPUB parsing.
"""
from .xml_utils import (
    EpubNamespaces,
    get_namespaces_from_root,
    find_element_with_namespace,
    find_all_elements_with_namespace,
    parse_datetime,
    clean_text,
    extract_opf_attributes,
    get_element_text_and_attributes
)

from .statistics import (
    EpubStatistics,
    calculate_reading_time,
    get_text_statistics
)

__all__ = [
    'EpubNamespaces',
    'get_namespaces_from_root',
    'find_element_with_namespace',
    'find_all_elements_with_namespace',
    'parse_datetime',
    'clean_text',
    'extract_opf_attributes',
    'get_element_text_and_attributes',
    'EpubStatistics',
    'calculate_reading_time',
    'get_text_statistics'
]
