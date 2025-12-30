"""
Pydantic models for Dublin Core metadata extracted from EPUB content.opf files.
Based on Dublin Core Metadata Element Set (DCMES) specification.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class DublinCoreIdentifier(BaseModel):
    """Dublin Core identifier with optional scheme and ID."""
    value: str
    id: Optional[str] = None
    scheme: Optional[str] = None  # ISBN, UUID, etc.


class DublinCoreCreator(BaseModel):
    """Dublin Core creator (author) with optional role and file-as attributes."""
    name: str
    role: Optional[str] = None  # aut, edt, etc. (MARC relators)
    file_as: Optional[str] = None  # sorting form


class DublinCoreDate(BaseModel):
    """Dublin Core date with optional event type."""
    value: str
    event: Optional[str] = None  # publication, modification, creation
    parsed_date: Optional[datetime] = None


class DublinCoreSubject(BaseModel):
    """Dublin Core subject/topic."""
    value: str
    scheme: Optional[str] = None  # classification scheme


class DublinCoreMetadata(BaseModel):
    """
    Complete Dublin Core metadata extracted from EPUB content.opf files.

    Based on the 15 core Dublin Core elements with extensions for EPUB-specific attributes.
    """
    # Core Dublin Core elements
    title: Optional[str] = None
    creators: List[DublinCoreCreator] = Field(default_factory=list)
    publisher: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None
    subjects: List[DublinCoreSubject] = Field(default_factory=list)
    dates: List[DublinCoreDate] = Field(default_factory=list)
    identifiers: List[DublinCoreIdentifier] = Field(default_factory=list)
    rights: Optional[str] = None

    # Additional metadata commonly found in EPUB files
    # Usually application/epub+zip
    format_: Optional[str] = Field(None, alias="format")
    source: Optional[str] = None
    relation: Optional[str] = None
    coverage: Optional[str] = None
    type_: Optional[str] = Field(None, alias="type")
    contributor: Optional[str] = None

    # EPUB-specific metadata
    unique_identifier: Optional[str] = None  # from package/@unique-identifier
    epub_version: Optional[str] = None  # EPUB 2.0 or 3.0
    modified_date: Optional[datetime] = None  # dcterms:modified

    # Raw metadata for debugging/extension
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {'populate_by_name': True}

    @field_validator('creators', mode='before')
    @classmethod
    def parse_creators(cls, v):
        """Handle single creator or list of creators."""
        if isinstance(v, str):
            return [DublinCoreCreator(name=v)]
        if isinstance(v, dict):
            return [DublinCoreCreator(**v)]
        return v or []

    @field_validator('subjects', mode='before')
    @classmethod
    def parse_subjects(cls, v):
        """Handle single subject or list of subjects."""
        if isinstance(v, str):
            return [DublinCoreSubject(value=v)]
        if isinstance(v, dict):
            return [DublinCoreSubject(**v)]
        return v or []

    @field_validator('identifiers', mode='before')
    @classmethod
    def parse_identifiers(cls, v):
        """Handle single identifier or list of identifiers."""
        if isinstance(v, str):
            return [DublinCoreIdentifier(value=v)]
        if isinstance(v, dict):
            return [DublinCoreIdentifier(**v)]
        return v or []

    @field_validator('dates', mode='before')
    @classmethod
    def parse_dates(cls, v):
        """Handle single date or list of dates."""
        if isinstance(v, str):
            return [DublinCoreDate(value=v)]
        if isinstance(v, dict):
            return [DublinCoreDate(**v)]
        return v or []

    def get_primary_author(self) -> Optional[str]:
        """Get the primary author name."""
        authors = [c.name for c in self.creators if c.role in (None, 'aut')]
        return authors[0] if authors else None

    def get_isbn(self) -> Optional[str]:
        """Get ISBN identifier if available."""
        for identifier in self.identifiers:
            if identifier.scheme == 'isbn' or 'isbn' in identifier.value.lower():
                return identifier.value
        return None

    def get_publication_date(self) -> Optional[str]:
        """Get publication date if available."""
        for date in self.dates:
            if date.event in (None, 'publication'):
                return date.value
        return None


class ParsedContentOpf(BaseModel):
    """
    Complete parsed content.opf file including Dublin Core metadata and manifest info.
    """
    metadata: DublinCoreMetadata
    manifest_items: List[Dict[str, str]] = Field(default_factory=list)
    spine_items: List[str] = Field(default_factory=list)
    guide_items: List[Dict[str, str]] = Field(default_factory=list)

    # File information
    file_path: Optional[str] = None
    namespace_info: Dict[str, str] = Field(default_factory=dict)
    parsing_errors: List[str] = Field(default_factory=list)

    def resolve_href(self, href: str, epub_root: str) -> str:
        """
        Resolve a manifest href to a path relative to the EPUB root.

        Args:
            href: The href from manifest
            epub_root: Absolute path to EPUB root directory

        Returns:
            EPUB-root-relative path (e.g. 'OEBPS/Text/ch01.xhtml')
        """
        if not self.file_path:
            return href

        import os

        # Absolute directory of the OPF file
        opf_dir = os.path.dirname(os.path.abspath(self.file_path))

        # Absolute path of the target file
        parts = href.split('#', 1)
        pure_href = parts[0]
        fragment = f"#{parts[1]}" if len(parts) > 1 else ""

        abs_target = os.path.normpath(os.path.join(opf_dir, pure_href))

        # Path relative to EPUB root
        try:
            rel_path = os.path.relpath(abs_target, os.path.abspath(epub_root))
            # Normalize separators to forward slashes for internal consistency
            return rel_path.replace('\\', '/') + fragment
        except Exception:
            return pure_href + fragment

    @property
    def manifest(self) -> List[Dict[str, str]]:
        """Backward compatibility for manifest."""
        return self.manifest_items

    @property
    def spine(self) -> List[str]:
        """Backward compatibility for spine."""
        return self.spine_items
