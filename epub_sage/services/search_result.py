"""Search result data structures."""

from typing import Optional

from pydantic import BaseModel


class SearchResult(BaseModel):
    """Represents a single search result."""
    chapter_id: int
    chapter_title: str
    context: str
    match_position: int
    section_id: Optional[str] = None
    section_title: Optional[str] = None
    section_path: Optional[str] = None
    relevance_score: float = 1.0
