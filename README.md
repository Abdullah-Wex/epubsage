# EpubSage

[![PyPI version](https://img.shields.io/pypi/v/epubsage.svg)](https://pypi.org/project/epubsage/)
[![Python versions](https://img.shields.io/pypi/pyversions/epubsage.svg)](https://pypi.org/project/epubsage/)
[![Tests](https://github.com/Abdullah-Wex/epubsage/actions/workflows/tests.yml/badge.svg)](https://github.com/Abdullah-Wex/epubsage/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**EpubSage** is a powerful Python library and CLI tool for extracting structured content, metadata, and images from EPUB files. It handles the complexity of diverse publisher formats and provides a clean, unified API.

## Why EpubSage?

EPUB files vary significantly between publishers. Headers can be nested in `<span>` tags, chapters split across files, and metadata formats differ wildly. EpubSage abstracts this complexity:

```python
from epub_sage import process_epub

result = process_epub("book.epub")
print(f"Title: {result.title}")
print(f"Chapters: {result.total_chapters}")
```

That's it. One function call to extract everything.

## Features

| Feature | Description |
|---------|-------------|
| **Publisher-Agnostic** | Works with O'Reilly, Packt, Manning, and more |
| **Complete Extraction** | Chapters, metadata, images, word counts, reading time |
| **Smart Image Handling** | Discovers and validates all referenced images |
| **Content Classification** | Identifies front matter, chapters, back matter, parts |
| **Dublin Core Metadata** | Full standards-compliant metadata extraction |
| **TOC Parsing** | Supports NCX (EPUB 2) and NAV (EPUB 3) |
| **Full-Text Search** | Search across all book content |
| **CLI Tool** | 13 commands for complete EPUB analysis |

## Requirements

- Python 3.10+
- Dependencies: `beautifulsoup4`, `lxml`, `pydantic`, `typer`, `rich`

## Installation

```bash
pip install epubsage
```

Or with `uv`:

```bash
uv add epubsage
```

## Quick Start

### Python

```python
from epub_sage import process_epub

result = process_epub("book.epub")

print(f"Title: {result.title}")
print(f"Author: {result.author}")
print(f"Words: {result.total_words:,}")
print(f"Reading time: {result.estimated_reading_time}")

for chapter in result.chapters[:3]:
    print(f"  {chapter['chapter_id']}: {chapter['title']}")
```

![Python Basic Usage](docs/screenshots/python-basic.png)

### Command Line

```bash
epub-sage info book.epub
```

![CLI Info](docs/screenshots/cli-info.png)

## Command Line Interface

EpubSage includes 13 commands for complete EPUB analysis.

```bash
epub-sage --help
```

![CLI Help](docs/screenshots/cli-help.png)

| Command | Description |
|---------|-------------|
| `info` | Quick book summary |
| `stats` | Detailed statistics |
| `chapters` | List chapters with word counts |
| `metadata` | Dublin Core metadata |
| `toc` | Table of contents |
| `images` | Image distribution |
| `search` | Full-text search |
| `validate` | Validate EPUB structure |
| `spine` | Reading order |
| `manifest` | All EPUB resources |
| `extract` | Export to JSON |
| `list` | Raw EPUB contents |
| `cover` | Extract cover image |

**[View full CLI documentation →](docs/CLI.md)**

### Key Commands

#### chapters

```bash
epub-sage chapters book.epub
```

![CLI Chapters](docs/screenshots/cli-chapters.png)

#### search

```bash
epub-sage search book.epub "machine learning"
```

![CLI Search](docs/screenshots/cli-search.png)

#### extract

```bash
epub-sage extract book.epub -o output.json
```

![CLI Extract](docs/screenshots/cli-extract.png)

## Python Library

### Basic Processing

```python
from epub_sage import process_epub

result = process_epub("book.epub")

if result.success:
    print(f"Title: {result.title}")
    print(f"Author: {result.author}")
    print(f"Chapters: {result.total_chapters}")
else:
    print(f"Errors: {result.errors}")
```

### Iterate Chapters

```python
for chapter in result.chapters:
    print(f"{chapter['chapter_id']}: {chapter['title']}")
    print(f"  Words: {chapter['word_count']}")
    print(f"  Images: {len(chapter['images'])}")
    print(f"  Type: {chapter['content_type']}")
```

![Python Chapters](docs/screenshots/python-chapters.png)

### Access Metadata

```python
metadata = result.full_metadata

print(f"Title: {metadata.title}")
print(f"Publisher: {metadata.publisher}")
print(f"ISBN: {metadata.get_isbn()}")
print(f"Publication Date: {metadata.get_publication_date()}")
```

![Python Metadata](docs/screenshots/python-metadata.png)

### Extract Images

```python
for chapter in result.chapters:
    if chapter['images']:
        print(f"Chapter: {chapter['title']}")
        for img in chapter['images']:
            print(f"  - {img}")
```

![Python Images](docs/screenshots/python-images.png)

### Content Blocks

```python
chapter = result.chapters[0]

for block in chapter['content']:
    print(f"[{block['tag']}] {block['text'][:100]}...")
```

![Python Content](docs/screenshots/python-content.png)

**[View full API documentation →](docs/API.md)**

**[View real-world examples →](docs/EXAMPLES.md)**

## Output Format

### SimpleEpubResult

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str` | Book title |
| `author` | `str` | Primary author |
| `publisher` | `str` | Publisher name |
| `chapters` | `list[dict]` | Chapter data |
| `total_chapters` | `int` | Chapter count |
| `total_words` | `int` | Word count |
| `estimated_reading_time` | `dict` | `{'hours': N, 'minutes': N}` |
| `success` | `bool` | Processing status |
| `full_metadata` | `DublinCoreMetadata` | Complete metadata |

### Chapter Dictionary

| Field | Type | Description |
|-------|------|-------------|
| `chapter_id` | `int` | Sequential ID |
| `title` | `str` | Chapter title |
| `word_count` | `int` | Words in chapter |
| `images` | `list[str]` | Image paths |
| `content` | `list[dict]` | Content blocks |
| `content_type` | `str` | `chapter`, `front_matter`, `back_matter`, `part` |

**[View complete data models →](docs/API.md#data-models)**

## Architecture

```
epub_sage/
├── core/           # Parsers (Dublin Core, Structure, TOC)
├── extractors/     # EPUB handling, content extraction
├── processors/     # Processing pipelines
├── models/         # Pydantic data models
├── services/       # Search, export services
└── cli.py          # Command-line interface
```

**Processing Pipeline:**

1. `EpubExtractor` → Unzips EPUB
2. `DublinCoreParser` → Extracts metadata
3. `EpubStructureParser` → Analyzes structure
4. `ContentExtractor` → Extracts text & images
5. `SimpleEpubProcessor` → Orchestrates all steps

## Development

### Setup

```bash
git clone https://github.com/Abdullah-Wex/epubsage.git
cd epubsage
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Commands

```bash
make test      # Run 60+ tests
make format    # Format code
make lint      # Check quality
```

### Running Tests

```bash
PYTHONPATH="$PWD" .venv/bin/python -m pytest tests/ -v
```

## Documentation

| Document | Description |
|----------|-------------|
| [CLI Reference](docs/CLI.md) | Complete CLI documentation |
| [API Reference](docs/API.md) | Python API documentation |
| [Examples](docs/EXAMPLES.md) | Real-world use cases |

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

<p align="center">
  <strong>EpubSage</strong> — Extract. Analyze. Build.
</p>
