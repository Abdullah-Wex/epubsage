"""
Statistics utilities for EPUB content analysis.

Provides word count, reading time estimation, and other metrics.
"""
from typing import Dict, List, Any
import re


class EpubStatistics:
    """
    Calculate various statistics for EPUB content.
    """

    # Average reading speeds (words per minute)
    READING_SPEEDS = {
        'slow': 200,
        'average': 250,
        'fast': 300
    }

    @staticmethod
    def calculate_word_count(text: str) -> int:
        """
        Calculate word count for text.

        Args:
            text: Text content

        Returns:
            Number of words
        """
        # Split by whitespace and filter empty strings
        words = text.split()
        return len(words)

    @staticmethod
    def calculate_sentence_count(text: str) -> int:
        """
        Calculate number of sentences.

        Args:
            text: Text content

        Returns:
            Number of sentences
        """
        # Simple sentence splitting (. ! ?)
        sentences = re.split(r'[.!?]+', text)
        # Filter empty strings
        sentences = [s.strip() for s in sentences if s.strip()]
        return len(sentences)

    @staticmethod
    def calculate_paragraph_count(text: str) -> int:
        """
        Calculate number of paragraphs.

        Args:
            text: Text content

        Returns:
            Number of paragraphs
        """
        # Split by double newlines or multiple spaces
        paragraphs = re.split(r'\n\n+|\r\n\r\n+', text)
        # Filter empty strings
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return len(paragraphs)

    @classmethod
    def estimate_reading_time(
            cls, word_count: int, reading_speed: str = 'average') -> Dict[str, int]:
        """
        Estimate reading time based on word count.

        Args:
            word_count: Total number of words
            reading_speed: 'slow', 'average', or 'fast'

        Returns:
            Dictionary with hours and minutes
        """
        wpm = cls.READING_SPEEDS.get(
            reading_speed, cls.READING_SPEEDS['average'])

        total_minutes = word_count / wpm
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)

        return {
            'hours': hours,
            'minutes': minutes,
            'total_minutes': int(total_minutes)
        }

    @staticmethod
    def calculate_readability_score(text: str) -> Dict[str, float]:
        """
        Calculate basic readability metrics.

        Args:
            text: Text content

        Returns:
            Dictionary with readability scores
        """
        words = text.split()
        word_count = len(words)
        sentence_count = EpubStatistics.calculate_sentence_count(text)

        if word_count == 0 or sentence_count == 0:
            return {
                'average_words_per_sentence': 0,
                'average_word_length': 0,
                'complexity_score': 0
            }

        # Average words per sentence
        avg_words_per_sentence = word_count / sentence_count

        # Average word length
        total_chars = sum(len(word) for word in words)
        avg_word_length = total_chars / word_count

        # Simple complexity score (0-100)
        # Based on sentence length and word length
        complexity = min(100, (avg_words_per_sentence - 10)
                         * 2 + (avg_word_length - 4) * 10)
        complexity = max(0, complexity)

        return {
            'average_words_per_sentence': round(avg_words_per_sentence, 1),
            'average_word_length': round(avg_word_length, 1),
            'complexity_score': round(complexity, 1)
        }

    @staticmethod
    def calculate_chapter_statistics(
            chapters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics for a list of chapters.

        Args:
            chapters: List of chapter dictionaries

        Returns:
            Comprehensive statistics dictionary
        """
        if not chapters:
            return {
                'total_chapters': 0,
                'total_words': 0,
                'total_characters': 0,
                'average_words_per_chapter': 0,
                'shortest_chapter': None,
                'longest_chapter': None,
                'reading_time': {'hours': 0, 'minutes': 0}
            }

        total_words = 0
        total_chars = 0
        chapter_word_counts = []

        for chapter in chapters:
            content = chapter.get('content', '')
            word_count = chapter.get('word_count')

            if word_count is None:
                word_count = EpubStatistics.calculate_word_count(content)

            total_words += word_count
            total_chars += len(content)
            chapter_word_counts.append({
                'chapter_id': chapter.get('chapter_id', 0),
                'title': chapter.get('title', 'Unknown'),
                'word_count': word_count
            })

        # Sort by word count
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
        """
        Calculate vocabulary richness metrics.

        Args:
            text: Text content

        Returns:
            Dictionary with vocabulary metrics
        """
        # Convert to lowercase and extract words
        words = re.findall(r'\b[a-z]+\b', text.lower())

        if not words:
            return {
                'total_words': 0,
                'unique_words': 0,
                'lexical_diversity': 0,
                'most_common_words': []
            }

        # Count unique words
        unique_words = set(words)

        # Calculate lexical diversity (unique/total)
        lexical_diversity = len(unique_words) / len(words)

        # Find most common words
        word_freq: Dict[str, int] = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        most_common = sorted(
            word_freq.items(),
            key=lambda x: x[1],
            reverse=True)[
            :10]

        return {
            'total_words': len(words),
            'unique_words': len(unique_words),
            'lexical_diversity': round(lexical_diversity, 3),
            'most_common_words': [
                {'word': word, 'count': count}
                for word, count in most_common
            ]
        }

    @staticmethod
    def generate_summary_statistics(
            epub_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive summary statistics for EPUB.

        Args:
            epub_data: Dictionary with EPUB data including chapters

        Returns:
            Complete statistical summary
        """
        chapters = epub_data.get('chapters', [])
        metadata = epub_data.get('metadata', {})

        # Calculate all statistics
        chapter_stats = EpubStatistics.calculate_chapter_statistics(chapters)

        # Combine all text for overall statistics
        all_text = ' '.join(ch.get('content', '') for ch in chapters)
        readability = EpubStatistics.calculate_readability_score(
            all_text) if all_text else {}
        vocabulary = EpubStatistics.calculate_vocabulary_richness(
            all_text) if all_text else {}

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
                'slow': EpubStatistics.estimate_reading_time(
                    chapter_stats['total_words'], 'slow'
                ),
                'average': EpubStatistics.estimate_reading_time(
                    chapter_stats['total_words'], 'average'
                ),
                'fast': EpubStatistics.estimate_reading_time(
                    chapter_stats['total_words'], 'fast'
                )
            }
        }


# Convenience functions
def calculate_reading_time(word_count: int) -> Dict[str, int]:
    """
    Quick function to calculate reading time.

    Args:
        word_count: Number of words

    Returns:
        Dictionary with hours and minutes
    """
    return EpubStatistics.estimate_reading_time(word_count)


def get_text_statistics(text: str) -> Dict[str, int]:
    """
    Get basic text statistics.

    Args:
        text: Text content

    Returns:
        Dictionary with word, sentence, and paragraph counts
    """
    return {
        'words': EpubStatistics.calculate_word_count(text),
        'sentences': EpubStatistics.calculate_sentence_count(text),
        'paragraphs': EpubStatistics.calculate_paragraph_count(text),
        'characters': len(text)
    }
