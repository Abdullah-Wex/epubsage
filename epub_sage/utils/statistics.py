"""Statistics utilities for EPUB content analysis."""

from typing import Dict, List, Any

from .text_analyzer import (
    calculate_word_count, calculate_sentence_count, calculate_paragraph_count,
    calculate_readability_score, calculate_vocabulary_richness, get_text_statistics,
)

# Re-export for backwards compatibility
__all__ = [
    'EpubStatistics', 'calculate_reading_time', 'get_text_statistics',
]

READING_SPEEDS = {'slow': 200, 'average': 250, 'fast': 300}


class EpubStatistics:
    """Calculate various statistics for EPUB content."""

    READING_SPEEDS = READING_SPEEDS

    @staticmethod
    def calculate_word_count(text: str) -> int:
        return calculate_word_count(text)

    @staticmethod
    def calculate_sentence_count(text: str) -> int:
        return calculate_sentence_count(text)

    @staticmethod
    def calculate_paragraph_count(text: str) -> int:
        return calculate_paragraph_count(text)

    @classmethod
    def estimate_reading_time(cls, word_count: int, reading_speed: str = 'average') -> Dict[str, int]:
        """Estimate reading time based on word count."""
        wpm = cls.READING_SPEEDS.get(reading_speed, cls.READING_SPEEDS['average'])
        total_minutes = word_count / wpm
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        return {'hours': hours, 'minutes': minutes, 'total_minutes': int(total_minutes)}

    @staticmethod
    def calculate_readability_score(text: str) -> Dict[str, float]:
        return calculate_readability_score(text)

    @staticmethod
    def calculate_chapter_statistics(chapters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for a list of chapters."""
        if not chapters:
            return {
                'total_chapters': 0, 'total_words': 0, 'total_characters': 0,
                'average_words_per_chapter': 0, 'shortest_chapter': None,
                'longest_chapter': None, 'reading_time': {'hours': 0, 'minutes': 0}
            }

        total_words = 0
        total_chars = 0
        chapter_word_counts = []

        for chapter in chapters:
            content = chapter.get('content', '')
            word_count = chapter.get('word_count')
            if word_count is None:
                word_count = calculate_word_count(content)

            total_words += word_count
            total_chars += len(content)
            chapter_word_counts.append({
                'chapter_id': chapter.get('chapter_id', 0),
                'title': chapter.get('title', 'Unknown'),
                'word_count': word_count
            })

        chapter_word_counts.sort(key=lambda x: x['word_count'])

        return {
            'total_chapters': len(chapters),
            'total_words': total_words,
            'total_characters': total_chars,
            'average_words_per_chapter': total_words // len(chapters) if chapters else 0,
            'shortest_chapter': chapter_word_counts[0] if chapter_word_counts else None,
            'longest_chapter': chapter_word_counts[-1] if chapter_word_counts else None,
            'reading_time': EpubStatistics.estimate_reading_time(total_words),
            'chapter_word_distribution': chapter_word_counts
        }

    @staticmethod
    def calculate_vocabulary_richness(text: str) -> Dict[str, Any]:
        return calculate_vocabulary_richness(text)

    @staticmethod
    def generate_summary_statistics(epub_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary statistics for EPUB."""
        chapters = epub_data.get('chapters', [])
        metadata = epub_data.get('metadata', {})

        chapter_stats = EpubStatistics.calculate_chapter_statistics(chapters)
        all_text = ' '.join(ch.get('content', '') for ch in chapters)
        readability = calculate_readability_score(all_text) if all_text else {}
        vocabulary = calculate_vocabulary_richness(all_text) if all_text else {}

        return {
            'metadata': {
                'title': metadata.get('title', 'Unknown'),
                'author': metadata.get('author', 'Unknown'),
                'language': metadata.get('language', 'Unknown')
            },
            'content_statistics': chapter_stats,
            'readability': readability,
            'vocabulary': vocabulary,
            'reading_times': {
                'slow': EpubStatistics.estimate_reading_time(chapter_stats['total_words'], 'slow'),
                'average': EpubStatistics.estimate_reading_time(chapter_stats['total_words'], 'average'),
                'fast': EpubStatistics.estimate_reading_time(chapter_stats['total_words'], 'fast')
            }
        }


def calculate_reading_time(word_count: int) -> Dict[str, int]:
    """Quick function to calculate reading time."""
    return EpubStatistics.estimate_reading_time(word_count)
