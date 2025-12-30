"""
Structure models for EPUB content organization.

Based on analysis of real content.opf and TOC files from uploaded samples.
Follows SOLID, KISS, DRY, YAGNI principles for simple, maintainable code.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ContentType(Enum):
    """Content classification based on EPUB structure analysis."""
    CHAPTER = "chapter"
    FRONT_MATTER = "front_matter"
    BACK_MATTER = "back_matter"
    INDEX = "index"
    PART = "part"
    IMAGE = "image"
    COVER = "cover"
    NAVIGATION = "navigation"
    STYLESHEET = "stylesheet"
    FONT = "font"
    OTHER = "other"


class StructureItem(BaseModel):
    """
    Represents a structural element in an EPUB.

    Covers chapters, parts, front/back matter with hierarchy support.
    """
    id: str
    title: str
    href: str
    content_type: ContentType
    order: int

    # Hierarchical information
    level: int = 1
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)

    # Chapter/Part numbering
    chapter_number: Optional[int] = None
    part_number: Optional[int] = None
    section_number: Optional[str] = None  # e.g., "1.2.3"

    # Additional metadata
    media_type: Optional[str] = None
    properties: List[str] = Field(default_factory=list)
    linear: bool = True


class ImageItem(BaseModel):
    """
    Represents an image file in the EPUB with classification.
    """
    id: str
    filename: str
    href: str
    media_type: str

    # Classification
    image_type: str = "figure"  # cover, figure, diagram, chart, etc.
    chapter_number: Optional[int] = None
    part_number: Optional[int] = None

    # Properties
    is_cover: bool = False
    file_size: Optional[int] = None

    # Association with content
    associated_content_id: Optional[str] = None


class NavigationPoint(BaseModel):
    """
    Represents a navigation entry from TOC with hierarchy.
    """
    id: str
    label: str
    href: str
    play_order: int
    level: int = 1

    # Hierarchy
    parent_id: Optional[str] = None
    children: List["NavigationPoint"] = Field(default_factory=list)

    # Classification
    nav_type: str = "chapter"  # chapter, section, part, etc.
    chapter_number: Optional[int] = None
    section_number: Optional[str] = None


class ContentOrganization(BaseModel):
    """
    High-level organization metrics for the EPUB.
    """
    total_chapters: int = 0
    total_parts: int = 0
    total_images: int = 0

    has_index: bool = False
    has_toc: bool = False
    has_parts: bool = False

    # Front matter counts
    front_matter_count: int = 0
    back_matter_count: int = 0

    # Structure depth
    max_toc_depth: int = 1
    max_chapter_sections: int = 0

    # Image distribution
    images_per_chapter: Dict[int, int] = Field(default_factory=dict)
    cover_images_count: int = 0


class EpubStructure(BaseModel):
    """
    Complete structural representation of an EPUB.

    Organizes all content by type with relationships and hierarchy.
    """
    # Content organization by type
    chapters: List[StructureItem] = Field(default_factory=list)
    parts: List[StructureItem] = Field(default_factory=list)
    front_matter: List[StructureItem] = Field(default_factory=list)
    back_matter: List[StructureItem] = Field(default_factory=list)
    index_items: List[StructureItem] = Field(default_factory=list)

    # Media assets
    images: List[ImageItem] = Field(default_factory=list)
    stylesheets: List[StructureItem] = Field(default_factory=list)
    fonts: List[StructureItem] = Field(default_factory=list)

    # Navigation structure
    navigation_tree: List[NavigationPoint] = Field(default_factory=list)
    reading_order: List[str] = Field(default_factory=list)  # Spine order

    # Analysis summary
    organization: ContentOrganization = Field(
        default_factory=ContentOrganization)

    # Processing metadata
    toc_file_path: Optional[str] = None
    parsing_errors: List[str] = Field(default_factory=list)

    def get_chapter_by_number(
            self,
            chapter_num: int) -> Optional[StructureItem]:
        """Get chapter by its number."""
        for chapter in self.chapters:
            if chapter.chapter_number == chapter_num:
                return chapter
        return None

    def get_chapters_in_part(self, part_num: int) -> List[StructureItem]:
        """Get all chapters belonging to a specific part."""
        return [ch for ch in self.chapters if ch.part_number == part_num]

    def get_images_for_chapter(self, chapter_num: int) -> List[ImageItem]:
        """Get all images associated with a specific chapter."""
        return [img for img in self.images if img.chapter_number == chapter_num]

    def get_cover_image(self) -> Optional[ImageItem]:
        """Get the main cover image."""
        covers = [img for img in self.images if img.is_cover]
        return covers[0] if covers else None

    def get_reading_sequence(self) -> List[StructureItem]:
        """Get content items in reading order."""
        sequence = []

        # Add front matter
        sequence.extend(sorted(self.front_matter, key=lambda x: x.order))

        # Add parts and chapters in order
        if self.parts:
            for part in sorted(self.parts, key=lambda x: x.order):
                sequence.append(part)
                part_chapters = self.get_chapters_in_part(
                    part.part_number or 0)
                sequence.extend(sorted(part_chapters, key=lambda x: x.order))
        else:
            sequence.extend(sorted(self.chapters, key=lambda x: x.order))

        # Add back matter
        sequence.extend(sorted(self.back_matter, key=lambda x: x.order))

        # Add index
        sequence.extend(sorted(self.index_items, key=lambda x: x.order))

        return sequence

    def get_structure_summary(self) -> Dict[str, Any]:
        """Get a summary of the EPUB structure."""
        return {
            "chapters": len(self.chapters),
            "parts": len(self.parts),
            "front_matter": len(self.front_matter),
            "back_matter": len(self.back_matter),
            "images": len(self.images),
            "has_index": len(self.index_items) > 0,
            "has_navigation": len(self.navigation_tree) > 0,
            "reading_order_items": len(self.reading_order),
            "max_toc_depth": max([nav.level for nav in self.navigation_tree], default=1),
            "cover_image": self.get_cover_image() is not None,
            "organization_type": "parts" if self.parts else "chapters"
        }


# Update NavigationPoint to handle self-referencing
NavigationPoint.model_rebuild()
