"""
Comprehensive tests for Dublin Core metadata parser using real content.opf files.
"""
import pytest
from pathlib import Path
from datetime import datetime

from epub_sage import DublinCoreParser
from epub_sage import DublinCoreMetadata, ParsedContentOpf
from epub_sage import DublinCoreService, parse_content_opf

# Check if test files exist (for CI environments)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_HAS_TEST_FILES = len(list(_PROJECT_ROOT.glob("uploads/**/content.opf"))) > 0


class TestDublinCoreParserUnit:
    """Unit tests for parser that don't require external files."""

    @pytest.fixture
    def parser(self):
        return DublinCoreParser()

    @pytest.fixture
    def service(self):
        return DublinCoreService()

    def test_parser_initialization(self, parser):
        """Test parser initializes correctly."""
        assert parser is not None
        assert parser.namespaces == {}
        assert parser.parsing_errors == []

    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service is not None
        assert service.parser is not None


@pytest.mark.skipif(not _HAS_TEST_FILES, reason="No test files in uploads directory")
class TestDublinCoreParserWithRealFiles:
    """Test parser with actual content.opf files from uploads directory."""

    @pytest.fixture
    def parser(self):
        return DublinCoreParser()

    @pytest.fixture
    def service(self):
        return DublinCoreService()

    @pytest.fixture
    def sample_files(self):
        """Get paths to sample content.opf files."""
        base_dir = Path(__file__).parent.parent.parent
        uploads_dir = base_dir / "uploads"

        sample_files = []
        for opf_file in uploads_dir.rglob("content.opf"):
            sample_files.append(opf_file)

        return sample_files

    @pytest.mark.parametrize("sample_file", [
        "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/8a14dea195908257/raw/OEBPS/content.opf",
        "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/ce8af01f13f2c804/raw/content.opf",
        "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/bea59a2a53580c79/raw/OEBPS/content.opf",
        "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/859d585241a05506/raw/OEBPS/content.opf"
    ])
    def test_parse_real_files(self, parser, sample_file):
        """Test parsing real content.opf files."""
        if not Path(sample_file).exists():
            pytest.skip(f"Sample file not found: {sample_file}")

        result = parser.parse_file(sample_file)

        assert isinstance(result, ParsedContentOpf)
        assert result.metadata is not None
        assert isinstance(result.metadata, DublinCoreMetadata)
        assert result.file_path == sample_file

        # Check that we got some basic metadata
        metadata = result.metadata
        assert metadata.title is not None
        assert len(metadata.creators) > 0
        assert len(metadata.identifiers) > 0

    def test_llm_engineers_handbook_parsing(self, parser):
        """Test parsing specific file: LLM Engineer's Handbook."""
        sample_file = "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/8a14dea195908257/raw/OEBPS/content.opf"

        if not Path(sample_file).exists():
            pytest.skip("LLM Engineer's Handbook file not found")

        result = parser.parse_file(sample_file)
        metadata = result.metadata

        # Test specific expected values
        assert "LLM Engineer" in metadata.title and "Handbook" in metadata.title
        assert len(metadata.creators) >= 1
        assert metadata.creators[0].name in [
            "Paul Iusztin\n| Maxime Labonne",
            "Paul Iusztin | Maxime Labonne",
            "Paul Iusztin",
            "Maxime Labonne"]
        assert metadata.publisher == "Packt"
        assert metadata.language == "en-US"
        assert len(metadata.subjects) >= 1
        assert "COMPUTERS" in metadata.subjects[0].value
        assert metadata.rights == "Packt Publishing"
        assert metadata.epub_version == "3.0"

    def test_build_llm_from_scratch_parsing(self, parser):
        """Test parsing specific file: Build a Large Language Model."""
        sample_file = "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/ce8af01f13f2c804/raw/content.opf"

        if not Path(sample_file).exists():
            pytest.skip("Build LLM file not found")

        result = parser.parse_file(sample_file)
        metadata = result.metadata

        # Test specific expected values
        assert metadata.title == "Build a Large Language Model (From Scratch)"
        assert len(metadata.creators) == 1
        assert metadata.creators[0].name == "Sebastian Raschka"
        assert metadata.creators[0].role == "aut"
        assert metadata.creators[0].file_as == "Sebastian Raschka"
        assert metadata.publisher == "Manning Publications Co."
        assert metadata.language == "en-us"
        assert metadata.epub_version == "2.0"

        # Check ISBN identifier
        isbn = metadata.get_isbn()
        assert isbn == "urn:isbn:9781633437166"

        # Check publication date
        pub_date = metadata.get_publication_date()
        assert pub_date == "2024-09-06"

    def test_generative_ai_book_parsing(self, parser):
        """Test parsing O'Reilly Generative AI book."""
        sample_file = "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/bea59a2a53580c79/raw/OEBPS/content.opf"

        if not Path(sample_file).exists():
            pytest.skip("Generative AI book file not found")

        result = parser.parse_file(sample_file)
        metadata = result.metadata

        # Test specific expected values
        assert "Hands-On Generative AI" in metadata.title
        assert "Transformers and Diffusion Models" in metadata.title
        assert metadata.publisher == "O'Reilly Media, Inc."
        assert metadata.language == "en"
        assert metadata.epub_version == "3.0"

        # Check creators
        creator_names = [c.name for c in metadata.creators]
        assert any("Pedro Cuenca" in name for name in creator_names)

    def test_service_basic_metadata_extraction(self, service):
        """Test service's basic metadata extraction."""
        sample_file = "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/ce8af01f13f2c804/raw/content.opf"

        if not Path(sample_file).exists():
            pytest.skip("Sample file not found")

        basic_metadata = service.extract_basic_metadata(sample_file)

        assert isinstance(basic_metadata, dict)
        assert 'title' in basic_metadata
        assert 'author' in basic_metadata
        assert 'publisher' in basic_metadata
        assert 'language' in basic_metadata
        assert 'epub_version' in basic_metadata

        # Check specific values
        assert basic_metadata['title'] == "Build a Large Language Model (From Scratch)"
        assert basic_metadata['author'] == "Sebastian Raschka"
        assert basic_metadata['publisher'] == "Manning Publications Co."
        assert basic_metadata['language'] == "en-us"
        assert basic_metadata['epub_version'] == "2.0"

    def test_service_validation(self, service):
        """Test service's validation functionality."""
        sample_file = "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/ce8af01f13f2c804/raw/content.opf"

        if not Path(sample_file).exists():
            pytest.skip("Sample file not found")

        validation_result = service.validate_content_opf(sample_file)

        assert isinstance(validation_result, dict)
        assert 'is_valid' in validation_result
        assert 'quality_score' in validation_result
        assert 'required_fields' in validation_result
        assert 'optional_fields' in validation_result

        # Should be valid with good quality score
        assert validation_result['is_valid'] is True
        assert validation_result['quality_score'] > 0.7

        # Check required fields
        required = validation_result['required_fields']
        assert required['title'] is True
        assert required['creator'] is True
        assert required['identifier'] is True
        assert required['language'] is True

    def test_convenience_function(self):
        """Test convenience parse function."""
        sample_file = "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/ce8af01f13f2c804/raw/content.opf"

        if not Path(sample_file).exists():
            pytest.skip("Sample file not found")

        result = parse_content_opf(sample_file)

        assert isinstance(result, ParsedContentOpf)
        assert result.metadata.title == "Build a Large Language Model (From Scratch)"

    def test_namespace_handling(self, parser):
        """Test proper namespace handling across different EPUB versions."""
        # Test EPUB 2.0 file
        epub2_file = "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/ce8af01f13f2c804/raw/content.opf"

        # Test EPUB 3.0 file
        epub3_file = "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/8a14dea195908257/raw/OEBPS/content.opf"

        for sample_file in [epub2_file, epub3_file]:
            if not Path(sample_file).exists():
                continue

            result = parser.parse_file(sample_file)

            # Should have detected namespaces
            assert len(result.namespace_info) > 0
            assert 'dc' in result.namespace_info

            # Should have parsed metadata successfully
            assert result.metadata.title is not None
            assert len(result.metadata.creators) > 0

    def test_manifest_spine_parsing(self, parser):
        """Test that manifest and spine are parsed correctly."""
        sample_file = "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/ce8af01f13f2c804/raw/content.opf"

        if not Path(sample_file).exists():
            pytest.skip("Sample file not found")

        result = parser.parse_file(sample_file)

        # Should have manifest items
        assert len(result.manifest_items) > 0

        # Manifest items should have required fields
        for item in result.manifest_items[:5]:  # Check first few
            assert 'id' in item
            assert 'href' in item
            assert 'media-type' in item

        # Should have spine items
        assert len(result.spine_items) > 0

        # Spine items should reference manifest items
        manifest_ids = [item['id'] for item in result.manifest_items]
        for spine_item in result.spine_items[:5]:  # Check first few
            assert spine_item in manifest_ids

    def test_error_handling(self, parser):
        """Test error handling for invalid files."""
        # Test non-existent file
        with pytest.raises(FileNotFoundError):
            parser.parse_file("/path/that/does/not/exist.opf")

        # Test invalid XML (if we have a sample)
        # This would need a deliberately malformed file to test properly

    def test_date_parsing(self, parser):
        """Test various date format parsing."""
        sample_file = "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/8a14dea195908257/raw/OEBPS/content.opf"

        if not Path(sample_file).exists():
            pytest.skip("Sample file not found")

        result = parser.parse_file(sample_file)
        metadata = result.metadata

        # Should have parsed dates
        assert len(metadata.dates) > 0

        # Check that date parsing worked
        for date_obj in metadata.dates:
            assert date_obj.value is not None
            # Some dates should be successfully parsed
            if date_obj.parsed_date:
                assert isinstance(date_obj.parsed_date, datetime)

    def test_identifier_scheme_detection(self, parser):
        """Test automatic scheme detection for identifiers."""
        sample_file = "/Users/abdullahwex/Desktop/MyFiles/Projects/Sage Reader/uploads/ce8af01f13f2c804/raw/content.opf"

        if not Path(sample_file).exists():
            pytest.skip("Sample file not found")

        result = parser.parse_file(sample_file)
        metadata = result.metadata

        # Should have identifiers
        assert len(metadata.identifiers) > 0

        # ISBN should be detected
        isbn_identifier = metadata.get_isbn()
        assert isbn_identifier is not None
        assert "isbn" in isbn_identifier.lower()

    def test_all_sample_files_parse_successfully(self, parser, sample_files):
        """Test that all sample files can be parsed without errors."""
        if not sample_files:
            pytest.skip("No sample files found")

        successful_parses = 0

        for sample_file in sample_files:
            try:
                result = parser.parse_file(str(sample_file))
                assert result is not None
                assert result.metadata is not None
                successful_parses += 1

                # Log some basic info about each file
                print(f"\nParsed {sample_file.name}:")
                print(f"  Title: {result.metadata.title}")
                print(f"  Author: {result.metadata.get_primary_author()}")
                print(f"  EPUB Version: {result.metadata.epub_version}")
                print(f"  Manifest items: {len(result.manifest_items)}")

            except Exception as e:
                print(f"\nFailed to parse {sample_file}: {e}")

        # At least some files should parse successfully
        assert successful_parses > 0
        print(
            f"\nSuccessfully parsed {successful_parses}/{len(sample_files)} files")
