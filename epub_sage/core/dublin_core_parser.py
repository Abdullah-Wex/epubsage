"""Dublin Core metadata parser for EPUB content.opf files."""

import logging
from pathlib import Path
from typing import Optional, List, Dict
from xml.etree import ElementTree as ET

from ..models.dublin_core import (
    DublinCoreMetadata,
    ParsedContentOpf
)
from ..utils.xml_utils import (
    get_namespaces_from_root,
    find_element_with_namespace,
    find_all_elements_with_namespace,
    clean_text,
)
from .metadata_element_parsers import (
    parse_creators,
    parse_subjects,
    parse_dates,
    parse_identifiers,
    parse_modified_date,
    collect_raw_metadata,
)


logger = logging.getLogger(__name__)


class DublinCoreParser:
    """Parser for Dublin Core metadata in EPUB content.opf files."""

    def __init__(self):
        self.namespaces = {}
        self.parsing_errors = []

    def parse_file(self, file_path: str) -> ParsedContentOpf:
        """Parse Dublin Core metadata from a content.opf file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Content.opf file not found: {file_path}")

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return self.parse_xml(root, file_path)
        except ET.ParseError as e:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

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
        """Parse Dublin Core metadata from XML root element."""
        self.parsing_errors = []
        self.namespaces = get_namespaces_from_root(root)

        metadata_element = find_element_with_namespace(
            root, "metadata", self.namespaces)
        if metadata_element is None:
            self.parsing_errors.append("No metadata element found")
            metadata_element = root

        metadata = self._parse_dublin_core_metadata(metadata_element)
        metadata.unique_identifier = root.get("unique-identifier")
        metadata.epub_version = root.get("version", "unknown")

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
        title = self._get_simple_element_text(metadata_element, "dc:title")
        publisher = self._get_simple_element_text(metadata_element, "dc:publisher")
        language = self._get_simple_element_text(metadata_element, "dc:language")
        description = self._get_simple_element_text(metadata_element, "dc:description")
        rights = self._get_simple_element_text(metadata_element, "dc:rights")
        source = self._get_simple_element_text(metadata_element, "dc:source")
        relation = self._get_simple_element_text(metadata_element, "dc:relation")
        coverage = self._get_simple_element_text(metadata_element, "dc:coverage")
        type_ = self._get_simple_element_text(metadata_element, "dc:type")
        contributor = self._get_simple_element_text(metadata_element, "dc:contributor")
        format_ = self._get_simple_element_text(metadata_element, "dc:format")

        creators = parse_creators(metadata_element, self.namespaces)
        subjects = parse_subjects(metadata_element, self.namespaces)
        dates = parse_dates(metadata_element, self.namespaces)
        identifiers = parse_identifiers(metadata_element, self.namespaces)
        modified_date = parse_modified_date(metadata_element, self.namespaces)
        raw_metadata = collect_raw_metadata(metadata_element)

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

    def _parse_manifest(self, root: ET.Element) -> List[Dict[str, str]]:
        """Parse manifest section."""
        manifest_items = []
        manifest = find_element_with_namespace(root, "manifest", self.namespaces)

        if manifest is not None:
            items = find_all_elements_with_namespace(manifest, "item", self.namespaces)
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
