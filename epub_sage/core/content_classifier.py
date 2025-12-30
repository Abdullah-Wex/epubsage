"""
Content classifier for EPUB structure analysis.

Uses pattern-based classification derived from real content.opf files.
Follows KISS principle with simple, effective classification rules.
"""
import re
from typing import Optional, List
from pathlib import Path

from ..models.structure import ContentType


class ContentClassifier:
    """
    Classifies EPUB content items based on ID, href, and filename patterns.

    Classification rules derived from analysis of uploaded sample files.
    """

    def __init__(self):
        # Chapter patterns from real data
        self.chapter_patterns = [
            r'^chapter[-_](\d+)$',           # chapter-1, chapter_1
            r'^Chapter[-_](\d+)$',           # Chapter-1, Chapter_1
            r'^ch(\d+)$',                    # ch01, ch1
            r'^ch(\d+)\.x?html$',            # ch01.xhtml, ch1.html
            r'chapter-idm\d+',               # O'Reilly style
            r'(\d+)\s+[A-Z][a-z]',           # "1 Understanding..."
        ]

        # Front matter patterns
        self.front_matter_patterns = [
            r'^(title|titlepage)[-_]?',
            r'^(preface|acknowledgments?|about)',
            r'^(copyright|dedication)',
            r'^(contents?|toc)',
            r'^(foreword|introduction)',
            r'^cover$',
        ]

        # Back matter patterns
        self.back_matter_patterns = [
            r'^appendix[-_]?[a-zA-Z]?',
            r'^(colophon|bibliography)',
            r'^(other[-_]book|about[-_]author)',
            r'^(references|further[-_]reading)',
        ]

        # Part/section patterns
        self.part_patterns = [
            r'^part[-_](\d+)$',              # part-1, part_1
            r'^Part[-_](\d+)$',              # Part-1, Part_1
            r'Part\s+(\d+)\s+',              # "Part 1 "
            # part-id357 (O'Reilly style) - extracts the final number sequence
            r'^part.*id.*?(\d+)$',
            r'^part(\d+)\.x?html?$',         # part01.html, part1.xhtml
            r'^part(\d+)$',                  # part01, part1
        ]

        # Image type patterns
        self.image_patterns = {
            'cover': [r'cover\.(png|jpg|jpeg)', r'.*cover.*\.(png|jpg|jpeg)'],
            'figure': [r'B\d+_\d+_\d+\.(png|jpg)', r'figure.*\.(png|jpg)'],
            'diagram': [r'.*diagram.*\.(png|jpg)', r'.*drawio.*\.(png|jpg)'],
            'chart': [r'.*chart.*\.(png|jpg)', r'.*graph.*\.(png|jpg)'],
            'cell_output': [r'cell-\d+-output-\d+\.(png|jpg)'],
            'model_figure': [r'.*model.*\.(png|jpg)', r'.*unet.*\.(png|jpg)'],
        }

    def classify_content_item(
            self,
            item_id: str,
            href: str,
            media_type: str = "") -> ContentType:
        """
        Classify a content item based on its ID, href, and media type.

        Args:
            item_id: Item ID from manifest
            href: File path/href
            media_type: MIME type

        Returns:
            ContentType classification
        """
        # Handle images first
        if self._is_image_media_type(media_type):
            return ContentType.IMAGE

        # Handle stylesheets and fonts
        if media_type == "text/css":
            return ContentType.STYLESHEET
        if "font" in media_type.lower():
            return ContentType.FONT

        # Extract filename for pattern matching
        filename = Path(href).stem.lower()

        # Check for index
        if item_id.lower() == "index" or "index" in filename:
            return ContentType.INDEX

        # Check for navigation
        if any(nav in item_id.lower() for nav in ["toc", "nav", "contents"]):
            return ContentType.NAVIGATION

        # Check for cover
        if item_id.lower() == "cover" or "cover" in filename:
            return ContentType.COVER

        # Check for parts
        if self._matches_patterns(item_id, self.part_patterns) or \
           self._matches_patterns(filename, self.part_patterns):
            return ContentType.PART

        # Check for chapters
        if self._is_chapter(item_id, href):
            return ContentType.CHAPTER

        # Check for front matter
        if self._matches_patterns(item_id, self.front_matter_patterns) or \
           self._matches_patterns(filename, self.front_matter_patterns):
            return ContentType.FRONT_MATTER

        # Check for back matter
        if self._matches_patterns(item_id, self.back_matter_patterns) or \
           self._matches_patterns(filename, self.back_matter_patterns):
            return ContentType.BACK_MATTER

        # Default classification
        return ContentType.OTHER

    def _extract_number_from_patterns(
            self,
            sources: List[str],
            patterns: List[str]) -> Optional[int]:
        """
        Extract number from sources using given patterns.

        Args:
            sources: List of text sources to search
            patterns: List of regex patterns to try

        Returns:
            Extracted number or None
        """
        for source in sources:
            if not source:
                continue

            for pattern in patterns:
                match = re.search(pattern, source, re.IGNORECASE)
                if match:
                    try:
                        return int(match.group(1))
                    except (IndexError, ValueError):
                        continue
        return None

    def extract_chapter_number(
            self,
            item_id: str,
            href: str = "",
            title: str = "") -> Optional[int]:
        """
        Extract chapter number from various text sources.

        Args:
            item_id: Item ID from manifest
            href: File path
            title: Chapter title if available

        Returns:
            Chapter number or None
        """
        sources = [item_id, Path(href).stem, title]

        # Try standard chapter patterns first
        result = self._extract_number_from_patterns(
            sources, self.chapter_patterns)
        if result is not None:
            return result

        # Try extracting number from title as fallback
        if title:
            number_match = re.search(r'^(\d+)', title.strip())
            if number_match:
                try:
                    return int(number_match.group(1))
                except ValueError:
                    pass

        return None

    def extract_part_number(
            self,
            item_id: str,
            href: str = "",
            title: str = "") -> Optional[int]:
        """Extract part number from text sources."""
        sources = [item_id, Path(href).stem, Path(href).name, title]
        return self._extract_number_from_patterns(sources, self.part_patterns)

    def classify_image_type(self, filename: str, item_id: str = "") -> str:
        """
        Classify image based on filename patterns.

        Args:
            filename: Image filename
            item_id: Item ID from manifest

        Returns:
            Image type classification
        """
        filename_lower = filename.lower()
        id_lower = item_id.lower()

        # Check each image type pattern
        for img_type, patterns in self.image_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    return img_type

        # Check for cover in ID
        if "cover" in id_lower:
            return "cover"

        # Default classification
        return "figure"

    def extract_chapter_from_image_name(self, filename: str) -> Optional[int]:
        """
        Extract chapter number from image filename.

        Based on patterns like B31105_01_01.png (chapter 1)
        """
        # Pattern: BookCode_Chapter_Image.ext
        match = re.search(r'[A-Z]\d+_(\d+)_\d+\.', filename)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

        # Pattern: chapter-N-something
        match = re.search(r'chapter[-_](\d+)', filename, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

        # Pattern: chN-something
        match = re.search(r'ch(\d+)', filename, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

        # Pattern: cell-N-output (O'Reilly notebook outputs)
        match = re.search(r'cell-(\d+)-output', filename, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

        return None

    def detect_section_numbering(self, title: str) -> Optional[str]:
        """
        Detect section numbering from title text.

        Examples: "1.2.3 Section Title", "A.9.2 Subsection"
        """
        # Pattern: Number.Number.Number
        match = re.search(r'^([A-Z]?\d+(?:\.\d+)*)', title.strip())
        if match:
            return match.group(1)

        return None

    def _is_chapter(self, item_id: str, href: str) -> bool:
        """Check if item represents a chapter."""
        return (self._matches_patterns(item_id, self.chapter_patterns) or
                self._matches_patterns(Path(href).stem, self.chapter_patterns))

    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given patterns."""
        if not text:
            return False

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _is_image_media_type(self, media_type: str) -> bool:
        """Check if media type represents an image."""
        return media_type.startswith("image/") if media_type else False

    def get_classification_confidence(
            self,
            item_id: str,
            href: str,
            media_type: str = "") -> float:
        """
        Get confidence score for classification (0.0 to 1.0).

        Higher scores indicate more certain classification.
        """
        # Strong indicators (high confidence)
        strong_patterns = {
            ContentType.CHAPTER: [r'^chapter[-_]\d+$', r'^Chapter[-_]\d+$'],
            ContentType.INDEX: [r'^index$'],
            ContentType.COVER: [r'^cover$'],
        }

        classification = self.classify_content_item(item_id, href, media_type)

        # Check for strong patterns
        if classification in strong_patterns:
            for pattern in strong_patterns[classification]:
                if re.search(pattern, item_id, re.IGNORECASE):
                    return 0.9

        # Medium confidence for partial matches
        if classification != ContentType.OTHER:
            return 0.7

        # Low confidence for unknown classification
        return 0.3
