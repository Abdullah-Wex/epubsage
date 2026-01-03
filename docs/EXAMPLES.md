# EpubSage Examples

Real-world use cases and practical examples.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Building a Reading App](#building-a-reading-app)
- [Library Management](#library-management)
- [Content Analysis](#content-analysis)
- [Batch Processing](#batch-processing)
- [Data Export](#data-export)
- [Search Implementation](#search-implementation)

---

## Basic Usage

### Extract Book Information

```python
from epub_sage import process_epub

result = process_epub("book.epub")

print(f"Title: {result.title}")
print(f"Author: {result.author}")
print(f"Publisher: {result.publisher}")
print(f"Chapters: {result.total_chapters}")
print(f"Words: {result.total_words:,}")
print(f"Reading time: {result.estimated_reading_time['hours']}h {result.estimated_reading_time['minutes']}m")
```

![Python Basic](screenshots/python-basic.png)

### Access Chapter Content

```python
from epub_sage import process_epub

result = process_epub("book.epub")

for chapter in result.chapters[:5]:
    print(f"\n## {chapter['title']}")
    print(f"Words: {chapter['word_count']}")
    print(f"Type: {chapter['content_type']}")

    # Get first paragraph
    for block in chapter['content']:
        if block['tag'] == 'p' and len(block['text']) > 50:
            print(f"Preview: {block['text'][:200]}...")
            break
```

![Python Chapters](screenshots/python-chapters.png)

---

## Building a Reading App

### Chapter Navigation

```python
from epub_sage import process_epub

class EbookReader:
    def __init__(self, epub_path):
        self.result = process_epub(epub_path)
        self.current_chapter = 0

    @property
    def title(self):
        return self.result.title

    @property
    def total_chapters(self):
        return self.result.total_chapters

    def get_chapter(self, index):
        """Get chapter by index."""
        if 0 <= index < len(self.result.chapters):
            return self.result.chapters[index]
        return None

    def get_chapter_content(self, index):
        """Get chapter content as HTML."""
        chapter = self.get_chapter(index)
        if chapter:
            return "\n".join(block['html'] for block in chapter['content'])
        return ""

    def get_chapter_text(self, index):
        """Get chapter content as plain text."""
        chapter = self.get_chapter(index)
        if chapter:
            return "\n\n".join(block['text'] for block in chapter['content'])
        return ""

    def next_chapter(self):
        """Move to next chapter."""
        if self.current_chapter < self.total_chapters - 1:
            self.current_chapter += 1
        return self.get_chapter(self.current_chapter)

    def prev_chapter(self):
        """Move to previous chapter."""
        if self.current_chapter > 0:
            self.current_chapter -= 1
        return self.get_chapter(self.current_chapter)

    def get_toc(self):
        """Get table of contents."""
        return [
            {
                'id': ch['chapter_id'],
                'title': ch['title'],
                'type': ch['content_type']
            }
            for ch in self.result.chapters
        ]

# Usage
reader = EbookReader("book.epub")
print(f"Reading: {reader.title}")
print(f"Chapters: {reader.total_chapters}")

# Navigate
chapter = reader.get_chapter(0)
print(f"Current: {chapter['title']}")

chapter = reader.next_chapter()
print(f"Next: {chapter['title']}")
```

### Progress Tracking

```python
from epub_sage import process_epub

class ReadingProgress:
    def __init__(self, epub_path):
        result = process_epub(epub_path)
        self.chapters = result.chapters
        self.total_words = result.total_words
        self.read_chapters = set()

    def mark_read(self, chapter_id):
        """Mark chapter as read."""
        self.read_chapters.add(chapter_id)

    def get_progress(self):
        """Get reading progress percentage."""
        if not self.chapters:
            return 0.0

        read_words = sum(
            ch['word_count']
            for ch in self.chapters
            if ch['chapter_id'] in self.read_chapters
        )
        return (read_words / self.total_words) * 100

    def get_remaining_time(self, wpm=250):
        """Get estimated remaining reading time."""
        read_words = sum(
            ch['word_count']
            for ch in self.chapters
            if ch['chapter_id'] in self.read_chapters
        )
        remaining_words = self.total_words - read_words
        minutes = remaining_words / wpm
        return {
            'hours': int(minutes // 60),
            'minutes': int(minutes % 60)
        }

# Usage
progress = ReadingProgress("book.epub")
progress.mark_read(0)
progress.mark_read(1)

print(f"Progress: {progress.get_progress():.1f}%")
print(f"Remaining: {progress.get_remaining_time()}")
```

---

## Library Management

### Build Book Catalog

```python
import os
from epub_sage import process_epub

def build_catalog(directory):
    """Build catalog from all EPUBs in directory."""
    catalog = []

    for filename in os.listdir(directory):
        if filename.endswith('.epub'):
            path = os.path.join(directory, filename)
            try:
                result = process_epub(path)
                if result.success:
                    catalog.append({
                        'file': filename,
                        'title': result.title,
                        'author': result.author,
                        'publisher': result.publisher,
                        'language': result.language,
                        'words': result.total_words,
                        'chapters': result.total_chapters,
                        'isbn': result.isbn
                    })
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    return catalog

# Usage
catalog = build_catalog("/path/to/ebooks")

# Sort by author
catalog.sort(key=lambda x: x['author'] or '')

for book in catalog:
    print(f"{book['author']} - {book['title']}")
```

### Search Library

```python
from epub_sage import process_epub, SearchService

def search_library(directory, query):
    """Search for text across all books."""
    results = []
    search = SearchService()

    for filename in os.listdir(directory):
        if filename.endswith('.epub'):
            path = os.path.join(directory, filename)
            result = process_epub(path)

            if result.success:
                matches = search.search(result.chapters, query, limit=5)
                if matches:
                    results.append({
                        'book': result.title,
                        'author': result.author,
                        'matches': [
                            {
                                'chapter': m.title,
                                'context': m.context
                            }
                            for m in matches
                        ]
                    })

    return results

# Usage
results = search_library("/path/to/ebooks", "machine learning")

for book in results:
    print(f"\n{book['book']} by {book['author']}")
    for match in book['matches']:
        print(f"  - {match['chapter']}: {match['context'][:100]}...")
```

---

## Content Analysis

### Word Frequency Analysis

```python
from collections import Counter
import re
from epub_sage import process_epub

def analyze_word_frequency(epub_path, top_n=20):
    """Analyze word frequency in book."""
    result = process_epub(epub_path)

    # Collect all text
    all_text = []
    for chapter in result.chapters:
        for block in chapter['content']:
            all_text.append(block['text'].lower())

    # Tokenize and count
    words = re.findall(r'\b[a-z]{3,}\b', ' '.join(all_text))

    # Remove common stop words
    stop_words = {'the', 'and', 'for', 'that', 'this', 'with', 'are', 'was', 'were', 'been'}
    words = [w for w in words if w not in stop_words]

    return Counter(words).most_common(top_n)

# Usage
frequencies = analyze_word_frequency("book.epub")

print("Top 20 words:")
for word, count in frequencies:
    print(f"  {word}: {count}")
```

### Chapter Statistics

```python
from epub_sage import process_epub

def analyze_chapters(epub_path):
    """Analyze chapter statistics."""
    result = process_epub(epub_path)

    stats = {
        'total_chapters': result.total_chapters,
        'total_words': result.total_words,
        'avg_words_per_chapter': result.total_words / result.total_chapters if result.total_chapters else 0,
        'chapters': []
    }

    for chapter in result.chapters:
        stats['chapters'].append({
            'title': chapter['title'],
            'words': chapter['word_count'],
            'images': len(chapter['images']),
            'blocks': len(chapter['content']),
            'type': chapter['content_type']
        })

    # Find longest/shortest
    by_length = sorted(stats['chapters'], key=lambda x: x['words'], reverse=True)
    stats['longest_chapter'] = by_length[0] if by_length else None
    stats['shortest_chapter'] = by_length[-1] if by_length else None

    return stats

# Usage
stats = analyze_chapters("book.epub")

print(f"Total: {stats['total_words']:,} words in {stats['total_chapters']} chapters")
print(f"Average: {stats['avg_words_per_chapter']:.0f} words/chapter")
print(f"Longest: {stats['longest_chapter']['title']} ({stats['longest_chapter']['words']:,} words)")
print(f"Shortest: {stats['shortest_chapter']['title']} ({stats['shortest_chapter']['words']:,} words)")
```

### Image Analysis

```python
from epub_sage import process_epub
from collections import defaultdict

def analyze_images(epub_path):
    """Analyze image distribution."""
    result = process_epub(epub_path)

    stats = {
        'total_images': 0,
        'chapters_with_images': 0,
        'image_types': defaultdict(int),
        'by_chapter': []
    }

    for chapter in result.chapters:
        images = chapter['images']
        if images:
            stats['chapters_with_images'] += 1
            stats['total_images'] += len(images)

            for img in images:
                ext = img.split('.')[-1].lower()
                stats['image_types'][ext] += 1

            stats['by_chapter'].append({
                'title': chapter['title'],
                'count': len(images),
                'images': images
            })

    return stats

# Usage
stats = analyze_images("book.epub")

print(f"Total images: {stats['total_images']}")
print(f"Chapters with images: {stats['chapters_with_images']}")
print(f"Image types: {dict(stats['image_types'])}")

print("\nTop chapters by images:")
for ch in sorted(stats['by_chapter'], key=lambda x: x['count'], reverse=True)[:5]:
    print(f"  {ch['title']}: {ch['count']} images")
```

![Python Images](screenshots/python-images.png)

---

## Batch Processing

### Process Multiple Books

```python
import os
from concurrent.futures import ThreadPoolExecutor
from epub_sage import process_epub

def process_batch(epub_paths, max_workers=4):
    """Process multiple EPUBs in parallel."""
    results = {}

    def process_one(path):
        try:
            return path, process_epub(path)
        except Exception as e:
            return path, str(e)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = executor.map(process_one, epub_paths)

        for path, result in futures:
            results[path] = result

    return results

# Usage
epub_files = [
    "book1.epub",
    "book2.epub",
    "book3.epub"
]

results = process_batch(epub_files)

for path, result in results.items():
    if isinstance(result, str):
        print(f"Error: {path} - {result}")
    else:
        print(f"OK: {result.title} ({result.total_words:,} words)")
```

### CLI Batch Processing

```bash
#!/bin/bash
# Process all EPUBs in directory

OUTPUT_DIR="./extracted"
mkdir -p "$OUTPUT_DIR"

for epub in *.epub; do
    name="${epub%.epub}"
    echo "Processing: $epub"
    epub-sage extract "$epub" -o "$OUTPUT_DIR/${name}.json"
done

echo "Done! Extracted $(ls -1 "$OUTPUT_DIR"/*.json | wc -l) books"
```

---

## Data Export

### Export to JSON

```python
import json
from epub_sage import process_epub

def export_book(epub_path, output_path):
    """Export book to JSON."""
    result = process_epub(epub_path)

    data = {
        'metadata': {
            'title': result.title,
            'author': result.author,
            'publisher': result.publisher,
            'language': result.language,
            'isbn': result.isbn,
            'description': result.full_metadata.description if result.full_metadata else None
        },
        'statistics': {
            'total_chapters': result.total_chapters,
            'total_words': result.total_words,
            'reading_time': result.estimated_reading_time
        },
        'chapters': [
            {
                'id': ch['chapter_id'],
                'title': ch['title'],
                'type': ch['content_type'],
                'word_count': ch['word_count'],
                'images': ch['images'],
                'content': ch['content']
            }
            for ch in result.chapters
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    return output_path

# Usage
export_book("book.epub", "book_data.json")
```

### Sample JSON Output

```json
{
  "metadata": {
    "title": "Learning Python",
    "author": "Mark Lutz",
    "publisher": "O'Reilly Media",
    "language": "en",
    "isbn": "978-1449355739"
  },
  "statistics": {
    "total_chapters": 42,
    "total_words": 245000,
    "reading_time": {
      "hours": 16,
      "minutes": 20
    }
  },
  "chapters": [
    {
      "id": 0,
      "title": "A Python Q&A Session",
      "type": "chapter",
      "word_count": 5200,
      "images": [
        "OEBPS/images/figure1-1.png"
      ],
      "content": [
        {
          "tag": "h1",
          "text": "A Python Q&A Session",
          "is_header": true
        },
        {
          "tag": "p",
          "text": "If you've bought this book..."
        }
      ]
    }
  ]
}
```

### Export to CSV

```python
import csv
from epub_sage import process_epub

def export_chapters_csv(epub_path, output_path):
    """Export chapter list to CSV."""
    result = process_epub(epub_path)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Title', 'Type', 'Words', 'Images'])

        for ch in result.chapters:
            writer.writerow([
                ch['chapter_id'],
                ch['title'],
                ch['content_type'],
                ch['word_count'],
                len(ch['images'])
            ])

    return output_path

# Usage
export_chapters_csv("book.epub", "chapters.csv")
```

---

## Search Implementation

### Basic Search

```python
from epub_sage import process_epub, SearchService

result = process_epub("book.epub")
search = SearchService()

matches = search.search(result.chapters, "python programming")

for match in matches:
    print(f"Chapter: {match.title}")
    print(f"Context: {match.context}")
    print()
```

### Advanced Search with Highlighting

```python
import re
from epub_sage import process_epub

def search_with_highlight(epub_path, query, context_chars=100):
    """Search with highlighted results."""
    result = process_epub(epub_path)
    matches = []

    pattern = re.compile(re.escape(query), re.IGNORECASE)

    for chapter in result.chapters:
        for block in chapter['content']:
            text = block['text']
            for match in pattern.finditer(text):
                start = max(0, match.start() - context_chars)
                end = min(len(text), match.end() + context_chars)

                context = text[start:end]
                # Highlight match
                highlighted = pattern.sub(f'**{match.group()}**', context)

                matches.append({
                    'chapter': chapter['title'],
                    'chapter_id': chapter['chapter_id'],
                    'context': highlighted,
                    'position': match.start()
                })

    return matches

# Usage
results = search_with_highlight("book.epub", "machine learning")

for r in results[:10]:
    print(f"[{r['chapter']}]")
    print(f"  ...{r['context']}...")
    print()
```

---

## See Also

- [README](../README.md) - Quick start guide
- [CLI Reference](CLI.md) - Command-line documentation
- [API Reference](API.md) - Python API documentation
