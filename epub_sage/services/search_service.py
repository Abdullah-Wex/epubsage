"""Search Service for EPUB content."""

import re
from typing import List, Dict, Any

from .search_result import SearchResult
from .search_scorer import (
    rank_results, highlight_matches, get_search_statistics, extract_context,
)


class SearchService:
    """Service for searching content within EPUB files."""

    def __init__(self, context_size: int = 100):
        self.context_size = context_size

    def search_content(self, chapters: List[Dict[str, Any]], query: str,
                       case_sensitive: bool = False) -> List[SearchResult]:
        """Search for query across all chapters."""
        results = []

        if not case_sensitive:
            query_lower = query.lower()

        for chapter in chapters:
            content = chapter.get('content', '')
            # Handle content as list of blocks (from process_epub)
            if isinstance(content, list):
                content = ' '.join(
                    block.get('text', '') for block in content if isinstance(block, dict)
                )
            chapter_id = chapter.get('chapter_id', 0)
            chapter_title = chapter.get('title', f'Chapter {chapter_id}')

            if case_sensitive:
                search_content = content
                search_query = query
            else:
                search_content = content.lower()
                search_query = query_lower

            start_pos = 0
            while True:
                match_pos = search_content.find(search_query, start_pos)
                if match_pos == -1:
                    break

                context = extract_context(
                    content, match_pos, len(query), self.context_size)
                results.append(SearchResult(
                    chapter_id=chapter_id,
                    chapter_title=chapter_title,
                    context=context,
                    match_position=match_pos
                ))
                start_pos = match_pos + 1

        return rank_results(results, query)

    def search_with_regex(self, chapters: List[Dict[str, Any]],
                          pattern: str) -> List[SearchResult]:
        """Search using regular expression pattern."""
        results = []

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return []

        for chapter in chapters:
            content = chapter.get('content', '')
            # Handle content as list of blocks (from process_epub)
            if isinstance(content, list):
                content = ' '.join(
                    block.get('text', '') for block in content if isinstance(block, dict)
                )
            chapter_id = chapter.get('chapter_id', 0)
            chapter_title = chapter.get('title', f'Chapter {chapter_id}')

            for match in regex.finditer(content):
                context = extract_context(
                    content, match.start(), match.end() - match.start(), self.context_size
                )
                results.append(SearchResult(
                    chapter_id=chapter_id,
                    chapter_title=chapter_title,
                    context=context,
                    match_position=match.start()
                ))

        return results

    def search_phrase(self, chapters: List[Dict[str, Any]],
                      phrase: str) -> List[SearchResult]:
        """Search for exact phrase match."""
        return self.search_content(chapters, phrase, case_sensitive=False)

    def search_sections(self, chapters: List[Dict[str, Any]], query: str,
                        case_sensitive: bool = False) -> List[SearchResult]:
        """Search within sections for more precise results."""
        results = []

        for chapter in chapters:
            chapter_id = chapter.get('chapter_id', 0)
            chapter_title = chapter.get('title', f'Chapter {chapter_id}')

            for section in chapter.get('sections', []):
                results.extend(self._search_section_recursive(
                    chapter_id, chapter_title, section, query,
                    case_sensitive, path=chapter_title
                ))

        return rank_results(results, query)

    def _search_section_recursive(self, chapter_id: int, chapter_title: str,
                                  section: Dict[str, Any], query: str,
                                  case_sensitive: bool, path: str) -> List[SearchResult]:
        """Recursively search section and its subsections."""
        results = []
        section_title = section.get('title', '')
        current_path = f"{path} > {section_title}" if path else section_title

        content = ' '.join(
            block.get('text', '') for block in section.get('content', [])
        )

        if content:
            if case_sensitive:
                search_content = content
                search_query = query
            else:
                search_content = content.lower()
                search_query = query.lower()

            start_pos = 0
            while True:
                match_pos = search_content.find(search_query, start_pos)
                if match_pos == -1:
                    break

                context = extract_context(
                    content, match_pos, len(query), self.context_size)
                results.append(SearchResult(
                    chapter_id=chapter_id,
                    chapter_title=chapter_title,
                    context=context,
                    match_position=match_pos,
                    section_id=section.get('id'),
                    section_title=section_title,
                    section_path=current_path
                ))
                start_pos = match_pos + 1

        for subsection in section.get('subsections', []):
            results.extend(self._search_section_recursive(
                chapter_id, chapter_title, subsection, query,
                case_sensitive, current_path
            ))

        return results

    def rank_results(self, results: List[SearchResult],
                     query: str) -> List[SearchResult]:
        """Rank search results by relevance."""
        return rank_results(results, query)

    def highlight_matches(self, text: str, query: str,
                          highlight_start: str = '**',
                          highlight_end: str = '**') -> str:
        """Highlight search matches in text."""
        return highlight_matches(text, query, highlight_start, highlight_end)

    def get_search_statistics(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Get statistics about search results."""
        return get_search_statistics(results)
