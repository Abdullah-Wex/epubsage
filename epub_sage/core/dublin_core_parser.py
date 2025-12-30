"""
Dublin Core metadata parser for EPUB content.opf files.

Extracts Dublin Core metadata following the DCMES specification with support
for EPUB-specific extensions and namespace variations.
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from xml.etree import ElementTree as ET
from datetime import datetime

from ..models.dublin_core import (
    DublinCoreMetadata,
    DublinCoreCreator,
    DublinCoreDate,
    DublinCoreSubject,
    DublinCoreIdentifier,
    ParsedContentOpf
)
from ..utils.xml_utils import (
    get_namespaces_from_root,
    find_element_with_namespace,
    find_all_elements_with_namespace,
    parse_datetime,
    clean_text,
    get_element_text_and_attributes
)


logger = logging.getLogger(__name__)


class DublinCoreParser:
    """
    Parser for Dublin Core metadata in EPUB content.opf files.

    Supports EPUB 2.0 and 3.0 with proper namespace handling and
    follows SOLID principles for clean, maintainable code.
    """

    def __init__(self):
        self.namespaces = {}
        self.parsing_errors = []

    def parse_file(self, file_path: str) -> ParsedContentOpf:
        """
        Parse Dublin Core metadata from a content.opf file.

        Args:
            file_path: Path to the content.opf file

        Returns:
            ParsedContentOpf object containing metadata and manifest info

        Raises:
            FileNotFoundError: If file doesn't exist
            ET.ParseError: If XML parsing fails
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Content.opf file not found: {file_path}")

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return self.parse_xml(root, file_path)
        except ET.ParseError as e:
            # Try to parse as string with XML declaration added
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Add XML declaration if missing
                if not content.strip().startswith('<?xml'):
                    content = '<?xml version="1.0" encoding="utf-8"?>\n' + content

                root = ET.fromstring(content)
                return self.parse_xml(root, file_path)
            except Exception:
                logger.error(f"XML parsing error in {file_path}: {e}")
                raise

    def parse_xml(
            self,
            root: ET.Element,
            file_path: Optional[str] = None) -> ParsedContentOpf:
        """
        Parse Dublin Core metadata from XML root element.

        Args:
            root: Root XML element (package element)
            file_path: Optional file path for error reporting

        Returns:
            ParsedContentOpf object containing parsed data
        """
        self.parsing_errors = []
        self.namespaces = get_namespaces_from_root(root)

        # Extract metadata section
        metadata_element = find_element_with_namespace(
            root, "metadata", self.namespaces)
        if metadata_element is None:
            self.parsing_errors.append("No metadata element found")
            metadata_element = root  # Fallback to root

        # Parse Dublin Core metadata
        metadata = self._parse_dublin_core_metadata(metadata_element)

        # Add EPUB-specific metadata
        metadata.unique_identifier = root.get("unique-identifier")
        metadata.epub_version = root.get("version", "unknown")

        # Parse manifest, spine, and guide
        manifest_items = self._parse_manifest(root)
        spine_items = self._parse_spine(root)
        guide_items = self._parse_guide(root)

        return ParsedContentOpf(
            metadata=metadata,
            manifest_items=manifest_items,
            spine_items=spine_items,
            guide_items=guide_items,
            file_path=file_path,
            namespace_info=self.namespaces,
            parsing_errors=self.parsing_errors
        )

    def _parse_dublin_core_metadata(
            self, metadata_element: ET.Element) -> DublinCoreMetadata:
        """Parse Dublin Core metadata elements."""

        # Basic Dublin Core elements
        title = self._get_simple_element_text(metadata_element, "dc:title")
        publisher = self._get_simple_element_text(
            metadata_element, "dc:publisher")
        language = self._get_simple_element_text(
            metadata_element, "dc:language")
        description = self._get_simple_element_text(
            metadata_element, "dc:description")
        rights = self._get_simple_element_text(metadata_element, "dc:rights")

        # Complex elements with attributes
        creators = self._parse_creators(metadata_element)
        subjects = self._parse_subjects(metadata_element)
        dates = self._parse_dates(metadata_element)
        identifiers = self._parse_identifiers(metadata_element)

        # Additional elements
        source = self._get_simple_element_text(metadata_element, "dc:source")
        relation = self._get_simple_element_text(
            metadata_element, "dc:relation")
        coverage = self._get_simple_element_text(
            metadata_element, "dc:coverage")
        type_ = self._get_simple_element_text(metadata_element, "dc:type")
        contributor = self._get_simple_element_text(
            metadata_element, "dc:contributor")
        format_ = self._get_simple_element_text(metadata_element, "dc:format")

        # EPUB-specific metadata
        modified_date = self._parse_modified_date(metadata_element)

        # Collect raw metadata for debugging
        raw_metadata = self._collect_raw_metadata(metadata_element)

        return DublinCoreMetadata(
            title=title,
            creators=creators,
            publisher=publisher,
            language=language,
            description=description,
            subjects=subjects,
            dates=dates,
            identifiers=identifiers,
            rights=rights,
            source=source,
            relation=relation,
            coverage=coverage,
            type=type_,
            contributor=contributor,
            format=format_,
            modified_date=modified_date,
            raw_metadata=raw_metadata
        )

    def _get_simple_element_text(
            self,
            parent: ET.Element,
            tag: str) -> Optional[str]:
        """Get text content from a simple Dublin Core element."""
        element = find_element_with_namespace(parent, tag, self.namespaces)
        return clean_text(
            element.text) if element is not None and element.text else None

    def _parse_creators(
            self,
            metadata_element: ET.Element) -> List[DublinCoreCreator]:
        """Parse dc:creator elements with optional attributes."""
        creators = []
        elements = find_all_elements_with_namespace(
            metadata_element, "dc:creator", self.namespaces)

        for element in elements:
            data = get_element_text_and_attributes(element, self.namespaces)
            if data['text']:
                creator = DublinCoreCreator(
                    name=data['text'],
                    role=data['attributes'].get('role'),
                    file_as=data['attributes'].get('file-as')
                )
                creators.append(creator)

        return creators

    def _parse_subjects(
            self,
            metadata_element: ET.Element) -> List[DublinCoreSubject]:
        """Parse dc:subject elements."""
        subjects = []
        elements = find_all_elements_with_namespace(
            metadata_element, "dc:subject", self.namespaces)

        for element in elements:
            data = get_element_text_and_attributes(element, self.namespaces)
            if data['text']:
                subject = DublinCoreSubject(
                    value=data['text'],
                    scheme=data['attributes'].get('scheme')
                )
                subjects.append(subject)

        return subjects

    def _parse_dates(
            self,
            metadata_element: ET.Element) -> List[DublinCoreDate]:
        """Parse dc:date elements with optional event attributes."""
        dates = []
        elements = find_all_elements_with_namespace(
            metadata_element, "dc:date", self.namespaces)

        for element in elements:
            data = get_element_text_and_attributes(element, self.namespaces)
            if data['text']:
                parsed_date = parse_datetime(data['text'])
                date_obj = DublinCoreDate(
                    value=data['text'],
                    event=data['attributes'].get('event'),
                    parsed_date=parsed_date
                )
                dates.append(date_obj)

        return dates

    def _parse_identifiers(
            self,
            metadata_element: ET.Element) -> List[DublinCoreIdentifier]:
        """Parse dc:identifier elements."""
        identifiers = []
        elements = find_all_elements_with_namespace(
            metadata_element, "dc:identifier", self.namespaces)

        for element in elements:
            data = get_element_text_and_attributes(element, self.namespaces)
            if data['text']:
                # Detect scheme from content or attributes
                scheme = data['attributes'].get('scheme')
                if not scheme:
                    if 'isbn' in data['text'].lower():
                        scheme = 'isbn'
                    elif 'uuid' in data['text'].lower() or 'urn:uuid' in data['text'].lower():
                        scheme = 'uuid'

                identifier = DublinCoreIdentifier(
                    value=data['text'],
                    id=data['attributes'].get('id'),
                    scheme=scheme
                )
                identifiers.append(identifier)

        return identifiers

    def _parse_modified_date(
            self,
            metadata_element: ET.Element) -> Optional[datetime]:
        """Parse dcterms:modified date."""
        element = find_element_with_namespace(
            metadata_element, "dcterms:modified", self.namespaces)
        if element is not None and element.text:
            return parse_datetime(element.text)

        # Also check for meta elements with dcterms:modified property
        meta_elements = find_all_elements_with_namespace(
            metadata_element, "meta", self.namespaces)
        for meta in meta_elements:
            if meta.get("property") == "dcterms:modified" and meta.text:
                return parse_datetime(meta.text)

        return None

    def _collect_raw_metadata(
            self, metadata_element: ET.Element) -> Dict[str, Any]:
        """Collect all metadata elements for debugging and extension."""
        raw_metadata: Dict[str, Any] = {}

        for element in metadata_element:
            # Get tag name without namespace
            tag = element.tag.split(
                '}')[-1] if '}' in element.tag else element.tag

            # Store element data
            element_data = {
                'text': clean_text(element.text) if element.text else None,
                'attributes': dict(element.attrib),
                'namespace': element.tag.split('}')[0][1:] if '}' in element.tag else None
            }

            # Handle multiple elements with same tag
            if tag in raw_metadata:
                if not isinstance(raw_metadata[tag], list):
                    raw_metadata[tag] = [raw_metadata[tag]]
                raw_metadata[tag].append(element_data)
            else:
                raw_metadata[tag] = element_data

        return raw_metadata

    def _parse_manifest(self, root: ET.Element) -> List[Dict[str, str]]:
        """Parse manifest section."""
        manifest_items = []
        manifest = find_element_with_namespace(
            root, "manifest", self.namespaces)

        if manifest is not None:
            items = find_all_elements_with_namespace(
                manifest, "item", self.namespaces)
            for item in items:
                item_data = {
                    'id': item.get('id', ''),
                    'href': item.get('href', ''),
                    'media-type': item.get('media-type', ''),
                    'properties': item.get('properties', '')
                }
                manifest_items.append(item_data)

        return manifest_items

    def _parse_spine(self, root: ET.Element) -> List[str]:
        """Parse spine section."""
        spine_items = []
        spine = find_element_with_namespace(root, "spine", self.namespaces)

        if spine is not None:
            itemrefs = find_all_elements_with_namespace(
                spine, "itemref", self.namespaces)
            for itemref in itemrefs:
                idref = itemref.get('idref')
                if idref:
                    spine_items.append(idref)

        return spine_items

    def _parse_guide(self, root: ET.Element) -> List[Dict[str, str]]:
        """Parse guide section."""
        guide_items = []
        guide = find_element_with_namespace(root, "guide", self.namespaces)

        if guide is not None:
            references = find_all_elements_with_namespace(
                guide, "reference", self.namespaces)
            for ref in references:
                ref_data = {
                    'type': ref.get('type', ''),
                    'title': ref.get('title', ''),
                    'href': ref.get('href', '')
                }
                guide_items.append(ref_data)

        return guide_items
