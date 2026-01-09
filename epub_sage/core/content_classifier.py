"""Content classifier for EPUB structure analysis."""

import re
from typing import Optional, List
from pathlib import Path

from ..models.structure import ContentType
from .classification_patterns import (
    CHAPTER_PATTERNS,
    FRONT_MATTER_PATTERNS,
    BACK_MATTER_PATTERNS,
    PART_PATTERNS,
    IMAGE_PATTERNS,
)


class ContentClassifier:
    """Classifies EPUB content items based on ID, href, and filename patterns."""

    def __init__(self):
        self.chapter_patterns = CHAPTER_PATTERNS
        self.front_matter_patterns = FRONT_MATTER_PATTERNS
        self.back_matter_patterns = BACK_MATTER_PATTERNS
        self.part_patterns = PART_PATTERNS
        self.image_patterns = IMAGE_PATTERNS

    def classify_content_item(
            self, item_id: str, href: str, media_type: str = "") -> ContentType:
        """Classify a content item based on its ID, href, and media type."""
        if self._is_image_media_type(media_type):
            return ContentType.IMAGE

        if media_type == "text/css":
            return ContentType.STYLESHEET
        if "font" in media_type.lower():
            return ContentType.FONT

        filename = Path(href).stem.lower()

        if item_id.lower() == "index" or "index" in filename:
            return ContentType.INDEX

        if any(nav in item_id.lower() for nav in ["toc", "nav", "contents"]):
            return ContentType.NAVIGATION

        if item_id.lower() == "cover" or "cover" in filename:
            return ContentType.COVER

        if self._matches_patterns(item_id, self.part_patterns) or \
           self._matches_patterns(filename, self.part_patterns):
            return ContentType.PART

        if self._is_chapter(item_id, href):
            return ContentType.CHAPTER

        if self._matches_patterns(item_id, self.front_matter_patterns) or \
           self._matches_patterns(filename, self.front_matter_patterns):
            return ContentType.FRONT_MATTER

        if self._matches_patterns(item_id, self.back_matter_patterns) or \
           self._matches_patterns(filename, self.back_matter_patterns):
            return ContentType.BACK_MATTER

        return ContentType.OTHER

    def extract_chapter_number(
            self, item_id: str, href: str = "", title: str = "") -> Optional[int]:
        """Extract chapter number from various text sources."""
        sources = [item_id, Path(href).stem, title]
        result = self._extract_number_from_patterns(sources, self.chapter_patterns)
        if result is not None:
            return result

        if title:
            number_match = re.search(r'^(\d+)', title.strip())
            if number_match:
                try:
                    return int(number_match.group(1))
                except ValueError:
                    pass

        return None

    def extract_part_number(
            self, item_id: str, href: str = "", title: str = "") -> Optional[int]:
        """Extract part number from text sources."""
        sources = [item_id, Path(href).stem, Path(href).name, title]
        return self._extract_number_from_patterns(sources, self.part_patterns)

    def classify_image_type(self, filename: str, item_id: str = "") -> str:
        """Classify image based on filename patterns."""
        filename_lower = filename.lower()
        id_lower = item_id.lower()

        for img_type, patterns in self.image_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    return img_type

        if "cover" in id_lower:
            return "cover"

        return "figure"

    def extract_chapter_from_image_name(self, filename: str) -> Optional[int]:
        """Extract chapter number from image filename."""
        patterns = [
            (r'[A-Z]\d+_(\d+)_\d+\.', None),
            (r'chapter[-_](\d+)', re.IGNORECASE),
            (r'ch(\d+)', re.IGNORECASE),
            (r'cell-(\d+)-output', re.IGNORECASE),
        ]

        for pattern, flags in patterns:
            match = re.search(pattern, filename, flags) if flags else re.search(pattern, filename)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass

        return None

    def detect_section_numbering(self, title: str) -> Optional[str]:
        """Detect section numbering from title text."""
        match = re.search(r'^([A-Z]?\d+(?:\.\d+)*)', title.strip())
        if match:
            return match.group(1)
        return None

    def get_classification_confidence(
            self, item_id: str, href: str, media_type: str = "") -> float:
        """Get confidence score for classification (0.0 to 1.0)."""
        strong_patterns = {
            ContentType.CHAPTER: [r'^chapter[-_]\d+$', r'^Chapter[-_]\d+$'],
            ContentType.INDEX: [r'^index$'],
            ContentType.COVER: [r'^cover$'],
        }

        classification = self.classify_content_item(item_id, href, media_type)

        if classification in strong_patterns:
            for pattern in strong_patterns[classification]:
                if re.search(pattern, item_id, re.IGNORECASE):
                    return 0.9

        if classification != ContentType.OTHER:
            return 0.7

        return 0.3

    def _extract_number_from_patterns(
            self, sources: List[str], patterns: List[str]) -> Optional[int]:
        """Extract number from sources using given patterns."""
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
