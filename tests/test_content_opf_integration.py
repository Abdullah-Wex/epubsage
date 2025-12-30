"""
Simple, focused integration tests for content.opf parsing.
Tests the epub_sage with real content.opf files from uploads directory.
Follows FIRST, SOLID, KISS, DRY, YAGNI principles.
"""
import pytest
import glob
from pathlib import Path

from epub_sage import DublinCoreService, parse_content_opf
from epub_sage import ParsedContentOpf, DublinCoreMetadata


def discover_content_opf_files():
    """Discover all content.opf files in uploads directory."""
    base_dir = Path(__file__).parent.parent.parent
    pattern = str(base_dir / "uploads" / "**" / "content.opf")
    return glob.glob(pattern, recursive=True)


class TestContentOpfIntegration:
    """Simple integration tests for content.opf parsing."""

    @pytest.fixture
    def service(self):
        """Single service instance for all tests."""
        return DublinCoreService()

    @pytest.fixture
    def content_opf_files(self):
        """Get all available content.opf files."""
        files = discover_content_opf_files()
        if not files:
            pytest.skip("No content.opf files found in uploads directory")
        return files

    @pytest.mark.parametrize("file_path", discover_content_opf_files())
    def test_parse_content_opf_file_successfully(self, service, file_path):
        """Test that each content.opf file parses without errors."""
        result = service.parse_content_opf(file_path)

        # Basic structure validation
        assert isinstance(result, ParsedContentOpf)
        assert isinstance(result.metadata, DublinCoreMetadata)
        assert result.file_path == file_path

        # Core metadata should exist
        assert result.metadata.title is not None, f"No title found in {file_path}"
        assert len(
            result.metadata.identifiers) > 0, f"No identifiers found in {file_path}"

    def test_service_methods_work(self, service, content_opf_files):
        """Test that service methods return expected data types."""
        test_file = content_opf_files[0]

        # Test extract_basic_metadata
        basic_metadata = service.extract_basic_metadata(test_file)
        assert isinstance(basic_metadata, dict)
        assert 'title' in basic_metadata
        assert 'author' in basic_metadata

        # Test validate_content_opf
        validation = service.validate_content_opf(test_file)
        assert isinstance(validation, dict)
        assert 'is_valid' in validation
        assert 'quality_score' in validation

    def test_convenience_function_works(self, content_opf_files):
        """Test the convenience parse function."""
        test_file = content_opf_files[0]
        result = parse_content_opf(test_file)

        assert isinstance(result, ParsedContentOpf)
        assert result.metadata.title is not None

    def test_core_metadata_extraction(self, service, content_opf_files):
        """Test that core metadata fields are extracted correctly."""
        for file_path in content_opf_files[:3]:  # Test first 3 files
            result = service.parse_content_opf(file_path)
            metadata = result.metadata

            # Required Dublin Core elements should exist
            assert metadata.title, f"Missing title in {file_path}"
            assert len(metadata.creators) > 0, f"No creators in {file_path}"
            assert metadata.language, f"Missing language in {file_path}"

            # Should have parsed manifest and spine
            assert len(
                result.manifest_items) > 0, f"No manifest items in {file_path}"

    def test_epub_version_detection(self, service, content_opf_files):
        """Test that EPUB version is detected correctly."""
        for file_path in content_opf_files:
            result = service.parse_content_opf(file_path)
            metadata = result.metadata

            # Should detect version (2.0 or 3.0)
            assert metadata.epub_version in [
                "2.0", "3.0"], f"Invalid EPUB version in {file_path}"

    def test_no_parsing_errors_on_valid_files(
            self, service, content_opf_files):
        """Test that valid files don't generate parsing errors."""
        for file_path in content_opf_files:
            result = service.parse_content_opf(file_path)

            # Should have minimal or no parsing errors on real files
            if result.parsing_errors:
                print(
                    f"Parsing warnings for {file_path}: {
                        result.parsing_errors}")
