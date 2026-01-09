"""Search result scoring and highlighting."""

import re
from typing import List, Dict, Any

from .search_result import SearchResult


def rank_results(results: List[SearchResult], query: str) -> List[SearchResult]:
    """Rank search results by relevance."""
    for result in results:
        score = 1.0

        position_factor = 1.0 / (1 + result.match_position / 1000)
        score *= (1 + position_factor)

        context_lower = result.context.lower()
        if f' {query.lower()} ' in context_lower:
            score *= 1.5

        if query in result.context:
            score *= 1.2

        result.relevance_score = score

    return sorted(results, key=lambda r: r.relevance_score, reverse=True)


def highlight_matches(text: str, query: str,
                      highlight_start: str = '**',
                      highlight_end: str = '**') -> str:
    """Highlight search matches in text."""
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    def replace_func(match):
        return f"{highlight_start}{match.group()}{highlight_end}"

    return pattern.sub(replace_func, text)


def get_search_statistics(results: List[SearchResult]) -> Dict[str, Any]:
    """Get statistics about search results."""
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


def extract_context(content: str, match_pos: int, match_len: int,
                    context_size: int = 100) -> str:
    """Extract context around match position."""
    start = max(0, match_pos - context_size)
    end = min(len(content), match_pos + match_len + context_size)

    context = content[start:end].strip()

    if start > 0:
        context = '...' + context
    if end < len(content):
        context = context + '...'

    return context
