"""Parsers for individual Dublin Core metadata elements."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from xml.etree import ElementTree as ET

from ..models.dublin_core import (
    DublinCoreCreator,
    DublinCoreDate,
    DublinCoreSubject,
    DublinCoreIdentifier,
)
from ..utils.xml_utils import (
    find_all_elements_with_namespace,
    parse_datetime,
    clean_text,
    get_element_text_and_attributes,
    find_element_with_namespace,
)


def parse_creators(
    metadata_element: ET.Element, namespaces: Dict[str, str]
) -> List[DublinCoreCreator]:
    """Parse dc:creator elements with optional attributes."""
    creators = []
    elements = find_all_elements_with_namespace(
        metadata_element, "dc:creator", namespaces
    )

    for element in elements:
        data = get_element_text_and_attributes(element, namespaces)
        if data["text"]:
            creator = DublinCoreCreator(
                name=data["text"],
                role=data["attributes"].get("role"),
                file_as=data["attributes"].get("file-as"),
            )
            creators.append(creator)

    return creators


def parse_subjects(
    metadata_element: ET.Element, namespaces: Dict[str, str]
) -> List[DublinCoreSubject]:
    """Parse dc:subject elements."""
    subjects = []
    elements = find_all_elements_with_namespace(
        metadata_element, "dc:subject", namespaces
    )

    for element in elements:
        data = get_element_text_and_attributes(element, namespaces)
        if data["text"]:
            subject = DublinCoreSubject(
                value=data["text"], scheme=data["attributes"].get("scheme")
            )
            subjects.append(subject)

    return subjects


def parse_dates(
    metadata_element: ET.Element, namespaces: Dict[str, str]
) -> List[DublinCoreDate]:
    """Parse dc:date elements with optional event attributes."""
    dates = []
    elements = find_all_elements_with_namespace(
        metadata_element, "dc:date", namespaces
    )

    for element in elements:
        data = get_element_text_and_attributes(element, namespaces)
        if data["text"]:
            parsed_date = parse_datetime(data["text"])
            date_obj = DublinCoreDate(
                value=data["text"],
                event=data["attributes"].get("event"),
                parsed_date=parsed_date,
            )
            dates.append(date_obj)

    return dates


def parse_identifiers(
    metadata_element: ET.Element, namespaces: Dict[str, str]
) -> List[DublinCoreIdentifier]:
    """Parse dc:identifier elements."""
    identifiers = []
    elements = find_all_elements_with_namespace(
        metadata_element, "dc:identifier", namespaces
    )

    for element in elements:
        data = get_element_text_and_attributes(element, namespaces)
        if data["text"]:
            scheme = data["attributes"].get("scheme")
            if not scheme:
                if "isbn" in data["text"].lower():
                    scheme = "isbn"
                elif "uuid" in data["text"].lower() or "urn:uuid" in data["text"].lower():
                    scheme = "uuid"

            identifier = DublinCoreIdentifier(
                value=data["text"],
                id=data["attributes"].get("id"),
                scheme=scheme,
            )
            identifiers.append(identifier)

    return identifiers


def parse_modified_date(
    metadata_element: ET.Element, namespaces: Dict[str, str]
) -> Optional[datetime]:
    """Parse dcterms:modified date."""
    element = find_element_with_namespace(
        metadata_element, "dcterms:modified", namespaces
    )
    if element is not None and element.text:
        return parse_datetime(element.text)

    meta_elements = find_all_elements_with_namespace(
        metadata_element, "meta", namespaces
    )
    for meta in meta_elements:
        if meta.get("property") == "dcterms:modified" and meta.text:
            return parse_datetime(meta.text)

    return None


def collect_raw_metadata(metadata_element: ET.Element) -> Dict[str, Any]:
    """Collect all metadata elements for debugging and extension."""
    raw_metadata: Dict[str, Any] = {}

    for element in metadata_element:
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

        element_data = {
            "text": clean_text(element.text) if element.text else None,
            "attributes": dict(element.attrib),
            "namespace": element.tag.split("}")[0][1:] if "}" in element.tag else None,
        }

        if tag in raw_metadata:
            if not isinstance(raw_metadata[tag], list):
                raw_metadata[tag] = [raw_metadata[tag]]
            raw_metadata[tag].append(element_data)
        else:
            raw_metadata[tag] = element_data

    return raw_metadata
