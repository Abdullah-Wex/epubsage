"""Text analysis utilities for EPUB content."""

import re
from typing import Dict, Any


def calculate_word_count(text: str) -> int:
    """Calculate word count for text."""
    return len(text.split())


def calculate_sentence_count(text: str) -> int:
    """Calculate number of sentences."""
    sentences = re.split(r'[.!?]+', text)
    return len([s.strip() for s in sentences if s.strip()])


def calculate_paragraph_count(text: str) -> int:
    """Calculate number of paragraphs."""
    paragraphs = re.split(r'\n\n+|\r\n\r\n+', text)
    return len([p.strip() for p in paragraphs if p.strip()])


def calculate_readability_score(text: str) -> Dict[str, float]:
    """Calculate basic readability metrics."""
    words = text.split()
    word_count = len(words)
    sentence_count = calculate_sentence_count(text)

    if word_count == 0 or sentence_count == 0:
        return {
            'average_words_per_sentence': 0,
            'average_word_length': 0,
            'complexity_score': 0
        }

    avg_words_per_sentence = word_count / sentence_count
    total_chars = sum(len(word) for word in words)
    avg_word_length = total_chars / word_count

    complexity = min(100, (avg_words_per_sentence - 10) * 2 + (avg_word_length - 4) * 10)
    complexity = max(0, complexity)

    return {
        'average_words_per_sentence': round(avg_words_per_sentence, 1),
        'average_word_length': round(avg_word_length, 1),
        'complexity_score': round(complexity, 1)
    }


def calculate_vocabulary_richness(text: str) -> Dict[str, Any]:
    """Calculate vocabulary richness metrics."""
    words = re.findall(r'\b[a-z]+\b', text.lower())

    if not words:
        return {
            'total_words': 0,
            'unique_words': 0,
            'lexical_diversity': 0,
            'most_common_words': []
        }

    unique_words = set(words)
    lexical_diversity = len(unique_words) / len(words)

    word_freq: Dict[str, int] = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1

    most_common = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        'total_words': len(words),
        'unique_words': len(unique_words),
        'lexical_diversity': round(lexical_diversity, 3),
        'most_common_words': [{'word': w, 'count': c} for w, c in most_common]
    }


def get_text_statistics(text: str) -> Dict[str, int]:
    """Get basic text statistics."""
    return {
        'words': calculate_word_count(text),
        'sentences': calculate_sentence_count(text),
        'paragraphs': calculate_paragraph_count(text),
        'characters': len(text)
    }
