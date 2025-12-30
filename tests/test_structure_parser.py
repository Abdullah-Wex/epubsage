"""
Test suite for EPUB structure parser using real sample files.

Tests the complete structure parsing functionality with actual EPUB files
from the uploads directory to ensure pattern recognition works correctly.
"""
from epub_sage import create_service
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestStructureParser:
    """Test EPUB structure parsing with real files."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return create_service()

    @pytest.fixture
    def sample_files(self):
        """Get all sample content.opf files."""
        project_root = Path(__file__).parent.parent.parent
        content_files = list(project_root.glob("uploads/**/content.opf"))

        # Map files to their directories for context
        file_info = []
        for content_file in content_files:
            epub_dir = content_file.parent
            file_info.append({
                'opf_path': str(content_file),
                'epub_dir': str(epub_dir),
                'identifier': content_file.parent.parent.name
            })

        return file_info

    def test_basic_dublin_core_parsing(self, service, sample_files):
        """Test basic Dublin Core metadata parsing for all samples."""
        for file_info in sample_files:
            opf_path = file_info['opf_path']
            identifier = file_info['identifier']

            # Parse basic metadata
            try:
                metadata = service.extract_basic_metadata(opf_path)

                # Verify required fields exist
                assert 'title' in metadata, f"Missing title in {identifier}"
                assert 'author' in metadata, f"Missing author in {identifier}"
                assert 'language' in metadata, f"Missing language in {identifier}"

                # Log results
                print(f"\n{identifier}:")
                print(f"  Title: {metadata.get('title')}")
                print(f"  Author: {metadata.get('author')}")
                print(f"  Language: {metadata.get('language')}")
                print(f"  ISBN: {metadata.get('isbn')}")

            except Exception as e:
                pytest.fail(f"Failed to parse {identifier}: {e}")

    def test_complete_structure_parsing(self, service, sample_files):
        """Test complete structure parsing including chapters and images."""
        for file_info in sample_files:
            opf_path = file_info['opf_path']
            epub_dir = file_info['epub_dir']
            identifier = file_info['identifier']

            try:
                # Parse complete structure
                structure = service.parse_complete_structure(
                    opf_path, epub_dir)

                # Verify structure components
                assert hasattr(
                    structure, 'chapters'), f"Missing chapters in {identifier}"
                assert hasattr(
                    structure, 'images'), f"Missing images in {identifier}"
                assert hasattr(
                    structure, 'organization'), f"Missing organization in {identifier}"

                # Log structure summary
                print(f"\n{identifier} Structure:")
                print(f"  Chapters: {len(structure.chapters)}")
                print(f"  Images: {len(structure.images)}")
                print(f"  Parts: {len(structure.parts)}")
                print(
                    f"  Navigation entries: {len(structure.navigation_tree)}")

                # Verify chapter numbers
                chapter_numbers = [
                    ch.chapter_number for ch in structure.chapters if ch.chapter_number]
                if chapter_numbers:
                    print(f"  Chapter numbers: {sorted(set(chapter_numbers))}")

            except Exception as e:
                pytest.fail(f"Failed to parse structure for {identifier}: {e}")

    def test_chapter_outline(self, service, sample_files):
        """Test chapter outline extraction."""
        for file_info in sample_files:
            opf_path = file_info['opf_path']
            epub_dir = file_info['epub_dir']
            identifier = file_info['identifier']

            try:
                outline = service.get_chapter_outline(opf_path, epub_dir)

                # Verify outline structure
                assert 'total_chapters' in outline, f"Missing total_chapters in {identifier}"
                assert 'has_parts' in outline, f"Missing has_parts in {identifier}"

                print(f"\n{identifier} Outline:")
                print(f"  Total chapters: {outline['total_chapters']}")
                print(f"  Has parts: {outline['has_parts']}")

                if outline['has_parts'] and 'parts' in outline:
                    for part in outline['parts']:
                        print(
                            f"  Part: {part.get('title')} ({len(part.get('chapters', []))} chapters)")

            except Exception as e:
                pytest.fail(f"Failed to get outline for {identifier}: {e}")

    def test_content_organization(self, service, sample_files):
        """Test content organization analysis."""
        for file_info in sample_files:
            opf_path = file_info['opf_path']
            epub_dir = file_info['epub_dir']
            identifier = file_info['identifier']

            try:
                org = service.analyze_content_organization(opf_path, epub_dir)

                # Verify organization components
                assert 'summary' in org, f"Missing summary in {identifier}"
                assert 'organization' in org, f"Missing organization in {identifier}"

                print(f"\n{identifier} Organization:")
                org_data = org['organization']
                print(f"  Total chapters: {org_data.get('total_chapters')}")
                print(f"  Total parts: {org_data.get('total_parts')}")
                print(f"  Front matter: {org_data.get('front_matter_count')}")
                print(f"  Back matter: {org_data.get('back_matter_count')}")
                print(f"  Has TOC: {org_data.get('has_toc')}")
                print(
                    f"  Organization type: {
                        org_data.get('organization_type')}")

            except Exception as e:
                pytest.fail(
                    f"Failed to analyze organization for {identifier}: {e}")

    def test_image_distribution(self, service, sample_files):
        """Test image distribution analysis."""
        for file_info in sample_files:
            opf_path = file_info['opf_path']
            epub_dir = file_info['epub_dir']
            identifier = file_info['identifier']

            try:
                images = service.get_image_distribution(opf_path, epub_dir)

                # Verify image analysis
                assert 'total_count' in images, f"Missing total_count in {identifier}"
                assert 'image_types' in images, f"Missing image_types in {identifier}"

                print(f"\n{identifier} Images:")
                print(f"  Total images: {images['total_count']}")
                print(f"  Cover images: {images['cover_count']}")
                print(f"  Chapter images: {images['chapter_images']}")
                print(f"  Unassociated: {images['unassociated_images']}")

                if images['image_types']:
                    print(f"  Image types: {images['image_types']}")

                if images['avg_images_per_chapter'] > 0:
                    print(
                        f"  Avg per chapter: {
                            images['avg_images_per_chapter']:.1f}")

            except Exception as e:
                pytest.fail(f"Failed to analyze images for {identifier}: {e}")

    def test_reading_order(self, service, sample_files):
        """Test reading order extraction."""
        for file_info in sample_files:
            opf_path = file_info['opf_path']
            epub_dir = file_info['epub_dir']
            identifier = file_info['identifier']

            try:
                reading_order = service.extract_reading_order(
                    opf_path, epub_dir)

                # Verify reading order
                assert isinstance(
                    reading_order, list), f"Reading order not a list for {identifier}"

                print(f"\n{identifier} Reading Order:")
                print(f"  Total items: {len(reading_order)}")

                linear_items = [
                    item for item in reading_order if item.get('linear')]
                print(f"  Linear items: {len(linear_items)}")

                # Show first few items
                for i, item in enumerate(reading_order[:3]):
                    print(
                        f"  {
                            i +
                            1}. {
                            item.get('title')} ({
                            item.get('type')})")

            except Exception as e:
                pytest.fail(
                    f"Failed to extract reading order for {identifier}: {e}")

    def test_navigation_structure(self, service, sample_files):
        """Test navigation structure extraction."""
        for file_info in sample_files:
            opf_path = file_info['opf_path']
            epub_dir = file_info['epub_dir']
            identifier = file_info['identifier']

            try:
                nav = service.get_navigation_structure(opf_path, epub_dir)

                # Verify navigation structure
                assert 'has_navigation' in nav, f"Missing has_navigation in {identifier}"

                print(f"\n{identifier} Navigation:")
                print(f"  Has navigation: {nav['has_navigation']}")
                print(f"  TOC file: {nav.get('toc_file')}")
                print(f"  Max depth: {nav.get('max_depth')}")
                print(
                    f"  Total entries: {len(nav.get('navigation_tree', []))}")

                if nav['has_navigation'] and 'flat_navigation' in nav:
                    flat_nav = nav['flat_navigation'][:5]  # First 5 entries
                    for entry in flat_nav:
                        print(
                            f"    {
                                entry.get('label')} (level {
                                entry.get('level')})")

            except Exception as e:
                pytest.fail(
                    f"Failed to extract navigation for {identifier}: {e}")

    def test_validation(self, service, sample_files):
        """Test content.opf validation."""
        for file_info in sample_files:
            opf_path = file_info['opf_path']
            identifier = file_info['identifier']

            try:
                validation = service.validate_content_opf(opf_path)

                # Verify validation results
                assert 'is_valid' in validation, f"Missing is_valid in {identifier}"
                assert 'quality_score' in validation, f"Missing quality_score in {identifier}"

                print(f"\n{identifier} Validation:")
                print(f"  Is valid: {validation['is_valid']}")
                print(f"  Quality score: {validation['quality_score']:.2f}")
                print(
                    f"  Manifest items: {
                        validation.get('manifest_items_count')}")
                print(f"  Spine items: {validation.get('spine_items_count')}")

                if validation.get('parsing_errors'):
                    print(f"  Errors: {validation['parsing_errors']}")

            except Exception as e:
                pytest.fail(f"Failed to validate {identifier}: {e}")


if __name__ == "__main__":
    # Run tests directly
    import subprocess
    import sys

    # Install pytest if not available
    try:
        import pytest
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pytest"])
        import pytest

    # Run the tests
    pytest.main([__file__, "-v", "-s"])
