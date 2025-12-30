"""
Example usage of the Dublin Core metadata parser service.

This demonstrates how to use the service with real content.opf files
from the uploads directory.
"""
from pathlib import Path
from parse_service import DublinCoreService, parse_content_opf


def demonstrate_basic_usage():
    """Demonstrate basic usage of the Dublin Core parser."""
    print("=== Dublin Core Parser Demo ===\n")

    # Find sample files
    base_dir = Path(__file__).parent.parent
    uploads_dir = base_dir / "uploads"
    sample_files = list(uploads_dir.rglob("content.opf"))

    if not sample_files:
        print("No sample content.opf files found in uploads directory.")
        return

    print(f"Found {len(sample_files)} content.opf files\n")

    # Create service
    service = DublinCoreService()

    # Parse each file
    for i, sample_file in enumerate(sample_files[:3], 1):  # Limit to first 3
        print(f"--- Sample {i}: {sample_file.name} ---")

        try:
            # Method 1: Using service
            result = service.parse_content_opf(sample_file)
            metadata = result.metadata

            print(f"Title: {metadata.title}")
            print(f"Primary Author: {metadata.get_primary_author()}")
            print(f"Publisher: {metadata.publisher}")
            print(f"Language: {metadata.language}")
            print(f"EPUB Version: {metadata.epub_version}")
            print(f"ISBN: {metadata.get_isbn()}")
            print(f"Publication Date: {metadata.get_publication_date()}")

            if metadata.subjects:
                subjects = [s.value for s in metadata.subjects[:3]]
                print(f"Subjects: {', '.join(subjects)}")

            print(f"Manifest Items: {len(result.manifest_items)}")
            print(f"Spine Items: {len(result.spine_items)}")

            if result.parsing_errors:
                print(f"Parsing Warnings: {len(result.parsing_errors)}")

        except Exception as e:
            print(f"Error parsing {sample_file.name}: {e}")

        print()


def demonstrate_validation():
    """Demonstrate validation functionality."""
    print("=== Validation Demo ===\n")

    # Find sample files
    base_dir = Path(__file__).parent.parent
    uploads_dir = base_dir / "uploads"
    sample_files = list(uploads_dir.rglob("content.opf"))

    if not sample_files:
        print("No sample files found.")
        return

    service = DublinCoreService()

    for sample_file in sample_files[:2]:  # Limit to first 2
        print(f"Validating: {sample_file.name}")

        validation = service.validate_content_opf(sample_file)

        print(f"  Valid: {validation['is_valid']}")
        print(f"  Quality Score: {validation['quality_score']:.2f}")
        print(
            f"  Required Fields: {sum(1 for v in validation['required_fields'].values() if v)}/4")
        print(
            f"  Optional Fields: {sum(1 for v in validation['optional_fields'].values() if v)}/4")

        if validation['parsing_errors']:
            print(f"  Errors: {len(validation['parsing_errors'])}")

        print()


def demonstrate_convenience_functions():
    """Demonstrate convenience functions."""
    print("=== Convenience Functions Demo ===\n")

    # Find a sample file
    base_dir = Path(__file__).parent.parent
    uploads_dir = base_dir / "uploads"
    sample_files = list(uploads_dir.rglob("content.opf"))

    if not sample_files:
        print("No sample files found.")
        return

    sample_file = sample_files[0]
    print(f"Using file: {sample_file.name}")

    # Method 1: Direct parse function
    result = parse_content_opf(sample_file)
    print(f"Quick parse - Title: {result.metadata.title}")

    # Method 2: Basic metadata extraction
    service = DublinCoreService()
    basic_metadata = service.extract_basic_metadata(sample_file)

    print("\nBasic metadata dictionary:")
    for key, value in basic_metadata.items():
        if value:
            print(f"  {key}: {value}")


def demonstrate_namespace_handling():
    """Demonstrate namespace handling for different EPUB versions."""
    print("=== Namespace Handling Demo ===\n")

    # Find sample files
    base_dir = Path(__file__).parent.parent
    uploads_dir = base_dir / "uploads"
    sample_files = list(uploads_dir.rglob("content.opf"))

    if not sample_files:
        print("No sample files found.")
        return

    service = DublinCoreService()

    for sample_file in sample_files:
        result = service.parse_content_opf(sample_file)

        print(f"File: {sample_file.name}")
        print(f"  EPUB Version: {result.metadata.epub_version}")
        print("  Namespaces detected:")
        for prefix, uri in result.namespace_info.items():
            print(f"    {prefix or '(default)'}: {uri}")
        print()


if __name__ == "__main__":
    try:
        demonstrate_basic_usage()
        demonstrate_validation()
        demonstrate_convenience_functions()
        demonstrate_namespace_handling()
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()
