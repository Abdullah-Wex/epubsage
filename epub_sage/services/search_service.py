"""
Search Service for EPUB content.

Provides search functionality across chapters and content.
"""
import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a single search result."""
    chapter_id: int
    chapter_title: str
    context: str
    match_position: int
    relevance_score: float = 1.0


class SearchService:
    """
    Service for searching content within EPUB files.

    Provides text search with context and ranking capabilities.
    """

    def __init__(self, context_size: int = 100):
        """
        Initialize search service.

        Args:
            context_size: Number of characters to show before and after match
        """
        self.context_size = context_size

    def search_content(self, chapters: List[Dict[str, Any]], query: str,
                       case_sensitive: bool = False) -> List[SearchResult]:
        """
        Search for query across all chapters.

        Args:
            chapters: List of chapter dictionaries with 'content' field
            query: Search query
            case_sensitive: Whether search should be case-sensitive

        Returns:
            List of SearchResult objects
        """
        results = []

        # Prepare query
        if not case_sensitive:
            query_lower = query.lower()

        for chapter in chapters:
            content = chapter.get('content', '')
            chapter_id = chapter.get('chapter_id', 0)
            chapter_title = chapter.get('title', f'Chapter {chapter_id}')

            # Search for matches
            if case_sensitive:
                search_content = content
                search_query = query
            else:
                search_content = content.lower()
                search_query = query_lower

            # Find all matches
            start_pos = 0
            while True:
                match_pos = search_content.find(search_query, start_pos)
                if match_pos == -1:
                    break

                # Extract context
                context = self._extract_context(content, match_pos, len(query))

                # Create result
                result = SearchResult(
                    chapter_id=chapter_id,
                    chapter_title=chapter_title,
                    context=context,
                    match_position=match_pos
                )
                results.append(result)

                # Move to next potential match
                start_pos = match_pos + 1

        # Rank results
        ranked_results = self.rank_results(results, query)

        return ranked_results

    def search_with_regex(
            self, chapters: List[Dict[str, Any]], pattern: str) -> List[SearchResult]:
        """
        Search using regular expression pattern.

        Args:
            chapters: List of chapter dictionaries
            pattern: Regular expression pattern

        Returns:
            List of SearchResult objects
        """
        results = []

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return []  # Invalid regex

        for chapter in chapters:
            content = chapter.get('content', '')
            chapter_id = chapter.get('chapter_id', 0)
            chapter_title = chapter.get('title', f'Chapter {chapter_id}')

            # Find all matches
            for match in regex.finditer(content):
                context = self._extract_context(
                    content, match.start(), match.end() - match.start())

                result = SearchResult(
                    chapter_id=chapter_id,
                    chapter_title=chapter_title,
                    context=context,
                    match_position=match.start()
                )
                results.append(result)

        return results

    def search_phrase(
            self, chapters: List[Dict[str, Any]], phrase: str) -> List[SearchResult]:
        """
        Search for exact phrase match.

        Args:
            chapters: List of chapter dictionaries
            phrase: Exact phrase to search

        Returns:
            List of SearchResult objects
        """
        # Use quotes to ensure exact phrase matching
        return self.search_content(chapters, phrase, case_sensitive=False)

    def rank_results(
            self,
            results: List[SearchResult],
            query: str) -> List[SearchResult]:
        """
        Rank search results by relevance.

        Args:
            results: List of search results
            query: Original search query

        Returns:
            Sorted list of results by relevance
        """
        for result in results:
            # Simple relevance scoring based on:
            # 1. Position in chapter (earlier is better)
            # 2. Word boundary matches
            # 3. Case match

            score = 1.0

            # Earlier in chapter scores higher
            position_factor = 1.0 / (1 + result.match_position / 1000)
            score *= (1 + position_factor)

            # Check if match is at word boundary
            context_lower = result.context.lower()
            if f' {query.lower()} ' in context_lower:
                score *= 1.5  # Bonus for whole word match

            # Check for exact case match
            if query in result.context:
                score *= 1.2  # Bonus for exact case

            result.relevance_score = score

        # Sort by relevance score (highest first)
        return sorted(results, key=lambda r: r.relevance_score, reverse=True)

    def _extract_context(
            self,
            content: str,
            match_pos: int,
            match_len: int) -> str:
        """
        Extract context around match position.

        Args:
            content: Full content text
            match_pos: Position of match
            match_len: Length of matched text

        Returns:
            Context string with match in the middle
        """
        # Calculate context boundaries
        start = max(0, match_pos - self.context_size)
        end = min(len(content), match_pos + match_len + self.context_size)

        # Extract context
        context = content[start:end].strip()

        # Add ellipsis if truncated
        if start > 0:
            context = '...' + context
        if end < len(content):
            context = context + '...'

        return context

    def highlight_matches(self, text: str, query: str,
                          highlight_start: str = '**',
                          highlight_end: str = '**') -> str:
        """
        Highlight search matches in text.

        Args:
            text: Text to highlight matches in
            query: Search query
            highlight_start: String to insert before match
            highlight_end: String to insert after match

        Returns:
            Text with highlighted matches
        """
        # Case-insensitive replacement while preserving original case
        pattern = re.compile(re.escape(query), re.IGNORECASE)

        def replace_func(match):
            return f"{highlight_start}{match.group()}{highlight_end}"

        return pattern.sub(replace_func, text)

    def get_search_statistics(
            self, results: List[SearchResult]) -> Dict[str, Any]:
        """
        Get statistics about search results.

        Args:
            results: List of search results

        Returns:
            Dictionary with search statistics
        """
        if not results:
            return {
                'total_matches': 0,
                'chapters_with_matches': 0,
                'average_relevance': 0.0
            }

        chapter_ids = set(r.chapter_id for r in results)
        avg_relevance = sum(r.relevance_score for r in results) / len(results)

        return {
            'total_matches': len(results),
            'chapters_with_matches': len(chapter_ids),
            'average_relevance': avg_relevance,
            'matches_per_chapter': {
                chapter_id: sum(1 for r in results if r.chapter_id == chapter_id)
                for chapter_id in chapter_ids
            }
        }
