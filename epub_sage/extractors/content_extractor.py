"""
Content Extractor for EPUB HTML files

This module provides intelligent content extraction that automatically detects
wrapper levels and groups content by headers for any EPUB publisher format.
"""

from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, Optional, Set
import os


# Common EPUB image extensions (YAGNI: only what's actually used)
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp')

# External URL prefixes (DRY: single source of truth)
EXTERNAL_PREFIXES = ('http://', 'https://', 'data:')


def _is_external_url(path: str) -> bool:
    """Check if path is an external URL."""
    return path.startswith(EXTERNAL_PREFIXES)


def _normalize_path(path: str) -> str:
    """Normalize path separators and handle parent refs."""
    normalized = path.replace('\\', '/')
    while normalized.startswith('../'):
        normalized = normalized[3:]
    return normalized


def discover_epub_images(epub_directory_path: str) -> Set[str]:
    """Discover all image files in an EPUB directory."""
    image_paths: Set[str] = set()

    for root, _, files in os.walk(epub_directory_path):
        for file in files:
            if file.lower().endswith(IMAGE_EXTENSIONS):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, epub_directory_path)
                image_paths.add(_normalize_path(relative_path))

    return image_paths


def resolve_image_path(img_src: str, html_rel_dir: str) -> Optional[str]:
    """Resolve a relative image path to EPUB-root-relative path."""
    if _is_external_url(img_src):
        return img_src

    # Remove fragment/query
    base_src = img_src.split('#')[0].split('?')[0]
    if not base_src:
        return None

    resolved = os.path.normpath(os.path.join(html_rel_dir, base_src))
    return _normalize_path(resolved)


def resolve_and_validate_images(
    raw_images: List[str],
    html_rel_dir: str,
    valid_images: Set[str]
) -> List[str]:
    """Resolve image paths and filter to only those that exist in EPUB."""
    seen: Set[str] = set()
    result: List[str] = []

    for img_src in raw_images:
        resolved = resolve_image_path(img_src, html_rel_dir)
        if not resolved or resolved in seen:
            continue

        # Include if external URL or exists in EPUB
        if _is_external_url(resolved) or resolved in valid_images:
            seen.add(resolved)
            result.append(resolved)

    return result


def is_generic_header(element: Optional[Tag]) -> bool:
    """
    Identifies if an element is a header using tags, classes, and roles.

    Broadens detection beyond h1-h6 to support diverse writer styles.
    """
    if not element or not hasattr(element, 'name') or not element.name:
        return False

    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        return True

    # Check common semantic roles
    if element.get('role') == 'heading':
        return True

    # Check class and ID for header-related keywords
    keywords = [
        'title', 'heading', 'chapter-head', 'ch-title', 'section-title',
        'chapter-label', 'ch-label', 'title-prefix', 'chapter-number',
        'label', 'title-text'
    ]

    # Combine class and ID for a single check
    class_attr = element.get('class')
    cls = " ".join(class_attr) if isinstance(class_attr, list) else (class_attr or "")
    id_val = element.get('id', '') or ""
    id_str = id_val if isinstance(id_val, str) else ""
    combined = (cls + " " + id_str).lower()

    if any(kw in combined for kw in keywords):
        # Additional safety: headers usually shouldn't be too long
        text = element.get_text(strip=True)
        if 0 < len(text) < 200:
            return True

    return False


def extract_content_sections(html_file_path: str) -> List[Dict[str, Any]]:
    """
    Extract content sections grouped by headers from HTML file.

    Uses generic header detection to support diverse publisher styles.

    Args:
        html_file_path: Path to HTML file to extract content from

    Returns:
        List of sections with header and content:
        [
            {
                'header': 'Chapter Title',
                'content': [list of content elements]
            },
            ...
        ]
    """
    if not os.path.exists(html_file_path):
        return []

    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            # Step 3.3: Try lxml-xml first for robustness with XHTML, then
            # fallback
            try:
                soup = BeautifulSoup(file, 'lxml-xml')
            except Exception:
                file.seek(0)
                soup = BeautifulSoup(file, 'html.parser')
    except Exception:
        return []

    body = soup.find('body')
    if not body:
        return []

    # Step 3.1: Selective tag stripping (boilerplate removal)
    for junk_tag in ['nav', 'aside', 'script', 'style', 'footer', 'header']:
        for junk in body.find_all(junk_tag):
            # Only decompose if it's not a generic header or doesn't contain
            # one
            if not is_generic_header(junk) and not any(
                    is_generic_header(c if isinstance(c, Tag) else None)
                    for c in junk.descendants if getattr(c, 'name', None)):
                junk.decompose()

    # Navigate to content level using child count logic
    current_container: Tag = body
    while True:
        children: List[Tag] = [
            child for child in current_container.children
            if isinstance(child, Tag) and child.name]

        # If only 1 child = wrapper, go deeper
        if len(children) == 1:
            current_container = children[0]
        else:
            # Multiple children = check if they are content or just wrapper containers
            # Look for headers as indication of content level
            header_tags: List[Tag] = [
                child for child in children if is_generic_header(child)]

            if len(header_tags) > 0:
                # Found headers, this is content level - stop here
                break
            elif len(children) > 0 and all(child.name in ['div', 'section', 'article'] for child in children):
                # All children are containers, need to check what's inside them
                break
            else:
                # Mixed content types, assume this is content level
                break

    # Get all content elements at this level
    content_children: List[Tag] = []
    if current_container:
        # Get all direct children (no filtering by tag type)
        all_direct_children: List[Tag] = [
            child for child in current_container.children
            if isinstance(child, Tag) and child.name]

        # Check if we have headers at this level
        direct_headers: List[Tag] = [
            child for child in all_direct_children if is_generic_header(child)]

        if direct_headers:
            # We have headers at this level, take ALL direct children as
            # content
            content_children = all_direct_children
        else:
            # No direct headers, check if children are containers that need to
            # be processed
            for child in all_direct_children:
                if child.name in ['div', 'section', 'article']:
                    # Check if this container has any children
                    child_elements: List[Tag] = [
                        subchild for subchild in child.children
                        if isinstance(subchild, Tag) and subchild.name]
                    if child_elements:
                        # Container has children, extract ALL of them
                        content_children.extend(child_elements)
                    else:
                        # Container has no children but might have text, treat
                        # as content
                        if child.get_text().strip():
                            content_children.append(child)
                else:
                    # Not a container, add directly
                    content_children.append(child)

    # Group by headers
    sections: List[Dict[str, Any]] = []
    current_header: Optional[str] = None
    current_content: List[Dict[str, Any]] = []
    current_images: List[str] = []

    for child in content_children:
        # Extract images from this child element
        child_images: List[str] = []
        # Standard img tags
        for img in child.find_all('img'):
            src = img.get('src')
            if src and isinstance(src, str):
                child_images.append(src)
        # SVG image tags
        for svg_img in child.find_all('image'):
            href = svg_img.get('href') or svg_img.get('xlink:href')
            if href and isinstance(href, str):
                child_images.append(href)
        # Check if the child itself is an image tag
        if child.name == 'img':
            src = child.get('src')
            if src and isinstance(src, str) and src not in child_images:
                child_images.append(src)
        elif child.name == 'image':
            href = child.get('href') or child.get('xlink:href')
            if href and isinstance(href, str) and href not in child_images:
                child_images.append(href)

        # Step 3.2: Filter out junk elements (boilerplate/link-heavy)
        generic_header = is_generic_header(child)
        if not generic_header:
            # Check link-to-text density
            text = child.get_text(strip=True)
            if len(text) > 40:  # Only check significant blocks
                links_text = "".join([a.get_text(strip=True)
                                     for a in child.find_all('a')])
                if (len(links_text) / len(text)) > 0.70:
                    # Likely a menu or breadcrumb block - skip
                    continue

            # Skip completely empty blocks that have no images
            if not text and not child_images:
                continue

        if generic_header:
            # Save previous section before starting new one
            if current_header or current_content:
                sections.append({
                    'header': current_header or 'Intro',
                    'content': current_content,
                    'images': current_images
                })
            # Start new section
            current_header = child.get_text().strip()
            current_content = [{
                'tag': child.name,
                'text': current_header,
                'html': str(child),
                'images': child_images,
                'is_header': True
            }]
            current_images = child_images  # Images in the header itself
        else:
            # Add to current section
            current_content.append({
                'tag': child.name,
                'text': child.get_text().strip(),
                'html': str(child),
                'images': child_images
            })
            current_images.extend(child_images)

    # Add final section
    if current_header or current_content:
        sections.append({
            'header': current_header or 'Intro',
            'content': current_content,
            'images': current_images
        })

    return sections


def extract_book_content(epub_directory_path: str) -> Dict[str, Any]:
    """
    Extract content from all HTML files in an EPUB directory.

    Args:
        epub_directory_path: Path to extracted EPUB directory

    Returns:
        Dictionary with file paths and their extracted content sections
    """
    content_data = {}

    # Step 1: Discover all valid images in the EPUB
    valid_images = discover_epub_images(epub_directory_path)

    # Process all HTML files in the directory recursively
    # This is more robust than looking specifically for 'OEBPS'
    for root, dirs, files in os.walk(epub_directory_path):
        # Skip some common non-content directories
        if any(skip in root for skip in ['META-INF', '__MACOSX', '.git']):
            continue

        for file in files:
            if file.endswith(('.html', '.xhtml', '.htm')):
                file_path = os.path.join(root, file)
                # Path relative to the EPUB root
                relative_path = os.path.relpath(file_path, epub_directory_path)
                # Normalize path separators
                relative_path = relative_path.replace('\\', '/')

                sections = extract_content_sections(file_path)
                if sections:
                    # Resolve and validate image paths
                    html_rel_dir = os.path.dirname(relative_path)

                    for section in sections:
                        # Resolve section-level images
                        section['images'] = resolve_and_validate_images(
                            section.get('images', []),
                            html_rel_dir,
                            valid_images
                        )

                        # Resolve element-level images
                        for block in section.get('content', []):
                            block['images'] = resolve_and_validate_images(
                                block.get('images', []),
                                html_rel_dir,
                                valid_images
                            )

                    content_data[relative_path] = sections

    return content_data
