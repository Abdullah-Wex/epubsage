"""Table of Contents parser for EPUB navigation structure."""

import logging
from pathlib import Path
from typing import List, Dict, Any
from xml.etree import ElementTree as ET

from ..models.structure import NavigationPoint
from .content_classifier import ContentClassifier
from .ncx_parser import parse_ncx
from .nav_parser import parse_nav

logger = logging.getLogger(__name__)


class TocParser:
    """Parser for EPUB Table of Contents files.

    Supports both EPUB 2.0 (toc.ncx) and EPUB 3.0 (nav documents).
    """

    def __init__(self):
        self.classifier = ContentClassifier()
        self.parsing_errors = []

    def parse_toc_file(self, file_path: str) -> List[NavigationPoint]:
        """Parse TOC file and return navigation structure.

        Auto-detects file type (NCX or nav document).
        """
        if not Path(file_path).exists():
            logger.warning(f"TOC file not found: {file_path}")
            return []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            if root.tag.endswith('}ncx') or root.tag == 'ncx':
                return parse_ncx(root, file_path, self.classifier)
            elif root.tag.endswith('}html') or 'nav' in str(root):
                return parse_nav(root, file_path, self.classifier)
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

    def flatten_navigation_tree(self, nav_points: List[NavigationPoint]) -> List[NavigationPoint]:
        """Flatten hierarchical navigation tree into a flat list."""
        flattened = []

        def _flatten_recursive(points: List[NavigationPoint]):
            for point in points:
                flattened.append(point)
                if point.children:
                    _flatten_recursive(point.children)

        _flatten_recursive(nav_points)
        return flattened

    def get_navigation_statistics(self, nav_points: List[NavigationPoint]) -> Dict[str, Any]:
        """Get statistics about navigation structure."""
        flattened = self.flatten_navigation_tree(nav_points)

        return {
            'total_entries': len(flattened),
            'max_depth': max([point.level for point in flattened], default=1),
            'chapters': len([p for p in flattened if p.nav_type == 'chapter']),
            'sections': len([p for p in flattened if p.nav_type == 'section']),
            'front_matter': len([p for p in flattened if p.nav_type == 'front_matter']),
            'back_matter': len([p for p in flattened if p.nav_type == 'back_matter']),
            'parts': len([p for p in flattened if p.nav_type == 'part']),
            'has_index': any(p.nav_type == 'index' for p in flattened),
        }
