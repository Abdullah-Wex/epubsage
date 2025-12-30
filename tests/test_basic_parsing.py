"""
Basic unit tests for Dublin Core parser components.

Tests individual components in isolation before integration testing.
"""
from epub_sage import TocParser
from epub_sage import ContentType
from epub_sage import ContentClassifier
from epub_sage import DublinCoreParser
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestContentClassifier:
    """Test content classification logic."""

    @pytest.fixture
    def classifier(self):
        return ContentClassifier()

    def test_chapter_classification(self, classifier):
        """Test chapter pattern recognition."""
        test_cases = [
            ("chapter-1", "chapter-1.xhtml", ContentType.CHAPTER),
            ("Chapter-01", "Chapter-01.html", ContentType.CHAPTER),
            ("ch01", "ch01.xhtml", ContentType.CHAPTER),
            ("ch1", "ch1.html", ContentType.CHAPTER),
        ]

        for item_id, href, expected in test_cases:
            result = classifier.classify_content_item(item_id, href)
            assert result == expected, f"Failed for {item_id}: got {result}, expected {expected}"

    def test_chapter_number_extraction(self, classifier):
        """Test chapter number extraction."""
        test_cases = [
            ("chapter-1", 1),
            ("Chapter-01", 1),
            ("ch05", 5),
            ("chapter-idm123", None),  # O'Reilly style without number
        ]

        for item_id, expected in test_cases:
            result = classifier.extract_chapter_number(item_id)
            assert result == expected, f"Failed for {item_id}: got {result}, expected {expected}"

    def test_image_classification(self, classifier):
        """Test image type classification."""
        test_cases = [
            ("cover.png", "cover-image", "cover"),
            ("B31105_01_01.png", "fig1", "figure"),
            ("diagram-example.jpg", "diag1", "diagram"),
        ]

        for filename, item_id, expected in test_cases:
            result = classifier.classify_image_type(filename, item_id)
            assert result == expected, f"Failed for {filename}: got {result}, expected {expected}"

    def test_front_matter_classification(self, classifier):
        """Test front matter recognition."""
        test_cases = [
            ("titlepage", "titlepage.xhtml", ContentType.FRONT_MATTER),
            ("preface", "preface.html", ContentType.FRONT_MATTER),
            ("toc", "toc.xhtml", ContentType.NAVIGATION),
        ]

        for item_id, href, expected in test_cases:
            result = classifier.classify_content_item(item_id, href)
            assert result == expected, f"Failed for {item_id}: got {result}, expected {expected}"


class TestDublinCoreParser:
    """Test Dublin Core metadata parsing."""

    @pytest.fixture
    def parser(self):
        return DublinCoreParser()

    def test_parser_initialization(self, parser):
        """Test parser initialization."""
        assert parser is not None
        assert hasattr(parser, 'parse_file')
        assert hasattr(parser, 'parse_xml')

    def test_namespace_handling(self, parser):
        """Test namespace detection."""
        # Test basic namespace patterns
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="bookid">
            <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                <dc:title>Test Title</dc:title>
            </metadata>
        </package>'''

        from xml.etree import ElementTree as ET
        root = ET.fromstring(test_xml)

        # Should not raise exception
        result = parser.parse_xml(root)
        assert result is not None
        assert result.metadata.title == "Test Title"


class TestTocParser:
    """Test TOC parsing functionality."""

    @pytest.fixture
    def toc_parser(self):
        return TocParser()

    def test_parser_initialization(self, toc_parser):
        """Test TOC parser initialization."""
        assert toc_parser is not None
        assert hasattr(toc_parser, 'parse_toc_file')
        assert toc_parser.ncx_namespace == "http://www.daisy.org/z3986/2005/ncx/"

    def test_nav_entry_classification(self, toc_parser):
        """Test navigation entry classification."""
        test_cases = [
            ("Chapter 1: Introduction", "ch01.html", ("chapter", 1, None)),
            ("Appendix A", "appendix-a.html", ("back_matter", None, None)),
            ("Preface", "preface.html", ("front_matter", None, None)),
            ("Index", "index.html", ("index", None, None)),
        ]

        for label, href, expected in test_cases:
            result = toc_parser._classify_nav_entry(label, href)
            assert result == expected, f"Failed for {label}: got {result}, expected {expected}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
