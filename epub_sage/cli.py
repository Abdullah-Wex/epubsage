import argparse
import sys
import os
from .processors import SimpleEpubProcessor, process_epub
from .services.export_service import save_to_json


def cmd_extract(args):
    """Handles the extraction of EPUB content to JSON."""
    print(f"🚀 Processing: {args.path}")

    processor = SimpleEpubProcessor()

    if os.path.isdir(args.path):
        result = processor.process_directory(args.path)
    else:
        result = processor.process_epub(args.path)

    if not result.success:
        print(f"❌ Error: {result.errors}")
        sys.exit(1)

    output_data = {
        "metadata": result.full_metadata.model_dump() if result.full_metadata else {
            "title": result.title,
            "author": result.author,
            "publisher": result.publisher,
            "language": result.language,
            "description": result.description,
            "isbn": result.isbn,
            "publication_date": result.publication_date},
        "statistics": {
            "total_words": result.total_words,
            "reading_time": result.estimated_reading_time,
            "chapter_count": len(
                result.chapters)},
        "chapters": result.chapters,
        "errors": result.errors}

    save_to_json(output_data, args.output)
    print(f"✅ Data saved to: {args.output}")


def cmd_info(args):
    """Displays basic metadata for an EPUB."""
    result = process_epub(args.path)
    if not result.success:
        print(f"❌ Error: {result.errors}")
        sys.exit(1)

    print("-" * 40)
    print(f"📖 Title:     {result.title}")
    print(f"👤 Author:    {result.author}")
    print(f"🏢 Publisher: {result.publisher}")
    print(f"📊 Words:     {result.total_words}")
    print(f"🕒 Est. Time: {result.estimated_reading_time} min")
    print(f"📑 Chapters:  {len(result.chapters)}")
    print("-" * 40)


def main():
    parser = argparse.ArgumentParser(
        prog="epub-sage",
        description="EpubSage: Modular EPUB Content Extractor")
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands")

    # Extract command
    extract_parser = subparsers.add_parser(
        "extract", help="Extract content to JSON")
    extract_parser.add_argument(
        "path", help="Path to EPUB file or extracted directory")
    extract_parser.add_argument(
        "-o",
        "--output",
        default="extracted_book.json",
        help="Output JSON path")

    # Info command
    info_parser = subparsers.add_parser("info", help="Display book metadata")
    info_parser.add_argument("path", help="Path to EPUB file")

    # List command (placeholder for now/minimal)
    list_parser = subparsers.add_parser(
        "list", help="List chapters and structure")
    list_parser.add_argument("path", help="Path to EPUB file")

    args = parser.parse_args()

    if args.command == "extract":
        cmd_extract(args)
    elif args.command == "info":
        cmd_info(args)
    elif args.command == "list":
        # Implementation of list can be added here or reuse info for now
        cmd_info(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
