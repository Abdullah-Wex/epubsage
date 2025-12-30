"""
Tests for part detection functionality.

Tests the enhanced part pattern detection against real book structures
found in the uploads directory.
"""
from epub_sage.core.content_classifier import ContentClassifier
from epub_sage.models.structure import ContentType


class TestPartDetection:
    """Test part detection with various naming patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = ContentClassifier()

    def test_standard_part_patterns(self):
        """Test standard part-N patterns."""
        # Test simple part patterns
        assert self.classifier.classify_content_item(
            "part-1", "Text/part-1.xhtml") == ContentType.PART
        assert self.classifier.classify_content_item(
            "part-2", "Text/part-2.xhtml") == ContentType.PART
        assert self.classifier.classify_content_item(
            "Part-3", "Text/Part-3.xhtml") == ContentType.PART

        # Test part number extraction
        assert self.classifier.extract_part_number(
            "part-1", "Text/part-1.xhtml") == 1
        assert self.classifier.extract_part_number(
            "part-2", "Text/part-2.xhtml") == 2
        assert self.classifier.extract_part_number(
            "Part-3", "Text/Part-3.xhtml") == 3

    def test_complex_oreilly_patterns(self):
        """Test O'Reilly style part-id patterns."""
        # Test complex O'Reilly patterns like part-id357
        assert self.classifier.classify_content_item(
            "part-id357", "part01.html") == ContentType.PART
        assert self.classifier.classify_content_item(
            "part-id361", "part02.html") == ContentType.PART
        assert self.classifier.classify_content_item(
            "part-id363", "part03.html") == ContentType.PART

        # Test part number extraction from complex IDs
        assert self.classifier.extract_part_number(
            "part-id357", "part01.html") == 357
        assert self.classifier.extract_part_number(
            "part-id361", "part02.html") == 361
        assert self.classifier.extract_part_number(
            "part-id363", "part03.html") == 363

    def test_filename_based_patterns(self):
        """Test part detection from filenames."""
        # Test when ID doesn't match but filename does
        assert self.classifier.classify_content_item(
            "chapter-id357", "part01.html") == ContentType.PART
        assert self.classifier.classify_content_item(
            "unknown-id", "part02.xhtml") == ContentType.PART
        assert self.classifier.classify_content_item(
            "random-id", "part03.html") == ContentType.PART

        # Test part number extraction from filenames
        assert self.classifier.extract_part_number(
            "chapter-id357", "part01.html") == 1
        assert self.classifier.extract_part_number(
            "unknown-id", "part02.xhtml") == 2
        assert self.classifier.extract_part_number(
            "random-id", "part03.html") == 3

    def test_simple_part_numbers(self):
        """Test simple part01, part02 patterns."""
        # Test simple part numbers
        assert self.classifier.classify_content_item(
            "part01", "Text/part01.xhtml") == ContentType.PART
        assert self.classifier.classify_content_item(
            "part02", "Text/part02.html") == ContentType.PART
        assert self.classifier.classify_content_item(
            "part1", "Text/part1.html") == ContentType.PART

        # Test part number extraction
        assert self.classifier.extract_part_number(
            "part01", "Text/part01.xhtml") == 1
        assert self.classifier.extract_part_number(
            "part02", "Text/part02.html") == 2
        assert self.classifier.extract_part_number(
            "part1", "Text/part1.html") == 1

    def test_mixed_id_and_filename_extraction(self):
        """Test extraction when both ID and filename contain part info."""
        # When both have part info, should extract from ID first (first match
        # wins)
        assert self.classifier.extract_part_number(
            "part-id357", "part01.html") == 357
        assert self.classifier.extract_part_number(
            "part-2", "part05.html") == 2

        # When only filename has part info
        assert self.classifier.extract_part_number(
            "random-id", "part04.html") == 4

        # When only ID has part info
        assert self.classifier.extract_part_number(
            "part-5", "random.html") == 5

    def test_non_part_items(self):
        """Test that non-part items are not classified as parts."""
        # Test chapters
        assert self.classifier.classify_content_item(
            "chapter-1", "Text/chapter-1.xhtml") == ContentType.CHAPTER
        assert self.classifier.extract_part_number(
            "chapter-1", "Text/chapter-1.xhtml") is None

        # Test front matter
        assert self.classifier.classify_content_item(
            "preface", "Text/preface.xhtml") == ContentType.FRONT_MATTER
        assert self.classifier.extract_part_number(
            "preface", "Text/preface.xhtml") is None

        # Test back matter
        assert self.classifier.classify_content_item(
            "appendix-a", "Text/appendix-a.xhtml") == ContentType.BACK_MATTER
        assert self.classifier.extract_part_number(
            "appendix-a", "Text/appendix-a.xhtml") is None

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty inputs
        assert self.classifier.extract_part_number("", "") is None
        assert self.classifier.extract_part_number("", "", "") is None

        # No part numbers
        assert self.classifier.extract_part_number(
            "random-text", "random.html") is None

        # Invalid patterns that should not match
        assert self.classifier.classify_content_item(
            "partner-1", "Text/partner.html") == ContentType.OTHER
        assert self.classifier.classify_content_item(
            "depart-1", "Text/depart.html") == ContentType.OTHER

        # Case insensitive matching
        assert self.classifier.classify_content_item(
            "PART-1", "Text/PART-1.XHTML") == ContentType.PART
        assert self.classifier.extract_part_number(
            "PART-2", "TEXT/PART-2.HTML") == 2


class TestPartDetectionIntegration:
    """Integration tests with real book data."""

    def test_hands_on_apis_part_pattern(self):
        """Test with real Hands-On APIs book patterns."""
        classifier = ContentClassifier()

        # Test the actual patterns from Hands-On APIs book
        test_cases = [
            ("part-id357", "part01.html"),
            ("part-id361", "part02.html"),
            ("part-id363", "part03.html"),
        ]

        for item_id, href in test_cases:
            assert classifier.classify_content_item(
                item_id, href) == ContentType.PART
            # Should extract part number from href since ID pattern is complex
            part_num = classifier.extract_part_number(item_id, href)
            assert part_num is not None
            assert part_num > 0

    def test_causal_ai_part_pattern(self):
        """Test with real Causal AI book patterns."""
        classifier = ContentClassifier()

        # Test the actual patterns from Causal AI book
        test_cases = [
            ("part-1", "Text/part-1.xhtml", 1),
            ("part-2", "Text/part-2.xhtml", 2),
            ("part-3", "Text/part-3.xhtml", 3),
            ("part-4", "Text/part-4.xhtml", 4),
        ]

        for item_id, href, expected_num in test_cases:
            assert classifier.classify_content_item(
                item_id, href) == ContentType.PART
            part_num = classifier.extract_part_number(item_id, href)
            assert part_num == expected_num

    def test_ai_powered_search_part_pattern(self):
        """Test with real AI-Powered Search book patterns."""
        classifier = ContentClassifier()

        # Test the actual patterns from AI-Powered Search book
        test_cases = [
            ("part-1", "Text/part-1.html", 1),
            ("part-2", "Text/part-2.html", 2),
            ("part-3", "Text/part-3.html", 3),
            ("part-4", "Text/part-4.html", 4),
        ]

        for item_id, href, expected_num in test_cases:
            assert classifier.classify_content_item(
                item_id, href) == ContentType.PART
            part_num = classifier.extract_part_number(item_id, href)
            assert part_num == expected_num
