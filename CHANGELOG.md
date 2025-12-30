# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/abdullahwex/epubsage/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/abdullahwex/epubsage/releases/tag/v0.1.0
