# EpubSage

[![PyPI version](https://img.shields.io/pypi/v/epubsage.svg)](https://pypi.org/project/epubsage/)
[![Python versions](https://img.shields.io/pypi/pyversions/epubsage.svg)](https://pypi.org/project/epubsage/)
[![Tests](https://github.com/Abdullah-Wex/epubsage/actions/workflows/tests.yml/badge.svg)](https://github.com/Abdullah-Wex/epubsage/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**EpubSage** is a Python library for extracting structured content and metadata from EPUB files. It handles the complexity of diverse publisher formats (Manning, O'Reilly, Packt, etc.) and provides a clean, unified API for accessing book data.

---

## Why EpubSage?

EPUB files vary significantly between publishers. Headers can be nested in `<span>` tags, chapters can be split across files, and metadata formats differ. EpubSage abstracts this complexity:

-   **Publisher-Agnostic**: Tested against real-world books from major technical publishers.
-   **Complete Extraction**: Returns metadata, chapters, word counts, and reading time estimates.
-   **Modular**: Use the high-level `process_epub()` function, or access individual parsers directly.
-   **CLI Included**: Extract books from the command line without writing code.

---

## Table of Contents

1.  [Installation](#installation)
2.  [Quick Start](#quick-start)
3.  [API Reference](#api-reference)
4.  [Command Line Interface](#command-line-interface)
5.  [Architecture](#architecture)
6.  [Error Handling](#error-handling)
7.  [Development](#development)
8.  [License](#license)

---

## Installation

```bash
pip install epubsage
```

For development with `uv`:

```bash
uv add epubsage
```

---

## Quick Start

### Basic Usage

```python
from epub_sage import process_epub

result = process_epub("my_book.epub")

if result.success:
    print(f"Title: {result.title}")
    print(f"Author: {result.author}")
    print(f"Chapters: {result.total_chapters}")
    print(f"Words: {result.total_words}")
else:
    print(f"Errors: {result.errors}")
```

### Export to JSON

```python
from epub_sage import process_epub, save_to_json

result = process_epub("my_book.epub")

output = {
    "title": result.title,
    "author": result.author,
    "chapters": result.chapters
}
save_to_json(output, "book_data.json")
```

---

## API Reference

### High-Level Functions

| Function | Description |
|----------|-------------|
| `process_epub(path)` | Process an EPUB file. Returns `SimpleEpubResult`. |
| `quick_extract(path)` | Extract EPUB to a directory. Returns path string. |
| `get_epub_info(path)` | Get file info without extraction. Returns dict. |
| `save_to_json(data, path)` | Save data to JSON with datetime support. |
| `parse_content_opf(path)` | Parse `content.opf` directly. Returns `ParsedContentOpf`. |

### Classes

#### SimpleEpubProcessor

Main processing class for full control over the extraction pipeline.

```python
from epub_sage import SimpleEpubProcessor

processor = SimpleEpubProcessor(temp_dir="/tmp/work")
result = processor.process_epub("book.epub", cleanup=True)

# Or process a pre-extracted directory
result = processor.process_directory("/path/to/extracted/")
```

**Methods:**

| Method | Description |
|--------|-------------|
| `process_epub(path, cleanup=True)` | Full pipeline: extract, parse, return result. |
| `process_directory(path)` | Process already-extracted EPUB contents. |
| `quick_info(path)` | Return metadata only, minimal processing. |

#### EpubExtractor

Low-level ZIP handling and file management.

```python
from epub_sage import EpubExtractor

extractor = EpubExtractor(base_dir="/tmp/epubs")
path = extractor.extract_epub("book.epub")
opf = extractor.find_content_opf(path)
extractor.cleanup_extraction(path)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `extract_epub(path)` | Extract ZIP to managed directory. |
| `get_epub_info(path)` | File stats without extraction. |
| `find_content_opf(dir)` | Locate `content.opf` in extracted tree. |
| `validate_epub_structure(path)` | Check EPUB spec compliance. |
| `cleanup_extraction(dir)` | Delete extracted files. |

#### DublinCoreParser

Parse `content.opf` for Dublin Core metadata.

```python
from epub_sage import DublinCoreParser

parser = DublinCoreParser()
result = parser.parse_file("/path/to/content.opf")

print(result.metadata.title)
print(result.metadata.get_primary_author())
print(result.metadata.get_isbn())
```

#### EpubStructureParser

Full structure analysis: chapters, parts, images, navigation.

```python
from epub_sage import EpubStructureParser, DublinCoreParser

dc_parser = DublinCoreParser()
opf_data = dc_parser.parse_file(opf_path)

struct_parser = EpubStructureParser()
structure = struct_parser.parse_structure(opf_data, epub_dir)

print(f"Chapters: {len(structure.chapters)}")
print(f"Images: {len(structure.images)}")
```

### Data Models

#### SimpleEpubResult

Returned by `process_epub()`.

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str` | Book title |
| `author` | `str` | Primary author |
| `publisher` | `str` | Publisher name |
| `language` | `str` | Language code |
| `chapters` | `list[dict]` | Chapter data with content |
| `total_chapters` | `int` | Chapter count |
| `total_words` | `int` | Word count |
| `estimated_reading_time` | `dict` | `{'hours': N, 'minutes': N}` |
| `success` | `bool` | Processing status |
| `errors` | `list[str]` | Error messages |

#### DublinCoreMetadata

Pydantic model for metadata.

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str` | Book title |
| `creators` | `list` | Author objects with roles |
| `publisher` | `str` | Publisher name |
| `language` | `str` | ISO language code |
| `identifiers` | `list` | ISBN, UUID, etc. |
| `dates` | `list` | Publication dates |
| `description` | `str` | Book description |

**Helper Methods:** `get_primary_author()`, `get_isbn()`, `get_publication_date()`

---

## Command Line Interface

### Extract to JSON

```bash
epub-sage extract book.epub -o output.json
```

### Display Metadata

```bash
epub-sage info book.epub
```

Output:
```
----------------------------------------
Title:     Build a Large Language Model (From Scratch)
Author:    Sebastian Raschka
Publisher: Manning Publications Co.
Words:     84287
Est. Time: 5 hours, 37 min
Chapters:  21
----------------------------------------
```

### List Chapters

```bash
epub-sage list book.epub
```

---

## Architecture

```
epub_sage/
├── core/                 # Low-level parsers
│   ├── dublin_core_parser.py
│   ├── structure_parser.py
│   ├── toc_parser.py
│   └── content_classifier.py
├── extractors/           # EPUB handling
│   ├── epub_extractor.py
│   └── content_extractor.py
├── processors/           # High-level pipelines
│   └── simple_processor.py
├── models/               # Pydantic data models
├── services/             # Export, search
└── utils/                # Helpers
```

**Data Flow:**

1.  `EpubExtractor` unzips the EPUB file.
2.  `DublinCoreParser` reads `content.opf` for metadata.
3.  `EpubStructureParser` analyzes chapters, images, and TOC.
4.  `ContentExtractor` pulls text content from HTML files.
5.  `SimpleEpubProcessor` orchestrates all steps and returns `SimpleEpubResult`.

---

## Error Handling

`SimpleEpubResult.success` indicates overall status. Errors are collected in `SimpleEpubResult.errors`:

```python
result = process_epub("book.epub")

if not result.success:
    for error in result.errors:
        print(f"Error: {error}")
```

Common errors:
-   `"File not found"` - EPUB path invalid.
-   `"Invalid ZIP/EPUB file"` - Corrupted or non-EPUB file.
-   `"No content.opf file found"` - Missing required metadata file.
-   `"Content extraction error: ..."` - HTML parsing issue.

---

## Development

```bash
make install   # Setup environment with uv
make format    # Run autopep8 and ruff
make lint      # Check code quality
make test      # Run test suite (60+ tests)
make clean     # Remove caches
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
