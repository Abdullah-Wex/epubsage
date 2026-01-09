"""Pattern definitions for EPUB content classification."""

# Chapter patterns from real data
CHAPTER_PATTERNS = [
    r'^chapter[-_](\d+)$',           # chapter-1, chapter_1
    r'^Chapter[-_](\d+)$',           # Chapter-1, Chapter_1
    r'^ch(\d+)$',                    # ch01, ch1
    r'^ch(\d+)\.x?html$',            # ch01.xhtml, ch1.html
    r'chapter-idm\d+',               # O'Reilly style
    r'(\d+)\s+[A-Z][a-z]',           # "1 Understanding..."
]

# Front matter patterns
FRONT_MATTER_PATTERNS = [
    r'^(title|titlepage)[-_]?',
    r'^(preface|acknowledgments?|about)',
    r'^(copyright|dedication)',
    r'^(contents?|toc)',
    r'^(foreword|introduction)',
    r'^cover$',
]

# Back matter patterns
BACK_MATTER_PATTERNS = [
    r'^appendix[-_]?[a-zA-Z]?',
    r'^(colophon|bibliography)',
    r'^(other[-_]book|about[-_]author)',
    r'^(references|further[-_]reading)',
]

# Part/section patterns
PART_PATTERNS = [
    r'^part[-_](\d+)$',              # part-1, part_1
    r'^Part[-_](\d+)$',              # Part-1, Part_1
    r'Part\s+(\d+)\s+',              # "Part 1 "
    r'^part.*id.*?(\d+)$',           # part-id357 (O'Reilly style)
    r'^part(\d+)\.x?html?$',         # part01.html, part1.xhtml
    r'^part(\d+)$',                  # part01, part1
]

# Image type patterns
IMAGE_PATTERNS = {
    'cover': [r'cover\.(png|jpg|jpeg)', r'.*cover.*\.(png|jpg|jpeg)'],
    'figure': [r'B\d+_\d+_\d+\.(png|jpg)', r'figure.*\.(png|jpg)'],
    'diagram': [r'.*diagram.*\.(png|jpg)', r'.*drawio.*\.(png|jpg)'],
    'chart': [r'.*chart.*\.(png|jpg)', r'.*graph.*\.(png|jpg)'],
    'cell_output': [r'cell-\d+-output-\d+\.(png|jpg)'],
    'model_figure': [r'.*model.*\.(png|jpg)', r'.*unet.*\.(png|jpg)'],
}
