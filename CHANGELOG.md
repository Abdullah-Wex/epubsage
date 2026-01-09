# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-01-09

### Added

- **TOC-Based Content Extraction** - Extract content using Table of Contents anchor boundaries for precise section splitting
  - `NavigationPoint.anchor` and `NavigationPoint.file_path` fields for parsed href components
  - New `toc_content_extractor.py` module with:
    - `SectionBoundary` model for defining content boundaries
    - `ExtractedSection` model for extracted section content
    - `build_section_boundaries()` function to compute section boundaries per file
    - `extract_book_by_toc()` function for full book extraction
  - `EpubStructureParser.extract_content_by_toc()` method for TOC-based extraction
- Precise section splitting based on publisher-defined TOC structure instead of header-based detection
- **Chapter Sections** - Each chapter now includes a `sections` field with TOC-based hierarchical content
  - Section structure: `id`, `title`, `level`, `content`, `images`, `word_count`, `subsections`
  - Nested `subsections` array matches TOC tree structure exactly
  - Uses existing TOC extraction for precise section boundaries

### Changed

- **CLI Rewrite** - Complete rewrite using Typer and Rich for better UX
  - New `epub_sage/cli/` directory structure
  - Commands: info, content, export, images, media, metadata
  - Modern CLI with colors and rich output
- **Code Modularization** - Split monolithic files into focused modules
  - Extractors: element_extractors, specialized_extractors, html_parser, image_resolver
  - Processors: orchestrator, content_consolidator, helpers, result
  - Major code reduction (-4,405 lines, +639 lines)
- Converted dataclasses to Pydantic models for consistency

### Fixed

- Type annotation fixes for mypy strict mode compliance
- Proper Optional types for model fields

## [0.2.0] - 2025-01-03

### Added

- CLI commands with basic output
- Comprehensive documentation

## [0.1.1] - 2024-12-30

### Fixed

- Build configuration improvements

## [0.1.0] - 2024-12-30

### Added

- Initial release of EpubSage
- **Core Parsers**
  - `DublinCoreParser` - Full Dublin Core metadata extraction (15 elements)
  - `EpubStructureParser` - Complete EPUB structure analysis
  - `TocParser` - Table of Contents parsing (NCX and nav documents)
  - `ContentClassifier` - Pattern-based content classification
- **Extractors**
  - `EpubExtractor` - ZIP extraction and file management
  - `content_extractor` - HTML content extraction with header detection
- **Processors**
  - `SimpleEpubProcessor` - One-step EPUB processing pipeline
  - `SimpleEpubResult` - Flat result dataclass
- **Services**
  - `SearchService` - Full-text search across chapters
  - `save_to_json` - JSON export with datetime support
- **Models**
  - Pydantic models for Dublin Core metadata
  - Pydantic models for EPUB structure
- **CLI**
  - `epub-sage extract` - Extract EPUB to JSON
  - `epub-sage info` - Display metadata
  - `epub-sage list` - List chapters
- **Utilities**
  - XML namespace handling
  - Text statistics and reading time estimation
- Publisher-agnostic pattern recognition (Manning, O'Reilly, Packt, etc.)
- Type hints throughout with `py.typed` marker
- Comprehensive test suite (60+ tests)

[Unreleased]: https://github.com/Abdullah-Wex/epubsage/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/Abdullah-Wex/epubsage/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Abdullah-Wex/epubsage/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/Abdullah-Wex/epubsage/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Abdullah-Wex/epubsage/releases/tag/v0.1.0
