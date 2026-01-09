"""EPUB namespace definitions and extraction."""

from typing import Dict
from xml.etree import ElementTree as ET


class EpubNamespaces:
    """Standard namespaces used in EPUB content.opf files."""

    DC_ELEMENTS_1_1 = "http://purl.org/dc/elements/1.1/"
    DC_TERMS = "http://purl.org/dc/terms/"
    OPF_2_0 = "http://www.idpf.org/2007/opf"
    OPF_1_0 = "http://openebook.org/namespaces/oeb-package/1.0/"

    PREFIXES = {
        "dc": DC_ELEMENTS_1_1,
        "dcterms": DC_TERMS,
        "opf": OPF_2_0,
        "": OPF_2_0
    }


def get_namespaces_from_root(root_element: ET.Element) -> Dict[str, str]:
    """Extract namespace mappings from the root element."""
    namespaces = {}

    for key, value in root_element.attrib.items():
        if key.startswith('xmlns'):
            prefix = key.split(':', 1)[1] if ':' in key else ''
            namespaces[prefix] = value

    if 'dc' not in namespaces:
        namespaces['dc'] = EpubNamespaces.DC_ELEMENTS_1_1
    if 'dcterms' not in namespaces:
        namespaces['dcterms'] = EpubNamespaces.DC_TERMS
    if 'opf' not in namespaces:
        namespaces['opf'] = EpubNamespaces.OPF_2_0

    if '' not in namespaces and 'xmlns' in root_element.attrib:
        namespaces[''] = root_element.attrib['xmlns']

    return namespaces
