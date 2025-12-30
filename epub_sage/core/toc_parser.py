"""
Table of Contents parser for EPUB navigation structure.

Parses toc.ncx (EPUB 2.0) and nav documents (EPUB 3.0) to extract
hierarchical navigation structure.
"""
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from xml.etree import ElementTree as ET

from ..models.structure import NavigationPoint
from .content_classifier import ContentClassifier


logger = logging.getLogger(__name__)


class TocParser:
    """
    Parser for EPUB Table of Contents files.

    Supports both EPUB 2.0 (toc.ncx) and EPUB 3.0 (nav documents).
    """

    def __init__(self):
        self.classifier = ContentClassifier()
        self.parsing_errors = []

        # NCX namespace
        self.ncx_namespace = "http://www.daisy.org/z3986/2005/ncx/"

        # EPUB 3.0 namespaces
        self.epub3_namespace = "http://www.idpf.org/2007/ops"
        self.xhtml_namespace = "http://www.w3.org/1999/xhtml"

    def parse_toc_file(self, file_path: str) -> List[NavigationPoint]:
        """
        Parse TOC file and return navigation structure.

        Auto-detects file type (NCX or nav document).

        Args:
            file_path: Path to TOC file

        Returns:
            List of NavigationPoint objects representing the TOC structure
        """
        if not Path(file_path).exists():
            logger.warning(f"TOC file not found: {file_path}")
            return []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Detect file type by root element
            if root.tag.endswith('}ncx') or root.tag == 'ncx':
                return self._parse_ncx_file(root, file_path)
            elif root.tag.endswith('}html') or 'nav' in str(root):
                return self._parse_nav_document(root, file_path)
            else:
                logger.warning(f"Unknown TOC file format: {file_path}")
                return []

        except ET.ParseError as e:
            logger.error(f"XML parsing error in TOC file {file_path}: {e}")
            self.parsing_errors.append(f"TOC parsing error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing TOC file {file_path}: {e}")
            self.parsing_errors.append(f"TOC error: {e}")
            return []

    def _parse_ncx_file(
            self,
            root: ET.Element,
            file_path: str) -> List[NavigationPoint]:
        """
        Parse NCX file (EPUB 2.0).

        Args:
            root: XML root element
            file_path: Original file path for error reporting

        Returns:
            List of NavigationPoint objects
        """
        namespaces = {'ncx': self.ncx_namespace}

        # Find navMap element
        nav_map = root.find('.//ncx:navMap', namespaces)
        if nav_map is None:
            # Try without namespace
            nav_map = root.find('.//navMap')

        if nav_map is None:
            logger.warning(f"No navMap found in NCX file: {file_path}")
            return []

        # Parse navigation points
        nav_points = self._parse_nav_points(nav_map, namespaces, level=1)

        return nav_points

    def _parse_nav_document(
            self,
            root: ET.Element,
            file_path: str) -> List[NavigationPoint]:
        """
        Parse EPUB 3.0 navigation document.

        Args:
            root: XML root element
            file_path: Original file path

        Returns:
            List of NavigationPoint objects
        """
        # Find nav element with epub:type="toc"
        nav_elements = root.findall(
            './/nav') + root.findall('.//{http://www.w3.org/1999/xhtml}nav')

        toc_nav = None
        for nav in nav_elements:
            epub_type = nav.get(
                '{http://www.idpf.org/2007/ops}type') or nav.get('epub:type')
            if epub_type == 'toc':
                toc_nav = nav
                break

        if toc_nav is None and nav_elements:
            # Use first nav element as fallback
            toc_nav = nav_elements[0]

        if toc_nav is None:
            logger.warning(f"No TOC nav element found in: {file_path}")
            return []

        # Find ol/ul list
        ol_element = toc_nav.find(
            './/ol') or toc_nav.find('.//{http://www.w3.org/1999/xhtml}ol')
        if ol_element is None:
            ol_element = toc_nav.find(
                './/ul') or toc_nav.find('.//{http://www.w3.org/1999/xhtml}ul')

        if ol_element is None:
            logger.warning(
                f"No list element found in nav document: {file_path}")
            return []

        # Parse list items
        nav_points = self._parse_nav_list(ol_element, level=1)

        return nav_points

    def _parse_nav_points(self,
                          parent: ET.Element,
                          namespaces: Dict[str,
                                           str],
                          level: int = 1,
                          parent_id: Optional[str] = None) -> List[NavigationPoint]:
        """
        Recursively parse navPoint elements from NCX.

        Args:
            parent: Parent XML element
            namespaces: XML namespaces
            level: Current hierarchy level
            parent_id: Parent navigation point ID

        Returns:
            List of NavigationPoint objects
        """
        nav_points = []

        # Find all direct navPoint children
        nav_point_elements = parent.findall('./ncx:navPoint', namespaces)
        if not nav_point_elements:
            # Try without namespace
            nav_point_elements = parent.findall('./navPoint')

        for nav_element in nav_point_elements:
            nav_point = self._create_nav_point_from_ncx(
                nav_element, namespaces, level, parent_id)
            if nav_point:
                # Parse children recursively
                children = self._parse_nav_points(
                    nav_element, namespaces, level + 1, nav_point.id)
                nav_point.children = children

                nav_points.append(nav_point)

        return nav_points

    def _parse_nav_list(self, ol_element: ET.Element, level: int = 1,
                        parent_id: Optional[str] = None) -> List[NavigationPoint]:
        """
        Parse navigation from EPUB 3.0 list structure.

        Args:
            ol_element: List element (ol/ul)
            level: Current hierarchy level
            parent_id: Parent navigation point ID

        Returns:
            List of NavigationPoint objects
        """
        nav_points = []
        play_order = 1

        # Find all direct li children
        li_elements = ol_element.findall(
            './li') + ol_element.findall('.//{http://www.w3.org/1999/xhtml}li')

        for li_element in li_elements:
            nav_point = self._create_nav_point_from_li(
                li_element, level, parent_id, play_order)
            if nav_point:
                # Look for nested list
                nested_list = li_element.find(
                    './/ol') or li_element.find('.//{http://www.w3.org/1999/xhtml}ol')
                if nested_list is None:
                    nested_list = li_element.find(
                        './/ul') or li_element.find('.//{http://www.w3.org/1999/xhtml}ul')

                if nested_list is not None:
                    children = self._parse_nav_list(
                        nested_list, level + 1, nav_point.id)
                    nav_point.children = children

                nav_points.append(nav_point)
                play_order += 1

        return nav_points

    def _create_nav_point_from_ncx(self,
                                   nav_element: ET.Element,
                                   namespaces: Dict[str,
                                                    str],
                                   level: int,
                                   parent_id: Optional[str] = None) -> Optional[NavigationPoint]:
        """Create NavigationPoint from NCX navPoint element."""
        # Get attributes
        nav_id = nav_element.get('id', '')
        play_order = int(nav_element.get('playOrder', '0'))

        # Get label text
        nav_label = nav_element.find('./ncx:navLabel/ncx:text', namespaces)
        if nav_label is None:
            nav_label = nav_element.find('./navLabel/text')

        if nav_label is None or not nav_label.text:
            logger.warning(f"No label found for navPoint: {nav_id}")
            return None

        label = nav_label.text.strip()

        # Get content src
        content = nav_element.find('./ncx:content', namespaces)
        if content is None:
            content = nav_element.find('./content')

        if content is None:
            logger.warning(f"No content found for navPoint: {nav_id}")
            return None

        href = content.get('src', '')

        # Classify navigation type and extract numbers
        nav_type, chapter_num, section_num = self._classify_nav_entry(
            label, href)

        return NavigationPoint(
            id=nav_id,
            label=label,
            href=href,
            play_order=play_order,
            level=level,
            parent_id=parent_id,
            nav_type=nav_type,
            chapter_number=chapter_num,
            section_number=section_num
        )

    def _create_nav_point_from_li(
            self,
            li_element: ET.Element,
            level: int,
            parent_id: Optional[str] = None,
            play_order: int = 1) -> Optional[NavigationPoint]:
        """Create NavigationPoint from EPUB 3.0 li element."""
        # Find anchor element
        a_element = li_element.find(
            './/a') or li_element.find('.//{http://www.w3.org/1999/xhtml}a')

        if a_element is None:
            logger.warning("No anchor found in nav li element")
            return None

        # Get href and label
        href = a_element.get('href', '')
        label = a_element.text or ''
        label = label.strip()

        if not label:
            logger.warning(f"Empty label for nav entry: {href}")
            return None

        # Generate ID if not present
        nav_id = f"nav-{play_order}"

        # Classify navigation type and extract numbers
        nav_type, chapter_num, section_num = self._classify_nav_entry(
            label, href)

        return NavigationPoint(
            id=nav_id,
            label=label,
            href=href,
            play_order=play_order,
            level=level,
            parent_id=parent_id,
            nav_type=nav_type,
            chapter_number=chapter_num,
            section_number=section_num
        )

    def _classify_nav_entry(self,
                            label: str,
                            href: str) -> tuple[str,
                                                Optional[int],
                                                Optional[str]]:
        """
        Classify navigation entry and extract chapter/section numbers.

        Args:
            label: Navigation label text
            href: Link href

        Returns:
            Tuple of (nav_type, chapter_number, section_number)
        """
        # Extract chapter number
        chapter_num = self.classifier.extract_chapter_number("", href, label)

        # Extract section numbering
        section_num = self.classifier.detect_section_numbering(label)

        # Classify navigation type
        label_lower = label.lower()
        href_lower = href.lower()

        if any(
            term in label_lower for term in [
                'appendix',
                'colophon',
                'bibliography']):
            nav_type = "back_matter"
        elif any(term in label_lower for term in ['preface', 'acknowledgment', 'about', 'title']):
            nav_type = "front_matter"
        elif 'index' in label_lower or 'index' in href_lower:
            nav_type = "index"
        elif 'part' in label_lower and chapter_num is None:
            nav_type = "part"
        elif chapter_num is not None:
            nav_type = "chapter"
        elif section_num is not None:
            nav_type = "section"
        else:
            nav_type = "other"

        return nav_type, chapter_num, section_num

    def flatten_navigation_tree(
            self,
            nav_points: List[NavigationPoint]) -> List[NavigationPoint]:
        """
        Flatten hierarchical navigation tree into a flat list.

        Args:
            nav_points: Hierarchical navigation points

        Returns:
            Flattened list preserving order and hierarchy information
        """
        flattened = []

        def _flatten_recursive(points: List[NavigationPoint]):
            for point in points:
                flattened.append(point)
                if point.children:
                    _flatten_recursive(point.children)

        _flatten_recursive(nav_points)
        return flattened

    def get_navigation_statistics(
            self, nav_points: List[NavigationPoint]) -> Dict[str, Any]:
        """
        Get statistics about navigation structure.

        Args:
            nav_points: Navigation points to analyze

        Returns:
            Dictionary with navigation statistics
        """
        flattened = self.flatten_navigation_tree(nav_points)

        stats = {
            'total_entries': len(flattened),
            'max_depth': max([point.level for point in flattened], default=1),
            'chapters': len([p for p in flattened if p.nav_type == 'chapter']),
            'sections': len([p for p in flattened if p.nav_type == 'section']),
            'front_matter': len([p for p in flattened if p.nav_type == 'front_matter']),
            'back_matter': len([p for p in flattened if p.nav_type == 'back_matter']),
            'parts': len([p for p in flattened if p.nav_type == 'part']),
            'has_index': any(p.nav_type == 'index' for p in flattened),
        }

        return stats
